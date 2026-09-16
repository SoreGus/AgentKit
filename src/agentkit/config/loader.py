from pathlib import Path
from typing import Any

from dotenv import load_dotenv
import yaml

from agentkit.config.settings import (
    ModelSettings,
    OllamaSettings,
    OpenAISettings,
    Settings,
)


DEFAULT_CONFIG_PATH = Path("config/default.yaml")


def load_settings(path: str | Path = DEFAULT_CONFIG_PATH) -> Settings:
    load_dotenv()

    config_path = Path(path)

    if not config_path.is_file():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}"
        )

    with config_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    if not isinstance(data, dict):
        raise ValueError("Configuration root must be a mapping.")

    model = _require_mapping(data, "model")
    ollama = _require_mapping(data, "ollama")
    openai = _require_mapping(data, "openai")

    return Settings(
        model=ModelSettings(
            provider=_require_string(
                model,
                "provider",
                "model",
            ),
            name=_require_string(
                model,
                "name",
                "model",
            ),
        ),
        ollama=OllamaSettings(
            host=_require_string(
                ollama,
                "host",
                "ollama",
            ),
        ),
        openai=OpenAISettings(
            api_key_env=_require_string(
                openai,
                "api_key_env",
                "openai",
            ),
        ),
    )


def _require_mapping(
    data: dict[str, Any],
    key: str,
) -> dict[str, Any]:
    value = data.get(key)

    if not isinstance(value, dict):
        raise ValueError(
            f"Configuration '{key}' must be a mapping."
        )

    return value


def _require_string(
    data: dict[str, Any],
    key: str,
    section: str,
) -> str:
    value = data.get(key)

    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"Configuration '{section}.{key}' "
            "must be a non-empty string."
        )

    return value
