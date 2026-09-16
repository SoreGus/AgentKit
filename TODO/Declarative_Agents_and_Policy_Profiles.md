# Declarative Agents and Policy Profiles

## Goal

Make AgentKit agents configurable primarily through YAML.

Applications using AgentKit should normally implement only their actual capabilities — the tools — in Python. Agent composition and policy behavior should be declarative.

```text
Tools     → Python behavior
Agents    → YAML composition
Policies  → YAML rules and configuration
```

AgentKit remains responsible for the runtime, generic policy implementations, validation, model interaction, tool execution, retries, and orchestration.

## Design Principle

> Python implements capabilities. YAML describes agent composition and policy behavior.

A project using AgentKit should not normally need to implement custom `BeforeToolPolicy`, `AfterToolPolicy`, `CompletionPolicy`, or model-policy subclasses.

Instead, AgentKit provides generic policy implementations configured through YAML.

## Suggested Project Structure

```text
project/
  main.py

  agents/
    workspace.yaml
    coding.yaml

  policies/
    workspace.yaml
    coding.yaml

  tools/
    __init__.py
    list_files.py
    read_file.py
    search_files.py
    file_info.py
```

`agents/` and `policies/` contain configuration only. `tools/` remains normal application Python code and can be organized however the application prefers.

## Tools

Tools remain implemented in Python because they contain executable behavior.

Each tool remains the source of truth for its own:

- name
- description
- parameter schema
- handler

For example, a tool can continue to be represented by AgentKit's existing `Tool` abstraction. No additional tool YAML is required.

Tools should be registered with AgentKit under stable logical names such as:

```text
list_files
read_file
search_files
file_info
```

The same registered tool may be referenced by multiple agents.

## Declarative Agents

An agent YAML describes composition rather than implementation.

Example:

```yaml
agent:
  name: workspace

  instructions: |
    You are a read-only workspace assistant.
    Inspect the workspace before making claims about its contents.
    Keep the final answer concise and grounded in inspected evidence.

  tools:
    - list_files
    - read_file
    - search_files
    - file_info

  policy_profile: workspace

  runtime:
    max_iterations: 10
```

AgentKit resolves the listed tool names against the application's registered tools.

The YAML should not reference Python classes, module paths, or handler method names. Those are implementation details owned by the tool registration layer.

## Declarative Policy Profiles

Policy profiles describe which generic AgentKit policies are active and how they behave.

Example:

```yaml
profile:
  name: workspace

policies:
  allowed_tools:
    enabled: true

  require_tool_success:
    enabled: true
    tool: read_file

  retry_tool_errors:
    enabled: true
    max_retries: 2

    messages:
      retry: |
        The tool failed. Review the failure, adjust the approach,
        and continue without treating the failed result as evidence.

  evidence_review:
    enabled: true
    max_retries: 2
    strictness: balanced

    model:
      system_prompt: |
        Review whether the candidate answer is sufficiently supported
        by the evidence actually collected.

        Require evidence for material claims, but do not require
        exhaustive inspection.

        Request additional evidence only when necessary to validate
        an important claim.

    messages:
      retry: |
        Some material claims are not sufficiently supported.
        Inspect only the additional evidence required and try again.

      reject: |
        The response cannot be adequately supported.

      allow: |
        The response is sufficiently supported.
```

## Generic AgentKit Policies

Instead of requiring applications to implement scenario-specific classes such as:

```text
RequireFileEvidencePolicy
RetryToolErrorsPolicy
WorkspaceToolPolicy
WorkspaceEvidenceReviewPolicy
```

AgentKit should provide reusable generic policies that can be parameterized by configuration.

Conceptually:

```text
AllowedToolsPolicy
RequireToolSuccessPolicy
RetryToolErrorsPolicy
ModelEvidenceReviewPolicy
```

A workspace agent can then configure `RequireToolSuccessPolicy` for `read_file`, while another agent could configure the same policy for a completely different tool.

## Deterministic and Model-Based Policies

AgentKit should continue supporting two categories internally.

### Deterministic policies

These use normal Python logic and do not require a model judgment.

Examples:

```text
Allow only tools assigned to the agent
Require a specific tool to succeed
Retry after a tool error
Require at least one successful tool execution
```

### Model-based policies

These use the AgentKit `Model` abstraction to evaluate contextual or subjective conditions.

