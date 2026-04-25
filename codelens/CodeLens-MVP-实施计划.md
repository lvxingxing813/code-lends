# CodeLens MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable CodeLens MVP that scans a repository, builds a feature/dependency graph, analyzes requirement impact, and serves a visual report.

**Architecture:** Use Python for the core engine, CLI, graph construction, risk scoring, and API service. Use a React/Next.js web app for graph, heatmap, test matrix, and requirement issue visualization. Keep LLM integration optional so the demo can run offline with deterministic rule-based analysis.

**Tech Stack:** Python 3.11+, Typer, FastAPI, NetworkX, Pydantic, pytest, React/Next.js, AntV G6/G2/S2, Docker.

---

## Scope

This plan covers the MVP described in `CodeLens-设计整理.md` plus the later review additions:

- Multi-language parsing must include backend languages and frontend frameworks.
- Frontend parsing must extract pages, routes, components, state modules, API calls, and interaction entry points.
- Local input failures must degrade gracefully with clear warnings.
- The final deliverable must include CLI, core package, Web UI, example project, Docker setup, and test report.
- Python is the primary implementation language for the core engine.

Out of MVP scope:

- Full production-grade semantic understanding for every language.
- Live Yuque MCP integration.
- Fully autonomous LLM agent orchestration.
- IDE plugin.
- CI/CD continuous learning.

---

## Target User Flow

```text
install -> scan repository -> generate .codelens/graph.json -> analyze requirement -> generate .codelens/report.json -> serve Web UI -> view report
```

Commands:

```bash
codelens scan ../demo-project
codelens analyze "新增用户批量导入功能，支持 Excel 上传"
codelens serve
```

Expected outputs:

```text
.codelens/graph.json
.codelens/report.json
http://localhost:8000
```

---

## File Structure

Create this structure from the current repository root:

```text
.
├── pyproject.toml
├── README.md
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── examples/
│   └── demo-project/
│       ├── frontend/
│       │   ├── package.json
│       │   └── src/
│       │       ├── app/
│       │       │   ├── login/page.tsx
│       │       │   └── orders/page.tsx
│       │       ├── components/LoginForm.tsx
│       │       └── lib/api.ts
│       └── backend/
│           ├── app/
│           │   ├── main.py
│           │   ├── auth.py
│           │   └── orders.py
│           └── requirements.txt
├── src/
│   └── codelens/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── api/
│       │   ├── __init__.py
│       │   └── server.py
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── code_agent.py
│       │   ├── dep_agent.py
│       │   ├── doc_agent.py
│       │   ├── reason_agent.py
│       │   └── review_agent.py
│       ├── graph/
│       │   ├── __init__.py
│       │   ├── models.py
│       │   ├── store.py
│       │   ├── builder.py
│       │   └── query.py
│       ├── parsers/
│       │   ├── __init__.py
│       │   ├── common.py
│       │   ├── python_parser.py
│       │   ├── frontend_parser.py
│       │   ├── java_parser.py
│       │   └── markdown_parser.py
│       ├── analysis/
│       │   ├── __init__.py
│       │   ├── impact.py
│       │   ├── risk.py
│       │   └── regression.py
│       └── demo/
│           ├── __init__.py
│           └── fixtures.py
├── tests/
│   ├── test_cli.py
│   ├── test_error_handling.py
│   ├── test_graph_store.py
│   ├── test_impact.py
│   ├── parsers/
│   │   ├── test_python_parser.py
│   │   ├── test_frontend_parser.py
│   │   ├── test_java_parser.py
│   │   └── test_markdown_parser.py
│   └── snapshots/
│       ├── graph.demo.json
│       └── report.demo.json
└── web/
    ├── package.json
    ├── next.config.js
    ├── tsconfig.json
    └── src/
        ├── app/
        │   ├── page.tsx
        │   └── impact/page.tsx
        ├── components/
        │   ├── GraphView.tsx
        │   ├── HeatMap.tsx
        │   ├── TestMatrix.tsx
        │   └── IssueAnnotation.tsx
        └── lib/api.ts
```

Responsibility boundaries:

- `src/codelens/parsers`: Parse source files and docs into normalized code/document elements.
- `src/codelens/graph`: Define graph schema, persist graph JSON, and query dependency paths.
- `src/codelens/agents`: Orchestrate parser, graph, impact, and review modules.
- `src/codelens/analysis`: Deterministic impact, risk, and regression logic.
- `src/codelens/cli.py`: User-facing `scan`, `analyze`, and `serve` commands.
- `src/codelens/api/server.py`: FastAPI routes consumed by Web UI.
- `web/src/components`: Visualization-only components.

---

## Data Contracts

### Graph JSON

```json
{
  "version": "0.1.0",
  "root": "/absolute/project/path",
  "generatedAt": "2026-04-25T00:00:00Z",
  "nodes": [
    {
      "id": "page:frontend/src/app/login/page.tsx",
      "type": "Page",
      "name": "login",
      "path": "frontend/src/app/login/page.tsx",
      "metadata": {
        "framework": "nextjs",
        "route": "/login",
        "complexity": 2,
        "changeFreq": 0,
        "bugHistory": 0
      }
    }
  ],
  "edges": [
    {
      "source": "page:frontend/src/app/login/page.tsx",
      "target": "api:POST /api/login",
      "type": "CALLS",
      "metadata": {
        "confidence": 0.8
      }
    }
  ],
  "warnings": [
    {
      "type": "FILE_PARSE_FAILED",
      "path": "docs/broken.md",
      "message": "Unsupported markdown encoding",
      "blocking": false
    }
  ]
}
```

### Report JSON

```json
{
  "requirement": "新增用户批量导入功能，支持 Excel 上传",
  "directImpact": [
    "page:frontend/src/app/users/import/page.tsx"
  ],
  "indirectImpact": [
    "api:POST /api/users/import",
    "module:backend/app/users.py"
  ],
  "riskMap": {
    "api:POST /api/users/import": {
      "score": 0.82,
      "reason": "涉及文件上传、用户数据写入、权限校验"
    }
  },
  "regressionList": [
    {
      "feature": "用户登录",
      "priority": "P1",
      "reason": "导入功能依赖登录态和权限校验"
    }
  ],
  "issues": [
    {
      "type": "边界缺失",
      "description": "需求未说明单次上传文件大小和行数上限",
      "severity": "medium",
      "suggestion": "补充文件大小、行数、失败回滚策略"
    }
  ],
  "warnings": []
}
```

---

## Task 1: Project Bootstrap

**Files:**
- Create: `pyproject.toml`
- Create: `src/codelens/__init__.py`
- Create: `src/codelens/config.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Create Python package metadata**

Add `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "codelens"
version = "0.1.0"
description = "Project graph and requirement impact analysis MVP"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.110",
  "networkx>=3.2",
  "pydantic>=2.6",
  "typer>=0.12",
  "uvicorn>=0.27"
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
  "pytest-cov>=4.1",
  "ruff>=0.4"
]

[project.scripts]
codelens = "codelens.cli:app"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[tool.ruff]
line-length = 100
target-version = "py311"
```

- [ ] **Step 2: Create package version**

Add `src/codelens/__init__.py`:

```python
__version__ = "0.1.0"
```

- [ ] **Step 3: Create config constants**

Add `src/codelens/config.py`:

```python
from pathlib import Path

CODELENS_DIR = ".codelens"
GRAPH_FILE = "graph.json"
REPORT_FILE = "report.json"


def codelens_dir(root: Path) -> Path:
    return root / CODELENS_DIR


def graph_path(root: Path) -> Path:
    return codelens_dir(root) / GRAPH_FILE


def report_path(root: Path) -> Path:
    return codelens_dir(root) / REPORT_FILE
```

- [ ] **Step 4: Write CLI smoke test**

Add `tests/test_cli.py`:

```python
from typer.testing import CliRunner

from codelens.cli import app


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert "0.1.0" in result.stdout
```

- [ ] **Step 5: Run test and confirm it fails before CLI exists**

Run:

```bash
pytest tests/test_cli.py::test_cli_version -v
```

Expected:

```text
ModuleNotFoundError: No module named 'codelens.cli'
```

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml src/codelens/__init__.py src/codelens/config.py tests/test_cli.py
git commit -m "chore: bootstrap codelens python package"
```

---

## Task 2: CLI Shell

