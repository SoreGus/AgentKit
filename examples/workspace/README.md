# Workspace Agent Example

A read-only workspace assistant built with AgentKit's declarative agent and policy profiles.

## Structure

```text
workspace/
  main.py
  workspace.py
  observer.py

  agents/
    workspace.yaml

  policies/
    workspace.yaml

  tools/
    __init__.py
    list_files.py
    read_file.py
    search_files.py
    file_info.py
```

The separation is intentional:

- `tools/` contains executable Python behavior.
- `agents/workspace.yaml` defines the agent composition, instructions, tools, policy profile, and iteration limit.
- `policies/workspace.yaml` configures generic AgentKit policies without custom policy Python classes.

## Run

From this directory:

```bash
python main.py /path/to/project "Explain how configuration is loaded."
```

The example expects AgentKit to be installed in the active environment.

## Policy profile

The default profile enables deterministic policies for:

- allowed tools
- tool error retries
- requiring a successful `read_file` before completion

The model-based evidence reviewer is included but disabled by default. It can be enabled directly in `policies/workspace.yaml` without changing Python code.
