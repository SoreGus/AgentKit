from agentkit.config import load_settings
from agentkit.models import (
    MessageRole,
    ModelFactoryError,
    ModelMessage,
    ModelRequest,
    create_model,
)


def run_model(prompt: str) -> int:
    try:
        settings = load_settings()
        model = create_model(settings)

        request = ModelRequest(
            messages=(
                ModelMessage(
                    role=MessageRole.USER,
                    content=prompt,
                ),
            ),
        )

        response = model.generate(request)
    except (FileNotFoundError, ValueError, ModelFactoryError, RuntimeError) as error:
        print(f"Model request failed: {error}")
        return 1

    print(response.content)
    return 0
