# V2 大厅稿迭代复盘

本文复盘“游戏大厅”真实 PSD 的这轮试运行，重点说明：

- 哪些方向是对的
- 哪些问题让当前结果还不能进入生产
- 为什么我们在底部栏资源上绕了远路
- 下一轮应该如何收敛

## 本轮目标

本轮原始目标是：

1. 用 V2 工作流跑通新的真实 PSD
2. 理解大厅主页面和多个状态页之间的关系
3. 导出共享资源、卡片资源和底部栏资源
4. 验证复杂 UI 资源的真实导出策略

## 本轮已产出

已经落下的核心产物包括：

1. `output/v2-trial-lobby/analysis/page-analysis.md`
2. `output/v2-trial-lobby/analysis/module-tree.md`
3. `output/v2-trial-lobby/analysis/component-plan.md`
4. `output/v2-trial-lobby/analysis/resource-task-list.json`
5. `output/v2-trial-lobby/resources/png/index.json`
6. `examples/experiments/v2_export_lobby_resources.py`

## 本轮做对的部分

### 1. 页面理解方向是对的

这份 PSD 不应被理解成多个彼此无关的页面，而应理解为：

- 1 个大厅主页面
- 多个交互状态

这个判断符合产品和前端视角。

### 2. 先任务单、后切图的流程是对的

本轮不是先盲目切图，而是先产出：

- `resource-task-list`
- `export-work-queue`
- `review summary`

这说明任务单机制是有价值的，后面必须保留。

### 3. 共享资源优先的方向是对的

这轮已经抽出了不少高复用资源，例如：

- 顶部信息栏
- Banner
- Tab
- 收藏角标
- 悬浮按钮
- 底部栏背景和激活底座

这符合 `reuse-first` 原则。

## 本轮暴露出的关键问题

### 1. 当前产物仍未达到生产可用

问题不只是“个别图不完美”，而是资源策略还不稳定：

- 同一类资源没有统一导出策略
- 某些资源被切成了错误粒度
- 某些资源带入了不该出现的背景
- 某些资源其实能直接导出，却被我们做复杂了

### 2. 底部栏是本轮最典型的反例

底部栏这组资源暴露出一个很重要的问题：

我们把一批本来应该先“做单层直出探测”的资源，过早推进成了复杂策略试验。

实际验证后可以明确得出：

- `icon_donation` 这层本身就是可直接导出的标准层
- 手工在 PSD 工具里右键导出是正确的
- `topil()` 和 `composite()` 也都能正常得到标准结果

这说明问题不在 PSD，也不在这层本身，而在我们：

- 选错了策略
- 过早升级到了复杂导出路径

### 3. 不是所有底部栏资源都属于“复杂嵌套资源”

本轮最大的误判之一是：

把整个底部栏统一当成“复杂上下文资源”处理。

实际上底部栏资源应拆成不同类别：

1. 可直接导出的单层资源  
例如：
- `icon_donation`
- `公告 (1)`
- `邮箱 (1)`
- `标签栏_福利`

2. 明确的多层组合资源  
例如：
- `商城` 图标组合

3. 状态或栏目级资源  
例如：
- `bottom_nav_active_bg`
- `商城选中栏目项`

## 这轮最重要的新结论

### 1. 先做“单层直出探测”，再决定是否升级策略

这是本轮最关键的新结论。

以后一个资源进入导出前，必须先回答：

1. 它是否已经是一个可直接导出的单层或单组
2. 如果是，就先走单层直出
3. 只有直出失败，或者语义上本来就不是单层资源，才允许升级到更复杂策略

这条规则比继续补更多后处理策略更重要。

### 2. 复杂策略不是默认路径

像这些策略：

- `hide_background_then_render`
- `PSD 差分隔离`
- `视觉抠图 fallback`

不应该作为默认入口。

它们应该只服务于以下场景：

- 明确的多层组合资源
- 需要上下文但不能带背景的状态资源
- 通用单层直出无法满足需求的资源

### 3. 正确的策略顺序应该是

建议后续正式固化为：

1. `export_ready_single_layer`
2. `explicit_layer_combo`
3. `hide_background_then_render`
4. `psd_difference_isolation`
5. `visual_matting_fallback`

这条顺序意味着：

- 先尝试最简单、最接近人工右键导出的方式
- 再升级到更重的策略

## 根因分析

### 1. 资源类型分流还不够细

我们虽然已经开始做资源分类，但还不够明确地区分：

- 本身可直接导出的层
- 明确的层组合
- 需要上下文的状态资源
- 需要白名单治理的复杂资源

### 2. 缺少“策略升级门槛”

当前系统还没有正式写死：

- 什么情况下必须先直出
- 什么情况下才允许升级到隐藏背景
- 什么情况下才允许进入差分或 fallback

### 3. 底部栏资源被错误地统一处理

底部栏本应按资源逐个选策略，但我们一度把它整组推进到同一条复杂链里，结果把简单问题做复杂了。

## 下一轮必须补的优化

### 1. 正式引入“单层直出探测”

每个资源进入复杂策略前，都要先做：

- `topil()` 探测
- `composite()` 探测
- 输出尺寸和可见性判断

如果通过，就直接作为：

- `export_ready_single_layer`

### 2. 正式固化资源策略优先级

下一轮必须把下面这条顺序写入工具链：

1. `export_ready_single_layer`
2. `explicit_layer_combo`
3. `hide_background_then_render`
4. `psd_difference_isolation`
5. `visual_matting_fallback`

### 3. 白名单应同时标记资源类型和策略

以后白名单不只写 `resource_key`，还要写：

- `resource_type`
- `preferred_strategy`
- `fallback_strategy`
- `review_focus`

例如：

- `bottom_nav_donation_icon -> export_ready_single_layer`
- `bottom_nav_mall_icon -> explicit_layer_combo`
- `bottom_nav_active_bg -> export_ready_single_layer`

## 本轮结论

这轮不能视为“生产可用版本”，但它是一次有效的工程收敛。

本轮最有价值的不是当前产物，而是明确了：

1. 页面理解主线是对的
2. 任务单驱动流程是对的
3. 复杂策略不该成为默认导出路径
4. 底部栏这类资源必须先做“单层直出探测”
5. 下一轮要正式转入“资源类型分流 + 策略升级门槛 + 白名单精修”
## 本轮新增修正

在这一轮后续精修里，我们又确认了一个更细的导出事实：

1. `icon_donation` 这类资源之所以能直接导出正确结果，不只是因为它是单层，还因为它本身的图层效果已经足够描述最终视觉。
2. `公告 / 福利 / 邮箱` 这类资源此前导出错误，根因不是缓存，也不是必须进入复杂抠图，而是：
   - `公告` 选错了隐藏层，正确层应优先选可见副本。
   - `福利 / 邮箱 / 公告` 这些标准层带有 `GradientOverlay`，如果忽略图层效果，就会导成偏黑的原始图。
3. 因此，`export_ready_single_layer` 的定义需要升级为：
   - 先做单层直出探测。
   - 再做图层效果感知导出。
   - 只有这两步都不能满足，才允许升级到更复杂策略。

这条结论会直接影响后续策略顺序：

`export_ready_single_layer(effect-aware) -> explicit_layer_combo -> hide_background_then_render -> psd_difference_isolation -> visual_matting_fallback`
