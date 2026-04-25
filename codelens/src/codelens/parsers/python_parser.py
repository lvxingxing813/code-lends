import ast
from pathlib import Path
from typing import Optional, Tuple

from codelens.graph.models import Edge, Node
from codelens.parsers.common import ParseResult

HTTP_DECORATORS = {
    "get": "GET",
    "post": "POST",
    "put": "PUT",
    "patch": "PATCH",
    "delete": "DELETE",
}


def parse_python_file(path: Path, root: Path) -> ParseResult:
    result = ParseResult()
    rel = path.relative_to(root).as_posix()
    module_id = "module:%s" % rel

    try:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
    except (SyntaxError, UnicodeDecodeError) as exc:
        result.warn("FILE_PARSE_FAILED", rel, str(exc), blocking=False)
        return result

    functions = [item for item in ast.walk(tree) if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))]
    classes = [item for item in ast.walk(tree) if isinstance(item, ast.ClassDef)]
    result.nodes.append(
        Node(
            id=module_id,
            type="Module",
            name=path.stem,
            path=rel,
            metadata={
                "language": "python",
                "complexity": max(1, len(functions) + len(classes)),
            },
        )
    )

    for item in tree.body:
        if isinstance(item, (ast.Import, ast.ImportFrom)):
            for dependency in _import_names(item):
                result.edges.append(
                    Edge(
                        source=module_id,
                        target="module:%s" % dependency,
                        type="DEPENDS",
                        metadata={"confidence": 0.5},
                    )
                )
        if isinstance(item, ast.ClassDef):
            class_id = "class:%s:%s" % (rel, item.name)
            result.nodes.append(
                Node(
                    id=class_id,
                    type="DataModel",
                    name=item.name,
                    path=rel,
                    metadata={"language": "python", "kind": "class"},
                )
            )
            result.edges.append(Edge(source=module_id, target=class_id, type="DEPENDS"))
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _append_function_and_routes(result, item, module_id, rel)

    return result


def _append_function_and_routes(
    result: ParseResult,
    item: ast.AST,
    module_id: str,
    rel: str,
) -> None:
    function_name = getattr(item, "name")
    function_id = "function:%s:%s" % (rel, function_name)
    result.nodes.append(
        Node(
            id=function_id,
            type="Module",
            name=function_name,
            path=rel,
            metadata={"kind": "function", "language": "python"},
        )
    )
    result.edges.append(Edge(source=module_id, target=function_id, type="DEPENDS"))

    for decorator in getattr(item, "decorator_list", []):
        api = _extract_fastapi_route(decorator)
        if api is None:
            continue
        method, route = api
        api_id = "api:%s %s" % (method, route)
        result.nodes.append(
            Node(
                id=api_id,
                type="API",
                name="%s %s" % (method, route),
                path=rel,
                metadata={"method": method, "route": route, "framework": "fastapi"},
            )
        )
        result.edges.append(Edge(source=module_id, target=api_id, type="EXPOSES"))
        result.edges.append(Edge(source=api_id, target=function_id, type="CALLS"))
        result.edges.append(Edge(source=api_id, target=module_id, type="CALLS"))


def _extract_fastapi_route(node: ast.AST) -> Optional[Tuple[str, str]]:
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        return None

    method = HTTP_DECORATORS.get(node.func.attr)
    if method is None:
        return None

    route = None
    if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
        route = node.args[0].value
    for keyword in node.keywords:
        if keyword.arg in {"path", "url"} and isinstance(keyword.value, ast.Constant):
            if isinstance(keyword.value.value, str):
                route = keyword.value.value

    if route is None:
        return None
    return method, route


def _import_names(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if isinstance(node, ast.ImportFrom) and node.module:
        return [node.module]
    return []

