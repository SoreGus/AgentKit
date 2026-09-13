from abc import ABC, abstractmethod

from agentkit.agents.policy.decision import PolicyDecision
from agentkit.agents.state import AgentState
from agentkit.tools import ToolCall


class BeforeToolPolicy(ABC):
    @abstractmethod
    def evaluate_before_tool(
        self,
        state: AgentState,
        call: ToolCall,
    ) -> PolicyDecision:
        raise NotImplementedError
