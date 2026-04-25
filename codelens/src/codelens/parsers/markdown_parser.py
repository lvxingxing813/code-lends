import re
from pathlib import Path

from codelens.graph.models import Edge, Node
from codelens.parsers.common import ParseResult

HEADING_RE = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)


def parse_markdown_file(path: Path, root: Path) -> ParseResult:
    result = ParseResult()
    rel = path.relative_to(root).as_posix()

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        result.warn("FILE_PARSE_FAILED", rel, str(exc), blocking=False)
        return result

    document_id = "document:%s" % rel
    result.nodes.append(
        Node(
            id=document_id,
            type="Document",
            name=path.stem,
            path=rel,
            metadata={"language": "markdown"},
        )
    )

    for index, match in enumerate(HEADING_RE.finditer(text), start=1):
        level = len(match.group(1))
        title = match.group(2).strip()
        feature_id = "feature:%s:%d" % (rel, index)
        result.nodes.append(
            Node(
                id=feature_id,
                type="Feature",
                name=title,
                path=rel,
                metadata={"headingLevel": level},
            )
        )
        result.edges.append(Edge(source=document_id, target=feature_id, type="MENTIONS"))

    return result

