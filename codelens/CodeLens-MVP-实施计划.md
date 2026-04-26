# CodeLens MVP 实施计划

## 当前定位

CodeLens 当前只做前端项目分析：先扫描现有代码里的功能点，再用新需求去匹配这些功能点，输出可能要改的地方、潜在逻辑漏洞和建议回归点。

## 目录约定

```text
demo/
├── codelens/       # 工具本身
└── demo-project/   # 被分析的前端示例项目
```

## 使用流程

```bash
cd codelens
PYTHONPATH=src python3 -m codelens.cli scan ../demo-project
PYTHONPATH=src python3 -m codelens.cli analyze "新增用户批量导入功能，支持 Excel 上传" --project ../demo-project
PYTHONPATH=src python3 -m codelens.cli serve --project ../demo-project --host 127.0.0.1 --port 8000
```

浏览器打开：

```text
http://127.0.0.1:8000
```

## 已实现范围

- 扫描 TS/JS、TSX/JSX 和 Markdown 文件。
- 提取前端页面、组件、点击入口、fetch API 调用和文档功能点。
- 生成 `.codelens/graph.json` 功能点图谱。
- 输入新需求后生成 `.codelens/report.json`。
- 报告包含命中功能点、关联功能点、逻辑漏洞、风险评分和建议回归点。
- 提供本地网页 Demo 和离线 HTML 报告。

## 暂不做

- 不分析服务端代码。
- 不解析数据库、接口实现或部署链路。
- 不自动修改业务代码。
- 不替代人工评审，只作为需求评审前的辅助清单。

## 下一步

1. 优化功能点命名，让页面里展示更接近产品语言。
2. 支持上传或粘贴 PRD 文档，一次生成需求审查报告。
3. 增加“为什么命中”的解释，展示关键词和代码来源。
4. 增加回归用例导出，方便给测试同事使用。
