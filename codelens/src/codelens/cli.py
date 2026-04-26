from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from codelens import __version__
from codelens.agents.code_agent import scan_project
from codelens.analysis.impact import analyze_impact
from codelens.config import graph_path, report_html_path, report_path
from codelens.graph.store import load_graph, load_report, save_graph, save_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codelens")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("version")

    scan = subparsers.add_parser("scan")
    scan.add_argument("project", type=Path)

    analyze = subparsers.add_parser("analyze")
    analyze.add_argument("requirement", nargs="?")
    analyze.add_argument("--prd", type=Path)
    analyze.add_argument("--project", type=Path, default=Path("."))

    serve = subparsers.add_parser("serve")
    serve.add_argument("--project", type=Path, default=Path("."))
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)

    export = subparsers.add_parser("export")
    export.add_argument("--project", type=Path, default=Path("."))
    export.add_argument("--output", type=Path)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "version":
        print("codelens %s" % __version__)
        return 0

    if args.command == "scan":
        return _scan(args.project)

    if args.command == "analyze":
        requirement = _load_requirement(args.requirement, args.prd)
        if not requirement:
            print("Requirement text is required. Pass text or --prd file.", file=sys.stderr)
            return 2
        return _analyze(requirement, args.project)

    if args.command == "serve":
        from codelens.api.server import run_server

        run_server(args.project, args.host, args.port)
        return 0

    if args.command == "export":
        return _export(args.project, args.output)

    parser.print_help()
    return 2


def entrypoint() -> None:
    raise SystemExit(main())


def _scan(project: Path) -> int:
    if not project.exists():
        print("Project path does not exist: %s" % project, file=sys.stderr)
        return 2
    graph = scan_project(project)
    output = graph_path(project)
    save_graph(graph, output)
    feature_count = len([node for node in graph.nodes if node.type in {"Page", "Component", "API", "Feature"}])
    code_count = len(graph.nodes) - feature_count
    print("Graph written: %s" % output)
    print("Functional nodes: %d" % feature_count)
    print("Code nodes: %d" % code_count)
    print("Edges: %d" % len(graph.edges))
    if graph.warnings:
        print("Warnings: %d" % len(graph.warnings))
    return 0


def _analyze(requirement: str, project: Path) -> int:
    graph_file = graph_path(project)
    if not graph_file.exists():
        print("Graph not found: %s. Run `codelens scan %s` first." % (graph_file, project), file=sys.stderr)
        return 2

    try:
        graph = load_graph(graph_file)
    except Exception as exc:
        print("Graph file is damaged: %s. Run `codelens scan %s` again." % (graph_file, project), file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 2

    report = analyze_impact(requirement, graph)
    output = report_path(project)
    save_report(report, output)
    print("Report written: %s" % output)
    print("Matched features: %d" % len(report["matchedFeatures"]))
    print("Related features: %d" % len(report["relatedFeatures"]))
    print("Logic issues: %d" % len(report["logicIssues"]))
    return 0


def _export(project: Path, output: Optional[Path]) -> int:
    from codelens.reporting.html import render_static_report

    graph_file = graph_path(project)
    report_file = report_path(project)
    if not graph_file.exists():
        print("Graph not found: %s. Run `codelens scan %s` first." % (graph_file, project), file=sys.stderr)
        return 2
    if not report_file.exists():
        print("Report not found: %s. Run `codelens analyze ... --project %s` first." % (report_file, project), file=sys.stderr)
        return 2

    try:
        graph = load_graph(graph_file)
        report = load_report(report_file)
    except Exception as exc:
        print("Graph or report file is damaged. Rerun `scan` and `analyze`.", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 2

    destination = output or report_html_path(project)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render_static_report(graph, report), encoding="utf-8")
    print("Static report written: %s" % destination)
    return 0


def _load_requirement(requirement: Optional[str], prd: Optional[Path]) -> Optional[str]:
    if prd is not None:
        return prd.read_text(encoding="utf-8").strip()
    if requirement is not None:
        return requirement.strip()
    return None


if __name__ == "__main__":
    entrypoint()
