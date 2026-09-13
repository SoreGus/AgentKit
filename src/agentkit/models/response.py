from dataclasses import dataclass

from agentkit.tools import ToolCall


@dataclass(frozen=True, slots=True)
class ModelResponse:
    content: str
    tool_calls: tuple[ToolCall, ...] = ()
