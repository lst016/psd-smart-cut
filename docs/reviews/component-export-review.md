# 组件拆解与导出策略审阅

## 结论
当前这套组件拆解不是“组件优先”，而是“图层候选优先 + 区域补丁兜底”。

所以它会稳定地产生 3 类错误：
- 把 `switch` 这种组合控件拆成一个小图和几段文字，而不是一个有内部部件关系的组件。
- 页面级容器和结构块大量缺失，因为候选规则只吃“看起来像按钮 / tab / banner 的小组”。
- `region_background / content_block` 只是后补的面积阈值规则，不是真正的页面结构理解，所以粒度和交付价值都不稳定。

## Findings
1. `switch` 行拆错的根因是识别条件和导出粒度都错了。
   在
   [ _guess_group_component_type ](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level9-integration/pipeline.py#L309)
   里，只要“有 1 个子 group + 至少 1 个文本 + 子 group 名字以 `btn` 开头”，就直接判成 `toggle_row`。这不是组件识别，只是命中了一个命名模式。

   在
   [ _build_group_component ](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level9-integration/pipeline.py#L346)
   里，`toggle_row` 的 `export_layer_ids` 又只取 `nested_component`，也就是只导出开关那一小组，文本和整行布局都退化成 metadata。

   结果：它不是“switch 行组件”，而是“switch 小图 + 两段文字”。这不符合前端 / 美术交付。

2. 页面只拆出很少可用组件，是因为候选构建阶段天然忽略了容器层和页面结构层。
   在
   [ _build_component_candidates ](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level9-integration/pipeline.py#L743)
   里，第一阶段只扫 group / leaf，并且一旦祖先 group 被选中，后续子层很多就不再进入候选。

   同时
   [ _guess_group_component_type ](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level9-integration/pipeline.py#L309)
   对 group 的判定非常窄：基本只会稳定命中 `tab_control`、`banner`、`button`、`toggle_row`。

   像设置页里的 `内容`、`按钮` 容器，教学页里的“标题区 / 说明文字块 / 预览框 / 底部说明框”，都不是这套规则的主目标，所以自然拆不出来。

3. `region_background` 现在仍然不符合交付需求，因为它本质上是在导出“整块画板背景复合图”，不是“可复用背景资源”。
   在
   [ _build_region_background_component ](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level9-integration/pipeline.py#L570)
   里，规则是“顶层 direct child、和 artboard 大范围重叠、面积够大，或者名字叫 `BG / top`”。

   它的 `render_bbox` 直接就是整个 `region_bbox`。这会让产物偏向“整页底板图”，而不是前端可组合的页头背景、面板背景、内容框背景。

4. `content_block` 现在也不符合交付需求，因为它只是“大矩形检测器”，没有语义。
   在
   [ _build_large_block_components ](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level9-integration/pipeline.py#L648)
   里，`content_block` 完全由 `overlap / area / size` 阈值驱动。

   这能抓到教学页里的大框，但它不知道这块是“截图框”、“说明框”、“占位区域”还是“底部卡片”。
   所以它只能输出 `content_block_1 / 2` 这种技术名，不能给前端或美术稳定的交付语义。

5. 导出器的模型本身也限制了组件策略。
   在
   [Exporter.export](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level5-export/exporter.py#L148)
   里，当前是“一个 component -> 一次 `asset_exporter.export()` -> 一张图”。

   这直接锁死了粒度：
   - 一个 `toggle_row` 不能同时产出“row config + switch skin asset”
   - 一个 `button` 不能自然产出“button background asset + text config”
   - 一个教学页结构块也不能拆成多个命名明确的资源

   这不是实现细节问题，是导出模型本身过于单一。

## 建议
1. 把模型拆成 3 层，而不是继续往 `component` 里塞字段。
   建议目标结构：
   - `RegionNode`
   - `UIComponent`
   - `ResourceAsset`

2. `switch` 应该改成“组件配置优先，资产次之”。
   更合理的粒度：
   - `toggle_row`
   - 子节点：`label_text`、`state_text`、`toggle_control`
   - 真正导出的图：`toggle_control_on` / `toggle_control_off`
   - 不要把整行当一张 PNG，也不要只剩一个无上下文的小开关图

3. 教学页不要只出 `region_background + content_block`。
   更合理的层级建议：
   - `guide_page`
   - `guide_header`
   - `tab_control`
   - `instruction_text_block`
   - `preview_frame_top`
   - `preview_frame_bottom`
   - `page_background` 可选，且通常不应作为默认导出资产

4. 组件识别应该先做区域模板，再往下拆。
   当前是先扫小 group，再补区域。建议反过来：
   - 先识别 `settings_panel / ios_guide / android_guide`
   - 再在每个 region 内按模板拆
   - 最后再抽取资源资产

   这样才是“视觉 / 页面优先，PSD 结构为辅”。

5. 产物协议要从“资产清单”改成“组件清单 + 资源清单”。
   建议目标：
   - `components.json`：组件树、边界、文本、状态、资源引用
   - `assets.json` 或 manifest 中单列 `assets`
   - 组件引用资源，而不是组件本身等于资源

## 一句话建议
下一步不要再调阈值，而是先重构目标数据模型：先把 `toggle_row` 和 `guide_page` 这两类组件的目标协议定死，再回头改提取逻辑。
