import argparse

from agentkit.cli.commands.bootstrap import run_bootstrap
from agentkit.cli.commands.doctor import run_doctor
from agentkit.cli.commands.down import run_down
from agentkit.cli.commands.model import run_model


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentkit",
        description="A reusable Python runtime for AI agents and tool calling.",
    )

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser(
        "bootstrap",
        help="Validate and prepare the AgentKit environment.",
    )

    subparsers.add_parser(
        "doctor",
        help="Diagnose the AgentKit environment without changing it.",
    )

    subparsers.add_parser(
        "down",
        help="Stop local model runtime services used by AgentKit.",
    )

    model_parser = subparsers.add_parser(
        "model",
        help="Send a prompt directly to the configured model.",
    )
    model_parser.add_argument(
        "prompt",
        help="Prompt to send to the configured model.",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "bootstrap":
        raise SystemExit(run_bootstrap())

    if args.command == "doctor":
        raise SystemExit(run_doctor())

    if args.command == "down":
        raise SystemExit(run_down())

    if args.command == "model":
        raise SystemExit(run_model(args.prompt))

    parser.print_help()


if __name__ == "__main__":
    main()
    