from agentkit.tools import (
    Tool,
    ToolParameter,
    ToolParameterType,
    ToolSchema,
)


def add(a: int, b: int) -> int:
    return a + b


calculator = Tool(
    name="calculator",
    description="Adds two integer numbers.",
    schema=ToolSchema(
        parameters={
            "a": ToolParameter(
                type=ToolParameterType.INTEGER,
                description="First integer.",
            ),
            "b": ToolParameter(
                type=ToolParameterType.INTEGER,
                description="Second integer.",
            ),
        }
    ),
    handler=add,
)
