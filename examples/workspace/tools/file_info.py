from agentkit.tools import Tool, ToolParameter, ToolParameterType, ToolSchema

from workspace import Workspace


def create_file_info_tool(workspace: Workspace) -> Tool:
    def file_info(path: str) -> str:
        target = workspace.resolve(path)
        stat = target.stat()
        kind = "directory" if target.is_dir() else "file"

        return "\n".join(
            (
                f"path: {workspace.relative(target) or '.'}",
                f"type: {kind}",
                f"size_bytes: {stat.st_size}",
                f"modified_timestamp: {stat.st_mtime}",
            )
        )

    return Tool(
        name="file_info",
        description="Returns metadata for a file or directory inside the workspace.",
        schema=ToolSchema(
            parameters={
                "path": ToolParameter(
                    type=ToolParameterType.STRING,
                    description="Workspace-relative file or directory path.",
                ),
            }
        ),
        handler=file_info,
    )
