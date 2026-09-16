from dataclasses import dataclass

from agentkit.agents.policy.decision import PolicyAction, PolicyDecision


@dataclass(frozen=True, slots=True)
class PolicyMessages:
    allow: str = ""
    retry: str = ""
    reject: str = ""

    def for_action(self, action: PolicyAction) -> str:
        if action == PolicyAction.ALLOW:
            return self.allow
        if action == PolicyAction.RETRY:
            return self.retry
        return self.reject


class ConfiguredPolicy:
    def __init__(
        self,
        policy_name: str,
        max_retries: int | None = None,
        messages: PolicyMessages | None = None,
    ) -> None:
        if not policy_name.strip():
            raise ValueError("Policy name must not be empty.")

        if max_retries is not None and max_retries < 0:
            raise ValueError("Policy max_retries must be zero or greater.")

        self.policy_name = policy_name
        self.max_retries = max_retries
        self.messages = messages or PolicyMessages()

    def configured_decision(
        self,
        decision: PolicyDecision,
    ) -> PolicyDecision:
        message = self.messages.for_action(decision.action)

        if not message:
            return decision

        if decision.action == PolicyAction.ALLOW:
            return PolicyDecision.allow(message)
        if decision.action == PolicyAction.RETRY:
            return PolicyDecision.retry(message)
        return PolicyDecision.reject(message)

    def retry_exhausted_feedback(self) -> str:
        if self.messages.reject:
            return self.messages.reject

        return (
            f"Policy '{self.policy_name}' exceeded its configured retry limit."
        )
