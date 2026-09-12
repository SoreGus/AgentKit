import argparse

from agentkit.bootstrap import BootstrapError, bootstrap
from agentkit.config import load_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentkit",
        description="A reusable Python runtime for AI agents and tool calling.",
    )

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser(
        "bootstrap",
        help="Validate the local AgentKit environment.",
    )

    return parser


def run_bootstrap() -> int:
    try:
        settings = load_settings()
        bootstrap(settings)
    except (BootstrapError, FileNotFoundError, ValueError) as error:
        print(f"Bootstrap failed: {error}")
        return 1

    print("AgentKit bootstrap completed successfully.")
    return 0


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "bootstrap":
        raise SystemExit(run_bootstrap())

    parser.print_help()


if __name__ == "__main__":
    main()
