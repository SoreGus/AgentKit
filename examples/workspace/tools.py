from pathlib import Path

from agentkit.tools import (
    Tool,
    ToolParameter,
    ToolParameterType,
    ToolSchema,
)

from workspace import DEFAULT_MAX_RESULTS, Workspace, WorkspaceError


def create_workspace_tools(workspace: Workspace) -> tuple[Tool, ...]:
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

    def read_file(path: str) -> str:
        return workspace.read_text(path)

    def search_files(query: str, path: str = ".") -> str:
        if not query:
            raise ValueError("query must not be empty.")

        needle = query.casefold()
        results: list[str] = []

        for file_path in workspace.walk_files(path):
            if file_path.stat().st_size > workspace.max_file_bytes:
                continue

            try:
                text = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue

            relative = workspace.relative(file_path)

            for line_number, line in enumerate(text.splitlines(), start=1):
                if needle in line.casefold():
                    excerpt = line.strip()
                    if len(excerpt) > 240:
                        excerpt = f"{excerpt[:237]}..."

                    results.append(
                        f"{relative}:{line_number}: {excerpt}"
                    )

                    if len(results) >= DEFAULT_MAX_RESULTS:
                        return "\n".join(results)

        return "\n".join(results) or "(no matches)"

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

    return (
        Tool(
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
        ),
        Tool(
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
        ),
        Tool(
            name="search_files",
            description=(
                "Searches UTF-8 text files in the workspace for an exact "
                "case-insensitive text fragment and returns matching lines."
            ),
            schema=ToolSchema(
                parameters={
                    "query": ToolParameter(
                        type=ToolParameterType.STRING,
                        description="Text fragment to search for.",
                    ),
                    "path": ToolParameter(
                        type=ToolParameterType.STRING,
                        description="Workspace-relative path to search. Use '.' for the root.",
                        required=False,
                    ),
                }
            ),
            handler=search_files,
        ),
        Tool(
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
        ),
    )
