# CodeLens

CodeLens 是一个项目功能图谱与需求影响分析 MVP。它可以扫描代码仓库，生成 `.codelens/graph.json`，再根据需求文本生成 `.codelens/report.json`，最后导出离线 HTML 或用内置 Web 页面查看全景图、风险热力、回归清单和需求审查结果。

## 推荐 Demo 流程

```bash
PYTHONPATH=src python3 -m codelens.cli scan ../demo-project
PYTHONPATH=src python3 -m codelens.cli analyze "新增用户批量导入功能，支持 Excel 上传" --project ../demo-project
PYTHONPATH=src python3 -m codelens.cli export --project ../demo-project
```

打开：

```text
../demo-project/.codelens/report.html
```

这个方式不依赖本地端口，不会遇到 `ERR_CONNECTION_REFUSED`。

## 内置服务模式

```bash
PYTHONPATH=src python3 -m codelens.cli serve --project ../demo-project
```

浏览器打开：

```text
http://127.0.0.1:8000
```

## 测试

```bash
PYTHONPATH=src python3 -m unittest discover -v
```

## Docker

```bash
docker compose up --build
```

## 当前能力

- Python FastAPI 路由解析
- Java Spring Controller 路由解析
- React/Next.js 页面、组件、交互入口、fetch API 调用解析
- Markdown 标题功能点解析
- 图谱 JSON 持久化
- 需求影响推理、风险评分、回归清单
- 批量导入、未登录下单、权限类需求的规则审查
- 无第三方依赖的 CLI、HTTP 报告页和离线 HTML 报告
