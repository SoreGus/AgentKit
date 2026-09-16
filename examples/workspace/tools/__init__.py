from agentkit.tools import Tool

from tools.file_info import create_file_info_tool
from tools.list_files import create_list_files_tool
from tools.read_file import create_read_file_tool
from tools.search_files import create_search_files_tool
from workspace import Workspace


def create_workspace_tools(workspace: Workspace) -> tuple[Tool, ...]:
    return (
        create_list_files_tool(workspace),
        create_read_file_tool(workspace),
        create_search_files_tool(workspace),
        create_file_info_tool(workspace),
    )


__all__ = ["create_workspace_tools"]
