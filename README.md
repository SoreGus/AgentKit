# AgentKit

AgentKit is a reusable Python project for learning and building generic AI agent runtimes with tool calling.

The project is developed incrementally, component by component, with the goal of understanding and implementing the fundamental building blocks behind AI agent frameworks instead of hiding them behind a large framework.

The current version provides:

- A Python package and command-line interface.
- Typed configuration loading.
- Automatic local runtime bootstrap.
- Ollama installation and startup management.
- Automatic model provisioning.
- A provider-independent model abstraction.
- An Ollama model provider.
- Direct model inference through the AgentKit CLI.
- A generic tool definition, registry, and execution layer.
- Model-driven tool calling.
- A reusable agent runtime loop.
- Runtime events and observers.
- Agent definitions and runtime state.
- Deterministic completion, before-tool, and after-tool policies.
- Generic model-backed policies.
- Observability for model-backed policy evaluation.
- A read-only Workspace example that combines models, tools, policies, and the runtime.

The default local model is currently Qwen3 8B running through Ollama.

## Requirements

- Python 3.14
- `make`
- macOS for the current automatic Ollama installation flow

Python may come from Homebrew or another installation. The executable is configured per machine through `.env`.

Ollama and the configured model do not need to be installed manually. AgentKit bootstrap prepares them automatically.

## Setup

Create your local environment configuration:

```bash
cp .env.example .env
```

The default is:

```dotenv
PYTHON_BIN=python3.14
```

For Homebrew on an Apple Silicon Mac, for example:

```dotenv
PYTHON_BIN=/opt/homebrew/opt/python@3.14/bin/python3.14
```

Then run:

```bash
make
```

The `make` command:

1. Reads `.env` when present.
2. Creates `.venv` using the configured Python 3.14 executable.
3. Upgrades `pip` inside the virtual environment.
4. Installs AgentKit in editable mode.

## Virtual Environment

Activate the virtual environment before working with AgentKit:

```bash
source .venv/bin/activate
```

When active, commands such as:

```bash
python
pip
agentkit
```

use the executables installed inside `.venv`.

To leave the virtual environment:

```bash
deactivate
```

## Configuration

The default AgentKit runtime configuration is stored in:

```text
config/default.yaml
```

The current configuration defines the model provider, model name, and Ollama host.

For example:

```yaml
model:
  provider: ollama
  name: qwen3:8b

ollama:
  host: http://localhost:11434
```

Configuration is loaded into typed AgentKit settings before being consumed by the bootstrap, CLI, examples, and model layers.

## Bootstrap

Prepare the local AgentKit runtime with:

```bash
agentkit bootstrap
```

The bootstrap process is designed to be idempotent and currently:

1. Validates Python 3.14.
2. Detects the Ollama executable.
3. Installs Ollama through Homebrew on macOS when necessary.
4. Starts the Ollama server when it is not running.
5. Waits until the Ollama API is available.
6. Checks whether the configured model is installed.
7. Pulls the configured model when necessary.

Running bootstrap again reuses an already prepared environment.

Example:

```text
Python 3.14.7: OK
Ollama executable: /usr/local/bin/ollama
Ollama server: OK
Model qwen3:8b: checking...
Model qwen3:8b: OK
AgentKit bootstrap completed successfully.
```

Ollama server output is stored outside the repository at:

```text
~/.agentkit/logs/ollama.log
```

## Models

AgentKit provides a model abstraction that separates the rest of the framework from a specific model provider.

The basic flow is:

```text
ModelRequest
     │
     ▼
   Model
     │
     ▼
OllamaModel
     │
     ▼
OllamaClient
     │
     ▼
   Ollama
     │
     ▼
 Qwen3 8B
     │
     ▼
ModelResponse
```

`ModelRequest`, `ModelMessage`, and `ModelResponse` are AgentKit structures and are not tied to the Ollama API.

The Ollama implementation is responsible for translating between the AgentKit model contract and the Ollama HTTP API.

This allows additional model providers to be introduced later without changing the agent runtime that consumes the `Model` abstraction.

