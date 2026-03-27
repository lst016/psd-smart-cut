# V2 Agent 交接协议（Handoff Payload）

本文定义 `PSD Smart Cut V2` 中各个 `subagent` 之间如何交接结果。

目标不是传一堆自由文本，而是传一份结构化的“判断结果 + 证据 + 未决问题”。

## 目标

每一次交接都必须回答：

1. 我看到了什么
2. 我做了什么判断
3. 我希望下一个 agent 基于什么继续
4. 还有哪些分歧没有解决

## 交接原则

所有 handoff 都必须遵守：

1. 先给结论，再给证据
2. 证据优先来自截图和页面语义
3. PSD 结构只能作为辅助说明
4. 必须区分“已确认”与“待确认”
5. 必须把复用策略写清楚，不能留给下游猜

## 标准结构

推荐结构如下：

```json
{
  "job_id": "job_add_to_home_v2",
  "from_role": "product",
  "to_role": "frontend",
  "handoff_version": "2.0",
  "summary": "该稿件应被理解为两个业务模块：设置弹窗、加入桌面教学；后者包含 Android/iOS 两个子页面。",
  "confirmed": {
    "page_count": 3,
    "business_module_count": 2,
    "page_keys": [
      "settings_modal",
      "guide_android",
      "guide_ios"
    ]
  },
  "structures": {
    "module_tree_path": "analysis/module-tree.json",
    "page_tree_path": "analysis/page-tree.json"
  },
  "evidence": {
    "preview_image": "analysis/page-preview.png",
    "supporting_layers": [
      "group:设置",
      "group:加入桌面教學"
    ]
  },
  "open_questions": [
    "广告区是否拆成 banner 图与下载按钮两部分",
    "底部按钮组是否全部复用相同 normal/selected 资源"
  ],
  "required_next_actions": [
    "定义前端意义上的组件边界",
    "定义 switch 与按钮组的状态资源"
  ]
}
```

## 公共字段

### `job_id`

必须和入口 `Job Spec` 保持一致。

### `from_role`

当前交接发起角色，建议值：

- `product`
- `frontend`
- `art`
- `export`
- `review`
- `orchestrator`

### `to_role`

下一跳角色。

### `handoff_version`

当前固定为：

```text
2.0
```

### `summary`

一句话摘要，只写本轮核心结论。

### `confirmed`

明确已经确认的结论，不能把猜测写进这里。

### `structures`

引用本轮生成的结构文件。

常见内容：

- 模块树
- 页面树
- 组件树
- 资源计划

### `evidence`

必须包含：

- 主截图或预览图引用
- 必要的 PSD 辅助证据

### `open_questions`

列出还没定论的问题。

如果这里是空，说明当前角色认为可以进入下一阶段。

### `required_next_actions`

告诉下一个 agent 必须完成的动作，而不是泛泛地“继续分析”。

## 各角色必须交什么

### Product -> Frontend

必须交：

- 页面用途判断
- 模块边界
- 子页面关系
- 主次区域划分

不能交：

- 直接写资源文件名
- 跳过模块判断直接下组件结论

### Frontend -> Art

必须交：

- 组件树
- 状态模型
- 文本保留策略
- 组件实例和共享组件的区分

不能交：

- 把每个实例都当独立资源
- 把文字默认都当图片

### Art -> Export

必须交：

- 资源边界
- 共享皮肤策略
- 必须出图的内容
- 可以保持为文本或样式的内容

不能交：

- 没有资源计划就直接导出
- 用“整页背景图”代替本该可复用的资源

### Export -> Review

必须交：

- 资源索引
- 组件定义
- 页面定义
- 去重结果
- 导出异常

不能交：

- 只给图片目录
- 没有 pages/components/resources 的引用关系

## 对 Frontend Subagent 的强约束

这部分是你特别要求的“强行为准则”。

当前端 agent 接手任务时，必须遵守：

1. 先按前端组件思维理解页面，而不是按 PSD group 命名切
2. 默认优先定义“共享状态资源”，而不是导出每个实例
3. 普通按钮文案、tab 文案、说明文案优先保留为文本槽位
4. 只有特殊字效、不可还原样式文字才允许升级为图片
5. `switch` 默认拆为：
   - `track_active`
   - `track_inactive`
   - `thumb`
   - 行级实例配置
6. 按钮组默认拆为：
   - `button_normal`
   - `button_selected`
   - 多个实例文本与行为配置
7. 如果页面理解不清楚，必须回退给 product/orchestrator，而不是盲切

## 未决问题的升级规则

如果出现以下情况，handoff 不能直接继续，必须升级给 `orchestrator`：

1. Product 和 Frontend 对模块边界理解不一致
2. Frontend 和 Art 对资源粒度理解不一致
3. Review 判断存在明显重复导出
4. 当前 agent 无法从截图解释某个组件为何存在

## 推荐目录

建议交接文件放在：

```text
analysis/handoffs/
```

例如：

```text
analysis/handoffs/
|- product-to-frontend.json
|- frontend-to-art.json
|- art-to-export.json
`- export-to-review.json
```

## 与其他协议的关系

- 入口任务由 [V2 任务协议](./JOB-SPEC.md) 定义
- 最终交付物由 [审阅包协议](./REVIEW-PACKAGE.md) 收口
- 各角色的硬规则参考 [Subagent 强制行为准则](./SUBAGENT-RULES.md)
