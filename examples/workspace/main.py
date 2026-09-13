import argparse

from agentkit.config import load_settings
from agentkit.models.ollama import OllamaClient, OllamaModel
from agentkit.runtime import AgentRuntime

from tools import create_workspace_tools
from workspace import Workspace


SYSTEM_PROMPT = """You are a read-only workspace assistant.
Use the available tools to inspect the workspace before making claims about its contents.
You may list, search, read, and inspect files.
You cannot modify files or execute commands.
Keep the final answer concise and cite workspace-relative file paths when useful.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run AgentKit against a local read-only workspace."
    )
    parser.add_argument(
        "workspace",
        help="Path to the workspace root.",
    )
    parser.add_argument(
        "prompt",
        help="Question or task for the workspace agent.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = load_settings()

    if settings.model.provider != "ollama":
        raise RuntimeError(
            f"Unsupported model provider: {settings.model.provider}"
        )

    workspace = Workspace.open(args.workspace)
    tools = create_workspace_tools(workspace)

    model = OllamaModel(
        name=settings.model.name,
        client=OllamaClient(host=settings.ollama.host),
    )

    runtime = AgentRuntime(
        model=model,
        tools=tools,
        max_iterations=10,
    )

    result = runtime.run(
        prompt=args.prompt,
        system_prompt=SYSTEM_PROMPT,
    )

    print(result.content)
    print()
    print(f"Iterations: {result.iterations}")


if __name__ == "__main__":
    main()
