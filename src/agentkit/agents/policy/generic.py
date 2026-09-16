from typing import Any

from agentkit.agents.policy.after_tool import AfterToolPolicy
from agentkit.agents.policy.before_tool import BeforeToolPolicy
from agentkit.agents.policy.completion import CompletionPolicy
from agentkit.agents.policy.configured import ConfiguredPolicy, PolicyMessages
from agentkit.agents.policy.decision import PolicyDecision
from agentkit.agents.policy.model import ModelPolicyEventHandler
from agentkit.agents.policy.model_completion import ModelCompletionPolicy
from agentkit.agents.state import AgentState
from agentkit.models import MessageRole, Model
from agentkit.tools import ToolCall, ToolResult


class AllowedToolsPolicy(ConfiguredPolicy, BeforeToolPolicy):
    def __init__(
        self,
        allowed_tools: tuple[str, ...],
        policy_name: str = "allowed_tools",
        max_retries: int | None = None,
        messages: PolicyMessages | None = None,
    ) -> None:
        ConfiguredPolicy.__init__(
            self,
            policy_name=policy_name,
            max_retries=max_retries,
            messages=messages,
        )
        self._allowed_tools = frozenset(allowed_tools)

    def evaluate_before_tool(
        self,
        state: AgentState,
        call: ToolCall,
    ) -> PolicyDecision:
        del state

        if call.name in self._allowed_tools:
            return self.configured_decision(PolicyDecision.allow())

        return self.configured_decision(
            PolicyDecision.reject(
                f"Tool '{call.name}' is not allowed by policy "
                f"'{self.policy_name}'."
            )
        )


class RetryToolErrorsPolicy(ConfiguredPolicy, AfterToolPolicy):
    def __init__(
        self,
        policy_name: str = "retry_tool_errors",
        max_retries: int | None = None,
        messages: PolicyMessages | None = None,
    ) -> None:
        ConfiguredPolicy.__init__(
            self,
            policy_name=policy_name,
            max_retries=max_retries,
            messages=messages,
        )

    def evaluate_after_tool(
        self,
        state: AgentState,
        result: ToolResult,
    ) -> PolicyDecision:
        del state

        if not result.is_error:
            return self.configured_decision(PolicyDecision.allow())

        return self.configured_decision(
            PolicyDecision.retry(
                f"Tool '{result.name}' failed: {result.content}. "
                "Review the failure, adjust the approach, and continue."
            )
        )


class RequireToolSuccessPolicy(ConfiguredPolicy, CompletionPolicy):
    def __init__(
        self,
        tool_names: tuple[str, ...],
        mode: str = "any",
        policy_name: str = "require_tool_success",
        max_retries: int | None = None,
        messages: PolicyMessages | None = None,
    ) -> None:
        if not tool_names:
            raise ValueError("RequireToolSuccessPolicy requires at least one tool.")

        normalized_mode = mode.strip().lower()
        if normalized_mode not in {"any", "all"}:
            raise ValueError("RequireToolSuccessPolicy mode must be 'any' or 'all'.")

        ConfiguredPolicy.__init__(
            self,
            policy_name=policy_name,
            max_retries=max_retries,
            messages=messages,
        )
        self._tool_names = tool_names
        self._mode = normalized_mode

    def evaluate_completion(
        self,
        state: AgentState,
    ) -> PolicyDecision:
        completed = {
            result.name
            for result in state.successful_tool_results()
        }

        if self._mode == "all":
            satisfied = all(name in completed for name in self._tool_names)
        else:
            satisfied = any(name in completed for name in self._tool_names)

        if satisfied:
            return self.configured_decision(PolicyDecision.allow())

        tool_list = ", ".join(self._tool_names)
        qualifier = "all" if self._mode == "all" else "at least one"
        return self.configured_decision(
            PolicyDecision.retry(
                f"Completion requires a successful call to {qualifier} of: "
                f"{tool_list}."
            )
        )