**Files:**
- Create: `src/codelens/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Implement minimal Typer app**

Add `src/codelens/cli.py`:

```python
from pathlib import Path

import typer

from codelens import __version__

app = typer.Typer(no_args_is_help=True)


@app.command()
def version() -> None:
    typer.echo(f"codelens {__version__}")


@app.command()
def scan(project: Path) -> None:
    typer.echo(f"scan not implemented: {project}")
    raise typer.Exit(code=1)


@app.command()
def analyze(requirement: str, project: Path = Path(".")) -> None:
    typer.echo(f"analyze not implemented: {requirement} in {project}")
    raise typer.Exit(code=1)


@app.command()
def serve(project: Path = Path("."), host: str = "127.0.0.1", port: int = 8000) -> None:
    typer.echo(f"serve not implemented: {project} {host}:{port}")
    raise typer.Exit(code=1)
```

- [ ] **Step 2: Add command existence tests**

Replace `tests/test_cli.py` with:

```python
from pathlib import Path

from typer.testing import CliRunner

from codelens.cli import app


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert "0.1.0" in result.stdout


def test_scan_command_exists(tmp_path: Path):
    runner = CliRunner()
    result = runner.invoke(app, ["scan", str(tmp_path)])

    assert result.exit_code == 1
    assert "scan not implemented" in result.stdout


def test_analyze_command_exists(tmp_path: Path):
    runner = CliRunner()
    result = runner.invoke(app, ["analyze", "新增批量导入", "--project", str(tmp_path)])

    assert result.exit_code == 1
    assert "analyze not implemented" in result.stdout
```

- [ ] **Step 3: Run CLI tests**

Run:

```bash
pytest tests/test_cli.py -v
```

Expected:

```text
3 passed
```

- [ ] **Step 4: Commit**

```bash
git add src/codelens/cli.py tests/test_cli.py
git commit -m "feat: add codelens cli shell"
```

---

## Task 3: Graph Schema And Persistence

**Files:**
- Create: `src/codelens/graph/__init__.py`
- Create: `src/codelens/graph/models.py`
- Create: `src/codelens/graph/store.py`
- Create: `tests/test_graph_store.py`

- [ ] **Step 1: Write graph persistence tests**

Add `tests/test_graph_store.py`:

```python
from pathlib import Path

from codelens.graph.models import Edge, Graph, Node, WarningItem
from codelens.graph.store import load_graph, save_graph


def test_save_and_load_graph(tmp_path: Path):
    graph = Graph(
        root=str(tmp_path),
        nodes=[
            Node(
                id="module:auth",
                type="Module",
                name="auth",
                path="app/auth.py",
                metadata={"complexity": 2},
            )
        ],
        edges=[
            Edge(
                source="module:auth",
                target="api:POST /api/login",
                type="EXPOSES",
                metadata={"confidence": 1.0},
            )
        ],
        warnings=[
            WarningItem(
                type="FILE_PARSE_FAILED",
                path="broken.py",
                message="invalid syntax",
                blocking=False,
            )
        ],
    )

    output = tmp_path / ".codelens" / "graph.json"
    save_graph(graph, output)
    loaded = load_graph(output)

    assert loaded.root == str(tmp_path)
    assert loaded.nodes[0].id == "module:auth"
    assert loaded.edges[0].type == "EXPOSES"
    assert loaded.warnings[0].blocking is False
```

- [ ] **Step 2: Run test and confirm it fails before models exist**

Run:

```bash
pytest tests/test_graph_store.py -v
```

Expected:

```text
ModuleNotFoundError: No module named 'codelens.graph'
```

- [ ] **Step 3: Implement graph models**

Add `src/codelens/graph/__init__.py`:

```python
from codelens.graph.models import Edge, Graph, Node, WarningItem

__all__ = ["Edge", "Graph", "Node", "WarningItem"]
```

Add `src/codelens/graph/models.py`:

```python
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

NodeType = Literal["Feature", "Module", "API", "Page", "Component", "DataModel", "Document"]
EdgeType = Literal["CALLS", "DEPENDS", "READS", "WRITES", "ROUTES_TO", "EXPOSES", "MENTIONS"]


class WarningItem(BaseModel):
    type: str
    path: str | None = None
    message: str
    blocking: bool = False


class Node(BaseModel):
    id: str
    type: NodeType
    name: str
    path: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Edge(BaseModel):
    source: str
    target: str
    type: EdgeType
    metadata: dict[str, Any] = Field(default_factory=dict)


class Graph(BaseModel):
    version: str = "0.1.0"
    root: str
    generatedAt: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    warnings: list[WarningItem] = Field(default_factory=list)
```

- [ ] **Step 4: Implement graph store**

Add `src/codelens/graph/store.py`:

```python
import json
from pathlib import Path

from codelens.graph.models import Graph


