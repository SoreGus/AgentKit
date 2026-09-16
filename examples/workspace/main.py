import argparse
from pathlib import Path

from agentkit.agents import load_agent
from agentkit.models import get_default_model
from agentkit.runtime import AgentRuntime

from observer import print_model_policy_event, print_runtime_event
from tools import create_workspace_tools
from workspace import Workspace


PROJECT_ROOT = Path(__file__).resolve().parent


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
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Hide runtime events and print only the final answer.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    try:
        workspace = Workspace.open(args.workspace)
        model = get_default_model()
        tools = create_workspace_tools(workspace)

        agent = load_agent(
            "workspace",
            tools=tools,
            model=model,
            project_root=PROJECT_ROOT,
            on_model_policy_event=(
                None
                if args.quiet
                else print_model_policy_event
            ),
        )

        runtime = AgentRuntime(
            model=model,
            on_event=(
                None
                if args.quiet
                else print_runtime_event
            ),
        )

        result = runtime.run(
            agent=agent,
            prompt=args.prompt,
        )

    except RuntimeError as error:
        raise SystemExit(f"Error: {error}") from error

    if not args.quiet:
        print()
        print("FINAL RESPONSE")

    print(result.content)


if __name__ == "__main__":
    main()
