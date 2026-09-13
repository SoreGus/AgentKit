from abc import abstractmethod
from typing import Any

from agentkit.agents.policy.after_tool import AfterToolPolicy
from agentkit.agents.policy.decision import PolicyDecision
from agentkit.agents.policy.model import ModelPolicy
from agentkit.agents.state import AgentState
from agentkit.models import Model
from agentkit.tools import ToolResult


class ModelAfterToolPolicy(ModelPolicy, AfterToolPolicy):
    def __init__(self, model: Model) -> None:
        ModelPolicy.__init__(self, model)

    def evaluate_after_tool(
        self,
        state: AgentState,
        result: ToolResult,
    ) -> PolicyDecision:
        return self.evaluate_with_model(
            instructions=self.review_instructions(state, result),
            payload=self.review_payload(state, result),
        )

    @abstractmethod
    def review_instructions(
        self,
        state: AgentState,
        result: ToolResult,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def review_payload(
        self,
        state: AgentState,
        result: ToolResult,
    ) -> dict[str, Any]:
        raise NotImplementedError
