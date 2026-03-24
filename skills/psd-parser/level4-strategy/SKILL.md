# Level 4 - Strategy Layer (策略层)

切割策略 Agent，决定如何切割 PSD 组件。

## 概述

Level 4 策略层负责分析画布布局、选择最佳切割策略、检测图层重叠、评估切割质量，并生成完整的切割计划。

## 模块结构

```
level4-strategy/
├── canvas_analyzer.py     # 画布分析器
├── strategy_selector.py   # 策略选择器
├── overlap_detector.py    # 重叠检测器
├── quality_evaluator.py   # 质量评估器
├── strategy.py            # 统一策略器
├── __init__.py            # 模块导出
└── SKILL.md               # 本文档
```

## 策略类型

### 1. FLAT (扁平切割)
- **描述**: 所有图层单独导出，每个图层一个文件
- **适用场景**: 少量图层、组件库、图标
- **优点**: 最精细的控制，便于单独修改
- **缺点**: 文件数量多

```python
from level4_strategy import StrategySelector, StrategyType

selector = StrategySelector()
result = selector.select(layers, strategy=StrategyType.FLAT)
```

### 2. GROUP_BY_TYPE (按类型分组)
- **描述**: 按图层类型分组导出，相似的图层放在一起
- **适用场景**: 文字密集页面、表单元素
- **优点**: 减少文件数量，保持类型一致性
- **缺点**: 可能需要手动拆分复杂组

```python
result = selector.select(layers, strategy=StrategyType.GROUP_BY_TYPE)
```

### 3. GROUP_BY_PAGE (按页面分组)
- **描述**: 按页面分组导出，每个页面的图层放在一起
- **适用场景**: 多页面 PSD、PPT 风格的 PSD
- **优点**: 符合设计文件的页面组织方式
- **缺点**: 需要图层有 page 属性

```python
result = selector.select(layers, strategy=StrategyType.GROUP_BY_PAGE)
```

### 4. PRESERVE_HIERARCHY (保留层级)
- **描述**: 保留 PSD 原有的层级结构
- **适用场景**: 复杂组结构、需要保持上下文的组件
- **优点**: 完全保留设计意图
- **缺点**: 可能产生深层的目录结构

```python
result = selector.select(layers, strategy=StrategyType.PRESERVE_HIERARCHY)
```

### 5. SMART_MERGE (智能合并)
- **描述**: 智能合并相邻且相似的图层
- **适用场景**: 大量相似元素、需要优化的场景
- **优点**: 减少冗余文件，优化输出
- **缺点**: 可能丢失细微差异

```python
result = selector.select(layers, strategy=StrategyType.SMART_MERGE)
```

## 核心类

### CanvasAnalyzer

分析画布尺寸、组件分布、密度热力图，识别切割线。

```python
from level4_strategy import CanvasAnalyzer

analyzer = CanvasAnalyzer()
result = analyzer.analyze(
    canvas_width=1920,
    canvas_height=1080,
    dpi=72,
    color_mode="RGB",
    layers=layers
)

# 获取统计信息
stats = analyzer.get_canvas_stats(result)
print(stats)
```

### StrategySelector

根据组件类型和分布选择最佳切割策略。

```python
from level4_strategy import StrategySelector

selector = StrategySelector()
result = selector.select(
    layers=layers,
    canvas_info={'width': 1920, 'height': 1080},
    classification_results=classifications
)

print(f"选择策略: {result.selected_strategy.value}")
print(f"切割建议: {len(result.recommendations)} 个")
```

### OverlapDetector

检测图层之间的重叠关系，确定切割优先级。

```python
from level4_strategy import OverlapDetector

detector = OverlapDetector()
result = detector.detect_overlaps(
    layers=layers,
    z_order=['layer1', 'layer2', 'layer3']
)

# 获取遮挡关系
print(f"重叠对数: {len(result.overlaps)}")
print(f"优先级图层: {result.priority_layers[:5]}")
```

### QualityEvaluator

评估切割质量，检测问题并提供改进建议。

```python
from level4_strategy import QualityEvaluator

evaluator = QualityEvaluator()
result = evaluator.evaluate(
    layers=layers,
    cut_lines=[{'id': 'cl_0', 'direction': 'vertical', 'position': 960}],
    suggested_slices=slices
)

print(f"质量分数: {result.score.overall}")
print(f"问题: {result.score.issues}")
```

### Strategy (统一策略器)

协调所有策略模块，生成完整的切割计划。

```python
from level4_strategy import Strategy

strategy = Strategy()
plan = strategy.create_plan(
    layers=layers,
    canvas_width=1920,
    canvas_height=1080,
    dpi=72,
    color_mode="RGB"
)

# 导出为 JSON
json_plan = strategy.export_plan_json(plan)
```

## 快速开始

### 完整流程示例

