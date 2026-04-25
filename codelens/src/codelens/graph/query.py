from collections import deque
from typing import Dict, Iterable, List, Set

from codelens.graph.models import Edge, Graph


def neighbors(graph: Graph, node_id: str, include_reverse: bool = False) -> List[str]:
    output = [edge.target for edge in graph.edges if edge.source == node_id]
    if include_reverse:
        output.extend(edge.source for edge in graph.edges if edge.target == node_id)
    return _dedupe(output)


def reachable_nodes(
    graph: Graph,
    start_ids: Iterable[str],
    max_depth: int = 3,
    include_reverse: bool = True,
) -> List[str]:
    starts = list(start_ids)
    seen: Set[str] = set(starts)
    output: List[str] = []
    queue = deque((node_id, 0) for node_id in starts)

    while queue:
        current, depth = queue.popleft()
        if depth >= max_depth:
            continue
        for target in neighbors(graph, current, include_reverse=include_reverse):
            if target in seen:
                continue
            seen.add(target)
            output.append(target)
            queue.append((target, depth + 1))

    return output


def degree_by_node(graph: Graph) -> Dict[str, int]:
    degree: Dict[str, int] = {}
    for edge in graph.edges:
        degree[edge.source] = degree.get(edge.source, 0) + 1
        degree[edge.target] = degree.get(edge.target, 0) + 1
    return degree


def _dedupe(items: Iterable[str]) -> List[str]:
    seen: Set[str] = set()
    output: List[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            output.append(item)
    return output

