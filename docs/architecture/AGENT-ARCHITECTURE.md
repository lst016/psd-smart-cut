# Agent 架构

## 项目定位

`PSD Smart Cut` 应被视为一个 AI 原生的资源规划工具台，而不是一个固定 PSD 导出 pipeline。

它的核心价值不是“读取 PSD 结构然后切图”，而是：

- 先让 AI 看懂整页
- 再让多个角色 agent 讨论模块、组件与资源边界
- 再让这些 agent 决定哪些东西应成为可复用资源、组件定义和页面协议
- 最后才调用确定性工具执行导出

## 核心原则

正确流程是：

1. 视觉理解优先
2. PSD 结构辅助对齐
3. 前端分析与实现决策
4. 多 agent 规划
5. 资源任务单
6. 并发切图
7. 复核交付

错误流程是：

1. 先解析 PSD
2. 从 group 猜组件
3. 规则命中什么就导什么

## 角色划分

### Orchestrator Agent

orchestrator 负责拥有整个会话。

职责：

- 观察整页截图或预览
- 判断这页有几个业务模块
- 拉起并协调专职 agent
- 合并结论，产出统一资产计划

### Product Agent

站在产品视角理解页面。

职责：

- 判断页面是干什么的
- 区分独立页面和子页面
- 定义业务模块边界
- 判断哪些块是功能模块，哪些只是装饰区域

### Frontend Agent

站在前端实现视角建模组件。

职责：

- 判断有哪些可复用组件
- 判断状态资源应如何抽离
- 避免实例级过度导出
- 定义文本、状态、资源如何被前端消费
- 判断哪些子部件应走 `image / css / text / svg`
- 基于中性的 `component-analysis` 产出 `strategy-decision.frontend_web`

注意：

- `css 优先` 只是 `frontend_web` 策略的结论
- 后续如果接入 `game_client`，应新增独立策略，而不是改写分析层事实

例子：

- switch 行应被建模为：
  - label 文本
  - state 文本
  - switch 控件资源
- 底部按钮组应被建模为：
  - 共享按钮皮肤
  - 多个按钮实例

### Art Agent

站在美术资源视角决定哪些东西必须保留为图片。

职责：

- 区分视觉资源与可实现样式
- 判断背景复用策略
- 判断文字应保持可编辑还是烘焙进图
- 识别共享皮肤、图标和装饰资源

### Export Agent

export agent 不是规划者，而是执行者。

职责：

- 按计划渲染唯一资源
- 写组件定义
- 写页面定义
- 保持 id、hash、引用稳定

### Review Agent

review agent 负责检查交付是否真的合理。

职责：

- 检查资源复用是否成立
- 检查组件定义是否完整
- 检查页面和组件引用是否正确
- 标记过切、漏切和重复切

## 目标执行链

```text
整页预览
-> 页面理解
-> 模块树
-> 区域树
-> 前端分析
-> 实现决策
-> 组件规划
-> 资源规划
-> 资源任务单
-> 并发切图
-> Export + Specs
-> Review
```

## 目标数据模型

系统需要稳定区分 4 个概念：

1. `PageModel`
2. `RegionModel`
3. `ComponentModel`
4. `ResourceModel`

在这 4 个正式模型之外，还需要一层强制分析层：

5. `FrontendAnalysis`

### PageModel

描述业务页面与模块实例。

建议字段：

- `page_id`
- `page_type`
- `summary`
- `regions`
- `component_instances`

### RegionModel

描述大块视觉与功能区域。

建议字段：

- `region_id`
- `region_type`
- `purpose`
- `bounds`
- `children`

### ComponentModel

描述前端意义上的组件。

建议字段：

- `component_id`
- `component_type`
- `bounds`
- `subparts`
- `states`
- `text_specs`
- `resource_refs`

### ResourceModel

描述唯一物理资源。

建议字段：

- `resource_id`
- `resource_key`
- `path`
- `hash`
- `dimensions`
- `usage_count`

### FrontendAnalysis

描述前端如何理解一个组件，以及如何决定实现方式。

建议字段：

- `component_id`
- `component_type`
- `subparts`
- `states`
- `implementation_modes`
- `text_slots`
- `export_priority`

## 示例：设置弹窗

当前样例中的左侧画面，更合理的理解是：

```text
SettingsModal
|- ModalFrame
|- Header
|  |- TitleText
|  `- CloseIcon
|- AdBanner
|  |- BannerArtwork
|  `- DownloadAppButton
|- SettingsForm
|  |- ToggleRow: BackgroundMusic
|  |- ToggleRow: GameSound
|  |- ToggleRow: BigWinBroadcast
|  `- ToggleRow: ChatPreview
|- Divider
`- ActionButtonGroup
   |- ButtonInstance: FB
   |- ButtonInstance: OfficialSite
   |- ButtonInstance: AddToHome
   |- ButtonInstance: Disclaimer
   |- ButtonInstance: Support
   `- ButtonInstance: Logout
```

而资源层应更接近：

- `modal_header_skin`
- `modal_body_background`
- `close_icon`
- `banner_artwork`
- `download_button`
- `switch_track_on`
- `switch_track_off`
- `switch_thumb`
- `divider_line`
- `button_normal`
- `button_secondary`

而不是：

- 6 张底部按钮位图
- 4 张 switch 行截图
- 一张糊在一起的 `modal_shell`

## 工具设计方向

工具层应暴露可组合的工具，而不是一个单体大 pipeline。

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

## 代码库应该如何变化

从架构角度看，应逐步做到：

- 远离“一条 `run_full_pipeline(...)` 跑到底”的思维
- 保留确定性的低层工具
- 把规划逻辑迁移到 agent 编排层
- 把旧 heuristic pipeline 冻结成 fallback

## 当前与目标的差距

当前代码还有很多旧行为：

- 先解析结构
- 再从 group 猜组件
- 再靠阈值补漏
- 最后导图

目标行为应该是：

- 先理解页面
- 再做前端分析与实现决策
- 再按角色判断模块与组件
- 再用前端和美术逻辑决定复用资源
- 先出任务单，再执行导出