```python
from level4_strategy import Strategy

# 初始化策略器
strategy = Strategy()

# 创建切割计划
plan = strategy.create_plan(
    layers=[
        {
            'id': 'layer_1',
            'name': 'Background',
            'type': 'background',
            'bounds': {'x': 0, 'y': 0, 'width': 1920, 'height': 1080}
        },
        {
            'id': 'layer_2',
            'name': 'Header',
            'type': 'group',
            'bounds': {'x': 0, 'y': 0, 'width': 1920, 'height': 100}
        },
        {
            'id': 'layer_3',
            'name': 'Logo',
            'type': 'image',
            'bounds': {'x': 50, 'y': 25, 'width': 100, 'height': 50}
        }
    ],
    canvas_width=1920,
    canvas_height=1080,
    dpi=72,
    color_mode="RGB"
)

# 查看结果
print(f"策略类型: {plan.strategy_type}")
print(f"切割区域数: {len(plan.cut_regions)}")
print(f"质量分数: {plan.quality_score.overall}")

# 优化计划
optimized_plan = strategy.optimize_plan(
    plan,
    layers=layers,
    max_regions=50,
    min_region_area=100
)

# 导出 JSON
import json
print(json.dumps(strategy.export_plan_json(optimized_plan), indent=2))
```

### Mock 模式测试

```python
from level4_strategy import Strategy

# 创建 mock 数据
mock_layers = [
    {
        'id': f'layer_{i}',
        'name': f'Layer {i}',
        'type': ['image', 'text', 'group'][i % 3],
        'bounds': {
            'x': (i % 4) * 200,
            'y': (i // 4) * 200,
            'width': 150,
            'height': 150
        }
    }
    for i in range(12)
]

# 创建计划
strategy = Strategy()
plan = strategy.create_plan(
    layers=mock_layers,
    canvas_width=800,
    canvas_height=600
)

assert plan is not None
assert len(plan.cut_regions) > 0
print("Mock 测试通过!")
```

## 数据类

### CanvasInfo
```python
@dataclass
class CanvasInfo:
    width: int           # 画布宽度
    height: int          # 画布高度
    dpi: int             # 分辨率
    color_mode: str      # 颜色模式
    layers_count: int    # 图层数量
```

### CutRegion
```python
@dataclass
class CutRegion:
    region_id: str                    # 区域 ID
    layer_ids: List[str]              # 包含的图层 ID 列表
    bounds: Tuple[int, int, int, int] # (x, y, width, height)
    cut_type: str                     # 'export'/'merge'/'ignore'
    reason: str                       # 切割原因
```

### CutPlan
```python
@dataclass
class CutPlan:
    strategy_type: str               # 策略类型
    canvas_info: CanvasInfo          # 画布信息
    cut_regions: List[CutRegion]      # 切割区域列表
    overlaps: List[OverlapInfo]      # 重叠信息列表
    quality_score: QualityScore      # 质量分数
    metadata: Dict                   # 元数据
```

## 配置

策略选择器支持自定义规则：

```python
from level4_strategy import StrategySelector, StrategyRule, StrategyType

# 创建自定义规则
custom_rule = StrategyRule(
    name="my_custom_rule",
    description="自定义规则",
    conditions={
        "layer_types": ["button", "icon"],
        "strategy": StrategyType.FLAT
    },
    priority=15  # 高优先级
)

selector = StrategySelector()
selector.add_rule(custom_rule)
```

## 错误处理

所有模块都使用统一的错误处理：

```python
from skills.common import get_error_handler, ErrorCategory

error_handler = get_error_handler()

try:
    plan = strategy.create_plan(layers=layers, ...)
except Exception as e:
    error_handler.record(
        task="create_cut_plan",
        error=e,
        category=ErrorCategory.CLASSIFY_ERROR
    )
```

## 日志

使用统一的日志系统：

```python
from skills.common import get_logger

logger = get_logger("strategy")
logger.info("创建切割计划", layers_count=len(layers))
logger.debug("选择策略", strategy=selected_strategy.value)
logger.warning("检测到重叠", overlap_count=len(overlaps))
```

## 测试

运行测试：

```bash
cd ~/Desktop/agent/projects/psd-smart-cut
python -m pytest skills/psd-parser/level4-strategy/test_level4.py -v
```

## 下游集成

Level 4 输出给 Level 5 (Export Layer)：

```python
# Level 4 输出
plan = strategy.create_plan(layers=layers, ...)

# Level 5 输入
from level5_export import asset_exporter

exporter = AssetExporter()
for region in plan.cut_regions:
    exporter.export(
        layer_ids=region.layer_ids,
        bounds=region.bounds,
        cut_type=region.cut_type
    )
```

## 版本历史

- v0.4: 初始版本，实现 4 个策略模块 + 统一策略器
