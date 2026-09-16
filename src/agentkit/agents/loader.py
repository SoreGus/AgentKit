from dataclasses import dataclass
from pathlib import Path

from agentkit.agents.agent import Agent
from agentkit.agents.policy import (
    AfterToolPolicy,
    AllowedToolsPolicy,
    BeforeToolPolicy,
    CompletionPolicy,
    EvidenceReviewPolicy,
    ModelPolicyEventHandler,
    PolicyMessages,
    RequireToolCallPolicy,
    RequireToolSuccessPolicy,
    RetryToolErrorsPolicy,
)
from agentkit.config.profiles import (
    AgentProfile,
    PolicyDefinition,
    PolicyProfile,
    load_agent_profile,
    load_policy_profile,
)
from agentkit.models import Model
from agentkit.tools import Tool


@dataclass(frozen=True, slots=True)
class PolicyBundle:
    completion: tuple[CompletionPolicy, ...] = ()
    before_tool: tuple[BeforeToolPolicy, ...] = ()
    after_tool: tuple[AfterToolPolicy, ...] = ()


def load_agent(
    name_or_path: str | Path,
    tools: tuple[Tool, ...] | list[Tool],
    model: Model | None = None,
    project_root: str | Path = ".",
    on_model_policy_event: ModelPolicyEventHandler | None = None,
) -> Agent:
    profile = load_agent_profile(
        name_or_path=name_or_path,
        project_root=project_root,
    )

    selected_tools = _resolve_tools(profile, tuple(tools))
    bundle = PolicyBundle()

    if profile.policy_profile is not None:
        policy_profile = load_policy_profile(
            profile.policy_profile,
            project_root=project_root,
        )
        bundle = build_policy_bundle(
            profile=policy_profile,
            tools=selected_tools,
            model=model,
            on_model_policy_event=on_model_policy_event,
        )

    return Agent(
        name=profile.name,
        instructions=profile.instructions,
        tools=selected_tools,
        completion_policies=bundle.completion,
        before_tool_policies=bundle.before_tool,
        after_tool_policies=bundle.after_tool,
        max_iterations=profile.max_iterations,
    )


def build_policy_bundle(
    profile: PolicyProfile,
    tools: tuple[Tool, ...],
    model: Model | None = None,
    on_model_policy_event: ModelPolicyEventHandler | None = None,
) -> PolicyBundle:
    completion: list[CompletionPolicy] = []
    before_tool: list[BeforeToolPolicy] = []
    after_tool: list[AfterToolPolicy] = []

    tool_names = tuple(tool.name for tool in tools)

    for definition in profile.policies:
        if not definition.enabled:
            continue

        policy = _build_policy(
            definition=definition,
            agent_tool_names=tool_names,
            model=model,
            on_model_policy_event=on_model_policy_event,
        )

        if isinstance(policy, CompletionPolicy):
            completion.append(policy)
        if isinstance(policy, BeforeToolPolicy):
            before_tool.append(policy)
        if isinstance(policy, AfterToolPolicy):
            after_tool.append(policy)

    return PolicyBundle(
        completion=tuple(completion),
        before_tool=tuple(before_tool),
        after_tool=tuple(after_tool),
    )


def _resolve_tools(
    profile: AgentProfile,
    available_tools: tuple[Tool, ...],
) -> tuple[Tool, ...]:
    by_name: dict[str, Tool] = {}

    for tool in available_tools:
        if tool.name in by_name:
            raise ValueError(f"Duplicate available tool name: '{tool.name}'.")
        by_name[tool.name] = tool

    selected: list[Tool] = []
    for name in profile.tools:
        tool = by_name.get(name)
        if tool is None:
            raise ValueError(
                f"Agent '{profile.name}' references unknown tool '{name}'."
            )
        selected.append(tool)

    return tuple(selected)


