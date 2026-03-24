# Level 3 - 识别层 (Recognition Layer)

**版本:** v0.3  
**状态:** ✅ 完成  
**依赖:** skills.common, psd-tools (可选)

---

## 概述

识别层（Level 3）是 PSD Smart Cut 的第三层，负责从解析后的图层元数据中识别 UI 组件的类型、边界和功能。

## 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      Recognizer (统一入口)                    │
│                  协调所有识别器，提供统一接口                    │
└──────────┬──────────────┬──────────────┬──────────────┬──────┘
           │              │              │              │
           ▼              ▼              ▼              ▼
┌─────────────────┐ ┌────────────┐ ┌─────────────┐ ┌────────────┐
│ScreenshotCapturer│ │RegionDetector│ │ComponentNamer│ │BoundaryAnalyzer│
│  图层截图捕获    │ │  区域检测    │ │  组件命名    │ │  边界分析   │
│                 │ │ 边界矩形     │ │ AI/规则推断   │ │ 边缘类型    │
│ PSD → PNG       │ │ 重叠检测     │ │ 语义化名称    │ │ 切割点     │
└─────────────────┘ └────────────┘ └─────────────┘ └────────────┘
                                                │
                                                ▼
                                       ┌────────────┐
                                       │FunctionAnalyzer│
                                       │  功能分析    │
                                       │ 交互类型    │
                                       │ 样式属性    │
                                       └────────────┘
```

## 模块说明

### 1. ScreenshotCapturer - 图层截图捕获器

从 PSD 导出单个或多个图层的 PNG 截图。

```python
from skills.psd-parser.level3_recognize import ScreenshotCapturer, ScreenshotResult

capturer = ScreenshotCapturer(output_dir="./output/screenshots")

# 捕获单个图层
result = capturer.capture_layer(
    psd_file="design.psd",
    layer_id="123",
    scale=2.0  # 2x 分辨率
)

# 批量捕获
results = capturer.capture_layers(
    psd_file="design.psd",
    layer_ids=["123", "456", "789"],
    scale=1.0
)
```

**ScreenshotResult 字段:**
| 字段 | 类型 | 说明 |
|------|------|------|
| success | bool | 是否成功 |
| layer_id | str | 图层 ID |
| screenshot_path | str | 截图保存路径 |
| width | int | 截图宽度 |
| height | int | 截图高度 |
| error | str | 错误信息（失败时） |

### 2. RegionDetector - 区域检测器

分析图层边界矩形，检测重叠区域，计算有效内容区域。

```python
from skills.psd-parser.level3_recognize import RegionDetector

detector = RegionDetector(
    overlap_threshold=0.3,    # IoU 阈值
    adjacent_threshold=5,     # 相邻判定阈值
    min_region_area=100      # 最小区域面积
)

# 分析单个图层
result = detector.analyze(layer_metadata)

# 批量分析
results = detector.batch_analyze(layers_metadata)
```

**RegionResult 字段:**
| 字段 | 类型 | 说明 |
|------|------|------|
| raw_boundary | dict | 原始边界 {x, y, width, height} |
| effective_boundary | dict | 有效内容边界 |
| overlap_regions | list | 重叠区域列表 |
| merged_regions | list | 合并后的区域列表 |

### 3. ComponentNamer - 组件命名器

基于截图和元数据命名组件，支持 AI（MiniMax VLM）识别。

```python
from skills.psd-parser.level3_recognize import ComponentNamer, guess_type_from_name, generate_component_name

namer = ComponentNamer(use_ai=True)  # 需要 MiniMax API

# 从元数据命名
result = namer.name_from_metadata(
    layer_metadata={"layer_id": "123", "name": "btn_submit", "type": "vector"},
    screenshot_path="./output/screenshots/layer_123.png"
)

# 批量命名
results = namer.batch_name([
    {"layer_metadata": meta1, "screenshot_path": path1},
    {"layer_metadata": meta2, "screenshot_path": path2},
])
```

**NamingResult 字段:**
| 字段 | 类型 | 说明 |
|------|------|------|
| component_name | str | 生成的组件名称（如 ButtonPrimary1） |
| component_type | str | 组件类型（button/input/card/icon 等） |
| confidence | float | 置信度 0-1 |
| reasoning | str | 识别理由 |

**支持的组件类型:**
- button, input, card, icon, text, heading, image
- navigation, list, modal, checkbox, radio, toggle
- dropdown, tooltip, badge, divider, avatar, progress

### 4. BoundaryAnalyzer - 边界分析器

分析组件边界，检测边缘类型，识别切割点。

```python
from skills.psd-parser.level3_recognize import BoundaryAnalyzer

analyzer = BoundaryAnalyzer(
    quality_threshold=0.7,
    min_cut_distance=10
)

