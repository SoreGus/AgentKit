from agentkit.agents import AgentState, CompletionPolicy, PolicyDecision


class RequireFileEvidencePolicy(CompletionPolicy):
    def evaluate_completion(
        self,
        state: AgentState,
    ) -> PolicyDecision:
        if state.successful_tool_results("read_file"):
            return PolicyDecision.allow()

        return PolicyDecision.retry(
            "You attempted to answer without reading any file contents. "
            "Read the relevant files before producing a final answer."
        )
