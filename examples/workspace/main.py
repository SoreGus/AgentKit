import argparse

from agentkit.config import load_settings
from agentkit.models.ollama import OllamaClient, OllamaModel
from agentkit.runtime import AgentRuntime

from agent import create_workspace_agent
from observer import print_model_policy_event, print_runtime_event
from workspace import Workspace


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
    settings = load_settings()

    if settings.model.provider != "ollama":
        raise RuntimeError(
            f"Unsupported model provider: {settings.model.provider}"
        )

    workspace = Workspace.open(args.workspace)

    model = OllamaModel(
        name=settings.model.name,
        client=OllamaClient(host=settings.ollama.host),
    )

    agent = create_workspace_agent(
        workspace,
        review_model=model,
        on_model_policy_event=None if args.quiet else print_model_policy_event,
    )

    runtime = AgentRuntime(
        model=model,
        on_event=None if args.quiet else print_runtime_event,
    )

    result = runtime.run(
        agent=agent,
        prompt=args.prompt,
    )

    if not args.quiet:
        print()
        print("FINAL RESPONSE")

    print(result.content)


if __name__ == "__main__":
    main()
