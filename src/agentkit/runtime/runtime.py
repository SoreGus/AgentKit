from dataclasses import dataclass

from agentkit.models import MessageRole, Model, ModelMessage, ModelRequest
from agentkit.runtime.event import (
    ModelRequested,
    ModelResponded,
    RuntimeCompleted,
    RuntimeEvent,
    RuntimeEventHandler,
    RuntimeStarted,
    ToolCalled,
    ToolCompleted,
)
from agentkit.tools import Tool, ToolExecutor, ToolRegistry, ToolResult


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
        on_event: RuntimeEventHandler | None = None,
    ) -> None:
        if max_iterations < 1:
            raise ValueError("max_iterations must be at least 1.")

        self._model = model
        self._tools = tools
        self._max_iterations = max_iterations
        self._on_event = on_event

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

        self._emit(
            RuntimeStarted(
                prompt=prompt,
                tool_names=tuple(tool.name for tool in self._tools),
            )
        )

        for iteration in range(1, self._max_iterations + 1):
            self._emit(
                ModelRequested(
                    iteration=iteration,
                    message_count=len(messages),
                )
            )

            response = self._model.generate(
                ModelRequest(
                    messages=tuple(messages),
                    tools=self._tools,
                )
            )

            self._emit(
                ModelResponded(
                    iteration=iteration,
                    response=response,
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
                result = RuntimeResult(
                    content=response.content,
                    messages=tuple(messages),
                    iterations=iteration,
                )

                self._emit(
                    RuntimeCompleted(
                        iterations=iteration,
                        content=response.content,
                    )
                )

                return result

            for call in response.tool_calls:
                self._emit(
                    ToolCalled(
                        iteration=iteration,
                        call=call,
                    )
                )

                tool_result = self._executor.execute(call)

                self._emit(
                    ToolCompleted(
                        iteration=iteration,
                        result=tool_result,
                    )
                )

                messages.append(self._tool_result_message(tool_result))

        raise AgentRuntimeError(
            f"Agent exceeded the maximum of {self._max_iterations} iterations."
        )

    def _emit(self, event: RuntimeEvent) -> None:
        if self._on_event is not None:
            self._on_event(event)

    def _tool_result_message(self, result: ToolResult) -> ModelMessage:
        return ModelMessage(
            role=MessageRole.TOOL,
            content=result.content,
            tool_name=result.name,
        )
