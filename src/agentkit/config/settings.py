from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModelSettings:
    provider: str
    name: str


@dataclass(frozen=True, slots=True)
class OllamaSettings:
    host: str


@dataclass(frozen=True, slots=True)
class Settings:
    model: ModelSettings
    ollama: OllamaSettings
