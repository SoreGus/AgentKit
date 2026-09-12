import argparse


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        prog="agentkit",
        description="A reusable Python runtime for AI agents and tool calling.",
    )


def main() -> None:
    parser = build_parser()
    parser.parse_args()


if __name__ == "__main__":
    main()
