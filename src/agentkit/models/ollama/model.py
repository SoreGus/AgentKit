from typing import Any
from uuid import uuid4

from agentkit.models.model import Model
from agentkit.models.ollama.client import OllamaClient, OllamaClientError
from agentkit.models.request import ModelRequest
from agentkit.models.response import ModelResponse
from agentkit.tools import Tool, ToolCall


class OllamaModel(Model):
    def __init__(self, name: str, client: OllamaClient) -> None:
        self._name = name
        self._client = client

    def generate(self, request: ModelRequest) -> ModelResponse:
        messages = [
            {
                "role": message.role.value,
                "content": message.content,
            }
            for message in request.messages
        ]

        tools = [
            self._serialize_tool(tool)
            for tool in request.tools
        ]

        payload = self._client.chat(
            model=self._name,
            messages=messages,
            tools=tools,
        )

        message = payload.get("message")
        if not isinstance(message, dict):
            raise OllamaClientError(
                "Ollama response does not contain a valid message."
            )

        content = message.get("content", "")
        if not isinstance(content, str):
            raise OllamaClientError(
                "Ollama response message does not contain valid content."
            )

        tool_calls = self._parse_tool_calls(message.get("tool_calls"))

        return ModelResponse(
            content=content,
            tool_calls=tool_calls,
        )

    def _serialize_tool(self, tool: Tool) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.schema.to_json_schema(),
            },
        }

    def _parse_tool_calls(self, value: object) -> tuple[ToolCall, ...]:
        if value is None:
            return ()

        if not isinstance(value, list):
            raise OllamaClientError(
                "Ollama response contains invalid tool calls."
            )

        calls: list[ToolCall] = []

        for item in value:
            if not isinstance(item, dict):
                raise OllamaClientError(
                    "Ollama response contains an invalid tool call."
                )

            function = item.get("function")
            if not isinstance(function, dict):
                raise OllamaClientError(
                    "Ollama tool call does not contain a valid function."
                )

            name = function.get("name")
            arguments = function.get("arguments")

            if not isinstance(name, str) or not name:
                raise OllamaClientError(
                    "Ollama tool call does not contain a valid function name."
                )

            if not isinstance(arguments, dict):
                raise OllamaClientError(
                    "Ollama tool call does not contain valid arguments."
                )

            calls.append(
                ToolCall(
                    id=f"call_{uuid4().hex}",
                    name=name,
                    arguments=arguments,
                )
            )

        return tuple(calls)