result = analyzer.analyze(
    boundary={"x": 0, "y": 0, "width": 200, "height": 50},
    layer_metadata=metadata
)
```

**BoundaryResult 字段:**
| 字段 | 类型 | 说明 |
|------|------|------|
| edge_type | str | 边缘类型（horizontal/vertical/diagonal/curve/irregular） |
| quality_score | float | 边界质量分数 0-1 |
| cut_points | list | 切割点列表 [{x, y, edge_type, quality}] |

### 5. FunctionAnalyzer - 功能分析器

分析组件功能、交互类型和样式属性。

```python
from skills.psd-parser.level3_recognize import FunctionAnalyzer

analyzer = FunctionAnalyzer()

result = analyzer.analyze(
    layer_metadata=metadata,
    component_type="button",
    component_name="ButtonPrimary"
)
```

**FunctionResult 字段:**
| 字段 | 类型 | 说明 |
|------|------|------|
| component_type | str | 组件类型 |
| interaction_types | list | 交互类型列表 |
| functions | list | 功能列表 |
| style_attributes | dict | 样式属性 |
| description | str | 功能描述 |
| accessibility_hints | list | 无障碍提示 |

**交互类型:**
- `click` - 点击
- `input` - 输入
- `hover` - 悬停
- `scroll` - 滚动
- `drag` - 拖拽
- `toggle` - 切换
- `select` - 选择
- `navigate` - 导航
- `display` - 仅展示

### 6. Recognizer - 统一识别器

整合所有识别器，提供一站式识别服务。

```python
from skills.psd-parser.level3_recognize import Recognizer

recognizer = Recognizer(
    output_dir="./output",
    use_screenshot=True,
    use_ai_naming=False  # 不使用 AI 命名
)

# 单个识别
result = recognizer.recognize(
    psd_file="design.psd",
    layer_metadata={
        "layer_id": "123",
        "name": "登录按钮",
        "type": "vector",
        "position": {"x": 100, "y": 200},
        "dimensions": {"width": 120, "height": 40}
    }
)

# 批量识别
results = recognizer.batch_recognize(
    psd_file="design.psd",
    layers_metadata=[meta1, meta2, meta3]
)

# 识别并保存
results, output_file = recognizer.recognize_and_save(
    psd_file="design.psd",
    layers_metadata=[meta1, meta2, meta3],
    output_file="./output/recognition.json"
)

# 获取摘要
summary = recognizer.get_summary(results)
print(f"识别了 {summary['total']} 个组件，成功率 {summary['success']/summary['total']*100:.1f}%")
```

**RecognitionResult 字段:**
| 字段 | 类型 | 说明 |
|------|------|------|
| layer_id | str | 图层 ID |
| component_name | str | 组件名称 |
| component_type | str | 组件类型 |
| boundary | dict | 边界信息 |
| functions | list | 功能列表 |
| interaction_types | list | 交互类型 |
| confidence | float | 综合置信度 0-1 |
| metadata | dict | 附加元数据 |

---

## 使用示例

### 完整工作流

```python
from skills.psd-parser.level3_recognize import Recognizer

# 初始化
recognizer = Recognizer(
    output_dir="./output",
    use_screenshot=True,
    use_ai_naming=False
)

# 模拟 Level 1/2 的输出
layers_metadata = [
    {
        "layer_id": "1",
        "name": "btn_submit",
        "type": "vector",
        "position": {"x": 100, "y": 200},
        "dimensions": {"width": 120, "height": 40}
    },
    {
        "layer_id": "2",
        "name": "input_username",
        "type": "text",
        "position": {"x": 100, "y": 100},
        "dimensions": {"width": 300, "height": 36}
    },
]

# 批量识别
results = recognizer.batch_recognize(
    psd_file="design.psd",
    layers_metadata=layers_metadata
)

# 打印结果
for r in results:
    print(f"{r.component_name} ({r.component_type}): confidence={r.confidence}")
    print(f"  边界: {r.boundary}")
    print(f"  功能: {r.functions}")
    print(f"  交互: {r.interaction_types}")
```

### Mock 模式（无 PSD 文件）

```python
from skills.psd-parser.level3_recognize import Recognizer

recognizer = Recognizer(use_screenshot=False)

# 模拟元数据
meta = {
    "layer_id": "mock_1",
    "name": "Header Card",
    "type": "pixel",
    "position": {"x": 0, "y": 0},
    "dimensions": {"width": 375, "height": 200}
}

result = recognizer.recognize(
    psd_file="",  # 空文件路径，mock 模式
    layer_metadata=meta
)

print(result.component_name)  # CardMockComponent
print(result.component_type)  # card
```

---

## 错误处理

所有模块都使用统一的 `ErrorHandler`，错误记录到 `logs/errors.jsonl`:

```json
{"timestamp": "...", "task": "recognize", "error_message": "...", "category": "parse_error", "severity": "medium"}
```

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.3.0 | 2026-03-24 | 初始版本，实现 5 个识别器和统一入口 |
