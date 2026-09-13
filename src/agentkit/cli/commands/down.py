import os
import signal
import subprocess
import time

from agentkit.bootstrap.ollama import is_ollama_ready
from agentkit.config import load_settings


def run_down() -> int:
    try:
        settings = load_settings()
    except (FileNotFoundError, ValueError) as error:
        print(f"Down failed: {error}")
        return 1

    if settings.model.provider != "ollama":
        print(
            "Down failed: "
            f"unsupported model provider '{settings.model.provider}'."
        )
        return 1

    if not is_ollama_ready(settings.ollama.host):
        print("Ollama server: already stopped")
        return 0

    pids = _ollama_server_pids()

    if not pids:
        print(
            "Down failed: Ollama is responding, but AgentKit could not "
            "identify a local 'ollama serve' process safely."
        )
        return 1

    print("Stopping Ollama...")

    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            continue
        except PermissionError:
            print(f"Down failed: permission denied while stopping PID {pid}.")
            return 1

    if _wait_until_stopped(settings.ollama.host):
        print("Ollama server: stopped")
        return 0

    print("Down failed: Ollama did not stop within the expected time.")
    return 1


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
