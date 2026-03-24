# Level 7 - Generate Layer

## 概述

**功能：** 规格生成 Agent，生成组件的技术规格文档  
**版本：** v0.7  
**状态：** ✅ 已完成

## 能力

### 1. 尺寸生成 (DimensionGenerator)
- 生成组件尺寸规格
- 支持多单位（px/rem/dp/pt/em/vh/vw/%）
- 生成响应式尺寸（mobile/tablet/desktop/wide）
- 计算缩放因子（1x/2x/3x）
- 单位转换

### 2. 位置生成 (PositionGenerator)
- 生成 CSS position 值
- 生成 Flex/Grid 布局属性
- 生成边距/内边距
- 坐标转换

### 3. 样式生成 (StyleGenerator)
- 生成 CSS 属性
- 生成 Tailwind CSS 类名
- 生成 iOS 样式 (Swift)
- 生成 Android 样式 (XML)
- 处理主题变量

### 4. 规格验证 (SpecValidator)
- 验证规格完整性
- 检查冲突属性
- 验证 CSS 语法
- 验证响应式断点

### 5. JSON Schema
- 组件规格 Schema
- 组件集合 Schema
- 完整的数据定义

## 文件结构

```
level7-generate/
├── __init__.py           # 模块导出
├── dimension_generator.py # 尺寸生成器
├── position_generator.py # 位置生成器
├── style_generator.py    # 样式生成器
├── spec_validator.py      # 规格验证器
├── schema.py              # JSON Schema 定义
├── generator.py          # 统一生成器
└── test_level7.py         # 测试文件
```

## 使用示例

### 基本使用

```python
from skills.psd_parser.level7_generate import (
    SpecGenerator,
    ComponentSpec
)

# 初始化生成器
generator = SpecGenerator()

# 单个图层生成
layer_info = {
    "id": "layer_1",
    "name": "Button",
    "kind": "image",
    "width": 200,
    "height": 50,
    "bbox": {"x": 100, "y": 100, "width": 200, "height": 50}
}

spec = generator.generate(layer_info)
print(spec.to_dict())
```

### 批量生成

```python
# 批量生成
layers = [
    {"id": "layer_1", "name": "Header", ...},
    {"id": "layer_2", "name": "Button", ...},
]

specs, report = generator.generate_batch(layers, canvas_size)
```

### 生成组件集合

```python
# 生成完整集合
collection = generator.generate_collection(
    layers=layers,
    source_file="design.psd",
    canvas_size={"width": 1920, "height": 1080}
)

# 导出 JSON
generator.export_to_json(collection, "output/specs.json")
```

### 尺寸生成

```python
from skills.psd_parser.level7_generate import DimensionGenerator

gen = DimensionGenerator()
dim = gen.generate({"width": 100, "height": 50}, unit="rem")
print(dim.to_dict())
```

### 样式生成

```python
from skills.psd_parser.level7_generate import StyleGenerator

gen = StyleGenerator()
style = gen.generate({
    "colors": {"primary": "#3498db"},
    "font": {"family": "Arial", "size": 14},
    "border_radius": 8
})
print(style.to_dict())
```

### 规格验证

```python
from skills.psd_parser.level7_generate import SpecValidator

validator = SpecValidator()
result = validator.validate(spec_dict)

if not result.valid:
    for error in result.errors:
        print(f"{error.field}: {error.message}")
```

## API 参考

### DimensionGenerator

| 方法 | 说明 |
|------|------|
| `generate(layer_info, unit)` | 生成单个尺寸规格 |
| `generate_batch(layers, unit)` | 批量生成 |
| `generate_responsive_sizes(base_width, base_height)` | 生成响应式尺寸 |

### PositionGenerator

| 方法 | 说明 |
|------|------|
| `generate(position_info, canvas_size)` | 生成单个位置规格 |
| `generate_batch(positions, canvas_size)` | 批量生成 |

### StyleGenerator

| 方法 | 说明 |
|------|------|
| `generate(style_info)` | 生成单个样式规格 |
| `generate_batch(styles)` | 批量生成 |
| `generate_text_style(text_info)` | 生成文字样式 |
| `generate_background_style(bg_info)` | 生成背景样式 |
| `merge_styles(styles)` | 合并多个样式 |

### SpecValidator

| 方法 | 说明 |
|------|------|
| `validate(spec)` | 验证单个规格 |
| `validate_batch(specs)` | 批量验证 |
| `check_conflicts(spec)` | 检查冲突属性 |

### SpecGenerator

| 方法 | 说明 |
|------|------|
| `generate(layer_info, canvas_size)` | 生成单个组件规格 |
| `generate_batch(layers, canvas_size)` | 批量生成 |
| `generate_collection(layers, source_file, canvas_size)` | 生成组件集合 |
| `export_to_json(collection, output_path)` | 导出 JSON |

## 配置

```yaml
level7:
  default_unit: "px"
  enable_validation: true
  enable_tailwind: true
  enable_native_styles: true
  breakpoints:
    mobile: 480
    tablet: 768
    desktop: 1024
    wide: 1440
```

## 响应式断点

| 断点 | 宽度范围 | 缩放比例 |
|------|----------|----------|
| mobile | < 480px | 0.5x |
| tablet | 480-768px | 0.75x |
| desktop | 768-1024px | 1.0x |
| wide | > 1024px | 1.0x |

## 主题变量

生成的主题变量格式：

```css
--theme-{color_name}: {value}
```

例如：

```css
--theme-primary: #3498db;
--theme-background: #ffffff;
--theme-text: #333333;
```

## 依赖

- Python 3.8+
- skills.common (错误处理、日志、验证)

## 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.7 | 2026-03-25 | 初始版本，4 个生成器 + JSON Schema |
