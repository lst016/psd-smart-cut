# Orchestrator 生命周期

本文定义 `PSD Smart Cut V2` 中默认的 orchestrator 生命周期。

## 角色定位

orchestrator 是系统主入口。

它不直接盲切图，而是协调：

- 页面理解
- 模块规划
- 组件规划
- 资源规划
- 资源任务单
- 并发导出
- 审阅

## 默认顺序

```text
1. Ingest
2. Preview
3. Product Pass
4. Frontend Pass
5. Art Pass
6. Plan Merge
7. Resource Task List
8. Parallel Export
9. Review Pass
10. Final Package
11. Iteration Closeout
```

## 各阶段说明

### 1. Ingest

输入：

- 截图或整页预览
- 可选 PSD 文件
- 可选已有页面元数据

输出：

- 任务上下文
- 输入源引用

规则：

- 截图是主理解源
- PSD 结构只是辅助证据

### 2. Preview

目标：

- 生成所有 agent 共用的整页预览

输出：

- `analysis/page-preview.png`

规则：

- 后续所有判断都应以预览图为锚点

### 3. Product Pass

负责角色：

- product-oriented subagent

目标：

- 先看懂这页是做什么的
- 拆清业务模块和子页面关系

必须产出：

- 页面摘要
- 模块树
- 子页面关系
- 主次区域判断

### 4. Frontend Pass

负责角色：

- frontend-oriented subagent

目标：

- 定义前端意义上的组件和状态模型

必须产出：

- 组件计划
- 状态计划
- 文本保留策略
- 实例与共享组件的拆分

### 5. Art Pass

负责角色：

- art-oriented subagent

目标：

- 定义哪些内容必须保留为图片
- 定义资源粒度和复用边界

必须产出：

- 资源候选清单
- 共享皮肤策略
- 必须烘焙为图的理由

### 6. Plan Merge

负责角色：

- orchestrator

目标：

- 合并产品、前端和美术三方意见，得到一份统一计划

必须产出：

- `pages` 草案
- `components` 草案
- `resources` 草案
- 分歧清单

### 7. Resource Task List

负责角色：

- orchestrator 或专门的 planning worker

目标：

- 把“资源规划”落实为可执行任务单

必须产出：

- `analysis/resource-task-list.json`
- `analysis/export-work-queue.json`

规则：

- 没有任务单，不允许直接导出
- 任务单必须写明资源 key、来源、优先级、是否共享、复核重点
- 如果资源需要先隐藏背景再导出，任务单必须显式写出：
  - `preferred_strategy: hide_background_then_render`
  - `background_layer_ids`
  - 可选 `context_layer_ids`

### 8. Parallel Export

负责角色：

- export worker A / B / C ...

目标：

- 按任务单并发执行真实资源导出

必须产出：

- `resources/`
- 实际资源文件
- 更新后的 `resources/<format>/index.json`

### 9. Review Pass

负责角色：

- review-oriented subagent

目标：

- 检查交付包是否符合计划

必须检查：

- 过切
- 漏切
- 重复资源
- 状态建模错误
- 文本误烘焙

### 10. Final Package

目标输出协议：

```text
output/
├─ pages/
├─ components/
├─ resources/
└─ analysis/
```

### 11. Iteration Closeout

目标：

- 判断本轮结果是进入生产、继续精修，还是仅作为试运行归档

必须产出：

- 复盘结论
- 失败点分类
- 下一轮策略收敛项
- 是否允许切换到下一份 PSD 的判断

规则：

- 只要结果未达到生产准入线，就必须进入“复盘 -> 收敛 -> 白名单精修 -> 回归验证”
- 不允许在没有复盘结论的情况下直接开始下一份 PSD
- 如果某类资源连续失败，应升级为白名单治理，而不是继续走通用链路

## 每个阶段至少要交什么

### Analysis

- `analysis/page-preview.png`
- `analysis/page-analysis.md`
- `analysis/module-tree.md`
- `analysis/component-plan.md`
- `analysis/resource-task-list.json`
- `analysis/review-checklist.md`

### Pages

- `pages/<page_key>.json`

### Components

- `components/<component_key>.json`

### Resources

- `resources/<format>/<resource_key>.<ext>`
- `resources/<format>/index.json`

## 默认失败规则

- 如果产品层对模块理解不清楚，停止导出
- 如果前端和美术对资源复用意见冲突，升级到 merge
- 如果 review 发现相同视觉资源被重复导出，判失败
- 如果某个资源无法从截图理解中被解释，不应进入正式输出

## 为什么这很重要

它可以避免旧错误流程：

- 先解析 PSD
- 再从 group 猜组件
- 然后命中什么就导什么

而强制执行：

- 先理解
- 再规划
- 再列任务
- 最后导出

同时它也避免新的错误流程：

- 试运行出结果后直接换 PSD
- 失败点没有归档
- 每轮都重新探索同一类资源问题
- 无法判断当前结果是否已经达到生产准入