def save_graph(graph: Graph, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(graph.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_graph(path: Path) -> Graph:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return Graph.model_validate(raw)
```

- [ ] **Step 5: Run graph store tests**

Run:

```bash
pytest tests/test_graph_store.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 6: Commit**

```bash
git add src/codelens/graph tests/test_graph_store.py
git commit -m "feat: add graph schema and persistence"
```

---

## Task 4: Parser Common Types And Error Handling

**Files:**
- Create: `src/codelens/parsers/__init__.py`
- Create: `src/codelens/parsers/common.py`
- Create: `tests/test_error_handling.py`

- [ ] **Step 1: Write parser error handling tests**

Add `tests/test_error_handling.py`:

```python
from pathlib import Path

from codelens.parsers.common import ParseResult, UnsupportedFile, iter_source_files


def test_parse_result_collects_warnings():
    result = ParseResult()
    result.warn("FILE_PARSE_FAILED", Path("bad.py"), "invalid syntax", blocking=False)

    assert result.warnings[0].type == "FILE_PARSE_FAILED"
    assert result.warnings[0].path == "bad.py"
    assert result.warnings[0].blocking is False


def test_iter_source_files_skips_common_noise(tmp_path: Path):
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "ignored.ts").write_text("export const x = 1", encoding="utf-8")
    (tmp_path / "app.py").write_text("def login(): pass", encoding="utf-8")

    files = list(iter_source_files(tmp_path))

    assert files == [tmp_path / "app.py"]


def test_unsupported_file_message():
    error = UnsupportedFile("image.png")

    assert "image.png" in str(error)
```

- [ ] **Step 2: Run tests and confirm failure**

Run:

```bash
pytest tests/test_error_handling.py -v
```

Expected:

```text
ModuleNotFoundError: No module named 'codelens.parsers'
```

- [ ] **Step 3: Implement common parser utilities**

Add `src/codelens/parsers/__init__.py`:

```python
from codelens.parsers.common import ParseResult

__all__ = ["ParseResult"]
```

Add `src/codelens/parsers/common.py`:

```python
from pathlib import Path

from pydantic import BaseModel, Field

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

SUPPORTED_SUFFIXES = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".java",
    ".md",
    ".mdx",
}


class UnsupportedFile(ValueError):
    def __init__(self, path: str) -> None:
        super().__init__(f"Unsupported file type: {path}")


class ParseResult(BaseModel):
    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    warnings: list[WarningItem] = Field(default_factory=list)

    def warn(self, warning_type: str, path: Path | str | None, message: str, blocking: bool) -> None:
        self.warnings.append(
            WarningItem(
                type=warning_type,
                path=str(path) if path is not None else None,
                message=message,
                blocking=blocking,
            )
        )


def iter_source_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix in SUPPORTED_SUFFIXES:
            files.append(path)
    return sorted(files)
```

- [ ] **Step 4: Run error handling tests**

Run:

```bash
pytest tests/test_error_handling.py -v
```

Expected:

```text
3 passed
```

- [ ] **Step 5: Commit**

```bash
git add src/codelens/parsers tests/test_error_handling.py
git commit -m "feat: add parser common types and warnings"
```

---

## Task 5: Python Backend Parser

**Files:**
- Create: `src/codelens/parsers/python_parser.py`
- Create: `tests/parsers/test_python_parser.py`

- [ ] **Step 1: Write Python parser tests**

Add `tests/parsers/test_python_parser.py`:

```python
from pathlib import Path

from codelens.parsers.python_parser import parse_python_file


def test_parse_fastapi_routes_and_functions(tmp_path: Path):
    source = tmp_path / "app" / "auth.py"
    source.parent.mkdir()
    source.write_text(
        """
from fastapi import APIRouter

router = APIRouter()

@router.post("/api/login")
def login():
    return {"ok": True}

def check_permission():
    return True
""".strip(),
        encoding="utf-8",
    )

    result = parse_python_file(source, tmp_path)

    node_ids = {node.id for node in result.nodes}
    assert "module:app/auth.py" in node_ids
    assert "api:POST /api/login" in node_ids
    assert "function:app/auth.py:login" in node_ids
    assert any(edge.source == "module:app/auth.py" and edge.target == "api:POST /api/login" for edge in result.edges)


def test_parse_invalid_python_returns_warning(tmp_path: Path):
    source = tmp_path / "broken.py"
    source.write_text("def broken(:", encoding="utf-8")

    result = parse_python_file(source, tmp_path)

    assert result.nodes == []
    assert result.warnings[0].type == "FILE_PARSE_FAILED"
    assert result.warnings[0].blocking is False
```

- [ ] **Step 2: Run parser tests and confirm failure**

Run:

```bash
pytest tests/parsers/test_python_parser.py -v
```

Expected:

```text
ModuleNotFoundError: No module named 'codelens.parsers.python_parser'
```

- [ ] **Step 3: Implement Python parser**

Add `src/codelens/parsers/python_parser.py`:

```python
import ast
from pathlib import Path

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
    module_id = f"module:{rel}"

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError) as exc:
        result.warn("FILE_PARSE_FAILED", rel, str(exc), blocking=False)
        return result

    result.nodes.append(
        Node(
            id=module_id,
            type="Module",
            name=path.stem,
            path=rel,
            metadata={"language": "python", "complexity": 1},
        )
    )

    for item in tree.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            function_id = f"function:{rel}:{item.name}"
            result.nodes.append(
                Node(
                    id=function_id,
                    type="Module",
                    name=item.name,
                    path=rel,
                    metadata={"kind": "function", "language": "python"},
                )
            )
            result.edges.append(Edge(source=module_id, target=function_id, type="DEPENDS"))

            for decorator in item.decorator_list:
                api = _extract_fastapi_route(decorator)
                if api is None:
                    continue
                method, route = api
                api_id = f"api:{method} {route}"
                result.nodes.append(
                    Node(
                        id=api_id,
                        type="API",
                        name=f"{method} {route}",
                        path=rel,
                        metadata={"method": method, "route": route, "framework": "fastapi"},
                    )
                )
                result.edges.append(Edge(source=module_id, target=api_id, type="EXPOSES"))
                result.edges.append(Edge(source=api_id, target=function_id, type="CALLS"))

    return result


def _extract_fastapi_route(node: ast.AST) -> tuple[str, str] | None:
    if not isinstance(node, ast.Call):
        return None
    if not isinstance(node.func, ast.Attribute):
        return None
    method = HTTP_DECORATORS.get(node.func.attr)
    if method is None:
        return None
    if not node.args or not isinstance(node.args[0], ast.Constant):
        return None
    if not isinstance(node.args[0].value, str):
        return None
    return method, node.args[0].value
```

- [ ] **Step 4: Run Python parser tests**

Run:

```bash
pytest tests/parsers/test_python_parser.py -v
```

Expected:

```text
2 passed
```

- [ ] **Step 5: Commit**

```bash
git add src/codelens/parsers/python_parser.py tests/parsers/test_python_parser.py
git commit -m "feat: parse python backend routes"
```

---

## Task 6: Frontend Parser For TS/JS, React, Next.js

**Files:**
- Create: `src/codelens/parsers/frontend_parser.py`
- Create: `tests/parsers/test_frontend_parser.py`

- [ ] **Step 1: Write frontend parser tests**

Add `tests/parsers/test_frontend_parser.py`:

```python
from pathlib import Path

from codelens.parsers.frontend_parser import parse_frontend_file


def test_parse_next_page_and_api_call(tmp_path: Path):
    page = tmp_path / "frontend" / "src" / "app" / "login" / "page.tsx"
    page.parent.mkdir(parents=True)
    page.write_text(
        """
import { LoginForm } from "../../components/LoginForm";

export default function LoginPage() {
  return <LoginForm />;
}

async function submit() {
  await fetch("/api/login", { method: "POST" });
}
""".strip(),
        encoding="utf-8",
    )

    result = parse_frontend_file(page, tmp_path)

    node_ids = {node.id for node in result.nodes}
    assert "page:frontend/src/app/login/page.tsx" in node_ids
    assert "component:frontend/src/app/login/page.tsx:LoginPage" in node_ids
    assert "api:POST /api/login" in node_ids
    assert any(edge.source == "page:frontend/src/app/login/page.tsx" and edge.target == "api:POST /api/login" for edge in result.edges)


def test_parse_component_with_interaction_entry(tmp_path: Path):
    component = tmp_path / "frontend" / "src" / "components" / "LoginForm.tsx"
    component.parent.mkdir(parents=True)
    component.write_text(
        """
export function LoginForm() {
  return <button onClick={login}>登录</button>;
}
""".strip(),
        encoding="utf-8",
    )

    result = parse_frontend_file(component, tmp_path)

    assert any(node.type == "Component" and node.name == "LoginForm" for node in result.nodes)
    assert any(node.metadata.get("interaction") == "onClick" for node in result.nodes)
```

- [ ] **Step 2: Run frontend parser tests and confirm failure**

Run:

```bash
pytest tests/parsers/test_frontend_parser.py -v
```

Expected:

```text
ModuleNotFoundError: No module named 'codelens.parsers.frontend_parser'
```

- [ ] **Step 3: Implement frontend parser**

Add `src/codelens/parsers/frontend_parser.py`:

```python
import re
from pathlib import Path

from codelens.graph.models import Edge, Node
from codelens.parsers.common import ParseResult

COMPONENT_RE = re.compile(r"(?:export\s+default\s+)?(?:function|const)\s+([A-Z][A-Za-z0-9_]*)")
FETCH_RE = re.compile(r"fetch\(\s*[\"']([^\"']+)[\"']\s*(?:,\s*\{(?P<options>.*?)\})?", re.DOTALL)
METHOD_RE = re.compile(r"method\s*:\s*[\"']([A-Za-z]+)[\"']")
INTERACTION_RE = re.compile(r"\b(onClick|onSubmit|onChange|onBlur|onFocus)=")
IMPORT_RE = re.compile(r"import\s+.*?\s+from\s+[\"']([^\"']+)[\"']")


def parse_frontend_file(path: Path, root: Path) -> ParseResult:
    result = ParseResult()
    rel = path.relative_to(root).as_posix()

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        result.warn("FILE_PARSE_FAILED", rel, str(exc), blocking=False)
        return result

    owner_id = _owner_node_id(path, root)
    owner_type = "Page" if "/app/" in f"/{rel}" and path.name in {"page.tsx", "page.jsx"} else "Component"
    result.nodes.append(
        Node(
            id=owner_id,
            type=owner_type,
            name=_route_name(path, root) if owner_type == "Page" else path.stem,
            path=rel,
            metadata={
                "language": path.suffix.lstrip("."),
                "framework": "nextjs" if "/app/" in f"/{rel}" else "react",
                "route": _route_for_next_page(path, root) if owner_type == "Page" else None,
            },
        )
    )

    for component in COMPONENT_RE.findall(text):
        component_id = f"component:{rel}:{component}"
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
        result.edges.append(
            Edge(
                source=owner_id,
                target=f"module:{imported}",
                type="DEPENDS",
                metadata={"import": imported, "confidence": 0.6},
            )
        )

    for match in FETCH_RE.finditer(text):
        route = match.group(1)
        options = match.group("options") or ""
        method_match = METHOD_RE.search(options)
        method = method_match.group(1).upper() if method_match else "GET"
        api_id = f"api:{method} {route}"
        result.nodes.append(
            Node(
                id=api_id,
                type="API",
                name=f"{method} {route}",
                path=rel,
                metadata={"method": method, "route": route, "calledFrom": rel},
            )
        )
        result.edges.append(Edge(source=owner_id, target=api_id, type="CALLS"))

    for interaction in INTERACTION_RE.findall(text):
        interaction_id = f"feature:{rel}:{interaction}"
        result.nodes.append(
            Node(
                id=interaction_id,
                type="Feature",
                name=interaction,
                path=rel,
                metadata={"interaction": interaction},
            )
        )
        result.edges.append(Edge(source=owner_id, target=interaction_id, type="DEPENDS"))

    return result


def _owner_node_id(path: Path, root: Path) -> str:
    rel = path.relative_to(root).as_posix()
    if "/app/" in f"/{rel}" and path.name in {"page.tsx", "page.jsx"}:
        return f"page:{rel}"
    return f"component:{rel}"


def _route_for_next_page(path: Path, root: Path) -> str:
    rel_parts = path.relative_to(root).parts
    if "app" not in rel_parts:
        return "/"
    app_index = rel_parts.index("app")
    route_parts = rel_parts[app_index + 1 : -1]
    route = "/" + "/".join(route_parts)
    return route if route != "/" else "/"


def _route_name(path: Path, root: Path) -> str:
    route = _route_for_next_page(path, root)
    return route.strip("/") or "root"
```

- [ ] **Step 4: Run frontend parser tests**

Run:

```bash
pytest tests/parsers/test_frontend_parser.py -v
```

Expected:

```text
2 passed
```

- [ ] **Step 5: Commit**

```bash
git add src/codelens/parsers/frontend_parser.py tests/parsers/test_frontend_parser.py
git commit -m "feat: parse frontend pages components and api calls"
```

---

## Task 7: Java Parser

**Files:**
- Create: `src/codelens/parsers/java_parser.py`
- Create: `tests/parsers/test_java_parser.py`

- [ ] **Step 1: Write Java parser tests**

Add `tests/parsers/test_java_parser.py`:

```python
from pathlib import Path

from codelens.parsers.java_parser import parse_java_file


def test_parse_spring_controller(tmp_path: Path):
    source = tmp_path / "src" / "main" / "java" / "com" / "demo" / "AuthController.java"
    source.parent.mkdir(parents=True)
    source.write_text(
        """
package com.demo;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class AuthController {
    @PostMapping("/api/login")
    public String login() {
        return "ok";
    }
}
""".strip(),
        encoding="utf-8",
    )

    result = parse_java_file(source, tmp_path)

    node_ids = {node.id for node in result.nodes}
    assert "module:src/main/java/com/demo/AuthController.java" in node_ids
    assert "api:POST /api/login" in node_ids
    assert any(edge.type == "EXPOSES" for edge in result.edges)
```

- [ ] **Step 2: Run Java parser tests and confirm failure**

Run:

```bash
pytest tests/parsers/test_java_parser.py -v
```

Expected:

```text
ModuleNotFoundError: No module named 'codelens.parsers.java_parser'
```

- [ ] **Step 3: Implement Java parser**

Add `src/codelens/parsers/java_parser.py`:

```python
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
    module_id = f"module:{rel}"

    result.nodes.append(
        Node(
            id=module_id,
            type="Module",
            name=class_name,
            path=rel,
            metadata={"language": "java", "package": package},
        )
    )

    for annotation, route in MAPPING_RE.findall(text):
        method = METHODS[annotation]
        api_id = f"api:{method} {route}"
        result.nodes.append(
            Node(
                id=api_id,
                type="API",
                name=f"{method} {route}",
                path=rel,
                metadata={"framework": "spring", "method": method, "route": route},
            )
        )
        result.edges.append(Edge(source=module_id, target=api_id, type="EXPOSES"))

    return result
```

- [ ] **Step 4: Run Java parser tests**

Run:

```bash
pytest tests/parsers/test_java_parser.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: Commit**

```bash
git add src/codelens/parsers/java_parser.py tests/parsers/test_java_parser.py
git commit -m "feat: parse spring java controllers"
```

---

## Task 8: Markdown Document Parser

**Files:**
- Create: `src/codelens/parsers/markdown_parser.py`
- Create: `tests/parsers/test_markdown_parser.py`

- [ ] **Step 1: Write Markdown parser tests**

Add `tests/parsers/test_markdown_parser.py`:

```python
from pathlib import Path

from codelens.parsers.markdown_parser import parse_markdown_file


def test_parse_markdown_headings_as_features(tmp_path: Path):
    doc = tmp_path / "docs" / "prd.md"
    doc.parent.mkdir()
    doc.write_text(
        """
# 用户登录

支持手机号验证码登录。

## 批量导入

支持 Excel 上传。
""".strip(),
        encoding="utf-8",
    )

    result = parse_markdown_file(doc, tmp_path)

    names = {node.name for node in result.nodes}
    assert "用户登录" in names
    assert "批量导入" in names
    assert any(edge.type == "MENTIONS" for edge in result.edges)
```

- [ ] **Step 2: Run Markdown parser tests and confirm failure**

Run:

```bash
pytest tests/parsers/test_markdown_parser.py -v
```

Expected:

```text
ModuleNotFoundError: No module named 'codelens.parsers.markdown_parser'
```

- [ ] **Step 3: Implement Markdown parser**

Add `src/codelens/parsers/markdown_parser.py`:

```python
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

    document_id = f"document:{rel}"
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
        feature_id = f"feature:{rel}:{index}"
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
```

- [ ] **Step 4: Run Markdown parser tests**

Run:

```bash
pytest tests/parsers/test_markdown_parser.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: Commit**

```bash
git add src/codelens/parsers/markdown_parser.py tests/parsers/test_markdown_parser.py
git commit -m "feat: parse markdown features"
```

---

## Task 9: CodeAgent Scan Orchestration

**Files:**
- Create: `src/codelens/agents/__init__.py`
- Create: `src/codelens/agents/code_agent.py`
- Modify: `src/codelens/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Add scan integration test**

Append to `tests/test_cli.py`:

```python

def test_scan_generates_graph_json(tmp_path: Path):
    app_file = tmp_path / "app.py"
    app_file.write_text(
        """
from fastapi import APIRouter
router = APIRouter()
@router.post("/api/login")
def login():
    return {"ok": True}
""".strip(),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(app, ["scan", str(tmp_path)])

    assert result.exit_code == 0
    assert (tmp_path / ".codelens" / "graph.json").exists()
    assert "nodes" in (tmp_path / ".codelens" / "graph.json").read_text(encoding="utf-8")
```

- [ ] **Step 2: Run test and confirm current scan fails**

Run:

```bash
pytest tests/test_cli.py::test_scan_generates_graph_json -v
```

Expected:

```text
FAILED
```

because `scan` still exits with code `1`.

- [ ] **Step 3: Implement CodeAgent**

Add `src/codelens/agents/__init__.py`:

```python
from codelens.agents.code_agent import scan_project

__all__ = ["scan_project"]
```

Add `src/codelens/agents/code_agent.py`:

```python
from pathlib import Path

from codelens.graph.models import Graph
from codelens.parsers.common import iter_source_files
from codelens.parsers.frontend_parser import parse_frontend_file
from codelens.parsers.java_parser import parse_java_file
from codelens.parsers.markdown_parser import parse_markdown_file
from codelens.parsers.python_parser import parse_python_file


def scan_project(root: Path) -> Graph:
    root = root.resolve()
    graph = Graph(root=str(root))

    for path in iter_source_files(root):
        if path.suffix == ".py":
            result = parse_python_file(path, root)
        elif path.suffix in {".ts", ".tsx", ".js", ".jsx"}:
            result = parse_frontend_file(path, root)
        elif path.suffix == ".java":
            result = parse_java_file(path, root)
        elif path.suffix in {".md", ".mdx"}:
            result = parse_markdown_file(path, root)
        else:
            continue

        graph.nodes.extend(result.nodes)
        graph.edges.extend(result.edges)
        graph.warnings.extend(result.warnings)

    return _dedupe_graph(graph)


def _dedupe_graph(graph: Graph) -> Graph:
    nodes = {}
    for node in graph.nodes:
        nodes[node.id] = node

    edges = {}
    for edge in graph.edges:
        key = (edge.source, edge.target, edge.type)
        edges[key] = edge

    graph.nodes = list(nodes.values())
    graph.edges = list(edges.values())
    return graph
```

- [ ] **Step 4: Wire scan CLI to CodeAgent**

Replace `scan` in `src/codelens/cli.py`:

```python
@app.command()
def scan(project: Path) -> None:
    from codelens.agents.code_agent import scan_project
    from codelens.config import graph_path
    from codelens.graph.store import save_graph

    if not project.exists():
        typer.echo(f"Project path does not exist: {project}")
        raise typer.Exit(code=2)

    graph = scan_project(project)
    output = graph_path(project)
    save_graph(graph, output)
    typer.echo(f"Graph written: {output}")
    typer.echo(f"Nodes: {len(graph.nodes)}")
    typer.echo(f"Edges: {len(graph.edges)}")
    if graph.warnings:
        typer.echo(f"Warnings: {len(graph.warnings)}")
```

- [ ] **Step 5: Run scan integration test**

Run:

```bash
pytest tests/test_cli.py::test_scan_generates_graph_json -v
```

Expected:

```text
1 passed
```

- [ ] **Step 6: Commit**

```bash
git add src/codelens/agents src/codelens/cli.py tests/test_cli.py
git commit -m "feat: scan project into graph json"
```

---

## Task 10: Graph Query

**Files:**
- Create: `src/codelens/graph/query.py`
- Create: `tests/test_impact.py`

- [ ] **Step 1: Write graph traversal tests**

Add `tests/test_impact.py`:

```python
from codelens.graph.models import Edge, Graph, Node
from codelens.graph.query import neighbors, reachable_nodes


def test_reachable_nodes_follows_dependency_edges():
    graph = Graph(
        root="/tmp/project",
        nodes=[
            Node(id="feature:login", type="Feature", name="登录"),
            Node(id="api:POST /api/login", type="API", name="POST /api/login"),
            Node(id="module:auth", type="Module", name="auth"),
        ],
        edges=[
            Edge(source="feature:login", target="api:POST /api/login", type="CALLS"),
            Edge(source="api:POST /api/login", target="module:auth", type="CALLS"),
        ],
    )

    assert neighbors(graph, "feature:login") == ["api:POST /api/login"]
    assert reachable_nodes(graph, ["feature:login"], max_depth=2) == [
        "api:POST /api/login",
        "module:auth",
    ]
```

- [ ] **Step 2: Run graph query tests and confirm failure**

Run:

```bash
pytest tests/test_impact.py::test_reachable_nodes_follows_dependency_edges -v
```

Expected:

```text
ModuleNotFoundError: No module named 'codelens.graph.query'
```

- [ ] **Step 3: Implement graph query**

Add `src/codelens/graph/query.py`:

```python
from collections import deque

from codelens.graph.models import Graph


def neighbors(graph: Graph, node_id: str) -> list[str]:
    return [edge.target for edge in graph.edges if edge.source == node_id]


def reachable_nodes(graph: Graph, start_ids: list[str], max_depth: int = 2) -> list[str]:
    seen = set(start_ids)
    output: list[str] = []
    queue = deque((node_id, 0) for node_id in start_ids)

    while queue:
        current, depth = queue.popleft()
        if depth >= max_depth:
            continue
        for target in neighbors(graph, current):
            if target in seen:
                continue
            seen.add(target)
            output.append(target)
            queue.append((target, depth + 1))

    return output
```

- [ ] **Step 4: Run graph query test**

Run:

```bash
pytest tests/test_impact.py::test_reachable_nodes_follows_dependency_edges -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: Commit**

```bash
git add src/codelens/graph/query.py tests/test_impact.py
git commit -m "feat: add graph traversal queries"
```

---

## Task 11: Impact, Risk, And Regression Analysis

**Files:**
- Create: `src/codelens/analysis/__init__.py`
- Create: `src/codelens/analysis/impact.py`
- Create: `src/codelens/analysis/risk.py`
- Create: `src/codelens/analysis/regression.py`
- Modify: `tests/test_impact.py`

- [ ] **Step 1: Add impact analysis test**

Append to `tests/test_impact.py`:

```python

from codelens.analysis.impact import analyze_impact


def test_analyze_impact_matches_requirement_keywords():
    graph = Graph(
        root="/tmp/project",
        nodes=[
            Node(id="feature:login", type="Feature", name="用户登录"),
            Node(id="api:POST /api/login", type="API", name="POST /api/login"),
            Node(id="module:auth", type="Module", name="auth", metadata={"bugHistory": 3}),
        ],
        edges=[
            Edge(source="feature:login", target="api:POST /api/login", type="CALLS"),
            Edge(source="api:POST /api/login", target="module:auth", type="CALLS"),
        ],
    )

    report = analyze_impact("修改用户登录验证码规则", graph)

    assert report["directImpact"] == ["feature:login"]
    assert "api:POST /api/login" in report["indirectImpact"]
    assert report["riskMap"]["module:auth"]["score"] > 0.5
    assert report["regressionList"][0]["priority"] == "P0"
```

- [ ] **Step 2: Run impact test and confirm failure**

Run:

```bash
pytest tests/test_impact.py::test_analyze_impact_matches_requirement_keywords -v
```

Expected:

```text
ModuleNotFoundError: No module named 'codelens.analysis'
```

- [ ] **Step 3: Implement analysis package**

Add `src/codelens/analysis/__init__.py`:

```python
from codelens.analysis.impact import analyze_impact

__all__ = ["analyze_impact"]
```

Add `src/codelens/analysis/risk.py`:

```python
from codelens.graph.models import Node


def score_node(node: Node, direct: bool) -> tuple[float, str]:
    complexity = float(node.metadata.get("complexity", 1))
    change_freq = float(node.metadata.get("changeFreq", 0))
    bug_history = float(node.metadata.get("bugHistory", 0))
    base = 0.45 if direct else 0.25
    score = min(1.0, base + complexity * 0.08 + change_freq * 0.04 + bug_history * 0.09)

    reasons = []
    if direct:
        reasons.append("需求关键词直接命中")
    if bug_history:
        reasons.append(f"历史 bug 次数 {int(bug_history)}")
    if complexity > 1:
        reasons.append(f"复杂度 {int(complexity)}")
    if not reasons:
        reasons.append("依赖链路影响")

    return round(score, 2), "，".join(reasons)
```

Add `src/codelens/analysis/regression.py`:

```python
from codelens.graph.models import Node


def build_regression_item(node: Node, direct: bool) -> dict[str, str]:
    priority = "P0" if direct else "P1"
    reason = "直接改动或需求命中" if direct else "依赖链路间接受影响"
    return {
        "feature": node.name,
        "priority": priority,
        "reason": reason,
    }
```

Add `src/codelens/analysis/impact.py`:

```python
from codelens.analysis.regression import build_regression_item
from codelens.analysis.risk import score_node
from codelens.graph.models import Graph, Node
from codelens.graph.query import reachable_nodes


def analyze_impact(requirement: str, graph: Graph) -> dict:
    node_by_id = {node.id: node for node in graph.nodes}
    direct_nodes = _match_direct_nodes(requirement, graph.nodes)
    direct_ids = [node.id for node in direct_nodes]
    indirect_ids = reachable_nodes(graph, direct_ids, max_depth=3)

    risk_map = {}
    for node_id in direct_ids + indirect_ids:
        node = node_by_id.get(node_id)
        if node is None:
            continue
        score, reason = score_node(node, direct=node_id in direct_ids)
        risk_map[node_id] = {"score": score, "reason": reason}

    regression_list = [
        build_regression_item(node_by_id[node_id], direct=node_id in direct_ids)
        for node_id in direct_ids + indirect_ids
        if node_id in node_by_id and node_by_id[node_id].type in {"Feature", "Page", "API", "Module"}
    ]

    return {
        "requirement": requirement,
        "directImpact": direct_ids,
        "indirectImpact": indirect_ids,
        "riskMap": risk_map,
        "regressionList": regression_list,
        "issues": [],
        "warnings": [],
    }


def _match_direct_nodes(requirement: str, nodes: list[Node]) -> list[Node]:
    normalized = requirement.lower()
    matches = []
    for node in nodes:
        tokens = {node.name.lower()}
        if node.path:
            tokens.add(node.path.lower())
        route = node.metadata.get("route")
        if route:
            tokens.add(str(route).lower())
        if any(_meaningful_overlap(normalized, token) for token in tokens):
            matches.append(node)
    return matches


def _meaningful_overlap(requirement: str, token: str) -> bool:
    if not token:
        return False
    if token in requirement:
        return True
    for char in token:
        if "\u4e00" <= char <= "\u9fff" and char in requirement:
            return True
    return False
```

- [ ] **Step 4: Run impact tests**

Run:

```bash
pytest tests/test_impact.py -v
```

Expected:

```text
2 passed
```

- [ ] **Step 5: Commit**

```bash
git add src/codelens/analysis tests/test_impact.py
git commit -m "feat: analyze requirement impact"
```

---

## Task 12: Requirement Review Rules

**Files:**
- Create: `src/codelens/agents/review_agent.py`
- Modify: `src/codelens/analysis/impact.py`
- Modify: `tests/test_impact.py`

- [ ] **Step 1: Add requirement review test**

Append to `tests/test_impact.py`:

```python

def test_analyze_impact_flags_batch_upload_missing_limits():
    graph = Graph(root="/tmp/project")

    report = analyze_impact("新增用户批量导入功能，支持 Excel 上传", graph)

    assert report["issues"][0]["type"] == "边界缺失"
    assert "文件大小" in report["issues"][0]["suggestion"]
```

- [ ] **Step 2: Run review test and confirm failure**

Run:

```bash
pytest tests/test_impact.py::test_analyze_impact_flags_batch_upload_missing_limits -v
```

Expected:

```text
IndexError: list index out of range
```

- [ ] **Step 3: Implement review rules**

Add `src/codelens/agents/review_agent.py`:

```python
def review_requirement(requirement: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    text = requirement.lower()

    if ("批量" in requirement or "导入" in requirement or "upload" in text) and not _mentions_limits(requirement):
        issues.append(
            {
                "type": "边界缺失",
                "description": "批量导入或上传需求未说明单次上限、文件大小、失败处理策略",
                "severity": "medium",
                "suggestion": "补充文件大小、行数上限、格式校验、失败回滚和部分成功处理规则",
            }
        )

    if "未登录" in requirement and "下单" in requirement:
        issues.append(
            {
                "type": "逻辑矛盾",
                "description": "需求允许未登录下单，可能与现有登录态校验冲突",
                "severity": "high",
                "suggestion": "明确是否修改下单登录校验、游客身份和支付后绑定规则",
            }
        )

    return issues


def _mentions_limits(requirement: str) -> bool:
    keywords = ["上限", "大小", "限制", "行数", "mb", "MB", "回滚", "失败"]
    return any(keyword in requirement for keyword in keywords)
```

- [ ] **Step 4: Wire review into impact analysis**

Modify `src/codelens/analysis/impact.py`:

```python
from codelens.agents.review_agent import review_requirement
from codelens.analysis.regression import build_regression_item
from codelens.analysis.risk import score_node
from codelens.graph.models import Graph, Node
from codelens.graph.query import reachable_nodes
```

Then change the return block in `analyze_impact`:

```python
    return {
        "requirement": requirement,
        "directImpact": direct_ids,
        "indirectImpact": indirect_ids,
        "riskMap": risk_map,
        "regressionList": regression_list,
        "issues": review_requirement(requirement),
        "warnings": [],
    }
```

- [ ] **Step 5: Run impact tests**

Run:

```bash
pytest tests/test_impact.py -v
```

Expected:

```text
3 passed
```

- [ ] **Step 6: Commit**

```bash
git add src/codelens/agents/review_agent.py src/codelens/analysis/impact.py tests/test_impact.py
git commit -m "feat: add requirement review rules"
```

---

## Task 13: Analyze CLI

**Files:**
- Modify: `src/codelens/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Add analyze integration test**

Append to `tests/test_cli.py`:

```python

def test_analyze_generates_report_json(tmp_path: Path):
    app_file = tmp_path / "app.py"
    app_file.write_text(
        """
from fastapi import APIRouter
router = APIRouter()
@router.post("/api/login")
def login():
    return {"ok": True}
""".strip(),
        encoding="utf-8",
    )

    runner = CliRunner()
    scan_result = runner.invoke(app, ["scan", str(tmp_path)])
    analyze_result = runner.invoke(app, ["analyze", "修改用户登录验证码规则", "--project", str(tmp_path)])

    assert scan_result.exit_code == 0
    assert analyze_result.exit_code == 0
    assert (tmp_path / ".codelens" / "report.json").exists()
    assert "directImpact" in (tmp_path / ".codelens" / "report.json").read_text(encoding="utf-8")
```

- [ ] **Step 2: Run analyze integration test and confirm failure**

Run:

```bash
pytest tests/test_cli.py::test_analyze_generates_report_json -v
```

Expected:

```text
FAILED
```

because `analyze` still exits with code `1`.

- [ ] **Step 3: Wire analyze CLI**

Replace `analyze` in `src/codelens/cli.py`:

```python
@app.command()
def analyze(requirement: str, project: Path = Path(".")) -> None:
    import json

    from codelens.analysis.impact import analyze_impact
    from codelens.config import graph_path, report_path
    from codelens.graph.store import load_graph

    graph_file = graph_path(project)
    if not graph_file.exists():
        typer.echo(f"Graph not found: {graph_file}. Run `codelens scan {project}` first.")
        raise typer.Exit(code=2)

    try:
        graph = load_graph(graph_file)
    except Exception as exc:
        typer.echo(f"Graph file is damaged: {graph_file}. Run `codelens scan {project}` again.")
        typer.echo(str(exc))
        raise typer.Exit(code=2) from exc

    report = analyze_impact(requirement, graph)
    output = report_path(project)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    typer.echo(f"Report written: {output}")
    typer.echo(f"Direct impact: {len(report['directImpact'])}")
    typer.echo(f"Indirect impact: {len(report['indirectImpact'])}")
    typer.echo(f"Issues: {len(report['issues'])}")
```

- [ ] **Step 4: Run analyze integration test**

Run:

```bash
pytest tests/test_cli.py::test_analyze_generates_report_json -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: Run all Python tests**

Run:

```bash
pytest -v
```

Expected:

```text
all tests passed
```

- [ ] **Step 6: Commit**

```bash
git add src/codelens/cli.py tests/test_cli.py
git commit -m "feat: generate impact report from cli"
```

---

## Task 14: FastAPI Service

**Files:**
- Create: `src/codelens/api/__init__.py`
- Create: `src/codelens/api/server.py`
- Modify: `src/codelens/cli.py`
- Create: `tests/test_api.py`

- [ ] **Step 1: Write API tests**

Add `tests/test_api.py`:

```python
from pathlib import Path

from fastapi.testclient import TestClient

from codelens.api.server import create_app
from codelens.graph.models import Graph, Node
from codelens.graph.store import save_graph


def test_api_returns_graph(tmp_path: Path):
    graph = Graph(
        root=str(tmp_path),
        nodes=[Node(id="feature:login", type="Feature", name="用户登录")],
    )
    save_graph(graph, tmp_path / ".codelens" / "graph.json")

    client = TestClient(create_app(tmp_path))
    response = client.get("/api/graph")

    assert response.status_code == 200
    assert response.json()["nodes"][0]["name"] == "用户登录"


def test_api_returns_404_when_report_missing(tmp_path: Path):
    client = TestClient(create_app(tmp_path))
    response = client.get("/api/report")

    assert response.status_code == 404
```

- [ ] **Step 2: Run API tests and confirm failure**

Run:

```bash
pytest tests/test_api.py -v
```

Expected:

```text
ModuleNotFoundError: No module named 'codelens.api'
```

- [ ] **Step 3: Implement FastAPI app**

Add `src/codelens/api/__init__.py`:

```python
from codelens.api.server import create_app

__all__ = ["create_app"]
```

Add `src/codelens/api/server.py`:

```python
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from codelens.config import graph_path, report_path
from codelens.graph.store import load_graph


def create_app(project: Path) -> FastAPI:
    app = FastAPI(title="CodeLens API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/graph")
    def graph() -> dict:
        path = graph_path(project)
        if not path.exists():
            raise HTTPException(status_code=404, detail="graph not found")
        return load_graph(path).model_dump()

    @app.get("/api/report")
    def report() -> dict:
        path = report_path(project)
        if not path.exists():
            raise HTTPException(status_code=404, detail="report not found")
        return json.loads(path.read_text(encoding="utf-8"))

    return app
```

- [ ] **Step 4: Wire serve CLI**

Replace `serve` in `src/codelens/cli.py`:

```python
@app.command()
def serve(project: Path = Path("."), host: str = "127.0.0.1", port: int = 8000) -> None:
    import uvicorn

    from codelens.api.server import create_app

    api = create_app(project.resolve())
    typer.echo(f"Serving CodeLens API at http://{host}:{port}")
    uvicorn.run(api, host=host, port=port)
```

- [ ] **Step 5: Run API tests**

Run:

```bash
pytest tests/test_api.py -v
```

Expected:

```text
2 passed
```

- [ ] **Step 6: Commit**

```bash
git add src/codelens/api src/codelens/cli.py tests/test_api.py
git commit -m "feat: serve graph and report api"
```

---

## Task 15: Example Demo Project

**Files:**
- Create: `../demo-project/backend/app/main.py`
- Create: `../demo-project/backend/app/auth.py`
- Create: `../demo-project/backend/app/orders.py`
- Create: `../demo-project/backend/requirements.txt`
- Create: `../demo-project/frontend/package.json`
- Create: `../demo-project/frontend/src/app/login/page.tsx`
- Create: `../demo-project/frontend/src/app/orders/page.tsx`
- Create: `../demo-project/frontend/src/components/LoginForm.tsx`
- Create: `../demo-project/frontend/src/lib/api.ts`

- [ ] **Step 1: Add backend demo files**

Add `../demo-project/backend/app/main.py`:

```python
from fastapi import FastAPI

from app.auth import router as auth_router
from app.orders import router as orders_router

app = FastAPI()
app.include_router(auth_router)
app.include_router(orders_router)
```

Add `../demo-project/backend/app/auth.py`:

```python
from fastapi import APIRouter

router = APIRouter()


@router.post("/api/login")
def login():
    return {"token": "demo"}


def check_permission():
    return True
```

Add `../demo-project/backend/app/orders.py`:

```python
from fastapi import APIRouter

router = APIRouter()


@router.post("/api/orders/checkout")
def checkout():
    return {"orderId": "demo-order"}
```

Add `../demo-project/backend/requirements.txt`:

```text
fastapi
uvicorn
```

- [ ] **Step 2: Add frontend demo files**

Add `../demo-project/frontend/package.json`:

```json
{
  "name": "codelens-demo-frontend",
  "private": true,
  "scripts": {
    "dev": "next dev"
  },
  "dependencies": {
    "next": "^14.2.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  }
}
```

Add `../demo-project/frontend/src/lib/api.ts`:

```typescript
export async function login() {
  return fetch("/api/login", { method: "POST" });
}

export async function checkout() {
  return fetch("/api/orders/checkout", { method: "POST" });
}
```

Add `../demo-project/frontend/src/components/LoginForm.tsx`:

```typescript
import { login } from "../lib/api";

export function LoginForm() {
  return <button onClick={login}>登录</button>;
}
```

Add `../demo-project/frontend/src/app/login/page.tsx`:

```typescript
import { LoginForm } from "../../components/LoginForm";

export default function LoginPage() {
  return <LoginForm />;
}
```

Add `../demo-project/frontend/src/app/orders/page.tsx`:

```typescript
import { checkout } from "../../lib/api";

export default function OrdersPage() {
  return <button onClick={checkout}>结算</button>;
}
```

- [ ] **Step 3: Run demo scan**

Run:

```bash
codelens scan ../demo-project
```

Expected:

```text
Graph written: ../demo-project/.codelens/graph.json
```

- [ ] **Step 4: Run demo analyze**

Run:

```bash
codelens analyze "修改用户登录验证码规则" --project ../demo-project
```

Expected:

```text
Report written: ../demo-project/.codelens/report.json
```

- [ ] **Step 5: Commit**

```bash
git add ../demo-project
git commit -m "test: add demo project fixture"
```

---

## Task 16: Web App Bootstrap

**Files:**
- Create: `web/package.json`
- Create: `web/next.config.js`
- Create: `web/tsconfig.json`
- Create: `web/src/lib/api.ts`
- Create: `web/src/app/page.tsx`
- Create: `web/src/app/impact/page.tsx`

- [ ] **Step 1: Create Web package metadata**

Add `web/package.json`:

```json
{
  "name": "codelens-web",
  "private": true,
  "scripts": {
    "dev": "next dev -p 3000",
    "build": "next build",
    "start": "next start -p 3000",
    "lint": "next lint"
  },
  "dependencies": {
    "@antv/g2": "^5.2.0",
    "@antv/g6": "^5.0.0",
    "@antv/s2": "^2.0.0",
    "lucide-react": "^0.468.0",
    "next": "^14.2.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/node": "^20.11.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "typescript": "^5.4.0"
  }
}
```

Add `web/next.config.js`:

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone"
};

module.exports = nextConfig;
```

Add `web/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": false,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve"
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
  "exclude": ["node_modules"]
}
```

- [ ] **Step 2: Add API client**

Add `web/src/lib/api.ts`:

```typescript
const API_BASE = process.env.NEXT_PUBLIC_CODELENS_API ?? "http://127.0.0.1:8000";

export async function getGraph() {
  const response = await fetch(`${API_BASE}/api/graph`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load graph: ${response.status}`);
  }
  return response.json();
}

export async function getReport() {
  const response = await fetch(`${API_BASE}/api/report`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load report: ${response.status}`);
  }
  return response.json();
}
```

- [ ] **Step 3: Add initial pages**

Add `web/src/app/page.tsx`:

```typescript
import Link from "next/link";

