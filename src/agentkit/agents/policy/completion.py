from abc import ABC, abstractmethod

from agentkit.agents.policy.decision import PolicyDecision
from agentkit.agents.state import AgentState


class CompletionPolicy(ABC):
    @abstractmethod
    def evaluate_completion(
        self,
        state: AgentState,
    ) -> PolicyDecision:
        raise NotImplementedError