def _build_policy(
    definition: PolicyDefinition,
    agent_tool_names: tuple[str, ...],
    model: Model | None,
    on_model_policy_event: ModelPolicyEventHandler | None,
) -> object:
    policy_type = definition.type
    messages = PolicyMessages(
        allow=definition.messages.allow,
        retry=definition.messages.retry,
        reject=definition.messages.reject,
    )

    if policy_type == "allowed_tools":
        configured_tools = _tool_names_option(
            definition,
            default=agent_tool_names,
        )
        _validate_referenced_tools(
            policy_name=definition.name,
            referenced=configured_tools,
            available=agent_tool_names,
        )
        return AllowedToolsPolicy(
            allowed_tools=configured_tools,
            policy_name=definition.name,
            max_retries=definition.max_retries,
            messages=messages,
        )

    if policy_type == "retry_tool_errors":
        return RetryToolErrorsPolicy(
            policy_name=definition.name,
            max_retries=definition.max_retries,
            messages=messages,
        )

    if policy_type in {"require_tool_success", "require_file_evidence"}:
        default = ("read_file",) if definition.name == "require_file_evidence" else ()
        configured_tools = _tool_names_option(definition, default=default)
        _validate_referenced_tools(
            policy_name=definition.name,
            referenced=configured_tools,
            available=agent_tool_names,
        )
        return RequireToolSuccessPolicy(
            tool_names=configured_tools,
            mode=_mode_option(definition),
            policy_name=definition.name,
            max_retries=definition.max_retries,
            messages=messages,
        )

    if policy_type == "require_tool_call":
        configured_tools = _tool_names_option(definition, default=())
        _validate_referenced_tools(
            policy_name=definition.name,
            referenced=configured_tools,
            available=agent_tool_names,
        )
        return RequireToolCallPolicy(
            tool_names=configured_tools,
            mode=_mode_option(definition),
            policy_name=definition.name,
            max_retries=definition.max_retries,
            messages=messages,
        )

    if policy_type in {"model_evidence_review", "workspace_evidence_review"}:
        if model is None:
            raise ValueError(
                f"Policy '{definition.name}' requires a Model instance."
            )

        system_prompt = (
            definition.model.system_prompt
            if definition.model is not None
            else ""
        )
        return EvidenceReviewPolicy(
            model=model,
            system_prompt=system_prompt,
            strictness=definition.strictness,
            policy_name=definition.name,
            max_retries=definition.max_retries,
            messages=messages,
            on_model_event=on_model_policy_event,
        )

    raise ValueError(
        f"Unsupported policy type '{policy_type}' "
        f"for policy '{definition.name}'."
    )


def _tool_names_option(
    definition: PolicyDefinition,
    default: tuple[str, ...],
) -> tuple[str, ...]:
    raw = definition.options.get("tools")
    if raw is None:
        raw = definition.options.get("tool_names")

    if raw is None:
        if default:
            return default
        raise ValueError(
            f"Policy '{definition.name}' requires a non-empty 'tools' list."
        )

    if not isinstance(raw, list) or not raw or not all(
        isinstance(item, str) and item.strip()
        for item in raw
    ):
        raise ValueError(
            f"Policy '{definition.name}.tools' must be a non-empty list of names."
        )

    return tuple(item.strip() for item in raw)


def _mode_option(definition: PolicyDefinition) -> str:
    raw = definition.options.get("mode", "any")
    if not isinstance(raw, str):
        raise ValueError(f"Policy '{definition.name}.mode' must be a string.")
    mode = raw.strip().lower()
    if mode not in {"any", "all"}:
        raise ValueError(
            f"Policy '{definition.name}.mode' must be 'any' or 'all'."
        )
    return mode


def _validate_referenced_tools(
    policy_name: str,
    referenced: tuple[str, ...],
    available: tuple[str, ...],
) -> None:
    available_set = set(available)
    unknown = [name for name in referenced if name not in available_set]
    if unknown:
        formatted = ", ".join(unknown)
        raise ValueError(
            f"Policy '{policy_name}' references tools not available to the agent: "
            f"{formatted}."
        )
