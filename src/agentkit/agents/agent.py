from dataclasses import dataclass

from agentkit.agents.policy import (
    AfterToolPolicy,
    BeforeToolPolicy,
    CompletionPolicy,
)
from agentkit.tools import Tool


@dataclass(frozen=True, slots=True)
class Agent:
    name: str
    instructions: str
    tools: tuple[Tool, ...] = ()
    completion_policies: tuple[CompletionPolicy, ...] = ()
    before_tool_policies: tuple[BeforeToolPolicy, ...] = ()
    after_tool_policies: tuple[AfterToolPolicy, ...] = ()
    max_iterations: int = 10

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Agent name must not be empty.")

        if self.max_iterations < 1:
            raise ValueError("Agent max_iterations must be at least 1.")
