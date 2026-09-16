# AgentKit

AgentKit is a reusable Python runtime for building AI agents with tool calling, declarative agents, configurable policies, model abstraction, and runtime orchestration.

The project keeps agent execution explicit and provider-independent while avoiding unnecessary framework complexity.

## Features

- Python 3.14 package and CLI
- Typed YAML configuration
- `.env` environment loading
- Provider-independent `Model` abstraction
- Ollama and OpenAI providers
- Model factory
- Tool calling and execution
- Declarative agents
- Declarative policy profiles
- Deterministic and model-backed policies
- Independent policy retry limits
- Agent execution state
- Runtime orchestration
- Runtime and policy observability events
- Automatic Ollama setup on macOS

## Requirements

- Python 3.14
- `make`
- macOS for automatic Ollama installation
- OpenAI API key when using the OpenAI provider

## Setup

Create the environment file:

```bash
cp .env.example .env
```

Example:

```dotenv
PYTHON_BIN=/opt/homebrew/opt/python@3.14/bin/python3.14
OPENAI_API_KEY=sk-...
```

Install AgentKit:

```bash
make
```

Activate the environment:

```bash
source .venv/bin/activate
```

AgentKit is installed in editable mode, so changes under `src/agentkit/` are immediately available.

## Model Configuration

The main runtime configuration is:

```text
config/default.yaml
```

Example with Ollama:

```yaml
model:
  provider: ollama
  name: qwen3:8b

ollama:
  host: http://localhost:11434
```

Example with OpenAI:

```yaml
model:
  provider: openai
  name: gpt-5.4-nano

openai:
  api_key_env: OPENAI_API_KEY
```

The rest of AgentKit depends only on the generic `Model` abstraction.

```text
ModelRequest
    │
    ▼
  Model
 ┌──┴───────┐
 ▼          ▼
Ollama    OpenAI
 └────┬─────┘
      ▼
ModelResponse
```

Applications can obtain the configured model with:

```python
model = get_default_model()
```

## Bootstrap

Prepare the configured provider:

```bash
agentkit bootstrap
```

For Ollama, AgentKit can:

1. Validate Python.
2. Detect or install Ollama.
3. Start the Ollama server.
4. Wait for the API.
5. Check the configured model.
6. Pull the model when necessary.

For OpenAI, bootstrap validates the required environment configuration.

## Direct Model Inference

Send a prompt directly to the configured model:

```bash
agentkit model "Hello"
```

## Tools

Tools are implemented in Python.

A `Tool` defines:

- Name
- Description
- Parameter schema
- Python handler

Core tool types include:

```text
Tool
ToolSchema
ToolCall
ToolResult
ToolRegistry
ToolExecutor
```

Example:

```python
Tool(
    name="read_file",
    description="Read a text file.",
    schema=...,
    handler=read_file,
)
```

The tool definition is the source of truth for its schema and behavior.

Tools can be reused by multiple agents.

## Declarative Agents

Agents can be defined in YAML instead of being manually assembled in Python.

Example:

```text
agents/
  workspace.yaml
```

```yaml
agent:
  name: workspace

  instructions: |
    You are a read-only workspace assistant.
    Inspect the workspace before making claims about its contents.
    Answer in the same language used by the user.

  tools:
    - list_files
    - search_files
    - read_file
    - file_info

  policy_profile: workspace

  max_iterations: 10
```

The agent references tools by their registered `Tool.name`.

AgentKit resolves those names against the Python tools registered by the application.

The resulting object is still a normal:

```text
Agent
├── name
├── instructions
├── tools
├── completion_policies
├── before_tool_policies
├── after_tool_policies
└── max_iterations
```

## Declarative Policy Profiles

Policy behavior can also be configured through YAML.

Example:

```text
policies/
  workspace.yaml
```

