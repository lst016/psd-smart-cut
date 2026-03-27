# 策略层协议

本文定义 `PSD Smart Cut V2` 中的策略层。

策略层解决的问题不是“这个 PSD 里有什么”，而是：

1. 针对某个端侧或消费方，应该如何实现这些组件
2. 哪些子部件走 `image / css / text / svg`
3. 哪些资源真的需要导出，哪些应该降级为样式或文本

## 为什么要单独拆出策略层

`component-analysis` 必须保持中性。

它只回答事实：

- 这是什么组件
- 组件由哪些子部件组成
- 哪些是品牌视觉、文本、纯色底板、状态层
- 哪些资源可以单层直出

而下面这些判断都不该写死进分析层：

- `CSS 优先`
- `游戏端位图优先`
- `SVG 优先`
- `文本必须烘焙`

这些都属于具体策略 profile。

## 三层模型

正确分层应为：

```text
analysis/
-> component-analysis

strategies/
-> strategy-decision.<profile>

plans/
-> resource-task-list.<profile>
```

含义：

- `analysis/`：中性事实
- `strategies/`：端侧策略
- `plans/`：执行任务

## 推荐 profile

建议至少支持：

- `frontend_web`
- `frontend_h5`
- `game_client`
- `marketing_export`

同一份 `component-analysis` 可以派生出多套策略决策。

## `strategy-decision.<profile>.json` 推荐结构

```json
{
  "profile": "frontend_web",
  "based_on": "analysis/component-analysis.json",
  "components": [
    {
      "component_id": "bottom_nav_item",
      "implementation": [
        {
          "part_id": "icon",
          "preferred_mode": "image",
          "reason": "品牌或复杂视觉不适合 CSS 还原"
        },
        {
          "part_id": "label_text",
          "preferred_mode": "text",
          "reason": "文案需要可编辑"
        },
        {
          "part_id": "badge_bg",
          "preferred_mode": "css",
          "reason": "纯色小红点优先前端样式实现"
        }
      ]
    }
  ]
}
```

## 典型例子

同一个组件在不同 profile 下，结论可以不同。

### `bottom_nav_item`

`frontend_web`

- `icon -> image`
- `label_text -> text`
- `active_bg -> image`
- `badge_bg -> css`
- `badge_text -> text`

`game_client`

- `icon -> image`
- `label_text -> image_or_bitmap_text`
- `active_bg -> image`
- `badge_bg -> image`
- `badge_text -> image_or_bitmap_text`

这正是策略层存在的意义。

## 硬规则

1. 分析层不能写死某个端侧的偏好。
2. 策略层必须显式声明 `profile`。
3. `resource-task-list` 必须从某个明确的 `strategy-decision.<profile>.json` 生成。
4. 如果未来新增端侧，不应修改分析层事实，只应新增或调整策略 profile。
