# AgentKit

AgentKit is a reusable Python project for learning and building generic AI agent runtimes with tool calling.

The project will be developed incrementally. The initial repository contains only the project/bootstrap configuration; the AgentKit source code and example agents will be added component by component.

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

At this initial stage, `make`:

1. Reads `.env` when present.
2. Creates `.venv` using the configured Python 3.14 executable.
3. Upgrades `pip`.
4. Installs the project in editable mode.

The `agentkit` CLI and `agentkit bootstrap` command will be added when the source layer is implemented.
