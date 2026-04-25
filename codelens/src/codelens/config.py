from pathlib import Path

CODELENS_DIR = ".codelens"
GRAPH_FILE = "graph.json"
REPORT_FILE = "report.json"
REPORT_HTML_FILE = "report.html"


def codelens_dir(root: Path) -> Path:
    return root / CODELENS_DIR


def graph_path(root: Path) -> Path:
    return codelens_dir(root) / GRAPH_FILE


def report_path(root: Path) -> Path:
    return codelens_dir(root) / REPORT_FILE


def report_html_path(root: Path) -> Path:
    return codelens_dir(root) / REPORT_HTML_FILE
