from agentkit.tools import Tool, ToolParameter, ToolParameterType, ToolSchema

from workspace import DEFAULT_MAX_RESULTS, Workspace, WorkspaceError


def create_list_files_tool(workspace: Workspace) -> Tool:
    def list_files(path: str = ".", recursive: bool = False) -> str:
        target = workspace.resolve(path)

        if target.is_file():
            return workspace.relative(target)

        if not target.is_dir():
            raise WorkspaceError(f"Not a directory: {path}")

        if recursive:
            items = [
                workspace.relative(item)
                for item in workspace.walk_files(path)
            ]
        else:
            items = []
            for item in sorted(target.iterdir(), key=lambda value: value.name):
                if item.name.startswith(".") or item.is_symlink():
                    continue

                resolved = item.resolve(strict=True)
                if not resolved.is_relative_to(workspace.root):
                    continue

                suffix = "/" if resolved.is_dir() else ""
                items.append(f"{workspace.relative(resolved)}{suffix}")

        return "\n".join(items[:DEFAULT_MAX_RESULTS]) or "(empty)"

    return Tool(
        name="list_files",
        description=(
            "Lists files and directories inside the workspace. "
            "Use recursive=true only when a recursive listing is needed."
        ),
        schema=ToolSchema(
            parameters={
                "path": ToolParameter(
                    type=ToolParameterType.STRING,
                    description="Workspace-relative directory path. Use '.' for the root.",
                    required=False,
                ),
                "recursive": ToolParameter(
                    type=ToolParameterType.BOOLEAN,
                    description="Whether to recursively list files.",
                    required=False,
                ),
            }
        ),
        handler=list_files,
    )
