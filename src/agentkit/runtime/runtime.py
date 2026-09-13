from dataclasses import dataclass

from agentkit.agents import Agent, AgentState, PolicyAction
from agentkit.models import MessageRole, Model, ModelMessage, ModelRequest
from agentkit.runtime.event import (
    ModelRequested,
    ModelResponded,
    PolicyEvaluated,
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
                for call in response.tool_calls:
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
                        )
                    )

                continue

            state = AgentState(
                messages=tuple(messages),
                iteration=iteration,
                tool_calls=tuple(all_calls),
                tool_results=tuple(all_results),
                response=response,
            )

            decision = self._evaluate_policies(agent, state)

            if decision is None or decision.action == PolicyAction.ALLOW:
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
                    decision.feedback or "Agent response was rejected by policy."
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

    def _evaluate_policies(
        self,
        agent: Agent,
        state: AgentState,
    ):
        for policy in agent.policies:
            decision = policy.evaluate(state)

            self._emit(
                PolicyEvaluated(
                    iteration=state.iteration,
                    policy_name=type(policy).__name__,
                    decision=decision,
                )
            )

            if decision.action != PolicyAction.ALLOW:
                return decision

        return None

    def _emit(self, event: RuntimeEvent) -> None:
        if self._on_event is not None:
            self._on_event(event)
