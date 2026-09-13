from pathlib import Path
import sys

from agentkit.config import load_settings
from agentkit.models import MessageRole, ModelMessage, ModelRequest
from agentkit.models.ollama import OllamaClient, OllamaModel
from agentkit.tools import ToolExecutor, ToolRegistry


EXAMPLES_DIR = Path(__file__).resolve().parents[1]
TOOLS_DIR = EXAMPLES_DIR / "tools"

if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from calculator import calculator


def main() -> None:
    settings = load_settings()

    client = OllamaClient(host=settings.ollama.host)
    model = OllamaModel(
        name=settings.model.name,
        client=client,
    )

    request = ModelRequest(
        messages=(
            ModelMessage(
                role=MessageRole.SYSTEM,
                content=(
                    "Use an available tool when it is appropriate. "
                    "Do not calculate arithmetic yourself when the calculator tool can do it."
                ),
            ),
            ModelMessage(
                role=MessageRole.USER,
                content="What is 37 + 58?",
            ),
        ),
        tools=(calculator,),
    )

    response = model.generate(request)

    print(f"Model content: {response.content!r}")
    print(f"Tool calls: {len(response.tool_calls)}")

    if not response.tool_calls:
        print("The model did not request a tool.")
        return

    registry = ToolRegistry()
    registry.register(calculator)

    executor = ToolExecutor(registry)

    for call in response.tool_calls:
        print()
        print("Model requested tool:")
        print(f"  id: {call.id}")
        print(f"  name: {call.name}")
        print(f"  arguments: {call.arguments}")

        result = executor.execute(call)

        print("Tool result:")
        print(f"  content: {result.content}")
        print(f"  is_error: {result.is_error}")


if __name__ == "__main__":
    main()
