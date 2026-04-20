# depgraph

Two complementary CLI tools for exploring Python call graphs via static analysis. Both wrap [pyan3](https://github.com/Technologicat/pyan) for AST-based analysis and [Graphviz](https://graphviz.org/) for rendering.

| Command | Question answered |
|---------|-------------------|
| `depson` | Who depends on X? — shows callers *into* a target namespace |
| `depsof` | What does X depend on? — shows callees *from* a target namespace |

> For full module-level dependency graphs with nice visuals out of the box, also check out [pydeps](https://github.com/thebjorn/pydeps). These tools focus on a different use case: filtering the call graph down to function-level granularity around a specific target.

## Acknowledgements

- [pyan](https://github.com/Technologicat/pyan) — static analysis engine that performs the call-graph extraction underlying these tools.

## Requirements

- Python >= 3.11
- [`uv`](https://github.com/astral-sh/uv) (used to run `pyan3` via `uvx`)
- Graphviz (`dot` must be on your `PATH`)

## Installation

### Run directly from GitHub (no clone needed)

```bash
uvx --from git+https://github.com/HugoHakem/depgraph depson <args>
uvx --from git+https://github.com/HugoHakem/depgraph depsof <args>
```

### Install locally

```bash
pip install .
# or with uv
uv pip install .
```

## Usage

Both commands share the same interface:

```bash
depson <target> [target ...] [options]
depsof <target> [target ...] [options]
```

### Targets

Each target can be:

- A **namespace** (e.g. `utils`, `delphi`) — matches all nodes whose pyan3 name starts with that prefix.
- A **Python file** (e.g. `utils/helpers.py`) — matches only nodes from that specific file. The path is converted to a pyan3 module identifier (`utils/helpers.py` → `utils__helpers`).

Multiple targets can be mixed freely:

```bash
depson utils delphi/helpers.py trainer --root .
depsof utils delphi/helpers.py trainer --root .
```

### File selection

| Flag                      | Description                                                             |
|---------------------------|-------------------------------------------------------------------------|
| `--root DIR`              | Project root for auto-discovery (default: `.`)                          |
| `--files GLOB [...]`      | Explicit glob patterns instead of auto-discovery                        |
| `--exclude PATTERN [...]` | Additional patterns to exclude (always combined with built-in defaults) |

Built-in excluded directories: `__pycache__`, `.venv`, `venv`, `env`, `legacy`, `.git`, `node_modules`, `build`, `dist`, `.tox`, `*.egg-info`.

### Output

| Flag                     | Description                                                                   |
|--------------------------|-------------------------------------------------------------------------------|
| `-o FILE`                | Output file (default: `<targets>_deps.<format>` / `<targets>_uses.<format>`)  |
| `--format svg\|png\|dot` | Output format (default: `svg`)                                                |
| `--keep-dot`             | Also write the intermediate `.dot` file                                       |

### Graph layout

| Flag                       | Description                                                                           |
|----------------------------|---------------------------------------------------------------------------------------|
| `--rankdir LR\|TB\|BT\|RL` | Graphviz layout direction (default: `LR`)                                             |
| `--depth N\|max`           | `0` = modules only, `1` = + top-level functions, `max` = full detail (default: `max`) |

## Examples

```bash
# Who calls into 'utils'?
depson utils --root .

# What does 'utils' call into?
depsof utils --root .

# Target multiple namespaces
depson utils delphi --root /path/to/project

# Target a specific file
depson src/model/trainer.py --root .

# Mix namespaces and files
depsof utils src/model/trainer.py --root .

# Explicit file list with glob patterns
depson utils --files "utils/*.py" "delphi/*.py" train.py

# Exclude an additional directory on top of the defaults
depsof utils --root . --exclude experiments

# Module-level only (faster, less noise)
depson utils --root . --depth 0

# Output as PNG and keep the intermediate .dot file
depsof utils --root . -o graph.png --format png --keep-dot
```
