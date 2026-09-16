from agentkit.tools import Tool, ToolParameter, ToolParameterType, ToolSchema

from workspace import Workspace


def create_read_file_tool(workspace: Workspace) -> Tool:
    def read_file(path: str) -> str:
        return workspace.read_text(path)

    return Tool(
        name="read_file",
        description="Reads a UTF-8 text file inside the workspace.",
        schema=ToolSchema(
            parameters={
                "path": ToolParameter(
                    type=ToolParameterType.STRING,
                    description="Workspace-relative file path.",
                ),
            }
        ),
        handler=read_file,
    )