### Model Messages

AgentKit currently supports the roles required by the agent loop:

```text
system
user
assistant
tool
```

Assistant messages may contain tool calls, while tool messages return tool execution results to the model.

This allows the generic model layer to represent multi-turn tool-calling conversations independently from Ollama.

## Direct Model Inference

A prompt can be sent directly to the configured model through the CLI:

```bash
agentkit model "Responda apenas com: AgentKit funcionando"
```

Example response:

```text
AgentKit funcionando
```

This command exercises the complete model path:

```text
CLI
 ↓
ModelRequest
 ↓
OllamaModel
 ↓
OllamaClient
 ↓
Ollama / Qwen3 8B
 ↓
ModelResponse
 ↓
CLI
```

The CLI itself does not communicate with the Ollama HTTP API directly.

## Tools

AgentKit provides a generic tool system that is independent from any specific agent or application domain.

The main concepts are:

```text
Tool
ToolSchema
ToolCall
ToolResult
ToolRegistry
ToolExecutor
```

A `Tool` describes a capability that may be offered to a model. It contains a name, description, parameter schema, and Python handler.

A `ToolCall` represents a specific request produced by a model.

A `ToolResult` represents the result of executing that request.

`ToolRegistry` manages the tools available to an execution context, while `ToolExecutor` resolves and invokes them.

The basic execution path is:

```text
Tool
  ↓
ToolRegistry
  ↓
ToolCall
  ↓
ToolExecutor
  ↓
Python handler
  ↓
ToolResult
```

Tool execution errors are represented as `ToolResult` values with `is_error=True`, allowing the runtime to return failures to the model instead of immediately losing the agent loop.

## Model Tool Calling

The model layer supports tool definitions and tool calls.

A request may contain both conversation messages and the tools available to the model:

```text
ModelRequest
├── messages
└── tools
```

The model may then either produce a normal response or request one or more tool calls:

```text
ModelResponse
├── content
└── tool_calls
```

For Ollama, `OllamaModel` translates AgentKit tools into Ollama function-tool definitions and converts Ollama tool calls back into AgentKit `ToolCall` values.

A simple example is available under:

```text
examples/model_tool/
```

The standalone tool example is available under:

```text
examples/tools/
```

## Agents

An `Agent` defines the behavior and capabilities that are given to the runtime.

The current agent definition contains:

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

The agent does not execute itself.

Execution belongs to `AgentRuntime`.

This keeps the agent definition separate from runtime orchestration.

## Agent State

`AgentState` provides policies and other runtime components with a snapshot of the current execution state.

It currently contains information such as:

```text
messages
iteration
tool_calls
tool_results
response
```

It also provides helpers for inspecting previous tool activity and successful results.

The state is intentionally generic and does not contain Workspace-specific or other domain-specific concepts.

## Runtime / Agent Loop

`AgentRuntime` implements the current reusable agent loop.

Conceptually:

```text
User Prompt
    │
    ▼
AgentRuntime
    │
    ▼
Model
    │
    ├── Final response ──────────────┐
    │                                │
    └── Tool call(s)                 │
             │                       │
             ▼                       │
       BeforeToolPolicy              │
             │                       │
             ▼                       │
        ToolExecutor                 │
             │                       │
             ▼                       │
         ToolResult                  │
             │                       │
             ▼                       │
        AfterToolPolicy              │
             │                       │
             └──────────► Model      │
                                     │
                              CompletionPolicy
                                     │
                            ┌────────┴────────┐
                            │                 │
                          allow             retry
                            │                 │
                            ▼                 └──► Model
                      Final Response
```

The runtime:

1. Builds the initial system and user messages.
2. Sends the conversation and available tools to the model.
3. Receives either a candidate final response or tool calls.
4. Evaluates before-tool policies.
5. Executes allowed tools.
6. Appends tool results to the conversation.
7. Evaluates after-tool policies.
8. Calls the model again when necessary.
9. Evaluates completion policies before accepting a final response.
10. Stops when a response is accepted or the maximum number of iterations is reached.

