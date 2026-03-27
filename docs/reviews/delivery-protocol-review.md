# 交付协议与输出结构审阅

## 结论
1. `assets / config / docs` 这个三分法方向是对的，但当前协议层次不够清晰。
2. 去重之后，当前 metadata 只能勉强写出来，还不能稳定表达“多个组件复用同一张图片”。
3. 现在的 `manifest / component-tree / page-analysis` 更像调试产物，不是前端团队和美术团队可长期协作的交付协议。

## 现状问题
1. 当前 `manifest` 把“组件实例”和“物理图片资源”混在了一张表里。
   在
   [Exporter.export](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level5-export/exporter.py#L148)
   里，`Exporter.export()` 逐个组件创建 metadata；
   在
   [MetadataAttacher.generate_manifest](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level5-export/metadata_attacher.py#L189)
   里，又直接把这些 metadata 当成 `assets` 输出。

   结果是：`manifest.json` 里的每一项其实是“组件导出记录”，不是“唯一资源”。一旦两行 switch 复用同一张 PNG，`manifest` 里还是两项，但物理资源只有一份。

2. 去重后，metadata 的读写协议不自洽。
   [MetadataAttacher._metadata_path_for](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level5-export/metadata_attacher.py#L81)
   现在支持 `metadata_key`，写入时在
   [MetadataAttacher.attach](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level5-export/metadata_attacher.py#L89)
   里会写成 `asset_3.meta.json` 这种组件级 sidecar；
   但读取时在
   [MetadataAttacher.extract](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level5-export/metadata_attacher.py#L149)
   仍然默认按图片文件名找 sidecar。

   这意味着：写是“按组件键”，读还是“按图片键”，协议已经分叉了。

3. `asset_id`、sidecar 文件名、真实图片文件名不是同一个身份体系。
   [MetadataAttacher.create_metadata](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level5-export/metadata_attacher.py#L247)
   里 `asset_id` 还是随机 UUID；
   [Exporter.export](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level5-export/exporter.py#L148)
   导出图片时用的是 `asset_{i}`；
   sidecar 文件名现在又基于 `metadata_key=export_result.asset_id`。

   同一个对象现在至少有 3 套 ID。单次导出里能凑合，但跨批次、回归对比、人工审阅时会很乱。

4. 图片文件名不是稳定资源名，无法作为长期交付物。
   [Exporter.export](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level5-export/exporter.py#L148)
   虽然拿到了 `naming.generated_name`，但物理图片还是用 `asset_{i}` 导出，最终资源名没有承载语义。

5. `component-tree` 和 `page-analysis` 还不是前端 / 美术可直接消费的协议。
   [ _build_component_tree ](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level9-integration/pipeline.py#L1185)
   和
   [ _build_page_analysis_markdown ](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level9-integration/pipeline.py#L1227)
   的输出里仍然混着大量内部分析字段，比如 `layer_roles`、`export_decision`、`frontend_hints`。

   这些字段对调试有价值，但对协作来说缺少更关键的东西：
   - 这个组件最终引用哪些资源
   - 哪些文字由前端渲染
   - 哪些背景图是共享资源
   - 哪些组件只是页面实例，不是资源定义

6. `docs` 和 `config` 的边界还没定死。
   现在
   [ _write_analysis_outputs ](/C:/Users/lushengtao/Desktop/新建文件夹/psd-smart-cut/skills/psd-parser/level9-integration/pipeline.py#L1269)
   产出的 `page-analysis / page-tree / component-tree` 同时承担“人工审阅文档”和“半结构化协议”两种角色。

## 风险
- 前端无法稳定建立资源引用表，因为 `manifest` 没有独立资源层。
- 美术无法清楚知道哪些图片是共享母版，哪些只是页面内单次实例。
- 一旦继续增强去重，当前 sidecar 方案会越来越脆，因为图片与组件已经不是 `1:1`。
- 后续做 diff、增量导出、版本回归会很痛苦，因为 ID 和文件名不稳定。

## 更合理的目标协议
建议把交付拆成 4 层，不要再让一个 `manifest.json` 同时承担所有职责。

### 1. resources
物理资源库，只描述真实文件。

建议结构：
- `resources/png/<resource_key>.png`
- `resources/png/index.json`

`resource` 记录建议最少包含：
- `resource_id`
- `resource_key`
- `path`
- `hash`
- `dimensions`
- `format`
- `source_layers`
- `usage_count`

### 2. components
组件定义层，描述“一个组件由什么构成”。

建议结构：
- `components/<component_key>.json`

`component` 记录建议包含：
- `component_id`
- `component_key`
- `component_type`
- `bounds`
- `resource_refs`
- `text_specs`
- `subparts`
- `states`
- `frontend_hints`

例如 switch 应该是：
- `label_text`
- `state_text`
- `switch_control_resource`
- `state=on / off`

### 3. pages
页面实例层，描述“页面上放了哪些组件实例”。

建议结构：
- `pages/<page_key>.json`

`page` 记录建议包含：
- `page_id`
- `page_type`
- `regions`
- `component_instances`
- 每个实例引用哪个 `component_key`
- 实例在页面上的位置和顺序

### 4. analysis
纯人工阅读产物，不参与协议消费。

建议结构：
- `analysis/page-preview.png`
- `analysis/page-analysis.md`
- `analysis/page-tree.md`
- `analysis/component-tree.md`

## 目标目录草案
```text
output/
├─ resources/
│  └─ png/
│     ├─ button_primary_pink.png
│     ├─ switch_control_on.png
│     ├─ switch_control_off.png
│     └─ index.json
├─ components/
│  ├─ button_join_desktop.json
│  ├─ toggle_background_music.json
│  ├─ tab_install_guide.json
│  └─ banner_download_app.json
├─ pages/
│  └─ settings_with_install_guides.json
└─ analysis/
   ├─ page-preview.png
   ├─ page-analysis.md
   ├─ page-tree.md
   └─ component-tree.md
```

## 协议关键原则
- `resources` 只描述唯一物理图片。
- `components` 描述可交付组件，不直接等于图片。
- `pages` 描述页面实例与区域树。
- `analysis` 只给人看，不给程序当主协议。
- 去重后，多个组件可以引用同一个 `resource_id`，但每个组件仍有自己的 JSON。

## 当前仓库最值得优先调整的点
1. 先把 `manifest` 拆成 `resources index` 和 `component records` 两层。
2. 让 `asset_id / resource_id / component_id` 各司其职，不再混用。
3. 让图片文件名从 `asset_{i}` 变成稳定 `resource_key`。
4. 让 `page-analysis` 从协议里降级为辅助文档，把 `pages/*.json` 提升为正式页面协议。

## 一句话建议
先定“目标协议”，再改实现。当前最大问题不是再补几个 heuristic，而是交付对象的模型还没彻底分层。
