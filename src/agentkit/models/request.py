from dataclasses import dataclass
from enum import StrEnum

class MessageRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

@dataclass(frozen=True, slots=True)
class ModelMessage:
    role: MessageRole
    content: str

@dataclass(frozen=True, slots=True)
class ModelRequest:
    messages: tuple[ModelMessage, ...]
