"""Filter a pyan3-generated dot graph to show only callers of a target namespace."""

import re


def filter_dot(dot_content: str, target_namespace: str) -> str:
    """
    Prune a full pyan3 dot graph to nodes and edges relevant to target_namespace.

    Keeps:
      - All nodes belonging to target_namespace.
      - All edges whose destination is inside target_namespace.
      - All external nodes that appear as a source of such an edge.

    Drops:
      - All other nodes and edges.
      - Empty subgraphs left over after pruning.
      - Duplicate "flying" nodes that already have a cluster subgraph.
    """
    lines = dot_content.splitlines(keepends=True)

    # Pass 0: collect subgraph cluster names (to detect "flying" duplicate nodes)
    clusters: set[str] = set()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('subgraph "cluster_'):
            cluster_name = stripped.split('"')[1].replace("cluster_", "")
            clusters.add(cluster_name)

    # Pass 1: keep structural lines; only keep edges pointing INTO target_namespace
    valid_lines: list[str] = []
    active_external_nodes: set[str] = set()
    for line in lines:
        if "->" in line:
            dest = line.split("->")[1].strip()
            if dest.startswith(f'"{target_namespace}'):
                valid_lines.append(line)
                src_node = line.split("->")[0].strip()
                active_external_nodes.add(src_node)
        else:
            valid_lines.append(line)

    # Pass 2: drop nodes that are neither in target_namespace nor active external callers
    final_lines: list[str] = []
    for line in valid_lines:
        stripped = line.strip()
        if "->" not in line and stripped.startswith('"') and "[" in line:
            node_name = stripped.split("[")[0].strip().strip('"')
            # Drop "flying" node if a cluster subgraph already represents it
            if node_name in clusters:
                continue
            # Drop nodes unrelated to target that made no calls into target
            if (
                not node_name.startswith(target_namespace)
                and f'"{node_name}"' not in active_external_nodes
            ):
                continue
        final_lines.append(line)

    # Pass 3: remove empty subgraphs left after pruning
    text = "".join(final_lines)
    empty_subgraph = re.compile(
        r'subgraph "cluster_[^"]+" \{\s*graph \[[^\]]+\];\s*\}', re.MULTILINE
    )
    return re.sub(empty_subgraph, "", text)