The runtime is provider-independent. It only depends on the generic `Model` contract.

## Policies

Policies allow AgentKit to validate or control behavior at specific points in the agent lifecycle.

The current lifecycle policy types are:

```text
CompletionPolicy
BeforeToolPolicy
AfterToolPolicy
```

They answer different questions:

- `CompletionPolicy`: may the current candidate response become the final answer?
- `BeforeToolPolicy`: may this tool call execute?
- `AfterToolPolicy`: is the result acceptable, or should the agent recover or try again?

A policy returns a `PolicyDecision`:

```text
allow
retry
reject
```

`allow` continues the current flow.

`retry` returns feedback to the agent loop so the model can make another attempt.

`reject` terminates the operation with an error.

Policies describe **when** a decision is made. The mechanism used to make that decision may be deterministic or model-based.

## Deterministic Policies

A deterministic policy evaluates state directly in Python.

Examples include:

```text
CompletionPolicy
└── RequireFileEvidencePolicy

BeforeToolPolicy
└── WorkspaceToolPolicy

AfterToolPolicy
└── RetryToolErrorsPolicy
```

These policies do not require another model inference.

They are useful for rules that can be expressed precisely in software.

## Model-Backed Policies

AgentKit also provides generic policies whose decisions are delegated to a `Model`.

The current hierarchy is:

```text
CompletionPolicy
├── deterministic implementation
└── ModelCompletionPolicy

BeforeToolPolicy
├── deterministic implementation
└── ModelBeforeToolPolicy

AfterToolPolicy
├── deterministic implementation
└── ModelAfterToolPolicy
```

The shared `ModelPolicy` layer is responsible for:

1. Building the policy evaluation request.
2. Calling the configured `Model`.
3. Requesting a structured policy decision.
4. Parsing the model response.
5. Converting it into `PolicyDecision`.

The expected model decision is conceptually:

```json
{
  "action": "allow",
  "feedback": ""
}
```

or:

```json
{
  "action": "retry",
  "feedback": "Explain what should happen next."
}
```

or:

```json
{
  "action": "reject",
  "feedback": "Explain why this must be rejected."
}
```

The runtime does not need to know whether a policy is deterministic or model-based.

That distinction remains internal to the policy implementation.

## Model Policy Observability

Model-backed policies perform their own model inference.

AgentKit exposes events around that internal inference:

```text
ModelPolicyRequested
ModelPolicyResponded
```

This makes it possible to observe when a reviewer or other model-backed policy calls a model and what raw response it produces.

For example:

```text
[policy model] requested | WorkspaceEvidenceReviewPolicy | messages: 2
[policy model] responded | WorkspaceEvidenceReviewPolicy
{"action": "allow", "feedback": ""}
```

The normal runtime policy event is still emitted after the model response is converted into a `PolicyDecision`:

```text
[iteration 4] policy | completion | WorkspaceEvidenceReviewPolicy | allow
```

This distinction is useful when studying model-backed validation because it exposes both:

```text
model evaluation
       ↓
raw model response
       ↓
PolicyDecision
       ↓
runtime behavior
```

A model-backed policy is not guaranteed to make a correct judgment. The model is still probabilistic and may approve insufficient evidence or reject valid work.

The observability layer makes these failures visible instead of hiding them behind a final `allow`, `retry`, or `reject`.

## Runtime Events

The runtime emits events instead of printing directly.

Current events include:

```text
RuntimeStarted
ModelRequested
ModelResponded
ToolCalled
ToolCompleted
PolicyEvaluated
RuntimeCompleted
```

An application can provide an event callback to observe execution without coupling presentation logic to the runtime.

This allows a CLI, GUI, logger, debugger, or future observability system to consume the same runtime events differently.

Model-policy inference has its own generic events because that inference occurs inside a policy rather than as the main agent model request.

## Workspace Example

The read-only Workspace example demonstrates how AgentKit components can be composed into a domain-specific agent without placing Workspace behavior inside the AgentKit core.

Run it with:

```bash
python examples/workspace/main.py . "Describe this project."
```

