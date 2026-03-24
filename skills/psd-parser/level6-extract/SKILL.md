# Level 6 - Extraction Layer

## 概述

**Level 6 - 提取层** 是 PSD Smart Cut 系统的第六层，负责从 PSD 图层中提取详细信息，包括：
- 文字内容
- 字体属性
- 图层样式
- 位置和尺寸

## 模块结构

```
level6-extract/
├── __init__.py           # 模块导出
├── text_reader.py        # 文字读取器
├── font_analyzer.py      # 字体分析器
├── style_extractor.py    # 样式提取器
├── position_reader.py    # 位置读取器
├── extractor.py          # 统一提取器
└── SKILL.md              # 本文档
```

## 核心功能

### 1. TextReader - 文字读取器

从 PSD 文字图层提取文字内容。

**主要类：**
- `TextReader` - 文字读取器
- `TextContent` - 文字内容数据类
- `TextDirection` - 文字方向枚举
- `ParagraphAlignment` - 段落对齐枚举

**功能：**
- 读取文字内容
- 检测编码（UTF-8 等）
- 检测 RTL 语言（阿拉伯文、希伯来文）
- 检测特殊字符
- 提取段落列表
- 批量读取

**使用示例：**
```python
from skills.psd_parser.level6_extract import TextReader, TextContent

reader = TextReader()

# 读取单个图层
layer = {
    'id': 'layer_1',
    'name': 'Title',
    'type': 'text',
    'kind': 'text',
    'text': {'content': 'Hello World'}
}

text_content = reader.read(layer)
if text_content:
    print(f"文字: {text_content.text}")
    print(f"编码: {text_content.encoding}")
    print(f"段落: {text_content.paragraphs}")
```

### 2. FontAnalyzer - 字体分析器

从 PSD 文字图层提取字体属性。

**主要类：**
- `FontAnalyzer` - 字体分析器
- `FontInfo` - 字体信息数据类
- `FontStyle` - 字体样式枚举

**功能：**
- 提取字体家族
- 提取字号和粗细
- 提取字体颜色
- 检测斜体和粗体
- 提取行高和字间距
- 检测下划线和删除线
- 批量分析

**使用示例：**
```python
from skills.psd_parser.level6_extract import FontAnalyzer, FontInfo

analyzer = FontAnalyzer()

# 分析单个图层
layer = {
    'id': 'layer_1',
    'name': 'Title',
    'type': 'text',
    'kind': 'text',
    'text': {
        'EngineDict': {
            'StyleRun': {
                'RunArray': [{
                    'RunData': {
                        'StyleSheet': {
                            'StyleSheetData': {
                                'Font': {'name': 'Arial'},
                                'FontSize': 24,
                                'FontWeight': 700,
                                'Color': {'red': 0, 'green': 0, 'blue': 0}
                            }
                        }
                    }
                }]
            }
        }
    }
}

font_info = analyzer.analyze(layer)
if font_info:
    print(f"字体: {font_info.family}")
    print(f"字号: {font_info.size}px")
    print(f"粗细: {font_info.weight}")
    print(f"颜色: {font_info.color}")
```

### 3. StyleExtractor - 样式提取器

从 PSD 图层提取样式属性。

**主要类：**
- `StyleExtractor` - 样式提取器
- `LayerStyle` - 图层样式数据类
- `ShadowEffect` - 阴影效果
- `BorderEffect` - 描边效果
- `GradientEffect` - 渐变效果

**功能：**
- 提取透明度
- 提取混合模式
- 提取填充不透明度
- 检测阴影效果
- 检测描边效果
- 检测渐变效果
- 批量提取

**使用示例：**
```python
from skills.psd_parser.level6_extract import StyleExtractor, LayerStyle

extractor = StyleExtractor()

# 提取单个图层样式
layer = {
    'id': 'layer_1',
    'name': 'Button',
    'type': 'image',
    'opacity': 0.8,
    'blendMode': 'multiply',
    'style': {
        'DropShadow': {
            'Color': {'red': 0, 'green': 0, 'blue': 0},
            'Opacity': 50,
            'OffsetX': 0,
            'OffsetY': 4,
            'Blur': 8
        }
    }
}

style = extractor.extract(layer)
print(f"透明度: {style.opacity}")
print(f"混合模式: {style.blend_mode}")
print(f"效果: {style.effects}")
if style.shadow:
    print(f"阴影: {style.shadow.color}, {style.shadow.opacity}")
```

