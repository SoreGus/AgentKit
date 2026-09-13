from agentkit.agents import AgentPolicy, AgentState, PolicyDecision


class RequireFileEvidencePolicy(AgentPolicy):
    def evaluate(self, state: AgentState) -> PolicyDecision:
        if state.completed_tool("read_file"):
            return PolicyDecision.allow()

        return PolicyDecision.retry(
            "You attempted to answer without reading any file contents. "
            "Use the available workspace tools to inspect the relevant files "
            "before producing a final answer."
        )
