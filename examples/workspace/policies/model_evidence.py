from typing import Any

from agentkit.agents import AgentState, ModelCompletionPolicy
from agentkit.models import MessageRole, Model


class WorkspaceEvidenceReviewPolicy(ModelCompletionPolicy):
    def __init__(self, model: Model) -> None:
        super().__init__(model)

    def review_instructions(
        self,
        state: AgentState,
    ) -> str:
        return """Decide whether the candidate answer is sufficiently supported by the workspace evidence actually collected.

Rules:
- Judge only the supplied tool evidence.
- Search results and filenames can identify what to inspect, but they do not prove implementation details.
- Claims about code behavior must be supported by contents of files that were actually read.
- If the task asks how configuration, data, or control flows across components, require evidence for the important links in that flow.
- Do not require an arbitrary number of files. Require only the evidence necessary to support the answer.
- If important claims remain unsupported, return retry and explain exactly what files or relationships should be inspected next.
- Return allow only when the candidate answer is adequately grounded in the collected evidence."""

    def review_payload(
        self,
        state: AgentState,
    ) -> dict[str, Any]:
        return {
            "task": self._original_prompt(state),
            "candidate_answer": (
                state.response.content
                if state.response is not None
                else ""
            ),
            "tool_evidence": self._tool_evidence(state),
        }

    def _original_prompt(self, state: AgentState) -> str:
        for message in state.messages:
            if message.role == MessageRole.USER:
                return message.content

        return ""

    def _tool_evidence(
        self,
        state: AgentState,
    ) -> list[dict[str, Any]]:
        results_by_call_id = {
            result.call_id: result
            for result in state.tool_results
        }

        evidence: list[dict[str, Any]] = []

        for call in state.tool_calls:
            result = results_by_call_id.get(call.id)

            if result is None:
                continue

            evidence.append(
                {
                    "tool": call.name,
                    "arguments": call.arguments,
                    "is_error": result.is_error,
                    "result": result.content,
                }
            )

        return evidence
