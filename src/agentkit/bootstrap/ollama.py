import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import urllib.error
import urllib.request


class OllamaError(RuntimeError):
    """Raised when the Ollama runtime cannot be prepared."""


def find_ollama() -> str | None:
    return shutil.which("ollama")


def install_ollama() -> str:
    if sys_platform() != "darwin":
        raise OllamaError(
            "Automatic Ollama installation is currently supported only on macOS."
        )

    brew = shutil.which("brew")

    if brew is None:
        raise OllamaError(
            "Homebrew is required to install Ollama automatically on macOS."
        )

    print("Ollama is not installed.")
    print("Installing Ollama with Homebrew...")

    _run([brew, "install", "ollama"])

    executable = find_ollama()

    if executable is None:
        raise OllamaError(
            "Ollama installation completed, but the executable was not found in PATH."
        )

    print(f"Ollama executable: {executable}")
    return executable


def ensure_ollama_installed() -> str:
    executable = find_ollama()

    if executable is not None:
        print(f"Ollama executable: {executable}")
        return executable

    return install_ollama()


def is_ollama_ready(host: str, timeout: float = 1.0) -> bool:
    try:
        _request_json(host, "/api/tags", timeout=timeout)
        return True
    except OllamaError:
        return False


def start_ollama(executable: str, host: str) -> None:
    if is_ollama_ready(host):
        return

    print("Ollama server: stopped")
    print("Starting Ollama...")

    log_path = Path.home() / ".agentkit" / "logs" / "ollama.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    log_file = log_path.open("ab")

    try:
        subprocess.Popen(
            [executable, "serve"],
            stdin=subprocess.DEVNULL,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            env=os.environ.copy(),
        )
    except OSError as error:
        log_file.close()
        raise OllamaError("Could not start Ollama.") from error

    log_file.close()


def wait_for_ollama(
    host: str,
    timeout: float = 30.0,
    interval: float = 0.5,
) -> None:
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        if is_ollama_ready(host):
            print("Ollama server: OK")
            return

        time.sleep(interval)

    raise OllamaError(
        f"Ollama did not become ready within {timeout:.0f} seconds."
    )


def list_models(host: str) -> set[str]:
    payload = _request_json(host, "/api/tags", timeout=5.0)
    models = payload.get("models")

    if not isinstance(models, list):
        raise OllamaError(
            "Ollama returned an invalid model list."
        )

    names: set[str] = set()

    for model in models:
        if not isinstance(model, dict):
            continue

        name = model.get("name")

        if isinstance(name, str) and name:
            names.add(name)

    return names


def is_model_installed(host: str, model_name: str) -> bool:
    models = list_models(host)

    if model_name in models:
        return True

    if ":" not in model_name:
        return f"{model_name}:latest" in models

    return False


def pull_model(executable: str, model_name: str) -> None:
    print(f"Model {model_name}: not installed")
    print(f"Pulling {model_name}...")

    _run([executable, "pull", model_name])


def ensure_model(
    executable: str,
    host: str,
    model_name: str,
) -> None:
    print(f"Model {model_name}: checking...")

    if is_model_installed(host, model_name):
        print(f"Model {model_name}: OK")
        return

    pull_model(executable, model_name)

    if not is_model_installed(host, model_name):
        raise OllamaError(
            f"Model '{model_name}' was pulled but is still unavailable."
        )

    print(f"Model {model_name}: OK")


def _request_json(
    host: str,
    path: str,
    timeout: float,
) -> dict[str, object]:
    url = f"{host.rstrip('/')}{path}"
    request = urllib.request.Request(url, method="GET")

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except (
        urllib.error.URLError,
        TimeoutError,
        json.JSONDecodeError,
    ) as error:
        raise OllamaError(
            f"Could not connect to Ollama at {host}."
        ) from error

    if not isinstance(payload, dict):
        raise OllamaError(
            "Ollama returned an invalid response."
        )

    return payload


def _run(command: list[str]) -> None:
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as error:
        raise OllamaError(
            f"Command failed with exit code {error.returncode}: "
            f"{' '.join(command)}"
        ) from error
    except OSError as error:
        raise OllamaError(
            f"Could not execute command: {' '.join(command)}"
        ) from error


def sys_platform() -> str:
    import sys

    return sys.platform
