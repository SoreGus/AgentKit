from agentkit.agents import AgentState, BeforeToolPolicy, PolicyDecision
from agentkit.tools import ToolCall


class WorkspaceToolPolicy(BeforeToolPolicy):
    def __init__(self, allowed_tools: tuple[str, ...]) -> None:
        self._allowed_tools = frozenset(allowed_tools)

    def evaluate_before_tool(
        self,
        state: AgentState,
        call: ToolCall,
    ) -> PolicyDecision:
        if call.name in self._allowed_tools:
            return PolicyDecision.allow()

        return PolicyDecision.reject(
            f"Tool '{call.name}' is not allowed by this workspace agent."
        )
