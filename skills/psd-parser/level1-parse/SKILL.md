# Level 1 - PSD 解析层

**版本：** v0.1  
**层级：** Level 1  
**职责：** 解析 PSD 文件，提取 Page 和 Layer 信息  

---

## 🎯 技能列表

| 技能 | 文件 | 职责 |
|------|------|------|
| psd_parser | psd_parser.py | PSD 文件核心解析 |
| page_extractor | page_extractor.py | 提取 Page 信息 |
| layer_reader | layer_reader.py | 读取 Layer 信息 |

---

## 📦 模块结构

```
level1-parse/
├── __init__.py
├── psd_parser.py       # 核心解析器
├── page_extractor.py   # Page 提取器
│   ├── PageLister      # Page 列表
│   ├── PageSelector    # Page 选择
│   └── PageExporter    # Page 导出
├── layer_reader.py     # Layer 读取器
│   ├── LayerLister     # Layer 列表
│   ├── LayerFilter     # Layer 过滤
│   └── LayerMetadata   # Layer 元数据
└── SKILL.md           # 本文件
```

---

## 🔧 使用方法

### 基本用法

```python
from skills.psd_parser.level1_parse import parse_psd

# 解析 PSD
document = parse_psd("path/to/file.psd")

# 获取 Page
page = document.get_page(0)

# 获取所有 Layer
layers = document.get_all_layers()
```

### Page Extractor

```python
from skills.psd_parser.level1_parse.page_extractor import PageExtractor

extractor = PageExtractor("path/to/file.psd")
result = extractor.extract()  # 提取所有 Page
result = extractor.extract(page_index=0)  # 提取指定 Page

# 列出所有 Page
pages = extractor.list_pages()

# 获取 Page 摘要
summary = extractor.get_page_summary()
```

### Layer Reader

```python
from skills.psd_parser.level1_parse.layer_reader import LayerReader, LayerFilter

reader = LayerReader("path/to/file.psd", page_index=0)

# 读取所有 Layer
result = reader.read()

# 读取可见 Layer
result = reader.read(filter_type=LayerFilter.VISIBLE)

# 读取图片 Layer
result = reader.read(filter_type=LayerFilter.IMAGES)

# 获取 Layer 树
tree = reader.get_layer_tree()
```

---

## 📤 输出格式

### PageInfo

```json
{
  "index": 0,
  "name": "Page 1",
  "width": 1920,
  "height": 1080,
  "layer_count": 25,
  "hidden_count": 3,
  "locked_count": 1,
  "layers": [...]
}
```

### LayerInfo

```json
{
  "id": "layer_0",
  "name": "Background",
  "kind": "image",
  "visible": true,
  "locked": false,
  "left": 0,
  "top": 0,
  "right": 1920,
  "bottom": 1080,
  "width": 1920,
  "height": 1080,
  "opacity": 1.0,
  "blend_mode": "normal",
  "bbox": {"x": 0, "y": 0, "width": 1920, "height": 1080},
  "parent_id": null,
  "children": []
}
```

---

## 🔗 依赖

| 依赖 | 版本 | 说明 |
|------|------|------|
| psd-tools | >= 2.0 | PSD 文件解析 |
| pillow | >= 8.0 | 图片处理 |

---

## ➡️ 下一层

Level 1 输出 → [Level 2: 分类层](../level2-classify/)
