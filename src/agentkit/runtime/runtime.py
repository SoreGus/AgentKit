from dataclasses import dataclass

from agentkit.models import MessageRole, Model, ModelMessage, ModelRequest
from agentkit.tools import Tool, ToolCall, ToolExecutor, ToolRegistry, ToolResult


class AgentRuntimeError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class RuntimeResult:
    content: str
    messages: tuple[ModelMessage, ...]
    iterations: int


class AgentRuntime:
    def __init__(
        self,
        model: Model,
        tools: tuple[Tool, ...] = (),
        max_iterations: int = 10,
    ) -> None:
        if max_iterations < 1:
            raise ValueError("max_iterations must be at least 1.")

        self._model = model
        self._tools = tools
        self._max_iterations = max_iterations

        registry = ToolRegistry()
        for tool in tools:
            registry.register(tool)

        self._executor = ToolExecutor(registry)

    def run(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> RuntimeResult:
        messages: list[ModelMessage] = []

        if system_prompt:
            messages.append(
                ModelMessage(
                    role=MessageRole.SYSTEM,
                    content=system_prompt,
                )
            )

        messages.append(
            ModelMessage(
                role=MessageRole.USER,
                content=prompt,
            )
        )

        for iteration in range(1, self._max_iterations + 1):
            response = self._model.generate(
                ModelRequest(
                    messages=tuple(messages),
                    tools=self._tools,
                )
            )

            messages.append(
                ModelMessage(
                    role=MessageRole.ASSISTANT,
                    content=response.content,
                    tool_calls=response.tool_calls,
                )
            )

            if not response.tool_calls:
                return RuntimeResult(
                    content=response.content,
                    messages=tuple(messages),
                    iterations=iteration,
                )

            for call in response.tool_calls:
                result = self._executor.execute(call)
                messages.append(self._tool_result_message(result))

        raise AgentRuntimeError(
            f"Agent exceeded the maximum of {self._max_iterations} iterations."
        )

    def _tool_result_message(self, result: ToolResult) -> ModelMessage:
        return ModelMessage(
            role=MessageRole.TOOL,
            content=result.content,
            tool_name=result.name,
        )
