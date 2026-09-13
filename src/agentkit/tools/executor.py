from agentkit.tools.call import ToolCall
from agentkit.tools.registry import ToolRegistry, ToolRegistryError
from agentkit.tools.result import ToolResult


class ToolExecutor:
    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    def execute(self, call: ToolCall) -> ToolResult:
        try:
            tool = self._registry.get(call.name)
            value = tool.invoke(call.arguments)

            return ToolResult(
                call_id=call.id,
                name=call.name,
                content=str(value),
            )
        except (ToolRegistryError, TypeError, ValueError) as error:
            return ToolResult(
                call_id=call.id,
                name=call.name,
                content=str(error),
                is_error=True,
            )
        except Exception as error:
            return ToolResult(
                call_id=call.id,
                name=call.name,
                content=f"{type(error).__name__}: {error}",
                is_error=True,
            )
