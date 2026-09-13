from agentkit.tools.tool import Tool


class ToolRegistryError(RuntimeError):
    """Raised when a tool registry operation fails."""


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ToolRegistryError(
                f"Tool '{tool.name}' is already registered."
            )

        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        tool = self._tools.get(name)

        if tool is None:
            raise ToolRegistryError(
                f"Tool '{name}' is not registered."
            )

        return tool

    def all(self) -> tuple[Tool, ...]:
        return tuple(self._tools.values())