export default function HomePage() {
  return (
    <main>
      <nav>
        <Link href="/">全景图</Link>
        <Link href="/impact">影响分析</Link>
      </nav>
      <section>
        <h1>CodeLens</h1>
        <p>项目功能图谱</p>
      </section>
    </main>
  );
}
```

Add `web/src/app/impact/page.tsx`:

```typescript
import Link from "next/link";

export default function ImpactPage() {
  return (
    <main>
      <nav>
        <Link href="/">全景图</Link>
        <Link href="/impact">影响分析</Link>
      </nav>
      <section>
        <h1>影响分析</h1>
        <p>风险热力图、回归矩阵和需求问题标注</p>
      </section>
    </main>
  );
}
```

- [ ] **Step 4: Install and build Web app**

Run:

```bash
cd web
npm install
npm run build
```

Expected:

```text
Compiled successfully
```

- [ ] **Step 5: Commit**

```bash
git add web
git commit -m "feat: bootstrap codelens web app"
```

---

## Task 17: Web Visualization Components

**Files:**
- Create: `web/src/components/GraphView.tsx`
- Create: `web/src/components/HeatMap.tsx`
- Create: `web/src/components/TestMatrix.tsx`
- Create: `web/src/components/IssueAnnotation.tsx`
- Modify: `web/src/app/page.tsx`
- Modify: `web/src/app/impact/page.tsx`

- [ ] **Step 1: Add GraphView component**

Add `web/src/components/GraphView.tsx`:

```typescript
"use client";

