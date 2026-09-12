# AgentKit

AgentKit is a reusable Python project for learning and building generic AI agent runtimes with tool calling.

The project is developed incrementally, component by component, with the goal of understanding and implementing the fundamental building blocks behind AI agent frameworks.

The current version includes the initial Python package structure and the `agentkit` command-line interface.

## Requirements

- Python 3.14
- `make`

Python may come from Homebrew or any other installation. The executable is configured per machine through `.env`.

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

will use the executables installed inside `.venv`.

To leave the virtual environment:

```bash
deactivate
```

## CLI

After activating the virtual environment, verify the AgentKit CLI:

```bash
agentkit --help
```

You can also invoke AgentKit directly as a Python module:

```bash
python -m agentkit --help
```

Both commands execute the same CLI entry point.

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
└── src/
    └── agentkit/
        ├── __init__.py
        ├── __main__.py
        └── cli/
            ├── __init__.py
            └── app.py
```

`.env` and `.venv/` are local files and are not committed to Git.

## Development

AgentKit is installed in editable mode:

```bash
pip install -e .
```

This means changes made to the Python source under `src/agentkit/` are immediately available to the installed `agentkit` command without reinstalling the package after every source change.

## Next Step

The next component will be the AgentKit bootstrap layer.

It will provide commands such as:

```bash
agentkit bootstrap
agentkit doctor
```

The bootstrap layer will be responsible for preparing and validating the local runtime environment required by AgentKit.

Additional components such as model providers, tool definitions, tool execution, context management, and the agent runtime loop will be introduced incrementally after the bootstrap layer.