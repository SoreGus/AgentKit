from agentkit.agents import PolicyAction
from agentkit.runtime import (
    ModelRequested,
    ModelResponded,
    PolicyEvaluated,
    RuntimeCompleted,
    RuntimeEvent,
    RuntimeStarted,
    ToolCalled,
    ToolCompleted,
)


def print_runtime_event(event: RuntimeEvent) -> None:
    if isinstance(event, RuntimeStarted):
        tools = ", ".join(event.tool_names) or "(none)"
        print(
            f"[runtime] started | agent: {event.agent_name} "
            f"| tools: {tools}"
        )
        return

    if isinstance(event, ModelRequested):
        print(
            f"[iteration {event.iteration}] model requested "
            f"| messages: {event.message_count}"
        )
        return

    if isinstance(event, ModelResponded):
        tool_count = len(event.response.tool_calls)

        if tool_count:
            print(
                f"[iteration {event.iteration}] model responded "
                f"| tool calls: {tool_count}"
            )
        else:
            print(
                f"[iteration {event.iteration}] model responded "
                "| final response candidate"
            )
        return

    if isinstance(event, ToolCalled):
        print(
            f"[iteration {event.iteration}] tool called "
            f"| {event.call.name} {event.call.arguments}"
        )
        return

    if isinstance(event, ToolCompleted):
        status = "error" if event.result.is_error else "ok"
        content = _compact(event.result.content)

        print(
            f"[iteration {event.iteration}] tool completed "
            f"| {event.result.name} | {status}"
        )
        print(f"  {content}")
        return

    if isinstance(event, PolicyEvaluated):
        action = event.decision.action.value
        print(
            f"[iteration {event.iteration}] policy "
            f"| {event.policy_name} | {action}"
        )

        if (
            event.decision.action != PolicyAction.ALLOW
            and event.decision.feedback
        ):
            print(f"  {event.decision.feedback}")

        return

    if isinstance(event, RuntimeCompleted):
        print(
            f"[runtime] completed | iterations: {event.iterations}"
        )


def _compact(content: str, limit: int = 500) -> str:
    compact = content.replace("\n", "\\n")

    if len(compact) <= limit:
        return compact

    return f"{compact[:limit]}..."
