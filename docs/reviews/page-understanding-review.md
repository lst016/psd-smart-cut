# 页面理解链审阅

## 结论
当前这条链本质上仍是“PSD 结构驱动，视觉只负责出预览图”。页面理解主要靠图层树、命名、文本关键字、面积阈值和 artboard 编号规则，不是靠页面截图本身做区域理解。

## 当前页面理解依赖的函数和启发式
执行链在 [pipeline.py](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level9-integration/pipeline.py)。

- 入口链路：
  [run_full_pipeline](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level9-integration/pipeline.py#L1426)
  `parse_psd -> _flatten_layers -> LayerClassifier.classify_batch -> _merge_layer_context -> _build_psd_layer_records -> _build_component_candidates -> Strategy.create_plan -> _write_analysis_outputs -> Exporter.export`

- PSD 结构来源：
  [parse_psd](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level1-parse/psd_parser.py#L346)
  [PSDParser._build_document](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level1-parse/psd_parser.py#L208)
  [PSDParser._get_layer_kind](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level1-parse/psd_parser.py#L298)
  这里把 PSD 统一建成单 page 文档，再递归扁平化图层；类型判断只有 `group / image / text / vector / unknown`。

- 页面理解实际依赖的启发式：
  [ _build_psd_layer_records ](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level9-integration/pipeline.py#L144)
  把 psd-tools 树转成 `id / parent_id / name / kind / text / bbox` 记录表。

  [ _guess_group_component_type ](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level9-integration/pipeline.py#L309)
  用名字 hint、文本子层数量、group 子层数量来猜 `button / tab_control / toggle_row / banner / panel`。

  [ _classify_child_role ](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level9-integration/pipeline.py#L214)
  用 `kind + 面积占比` 分背景、文本、图标、装饰。

  [ _build_component_candidates ](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level9-integration/pipeline.py#L743)
  先挑 group 组件，再补 leaf，再拼 synthetic `region_background / content_block`。这里还有硬编码 artboard 名字数字：
  `9 -> settings_panel`
  `10 -> ios_install_guide`
  `11 -> android_install_guide`

  [ _derive_region_purpose ](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level9-integration/pipeline.py#L963)
  用文本关键词和组件类型判定区域用途，例如 `toggle_row / button / 设置` => `settings_panel`，`safari / chrome / tab_control` => iOS / Android guide。

  [ _build_page_summary ](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level9-integration/pipeline.py#L1064)
  用 region 数量和位置推断 `horizontal_triptych`、`settings_with_install_guides` 等页面结论。

## 为什么它还不是视觉优先、PSD 结构为辅
- 页面预览没有参与决策，只参与文档输出。
  [ _write_analysis_outputs ](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level9-integration/pipeline.py#L1269)
  里先拿已经算好的 `components / regions` 生成文档，然后才用
  [ _render_page_preview ](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level9-integration/pipeline.py#L1257)
  存一张 `page-preview.png`。预览图没有反向影响 `region / component` 决策。

- recognizer 也没有走截图分析链。
  [run_full_pipeline](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level9-integration/pipeline.py#L1454)
  里即使开启 recognizer，也是 `use_screenshot=False`、`capture_screenshots=False`。这意味着不是“先看图再理解”。

- 区域与组件判断严重依赖命名和文本。
  例如 `btn / tab / banner / BG / top`、`设置 / safari / chrome / iOS / Android` 这些命中条件，是典型规则库，不是视觉分区。

- Level 1 的文档模型本身就是“单页扁平图层”。
  [PSDParser._build_document](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level1-parse/psd_parser.py#L208)
  明确把 PSD 当成一个默认 page，后面的 `page / region` 语义只能在 integration 层硬推。

## 顶层最该改的 3 个切入点
1. 在 `run_full_pipeline` 前半段引入真正的视觉分区阶段。
   位置：
   [run_full_pipeline](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level9-integration/pipeline.py#L1426)
   前半段。
   目标：先基于整页预览图做 `page segmentation`，产出 `RegionProposal[]`，再用 PSD 结构去对齐图层，而不是先从图层拼组件再反推页面。

2. 重建 Level 1 文档模型，显式区分 `artboard / page / region / layer`。
   位置：
   [PSDParser._build_document](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level1-parse/psd_parser.py#L208)
   和
   [PSDParser._get_layer_kind](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level1-parse/psd_parser.py#L298)。
   目标：不要再把所有东西扁平成一个 page。真实 artboard 应该成为一等公民，否则上层永远要靠名字和坐标猜。

3. 把“组件识别”和“导出资产规划”拆成两个独立模型。
   位置：
   [ _build_component_candidates ](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level9-integration/pipeline.py#L743)
   和
   [ _write_analysis_outputs ](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level9-integration/pipeline.py#L1269)。
   现状：这里同时在做 `region` 推断、`component` 推断、synthetic 背景块拼装、导出候选生成。
   目标：先得到稳定的 `PageModel -> RegionModel -> ComponentModel`，再单独生成 `AssetPlan`。否则 `region_background / content_block` 这种产物会一直是规则拼出来的折中物。

## 一句话判断
现在的核心问题不是规则不够多，而是执行顺序错了：它先从 PSD 结构找可导出对象，再拿这些对象去解释页面。方向应该反过来。
