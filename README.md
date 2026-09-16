# AgentKit

AgentKit is a reusable Python runtime for building AI agents with tool calling, policies, model abstraction, and runtime orchestration.

The project focuses on keeping the core agent architecture explicit and provider-independent instead of hiding execution behind a large framework.

## Features

AgentKit currently provides:

- Python package and command-line interface.
- Typed YAML configuration.
- `.env` environment loading.
- Provider-independent model abstraction.
- Ollama model provider.
- OpenAI model provider.
- Automatic Ollama installation and startup management on macOS.
- Model factory based on configuration.
- Generic tool definitions, schemas, calls, results, registry, and execution.
- Model-driven tool calling.
- Reusable agent runtime loop.
- Agent state.
- Completion, before-tool, and after-tool policies.
- Deterministic and model-backed policies.
- Runtime and policy events for observability.

## Requirements

- Python 3.14
- `make`
- macOS for automatic Ollama installation
- An OpenAI API key when using the OpenAI provider

## Setup

Create the local environment configuration:

```bash
cp .env.example .env
```

Example:

```dotenv
PYTHON_BIN=/opt/homebrew/opt/python@3.14/bin/python3.14
OPENAI_API_KEY=sk-...
```

Then run:

```bash
make
```

The setup creates `.venv` and installs AgentKit in editable mode.

Activate the environment:

```bash
source .venv/bin/activate
```

## Configuration

The main runtime configuration is:

```text
config/default.yaml
```

The selected provider and model are defined by:

```yaml
model:
  provider: ollama
  name: qwen3:8b
```

or:

```yaml
model:
  provider: openai
  name: gpt-5.4-nano
```

Provider-specific configuration remains available in the same file:

```yaml
ollama:
  host: http://localhost:11434

openai:
  api_key_env: OPENAI_API_KEY
```

Changing the model or provider only requires changing `model.provider` and `model.name`.

The rest of AgentKit consumes the generic `Model` abstraction.

## Models

The model layer is provider-independent:

```text
ModelRequest
    │
    ▼
  Model
    │
    ├── OllamaModel
    │
    └── OpenAIModel
    │
    ▼
ModelResponse
```

Core structures such as:

```text
ModelMessage
ModelRequest
ModelResponse
ToolCall
```

do not depend on Ollama or OpenAI.

Provider implementations are responsible for translating between AgentKit structures and their respective APIs.

### Model Factory

Model creation is centralized:

```python
model = get_default_model()
```

The factory:

1. Loads the current settings.
2. Reads the configured provider.
3. Creates the correct model implementation.
4. Passes the configured model name and provider settings.

Applications therefore do not need to know which provider is being used.

## Bootstrap

Prepare the configured runtime with:

```bash
agentkit bootstrap
```

For Ollama, bootstrap:

1. Validates Python.
2. Detects or installs Ollama.
3. Starts the local Ollama server when necessary.
4. Waits for the API to become available.
5. Checks the configured model.
6. Pulls the model when necessary.

For OpenAI, bootstrap validates the required environment configuration, including the configured API key variable.

## Direct Model Inference

Send a prompt directly to the configured model:

```bash
agentkit model "Hello"
```

The command follows the generic model path:

```text
CLI
 │
 ▼
ModelRequest
 │
 ▼
Model
 │
 ├── Ollama
 └── OpenAI
 │
 ▼
ModelResponse
```

## Tools

AgentKit provides a generic tool system:

```text
Tool
ToolSchema
ToolCall
ToolResult
ToolRegistry
ToolExecutor
```

A `Tool` defines:

- Name
- Description
- Parameter schema
- Python handler

A model may return one or more `ToolCall` values.

The runtime executes them through `ToolExecutor` and returns `ToolResult` values to the conversation.

Tool calls include an identifier so provider-specific function calls and their results can be correctly associated across model turns.

## Agents

An `Agent` defines the behavior available to an execution:

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

The agent itself does not execute anything.

Execution is handled by `AgentRuntime`.

## Agent State

`AgentState` represents the current execution state:

```text
messages
iteration
tool_calls
tool_results
response
```

Policies can inspect this state without depending on a specific model provider or application domain.

## Runtime

`AgentRuntime` implements the agent loop:

```text
User Prompt
    │
    ▼
AgentRuntime
    │
    ▼
Model
    │
    ├── Final candidate
    │       │
    │       ▼
    │  CompletionPolicy
    │
    └── ToolCall
            │
            ▼
      BeforeToolPolicy
            │
            ▼
       ToolExecutor
            │
            ▼
        ToolResult
            │
            ▼
       AfterToolPolicy
            │
            └──────► Model
```

The runtime:

1. Creates the initial conversation.
2. Sends messages and tools to the model.
3. Receives either content or tool calls.
4. Evaluates policies before tool execution.
5. Executes allowed tools.
6. Returns tool results to the model.
7. Evaluates policies after tool execution.
8. Evaluates completion policies before accepting a final response.
9. Continues until completion or the agent iteration limit is reached.

The runtime depends only on the generic `Model` contract.

## Policies

Policies control or validate behavior during the agent lifecycle.

AgentKit currently defines:

```text
CompletionPolicy
BeforeToolPolicy
AfterToolPolicy
```

A policy returns a `PolicyDecision`:

```text
allow
retry
reject
```

### Deterministic Policies

Deterministic policies evaluate state directly in Python.

They are appropriate for rules that can be expressed precisely without another model call.

### Model-Backed Policies

Model-backed policies use a `Model` to evaluate agent state or candidate behavior.

The generic flow is:

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

Because model-backed policies depend only on the `Model` abstraction, they can use either Ollama, OpenAI, or another compatible provider.

## Observability

AgentKit emits runtime events instead of printing directly.

Current runtime events include:

```text
RuntimeStarted
ModelRequested
ModelResponded
ToolCalled
ToolCompleted
PolicyEvaluated
RuntimeCompleted
```

Model-backed policies also expose:

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

Show available commands:

```bash
agentkit --help
```

AgentKit can also be invoked as:

```bash
python -m agentkit --help
```

Current commands:

```bash
agentkit bootstrap
agentkit doctor
agentkit model "<prompt>"
agentkit down
```

### `bootstrap`

Validates and prepares the configured provider environment.

### `doctor`

Diagnoses the current AgentKit environment without changing it.

### `model`

Sends a prompt directly to the configured model.

### `down`

Stops local runtime services when the active provider requires them.

Remote providers such as OpenAI do not require a local runtime shutdown.

## Architecture

The current architecture can be summarized as:

```text
Application
    │
    ▼
  Agent
    │
    ├── instructions
    ├── tools
    └── policies
          │
          ▼
     AgentRuntime
          │
          ▼
        Model
      ┌────┴─────┐
      ▼          ▼
   Ollama      OpenAI
      │          │
      └────┬─────┘
           ▼
    ModelResponse
           │
      ┌────┴─────┐
      ▼          ▼
 Final       ToolCall
candidate        │
    │            ▼
    │      ToolExecutor
    │            │
    ▼            ▼
 Policies    ToolResult
      └──────┬─────┘
             ▼
           Model
```

AgentKit core remains independent from application-specific behavior and model providers.

## Development

AgentKit is installed in editable mode:

```bash
pip install -e .
```

Changes under:

```text
src/agentkit/
```

are immediately available to the installed `agentkit` command.

The project keeps provider-specific behavior behind generic interfaces so models, tools, policies, and runtime orchestration can evolve independently.
