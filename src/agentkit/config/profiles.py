from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


DEFAULT_AGENTS_DIRECTORY = Path("agents")
DEFAULT_POLICIES_DIRECTORY = Path("policies")


@dataclass(frozen=True, slots=True)
class PolicyMessagesConfig:
    allow: str = ""
    retry: str = ""
    reject: str = ""


@dataclass(frozen=True, slots=True)
class PolicyModelConfig:
    system_prompt: str = ""


@dataclass(frozen=True, slots=True)
class PolicyDefinition:
    name: str
    type: str
    enabled: bool = True
    max_retries: int | None = None
    strictness: str = "balanced"
    model: PolicyModelConfig | None = None
    messages: PolicyMessagesConfig = field(default_factory=PolicyMessagesConfig)
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PolicyProfile:
    name: str
    policies: tuple[PolicyDefinition, ...]


@dataclass(frozen=True, slots=True)
class AgentProfile:
    name: str
    instructions: str
    tools: tuple[str, ...]
    policy_profile: str | None = None
    max_iterations: int = 10


def load_policy_profile(
    name_or_path: str | Path,
    project_root: str | Path = ".",
) -> PolicyProfile:
    path = _resolve_profile_path(
        name_or_path=name_or_path,
        project_root=project_root,
        directory=DEFAULT_POLICIES_DIRECTORY,
    )
    data = _load_yaml_mapping(path)

    profile_section = data.get("profile", {})
    if profile_section is None:
        profile_section = {}
    if not isinstance(profile_section, dict):
        raise ValueError("Policy profile 'profile' must be a mapping.")

    default_name = path.stem
    profile_name = _optional_string(profile_section, "name") or default_name

    raw_policies = data.get("policies")
    if not isinstance(raw_policies, dict):
        raise ValueError("Policy profile 'policies' must be a mapping.")

    definitions = tuple(
        _parse_policy_definition(policy_name, raw_config)
        for policy_name, raw_config in raw_policies.items()
    )

    return PolicyProfile(
        name=profile_name,
        policies=definitions,
    )


def load_agent_profile(
    name_or_path: str | Path,
    project_root: str | Path = ".",
) -> AgentProfile:
    path = _resolve_profile_path(
        name_or_path=name_or_path,
        project_root=project_root,
        directory=DEFAULT_AGENTS_DIRECTORY,
    )
    data = _load_yaml_mapping(path)

    agent = data.get("agent", data)
    if not isinstance(agent, dict):
        raise ValueError("Agent profile must be a mapping.")

    name = _require_string(agent, "name", "agent")
    instructions = _require_string(agent, "instructions", "agent")

    raw_tools = agent.get("tools", [])
    if not isinstance(raw_tools, list) or not all(
        isinstance(item, str) and item.strip()
        for item in raw_tools
    ):
        raise ValueError("Agent profile 'tools' must be a list of tool names.")

    policy_profile = _optional_string(agent, "policy_profile")
    max_iterations = agent.get("max_iterations", 10)
    if not isinstance(max_iterations, int) or isinstance(max_iterations, bool):
        raise ValueError("Agent profile 'max_iterations' must be an integer.")
    if max_iterations < 1:
        raise ValueError("Agent profile 'max_iterations' must be at least 1.")

    return AgentProfile(
        name=name,
        instructions=instructions,
        tools=tuple(item.strip() for item in raw_tools),
        policy_profile=policy_profile,
        max_iterations=max_iterations,
    )


