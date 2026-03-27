# PSD Smart Cut 使用说明

本文说明当前仓库里可直接调用的低层工具，以及它们如何挂接到新的多 agent 工作流中。

先给结论：

- 旧 runtime pipeline 仍然存在，但只是兼容层
- 项目的目标产品形态已经切到多 agent AI 工具链
- Python API 仍然重要，因为它们会成为 orchestrator 和 worker 的确定性工具

## 环境

- Python 3.10+
- `psd-tools>=1.14.0`
- `Pillow>=8.0.0`
- `PyYAML>=6.0`
- `pydantic>=2.0.0`

安装依赖：

```bash
pip install -r requirements.txt
```

可选 AI 依赖：

```bash
pip install openai minimax-api
```

## Level 1 API

Level 1 是当前最稳定的低层入口：

```python
from skills.psd_parser.level1_parse import (
    LayerFilter,
    extract_pages,
    parse_psd,
    read_layers,
)
```

### 解析 PSD

```python
document = parse_psd("design.psd")

print(document.file_path)
print(document.width, document.height)
print(document.page_count)
print(document.total_layers)
```

### 提取页面 / 画板

```python
pages = extract_pages("design.psd")

print(pages.success)
print(pages.page_count)
for page in pages.pages:
    print(page["index"], page["name"], page["width"], page["height"])
```

### 读取图层

```python
layers = read_layers(
    "design.psd",
    page_index=0,
    filter_type=LayerFilter.VISIBLE,
)

print(layers.success)
print(layers.layer_count)
print(layers.visible_count)
print(layers.hidden_count)
for layer in layers.layers[:5]:
    print(layer["id"], layer["name"], layer["kind"])
```

## 当前兼容层 Pipeline

兼容层入口仍然是：

```python
from skills.psd_parser.level9_integration import run_full_pipeline
```

示例：

```python
result = run_full_pipeline(
    psd_path="design.psd",
    output_dir="./output",
    strategy="SMART_MERGE",
    formats=["png", "webp"],
    use_recognizer=True,
)

print(result.psd_path)
print(result.output_dir)
print(result.total_layers)
print(result.strategy)
print(result.export_formats)
print(result.manifest_paths)
print(result.analysis_paths)
```

它当前仍会编排：

1. PSD 解析
2. 页面级分析文档生成
3. 组件树生成
4. 图层分类
5. 可选识别
6. 切图策略规划
7. 资源导出

但要注意：

`run_full_pipeline(...)` 不代表最终产品形态，它只是当前仓库里保留的回归/兼容入口。

### 当前输出结构

兼容层当前输出：

- 图片资源
- config 与 manifest
- 页面/组件分析文档

示例：

```text
output/
|-- assets/
|   `-- png/
|-- config/
|   `-- png/
|       |-- manifest.json
|       `-- *.meta.json
`-- docs/
    |-- page-analysis.md
    |-- page-analysis.json
    |-- page-tree.md
    |-- component-tree.json
    |-- component-tree.md
    `-- page-preview.png
```

建议审阅顺序：

1. 先看 `docs/page-preview.png`
2. 再看 `docs/page-analysis.md`
3. 再看 `docs/page-tree.md`
4. 再看 `docs/component-tree.json`
5. 最后再看 `assets/` 和 `config/`

## CLI

仓库当前仍保留了一个轻量 CLI：

```bash
python -m skills.cli --help
```

处理 PSD：

```bash
python -m skills.cli process design.psd --output ./output
```

指定策略和多格式：

```bash
python -m skills.cli process design.psd --strategy SMART_MERGE --formats png,webp
```

跳过识别阶段：

```bash
python -m skills.cli process design.psd --no-recognizer
```

## 示例脚本

当前维护中的示例：

```bash
python examples/basic_parse.py design.psd
```

## V2 正式工作流

现在推荐的正式工作流不是“直接跑 CLI 导出”，而是：

1. 先渲染整页预览
2. 先做页面理解和模块判断
3. 先产出 `frontend-analysis` 和 `implementation-decision`
4. 再由 `product / frontend / art` agent 收敛组件与资源
5. 先产出 `resource-task-list`
6. 再按 worker 并发切图
7. 最后复核和交付

CLI 和低层 API 在这个流程里扮演的是工具角色，不是大脑角色。

### 前端分析层

在真正生成切图任务前，建议先固定产出：

- `analysis/frontend-analysis.md`
- `analysis/frontend-analysis.json`
- `analysis/implementation-decision.json`

这三份文件用来回答：

- 页面里有哪些前端组件
- 每个组件如何拆成子部件
- 哪些部分该切图
- 哪些部分更适合走 `CSS / 文本 / SVG`

详细协议见：

- [Frontend Analysis Spec](./FRONTEND-ANALYSIS-SPEC.md)

## 测试

完整测试：

```bash
python -m pytest skills/psd-parser -q
```

常用冒烟检查：

```bash
python -m compileall skills examples
python -m skills.cli --help
python examples/basic_parse.py
```

## 相关文档

- [Agent Architecture](./AGENT-ARCHITECTURE.md)
- [V2 Foundation](./V2-FOUNDATION.md)
- [Frontend Analysis Spec](./FRONTEND-ANALYSIS-SPEC.md)
- [V2 Implementation Plan](./V2-IMPLEMENTATION-PLAN.md)
- [Orchestrator Lifecycle](./ORCHESTRATOR-LIFECYCLE.md)
- [V2 Job Spec](./JOB-SPEC.md)
- [V2 Agent Handoff](./AGENT-HANDOFF.md)
- [V2 Review Package](./REVIEW-PACKAGE.md)
- [Subagent Rules](./SUBAGENT-RULES.md)
- [V2 Schemas](./schemas/README.md)

## 故障排查

### `psd-tools` 缺失

安装：

```bash
pip install psd-tools
```

### CLI 导入失败

确认当前目录是仓库根目录，并且已从 [`requirements.txt`](../requirements.txt) 安装依赖。

### 识别或 AI 阶段不可用

这些阶段是可选的。你可以：

- 安装可选 AI 依赖
- 在 CLI 里使用 `--no-recognizer`
- 只调用低层解析 API
