from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class WarningItem:
    type: str
    message: str
    path: Optional[str] = None
    blocking: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "path": self.path,
            "message": self.message,
            "blocking": self.blocking,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WarningItem":
        return cls(
            type=str(data.get("type", "UNKNOWN")),
            path=data.get("path"),
            message=str(data.get("message", "")),
            blocking=bool(data.get("blocking", False)),
        )


@dataclass
class Node:
    id: str
    type: str
    name: str
    path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "path": self.path,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Node":
        return cls(
            id=str(data["id"]),
            type=str(data["type"]),
            name=str(data["name"]),
            path=data.get("path"),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class Edge:
    source: str
    target: str
    type: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "type": self.type,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Edge":
        return cls(
            source=str(data["source"]),
            target=str(data["target"]),
            type=str(data["type"]),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class Graph:
    root: str
    version: str = "0.1.0"
    generatedAt: str = field(default_factory=utc_now)
    nodes: List[Node] = field(default_factory=list)
    edges: List[Edge] = field(default_factory=list)
    warnings: List[WarningItem] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "root": self.root,
            "generatedAt": self.generatedAt,
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "warnings": [warning.to_dict() for warning in self.warnings],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Graph":
        return cls(
            version=str(data.get("version", "0.1.0")),
            root=str(data["root"]),
            generatedAt=str(data.get("generatedAt", utc_now())),
            nodes=[Node.from_dict(item) for item in data.get("nodes", [])],
            edges=[Edge.from_dict(item) for item in data.get("edges", [])],
            warnings=[WarningItem.from_dict(item) for item in data.get("warnings", [])],
        )

