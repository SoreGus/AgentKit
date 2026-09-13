from agentkit.bootstrap import ShutdownError, shutdown
from agentkit.config import load_settings


def run_down() -> int:
    try:
        settings = load_settings()
        stopped = shutdown(settings)
    except (FileNotFoundError, ValueError, ShutdownError) as error:
        print(f"Down failed: {error}")
        return 1

    if stopped:
        print("Ollama server: stopped")
    else:
        print("Ollama server: already stopped")

    return 0
