from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class ToolParameterType(StrEnum):
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


@dataclass(frozen=True, slots=True)
class ToolParameter:
    type: ToolParameterType
    description: str
    required: bool = True


@dataclass(frozen=True, slots=True)
class ToolSchema:
    parameters: dict[str, ToolParameter]

    def to_json_schema(self) -> dict[str, Any]:
        properties = {
            name: {
                "type": parameter.type.value,
                "description": parameter.description,
            }
            for name, parameter in self.parameters.items()
        }

        required = [
            name
            for name, parameter in self.parameters.items()
            if parameter.required
        ]

        schema: dict[str, Any] = {
            "type": "object",
            "properties": properties,
        }

        if required:
            schema["required"] = required

        return schema
