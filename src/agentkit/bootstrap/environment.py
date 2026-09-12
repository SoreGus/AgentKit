import sys


REQUIRED_PYTHON = (3, 14)


def validate_python() -> str:
    current = sys.version_info[:2]
    version = sys.version.split()[0]

    if current != REQUIRED_PYTHON:
        raise RuntimeError(
            "AgentKit requires Python 3.14. "
            f"Current version: {version}"
        )

    print(f"Python {version}: OK")
    return version
