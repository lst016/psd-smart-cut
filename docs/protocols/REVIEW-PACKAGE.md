# V2 审阅包协议（Review Package）

本文定义 `PSD Smart Cut V2` 的最终审阅包结构。

审阅包不是简单的“导出结果目录”，而是一份能够让产品、前端、美术和评审共同检查的交付包。

## 目标

审阅包必须能回答：

1. 这页被理解成了什么
2. 拆成了哪些模块和组件
3. 最终复用了哪些资源
4. 哪些资源被导出了
5. 是否存在过切、漏切、重复切

## 目录结构

V2 推荐结构如下：

```text
output/
|- analysis/
|- pages/
|- components/
`- resources/
```

### `analysis/`

给人看，用于审阅与对齐。

建议包含：

- `page-preview.png`
- `page-analysis.md`
- `module-tree.md`
- `component-tree.md`
- `handoffs/`
- `review-summary.md`

### `pages/`

页面与模块实例定义。

建议每个页面一个文件：

```text
pages/
|- settings_modal.json
|- guide_android.json
`- guide_ios.json
```

页面层是整个交付包的主入口。

### `components/`

组件定义文件。

建议一个组件定义一个文件：

```text
components/
|- modal.json
|- ad_banner.json
|- toggle_row.json
|- switch_control.json
|- action_button.json
`- tab_control.json
```

### `resources/`

唯一物理资源层。

推荐结构：

```text
resources/
|- png/
|  |- index.json
|  |- button_normal.png
|  |- button_selected.png
|  |- switch_track_active.png
|  |- switch_track_inactive.png
|  `- switch_thumb.png
`- webp/
   `- index.json
```

## 四层的职责边界

### `analysis`

职责：

- 解释页面理解过程
- 解释模块树和组件树
- 保留 handoff 和 review 记录

不负责：

- 作为正式运行时协议入口

### `pages`

职责：

- 记录页面实例
- 记录页面内有哪些区域和组件实例
- 作为主入口供前端或后续工具读取

不负责：

- 直接存图片二进制

### `components`

职责：

- 定义组件结构
- 定义状态
- 定义文本槽位
- 定义组件和资源的引用关系

不负责：

- 绑定具体页面业务位置

### `resources`

职责：

- 存放唯一物理资源
- 提供稳定资源 id、文件名、hash 和尺寸
- 支持复用审计

不负责：

- 表达页面语义

## 必备文件

至少应包含：

1. `analysis/page-preview.png`
2. `analysis/page-analysis.md`
3. `analysis/review-summary.md`
4. `pages/*.json`
5. `components/*.json`
6. `resources/<format>/index.json`

缺任何一层，都不能算完整交付。

## `review-summary.md` 必须回答什么

最终审阅摘要必须明确回答：

1. 识别了几个业务模块
2. 哪些页面是子页面
3. 共定义了多少组件
4. 共导出了多少唯一资源
5. 哪些实例实现了资源复用
6. 哪些文字保留为文本
7. 哪些内容因特殊样式被烘焙为图片
8. 是否存在疑似重复导出
9. 是否存在漏切

## 资源复用审计

审阅包必须支持复用检查。

最少要有：

- 每个资源的 `resource_id`
- `hash`
- `usage_count`
- `used_by_components`
- `used_by_pages`

这样 review agent 才能判断：

- 是否 6 个按钮重复导出了 6 张图
- 是否 switch 的 on/off/thumb 已被抽为共享资源
- 是否多个 tab 只是状态实例，而不是多份重复位图

## 对当前样例稿的期望

以当前的“设置弹窗 + 加入桌面教学”样例为例，审阅包应更接近：

### 页面层

- `settings_modal`
- `guide_android`
- `guide_ios`

### 组件层

- `modal`
- `ad_banner`
- `download_button`
- `settings_form`
- `toggle_row`
- `switch_control`
- `divider`
- `action_button`
- `tab_control`
- `guide_content_frame`

### 资源层

- `modal_background`
- `close_icon`
- `banner_artwork`
- `button_normal`
- `button_selected`
- `switch_track_active`
- `switch_track_inactive`
- `switch_thumb`
- `divider_line`
- `tab_active`
- `tab_inactive`
- `guide_content_background`

## 失败判定

如果出现以下任一情况，审阅包应标记为不通过：

1. 页面层缺失，只剩图片
2. 组件层缺失，只剩实例化散图
3. 资源层没有去重信息
4. 大量相同按钮或 switch 被重复导出
5. 无法解释某个资源为什么存在
6. 文字被大面积错误烘焙成图片

## 推荐审阅顺序

建议按以下顺序查看：

1. `analysis/page-preview.png`
2. `analysis/page-analysis.md`
3. `analysis/module-tree.md`
4. `components/`
5. `pages/`
6. `resources/<format>/index.json`
7. `analysis/review-summary.md`

## 与其他协议的关系

- 任务入口由 [V2 任务协议](./JOB-SPEC.md) 定义
- 角色交接由 [Agent 交接协议](./AGENT-HANDOFF.md) 定义
- 子 agent 的行为约束由 [Subagent 强制行为准则](./SUBAGENT-RULES.md) 定义
