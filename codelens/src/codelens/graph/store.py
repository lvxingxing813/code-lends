import json
from pathlib import Path
from typing import Any, Dict

from codelens.graph.models import Graph


def save_graph(graph: Graph, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def load_graph(path: Path) -> Graph:
    return Graph.from_dict(_load_json(path))


def save_report(report: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def load_report(path: Path) -> Dict[str, Any]:
    return _load_json(path)


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