```yaml
profile:
  name: workspace

policies:
  require_tool_success:
    enabled: true
    tool: read_file

  retry_tool_errors:
    enabled: true
    max_retries: 2

  workspace_evidence_review:
    enabled: false
    max_retries: 2
    strictness: balanced

    model:
      system_prompt: |
        Review whether the candidate answer is sufficiently
        supported by the collected workspace evidence.

    messages:
      retry: |
        Inspect only the additional evidence required and try again.

      reject: |
        The response cannot be adequately supported.

      allow: |
        The response is sufficiently supported.
```

The intended separation is:

```text
Tools     → Python behavior
Agents    → YAML composition
Policies  → YAML behavior and constraints
```

Applications normally do not need to implement custom policy classes for common scenarios.

AgentKit provides reusable policy implementations and builds them from the selected profile.

## Policies

Policies can run at three stages:

```text
BeforeToolPolicy
AfterToolPolicy
CompletionPolicy
```

They return a `PolicyDecision`:

```text
allow
retry
reject
```

### Deterministic Policies

Deterministic policies evaluate rules directly in Python.

Examples include:

- Allowed tools
- Tool execution errors
- Required successful tool calls

### Model-Backed Policies

Model-backed policies use the generic `Model` abstraction to evaluate behavior or evidence.

```text
Policy
  │
  ▼
ModelPolicy
  │
  ▼
Model
  │
  ▼
PolicyDecision
```

They remain provider-independent and can therefore use Ollama, OpenAI, or another compatible provider.

Policy configuration may define:

- `enabled`
- `max_retries`
- `strictness`
- System prompts
- `allow` messages
- `retry` messages
- `reject` messages

Policy retry limits are independent from:

```python
Agent(max_iterations=10)
```

This prevents one strict policy from consuming the entire agent iteration budget.

## Agent State

`AgentState` represents the current execution state:

```text
messages
iteration
tool_calls
tool_results
response
```

Policies can inspect this state without depending on a specific provider or application.

## Runtime

`AgentRuntime` executes the agent loop.

```text
User
 │
 ▼
Model
 │
 ├── ToolCall
 │      │
 │      ▼
 │ BeforeToolPolicy
 │      │
 │      ▼
 │ ToolExecutor
 │      │
 │      ▼
 │ ToolResult
 │      │
 │      ▼
 │ AfterToolPolicy
 │      │
 │      └─────────► Model
 │
 └── Final candidate
         │
         ▼
   CompletionPolicy
         │
         ▼
      Complete
```

The runtime:

1. Creates the initial conversation.
2. Sends messages and tools to the model.
3. Receives content or tool calls.
4. Evaluates before-tool policies.
5. Executes allowed tools.
6. Stores tool results.
7. Evaluates after-tool policies.
8. Detects final-response candidates.
9. Evaluates completion policies.
10. Continues until completion or the iteration limit is reached.

The runtime depends only on AgentKit abstractions.

## Observability

AgentKit emits events instead of printing directly.

Runtime events include:

```text
RuntimeStarted
ModelRequested
ModelResponded
ToolCalled
ToolCompleted
PolicyEvaluated
RuntimeCompleted
```

Model-backed policies also emit:

```text
ModelPolicyRequested
ModelPolicyResponded
```

Applications can use these events for:

- CLI output
- Logging
- Debugging
- GUIs
- Execution tracing

## CLI

Available commands:

```bash
agentkit bootstrap
agentkit doctor
agentkit model "<prompt>"
agentkit down
```

Show help with:

```bash
agentkit --help
```

or:

```bash
python -m agentkit --help
```

### `bootstrap`

Validates and prepares the configured provider.

### `doctor`

Diagnoses the current environment without modifying it.

### `model`

Sends a prompt directly to the configured model.

### `down`

Stops local provider services when applicable.

## Project Architecture

```text
Application
    │
    ├── Python Tools
    │
    ├── Agent YAML
    │
    └── Policy YAML
          │
          ▼
       AgentKit
          │
          ▼
      AgentRuntime
          │
     ┌────┴─────┐
     ▼          ▼
   Model      Tools
     │
 ┌───┴────┐
 ▼        ▼
Ollama   OpenAI
```

AgentKit keeps application behavior, policy configuration, runtime orchestration, and model providers separated so each layer can evolve independently.
