import re
from pathlib import Path
from typing import Optional

from codelens.graph.models import Edge, Node
from codelens.parsers.common import ParseResult

COMPONENT_RE = re.compile(
    r"(?:export\s+default\s+)?(?:export\s+)?(?:async\s+)?(?:function|const)\s+([A-Z][A-Za-z0-9_]*)"
)
FETCH_RE = re.compile(r"fetch\(\s*[\"']([^\"']+)[\"']\s*(?:,\s*\{(?P<options>.*?)\})?", re.DOTALL)
METHOD_RE = re.compile(r"method\s*:\s*[\"']([A-Za-z]+)[\"']")
INTERACTION_RE = re.compile(r"\b(onClick|onSubmit|onChange|onBlur|onFocus)=")
INTERACTION_TAG_RE = re.compile(
    r"<(?P<tag>[A-Za-z][A-Za-z0-9.]*)\b(?P<attrs>[^>]*)\b(?P<event>onClick|onSubmit|onChange|onBlur|onFocus)=\{?(?P<handler>[^}\s>]+)\}?[^>]*>(?P<body>.*?)</(?P=tag)>",
    re.DOTALL,
)
IMPORT_RE = re.compile(r"import\s+.*?\s+from\s+[\"']([^\"']+)[\"']")
STATE_RE = re.compile(r"\b(useState|useReducer|useContext|createContext|create|defineStore)\b")


def parse_frontend_file(path: Path, root: Path) -> ParseResult:
    result = ParseResult()
    rel = path.relative_to(root).as_posix()

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        result.warn("FILE_PARSE_FAILED", rel, str(exc), blocking=False)
        return result

    owner_id = _owner_node_id(path, root)
    owner_type = _owner_type(path, root)
    result.nodes.append(
        Node(
            id=owner_id,
            type=owner_type,
            name=_owner_name(path, root, owner_type),
            path=rel,
            metadata={
                "language": path.suffix.lstrip("."),
                "framework": _framework(path, root),
                "route": _route_for_next_page(path, root) if owner_type == "Page" else None,
                "stateApis": sorted(set(STATE_RE.findall(text))),
                "complexity": max(1, len(COMPONENT_RE.findall(text)) + len(INTERACTION_RE.findall(text))),
            },
        )
    )

    for component in COMPONENT_RE.findall(text):
        component_id = "component:%s:%s" % (rel, component)
        result.nodes.append(
            Node(
                id=component_id,
                type="Component",
                name=component,
                path=rel,
                metadata={"framework": "react"},
            )
        )
        result.edges.append(Edge(source=owner_id, target=component_id, type="DEPENDS"))

    for imported in IMPORT_RE.findall(text):
        target = _resolve_import_target(path, root, imported)
        result.edges.append(
            Edge(
                source=owner_id,
                target=target or "module:%s" % imported,
                type="DEPENDS",
                metadata={"import": imported, "confidence": 0.6},
            )
        )

    for match in FETCH_RE.finditer(text):
        route = match.group(1)
        options = match.group("options") or ""
        method_match = METHOD_RE.search(options)
        method = method_match.group(1).upper() if method_match else "GET"
        api_id = "api:%s %s" % (method, route)
        result.nodes.append(
            Node(
                id=api_id,
                type="API",
                name="%s %s" % (method, route),
                path=rel,
                metadata={"method": method, "route": route, "calledFrom": rel},
            )
        )
        result.edges.append(Edge(source=owner_id, target=api_id, type="CALLS"))

    for index, entry in enumerate(_interaction_entries(text), start=1):
        interaction = entry["event"]
        interaction_id = "feature:%s:%s:%d" % (rel, interaction, index)
        result.nodes.append(
            Node(
                id=interaction_id,
                type="Feature",
                name=entry["name"],
                path=rel,
                metadata={
                    "interaction": interaction,
                    "label": entry["label"],
                    "handler": entry["handler"],
                },
            )
        )
        result.edges.append(Edge(source=owner_id, target=interaction_id, type="DEPENDS"))

    return result


def _owner_node_id(path: Path, root: Path) -> str:
    rel = path.relative_to(root).as_posix()
    owner_type = _owner_type(path, root)
    if owner_type == "Page":
        return "page:%s" % rel
    if owner_type == "Component":
        return "component:%s" % rel
    return "module:%s" % rel


def _interaction_entries(text: str) -> list:
    entries = []
    for match in INTERACTION_TAG_RE.finditer(text):
        event = match.group("event")
        label = _clean_label(match.group("body"))
        handler = match.group("handler").strip("\"'")
        entries.append(
            {
                "event": event,
                "label": label,
                "handler": handler,
                "name": _interaction_name(event, label, handler),
            }
        )

    if entries:
        return entries

    return [
        {"event": event, "label": "", "handler": "", "name": _interaction_name(event, "", "")}
        for event in INTERACTION_RE.findall(text)
    ]


def _clean_label(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value)
    text = re.sub(r"\{[^}]+\}", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _interaction_name(event: str, label: str, handler: str) -> str:
    verbs = {
        "onClick": "点击",
        "onSubmit": "提交",
        "onChange": "变更",
        "onBlur": "失焦",
        "onFocus": "聚焦",
    }
    verb = verbs.get(event, event)
    target = label or handler
    return "%s：%s" % (verb, target) if target else verb


def _owner_type(path: Path, root: Path) -> str:
    rel = path.relative_to(root).as_posix()
    if "/app/" in "/%s" % rel and path.name in {"page.tsx", "page.jsx", "page.ts", "page.js"}:
        return "Page"
    if path.suffix in {".tsx", ".jsx"} or "/components/" in "/%s" % rel:
        return "Component"
    return "Module"


def _owner_name(path: Path, root: Path, owner_type: str) -> str:
    if owner_type == "Page":
        return _route_for_next_page(path, root).strip("/") or "root"
    return path.stem


def _route_for_next_page(path: Path, root: Path) -> str:
    rel_parts = path.relative_to(root).parts
    if "app" not in rel_parts:
        return "/"
    app_index = rel_parts.index("app")
    route_parts = rel_parts[app_index + 1 : -1]
    route = "/" + "/".join(route_parts)
    return route if route != "/" else "/"


def _framework(path: Path, root: Path) -> Optional[str]:
    rel = path.relative_to(root).as_posix()
    if "/app/" in "/%s" % rel or "/pages/" in "/%s" % rel:
        return "nextjs"
    if path.suffix in {".tsx", ".jsx"}:
        return "react"
    return None


def _resolve_import_target(path: Path, root: Path, imported: str) -> Optional[str]:
    if not imported.startswith("."):
        return None

    base = (path.parent / imported).resolve()
    candidates = []
    if base.suffix:
        candidates.append(base)
    else:
        for suffix in [".tsx", ".ts", ".jsx", ".js"]:
            candidates.append(base.with_suffix(suffix))
        for suffix in [".tsx", ".ts", ".jsx", ".js"]:
            candidates.append(base / ("index" + suffix))

    root = root.resolve()
    for candidate in candidates:
        try:
            candidate.relative_to(root)
        except ValueError:
            continue
        if candidate.exists():
            return _owner_node_id(candidate, root)
    return None
