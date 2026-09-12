# AgentKit

AgentKit is a reusable Python project for learning and building generic AI agent runtimes with tool calling.

The project is developed incrementally, component by component, with the goal of understanding and implementing the fundamental building blocks behind AI agent frameworks.

The current version provides:

- A Python package and command-line interface.
- Typed configuration loading.
- Automatic local runtime bootstrap.
- Ollama installation and startup management.
- Automatic model provisioning.
- A provider-independent model abstraction.
- An Ollama model provider.
- Direct model inference through the AgentKit CLI.

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

Configuration is loaded into typed AgentKit settings before being consumed by the bootstrap and model layers.

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

The current flow is:

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

`ModelRequest` and `ModelResponse` are AgentKit structures and are not tied to the Ollama API.

The Ollama implementation is responsible for translating between the AgentKit model contract and the Ollama HTTP API.

This allows additional model providers to be introduced later without changing the agent runtime that consumes the `Model` abstraction.

## Direct Model Inference

A prompt can be sent directly to the configured model through the CLI:

```bash
agentkit model "Responda apenas com: AgentKit funcionando"
```

Example response:

```text
AgentKit funcionando
```

This command exercises the complete current model path:

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
agentkit model "<prompt>"
```

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
└── src/
    └── agentkit/
        ├── __init__.py
        ├── __main__.py
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
        │       └── model.py
        ├── config/
        │   ├── __init__.py
        │   ├── loader.py
        │   └── settings.py
        └── models/
            ├── __init__.py
            ├── model.py
            ├── request.py
            ├── response.py
            └── ollama/
                ├── __init__.py
                ├── client.py
                └── model.py
```

`.env` and `.venv/` are local and are not committed to Git.

Runtime state such as Ollama logs is also kept outside the repository.

## Development

AgentKit is installed in editable mode:

```bash
pip install -e .
```

Changes made to Python source under `src/agentkit/` are therefore immediately available to the installed `agentkit` command without reinstalling the package after every source change.

The project intentionally avoids introducing abstractions before they are required. Components are added incrementally as their responsibilities become concrete.

## Current Progress

```text
Project setup        ✓
Configuration        ✓
CLI                  ✓
Bootstrap            ✓
Models               ✓
Ollama integration   ✓
Local inference      ✓

Tools                ← Next
Context
Runtime / Agent Loop
Agents
Memory
Graph / Subagents
Observability
```

## Next Step: Tools

The next component is the AgentKit tool system.

This layer will define how capabilities external to the language model are represented, registered, discovered, invoked, and returned to the agent runtime.

The initial tool layer will be developed independently from the model integration so its responsibilities remain explicit.

After the tool abstraction and execution path are working, model requests and responses will be extended to support tool definitions and tool calls.

This will form the foundation for the first real AgentKit agent loop:

```text
User
 ↓
Model
 ↓
Tool Call?
 ├── No  → Final Response
 │
 └── Yes
      ↓
   Execute Tool
      ↓
   Tool Result
      ↓
     Model
      ↓
     ...
```

Later components such as context management, runtime orchestration, agents, memory, graphs, subagents, and observability will build on top of these foundations.