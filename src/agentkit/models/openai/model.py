import json
from typing import Any

from agentkit.models.model import Model
from agentkit.models.request import MessageRole, ModelMessage, ModelRequest
from agentkit.models.response import ModelResponse
from agentkit.tools import Tool, ToolCall


class OpenAIModelError(RuntimeError):
    pass


class OpenAIModel(Model):
    def __init__(
        self,
        name: str,
        api_key: str,
    ) -> None:
        try:
            import openai
            from openai import OpenAI
        except ImportError as error:
            raise OpenAIModelError(
                "OpenAI provider requires the 'openai' package."
            ) from error

        self._openai = openai
        self._name = name
        self._client = OpenAI(
            api_key=api_key,
        )

    def generate(
        self,
        request: ModelRequest,
    ) -> ModelResponse:
        try:
            response = self._client.responses.create(
                model=self._name,
                input=self._serialize_messages(
                    request.messages
                ),
                tools=[
                    self._serialize_tool(tool)
                    for tool in request.tools
                ],
                store=False,
            )

        except self._openai.AuthenticationError as error:
            raise OpenAIModelError(
                "OpenAI authentication failed. "
                "Check OPENAI_API_KEY in your .env file."
            ) from error

        except self._openai.RateLimitError as error:
            raise OpenAIModelError(
                "OpenAI request was rate limited. "
                "Check your API usage, credits, and rate limits."
            ) from error

        except self._openai.APITimeoutError as error:
            raise OpenAIModelError(
                "OpenAI request timed out."
            ) from error

        except self._openai.APIConnectionError as error:
            raise OpenAIModelError(
                "Could not connect to the OpenAI API. "
                "Check your internet connection."
            ) from error

        except self._openai.PermissionDeniedError as error:
            raise OpenAIModelError(
                "OpenAI denied access to this request. "
                "Check the API key permissions and model access."
            ) from error

        except self._openai.NotFoundError as error:
            raise OpenAIModelError(
                f"OpenAI resource or model '{self._name}' was not found."
            ) from error

        except self._openai.BadRequestError as error:
            raise OpenAIModelError(
                f"OpenAI rejected the request: {error.message}"
            ) from error

        except self._openai.APIStatusError as error:
            raise OpenAIModelError(
                f"OpenAI request failed with HTTP "
                f"{error.status_code}: {error.message}"
            ) from error

        except self._openai.APIError as error:
            raise OpenAIModelError(
                f"OpenAI request failed: {error}"
            ) from error

        return ModelResponse(
            content=response.output_text or "",
            tool_calls=self._parse_tool_calls(
                response.output
            ),
        )

    def _serialize_messages(
        self,
        messages: tuple[ModelMessage, ...],
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []

        for message in messages:
            if message.role == MessageRole.TOOL:
                if not message.tool_call_id:
                    raise OpenAIModelError(
                        "Tool messages require a tool_call_id."
                    )

                items.append(
                    {
                        "type": "function_call_output",
                        "call_id": message.tool_call_id,
                        "output": message.content,
                    }
                )

                continue

            if message.content:
                items.append(
                    {
                        "role": message.role.value,
                        "content": message.content,
                    }
                )

            for call in message.tool_calls:
                items.append(
                    {
                        "type": "function_call",
                        "call_id": call.id,
                        "name": call.name,
                        "arguments": json.dumps(
                            call.arguments
                        ),
                    }
                )

        return items

    def _serialize_tool(
        self,
        tool: Tool,
    ) -> dict[str, Any]:
        return {
            "type": "function",
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.schema.to_json_schema(),
        }

    def _parse_tool_calls(
        self,
        output: object,
    ) -> tuple[ToolCall, ...]:
        if not isinstance(output, list):
            try:
                output = list(output)
            except TypeError as error:
                raise OpenAIModelError(
                    "OpenAI response contains invalid output."
                ) from error

        calls: list[ToolCall] = []

        for item in output:
            item_type = getattr(
                item,
                "type",
                None,
            )

            if item_type != "function_call":
                continue

            call_id = getattr(
                item,
                "call_id",
                None,
            )
            name = getattr(
                item,
                "name",
                None,
            )
            arguments_json = getattr(
                item,
                "arguments",
                None,
            )

            if not isinstance(call_id, str) or not call_id:
                raise OpenAIModelError(
                    "OpenAI function call does not contain "
                    "a valid call_id."
                )

            if not isinstance(name, str) or not name:
                raise OpenAIModelError(
                    "OpenAI function call does not contain "
                    "a valid name."
                )

            if not isinstance(arguments_json, str):
                raise OpenAIModelError(
                    "OpenAI function call does not contain "
                    "valid arguments."
                )

            try:
                arguments = json.loads(
                    arguments_json
                )
            except json.JSONDecodeError as error:
                raise OpenAIModelError(
                    "OpenAI function call arguments "
                    "are invalid JSON."
                ) from error

            if not isinstance(arguments, dict):
                raise OpenAIModelError(
                    "OpenAI function call arguments "
                    "must be a JSON object."
                )

            calls.append(
                ToolCall(
                    id=call_id,
                    name=name,
                    arguments=arguments,
                )
            )

        return tuple(calls)
    