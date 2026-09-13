from agentkit.agents import Agent

from policy import RequireFileEvidencePolicy
from tools import create_workspace_tools
from workspace import Workspace


WORKSPACE_INSTRUCTIONS = """You are a read-only workspace assistant.
Use the available tools to inspect the workspace before making claims about its contents.
Search for relevant files and read the files needed to support implementation claims.
You may list, search, read, and inspect files.
You cannot modify files or execute commands.
Keep the final answer concise and cite workspace-relative file paths when useful.
"""


def create_workspace_agent(workspace: Workspace) -> Agent:
    return Agent(
        name="workspace",
        instructions=WORKSPACE_INSTRUCTIONS,
        tools=create_workspace_tools(workspace),
        policies=(RequireFileEvidencePolicy(),),
        max_iterations=10,
    )
