from dataclasses import dataclass

from agentkit.agents import Agent, AgentState, PolicyAction, PolicyDecision
from agentkit.models import MessageRole, Model, ModelMessage, ModelRequest
from agentkit.runtime.event import (
    ModelRequested,
    ModelResponded,
    PolicyEvaluated,
    PolicyPhase,
    RuntimeCompleted,
    RuntimeEvent,
    RuntimeEventHandler,
    RuntimeStarted,
    ToolCalled,
    ToolCompleted,
)
from agentkit.tools import ToolCall, ToolExecutor, ToolRegistry, ToolResult


class AgentRuntimeError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class RuntimeResult:
    content: str
    messages: tuple[ModelMessage, ...]
    iterations: int
    state: AgentState


class AgentRuntime:
    def __init__(
        self,
        model: Model,
        on_event: RuntimeEventHandler | None = None,
    ) -> None:
        self._model = model
        self._on_event = on_event

    def run(
        self,
        agent: Agent,
        prompt: str,
    ) -> RuntimeResult:
        messages = [
            ModelMessage(
                role=MessageRole.SYSTEM,
                content=agent.instructions,
            ),
            ModelMessage(
                role=MessageRole.USER,
                content=prompt,
            ),
        ]

        registry = ToolRegistry()
        for tool in agent.tools:
            registry.register(tool)

        executor = ToolExecutor(registry)
        all_calls: list[ToolCall] = []
        all_results: list[ToolResult] = []
        policy_retry_counts: dict[tuple[PolicyPhase, int], int] = {}

        self._emit(
            RuntimeStarted(
                agent_name=agent.name,
                prompt=prompt,
                tool_names=tuple(tool.name for tool in agent.tools),
            )
        )

        for iteration in range(1, agent.max_iterations + 1):
            self._emit(
                ModelRequested(
                    iteration=iteration,
                    message_count=len(messages),
                )
            )

            response = self._model.generate(
                ModelRequest(
                    messages=tuple(messages),
                    tools=agent.tools,
                )
            )

            self._emit(
                ModelResponded(
                    iteration=iteration,
                    response=response,
                )
            )

            messages.append(
                ModelMessage(
                    role=MessageRole.ASSISTANT,
                    content=response.content,
                    tool_calls=response.tool_calls,
                )
            )

            if response.tool_calls:
                retry_feedback = self._process_tool_calls(
                    agent=agent,
                    executor=executor,
                    messages=messages,
                    iteration=iteration,
                    calls=response.tool_calls,
                    all_calls=all_calls,
                    all_results=all_results,
                    policy_retry_counts=policy_retry_counts,
                )

                if retry_feedback:
                    messages.append(
                        ModelMessage(
                            role=MessageRole.USER,
                            content=retry_feedback,
                        )
                    )

                continue

            state = self._state(
                messages=messages,
                iteration=iteration,
                calls=all_calls,
                results=all_results,
                response=response,
            )

            decision = self._evaluate_completion_policies(
                agent=agent,
                state=state,
                retry_counts=policy_retry_counts,
            )

            if decision.action == PolicyAction.ALLOW:
                result = RuntimeResult(
                    content=response.content,
                    messages=tuple(messages),
                    iterations=iteration,
                    state=state,
                )

                self._emit(
                    RuntimeCompleted(
                        iterations=iteration,
                        content=response.content,
                    )
                )

                return result

            if decision.action == PolicyAction.REJECT:
                raise AgentRuntimeError(
                    decision.feedback
                    or "Agent completion was rejected by policy."
                )

            messages.append(
                ModelMessage(
                    role=MessageRole.USER,
                    content=decision.feedback,
                )
            )

        raise AgentRuntimeError(
            f"Agent '{agent.name}' exceeded the maximum of "
            f"{agent.max_iterations} iterations."
        )

    def _process_tool_calls(
        self,
        agent: Agent,
        executor: ToolExecutor,
        messages: list[ModelMessage],
        iteration: int,
        calls: tuple[ToolCall, ...],
        all_calls: list[ToolCall],
        all_results: list[ToolResult],
        policy_retry_counts: dict[tuple[PolicyPhase, int], int],
    ) -> str:
        feedback: list[str] = []

        for call in calls:
            state = self._state(
                messages=messages,
                iteration=iteration,
                calls=all_calls,
                results=all_results,
            )

            decision = self._evaluate_before_tool_policies(
                agent=agent,
                state=state,
                call=call,
                retry_counts=policy_retry_counts,
            )

            if decision.action == PolicyAction.REJECT:
                raise AgentRuntimeError(
                    decision.feedback
                    or f"Tool call '{call.name}' was rejected by policy."
                )

            if decision.action == PolicyAction.RETRY:
                feedback.append(decision.feedback)
                continue

            all_calls.append(call)

            self._emit(
                ToolCalled(
                    iteration=iteration,
                    call=call,
                )
            )

            result = executor.execute(call)
            all_results.append(result)

            self._emit(
                ToolCompleted(
                    iteration=iteration,
                    result=result,
                )
            )

            messages.append(
                ModelMessage(
                    role=MessageRole.TOOL,
                    content=result.content,
                    tool_name=result.name,
                    tool_call_id=call.id,
                )
            )

            state = self._state(
                messages=messages,
                iteration=iteration,
                calls=all_calls,
                results=all_results,
            )

            decision = self._evaluate_after_tool_policies(
                agent=agent,
                state=state,
                result=result,
                retry_counts=policy_retry_counts,
            )

            if decision.action == PolicyAction.REJECT:
                raise AgentRuntimeError(
                    decision.feedback
                    or f"Tool result '{result.name}' was rejected by policy."
                )

            if decision.action == PolicyAction.RETRY:
                feedback.append(decision.feedback)

        return "\n".join(item for item in feedback if item)

    def _evaluate_completion_policies(
        self,
        agent: Agent,
        state: AgentState,
        retry_counts: dict[tuple[PolicyPhase, int], int],
    ) -> PolicyDecision:
        for policy in agent.completion_policies:
            decision = policy.evaluate_completion(state)
            decision = self._enforce_retry_limit(
                phase=PolicyPhase.COMPLETION,
                policy=policy,
                decision=decision,
                retry_counts=retry_counts,
            )

            self._emit_policy(
                state=state,
                phase=PolicyPhase.COMPLETION,
                policy=policy,
                decision=decision,
            )

            if decision.action != PolicyAction.ALLOW:
                return decision

        return PolicyDecision.allow()

    def _evaluate_before_tool_policies(
        self,
        agent: Agent,
        state: AgentState,
        call: ToolCall,
        retry_counts: dict[tuple[PolicyPhase, int], int],
    ) -> PolicyDecision:
        for policy in agent.before_tool_policies:
            decision = policy.evaluate_before_tool(state, call)
            decision = self._enforce_retry_limit(
                phase=PolicyPhase.BEFORE_TOOL,
                policy=policy,
                decision=decision,
                retry_counts=retry_counts,
            )

            self._emit_policy(
                state=state,
                phase=PolicyPhase.BEFORE_TOOL,
                policy=policy,
                decision=decision,
            )

            if decision.action != PolicyAction.ALLOW:
                return decision

        return PolicyDecision.allow()

    def _evaluate_after_tool_policies(
        self,
        agent: Agent,
        state: AgentState,
        result: ToolResult,
        retry_counts: dict[tuple[PolicyPhase, int], int],
    ) -> PolicyDecision:
        for policy in agent.after_tool_policies:
            decision = policy.evaluate_after_tool(state, result)
            decision = self._enforce_retry_limit(
                phase=PolicyPhase.AFTER_TOOL,
                policy=policy,
                decision=decision,
                retry_counts=retry_counts,
            )

            self._emit_policy(
                state=state,
                phase=PolicyPhase.AFTER_TOOL,
                policy=policy,
                decision=decision,
            )

            if decision.action != PolicyAction.ALLOW:
                return decision

        return PolicyDecision.allow()

    def _enforce_retry_limit(
        self,
        phase: PolicyPhase,
        policy: object,
        decision: PolicyDecision,
        retry_counts: dict[tuple[PolicyPhase, int], int],
    ) -> PolicyDecision:
        if decision.action != PolicyAction.RETRY:
            return decision

        max_retries = getattr(policy, "max_retries", None)
        if max_retries is None:
            return decision

        key = (phase, id(policy))
        count = retry_counts.get(key, 0) + 1
        retry_counts[key] = count

        if count <= max_retries:
            return decision

        feedback_method = getattr(policy, "retry_exhausted_feedback", None)
        if callable(feedback_method):
            feedback = feedback_method()
        else:
            name = self._policy_name(policy)
            feedback = f"Policy '{name}' exceeded its retry limit."

        return PolicyDecision.reject(feedback)

    def _emit_policy(
        self,
        state: AgentState,
        phase: PolicyPhase,
        policy: object,
        decision: PolicyDecision,
    ) -> None:
        self._emit(
            PolicyEvaluated(
                iteration=state.iteration,
                phase=phase,
                policy_name=self._policy_name(policy),
                decision=decision,
            )
        )

    def _policy_name(self, policy: object) -> str:
        configured_name = getattr(policy, "policy_name", None)
        if isinstance(configured_name, str) and configured_name.strip():
            return configured_name
        return type(policy).__name__

    def _state(
        self,
        messages: list[ModelMessage],
        iteration: int,
        calls: list[ToolCall],
        results: list[ToolResult],
        response=None,
    ) -> AgentState:
        return AgentState(
            messages=tuple(messages),
            iteration=iteration,
            tool_calls=tuple(calls),
            tool_results=tuple(results),
            response=response,
        )

    def _emit(self, event: RuntimeEvent) -> None:
        if self._on_event is not None:
            self._on_event(event)
