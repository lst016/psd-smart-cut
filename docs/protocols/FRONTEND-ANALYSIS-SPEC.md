# 前端分析协议

本文定义 `PSD Smart Cut V2` 中截图驱动的前端分析层。

它回答的不是“这次切哪些图”，而是：

1. 这张页面在前端眼里是什么页面
2. 页面里有哪些模块和组件
3. 每个组件应如何拆成前端可实现的子部件
4. 哪些部分该切图，哪些部分应走 CSS，哪些部分应保留文本

这是 `resource-task-list` 之前的强制步骤。

## 目标

前端分析层的目标是输出一份“前端组件说明书”，让后续的：

- `product`
- `frontend`
- `art`
- `export`
- `review`

都基于同一份组件理解继续工作。

如果这一层缺失，后续很容易出现：

- 把一个组件误识别成一张图
- 把一个按钮误切成多个重复资源
- 把本应用 CSS 的结构烘焙进图片
- 把文字、气泡、徽标和主体按钮混成一个资源

## 标准产物

建议把这层拆成“分析层 + 策略层”两部分：

1. `analysis/component-analysis.md`
2. `analysis/component-analysis.json`
3. `strategies/strategy-decision.frontend_web.json`

含义如下：

- `component-analysis.md`
  面向人阅读的前端分析说明书
- `component-analysis.json`
  面向工具和 subagent 的结构化组件分析
- `strategy-decision.frontend_web.json`
  明确回答在 `frontend_web` 这个策略 profile 下，“切图 / CSS / 文本 / SVG”应如何选择

## 前端分析层在工作流中的位置

正确顺序应是：

```text
整页截图 / 预览
-> 页面理解
-> 模块树
-> 组件分析
-> 策略层决策
-> 资源规划
-> 资源任务单
-> 并发切图
-> 复核交付
```

禁止顺序：

```text
整页截图 / 预览
-> 资源候选
-> 直接切图
```

## `component-analysis.md` 应包含什么

建议至少包含以下章节：

1. 页面定位
2. 模块拆解
3. 组件拆解
4. 状态建模
5. 文本策略
6. 实现建议
7. 风险和疑点

### 示例结构

```text
# 前端分析

## 页面定位
- 页面类型：游戏大厅
- 页面状态：默认态、聊天展开态、筛选展开态

## 模块拆解
- 顶部栏
- 跑马灯
- 轮播区
- 游戏卡片区
- 浮动入口区
- 底部导航栏

## 组件拆解
- 底部导航栏
  - 导航项：公告
  - 导航项：支援金
  - 导航项：商城（选中态）
  - 导航项：赠礼
  - 导航项：邮箱
- 浮动聊天入口
  - 按钮主体
  - 未读气泡
  - 未读数量文本
```

## `component-analysis.json` 推荐结构

推荐结构如下：

```json
{
  "page_id": "lobby_home",
  "page_type": "game_lobby",
  "page_states": [
    "default",
    "chat_open",
    "filter_open"
  ],
  "modules": [
    {
      "module_id": "floating_actions",
      "module_type": "floating_action_stack",
      "purpose": "quick entry and communication",
      "components": [
        {
          "component_id": "chat_entry",
          "component_type": "floating_chat_entry",
          "subparts": [
            "chat_button_base",
            "unread_badge",
            "unread_count_text"
          ],
          "states": [
            "default",
            "has_unread"
          ]
        }
      ]
    }
  ]
}
```

## `strategy-decision.frontend_web.json` 推荐结构

这份文件专门回答：

- 哪些部分必须导出图片
- 哪些部分优先走 CSS
- 哪些部分应保留为文本
- 哪些部分应优先走 SVG/矢量

推荐结构如下：

```json
{
  "component_id": "chat_entry",
  "component_type": "floating_chat_entry",
  "implementation": [
    {
      "part_id": "chat_button_base",
      "preferred_mode": "image",
      "reason": "主体图标和装饰效果不可稳定用 CSS 还原"
    },
    {
      "part_id": "unread_badge",
      "preferred_mode": "css",
      "reason": "圆角气泡和底色可稳定用 CSS 构建"
    },
    {
      "part_id": "unread_count_text",
      "preferred_mode": "text",
      "reason": "数字应保持可编辑"
    }
  ]
}
```

## 推荐决策枚举

`preferred_mode` 建议先统一成以下几类：

- `image`
- `css`
- `text`
- `svg`
- `mixed`
- `undecided`

## 前端分析必须回答的 6 个问题

在进入资源任务单前，前端分析必须明确回答：

1. 这是一个页面、一个模块，还是一个组件
2. 这个组件有哪些前端子部件
3. 这个组件有哪些状态
4. 哪些子部件可以跨实例复用
5. 哪些文字应保留为文本
6. 哪些子部件应该切图，哪些应由 CSS 或 SVG 实现

只要有一项回答不清楚，就不应进入最终切图阶段。

## 两个关键例子

### `floating_chat_button`

错误理解：

- 一张独立图片资源

正确理解：

- 一个浮动聊天入口组件

建议拆解：

- `chat_button_base`
- `unread_badge`
- `unread_count_text`

建议实现：

- `chat_button_base`：`image`
- `unread_badge`：`css`
- `unread_count_text`：`text`

### `chat_panel_bubble`

错误理解：

- 直接切成一张整图

正确理解：

- 一个聊天气泡类组件或聊天面板入口容器

建议拆解：

- `bubble_background`
- `icon`
- `text_slot`
- `badge_slot`

建议实现：

- `bubble_background`：优先 `css`
- `icon`：`image` 或 `svg`
- `text_slot`：`text`
- `badge_slot`：优先 `css`

## 与资源策略的关系

前端分析层负责给资源策略“降维”。

资源层后续再根据这些结果决定是否进入：

1. `export_ready_single_layer`
2. `explicit_layer_combo`
3. `hide_background_then_render`
4. `psd_difference_isolation`
5. `visual_matting_fallback`

## 一句话原则

截图分析不应直接产出“切图列表”。

截图分析应先产出：

`前端可实现的组件说明书 + 实现决策`
