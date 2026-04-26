from pathlib import Path

from codelens.graph.models import Graph
from codelens.parsers.common import collect_source_files
from codelens.parsers.frontend_parser import parse_frontend_file
from codelens.parsers.markdown_parser import parse_markdown_file


def scan_project(root: Path) -> Graph:
    root = root.resolve()
    graph = Graph(root=str(root))
    files, warnings = collect_source_files(root)
    graph.warnings.extend(warnings)

    for path in files:
        if path.suffix in {".ts", ".tsx", ".js", ".jsx"}:
            result = parse_frontend_file(path, root)
        elif path.suffix in {".md", ".mdx"}:
            result = parse_markdown_file(path, root)
        else:
            continue

        graph.nodes.extend(result.nodes)
        graph.edges.extend(result.edges)
        graph.warnings.extend(result.warnings)

    return dedupe_graph(graph)


def dedupe_graph(graph: Graph) -> Graph:
    nodes = {}
    for node in graph.nodes:
        if node.id in nodes:
            existing = nodes[node.id]
            sources = existing.metadata.setdefault("sources", [])
            if existing.path and existing.path not in sources:
                sources.append(existing.path)
            if node.path and node.path not in sources:
                sources.append(node.path)
            for key, value in node.metadata.items():
                if key not in existing.metadata or _empty_metadata(existing.metadata[key]):
                    existing.metadata[key] = value
            continue
        nodes[node.id] = node

    edges = {}
    for edge in graph.edges:
        edges[(edge.source, edge.target, edge.type)] = edge

    graph.nodes = list(nodes.values())
    graph.edges = list(edges.values())
    return graph


def _empty_metadata(value: object) -> bool:
    return value is None or value == "" or value == []
