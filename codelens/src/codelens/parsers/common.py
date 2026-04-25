from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple, Union

from codelens.graph.models import Edge, Node, WarningItem

IGNORED_DIRS = {
    ".codelens",
    ".git",
    ".next",
    ".pytest_cache",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
    ".venv",
}

SUPPORTED_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".md", ".mdx"}


class UnsupportedFile(ValueError):
    def __init__(self, path: str) -> None:
        super().__init__("Unsupported file type: %s" % path)


@dataclass
class ParseResult:
    nodes: List[Node] = field(default_factory=list)
    edges: List[Edge] = field(default_factory=list)
    warnings: List[WarningItem] = field(default_factory=list)

    def warn(
        self,
        warning_type: str,
        path: Optional[Union[Path, str]],
        message: str,
        blocking: bool,
    ) -> None:
        self.warnings.append(
            WarningItem(
                type=warning_type,
                path=str(path) if path is not None else None,
                message=message,
                blocking=blocking,
            )
        )


def collect_source_files(root: Path) -> Tuple[List[Path], List[WarningItem]]:
    files: List[Path] = []
    warnings: List[WarningItem] = []

    def on_error(error: OSError) -> None:
        warnings.append(
            WarningItem(
                type="DIRECTORY_ACCESS_FAILED",
                path=getattr(error, "filename", None),
                message=str(error),
                blocking=False,
            )
        )

    for dirpath, dirnames, filenames in os.walk(root, onerror=on_error):
        dirnames[:] = [name for name in dirnames if name not in IGNORED_DIRS]
        current = Path(dirpath)
        for filename in filenames:
            path = current / filename
            if path.suffix in SUPPORTED_SUFFIXES:
                files.append(path)

    return sorted(files), warnings


def iter_source_files(root: Path) -> List[Path]:
    files, _warnings = collect_source_files(root)
    return files
