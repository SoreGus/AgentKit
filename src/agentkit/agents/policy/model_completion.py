from abc import abstractmethod
from typing import Any

from agentkit.agents.policy.completion import CompletionPolicy
from agentkit.agents.policy.decision import PolicyDecision
from agentkit.agents.policy.model import ModelPolicy
from agentkit.agents.state import AgentState
from agentkit.models import Model


class ModelCompletionPolicy(ModelPolicy, CompletionPolicy):
    def __init__(self, model: Model) -> None:
        ModelPolicy.__init__(self, model)

    def evaluate_completion(
        self,
        state: AgentState,
    ) -> PolicyDecision:
        return self.evaluate_with_model(
            instructions=self.review_instructions(state),
            payload=self.review_payload(state),
        )

    @abstractmethod
    def review_instructions(
        self,
        state: AgentState,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def review_payload(
        self,
        state: AgentState,
    ) -> dict[str, Any]:
        raise NotImplementedError
