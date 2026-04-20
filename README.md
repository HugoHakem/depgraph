# depgraph

A CLI tool that generates a dependency graph showing which Python modules call into a target namespace or file. It wraps [pyan3](https://github.com/Technologicat/pyan) for static analysis and [Graphviz](https://graphviz.org/) for rendering.

## Requirements

- Python >= 3.11
- [`uv`](https://github.com/astral-sh/uv) (used to run `pyan3` via `uvx`)
- Graphviz (`dot` must be on your `PATH`)

## Installation

### Run directly from GitHub (no clone needed)

```bash
uvx --from git+https://github.com/HugoHakem/depgraph depgraph <args>
```

### Install locally

```bash
pip install .
# or with uv
uv pip install .
```

## Usage

```bash
depgraph <target> [target ...] [options]
```

### Targets

Each target can be:

- A **namespace** (e.g. `utils`, `delphi`) — matches all nodes whose pyan3 name starts with that prefix.
- A **Python file** (e.g. `utils/helpers.py`) — matches only nodes from that specific file. The path is converted to a pyan3 module identifier (`utils/helpers.py` → `utils__helpers`).

Multiple targets can be mixed freely:

```bash
depgraph utils delphi/helpers.py trainer --root .
```

### File selection

| Flag                      | Description                                                             |
|---------------------------|-------------------------------------------------------------------------|
| `--root DIR`              | Project root for auto-discovery (default: `.`)                          |
| `--files GLOB [...]`      | Explicit glob patterns instead of auto-discovery                        |
| `--exclude PATTERN [...]` | Additional patterns to exclude (always combined with built-in defaults) |

Built-in excluded directories: `__pycache__`, `.venv`, `venv`, `env`, `legacy`, `.git`, `node_modules`, `build`, `dist`, `.tox`, `*.egg-info`.

### Output

| Flag                     | Description                                      |
|--------------------------|--------------------------------------------------|
| `-o FILE`                | Output file (default: `<targets>_deps.<format>`) |
| `--format svg\|png\|dot` | Output format (default: `svg`)                   |
| `--keep-dot`             | Also write the intermediate `.dot` file          |

### Graph layout

| Flag                       | Description                                                                           |
|----------------------------|---------------------------------------------------------------------------------------|
| `--rankdir LR\|TB\|BT\|RL` | Graphviz layout direction (default: `LR`)                                             |
| `--depth N\|max`           | `0` = modules only, `1` = + top-level functions, `max` = full detail (default: `max`) |

## Examples

```bash
# Auto-discover all .py files under cwd, show callers of 'utils'
depgraph utils --root .

# Target multiple namespaces
depgraph utils delphi --root /path/to/project

# Target a specific file
depgraph src/model/trainer.py --root .

# Mix namespaces and files
depgraph utils src/model/trainer.py --root .

# Explicit file list with glob patterns
depgraph utils --files "utils/*.py" "delphi/*.py" train.py

# Exclude an additional directory on top of the defaults
depgraph utils --root . --exclude experiments

# Module-level only (faster, less noise)
depgraph utils --root . --depth 0

# Output as PNG and keep the intermediate .dot file
depgraph utils --root . -o graph.png --format png --keep-dot
```
