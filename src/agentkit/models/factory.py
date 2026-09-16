import os

from agentkit.config import Settings, load_settings
from agentkit.models.model import Model


class ModelFactoryError(RuntimeError):
    pass


def create_model(settings: Settings) -> Model:
    provider = settings.model.provider.strip().lower()

    if provider == "ollama":
        from agentkit.models.ollama import OllamaClient, OllamaModel

        return OllamaModel(
            name=settings.model.name,
            client=OllamaClient(
                host=settings.ollama.host,
            ),
        )

    if provider == "openai":
        from agentkit.models.openai import OpenAIModel

        api_key = os.environ.get(
            settings.openai.api_key_env
        )

        if not api_key:
            raise ModelFactoryError(
                f"Environment variable "
                f"'{settings.openai.api_key_env}' "
                "is not set."
            )

        return OpenAIModel(
            name=settings.model.name,
            api_key=api_key,
        )

    raise ModelFactoryError(
        f"Unsupported model provider: "
        f"{settings.model.provider}"
    )


def get_default_model() -> Model:
    return create_model(
        load_settings()
    )