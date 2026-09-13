import os
import signal
import subprocess
import time

from agentkit.bootstrap.ollama import is_ollama_ready
from agentkit.config import Settings


class ShutdownError(RuntimeError):
    """Raised when AgentKit cannot safely stop the configured provider."""


def shutdown(settings: Settings) -> bool:
    """Stop the configured local model provider.

    Returns True when a running provider was stopped and False when it was
    already stopped.
    """
    if settings.model.provider != "ollama":
        raise ShutdownError(
            f"Unsupported model provider: {settings.model.provider}"
        )

    if not is_ollama_ready(settings.ollama.host):
        return False

    pids = _ollama_server_pids()

    if not pids:
        raise ShutdownError(
            "Ollama is responding, but AgentKit could not identify a local "
            "'ollama serve' process safely."
        )

    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            continue
        except PermissionError as error:
            raise ShutdownError(
                f"Permission denied while stopping Ollama PID {pid}."
            ) from error

    if not _wait_until_stopped(settings.ollama.host):
        raise ShutdownError(
            "Ollama did not stop within the expected time."
        )

    return True


def _ollama_server_pids() -> tuple[int, ...]:
    try:
        result = subprocess.run(
            ["pgrep", "-f", r"(^|/)ollama serve$"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return ()

    if result.returncode not in (0, 1):
        return ()

    pids: list[int] = []

    for line in result.stdout.splitlines():
        try:
            pid = int(line.strip())
        except ValueError:
            continue

        if pid != os.getpid():
            pids.append(pid)

    return tuple(pids)


def _wait_until_stopped(
    host: str,
    timeout: float = 10.0,
    interval: float = 0.25,
) -> bool:
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        if not is_ollama_ready(host):
            return True
        time.sleep(interval)

    return not is_ollama_ready(host)
