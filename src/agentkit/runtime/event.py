from dataclasses import dataclass
from typing import Callable

from agentkit.agents import PolicyDecision
from agentkit.models import ModelResponse
from agentkit.tools import ToolCall, ToolResult


@dataclass(frozen=True, slots=True)
class RuntimeStarted:
    agent_name: str
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
class PolicyEvaluated:
    iteration: int
    policy_name: str
    decision: PolicyDecision


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
    | PolicyEvaluated
    | RuntimeCompleted
)

RuntimeEventHandler = Callable[[RuntimeEvent], None]
