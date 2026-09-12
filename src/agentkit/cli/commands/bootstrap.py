from agentkit.bootstrap import BootstrapError, bootstrap
from agentkit.config import load_settings


def run_bootstrap() -> int:
    try:
        settings = load_settings()
        bootstrap(settings)
    except (BootstrapError, FileNotFoundError, ValueError) as error:
        print(f"Bootstrap failed: {error}")
        return 1

    print("AgentKit bootstrap completed successfully.")
    return 0
