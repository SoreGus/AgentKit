from dataclasses import dataclass

from agentkit.models import ModelMessage, ModelResponse
from agentkit.tools import ToolCall, ToolResult


@dataclass(frozen=True, slots=True)
class AgentState:
    messages: tuple[ModelMessage, ...]
    iteration: int
    tool_calls: tuple[ToolCall, ...] = ()
    tool_results: tuple[ToolResult, ...] = ()
    response: ModelResponse | None = None

    def called_tool(self, name: str) -> bool:
        return any(call.name == name for call in self.tool_calls)

    def completed_tool(self, name: str) -> bool:
        return any(result.name == name for result in self.tool_results)

    def successful_tool_results(
        self,
        name: str | None = None,
    ) -> tuple[ToolResult, ...]:
        return tuple(
            result
            for result in self.tool_results
            if not result.is_error
            and (name is None or result.name == name)
        )
