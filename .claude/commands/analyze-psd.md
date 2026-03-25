# 分析 PSD 文件

> 分析指定的 PSD 文件，输出图层结构、分类统计和组件信息。

## 使用方法

```
/analyze-psd <psd_file> [--page <page_index>] [--verbose]
```

## 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `psd_file` | string | ✅ | PSD 文件路径 |
| `--page` | integer | ❌ | 页面索引（默认 0） |
| `--verbose` | flag | ❌ | 详细输出模式 |

## 示例

```
/analyze-psd designs/hero.psd
/analyze-psd designs/hero.psd --page 0 --verbose
```

## 执行流程

### Step 1: PSD 解析（Level 1）

```python
from skills.psd_parser.level1_parse import parse_psd, extract_pages, read_layers

# 解析 PSD 文件
document = parse_psd(psd_file)
print(f"📄 文档: {document.name}")
print(f"📐 画布: {document.width}x{document.height}px")

# 提取页面
pages = extract_pages(psd_file)
print(f"📑 页面数: {len(pages)}")

# 读取图层
layers = read_layers(psd_file, page_index=page_index)
print(f"📊 图层数: {len(layers)}")
```

### Step 2: 图层分类（Level 2）

```python
from skills.psd_parser.level2_classify import LayerClassifier

classifier = LayerClassifier()
classified = classifier.classify(layers)

print("\n🎨 图层分类统计:")
for layer_type, type_layers in classified.items():
    print(f"  {layer_type}: {len(type_layers)} 个")
```

### Step 3: 组件识别（Level 3）

```python
from skills.psd_parser.level3_recognize import Recognizer

recognizer = Recognizer()
components = recognizer.recognize(
    layers,
    screenshots_dir="temp_screenshots/",
    use_ai=False  # 快速模式，不调用 AI
)

print(f"\n🔍 识别到 {len(components)} 个组件:")
for comp in components:
    print(f"  - {comp.name} ({comp.component_type})")
```

### Step 4: 生成分析报告

```python
# 输出结构化报告
report = {
    "file": psd_file,
    "canvas": {
        "width": document.width,
        "height": document.height
    },
    "pages": len(pages),
    "layers": len(layers),
    "classification": {
        layer_type: len(type_layers) 
        for layer_type, type_layers in classified.items()
    },
    "components": len(components),
    "component_types": list(set(c.component_type for c in components))
}

import json
print("\n📋 分析报告:")
print(json.dumps(report, indent=2, ensure_ascii=False))
```

## 输出示例

```
📄 文档: hero.psd
📐 画布: 1920x1080px
📑 页面数: 1
📊 图层数: 24

🎨 图层分类统计:
  Image: 12 个
  Text: 5 个
  Vector: 4 个
  Group: 2 个
  Decorator: 1 个

🔍 识别到 18 个组件:
  - hero_background (background)
  - logo (image)
  - nav_button (button)
  - headline_text (text)
  - ...

📋 分析报告:
{
  "file": "designs/hero.psd",
  "canvas": {"width": 1920, "height": 1080},
  "pages": 1,
  "layers": 24,
  "classification": {...},
  "components": 18,
  "component_types": ["background", "image", "button", "text", "icon"]
}
```

## 注意事项

1. **快速模式**: 使用 `--verbose` 获取详细信息
2. **AI 识别**: 默认关闭 AI 识别以加快速度，添加 `--ai` 启用
3. **截图目录**: 临时截图保存在 `temp_screenshots/`，分析完成后自动清理

## 错误处理

| 错误 | 解决方案 |
|------|----------|
| 文件不存在 | 检查路径是否正确 |
| PSD 解析失败 | 确认文件是有效的 PSD 格式 |
| 依赖缺失 | 运行 `pip install -r requirements.txt` |
