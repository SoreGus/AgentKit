from dataclasses import dataclass
from enum import StrEnum
from typing import Callable

from agentkit.models import ModelResponse
from agentkit.tools import ToolCall, ToolResult


class RuntimeEventType(StrEnum):
    RUNTIME_STARTED = "runtime_started"
    MODEL_REQUESTED = "model_requested"
    MODEL_RESPONDED = "model_responded"
    TOOL_CALLED = "tool_called"
    TOOL_COMPLETED = "tool_completed"
    RUNTIME_COMPLETED = "runtime_completed"


@dataclass(frozen=True, slots=True)
class RuntimeStarted:
    prompt: str
    tool_names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ModelRequested:
    iteration: int
    message_count: int


@dataclass(frozen=True, slots=True)
class ModelResponded:
    iteration: int
    response: ModelResponse


@dataclass(frozen=True, slots=True)
class ToolCalled:
    iteration: int
    call: ToolCall


@dataclass(frozen=True, slots=True)
class ToolCompleted:
    iteration: int
    result: ToolResult


@dataclass(frozen=True, slots=True)
class RuntimeCompleted:
    iterations: int
    content: str


RuntimeEvent = (
    RuntimeStarted
    | ModelRequested
    | ModelResponded
    | ToolCalled
    | ToolCompleted
    | RuntimeCompleted
)

RuntimeEventHandler = Callable[[RuntimeEvent], None]
