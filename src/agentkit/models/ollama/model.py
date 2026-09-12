from agentkit.models.model import Model
from agentkit.models.ollama.client import OllamaClient, OllamaClientError
from agentkit.models.request import ModelRequest
from agentkit.models.response import ModelResponse

class OllamaModel(Model):
    def __init__(self, name: str, client: OllamaClient) -> None:
        self._name = name
        self._client = client

    def generate(self, request: ModelRequest) -> ModelResponse:
        messages = [
            {"role": message.role.value, "content": message.content}
            for message in request.messages
        ]
        payload = self._client.chat(self._name, messages)
        message = payload.get("message")
        if not isinstance(message, dict):
            raise OllamaClientError("Ollama response does not contain a valid message.")
        content = message.get("content")
        if not isinstance(content, str):
            raise OllamaClientError("Ollama response message does not contain valid content.")
        return ModelResponse(content=content)
