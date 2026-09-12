from agentkit.config import load_settings
from agentkit.models import MessageRole, ModelMessage, ModelRequest
from agentkit.models.ollama import OllamaClient, OllamaClientError, OllamaModel


def run_model(prompt: str) -> int:
    try:
        settings = load_settings()

        if settings.model.provider != "ollama":
            print(f"Unsupported model provider: {settings.model.provider}")
            return 1

        client = OllamaClient(
            host=settings.ollama.host,
        )

        model = OllamaModel(
            name=settings.model.name,
            client=client,
        )

        request = ModelRequest(
            messages=(
                ModelMessage(
                    role=MessageRole.USER,
                    content=prompt,
                ),
            ),
        )

        response = model.generate(request)
    except (FileNotFoundError, ValueError, OllamaClientError) as error:
        print(f"Model request failed: {error}")
        return 1

    print(response.content)
    return 0
