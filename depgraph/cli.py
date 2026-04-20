"""CLI entry point for depgraph."""

from __future__ import annotations

import argparse
import glob
import subprocess
import sys
from pathlib import Path

from depgraph.discover import DEFAULT_EXCLUDES, discover_files
from depgraph.filter_dot import filter_dot


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="depgraph",
        description=(
            "Generate a dependency graph showing which modules call into a "
            "target namespace. Wraps pyan3 for analysis and graphviz for rendering."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  # Auto-discover all .py files, focus on 'utils' namespace
  depgraph utils --root /path/to/project

  # Explicit file list with glob patterns
  depgraph utils --files "utils/*.py" "delphi/*.py" train.py "auc/*.py"

  # Module-level only (faster, less noise)
  depgraph utils --root . --depth 0

  # Output as PNG and keep the intermediate .dot
  depgraph utils --root . -o graph.png --format png --keep-dot
""",
    )

    parser.add_argument(
        "target",
        nargs="+",
        help="Namespaces or .py files to focus on (e.g. 'utils' 'delphi.py'). "
             "Only edges pointing into these namespaces are shown.",
    )

    # ── File selection ────────────────────────────────────────────────────────
    sel = parser.add_argument_group("file selection")
    sel.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        metavar="DIR",
        help="Project root for auto-discovering Python files (default: .).",
    )
    sel.add_argument(
        "--files",
        nargs="+",
        metavar="GLOB",
        help="Explicit glob patterns to include instead of auto-discovery "
             "(e.g. 'utils/*.py' train.py 'auc/*.py').",
    )
    sel.add_argument(
        "--exclude",
        nargs="+",
        default=None,
        metavar="PATTERN",
        help=f"Additional patterns to exclude during auto-discovery "
             f"(always combined with defaults: {DEFAULT_EXCLUDES}).",
    )

    # ── Output ────────────────────────────────────────────────────────────────
    out = parser.add_argument_group("output")
    out.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        metavar="FILE",
        help="Output file (default: <target>_deps.<format>).",
    )
    out.add_argument(
        "--format",
        choices=["svg", "png", "dot"],
        default="svg",
        help="Output format (default: svg).",
    )
    out.add_argument(
        "--keep-dot",
        action="store_true",
        help="Write intermediate filtered .dot file alongside the output.",
    )

    # ── Graph layout ──────────────────────────────────────────────────────────
    layout = parser.add_argument_group("graph layout")
    layout.add_argument(
        "--rankdir",
        choices=["LR", "TB", "BT", "RL"],
        default="LR",
        help="Graphviz rankdir (default: LR = left-to-right).",
    )
    layout.add_argument(
        "--depth",
        default="max",
        metavar="N",
        help="pyan3 graph depth: 0=modules only, 1=+top-level functions, "
             "max=full detail (default: max).",
    )

    return parser


def resolve_targets(targets: list[str]) -> list[str]:
    namespaces: list[str] = []
    for t in targets:
        if t.endswith(".py"):
            module = Path(t).with_suffix("").as_posix().replace("/", "__")
            if not module:
                print(f"Warning: '{t}' has no resolvable module name, skipping.", file=sys.stderr)
                continue
            namespaces.append(module)
        else:
            namespaces.append(t)
    return namespaces


def resolve_files(args: argparse.Namespace) -> list[Path]:
    if args.files:
        paths: list[Path] = []
        for pattern in args.files:
            matches = glob.glob(pattern, recursive=True)
            if not matches:
                print(f"Warning: no files matched '{pattern}'", file=sys.stderr)
            paths.extend(Path(m) for m in matches)
        return sorted(set(paths))
    extra = args.exclude or []
    return discover_files(args.root, DEFAULT_EXCLUDES + extra)


def run_pyan3(py_files: list[Path], rankdir: str, depth: str) -> str:
    cmd = [
        "uvx", "pyan3",
        *[str(f) for f in py_files],
        "--dot",
        "--grouped", "--colored",
        "--no-defines", "--uses",
        "--dot-rankdir", rankdir,
    ]
    if depth != "max":
        cmd += ["--depth", depth]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)
    return result.stdout


def render_dot(dot_content: str, output: Path, fmt: str) -> None:
    cmd = ["dot", f"-T{fmt}", "-o", str(output)]
    result = subprocess.run(cmd, input=dot_content, text=True, capture_output=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    namespaces = resolve_targets(args.target)
    if not namespaces:
        print("No valid targets provided.", file=sys.stderr)
        sys.exit(1)

    # Resolve output path default
    if args.output is None:
        args.output = Path(f"{'_'.join(namespaces)}_deps.{args.format}")

    py_files = resolve_files(args)
    if not py_files:
        print("No Python files found.", file=sys.stderr)
        sys.exit(1)

    print(f"Analysing {len(py_files)} files for {namespaces} callers...", file=sys.stderr)

    raw_dot = run_pyan3(py_files, args.rankdir, args.depth)
    filtered = filter_dot(raw_dot, namespaces)

    if args.format == "dot":
        args.output.write_text(filtered)
    else:
        if args.keep_dot:
            dot_path = args.output.with_suffix(".dot")
            dot_path.write_text(filtered)
            print(f"DOT:    {dot_path}", file=sys.stderr)
        render_dot(filtered, args.output, args.format)

    print(f"Output: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
