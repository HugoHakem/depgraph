"""Filter a pyan3-generated dot graph to show callers or callees of target namespaces."""

import re


def _collect_clusters(lines: list[str]) -> set[str]:
    clusters: set[str] = set()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('subgraph "cluster_'):
            cluster_name = stripped.split('"')[1].replace("cluster_", "")
            clusters.add(cluster_name)
    return clusters


def _remove_empty_subgraphs(text: str) -> str:
    empty_subgraph = re.compile(
        r'subgraph "cluster_[^"]+" \{\s*graph \[[^\]]+\];\s*\}', re.MULTILINE
    )
    return re.sub(empty_subgraph, "", text)


def filter_dot(dot_content: str, target_namespaces: list[str]) -> str:
    """
    Prune a full pyan3 dot graph to nodes and edges relevant to target_namespaces.

    Keeps:
      - All nodes belonging to any target namespace.
      - All edges whose destination is inside any target namespace.
      - All external nodes that appear as a source of such an edge.

    Drops:
      - All other nodes and edges.
      - Empty subgraphs left over after pruning.
      - Duplicate "flying" nodes that already have a cluster subgraph.
    """
    lines = dot_content.splitlines(keepends=True)
    clusters = _collect_clusters(lines)

    def matches_any_target(name: str) -> bool:
        return any(name.startswith(ns) for ns in target_namespaces)

    # Pass 1: keep structural lines; only keep edges pointing INTO a target namespace
    valid_lines: list[str] = []
    active_external_nodes: set[str] = set()
    for line in lines:
        if "->" in line:
            dest = line.split("->")[1].strip().strip('"').split("[")[0].strip()
            if matches_any_target(dest):
                valid_lines.append(line)
                src_node = line.split("->")[0].strip()
                active_external_nodes.add(src_node)
        else:
            valid_lines.append(line)

    # Pass 2: drop nodes that are neither in a target namespace nor active external callers
    final_lines: list[str] = []
    for line in valid_lines:
        stripped = line.strip()
        if "->" not in line and stripped.startswith('"') and "[" in line:
            node_name = stripped.split("[")[0].strip().strip('"')
            if node_name in clusters:
                continue
            if (
                not matches_any_target(node_name)
                and f'"{node_name}"' not in active_external_nodes
            ):
                continue
        final_lines.append(line)

    # Pass 3: remove empty subgraphs left after pruning
    return _remove_empty_subgraphs("".join(final_lines))


def filter_dot_outgoing(dot_content: str, target_namespaces: list[str]) -> str:
    """
    Prune a full pyan3 dot graph to nodes and edges relevant to target_namespaces.

    Keeps:
      - All nodes belonging to any target namespace.
      - All edges whose source is inside any target namespace.
      - All external nodes that appear as a destination of such an edge.

    Drops:
      - All other nodes and edges.
      - Empty subgraphs left over after pruning.
      - Duplicate "flying" nodes that already have a cluster subgraph.
    """
    lines = dot_content.splitlines(keepends=True)
    clusters = _collect_clusters(lines)

    def matches_any_target(name: str) -> bool:
        return any(name.startswith(ns) for ns in target_namespaces)

    # Pass 1: keep edges pointing OUT FROM a target namespace
    valid_lines: list[str] = []
    active_external_nodes: set[str] = set()
    for line in lines:
        if "->" in line:
            src = line.split("->")[0].strip().strip('"')
            if matches_any_target(src):
                valid_lines.append(line)
                dest_node = line.split("->")[1].strip().split("[")[0].strip()
                active_external_nodes.add(dest_node)
        else:
            valid_lines.append(line)

    # Pass 2: drop nodes that are neither in target namespace nor active external callees
    final_lines: list[str] = []
    for line in valid_lines:
        stripped = line.strip()
        if "->" not in line and stripped.startswith('"') and "[" in line:
            node_name = stripped.split("[")[0].strip().strip('"')
            if node_name in clusters:
                continue
            if (
                not matches_any_target(node_name)
                and f'"{node_name}"' not in active_external_nodes
            ):
                continue
        final_lines.append(line)

    # Pass 3: remove empty subgraphs left after pruning
    return _remove_empty_subgraphs("".join(final_lines))
