from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from agentkit.tools.schema import ToolSchema


ToolHandler = Callable[..., Any]


@dataclass(frozen=True, slots=True)
class Tool:
    name: str
    description: str
    schema: ToolSchema
    handler: ToolHandler

    def invoke(self, arguments: dict[str, Any]) -> Any:
        return self.handler(**arguments)