def _parse_policy_definition(
    name: object,
    raw_config: object,
) -> PolicyDefinition:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Policy names must be non-empty strings.")
    if not isinstance(raw_config, dict):
        raise ValueError(f"Policy '{name}' must be a mapping.")

    enabled = raw_config.get("enabled", True)
    if not isinstance(enabled, bool):
        raise ValueError(f"Policy '{name}.enabled' must be a boolean.")

    max_retries = raw_config.get("max_retries")
    if max_retries is not None:
        if not isinstance(max_retries, int) or isinstance(max_retries, bool):
            raise ValueError(f"Policy '{name}.max_retries' must be an integer.")
        if max_retries < 0:
            raise ValueError(f"Policy '{name}.max_retries' must be >= 0.")

    strictness = raw_config.get("strictness", "balanced")
    if not isinstance(strictness, str):
        raise ValueError(f"Policy '{name}.strictness' must be a string.")
    strictness = strictness.strip().lower()
    if strictness not in {"lenient", "balanced", "strict"}:
        raise ValueError(
            f"Policy '{name}.strictness' must be lenient, balanced, or strict."
        )

    explicit_type = raw_config.get("type")
    if explicit_type is None:
        policy_type = _infer_policy_type(name)
    elif isinstance(explicit_type, str) and explicit_type.strip():
        policy_type = explicit_type.strip().lower()
    else:
        raise ValueError(f"Policy '{name}.type' must be a non-empty string.")

    model_config = None
    raw_model = raw_config.get("model")
    if raw_model is not None:
        if not isinstance(raw_model, dict):
            raise ValueError(f"Policy '{name}.model' must be a mapping.")
        prompt = raw_model.get("system_prompt", "")
        if not isinstance(prompt, str):
            raise ValueError(
                f"Policy '{name}.model.system_prompt' must be a string."
            )
        model_config = PolicyModelConfig(system_prompt=prompt)

    raw_messages = raw_config.get("messages", {})
    if raw_messages is None:
        raw_messages = {}
    if not isinstance(raw_messages, dict):
        raise ValueError(f"Policy '{name}.messages' must be a mapping.")

    messages = PolicyMessagesConfig(
        allow=_message_value(raw_messages, "allow", name),
        retry=_message_value(raw_messages, "retry", name),
        reject=_message_value(raw_messages, "reject", name),
    )

    reserved = {
        "type",
        "enabled",
        "max_retries",
        "strictness",
        "model",
        "messages",
    }
    options = {
        key: value
        for key, value in raw_config.items()
        if key not in reserved
    }

    return PolicyDefinition(
        name=name.strip(),
        type=policy_type,
        enabled=enabled,
        max_retries=max_retries,
        strictness=strictness,
        model=model_config,
        messages=messages,
        options=options,
    )


def _infer_policy_type(name: str) -> str:
    aliases = {
        "require_file_evidence": "require_tool_success",
        "retry_tool_errors": "retry_tool_errors",
        "workspace_tool_policy": "allowed_tools",
        "workspace_evidence_review": "model_evidence_review",
    }
    inferred = aliases.get(name.strip().lower())
    if inferred is None:
        raise ValueError(
            f"Policy '{name}' must declare a 'type'."
        )
    return inferred


def _resolve_profile_path(
    name_or_path: str | Path,
    project_root: str | Path,
    directory: Path,
) -> Path:
    candidate = Path(name_or_path)

    if candidate.suffix.lower() in {".yaml", ".yml"} or candidate.parent != Path("."):
        path = candidate
        if not path.is_absolute():
            path = Path(project_root) / path
    else:
        yaml_path = Path(project_root) / directory / f"{candidate}.yaml"
        yml_path = Path(project_root) / directory / f"{candidate}.yml"
        path = yaml_path if yaml_path.is_file() else yml_path

    if not path.is_file():
        raise FileNotFoundError(f"Profile file not found: {path}")

    return path


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")

    return data


def _require_string(
    data: dict[str, Any],
    key: str,
    section: str,
) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"Configuration '{section}.{key}' must be a non-empty string."
        )
    return value.strip()


def _optional_string(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Configuration '{key}' must be a non-empty string.")
    return value.strip()


def _message_value(
    messages: dict[str, Any],
    key: str,
    policy_name: str,
) -> str:
    value = messages.get(key, "")
    if not isinstance(value, str):
        raise ValueError(
            f"Policy '{policy_name}.messages.{key}' must be a string."
        )
    return value.strip()
