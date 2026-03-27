# V2 实施计划

本文把已经锁定的 V2 产品决策翻译成具体实施阶段。

## 总目标

构建一个服务于前端与美术交付的多 agent AI 工作台，而不是一个固定的 PSD 切图器。

## 阶段 1：Orchestrator 规范

先把 orchestrator 定义清楚，作为整个系统的主入口。

交付物：

- orchestrator 职责定义
- agent 角色划分
- agent 交接协议
- 不确定情况下的 fallback 规则

## 阶段 2：数据模型重构

把 V2 的四层模型固定下来。

必须有：

- `PageModel`
- `RegionModel`
- `ComponentModel`
- `ResourceModel`

结果要求：

- 每层都有确定性的 JSON schema
- id 和引用稳定
- 组件实例和资源身份明确分离

## 阶段 3：输出协议重构

替换当前混合型 manifest 逻辑，改成分层协议。

目标结构：

```text
output/
├─ pages/
├─ components/
├─ resources/
└─ analysis/
```

结果要求：

- `pages` 引用组件实例
- `components` 引用可复用资源
- `resources` 描述唯一物理资源
- `analysis` 只放给人看的审阅材料

## 阶段 4：AI 规划工具化

把当前单体 pipeline 拆成可组合工具。

建议工具面：

- `render_page_preview`
- `analyze_page_modules`
- `build_region_tree`
- `plan_components`
- `plan_resources`
- `build_resource_task_list`
- `export_resources`
- `write_component_specs`
- `write_page_specs`
- `review_delivery_package`

## 阶段 5：Agent 工作流与 Prompt 规范

定义各类专职 agent 如何思考和输出。

必须覆盖：

- `product`
- `frontend`
- `art`
- `export`
- `review`

结果要求：

- 共享词汇表
- 结构化输出
- 明确冲突处理规则

## 阶段 6：资源任务单与并发导出

这是当前工作流中新增且已经验证有效的一层。

必须新增：

- `analysis/resource-task-list.json`
- `analysis/export-work-queue.json`
- `analysis/review-checklist.md`

结果要求：

- 切图前先有任务单
- 资源按类别分 worker 并发执行
- 每个 worker 都有明确复核目标

## 阶段 6.5：资源类型分流与导出策略治理

这是本轮大厅稿试运行后新增出来的关键阶段，优先级很高。

必须新增：

- 资源类型分类器
- 每类资源的默认导出策略
- 白名单覆盖机制
- 失败后的 fallback 规则

建议资源类型至少包含：

- `export_ready_single_layer`
- `single_layer_icon`
- `explicit_layer_combo`
- `composed_icon`
- `context_state_asset`
- `shared_skin`
- `instance_crop`
- `hero_artwork`

结果要求：

- 不是所有资源都走同一条导出链
- 每种资源都能明确回答“为什么这样切”
- 资源策略能被文档和任务单显式表达
- 每个资源在升级到复杂策略前，都要先经过“单层直出探测”

## 阶段 6.6：PSD 差分隔离

这是多层嵌套 UI 资源进入生产可用前必须补上的能力。

目标：

- 解决“需要上下文，但不能带背景”的资源导出问题

核心方法：

- 父组完整渲染
- 去目标渲染
- 两者差分得到目标贡献

结果要求：

- 适用于底部栏、状态资源、复杂组合图标
- 比通用视觉抠图更稳定
- 作为正式工具进入导出链，而不是临时实验脚本

## 阶段 6.7：试运行后收敛机制

这是为了避免项目在多份真实 PSD 之间反复试错而新增的阶段。

必须新增：

- 标准复盘模板
- 问题分类规则
- 资源白名单治理流程
- 生产准入判断流程

结果要求：

- 每次试运行结束后，都能明确回答“下一步该继续修哪里”
- 每轮暴露的问题都会被沉淀成默认策略或白名单
- 项目状态能明确区分为“工程探索”或“生产可用”

## 阶段 7：兼容层隔离

保留旧 heuristic pipeline，但冻结成兼容模式。

规则：

- 不再把它当主架构扩展
- 继续允许回归和 fallback 调用
- 与 orchestrator-first 路径明确隔离

## 当前建议的优先顺序

1. orchestrator 规范
2. 数据模型
3. 输出协议
4. 资源任务单机制
5. agent 工作流
6. 工具拆分
7. 兼容层隔离

## 当前最有价值的下一步

下一阶段最值得做的是：

1. 落实 `单层直出探测`
2. 落实 `资源类型分流`
3. 落实 `PSD 差分隔离`
4. 把 `resource-task-list -> export-work-queue -> review-checklist` 做成真正可执行脚本
5. 建立“试运行后收敛”机制
6. 把真实 PSD 的试运行包变成标准回归样例

因为这几件事一旦落下，V2 才有机会从“方法正确”进入“产物可交付”。

## 当前阶段判断

根据最新大厅稿试运行结果，当前项目状态应明确标注为：

- `方向正确`
- `产物未达到生产可用`
- `需要转入精修阶段`

本轮正式复盘见：

- `docs/process/ITERATION-RETRO-V2-LOBBY.md`
- `docs/process/POST-ITERATION-WORKFLOW.md`
