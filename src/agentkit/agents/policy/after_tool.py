from abc import ABC, abstractmethod

from agentkit.agents.policy.decision import PolicyDecision
from agentkit.agents.state import AgentState
from agentkit.tools import ToolResult


class AfterToolPolicy(ABC):
    @abstractmethod
    def evaluate_after_tool(
        self,
        state: AgentState,
        result: ToolResult,
    ) -> PolicyDecision:
        raise NotImplementedError
