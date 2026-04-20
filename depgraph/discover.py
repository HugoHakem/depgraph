"""Auto-discover Python source files in a project tree."""

import fnmatch
from pathlib import Path

DEFAULT_EXCLUDES = [
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".git",
    "node_modules",
    "build",
    "dist",
    ".tox",
    "*.egg-info",
]


def discover_files(root: Path, excludes: list[str] | None = None) -> list[Path]:
    """
    Recursively find all .py files under root, skipping excluded paths.

    excludes entries are matched against each path component (directory or
    filename) as well as the full relative path via fnmatch.
    """
    excludes = excludes if excludes is not None else DEFAULT_EXCLUDES
    files: list[Path] = []

    for p in sorted(root.rglob("*.py")):
        rel = p.relative_to(root)
        parts = rel.parts
        if any(
            fnmatch.fnmatch(part, pat) or fnmatch.fnmatch(str(rel), pat)
            for part in parts
            for pat in excludes
        ):
            continue
        files.append(p)

    return files
