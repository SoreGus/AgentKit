# Configurable Policy Profiles

## Goal

Add declarative policy configuration to AgentKit so policy behavior can be changed without modifying Python code.

Policies remain implemented in Python. YAML defines:

- Whether a policy is enabled
- Retry limits
- Strictness
- Model-based policy prompts
- `allow`, `retry`, and `reject` messages

## Structure

```text
config/
  policies/
    workspace.yaml
    coding.yaml
    research.yaml
```

Each agent can use a policy profile appropriate to its scenario.

## Example

```yaml
profile:
  name: workspace

policies:
  require_file_evidence:
    enabled: true

  retry_tool_errors:
    enabled: true
    max_retries: 2

  workspace_evidence_review:
    enabled: true
    max_retries: 2
    strictness: balanced

    model:
      system_prompt: |
        Review whether the candidate answer is sufficiently supported
        by the inspected workspace evidence.

        Require evidence for material claims, but do not require
        exhaustive repository inspection.

        Do not request peripheral files unless they are necessary
        to validate an important claim.

    messages:
      retry: |
        Some material claims are not sufficiently supported.
        Inspect only the additional evidence required and try again.

      reject: |
        The response cannot be adequately supported.

      allow: |
        The response is sufficiently supported.
```

## Policy Types

AgentKit should distinguish between:

```text
Deterministic policies
  RequireFileEvidencePolicy
  RetryToolErrorsPolicy
  WorkspaceToolPolicy

Model-based policies
  WorkspaceEvidenceReviewPolicy
```

Deterministic policies use normal Python rules.

Model-based policies may additionally receive a configurable prompt and feedback messages.

## Retry Limits

Policy retries should be independent from:

```python
Agent(max_iterations=10)
```

For example:

```yaml
workspace_evidence_review:
  max_retries: 2
```

This prevents one strict policy from consuming all agent iterations.

## Integration

The existing policy interfaces should remain.

Instead of constructing every policy manually:

```python
Agent(
    completion_policies=(...),
    before_tool_policies=(...),
    after_tool_policies=(...),
)
```

AgentKit should load a profile and build those policy collections automatically.

Conceptually:

```python
policies = load_policy_profile("workspace")
```

The resulting policies are still normal Python policy objects.

## Provider Independence

Policies must continue depending only on AgentKit abstractions such as:

```python
Model
```

They must not depend directly on:

```python
OpenAIModel
OllamaModel
```

This allows the same policy configuration to work with any provider.

## Design Principle

> Python defines what a policy can do. YAML defines how that policy should behave for a specific scenario.

The initial implementation should focus only on:

- YAML policy profiles
- `enabled`
- `max_retries`
- `strictness`
- Model policy system prompts
- `allow`, `retry`, and `reject` messages
- Profile loading and validation
- Independent policy retry counting

More complex features such as inheritance, model overrides, metrics, and per-agent overrides can be added later.