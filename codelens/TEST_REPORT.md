# CodeLens MVP Test Report

## 自动化测试

```bash
PYTHONPATH=src python3 -m unittest discover -v
```

实际结果：

```text
Ran 15 tests in 0.011s
OK
```

## 演示流程

```bash
source ./use
scan ../demo-project
analyze "新增用户批量导入功能，支持 Excel 上传" --project ../demo-project
export_report --project ../demo-project
```

期望产物：

```text
../demo-project/.codelens/graph.json
../demo-project/.codelens/report.json
../demo-project/.codelens/report.html
```

实际演示结果：

```text
Graph written: ../demo-project/.codelens/graph.json
Functional nodes: 14
Code nodes: 1
Edges: 14

Report written: ../demo-project/.codelens/report.json
Matched features: 4
Related features: 10
Logic issues: 1

Static report written: ../demo-project/.codelens/report.html
```

## 验收清单

- [x] CLI 可以执行 `scan`、`analyze`、`serve`。
- [x] TS/JS、TSX/JSX、Markdown 文件可以被扫描。
- [x] 前端解析可以提取页面、组件、API 调用和交互入口。
- [x] 单文件解析失败记录为非阻断 warning。
- [x] 缺失图谱时 `analyze` 明确提示先执行 `scan`。
- [x] 损坏图谱时 `analyze` 明确提示重新执行 `scan`。
- [x] 报告包含 matchedFeatures、relatedFeatures、riskMap、regressionPoints、logicIssues。
- [x] 批量上传/导入需求能提示缺少文件大小、行数上限和失败策略。
- [x] 内置 HTTP 服务能返回 `/api/graph`、`/api/report` 和报告页。
- [x] `export` 可以生成无需启动服务的离线 HTML 报告。
