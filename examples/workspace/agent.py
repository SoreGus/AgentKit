from agentkit.agents import Agent
from agentkit.models import Model

from policies import (
    RequireFileEvidencePolicy,
    RetryToolErrorsPolicy,
    WorkspaceEvidenceReviewPolicy,
    WorkspaceToolPolicy,
)
from tools import create_workspace_tools
from workspace import Workspace


WORKSPACE_INSTRUCTIONS = """You are a read-only workspace assistant.
Use the available tools to inspect the workspace before making claims about its contents.
Search for relevant files, then read every file needed to support the claims in your answer.
Do not treat filenames, search snippets, or assumptions as sufficient evidence for implementation details.
Trace relationships across files when the question asks how configuration or data flows through the project.
You may list, search, read, and inspect files.
You cannot modify files or execute commands.
Keep the final answer concise and cite workspace-relative file paths when useful.
"""


def create_workspace_agent(
    workspace: Workspace,
    review_model: Model,
) -> Agent:
    tools = create_workspace_tools(workspace)
    tool_names = tuple(tool.name for tool in tools)

    return Agent(
        name="workspace",
        instructions=WORKSPACE_INSTRUCTIONS,
        tools=tools,
        completion_policies=(
            RequireFileEvidencePolicy(),
            WorkspaceEvidenceReviewPolicy(review_model),
        ),
        before_tool_policies=(WorkspaceToolPolicy(tool_names),),
        after_tool_policies=(RetryToolErrorsPolicy(),),
        max_iterations=10,
    )
