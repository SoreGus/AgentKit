import json
import urllib.error
import urllib.request
from typing import Any


class OllamaClientError(RuntimeError):
    pass


class OllamaClient:
    def __init__(self, host: str) -> None:
        self._host = host.rstrip("/")

    def chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
        }

        if tools:
            payload["tools"] = tools

        return self._post_json("/api/chat", payload)

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            f"{self._host}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                result = json.load(response)
        except urllib.error.HTTPError as error:
            raise OllamaClientError(
                f"Ollama HTTP error: {error.code}"
            ) from error
        except urllib.error.URLError as error:
            raise OllamaClientError(
                f"Could not connect to Ollama at {self._host}."
            ) from error
        except TimeoutError as error:
            raise OllamaClientError("Ollama request timed out.") from error
        except json.JSONDecodeError as error:
            raise OllamaClientError("Ollama returned invalid JSON.") from error

        if not isinstance(result, dict):
            raise OllamaClientError("Ollama returned an invalid response.")

        return result