class RequireToolCallPolicy(ConfiguredPolicy, CompletionPolicy):
    def __init__(
        self,
        tool_names: tuple[str, ...],
        mode: str = "any",
        policy_name: str = "require_tool_call",
        max_retries: int | None = None,
        messages: PolicyMessages | None = None,
    ) -> None:
        if not tool_names:
            raise ValueError("RequireToolCallPolicy requires at least one tool.")

        normalized_mode = mode.strip().lower()
        if normalized_mode not in {"any", "all"}:
            raise ValueError("RequireToolCallPolicy mode must be 'any' or 'all'.")

        ConfiguredPolicy.__init__(
            self,
            policy_name=policy_name,
            max_retries=max_retries,
            messages=messages,
        )
        self._tool_names = tool_names
        self._mode = normalized_mode

    def evaluate_completion(self, state: AgentState) -> PolicyDecision:
        called = {call.name for call in state.tool_calls}
        if self._mode == "all":
            satisfied = all(name in called for name in self._tool_names)
        else:
            satisfied = any(name in called for name in self._tool_names)

        if satisfied:
            return self.configured_decision(PolicyDecision.allow())

        tool_list = ", ".join(self._tool_names)
        return self.configured_decision(
            PolicyDecision.retry(
                f"Completion requires calling the configured tool(s): {tool_list}."
            )
        )


class EvidenceReviewPolicy(ConfiguredPolicy, ModelCompletionPolicy):
    def __init__(
        self,
        model: Model,
        system_prompt: str,
        strictness: str = "balanced",
        policy_name: str = "evidence_review",
        max_retries: int | None = None,
        messages: PolicyMessages | None = None,
        on_model_event: ModelPolicyEventHandler | None = None,
    ) -> None:
        normalized_strictness = strictness.strip().lower()
        if normalized_strictness not in {"lenient", "balanced", "strict"}:
            raise ValueError(
                "Model policy strictness must be 'lenient', 'balanced', or 'strict'."
            )

        ConfiguredPolicy.__init__(
            self,
            policy_name=policy_name,
            max_retries=max_retries,
            messages=messages,
        )
        ModelCompletionPolicy.__init__(
            self,
            model=model,
            on_model_event=on_model_event,
            policy_name=policy_name,
        )
        self._review_system_prompt = system_prompt.strip()
        self._strictness = normalized_strictness

    def evaluate_completion(self, state: AgentState) -> PolicyDecision:
        decision = ModelCompletionPolicy.evaluate_completion(self, state)
        return self.configured_decision(decision)

    def review_instructions(self, state: AgentState) -> str:
        del state

        strictness = {
            "lenient": (
                "Use lenient review: retry only when an important claim is clearly "
                "unsupported or contradicted by the collected evidence."
            ),
            "balanced": (
                "Use balanced review: require support for material claims without "
                "requiring exhaustive inspection or peripheral evidence."
            ),
            "strict": (
                "Use strict review: require direct evidence for all material claims "
                "and important relationships before allowing completion."
            ),
        }[self._strictness]

        if self._review_system_prompt:
            return f"{self._review_system_prompt}\n\n{strictness}"

        return strictness

    def review_payload(self, state: AgentState) -> dict[str, Any]:
        return {
            "task": self._original_prompt(state),
            "candidate_answer": (
                state.response.content
                if state.response is not None
                else ""
            ),
            "tool_evidence": self._tool_evidence(state),
        }

    def _original_prompt(self, state: AgentState) -> str:
        for message in state.messages:
            if message.role == MessageRole.USER:
                return message.content
        return ""

    def _tool_evidence(self, state: AgentState) -> list[dict[str, Any]]:
        results_by_call_id = {
            result.call_id: result
            for result in state.tool_results
        }

        evidence: list[dict[str, Any]] = []
        for call in state.tool_calls:
            result = results_by_call_id.get(call.id)
            if result is None:
                continue

            evidence.append(
                {
                    "tool": call.name,
                    "arguments": call.arguments,
                    "is_error": result.is_error,
                    "result": result.content,
                }
            )

        return evidence
