from calculator import calculator

from agentkit.tools import ToolCall, ToolExecutor, ToolRegistry


def main() -> None:
    registry = ToolRegistry()
    registry.register(calculator)

    executor = ToolExecutor(registry)

    call = ToolCall(
        id="call_1",
        name="calculator",
        arguments={
            "a": 10,
            "b": 20,
        },
    )

    result = executor.execute(call)

    print(result)


if __name__ == "__main__":
    main()
