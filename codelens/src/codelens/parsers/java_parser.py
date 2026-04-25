import re
from pathlib import Path

from codelens.graph.models import Edge, Node
from codelens.parsers.common import ParseResult

PACKAGE_RE = re.compile(r"package\s+([A-Za-z0-9_.]+)\s*;")
CLASS_RE = re.compile(r"\bclass\s+([A-Za-z0-9_]+)")
MAPPING_RE = re.compile(
    r"@(GetMapping|PostMapping|PutMapping|PatchMapping|DeleteMapping|RequestMapping)\(\s*[\"']([^\"']+)[\"']"
)

METHODS = {
    "GetMapping": "GET",
    "PostMapping": "POST",
    "PutMapping": "PUT",
    "PatchMapping": "PATCH",
    "DeleteMapping": "DELETE",
    "RequestMapping": "GET",
}


def parse_java_file(path: Path, root: Path) -> ParseResult:
    result = ParseResult()
    rel = path.relative_to(root).as_posix()

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        result.warn("FILE_PARSE_FAILED", rel, str(exc), blocking=False)
        return result

    package_match = PACKAGE_RE.search(text)
    class_match = CLASS_RE.search(text)
    package = package_match.group(1) if package_match else None
    class_name = class_match.group(1) if class_match else path.stem
    module_id = "module:%s" % rel

    result.nodes.append(
        Node(
            id=module_id,
            type="Module",
            name=class_name,
            path=rel,
            metadata={"language": "java", "package": package, "complexity": max(1, len(MAPPING_RE.findall(text)))},
        )
    )

    for annotation, route in MAPPING_RE.findall(text):
        method = METHODS[annotation]
        api_id = "api:%s %s" % (method, route)
        result.nodes.append(
            Node(
                id=api_id,
                type="API",
                name="%s %s" % (method, route),
                path=rel,
                metadata={"framework": "spring", "method": method, "route": route},
            )
        )
        result.edges.append(Edge(source=module_id, target=api_id, type="EXPOSES"))
        result.edges.append(Edge(source=api_id, target=module_id, type="CALLS"))

    return result

