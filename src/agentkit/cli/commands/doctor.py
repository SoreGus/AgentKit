import os
import shutil
import sys

from agentkit.bootstrap.ollama import is_model_installed, is_ollama_ready
from agentkit.config import load_settings


def run_doctor() -> int:
    print("AgentKit Doctor")
    print()

    healthy = True

    python_version = sys.version.split()[0]
    python_ok = sys.version_info[:2] == (3, 14)
    _print_status(f"Python {python_version}", python_ok)
    healthy = healthy and python_ok

    try:
        settings = load_settings()
        _print_status("Configuration", True)
    except (FileNotFoundError, ValueError) as error:
        _print_status("Configuration", False, str(error))
        return 1

    print(f"Model provider:      {settings.model.provider}")
    print(f"Configured model:    {settings.model.name}")

    provider = settings.model.provider.strip().lower()

    if provider == "ollama":
        healthy = _check_ollama(settings) and healthy
    elif provider == "openai":
        healthy = _check_openai(settings) and healthy
    else:
        _print_status(
            "Model provider",
            False,
            f"unsupported provider '{settings.model.provider}'",
        )
        healthy = False

    print()

    if healthy:
        print("AgentKit is ready.")
        return 0

    print("AgentKit has one or more issues.")
    return 1


def _check_ollama(settings) -> bool:
    healthy = True

    executable = shutil.which("ollama")
    executable_ok = executable is not None
    _print_status(
        "Ollama executable",
        executable_ok,
        executable or "not found",
    )
    healthy = healthy and executable_ok

    server_ready = is_ollama_ready(settings.ollama.host)
    _print_status(
        "Ollama API",
        server_ready,
        settings.ollama.host if server_ready else "not running",
    )
    healthy = healthy and server_ready

    if server_ready:
        try:
            model_installed = is_model_installed(
                settings.ollama.host,
                settings.model.name,
            )
        except Exception as error:
            _print_status("Configured model", False, str(error))
            healthy = False
        else:
            _print_status(
                f"Model {settings.model.name}",
                model_installed,
                "installed" if model_installed else "not installed",
            )
            healthy = healthy and model_installed
    else:
        _print_status(
            f"Model {settings.model.name}",
            False,
            "cannot check while Ollama is stopped",
        )
        healthy = False

    return healthy


def _check_openai(settings) -> bool:
    try:
        from openai import OpenAI  # noqa: F401
    except ImportError:
        package_ok = False
    else:
        package_ok = True
    _print_status(
        "OpenAI package",
        package_ok,
        "installed" if package_ok else "official package not installed",
    )

    variable = settings.openai.api_key_env
    api_key_ok = bool(os.environ.get(variable))
    _print_status(
        "OpenAI API key",
        api_key_ok,
        variable if api_key_ok else f"{variable} is not set",
    )

    return package_ok and api_key_ok


def _print_status(
    label: str,
    ok: bool,
    detail: str | None = None,
) -> None:
    status = "OK" if ok else "FAIL"
    suffix = f" ({detail})" if detail else ""
    print(f"{label + ':':<22} {status}{suffix}")
