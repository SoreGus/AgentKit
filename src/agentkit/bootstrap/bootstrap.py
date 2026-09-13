from dataclasses import dataclass

from agentkit.bootstrap.environment import validate_python
from agentkit.bootstrap.ollama import (
    OllamaError,
    ensure_model,
    ensure_ollama_installed,
    start_ollama,
    wait_for_ollama,
)
from agentkit.config import Settings


class BootstrapError(RuntimeError):
    """Raised when AgentKit bootstrap cannot complete."""


@dataclass(frozen=True, slots=True)
class BootstrapResult:
    python_version: str
    provider: str
    model: str
    provider_executable: str
    provider_started: bool


def bootstrap(settings: Settings) -> BootstrapResult:
    try:
        python_version = validate_python()

        if settings.model.provider != "ollama":
            raise BootstrapError(
                f"Unsupported model provider: {settings.model.provider}"
            )

        executable = ensure_ollama_installed()

        provider_started = start_ollama(
            executable=executable,
            host=settings.ollama.host,
        )

        wait_for_ollama(settings.ollama.host)

        ensure_model(
            executable=executable,
            host=settings.ollama.host,
            model_name=settings.model.name,
        )

        return BootstrapResult(
            python_version=python_version,
            provider=settings.model.provider,
            model=settings.model.name,
            provider_executable=executable,
            provider_started=provider_started,
        )

    except BootstrapError:
        raise
    except (RuntimeError, OllamaError) as error:
        raise BootstrapError(str(error)) from error
