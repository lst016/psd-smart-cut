# PSD Smart Cut

> 一个面向 `Cursor`、`Claude`、`Codex` 等 AI 的多 agent 美术资源规划工具台。

`PSD Smart Cut` 的目标不是“把 PSD 图层一层层切出来”，而是先让 AI 看懂页面、拆清模块、规划组件与共享资源，然后再调用确定性的导出工具生成前端和美术都能消费的交付物。

## 当前定位

这个仓库现在明确定位为：

- 一个 `AI orchestrator` 驱动的工作台
- 一个给多角色 agent 协作使用的工具项目
- 一个把“页面理解 -> 组件规划 -> 资源规划 -> 资源任务单 -> 并发切图 -> 复核交付”固化下来的工作流仓库

当前确认下来的 5 条原则：

1. 主入口是 `AI orchestrator`
2. 页面理解必须 `截图优先`
3. PSD 结构只做辅助证据
4. 资源策略默认 `复用优先`
5. 旧 `heuristic pipeline` 只保留为兼容层

## 这项目是什么

- 一个 AI 原生的资源规划工具台
- 一个服务于前端、美术、产品和审阅角色协作的工作流仓库
- 一个把页面、组件、资源和分析文档分层输出的交付系统

## 这项目不是什么

- 不是一个只会按图层导出的固定切图脚本
- 不是一个“读结构后有什么切什么”的傻流程
- 不是一个只能靠单条 pipeline 跑到底的工具

## 仓库结构

```text
psd-smart-cut/
|-- skills/
|   |-- cli.py
|   |-- psd-parser/
|   |   |-- level1-parse/
|   |   |-- level2-classify/
|   |   |-- level3_recognize/
|   |   |-- level4-strategy/
|   |   |-- level5-export/
|   |   |-- level6-extract/
|   |   |-- level7-generate/
|   |   |-- level8-document/
|   |   `-- level9-integration/
|   `-- psd_parser/
|-- docs/
|-- examples/
|-- input/
|-- output/
|-- requirements.txt
`-- README.md
```

## 安装

环境要求：

- Python 3.10+
- `psd-tools`
- `Pillow`

安装依赖：

```bash
pip install -r requirements.txt
```

可选 AI 依赖：

```bash
pip install openai minimax-api
```

## 核心工作流

当前确认下来的 V2 工作流是：

```text
整页截图 / 预览
-> 页面理解
-> 模块树 / 区域树
-> 组件分析
-> 策略层决策
-> 多 agent 组件规划
-> 资源规划
-> 资源任务单
-> 并发切图
-> 复核
-> 交付包
```

更具体地说，执行顺序应是：

1. 先生成整页预览
2. 由 AI 判断页面用途和业务模块
3. 先产出中性的 `component-analysis`
4. 再由不同端侧策略生成 `strategy-decision.<profile>`
5. 再由 `product / frontend / art / game` 等 agent 收敛组件和资源策略
6. 先产出 `resource-task-list.<profile>`
6. 再按 worker 并发执行真实导出
7. 最后用 `review checklist` 复核

## 试运行后的推进方式

每次真实 PSD 试运行结束后，不允许直接跳到下一份 PSD。

必须按这条后续链路推进：

```text
试运行包
-> 复盘
-> 问题分类
-> 策略收敛
-> 白名单精修
-> 回归验证
-> 生产准入判断
-> 决定继续当前 PSD / 切下一份 PSD
```

这条链路的目标是避免“每轮都重新试错”，并把试运行结果真正沉淀成下一轮的默认策略。

## 目标输出层

V2 的目标输出协议是：

- `pages/`
- `components/`
- `resources/`
- `analysis/`

含义如下：

- `pages/`：页面与模块实例，是主入口
- `components/`：可复用组件定义
- `resources/`：唯一物理资源
- `analysis/`：给人审阅和对齐的文档层

V2 现在建议按三层来组织：

- `analysis/`：只放中性事实分析，不带端侧偏好
- `strategies/`：放具体策略 profile 的决策结果
- `plans/`：放策略层落地后的执行任务单

其中建议至少包含：

- `analysis/page-analysis`
- `analysis/component-analysis`
- `strategies/strategy-decision.<profile>`
- `plans/resource-task-list.<profile>`

注意：

- `css 优先`、`image 优先` 这类判断属于策略层，不属于通用分析层
- 同一份 `component-analysis` 可以同时服务 `frontend_web`、`game_client` 等不同 profile

## 核心文档

- [Docs Index](./docs/README.md)
- [Usage Guide](./docs/guides/usage.md)
- [Agent Architecture](./docs/architecture/AGENT-ARCHITECTURE.md)
- [V2 Foundation](./docs/planning/V2-FOUNDATION.md)
- [Frontend Analysis Spec](./docs/protocols/FRONTEND-ANALYSIS-SPEC.md)
- [Strategy Layer Spec](./docs/protocols/STRATEGY-LAYER-SPEC.md)
- [V2 Implementation Plan](./docs/planning/V2-IMPLEMENTATION-PLAN.md)
- [Orchestrator Lifecycle](./docs/architecture/ORCHESTRATOR-LIFECYCLE.md)
- [Post Iteration Workflow](./docs/process/POST-ITERATION-WORKFLOW.md)
- [V2 Job Spec](./docs/protocols/JOB-SPEC.md)
- [V2 Agent Handoff](./docs/protocols/AGENT-HANDOFF.md)
- [V2 Review Package](./docs/protocols/REVIEW-PACKAGE.md)
- [V2 Schemas](./docs/schemas/README.md)
- [Subagent Rules](./docs/architecture/SUBAGENT-RULES.md)
- [Alignment Checklist](./docs/architecture/ALIGNMENT-CHECKLIST.md)

补充文档：

- [Page Understanding Review](./docs/reviews/page-understanding-review.md)
- [Component Export Review](./docs/reviews/component-export-review.md)
- [Delivery Protocol Review](./docs/reviews/delivery-protocol-review.md)

样例与实验：

- [frontend-component-planner skill sample](./docs/examples/agent-skills/frontend-component-planner.SKILL.md)
- [lobby export experiment](./examples/experiments/v2_export_lobby_resources.py)

## 低层工具入口

这些 API 仍然重要，因为它们是 orchestrator 和各类 agent 最终会调用的确定性工具。

### Level 1 解析

```python
from skills.psd_parser.level1_parse import (
    LayerFilter,
    extract_pages,
    parse_psd,
    read_layers,
)

