from abc import abstractmethod
from typing import Any

from agentkit.agents.policy.before_tool import BeforeToolPolicy
from agentkit.agents.policy.decision import PolicyDecision
from agentkit.agents.policy.model import ModelPolicy
from agentkit.agents.state import AgentState
from agentkit.models import Model
from agentkit.tools import ToolCall


class ModelBeforeToolPolicy(ModelPolicy, BeforeToolPolicy):
    def __init__(self, model: Model) -> None:
        ModelPolicy.__init__(self, model)

    def evaluate_before_tool(
        self,
        state: AgentState,
        call: ToolCall,
    ) -> PolicyDecision:
        return self.evaluate_with_model(
            instructions=self.review_instructions(state, call),
            payload=self.review_payload(state, call),
        )

    @abstractmethod
    def review_instructions(
        self,
        state: AgentState,
        call: ToolCall,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def review_payload(
        self,
        state: AgentState,
        call: ToolCall,
    ) -> dict[str, Any]:
        raise NotImplementedError
