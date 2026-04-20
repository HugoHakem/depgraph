"""CLI entry point for depsof — shows what a target namespace depends on."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from depgraph.depson import render_dot, resolve_files, resolve_targets, run_pyan3
from depgraph.discover import DEFAULT_EXCLUDES
from depgraph.filter_dot import filter_dot_outgoing


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="depsof",
        description=(
            "Generate a dependency graph showing which functions a target namespace "
            "calls into. Wraps pyan3 for analysis and graphviz for rendering."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  # Auto-discover all .py files, show what 'utils' depends on
  depsof utils --root /path/to/project

  # Explicit file list with glob patterns
  depsof utils --files "utils/*.py" "delphi/*.py" train.py "auc/*.py"

  # Module-level only (faster, less noise)
  depsof utils --root . --depth 0

  # Output as PNG and keep the intermediate .dot
  depsof utils --root . -o graph.png --format png --keep-dot
""",
    )

    parser.add_argument(
        "target",
        nargs="+",
        help="Namespaces or .py files to focus on (e.g. 'utils' 'delphi.py'). "
             "Only edges originating from these namespaces are shown.",
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
        help="Output file (default: <target>_uses.<format>).",
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


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    namespaces = resolve_targets(args.target)
    if not namespaces:
        print("No valid targets provided.", file=sys.stderr)
        sys.exit(1)

    if args.output is None:
        args.output = Path(f"{'_'.join(namespaces)}_uses.{args.format}")

    py_files = resolve_files(args)
    if not py_files:
        print("No Python files found.", file=sys.stderr)
        sys.exit(1)

    print(f"Analysing {len(py_files)} files for {namespaces} dependencies...", file=sys.stderr)

    raw_dot = run_pyan3(py_files, args.rankdir, args.depth)
    filtered = filter_dot_outgoing(raw_dot, namespaces)

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