A more investigative example:

```bash
python examples/workspace/main.py . "Encontre onde o modelo Ollama é configurado e explique como essa configuração chega até o OllamaModel."
```

Use `--quiet` to hide runtime and policy events:

```bash
python examples/workspace/main.py . "Describe this project." --quiet
```

### Workspace Tools

The Workspace currently exposes read-only tools:

```text
list_files
read_file
search_files
file_info
```

These tools belong to the example application, not to the generic AgentKit framework.

### Workspace Policies

The example currently combines deterministic and model-backed policies:

```text
Completion
├── RequireFileEvidencePolicy
└── WorkspaceEvidenceReviewPolicy

Before Tool
└── WorkspaceToolPolicy

After Tool
└── RetryToolErrorsPolicy
```

`RequireFileEvidencePolicy` deterministically requires successful file-content evidence before a final response is accepted.

`WorkspaceEvidenceReviewPolicy` is a `ModelCompletionPolicy` that asks a model whether the candidate answer is sufficiently grounded in the evidence collected from the workspace.

`WorkspaceToolPolicy` validates allowed Workspace tool calls before execution.

`RetryToolErrorsPolicy` asks the agent to recover when a Workspace tool fails.

The Workspace example intentionally keeps these domain-specific rules outside `src/agentkit/`.

## Generic Framework vs Domain Behavior

AgentKit is designed to remain domain-independent.

The core framework provides mechanisms such as:

```text
models
tools
agents
runtime
policies
events
```

Applications define domain-specific behavior on top:

```text
AgentKit
   │
   ├── Workspace agent
   ├── 3D engine agent
   ├── IoT agent
   ├── data analysis agent
   └── other applications
```

For example, AgentKit may know how to execute a `Tool`, but it should not know what `read_file`, `modify_shape`, `control_device`, or `search_proposition` mean.

Likewise, AgentKit knows how a `ModelCompletionPolicy` works, but the Workspace example defines what counts as sufficient file evidence.

## CLI

Display the available commands with:

```bash
agentkit --help
```

AgentKit can also be invoked directly as a Python module:

```bash
python -m agentkit --help
```

Both execute the same CLI entry point.

Current commands include:

```bash
agentkit bootstrap
agentkit doctor
agentkit model "<prompt>"
agentkit down
```

### `bootstrap`

Prepares the local runtime and configured model.

### `doctor`

Checks the current AgentKit/Ollama environment and reports its status.

### `model`

Sends a prompt directly through the configured model provider.

### `down`

Stops the Ollama server started for local AgentKit usage.

There is intentionally no required manual `up` command in the normal workflow. Components that require the local model runtime can ensure that the required runtime is available.

`down` remains explicit because AgentKit cannot infer when the user has finished working and wants the local service stopped.

CLI command implementations are separated from the main argument parser under `cli/commands/`.

## Current Structure

```text
AgentKit/
├── .env
├── .env.example
├── .gitignore
├── .venv/
├── Makefile
├── README.md
├── pyproject.toml
├── config/
│   └── default.yaml
├── examples/
│   ├── model_tool/
│   │   └── main.py
│   ├── tools/
│   │   ├── calculator.py
│   │   └── main.py
│   └── workspace/
│       ├── __init__.py
│       ├── agent.py
│       ├── main.py
│       ├── observer.py
│       ├── tools.py
│       ├── workspace.py
│       └── policies/
│           ├── __init__.py
│           ├── evidence.py
│           ├── model_evidence.py
│           ├── read_only.py
│           └── tool_errors.py
└── src/
    └── agentkit/
        ├── __init__.py
        ├── __main__.py
        ├── agents/
        │   ├── __init__.py
        │   ├── agent.py
        │   ├── state.py
        │   └── policy/
        │       ├── __init__.py
        │       ├── after_tool.py
        │       ├── before_tool.py
        │       ├── completion.py
        │       ├── decision.py
        │       ├── model.py
        │       ├── model_after_tool.py
        │       ├── model_before_tool.py
        │       └── model_completion.py
        ├── bootstrap/
        │   ├── __init__.py
        │   ├── bootstrap.py
        │   ├── environment.py
        │   └── ollama.py
        ├── cli/
        │   ├── __init__.py
        │   ├── app.py
        │   └── commands/
        │       ├── __init__.py
        │       ├── bootstrap.py
        │       ├── doctor.py
        │       ├── down.py
        │       └── model.py
        ├── config/
        │   ├── __init__.py
        │   ├── loader.py
        │   └── settings.py
        ├── models/
        │   ├── __init__.py
        │   ├── model.py
        │   ├── request.py
        │   ├── response.py
        │   └── ollama/
        │       ├── __init__.py
        │       ├── client.py
        │       └── model.py
        ├── runtime/
        │   ├── __init__.py
        │   ├── event.py
        │   └── runtime.py
        └── tools/
            ├── __init__.py
            ├── call.py
            ├── executor.py
            ├── registry.py
            ├── result.py
            ├── schema.py
            └── tool.py
```

