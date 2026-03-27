# V2 任务协议（Job Spec）

本文定义 `PSD Smart Cut V2` 中由 `AI orchestrator` 发起的标准任务包格式。

这不是一个“跑固定 pipeline”的输入参数说明，而是一份给多 agent 协作使用的任务上下文协议。

## 目标

`Job Spec` 负责回答 4 个问题：

1. 这次任务的目标是什么
2. 主理解来源是什么
3. 协作边界和输出要求是什么
4. 哪些约束是强制的

## 核心原则

`Job Spec` 必须遵守以下原则：

1. 截图优先，PSD 结构为辅
2. 页面理解优先于切图
3. 组件规划优先于资源导出
4. 复用优先于实例级导出
5. 输出必须同时服务前端、美术和审阅
6. 必须先形成中性的组件分析，再生成某个策略 profile 的实现决策

## 标准结构

推荐结构如下：

```json
{
  "job_id": "job_settings_modal_v2",
  "job_type": "page_asset_planning",
  "version": "2.0",
  "goal": "为前端团队和美术团队生成可复用的页面资源方案",
  "primary_input": {
    "preview_image": "analysis/page-preview.png",
    "psd_path": "input/real-psd/设置.psd"
  },
  "understanding_rules": {
    "screenshot_first": true,
    "psd_as_supporting_evidence": true,
    "reuse_first": true,
    "component_plan_before_export": true
  },
  "required_roles": [
    "product",
    "frontend",
    "art",
    "export",
    "review"
  ],
  "deliverables": {
    "analysis": true,
    "pages": true,
    "components": true,
    "resources": true
  },
  "analysis_outputs": {
    "page_analysis": true,
    "component_analysis": true,
    "strategy_decision": true
  },
  "constraints": {
    "language": "zh-CN",
    "avoid_instance_bitmap_duplication": true,
    "keep_text_editable_when_possible": true
  }
}
```

## 字段说明

### `job_id`

任务唯一标识。

要求：

- 在一次完整协作中保持稳定
- 不要和导出图片文件名耦合
- 不要和某个单独 component id 混用

### `job_type`

任务类型，建议先支持：

- `page_asset_planning`
- `component_review`
- `resource_reuse_audit`
- `delivery_package_review`

### `version`

协议版本，当前建议固定为：

```text
2.0
```

### `goal`

用一句话说明本次任务最终要交付什么。

推荐写法：

- 给前端提供组件定义和资源引用
- 给美术提供资源边界和复用策略
- 给审阅者提供页面理解和组件树

### `primary_input`

主输入源。

必须强调：

- `preview_image` 是主理解来源
- `psd_path` 只是辅助证据源

### `understanding_rules`

这部分是强约束，不能省略。

建议至少包括：

- `screenshot_first`
- `psd_as_supporting_evidence`
- `reuse_first`
- `component_plan_before_export`

### `required_roles`

定义这次协作必须经过哪些角色。

默认顺序：

1. `product`
2. `frontend`
3. `art`
4. `export`
5. `review`

### `deliverables`

定义本次必须产出哪些层。

V2 的目标层固定为：

- `analysis`
- `pages`
- `components`
- `resources`

### `analysis_outputs`

定义 `analysis/` 层里这次必须产出的分析文件。

建议至少包括：

- `page_analysis`
- `component_analysis`
- `strategy_decision`

其中：

- `page_analysis` 负责解释页面与模块
- `component_analysis` 负责解释组件与子部件
- `strategy_decision` 负责解释某个 profile 下的 `image / css / text / svg` 决策

### `constraints`

记录任务的硬限制。

推荐字段：

- `language`
- `avoid_instance_bitmap_duplication`
- `keep_text_editable_when_possible`
- `force_visual_reasoning`
- `fallback_pipeline_allowed`

## 必填判断题

在任何 `Job Spec` 里，编排 agent 必须先给出以下判断：

1. 这次任务的主页面有几个业务模块
2. 哪些页面是子页面，而不是独立页面
3. 哪些资源必须复用
4. 哪些文字默认不出图
5. 是否允许兼容层 pipeline 参与辅助输出
6. 哪些子部件应走 `image / css / text / svg`

如果这 5 个问题没有明确答案，不应进入最终导出阶段。

## 针对当前项目的推荐模板

以你当前这类稿件为例，任务描述应该更接近：

```json
{
  "job_id": "job_add_to_home_v2",
  "job_type": "page_asset_planning",
  "version": "2.0",
  "goal": "围绕设置弹窗与加入桌面教学模块，生成前端可消费的页面、组件、资源和分析文档",
  "primary_input": {
    "preview_image": "analysis/page-preview.png",
    "psd_path": "input/real-psd/设置.psd"
  },
  "understanding_rules": {
    "screenshot_first": true,
    "psd_as_supporting_evidence": true,
    "reuse_first": true,
    "component_plan_before_export": true
  },
  "required_roles": [
    "product",
    "frontend",
    "art",
    "export",
    "review"
  ],
  "deliverables": {
    "analysis": true,
    "pages": true,
    "components": true,
    "resources": true
  },
  "analysis_outputs": {
    "page_analysis": true,
    "component_analysis": true,
    "strategy_decision": true
  },
  "constraints": {
    "language": "zh-CN",
    "avoid_instance_bitmap_duplication": true,
    "keep_text_editable_when_possible": true,
    "force_visual_reasoning": true,
    "fallback_pipeline_allowed": true
  }
}
```

## 编排器行为要求

`orchestrator` 在读取 `Job Spec` 后，必须按以下顺序推进：

1. 先产出页面总览和模块判断
2. 再生成模块树和区域树
3. 再先产出中性的 `component-analysis`
4. 再按指定 profile 生成 `strategy-decision`
5. 再交给美术 agent 产出资源计划
6. 只有计划收敛后，才允许导出

禁止行为：

- 直接从 PSD 图层开始切图
- 没有页面理解就开始产出资源
- 还没判断复用策略就导出大量实例级图片

## 与其他协议的关系

`Job Spec` 只是入口。

后续还需要配套：

- [Agent 交接协议](./AGENT-HANDOFF.md)
- [审阅包协议](./REVIEW-PACKAGE.md)
- [Subagent 强制行为准则](./SUBAGENT-RULES.md)
