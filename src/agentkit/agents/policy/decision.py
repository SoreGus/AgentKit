from dataclasses import dataclass
from enum import StrEnum


class PolicyAction(StrEnum):
    ALLOW = "allow"
    RETRY = "retry"
    REJECT = "reject"


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    action: PolicyAction
    feedback: str = ""

    @classmethod
    def allow(cls, feedback: str = "") -> "PolicyDecision":
        return cls(action=PolicyAction.ALLOW, feedback=feedback)

    @classmethod
    def retry(cls, feedback: str) -> "PolicyDecision":
        return cls(action=PolicyAction.RETRY, feedback=feedback)

    @classmethod
    def reject(cls, feedback: str) -> "PolicyDecision":
        return cls(action=PolicyAction.REJECT, feedback=feedback)
