import os

from agentkit.config import Settings


class OpenAIEnvironmentError(RuntimeError):
    pass


def validate_openai_environment(settings: Settings) -> None:
    try:
        from openai import OpenAI
    except ImportError as error:
        raise OpenAIEnvironmentError(
            "OpenAI provider requires the official 'openai' package."
        ) from error

    variable = settings.openai.api_key_env

    if not os.environ.get(variable):
        raise OpenAIEnvironmentError(
            f"Environment variable '{variable}' is not set."
        )
