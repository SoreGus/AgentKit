from pathlib import Path
from typing import Any

import yaml

from agentkit.config.settings import ModelSettings, OllamaSettings, Settings


DEFAULT_CONFIG_PATH = Path("config/default.yaml")


def load_settings(path: str | Path = DEFAULT_CONFIG_PATH) -> Settings:
    config_path = Path(path)

    if not config_path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    if not isinstance(data, dict):
        raise ValueError("Configuration root must be a mapping.")

    model = _require_mapping(data, "model")
    ollama = _require_mapping(data, "ollama")

    return Settings(
        model=ModelSettings(
            provider=_require_string(model, "provider", "model"),
            name=_require_string(model, "name", "model"),
        ),
        ollama=OllamaSettings(
            host=_require_string(ollama, "host", "ollama"),
        ),
    )


def _require_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)

    if not isinstance(value, dict):
        raise ValueError(f"Configuration '{key}' must be a mapping.")

    return value


def _require_string(data: dict[str, Any], key: str, section: str) -> str:
    value = data.get(key)

    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"Configuration '{section}.{key}' must be a non-empty string."
        )

    return value
