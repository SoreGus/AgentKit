from agentkit.agents import AfterToolPolicy, AgentState, PolicyDecision
from agentkit.tools import ToolResult


class RetryToolErrorsPolicy(AfterToolPolicy):
    def evaluate_after_tool(
        self,
        state: AgentState,
        result: ToolResult,
    ) -> PolicyDecision:
        if not result.is_error:
            return PolicyDecision.allow()

        return PolicyDecision.retry(
            f"The tool '{result.name}' failed. Review the error, adjust the "
            "approach, and continue investigating instead of treating the "
            "failed result as evidence."
        )