document = parse_psd("design.psd")
print(document.width, document.height)
print(document.page_count, document.total_layers)

pages = extract_pages("design.psd")
print(pages.page_count)

visible_layers = read_layers(
    "design.psd",
    page_index=0,
    filter_type=LayerFilter.VISIBLE,
)
print(visible_layers.layer_count)
```

### 当前兼容层 pipeline

```python
from skills.psd_parser.level9_integration import run_full_pipeline

result = run_full_pipeline(
    psd_path="design.psd",
    output_dir="./output",
    strategy="SMART_MERGE",
    formats=["png", "webp"],
)

print(result.total_layers)
print(result.manifest_paths)
print(result.analysis_paths)
```

注意：
`run_full_pipeline(...)` 现在仍可用于实验和回归，但它只是兼容层，不代表最终产品形态。

### CLI

```bash
python -m skills.cli --help
python -m skills.cli process design.psd --output ./output
python -m skills.cli process design.psd --strategy SMART_MERGE --formats png,webp
python examples/basic_parse.py design.psd
```

## 当前兼容层输出

旧 pipeline 当前仍会输出一套过渡型目录：

```text
output/
|-- assets/
|   `-- png/
|-- config/
|   `-- png/
|       |-- manifest.json
|       `-- *.meta.json
`-- docs/
    |-- page-analysis.json
    |-- page-tree.md
    |-- component-tree.json
    |-- component-tree.md
    `-- page-preview.png
```

这套输出仍然有价值，但它只是过渡产物：

- 适合调试
- 适合回归对照
- 不适合作为最终前端/美术交付协议

## 已验证的试运行方式

围绕真实 PSD，我们已经跑出了一套更接近 V2 的试运行包，核心思路是：

1. 先锁定一个模块
2. 先出页面理解和模块树
3. 再出组件计划与资源计划
4. 再出 `resource-task-list`
5. 再按 worker 并发切图
6. 最后生成真实 `resources/png/index.json`

这套方式已经被用于“设置弹窗模块”的试运行验证。

## 测试

跑完整测试：

```bash
python -m pytest skills/psd-parser -q
```

常用冒烟检查：

```bash
python -m compileall skills examples
python -m skills.cli --help
python examples/basic_parse.py
```

## 当前结论

- 组件分解应由 AI 主导，而不是由图层结构主导
- 切图必须经过“资源任务单”这一层
- 并发 worker 是正式工作流的一部分，不是临时技巧
- 旧 pipeline 继续保留，但不再承载未来架构
