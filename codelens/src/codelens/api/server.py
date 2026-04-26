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
      --panel: #fffdf7;
      --teal: #0f766e;
      --blue: #2454a6;
      --amber: #b7791f;
      --red: #b42318;
      --green: #287a3e;
      --shadow: rgba(32, 35, 35, 0.08);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background:
        linear-gradient(90deg, rgba(32, 35, 35, 0.03) 1px, transparent 1px),
        linear-gradient(rgba(32, 35, 35, 0.03) 1px, transparent 1px),
        var(--paper);
      background-size: 36px 36px;
      color: var(--ink);
      font-family: "Avenir Next", "Trebuchet MS", "Helvetica Neue", sans-serif;
    }
    header {
      align-items: center;
      border-bottom: 1px solid var(--line);
      display: grid;
      gap: 16px;
      grid-template-columns: minmax(0, 1fr) auto;
      padding: 18px 24px;
    }
    .brand {
      font-family: Georgia, "Times New Roman", serif;
      font-size: 32px;
      font-weight: 700;
      line-height: 1;
    }
    .subtitle { color: var(--muted); font-size: 14px; margin-top: 6px; }
    .tabs { display: flex; gap: 8px; }
    .tabs button {
      background: transparent;
      border: 1px solid var(--line);
      border-radius: 8px;
      color: var(--ink);
      cursor: pointer;
      font: inherit;
      font-weight: 700;
      padding: 9px 12px;
    }
    .tabs button.active { background: var(--ink); color: var(--paper); }
    main {
      display: grid;
      gap: 18px;
      grid-template-columns: minmax(0, 1.25fr) minmax(320px, 0.75fr);
      padding: 20px 24px 28px;
    }
    section {
      background: rgba(255, 253, 247, 0.95);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 16px 30px var(--shadow);
      padding: 16px;
    }
    .metrics {
      display: grid;
      gap: 10px;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      margin-bottom: 14px;
    }
    .metric { border-left: 4px solid var(--teal); padding: 6px 0 6px 12px; }
    .metric strong {
      display: block;
      font-family: Georgia, "Times New Roman", serif;
      font-size: 26px;
      line-height: 1;
    }
    .metric span { color: var(--muted); display: block; font-size: 12px; margin-top: 6px; }
    .graph-head {
      align-items: center;
      display: flex;
      justify-content: space-between;
      margin-bottom: 12px;
    }
    h1, h2 { margin: 0; }
    h1 { font-size: 20px; }
    h2 { font-size: 16px; }
    .legend {
      color: var(--muted);
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      font-size: 12px;
    }
    .dot { border-radius: 999px; display: inline-block; height: 9px; margin-right: 5px; width: 9px; }
    .stage {
      background: #fafbf7;
      border: 1px solid var(--line);
      border-radius: 8px;
      height: 520px;
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
    .edge { stroke: #bbc4bf; stroke-width: 1.4; opacity: 0.7; }
    .edge.hot { stroke: var(--red); stroke-dasharray: 7 5; stroke-width: 2.6; }
    .node {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 8px 16px rgba(32, 35, 35, 0.08);
      cursor: pointer;
      min-height: 56px;
      padding: 10px 11px;
      position: absolute;
      transform: translate(-50%, -50%);
      width: 160px;
      z-index: 2;
    }
    .node strong {
      display: block;
      font-size: 13px;
      line-height: 1.25;
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
    .node.Feature::before { background: var(--amber); }
    .node.direct { border-color: var(--red); box-shadow: 0 0 0 3px rgba(180, 35, 24, 0.12), 0 8px 16px rgba(180, 35, 24, 0.12); }
    .node.affected { border-color: var(--amber); }
    .node.selected { outline: 3px solid rgba(15, 118, 110, 0.22); }
    .side { display: grid; gap: 16px; }
    .list {
      display: grid;
      gap: 8px;
      max-height: 240px;
      overflow: auto;
    }
    .item, .issue {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px 11px;
    }
    .item strong, .issue strong { display: block; font-size: 13px; }
    .item small, .issue small {
      color: var(--muted);
      display: block;
      font-size: 12px;
      line-height: 1.45;
      margin-top: 5px;
      overflow-wrap: anywhere;
    }
    .risk-score {
      align-items: center;
      display: grid;
      gap: 10px;
      grid-template-columns: 68px minmax(0, 1fr);
      margin-top: 12px;
    }
    .score {
      background: var(--ink);
      border-radius: 8px;
      color: var(--paper);
      font-family: Georgia, "Times New Roman", serif;
      font-size: 26px;
      padding: 12px 0;
      text-align: center;
    }
    .muted { color: var(--muted); font-size: 13px; line-height: 1.5; }
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
    .p1 { background: #fef0c7; color: var(--amber); }
    .matrix {
      display: grid;
      gap: 18px;
      grid-column: 1 / -1;
      grid-template-columns: minmax(0, 1fr) 420px;
    }
    .empty { color: var(--muted); padding: 18px 0; }
    @media (max-width: 1100px) {
      header, main, .matrix { grid-template-columns: 1fr; }
      .metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .graph-head { align-items: flex-start; flex-direction: column; gap: 8px; }
    }
  </style>
</head>
<body>
  <header>
    <div>
      <div class="brand">CodeLens</div>
      <div class="subtitle">现有功能点扫描 + 新需求审查</div>
    </div>
    <nav class="tabs">
      <button id="graph-btn" class="active">功能点图谱</button>
      <button id="review-btn">需求审查</button>
    </nav>
  </header>
  <main>
    <section>
      <div class="metrics" id="metrics"></div>
      <div class="graph-head">
        <h2>现有功能点图谱</h2>
        <div class="legend">
          <span><i class="dot" style="background:var(--teal)"></i>页面</span>
          <span><i class="dot" style="background:var(--green)"></i>组件</span>
          <span><i class="dot" style="background:var(--blue)"></i>接口</span>
          <span><i class="dot" style="background:var(--amber)"></i>命中</span>
        </div>
      </div>
      <div class="stage" id="stage">
        <svg class="edges" id="edges"></svg>
        <div id="nodes"></div>
      </div>
    </section>
    <aside class="side">
      <section>
        <h2>功能点详情</h2>
        <div id="inspector"></div>
      </section>
      <section>
        <h2>高风险功能点</h2>
        <div class="list" id="risk-list"></div>
      </section>
    </aside>
    <div class="matrix">
      <section>
        <h2>建议回归点</h2>
        <div id="matrix"></div>
      </section>
      <section>
        <h2>逻辑漏洞</h2>
        <div id="issues"></div>
      </section>
    </div>
  </main>
  <script>
    const state = {
      graph: { nodes: [], edges: [] },
      report: { matchedFeatures: [], relatedFeatures: [], riskMap: {}, regressionPoints: [], logicIssues: [] },
      showAll: false,
      selectedId: null
    };

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
    function featureSet() {
      return new Set([...(state.report.matchedFeatures || state.report.directImpact || []), ...(state.report.relatedFeatures || state.report.indirectImpact || [])]);
    }
    function directSet() {
      return new Set(state.report.matchedFeatures || state.report.directImpact || []);
    }
    function visibleNodes() {
      const features = featureSet();
      const nodes = (state.graph.nodes || []).filter(node => node.type !== "Module");
      const picked = state.showAll ? nodes : nodes.filter(node => features.has(node.id));
      return picked;
    }
    function layout(nodes) {
      const groups = [[], [], [], []];
      const order = { Page: 0, Component: 1, API: 2, Feature: 3 };
      nodes.forEach(node => groups[order[node.type] ?? 3].push(node));
      const coords = new Map();
      groups.forEach((items, index) => {
        items.sort((a, b) => a.name.localeCompare(b.name));
        const x = [18, 40, 64, 84][index];
        const start = Math.max(54, 260 - ((items.length - 1) * 78) / 2);
        items.forEach((node, row) => coords.set(node.id, { x, y: start + row * 78 }));
      });
      return coords;
    }
    function renderMetrics() {
      const graph = state.graph;
      const report = state.report;
      const values = [
        ["功能点", graph.nodes.filter(node => node.type !== "Module").length],
        ["关系", graph.edges.length],
        ["命中", (report.matchedFeatures || report.directImpact || []).length + (report.relatedFeatures || report.indirectImpact || []).length],
        ["漏洞", (report.logicIssues || report.issues || []).length]
      ];
      document.getElementById("metrics").innerHTML = values.map(([label, value]) =>
        `<div class="metric"><strong>${value}</strong><span>${esc(label)}</span></div>`
      ).join("");
    }
    function renderGraph() {
      const nodes = visibleNodes();
      const ids = new Set(nodes.map(node => node.id));
      const coords = layout(nodes);
      const features = featureSet();
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
        const mid = (width * from.x / 100 + width * to.x / 100) / 2;
        const x1 = width * from.x / 100;
        const y1 = from.y;
        const x2 = width * to.x / 100;
        const y2 = to.y;
        const hot = direct.has(edge.source) && features.has(edge.target);
        return `<path class="edge ${hot ? "hot" : ""}" d="M ${x1} ${y1} C ${mid} ${y1}, ${mid} ${y2}, ${x2} ${y2}" fill="none" />`;
      }).join("");

      document.getElementById("nodes").innerHTML = nodes.map(node => {
        const pos = coords.get(node.id);
        const classes = ["node", node.type];
        if (features.has(node.id)) classes.push("affected");
        if (direct.has(node.id)) classes.push("direct");
        if (state.selectedId === node.id) classes.push("selected");
        const risk = state.report.riskMap[node.id]?.score;
        return `<button class="${classes.join(" ")}" style="left:${pos.x}%;top:${pos.y}px" data-id="${esc(node.id)}"><strong>${esc(node.name)}</strong><small>${esc(node.type)}${risk ? " · risk " + esc(risk) : ""}</small></button>`;
      }).join("");

      document.querySelectorAll(".node").forEach(button => {
        button.addEventListener("click", () => {
          state.selectedId = button.dataset.id;
          render();
        });
      });
    }
    function renderInspector() {
      const byId = new Map((state.graph.nodes || []).map(node => [node.id, node]));
      const features = featureSet();
      const direct = directSet();
      const fallbackId = (state.report.matchedFeatures || state.report.directImpact || [])[0] || (state.graph.nodes[0] || {}).id;
      const id = state.selectedId || fallbackId;
      const node = byId.get(id);
      if (!node) {
        document.getElementById("inspector").innerHTML = `<p class="muted">暂无节点</p>`;
        return;
      }
      const risk = state.report.riskMap[id] || { score: "-", reason: "未进入当前需求命中范围" };
      const status = direct.has(id) ? "直接命中" : features.has(id) ? "关联命中" : "未命中";
      document.getElementById("inspector").innerHTML = `
        <strong>${esc(node.name)}</strong>
        <div class="risk-score">
          <div class="score">${esc(risk.score)}</div>
          <div>
            <div>${esc(status)}</div>
            <div class="muted">${esc(risk.reason)}</div>
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
      }).join("") || `<div class="empty">暂无风险数据</div>`;
    }
    function renderRegression() {
      const rows = state.report.regressionPoints || state.report.regressionList || [];
      document.getElementById("matrix").innerHTML = rows.length
        ? `<table><thead><tr><th>功能点</th><th>优先级</th><th>原因</th></tr></thead><tbody>${rows.slice(0, 12).map(item => `<tr><td>${esc(item.feature)}</td><td><span class="badge ${String(item.priority).toLowerCase()}">${esc(item.priority)}</span></td><td>${esc(item.reason)}</td></tr>`).join("")}</tbody></table>`
        : `<div class="empty">暂无回归点</div>`;
    }
    function renderIssues() {
      const issues = state.report.logicIssues || state.report.issues || [];
      document.getElementById("issues").innerHTML = issues.length
        ? issues.map(issue => `<div class="issue"><strong>${esc(issue.type)} · ${esc(issue.severity)}</strong><small>${esc(issue.description)}<br>${esc(issue.suggestion)}</small></div>`).join("")
        : `<div class="empty">未发现逻辑漏洞</div>`;
    }
    function render() {
      renderMetrics();
      renderGraph();
      renderInspector();
      renderRiskList();
      renderRegression();
      renderIssues();
    }
    document.getElementById("graph-btn").addEventListener("click", () => {
      state.showAll = false;
      document.getElementById("graph-btn").classList.add("active");
      document.getElementById("review-btn").classList.remove("active");
      render();
    });
    document.getElementById("review-btn").addEventListener("click", () => {
      state.showAll = true;
      document.getElementById("review-btn").classList.add("active");
      document.getElementById("graph-btn").classList.remove("active");
      render();
    });
    window.addEventListener("resize", render);
    Promise.all([loadJson("/api/graph"), loadJson("/api/report")]).then(([graph, report]) => {
      state.graph = graph || state.graph;
      state.report = report || state.report;
      state.selectedId = (state.report.matchedFeatures || state.report.directImpact || [])[0] || null;
      render();
    });
  </script>
</body>
</html>"""
