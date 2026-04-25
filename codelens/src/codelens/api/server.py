from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Type
from urllib.parse import urlparse

from codelens.config import graph_path, report_path
from codelens.graph.store import load_graph, load_report


def run_server(project: Path, host: str, port: int) -> None:
    handler = create_handler(project.resolve())
    server = ThreadingHTTPServer((host, port), handler)
    print("Serving CodeLens at http://%s:%d" % (host, port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped")
    finally:
        server.server_close()


def create_handler(project: Path) -> Type[BaseHTTPRequestHandler]:
    class CodeLensHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path == "/api/health":
                self._send_json({"status": "ok"})
                return
            if path == "/api/graph":
                self._send_graph(project)
                return
            if path == "/api/report":
                self._send_report(project)
                return
            if path in {"/", "/impact"}:
                self._send_html(_dashboard_html())
                return
            self._send_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)

        def log_message(self, format: str, *args) -> None:
            return

        def _send_graph(self, project_root: Path) -> None:
            path = graph_path(project_root)
            if not path.exists():
                self._send_json({"error": "graph not found"}, status=HTTPStatus.NOT_FOUND)
                return
            try:
                self._send_json(load_graph(path).to_dict())
            except Exception as exc:
                self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

        def _send_report(self, project_root: Path) -> None:
            path = report_path(project_root)
            if not path.exists():
                self._send_json({"error": "report not found"}, status=HTTPStatus.NOT_FOUND)
                return
            try:
                self._send_json(load_report(path))
            except Exception as exc:
                self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

        def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(status.value)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_html(self, html: str) -> None:
            body = html.encode("utf-8")
            self.send_response(HTTPStatus.OK.value)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return CodeLensHandler


def _dashboard_html() -> str:
    return """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>CodeLens</title>
  <style>
    :root {
      --paper: #f7f4ed;
      --ink: #202323;
      --muted: #6d706b;
      --line: #d8d2c3;
      --teal: #0f766e;
      --blue: #2454a6;
      --amber: #b7791f;
      --red: #b42318;
      --panel: #fffdf7;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--paper);
      color: var(--ink);
      font-family: "Avenir Next", "Trebuchet MS", "Helvetica Neue", sans-serif;
    }
    main { min-height: 100vh; }
    .topbar {
      align-items: center;
      border-bottom: 1px solid var(--line);
      display: flex;
      gap: 24px;
      justify-content: space-between;
      padding: 18px 28px;
    }
    .brand { font-family: Georgia, serif; font-size: 26px; font-weight: 700; }
    .tabs { display: flex; gap: 8px; }
    .tabs button {
      background: transparent;
      border: 1px solid var(--line);
      border-radius: 8px;
      color: var(--ink);
      cursor: pointer;
      font: inherit;
      padding: 8px 12px;
    }
    .tabs button.active { background: var(--ink); color: var(--paper); }
    .layout {
      display: grid;
      gap: 22px;
      grid-template-columns: minmax(0, 1.3fr) minmax(320px, 0.7fr);
      padding: 24px 28px 36px;
    }
    section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 10px 24px rgba(32, 35, 35, 0.06);
      padding: 18px;
    }
    h1, h2 { margin: 0; }
    h1 { font-size: 20px; }
    h2 { font-size: 15px; margin-bottom: 14px; }
    .metrics {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      margin-bottom: 22px;
    }
    .metric {
      border-left: 4px solid var(--teal);
      padding: 4px 0 4px 12px;
    }
    .metric strong { display: block; font-size: 24px; }
    .metric span { color: var(--muted); font-size: 13px; }
    .node-grid {
      display: grid;
      gap: 10px;
      grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
      max-height: 430px;
      overflow: auto;
    }
    .node, .risk, .issue {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
    }
    .node small, .risk small, .issue small { color: var(--muted); display: block; margin-top: 6px; }
    .type-API { border-left: 4px solid var(--blue); }
    .type-Page { border-left: 4px solid var(--teal); }
    .type-Feature { border-left: 4px solid var(--amber); }
    .type-Module { border-left: 4px solid #4b5563; }
    .stack { display: grid; gap: 22px; }
    table {
      border-collapse: collapse;
      width: 100%;
    }
    th, td {
      border-bottom: 1px solid var(--line);
      padding: 10px 8px;
      text-align: left;
      vertical-align: top;
    }
    th { color: var(--muted); font-size: 12px; }
    .badge {
      border-radius: 999px;
      display: inline-block;
      font-size: 12px;
      padding: 3px 8px;
    }
    .p0 { background: #fee4e2; color: var(--red); }
    .p1 { background: #fef0c7; color: var(--amber); }
    .empty { color: var(--muted); padding: 24px 0; }
    @media (max-width: 900px) {
      .layout { grid-template-columns: 1fr; padding: 18px; }
      .metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .topbar { align-items: flex-start; flex-direction: column; }
    }
  </style>
</head>
<body>
  <main>
    <header class="topbar">
      <div>
        <div class="brand">CodeLens</div>
        <h1>项目功能图谱与需求影响分析</h1>
      </div>
      <nav class="tabs">
        <button class="active" data-tab="graph">全景图</button>
        <button data-tab="impact">影响分析</button>
      </nav>
    </header>
    <div class="layout">
      <div>
        <div class="metrics" id="metrics"></div>
        <section id="graph-panel">
          <h2>功能节点</h2>
          <div class="node-grid" id="nodes"></div>
        </section>
        <section id="impact-panel" hidden>
          <h2>回归测试矩阵</h2>
          <div id="matrix"></div>
        </section>
      </div>
      <aside class="stack">
        <section>
          <h2>风险热力</h2>
          <div id="risks"></div>
        </section>
        <section>
          <h2>需求审查</h2>
          <div id="issues"></div>
        </section>
      </aside>
    </div>
  </main>
  <script>
    const state = { graph: null, report: null };
    async function loadJson(path) {
      const response = await fetch(path);
      if (!response.ok) return null;
      return response.json();
    }
    function nodeClass(type) {
      return "node type-" + String(type || "").replace(/[^a-zA-Z0-9_-]/g, "");
    }
    function renderMetrics() {
      const graph = state.graph || { nodes: [], edges: [], warnings: [] };
      const report = state.report || { directImpact: [], indirectImpact: [], issues: [] };
      const metrics = [
        ["节点", graph.nodes.length],
        ["关系", graph.edges.length],
        ["影响", report.directImpact.length + report.indirectImpact.length],
        ["告警", (graph.warnings || []).length + (report.issues || []).length],
      ];
      document.getElementById("metrics").innerHTML = metrics.map(([label, value]) =>
        `<div class="metric"><strong>${value}</strong><span>${label}</span></div>`
      ).join("");
    }
    function renderGraph() {
      const graph = state.graph;
      const box = document.getElementById("nodes");
      if (!graph) {
        box.innerHTML = `<div class="empty">未生成 graph.json</div>`;
        return;
      }
      box.innerHTML = graph.nodes.map(node =>
        `<article class="${nodeClass(node.type)}"><strong>${node.name}</strong><small>${node.type} · ${node.path || node.id}</small></article>`
      ).join("");
    }
    function renderRisks() {
      const report = state.report;
      const box = document.getElementById("risks");
      if (!report || !Object.keys(report.riskMap || {}).length) {
        box.innerHTML = `<div class="empty">暂无风险评分</div>`;
        return;
      }
      box.innerHTML = Object.entries(report.riskMap).map(([id, risk]) =>
        `<article class="risk"><strong>${risk.score} · ${id}</strong><small>${risk.reason}</small></article>`
      ).join("");
    }
    function renderMatrix() {
      const report = state.report;
      const box = document.getElementById("matrix");
      if (!report || !(report.regressionList || []).length) {
        box.innerHTML = `<div class="empty">暂无回归清单</div>`;
        return;
      }
      box.innerHTML = `<table><thead><tr><th>功能</th><th>优先级</th><th>原因</th></tr></thead><tbody>` +
        report.regressionList.map(item => `<tr><td>${item.feature}</td><td><span class="badge ${item.priority.toLowerCase()}">${item.priority}</span></td><td>${item.reason}</td></tr>`).join("") +
        `</tbody></table>`;
    }
    function renderIssues() {
      const report = state.report;
      const box = document.getElementById("issues");
      if (!report || !(report.issues || []).length) {
        box.innerHTML = `<div class="empty">未发现需求问题</div>`;
        return;
      }
      box.innerHTML = report.issues.map(issue =>
        `<article class="issue"><strong>${issue.type}</strong><small>${issue.severity}</small><p>${issue.description}</p><small>${issue.suggestion}</small></article>`
      ).join("");
    }
    function render() {
      renderMetrics();
      renderGraph();
      renderRisks();
      renderMatrix();
      renderIssues();
    }
    document.querySelectorAll(".tabs button").forEach(button => {
      button.addEventListener("click", () => {
        document.querySelectorAll(".tabs button").forEach(item => item.classList.remove("active"));
        button.classList.add("active");
        const impact = button.dataset.tab === "impact";
        document.getElementById("graph-panel").hidden = impact;
        document.getElementById("impact-panel").hidden = !impact;
      });
    });
    Promise.all([loadJson("/api/graph"), loadJson("/api/report")]).then(([graph, report]) => {
      state.graph = graph;
      state.report = report;
      render();
    });
  </script>
</body>
</html>"""


def _dashboard_html() -> str:
    return """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>CodeLens Impact Graph</title>
  <style>
    :root {
      --bg: #eef3ef;
      --ink: #151b1d;
      --muted: #66726f;
      --panel: #fbfcf8;
      --line: #cbd5cf;
      --teal: #0f766e;
      --blue: #2454a6;
      --rust: #a8482f;
      --gold: #b7791f;
      --green: #287a3e;
      --red: #b42318;
      --shadow: rgba(21, 27, 29, 0.12);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background:
        linear-gradient(90deg, rgba(21, 27, 29, 0.04) 1px, transparent 1px),
        linear-gradient(rgba(21, 27, 29, 0.035) 1px, transparent 1px),
        var(--bg);
      background-size: 34px 34px;
      color: var(--ink);
      font-family: "Avenir Next", "Trebuchet MS", "Helvetica Neue", sans-serif;
      letter-spacing: 0;
    }
    header {
      align-items: center;
      border-bottom: 1px solid var(--line);
      display: grid;
      gap: 18px;
      grid-template-columns: minmax(260px, 0.8fr) minmax(320px, 1.2fr) auto;
      padding: 18px 24px;
    }
    .brand {
      font-family: Georgia, "Times New Roman", serif;
      font-size: 34px;
      font-weight: 700;
      line-height: 1;
    }
    .subtitle { color: var(--muted); font-size: 14px; margin-top: 6px; }
    .requirement {
      background: var(--ink);
      border-radius: 8px;
      color: #f8faf6;
      padding: 12px 14px;
    }
    .requirement small { color: #b7c2bd; display: block; font-size: 12px; margin-bottom: 5px; }
    .toolbar { display: flex; gap: 8px; justify-content: flex-end; }
    button {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      color: var(--ink);
      cursor: pointer;
      font: inherit;
      font-weight: 700;
      padding: 10px 12px;
    }
    button.active { background: var(--ink); color: #f8faf6; }
    main {
      display: grid;
      gap: 18px;
      grid-template-columns: minmax(0, 1fr) 380px;
      padding: 18px 24px 24px;
    }
    section, aside {
      background: rgba(251, 252, 248, 0.94);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 18px 36px var(--shadow);
    }
    .graph-shell { min-height: 620px; padding: 16px; }
    .metrics {
      display: grid;
      gap: 10px;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      margin-bottom: 14px;
    }
    .metric {
      border-left: 5px solid var(--teal);
      padding: 6px 0 6px 12px;
    }
    .metric strong { display: block; font-family: Georgia, serif; font-size: 28px; line-height: 1; }
    .metric span { color: var(--muted); display: block; font-size: 12px; margin-top: 6px; }
    .graph-head {
      align-items: center;
      display: flex;
      justify-content: space-between;
      margin-bottom: 12px;
    }
    h2 { font-size: 16px; margin: 0; }
    .legend { color: var(--muted); display: flex; flex-wrap: wrap; gap: 10px; font-size: 12px; }
    .dot { border-radius: 999px; display: inline-block; height: 9px; margin-right: 5px; width: 9px; }
    .stage {
      background: #f7faf6;
      border: 1px solid var(--line);
      border-radius: 8px;
      height: 510px;
      overflow: hidden;
      position: relative;
    }
    .edges {
      height: 100%;
      left: 0;
      pointer-events: none;
      position: absolute;
      top: 0;
      width: 100%;
      z-index: 1;
    }
    .edge { stroke: #b8c3be; stroke-width: 1.4; opacity: 0.65; }
    .edge.hot { stroke: var(--rust); stroke-width: 2.6; opacity: 0.95; stroke-dasharray: 7 5; animation: flow 1.6s linear infinite; }
    @keyframes flow { to { stroke-dashoffset: -24; } }
    .node {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 8px 18px rgba(21, 27, 29, 0.09);
      cursor: pointer;
      min-height: 56px;
      padding: 9px 11px;
      position: absolute;
      transform: translate(-50%, -50%);
      width: 154px;
      z-index: 2;
    }
    .node strong {
      display: block;
      font-size: 13px;
      line-height: 1.2;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .node small {
      color: var(--muted);
      display: block;
      font-size: 11px;
      margin-top: 5px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .node::before {
      border-radius: 999px;
      content: "";
      height: 9px;
      position: absolute;
      right: 9px;
      top: 9px;
      width: 9px;
    }
    .node.Page::before { background: var(--teal); }
    .node.Component::before { background: var(--green); }
    .node.API::before { background: var(--blue); }
    .node.Module::before { background: #4b5563; }
    .node.Feature::before { background: var(--gold); }
    .node.affected {
      border-color: var(--rust);
      box-shadow: 0 0 0 3px rgba(168, 72, 47, 0.14), 0 10px 24px rgba(168, 72, 47, 0.16);
    }
    .node.direct {
      background: #fff4ef;
      border-color: var(--red);
    }
    .node.selected { outline: 3px solid rgba(15, 118, 110, 0.28); }
    .node.direct::after {
      animation: pulse 1.8s ease-out infinite;
      border: 2px solid rgba(180, 35, 24, 0.35);
      border-radius: 10px;
      content: "";
      inset: -8px;
      position: absolute;
    }
    @keyframes pulse {
      0% { opacity: 0.85; transform: scale(0.94); }
      100% { opacity: 0; transform: scale(1.2); }
    }
    .side {
      display: grid;
      gap: 14px;
    }
    .panel { padding: 16px; }
    .inspector-title {
      border-bottom: 1px solid var(--line);
      margin-bottom: 12px;
      padding-bottom: 12px;
    }
    .inspector-title strong { display: block; font-size: 18px; overflow-wrap: anywhere; }
    .inspector-title small { color: var(--muted); display: block; margin-top: 5px; overflow-wrap: anywhere; }
    .risk-score {
      align-items: center;
      display: grid;
      gap: 10px;
      grid-template-columns: 72px minmax(0, 1fr);
    }
    .score {
      background: var(--ink);
      border-radius: 8px;
      color: #f8faf6;
      font-family: Georgia, serif;
      font-size: 28px;
      padding: 12px 0;
      text-align: center;
    }
    .muted { color: var(--muted); font-size: 13px; line-height: 1.5; }
    .list {
      display: grid;
      gap: 8px;
      max-height: 220px;
      overflow: auto;
    }
    .item {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 9px 10px;
    }
    .item strong { display: block; font-size: 13px; }
    .item small { color: var(--muted); display: block; font-size: 12px; margin-top: 5px; }
    .matrix {
      display: grid;
      gap: 18px;
      grid-column: 1 / -1;
      grid-template-columns: minmax(0, 1fr) 420px;
    }
    table { border-collapse: collapse; width: 100%; }
    th, td {
      border-bottom: 1px solid var(--line);
      font-size: 13px;
      padding: 10px 8px;
      text-align: left;
      vertical-align: top;
    }
    th { color: var(--muted); font-size: 12px; }
    .badge {
      border-radius: 999px;
      display: inline-block;
      font-size: 12px;
      min-width: 34px;
      padding: 3px 8px;
      text-align: center;
    }
    .p0 { background: #fee4e2; color: var(--red); }
    .p1 { background: #fef0c7; color: var(--gold); }
    .issue {
      border-left: 5px solid var(--gold);
      padding-left: 12px;
    }
    @media (max-width: 1100px) {
      header, main, .matrix { grid-template-columns: 1fr; }
      .toolbar { justify-content: flex-start; }
      .metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
  </style>
</head>
<body>
  <header>
    <div>
      <div class="brand">CodeLens</div>
      <div class="subtitle">项目全景透视 + 需求影响推理</div>
    </div>
    <div class="requirement">
      <small>当前需求</small>
      <div id="requirement">读取中...</div>
    </div>
    <div class="toolbar">
      <button id="all-btn">全景图</button>
      <button id="impact-btn" class="active">影响扩散</button>
    </div>
  </header>
  <main>
    <section class="graph-shell">
      <div class="metrics" id="metrics"></div>
      <div class="graph-head">
        <h2>影响链路图</h2>
        <div class="legend">
          <span><i class="dot" style="background:var(--teal)"></i>页面</span>
          <span><i class="dot" style="background:var(--blue)"></i>接口</span>
          <span><i class="dot" style="background:#4b5563"></i>模块</span>
          <span><i class="dot" style="background:var(--rust)"></i>受影响</span>
        </div>
      </div>
      <div class="stage" id="stage">
        <svg class="edges" id="edges"></svg>
        <div id="nodes"></div>
      </div>
    </section>
    <aside class="side">
      <section class="panel">
        <h2>节点详情</h2>
        <div id="inspector"></div>
      </section>
      <section class="panel">
        <h2>高风险 TOP</h2>
        <div class="list" id="risk-list"></div>
      </section>
    </aside>
    <div class="matrix">
      <section class="panel">
        <h2>回归测试清单</h2>
        <div id="regression"></div>
      </section>
      <section class="panel">
        <h2>需求审查</h2>
        <div id="issues"></div>
      </section>
    </div>
  </main>
  <script>
    const state = {
      graph: { nodes: [], edges: [] },
      report: { directImpact: [], indirectImpact: [], riskMap: {}, regressionList: [], issues: [] },
      impactOnly: true,
      selectedId: null
    };
    const typeOrder = { Page: 0, Component: 0, Feature: 0, API: 1, Module: 2, DataModel: 2, Document: 3 };

    async function loadJson(path) {
      const response = await fetch(path);
      if (!response.ok) return null;
      return response.json();
    }
    function esc(value) {
      return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
      }[char]));
    }
    function impactedSet() {
      return new Set([...(state.report.directImpact || []), ...(state.report.indirectImpact || [])]);
    }
    function directSet() {
      return new Set(state.report.directImpact || []);
    }
    function visibleNodes() {
      const impact = impactedSet();
      const nodes = state.graph.nodes || [];
      const picked = state.impactOnly ? nodes.filter(node => impact.has(node.id)) : nodes;
      return picked.slice(0, 34);
    }
    function layout(nodes) {
      const groups = [[], [], [], []];
      nodes.forEach(node => groups[typeOrder[node.type] ?? 3].push(node));
      const coords = new Map();
      const xByGroup = [18, 43, 70, 88];
      groups.forEach((items, groupIndex) => {
        items.sort((a, b) => a.name.localeCompare(b.name));
        const step = 82;
        const top = Math.max(56, 255 - ((items.length - 1) * step) / 2);
        items.forEach((node, index) => {
          coords.set(node.id, { x: xByGroup[groupIndex], y: top + index * step });
        });
      });
      return coords;
    }
    function renderMetrics() {
      const graph = state.graph;
      const report = state.report;
      const values = [
        ["节点", graph.nodes.length],
        ["关系", graph.edges.length],
        ["直接影响", (report.directImpact || []).length],
        ["需求问题", (report.issues || []).length]
      ];
      document.getElementById("metrics").innerHTML = values.map(([label, value]) =>
        `<div class="metric"><strong>${value}</strong><span>${esc(label)}</span></div>`
      ).join("");
    }
    function renderGraph() {
      const nodes = visibleNodes();
      const ids = new Set(nodes.map(node => node.id));
      const coords = layout(nodes);
      const impact = impactedSet();
      const direct = directSet();
      const stage = document.getElementById("stage");
      const width = stage.clientWidth;
      const height = stage.clientHeight;
      const edges = (state.graph.edges || []).filter(edge => ids.has(edge.source) && ids.has(edge.target));
      document.getElementById("edges").setAttribute("viewBox", `0 0 ${width} ${height}`);
      document.getElementById("edges").innerHTML = edges.map(edge => {
        const from = coords.get(edge.source);
        const to = coords.get(edge.target);
        if (!from || !to) return "";
        const x1 = width * from.x / 100;
        const x2 = width * to.x / 100;
        const y1 = from.y;
        const y2 = to.y;
        const hot = impact.has(edge.source) && impact.has(edge.target);
        const mid = (x1 + x2) / 2;
        return `<path class="edge ${hot ? "hot" : ""}" d="M ${x1} ${y1} C ${mid} ${y1}, ${mid} ${y2}, ${x2} ${y2}" fill="none" />`;
      }).join("");
      document.getElementById("nodes").innerHTML = nodes.map(node => {
        const pos = coords.get(node.id);
        const classes = ["node", node.type];
        if (impact.has(node.id)) classes.push("affected");
        if (direct.has(node.id)) classes.push("direct");
        if (state.selectedId === node.id) classes.push("selected");
        const style = `left:${pos.x}%; top:${pos.y}px`;
        const score = state.report.riskMap[node.id]?.score;
        return `<button class="${classes.join(" ")}" style="${style}" data-id="${esc(node.id)}"><strong>${esc(node.name)}</strong><small>${esc(node.type)}${score ? " · risk " + esc(score) : ""}</small></button>`;
      }).join("");
      document.querySelectorAll(".node").forEach(item => {
        item.addEventListener("click", () => {
          state.selectedId = item.dataset.id;
          render();
        });
      });
    }
    function renderInspector() {
      const byId = new Map((state.graph.nodes || []).map(node => [node.id, node]));
      const impact = impactedSet();
      const direct = directSet();
      const fallbackId = (state.report.directImpact || [])[0] || (state.graph.nodes[0] || {}).id;
      const id = state.selectedId || fallbackId;
      const node = byId.get(id);
      if (!node) {
        document.getElementById("inspector").innerHTML = `<p class="muted">暂无节点</p>`;
        return;
      }
      const risk = state.report.riskMap[id] || { score: "-", reason: "未进入当前需求影响范围" };
      const status = direct.has(id) ? "直接影响" : impact.has(id) ? "间接影响" : "未受影响";
      document.getElementById("inspector").innerHTML = `
        <div class="inspector-title">
          <strong>${esc(node.name)}</strong>
          <small>${esc(node.id)}</small>
        </div>
        <div class="risk-score">
          <div class="score">${esc(risk.score)}</div>
          <div>
            <strong>${esc(status)}</strong>
            <p class="muted">${esc(risk.reason)}</p>
          </div>
        </div>
        <p class="muted">类型：${esc(node.type)}<br>路径：${esc(node.path || "-")}</p>
      `;
    }
    function renderRiskList() {
      const byId = new Map((state.graph.nodes || []).map(node => [node.id, node]));
      const entries = Object.entries(state.report.riskMap || {}).sort((a, b) => b[1].score - a[1].score).slice(0, 8);
      document.getElementById("risk-list").innerHTML = entries.map(([id, risk]) => {
        const node = byId.get(id);
        return `<div class="item"><strong>${esc(risk.score)} · ${esc(node ? node.name : id)}</strong><small>${esc(risk.reason)}</small></div>`;
      }).join("") || `<p class="muted">暂无风险数据</p>`;
    }
    function renderRegression() {
      const rows = (state.report.regressionList || []).slice(0, 12);
      document.getElementById("regression").innerHTML = `<table><thead><tr><th>功能</th><th>优先级</th><th>原因</th></tr></thead><tbody>` +
        rows.map(item => `<tr><td>${esc(item.feature)}</td><td><span class="badge ${String(item.priority).toLowerCase()}">${esc(item.priority)}</span></td><td>${esc(item.reason)}</td></tr>`).join("") +
        `</tbody></table>`;
    }
    function renderIssues() {
      document.getElementById("issues").innerHTML = (state.report.issues || []).map(issue =>
        `<div class="issue"><strong>${esc(issue.type)} · ${esc(issue.severity)}</strong><p class="muted">${esc(issue.description)}<br>${esc(issue.suggestion)}</p></div>`
      ).join("") || `<p class="muted">未发现需求问题</p>`;
    }
    function render() {
      document.getElementById("requirement").textContent = state.report.requirement || "未输入需求";
      renderMetrics();
      renderGraph();
      renderInspector();
      renderRiskList();
      renderRegression();
      renderIssues();
    }
    document.getElementById("all-btn").addEventListener("click", () => {
      state.impactOnly = false;
      document.getElementById("all-btn").classList.add("active");
      document.getElementById("impact-btn").classList.remove("active");
      render();
    });
    document.getElementById("impact-btn").addEventListener("click", () => {
      state.impactOnly = true;
      document.getElementById("impact-btn").classList.add("active");
      document.getElementById("all-btn").classList.remove("active");
      render();
    });
    window.addEventListener("resize", render);
    Promise.all([loadJson("/api/graph"), loadJson("/api/report")]).then(([graph, report]) => {
      state.graph = graph || state.graph;
      state.report = report || state.report;
      state.selectedId = (state.report.directImpact || [])[0] || null;
      render();
    });
  </script>
</body>
</html>"""