type GraphNode = {
  id: string;
  type: string;
  name: string;
};

type GraphEdge = {
  source: string;
  target: string;
  type: string;
};

export function GraphView({ nodes, edges }: { nodes: GraphNode[]; edges: GraphEdge[] }) {
  return (
    <section aria-label="功能全景图">
      <header>
        <h2>功能全景图</h2>
        <span>{nodes.length} 节点 / {edges.length} 关系</span>
      </header>
      <div>
        {nodes.map((node) => (
          <article key={node.id}>
            <strong>{node.name}</strong>
            <small>{node.type}</small>
          </article>
        ))}
      </div>
    </section>
  );
}
```

- [ ] **Step 2: Add report components**

Add `web/src/components/HeatMap.tsx`:

```typescript
type RiskEntry = {
  score: number;
  reason: string;
};

export function HeatMap({ riskMap }: { riskMap: Record<string, RiskEntry> }) {
  const entries = Object.entries(riskMap);
  return (
    <section aria-label="风险热力图">
      <h2>风险热力图</h2>
      <div>
        {entries.map(([id, risk]) => (
          <article key={id}>
            <strong>{id}</strong>
            <span>{risk.score}</span>
            <p>{risk.reason}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
```

Add `web/src/components/TestMatrix.tsx`:

```typescript
type RegressionItem = {
  feature: string;
  priority: string;
  reason: string;
};

export function TestMatrix({ items }: { items: RegressionItem[] }) {
  return (
    <section aria-label="回归测试矩阵">
      <h2>回归测试矩阵</h2>
      <table>
        <thead>
          <tr>
            <th>功能</th>
            <th>优先级</th>
            <th>原因</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={`${item.feature}-${item.priority}`}>
              <td>{item.feature}</td>
              <td>{item.priority}</td>
              <td>{item.reason}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
```

Add `web/src/components/IssueAnnotation.tsx`:

```typescript
type Issue = {
  type: string;
  description: string;
  severity: string;
  suggestion: string;
};

export function IssueAnnotation({ issues }: { issues: Issue[] }) {
  return (
    <section aria-label="需求逻辑漏洞">
      <h2>需求逻辑漏洞</h2>
      {issues.map((issue) => (
        <article key={`${issue.type}-${issue.description}`}>
          <strong>{issue.type}</strong>
          <span>{issue.severity}</span>
          <p>{issue.description}</p>
          <p>{issue.suggestion}</p>
        </article>
      ))}
    </section>
  );
}
```

- [ ] **Step 3: Wire pages to API**

Replace `web/src/app/page.tsx`:

```typescript
import Link from "next/link";

import { GraphView } from "../components/GraphView";
import { getGraph } from "../lib/api";

export default async function HomePage() {
  const graph = await getGraph();

  return (
    <main>
      <nav>
        <Link href="/">全景图</Link>
        <Link href="/impact">影响分析</Link>
      </nav>
      <GraphView nodes={graph.nodes} edges={graph.edges} />
    </main>
  );
}
```

Replace `web/src/app/impact/page.tsx`:

```typescript
import Link from "next/link";

import { HeatMap } from "../../components/HeatMap";
import { IssueAnnotation } from "../../components/IssueAnnotation";
import { TestMatrix } from "../../components/TestMatrix";
import { getReport } from "../../lib/api";

export default async function ImpactPage() {
  const report = await getReport();

  return (
    <main>
      <nav>
        <Link href="/">全景图</Link>
        <Link href="/impact">影响分析</Link>
      </nav>
      <HeatMap riskMap={report.riskMap} />
      <TestMatrix items={report.regressionList} />
      <IssueAnnotation issues={report.issues} />
    </main>
  );
}
```

- [ ] **Step 4: Build Web app**

Run:

```bash
cd web
npm run build
```

Expected:

```text
Compiled successfully
```

- [ ] **Step 5: Commit**

```bash
git add web/src
git commit -m "feat: render codelens graph and report"
```

---

## Task 18: Docker And Deployment

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.env.example`
- Modify: `README.md`

- [ ] **Step 1: Add environment template**

Add `.env.example`:

```text
CODELENS_PROJECT=../demo-project
CODELENS_API_PORT=8000
NEXT_PUBLIC_CODELENS_API=http://127.0.0.1:8000
```

- [ ] **Step 2: Add Dockerfile**

Add `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY examples ./examples

RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["codelens", "serve", "--project", "../demo-project", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 3: Add docker-compose**

Add `docker-compose.yml`:

```yaml
services:
  api:
    build: .
    command: >
      sh -c "codelens scan ${CODELENS_PROJECT:-../demo-project}
      && codelens analyze '修改用户登录验证码规则' --project ${CODELENS_PROJECT:-../demo-project}
      && codelens serve --project ${CODELENS_PROJECT:-../demo-project} --host 0.0.0.0 --port 8000"
    ports:
      - "${CODELENS_API_PORT:-8000}:8000"
```

- [ ] **Step 4: Add README**

Add `README.md`:

```markdown
# CodeLens

CodeLens scans a repository, builds a feature/dependency graph, analyzes requirement impact, and serves a visual report.

## Local Demo

```bash
python -m pip install -e ".[dev]"
codelens scan ../demo-project
codelens analyze "修改用户登录验证码规则" --project ../demo-project
codelens serve --project ../demo-project
```

Open:

```text
http://127.0.0.1:8000/api/graph
http://127.0.0.1:8000/api/report
```

## Docker Demo

```bash
docker compose up --build
```

## Deliverables

- CLI commands: `scan`, `analyze`, `serve`
- Python core engine
- Graph JSON: `.codelens/graph.json`
- Report JSON: `.codelens/report.json`
- FastAPI service
- Demo project
- Docker setup
```

- [ ] **Step 5: Build Docker image**

Run:

```bash
docker compose build
```

Expected:

```text
api  Built
```

- [ ] **Step 6: Commit**

```bash
git add Dockerfile docker-compose.yml .env.example README.md
git commit -m "chore: add docker deployment"
```

---

## Task 19: Test Report And Acceptance Checklist

**Files:**
- Create: `TEST_REPORT.md`

- [ ] **Step 1: Run full test suite**

Run:

```bash
pytest -v
```

Expected:

```text
all tests passed
```

- [ ] **Step 2: Run demo commands**

Run:

```bash
codelens scan ../demo-project
codelens analyze "新增用户批量导入功能，支持 Excel 上传" --project ../demo-project
```

Expected:

```text
Graph written: ../demo-project/.codelens/graph.json
Report written: ../demo-project/.codelens/report.json
```

- [ ] **Step 3: Add test report**

Add `TEST_REPORT.md`:

```markdown
# CodeLens MVP Test Report

## Environment

- Python: 3.11+
- OS: macOS/Linux
- Project: `../demo-project`

## Automated Tests

Command:

```bash
pytest -v
```

Expected result:

```text
all tests passed
```

## Manual Demo

Commands:

```bash
codelens scan ../demo-project
codelens analyze "新增用户批量导入功能，支持 Excel 上传" --project ../demo-project
codelens serve --project ../demo-project
```

Expected artifacts:

```text
../demo-project/.codelens/graph.json
../demo-project/.codelens/report.json
```

## Acceptance Checklist

- [ ] CLI can scan Python, Java, TS/JS, TSX/JSX, and Markdown files.
- [ ] Frontend parser extracts pages, components, API calls, and interaction entry points.
- [ ] Backend parser extracts FastAPI and Spring-style API endpoints.
- [ ] Local file parse failures are recorded as non-blocking warnings.
- [ ] Missing graph blocks `analyze` with a clear message.
- [ ] Damaged graph blocks `analyze` and asks user to rerun `scan`.
- [ ] Requirement impact report includes direct impact, indirect impact, risk map, regression list, and issues.
- [ ] Batch upload requirement flags missing size/row/failure limits.
- [ ] API exposes `/api/graph` and `/api/report`.
- [ ] Docker demo can start the API service.
```

- [ ] **Step 4: Commit**

```bash
git add TEST_REPORT.md
git commit -m "docs: add mvp test report"
```

---

## Delivery Priority

P0:

- Task 1 to Task 14.
- Produces working CLI, Python core, graph JSON, report JSON, and FastAPI API.

P1:

- Task 15 to Task 17.
- Produces demo project and first Web visualization.

P2:

- Task 18 to Task 19.
- Produces Docker deployment and test report.

---

## Implementation Notes

- Start with deterministic rule-based logic. Add LLM integration only after the graph and report pipeline is stable.
- Keep parser failures non-blocking unless the graph itself is missing or damaged.
- Use `warnings` arrays in graph/report outputs to make incomplete analysis visible.
- Use the demo project as the first acceptance fixture.
- For frontend parsing, the MVP regex parser is acceptable for demo coverage. Replace it with Tree-sitter later when parser precision becomes the bottleneck.
- For graph rendering, the first Web version can render structured lists. Upgrade to AntV G6/G2/S2 after API data contracts are stable.

---

## Self-Review

Spec coverage:

- Product goal: covered by target user flow and P0 tasks.
- Multi-language support: covered by Python, Java, Markdown, and frontend parsers.
- Frontend framework support: covered by Next.js page/component/API/interaction extraction.
- Graph construction: covered by graph schema, store, scan orchestration, and query tasks.
- Requirement impact analysis: covered by impact, risk, regression, and review tasks.
- Exception handling: covered by parser warnings and analyze graph validation.
- Deliverables and deployment: covered by demo project, API, Web app, Docker, README, and test report.

Placeholder scan:

- No `TBD`, `TODO`, or undefined future placeholders are required to execute the MVP.

Type consistency:

- `Node`, `Edge`, `Graph`, and `WarningItem` are defined before use.
- CLI command names match the target user flow.
- Graph/report JSON contracts match API and Web component expectations.