Examples:

```text
Is the candidate answer sufficiently supported?
Was enough evidence collected?
Does the result satisfy the task requirements?
```

Their prompts, strictness, retry behavior, and feedback messages can be configured through YAML.

They must remain provider-independent and depend only on AgentKit abstractions such as `Model`, never directly on `OpenAIModel`, `OllamaModel`, or another provider implementation.

## Tool Resolution

AgentKit should not scan the project filesystem looking for tool implementations.

The consuming application registers its Python tools normally. When an agent profile is loaded, AgentKit resolves YAML tool names against that registry.

Conceptually:

```text
Application Python
      ↓
register tools
      ↓
ToolRegistry
      ↑
agent YAML references logical tool names
```

Missing or duplicate tool names should fail during configuration validation rather than during agent execution.

## Policy Resolution

AgentKit owns a registry of built-in generic policy types.

When a policy profile is loaded, AgentKit:

1. Loads and validates the YAML.
2. Resolves each configured policy type.
3. Applies its configuration.
4. Creates normal Python policy objects internally.
5. Assigns them to the correct lifecycle stage: before-tool, after-tool, or completion.

The existing policy interfaces remain valid internally.

## Retry Limits

Policy retries must be independent from the agent's general iteration limit.

For example:

```yaml
retry_tool_errors:
  max_retries: 2

evidence_review:
  max_retries: 2
```

is separate from:

```yaml
runtime:
  max_iterations: 10
```

This prevents one strict policy from repeatedly consuming the entire agent iteration budget.

Retry counters should be tracked by the runtime for each policy during the current agent run.

## Configuration Discovery

AgentKit should use a predictable project convention rather than recursively scanning the consuming project.

For example, from the project root:

```text
agents/
policies/
```

The application can then request an agent by logical name:

```python
agent = load_agent("workspace")
```

AgentKit resolves:

```text
agents/workspace.yaml
        ↓
policy_profile: workspace
        ↓
policies/workspace.yaml
```

An explicit configuration root may be supported when the application does not use the default structure, but the common case should require minimal setup.

## Application Bootstrap

The final application code should become small.

Conceptually:

```python
registry = ToolRegistry()
register_tools(registry)

agent = load_agent(
    "workspace",
    tool_registry=registry,
    model=model,
)

response = agent.run(prompt)
```

The exact public API can be refined during implementation, but the important property is that the application does not manually construct policy collections.

## Responsibilities

### Consuming application

Implements:

```text
Tool behavior
Tool registration
Application-specific models/runtime dependencies
Agent YAML
Policy YAML
```

### AgentKit

Implements:

```text
Agent runtime
Tool execution
Tool registry abstractions
Agent loading
Policy profile loading
Configuration validation
Generic deterministic policies
Generic model-based policies
Policy lifecycle integration
Independent policy retry counting
Model-policy prompting and parsing
Observability hooks
```

## Initial Scope

The first implementation should focus on:

- YAML agent definitions
- YAML policy profiles
- conventional `agents/` and `policies/` discovery
- tool-name resolution through the existing registry
- generic deterministic policies
- generic model-based policies
- `enabled`
- `max_retries`
- `strictness`
- configurable model-policy prompts
- configurable `allow`, `retry`, and `reject` messages
- profile loading and validation
- independent policy retry counting
- automatic construction of before-tool, after-tool, and completion policy collections

Do not introduce tool YAML in the initial implementation. Tool metadata and schemas remain owned by their Python `Tool` definitions.

## Future Extensions

Possible later additions include:

- profile inheritance
- per-agent policy overrides
- per-policy model overrides
- policy metrics
- plugin-based tool discovery
- explicit completion actions
- richer configuration composition

These should not complicate the initial implementation.

## Final Architecture

```text
                 Application
                     │
        ┌────────────┼────────────┐
        │            │            │
     Python         YAML         YAML
      Tools         Agents      Policies
        │            │            │
        └────────────┼────────────┘
                     ↓
                  AgentKit
                     │
          ┌──────────┼──────────┐
          │          │          │
       Runtime     Policies    Models
          │          │          │
          └──────────┼──────────┘
                     ↓
                  Agent Run
```

The consuming application defines what the agent can do through Python tools and describes how agents are composed and governed through YAML. AgentKit owns the reusable execution machinery behind both.
