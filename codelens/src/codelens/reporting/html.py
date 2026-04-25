from __future__ import annotations

import json
from typing import Any, Dict

from codelens.graph.models import Graph


def render_static_report(graph: Graph, report: Dict[str, Any]) -> str:
    graph_json = _script_json(graph.to_dict())
    report_json = _script_json(report)
    return _template(graph_json, report_json)


def _script_json(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")


def _template(graph_json: str, report_json: str) -> str:
    return """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>CodeLens Demo Report</title>
  <style>
    :root {
      --paper: #f5f1e8;
      --ink: #171a19;
      --muted: #6c716d;
      --panel: #fffdf6;
      --line: #d9d1bf;
      --teal: #0f766e;
      --blue: #2454a6;
      --red: #b42318;
      --amber: #b7791f;
      --green: #287a3e;
      --shadow: rgba(27, 31, 29, 0.09);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background:
        linear-gradient(90deg, rgba(23, 26, 25, 0.035) 1px, transparent 1px),
        linear-gradient(rgba(23, 26, 25, 0.025) 1px, transparent 1px),
        var(--paper);
      background-size: 38px 38px;
      color: var(--ink);
      font-family: "Avenir Next", "Trebuchet MS", "Helvetica Neue", sans-serif;
      letter-spacing: 0;
    }
    header {
      border-bottom: 1px solid var(--line);
      display: grid;
      gap: 18px;
      grid-template-columns: minmax(0, 1fr) auto;
      padding: 24px 28px 18px;
    }
    .brand {
      font-family: Georgia, "Times New Roman", serif;
      font-size: 36px;
      font-weight: 700;
      line-height: 1;
    }
    .subtitle {
      color: var(--muted);
      font-size: 14px;
      margin-top: 8px;
    }
    .requirement {
      background: var(--ink);
      border-radius: 8px;
      color: var(--paper);
      max-width: 560px;
      padding: 14px 16px;
    }
    .requirement small {
      color: #cfc7b8;
      display: block;
      font-size: 12px;
      margin-bottom: 5px;
    }
    main {
      display: grid;
      gap: 18px;
      grid-template-columns: minmax(0, 1.25fr) minmax(340px, 0.75fr);
      padding: 20px 28px 34px;
    }
    section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 14px 28px var(--shadow);
      padding: 18px;
    }
    h2 {
      font-size: 15px;
      margin: 0 0 14px;
    }
    .metrics {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      margin-bottom: 18px;
    }
    .metric {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
    }
    .metric strong {
      display: block;
      font-family: Georgia, "Times New Roman", serif;
      font-size: 30px;
      line-height: 1;
    }
    .metric span {
      color: var(--muted);
      display: block;
      font-size: 12px;
      margin-top: 7px;
    }
    .grid {
      display: grid;
      gap: 10px;
      grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
      max-height: 440px;
      overflow: auto;
      padding-right: 2px;
    }
    .node, .risk, .issue {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      position: relative;
    }
    .node strong, .risk strong, .issue strong {
      display: block;
      font-size: 14px;
      overflow-wrap: anywhere;
    }
    .node small, .risk small, .issue small {
      color: var(--muted);
      display: block;
      font-size: 12px;
      line-height: 1.45;
      margin-top: 7px;
      overflow-wrap: anywhere;
    }
    .node::before {
      border-radius: 999px;
      content: "";
      height: 8px;
      position: absolute;
      right: 12px;
      top: 14px;
      width: 8px;
    }
    .type-API::before { background: var(--blue); }
    .type-Page::before { background: var(--teal); }
    .type-Feature::before { background: var(--amber); }
    .type-Module::before { background: #4b5563; }
    .type-Component::before { background: var(--green); }
    .split {
      display: grid;
      gap: 18px;
    }
    table {
      border-collapse: collapse;
      width: 100%;
    }
    th, td {
      border-bottom: 1px solid var(--line);
      font-size: 13px;
      padding: 10px 8px;
      text-align: left;
      vertical-align: top;
    }
    th {
      color: var(--muted);
      font-size: 12px;
      font-weight: 600;
    }
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
    .risk[data-level="high"] { border-left: 5px solid var(--red); }
    .risk[data-level="mid"] { border-left: 5px solid var(--amber); }
    .risk[data-level="low"] { border-left: 5px solid var(--green); }
    .issue { border-left: 5px solid var(--amber); }
    .empty {
      color: var(--muted);
      padding: 18px 0;
    }
    @media (max-width: 960px) {
      header, main { grid-template-columns: 1fr; }
      .metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
  </style>
</head>
<body>
  <header>
    <div>
      <div class="brand">CodeLens</div>
      <div class="subtitle">项目全景透视 + 需求影响推理报告</div>
    </div>
    <div class="requirement">
      <small>当前需求</small>
      <div id="requirement"></div>
    </div>
  </header>
  <main>
    <div>
      <div class="metrics" id="metrics"></div>
      <section>
        <h2>功能全景节点</h2>
        <div class="grid" id="nodes"></div>
      </section>
      <section style="margin-top:18px">
        <h2>回归测试矩阵</h2>
        <div id="matrix"></div>
      </section>
    </div>
    <aside class="split">
      <section>
        <h2>风险热力</h2>
        <div id="risks"></div>
      </section>
      <section>
        <h2>需求逻辑审查</h2>
        <div id="issues"></div>
      </section>
    </aside>
  </main>
  <script id="graph-data" type="application/json">__GRAPH_JSON__</script>
  <script id="report-data" type="application/json">__REPORT_JSON__</script>
  <script>
    const graph = JSON.parse(document.getElementById("graph-data").textContent);
    const report = JSON.parse(document.getElementById("report-data").textContent);
    const byId = new Map((graph.nodes || []).map(node => [node.id, node]));
    const impacted = new Set([...(report.directImpact || []), ...(report.indirectImpact || [])]);
    document.getElementById("requirement").textContent = report.requirement || "未输入需求";

    function escapeText(value) {
      return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
      }[char]));
    }
    function nodeClass(type) {
      return "node type-" + String(type || "").replace(/[^a-zA-Z0-9_-]/g, "");
    }
    function riskLevel(score) {
      if (score >= 0.66) return "high";
      if (score >= 0.45) return "mid";
      return "low";
    }
    function renderMetrics() {
      const metrics = [
        ["节点", (graph.nodes || []).length],
        ["关系", (graph.edges || []).length],
        ["直接影响", (report.directImpact || []).length],
        ["问题", (report.issues || []).length]
      ];
      document.getElementById("metrics").innerHTML = metrics.map(([label, value]) =>
        `<div class="metric"><strong>${value}</strong><span>${escapeText(label)}</span></div>`
      ).join("");
    }
    function renderNodes() {
      const nodes = [...(graph.nodes || [])].sort((a, b) => Number(impacted.has(b.id)) - Number(impacted.has(a.id)));
      document.getElementById("nodes").innerHTML = nodes.map(node => {
        const mark = impacted.has(node.id) ? " · affected" : "";
        return `<article class="${nodeClass(node.type)}"><strong>${escapeText(node.name)}</strong><small>${escapeText(node.type)}${mark}<br>${escapeText(node.path || node.id)}</small></article>`;
      }).join("");
    }
    function renderRisks() {
      const entries = Object.entries(report.riskMap || {}).sort((a, b) => b[1].score - a[1].score);
      if (!entries.length) {
        document.getElementById("risks").innerHTML = `<div class="empty">暂无风险评分</div>`;
        return;
      }
      document.getElementById("risks").innerHTML = entries.map(([id, risk]) => {
        const node = byId.get(id);
        return `<article class="risk" data-level="${riskLevel(risk.score)}"><strong>${escapeText(risk.score)} · ${escapeText(node ? node.name : id)}</strong><small>${escapeText(id)}<br>${escapeText(risk.reason)}</small></article>`;
      }).join("");
    }
    function renderMatrix() {
      const items = report.regressionList || [];
      if (!items.length) {
        document.getElementById("matrix").innerHTML = `<div class="empty">暂无回归清单</div>`;
        return;
      }
      document.getElementById("matrix").innerHTML = `<table><thead><tr><th>功能</th><th>优先级</th><th>原因</th></tr></thead><tbody>` +
        items.map(item => `<tr><td>${escapeText(item.feature)}</td><td><span class="badge ${String(item.priority).toLowerCase()}">${escapeText(item.priority)}</span></td><td>${escapeText(item.reason)}</td></tr>`).join("") +
        `</tbody></table>`;
    }
    function renderIssues() {
      const issues = report.issues || [];
      if (!issues.length) {
        document.getElementById("issues").innerHTML = `<div class="empty">未发现需求问题</div>`;
        return;
      }
      document.getElementById("issues").innerHTML = issues.map(issue =>
        `<article class="issue"><strong>${escapeText(issue.type)} · ${escapeText(issue.severity)}</strong><small>${escapeText(issue.description)}<br>${escapeText(issue.suggestion)}</small></article>`
      ).join("");
    }
    renderMetrics();
    renderNodes();
    renderRisks();
    renderMatrix();
    renderIssues();
  </script>
</body>
</html>""".replace("__GRAPH_JSON__", graph_json).replace("__REPORT_JSON__", report_json)