### 4. PositionReader - 位置读取器

从 PSD 图层提取位置和尺寸信息。

**主要类：**
- `PositionReader` - 位置读取器
- `PositionData` - 位置数据类

**功能：**
- 提取左上角坐标 (x, y)
- 提取宽度和高度
- 计算右下角坐标 (right, bottom)
- 计算中心点 (center_x, center_y)
- 检测可见性和锁定状态
- 提取旋转角度
- 检测重叠
- 计算重叠面积
- 计算图层间距离

**使用示例：**
```python
from skills.psd_parser.level6_extract import PositionReader, PositionData

reader = PositionReader()

# 读取单个图层位置
layer = {
    'id': 'layer_1',
    'name': 'Image',
    'visible': True,
    'locked': False,
    'left': 100,
    'top': 50,
    'right': 300,
    'bottom': 200
}

position = reader.read(layer)
print(f"位置: ({position.x}, {position.y})")
print(f"尺寸: {position.width} x {position.height}")
print(f"中心: ({position.center_x}, {position.center_y})")
print(f"可见: {position.is_visible}")

# 检查重叠
pos2 = reader.read(layer2)
if reader.is_overlapping(position, pos2):
    area = reader.calculate_overlap_area(position, pos2)
    print(f"重叠面积: {area}")
```

### 5. Extractor - 统一提取器

协调所有提取器，提供统一接口。

**主要类：**
- `Extractor` - 统一提取器
- `ExtractionResult` - 提取结果数据类

**功能：**
- 提取所有信息（文字、字体、样式、位置）
- 批量提取
- 转换为字典
- 转换为 JSON
- 生成摘要
- 获取统计信息

**使用示例：**
```python
from skills.psd_parser.level6_extract import Extractor, ExtractionResult

# 创建提取器
extractor = Extractor(mock_mode=True)

# 提取单个图层
layer = {
    'id': 'layer_1',
    'name': 'Title',
    'type': 'text',
    'kind': 'text',
    'visible': True,
    'left': 100, 'top': 50, 'right': 300, 'bottom': 100,
    'opacity': 1.0,
    'blendMode': 'norm',
    'text': {'content': 'Hello World'}
}

result = extractor.extract_all(layer)

# 访问结果
print(f"文字: {result.text.text if result.text else 'N/A'}")
print(f"字体: {result.font.family if result.font else 'N/A'}")
print(f"透明度: {result.style.opacity if result.style else 'N/A'}")
print(f"位置: ({result.position.x}, {result.position.y})" if result.position else "位置: N/A")

# 转换为 JSON
json_str = extractor.to_json(result)
print(json_str)

# 批量提取
layers = [layer1, layer2, layer3]
results = extractor.extract_batch(layers)

# 获取统计
stats = extractor.get_statistics(results)
print(f"成功率: {stats['success_rate']:.1%}")
```

## 数据流

```
PSD Layer
    │
    ▼
┌─────────────────────────────────────────────────────┐
│                   Extractor                         │
│  (协调所有提取器，提供统一接口)                        │
└─────────────────────────────────────────────────────┘
    │
    ├──► TextReader ─────► TextContent
    ├──► FontAnalyzer ───► FontInfo
    ├──► StyleExtractor ─► LayerStyle
    └──► PositionReader ─► PositionData
              │
              ▼
      ExtractionResult
```

## Mock 模式

所有提取器都支持 Mock 模式，在没有真实 PSD 数据时生成模拟数据：

```python
# 启用 Mock 模式（默认）
extractor = Extractor(mock_mode=True)

# Mock 模式会自动生成合理的模拟数据
# 用于测试和开发
```

## 错误处理

所有提取器都使用统一的错误处理机制：

```python
try:
    result = extractor.extract_all(layer)
except Exception as e:
    logger.error(f"提取失败: {e}")
    # 错误会被记录到 error_handler
```

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v0.6 | 2026-03-25 | 初始版本，4 个提取器 + 统一提取器 |