`.env` and `.venv/` are local and are not committed to Git.

Runtime state such as Ollama logs is also kept outside the repository.

## Development

AgentKit is installed in editable mode:

```bash
pip install -e .
```

Changes made to Python source under `src/agentkit/` are therefore immediately available to the installed `agentkit` command without reinstalling the package after every source change.

The project intentionally avoids introducing abstractions before they are required.

Components are added incrementally as their responsibilities become concrete, while keeping the generic framework separate from application-specific behavior.

## Current Progress

```text
Project setup                    ✓
Configuration                    ✓
CLI                              ✓
Bootstrap                        ✓
Models                           ✓
Ollama integration               ✓
Local inference                  ✓
Tools                            ✓
Model tool calling               ✓
CLI doctor / down                ✓
Runtime / Agent Loop             ✓
Runtime events                   ✓
Agent definition                 ✓
AgentState                       ✓
CompletionPolicy                 ✓
BeforeToolPolicy                 ✓
AfterToolPolicy                  ✓
Deterministic policies           ✓
Generic ModelPolicy              ✓
ModelCompletionPolicy            ✓
ModelBeforeToolPolicy            ✓
ModelAfterToolPolicy             ✓
Model policy observability       ✓
Read-only Workspace example      ✓
Workspace evidence reviewer      ✓

Context                          Not built
Memory                           Not built
Graph / Subagents                Not built
Observability package            Not built
```

Runtime events and model-policy events already provide basic observability primitives.

A dedicated observability package has not been introduced yet.

## Current Architecture

The current system can be summarized as:

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
        │
        ├───────────────┐
        │               │
        ▼               ▼
 Final candidate     ToolCall
        │               │
        ▼               ▼
CompletionPolicy   BeforeToolPolicy
        │               │
        │               ▼
        │          ToolExecutor
        │               │
        │               ▼
        │           ToolResult
        │               │
        │               ▼
        │          AfterToolPolicy
        │               │
        └───────┬───────┘
                │
                ▼
              Model
```

A policy may itself use another model inference:

```text
AgentRuntime
    │
    ▼
CompletionPolicy
    │
    ▼
ModelCompletionPolicy
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

The runtime still depends only on the lifecycle policy interfaces and does not need special logic for model-backed policies.

## Next Steps

The next major layers have intentionally not been implemented yet:

### Context

Context management will eventually decide what information should be included in a model request as conversations, tool evidence, and agent executions grow.

This is especially important for local models with limited context windows.

### Memory

Memory will define how useful information can survive beyond a single runtime execution without mixing persistent memory responsibilities into the core agent loop.

### Graph / Subagents

Graph orchestration and subagents will be introduced only after the current agent loop, policies, and state model are sufficiently understood.

A graph will control execution structure and transitions between steps or agents.

Policies will continue to control or validate behavior at specific lifecycle points.

These are separate responsibilities:

```text
Graph
└── What should execute next?

Policy
└── Is this action or result acceptable?
```

The project will continue to evolve incrementally rather than introducing all orchestration concepts at once.
