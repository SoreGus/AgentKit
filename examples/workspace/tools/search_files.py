from agentkit.tools import Tool, ToolParameter, ToolParameterType, ToolSchema

from workspace import DEFAULT_MAX_RESULTS, Workspace


def create_search_files_tool(workspace: Workspace) -> Tool:
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

    return Tool(
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
    )
