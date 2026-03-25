# PSD Smart Cut - 使用文档

> 详细的使用指南，涵盖安装、基础使用、高级功能和 API 参考。

---

## 📦 安装

### 环境要求

- Python >= 3.10
- psd-tools >= 2.0.0
- Pillow >= 8.0.0
- PyYAML >= 6.0
- pydantic >= 2.0.0

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/lst016/psd-smart-cut.git
cd psd-smart-cut

# 2. 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 验证安装
python -c "from skills.psd_parser.level1_parse import parse_psd; print('✅ 安装成功')"
```

### 可选依赖（AI 功能）

```bash
# MiniMax VLM（推荐用于组件识别）
pip install minimax-api

# OpenAI GPT-4 Vision（备选方案）
pip install openai>=1.0.0
```

---

## 🚀 基础使用

### 1. PSD 文件解析

#### 基本解析

```python
from skills.psd_parser.level1_parse import parse_psd, extract_pages, read_layers

# 解析 PSD 文件
document = parse_psd("design.psd")
print(f"文档名称: {document.name}")
print(f"画布尺寸: {document.width}x{document.height}")

# 提取所有页面
pages = extract_pages("design.psd")
for i, page in enumerate(pages):
    print(f"页面 {i+1}: {page.name}")

# 读取第一页的图层
layers = read_layers("design.psd", page_index=0)
for layer in layers:
    print(f"  - {layer.name} ({layer.kind})")
```

#### LayerFilter 过滤图层

```python
from skills.psd_parser.level1_parse import LayerFilter, read_layers

layers = read_layers("design.psd", page_index=0)

# 过滤条件
filter_config = LayerFilter(
    include_hidden=False,    # 排除隐藏图层
    include_locked=False,    # 排除锁定图层
    min_width=10,            # 最小宽度
    min_height=10            # 最小高度
)

filtered = LayerFilter.apply(layers, filter_config)
```

### 2. 图层分类

#### 基本分类

```python
from skills.psd_parser.level2_classify import LayerClassifier

classifier = LayerClassifier()
classified = classifier.classify(layers)

# 输出分类结果
for layer_type, type_layers in classified.items():
    print(f"{layer_type}: {len(type_layers)} 个")
    for layer in type_layers[:3]:  # 只显示前3个
        print(f"  - {layer.name}")
```

#### 分类器详情

| 分类器 | 说明 | 子类型 |
|--------|------|--------|
| `ImageClassifier` | 图片分类 | button, icon, background, photo, illustration, banner, logo, avatar, decoration |
| `TextClassifier` | 文字分类 | heading, body, label, button_text, link, caption |
| `VectorClassifier` | 矢量分类 | shape, line, path, mask, clipping_path |
| `GroupClassifier` | 组分类 | section, component, layer_set |
| `DecoratorClassifier` | 装饰分类 | shadow, border, gradient, blur, pattern |

### 3. 组件识别

#### 基本识别

```python
from skills.psd_parser.level3_recognize import Recognizer

recognizer = Recognizer()
components = recognizer.recognize(
    layers,
    screenshots_dir="screenshots/",  # 截图保存目录
    use_ai=True                        # 启用 AI 识别
)

for comp in components:
    print(f"{comp.name}:")
    print(f"  类型: {comp.component_type}")
    print(f"  位置: {comp.bounds}")
    print(f"  截图: {comp.screenshot_path}")
```

#### 识别器模块

| 模块 | 功能 |
|------|------|
| `ScreenshotCapturer` | 捕获图层截图 |
| `RegionDetector` | 检测有效区域和边界 |
| `ComponentNamer` | 语义化组件命名 |
| `BoundaryAnalyzer` | 分析边缘质量和切割点 |
| `FunctionAnalyzer` | 分析交互功能和样式 |

### 4. 切割策略

#### 生成切割计划

```python
from skills.psd_parser.level4_strategy import Strategy

strategy = Strategy()
plan = strategy.generate(
    components,
    strategy_type="SMART_MERGE"  # 指定策略类型
)

print(f"策略: {plan.strategy_type}")
print(f"分组数: {len(plan.cut_groups)}")

for group in plan.cut_groups:
    print(f"  {group.name}: {len(group.components)} 个组件")
```

#### 策略类型

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| `FLAT` | 扁平化导出 | 简单 PSD，层级少 |
| `GROUP_BY_TYPE` | 按类型分组 | 需要按 image/text/vector 分类 |
| `GROUP_BY_PAGE` | 按页面分组 | 多页面 PSD |
| `PRESERVE_HIERARCHY` | 保持层级 | 需要还原 PSD 结构 |
| `SMART_MERGE` | 智能合并 | 自动优化重叠区域 |

### 5. 资产导出

#### 基本导出

```python
from skills.psd_parser.level5_export import Exporter

exporter = Exporter()
report = exporter.export(
    components,
    plan,
    output_dir="output/",
    formats=["png", "webp"],     # 导出格式
    quality=90,                    # 图片质量
    naming_template="{type}/{name}"  # 命名模板
)

print(f"导出完成!")
print(f"总数: {report.total_exported}")
print(f"成功: {report.successful}")
print(f"失败: {report.failed}")
print(f"Manifest: {report.manifest_path}")
```

#### 命名模板变量

| 变量 | 说明 | 示例 |
|------|------|------|
| `{name}` | 组件名称 | hero_image |
| `{type}` | 组件类型 | image |
| `{page}` | 页面名称 | home |
| `{index}` | 序号 | 001 |
| `{width}` | 宽度 | 1920 |
| `{height}` | 高度 | 1080 |

---

## 🔧 高级用法

### 1. 自定义分类规则

```python
from skills.psd_parser.level2_classify import ImageClassifier, TextClassifier

# 自定义图片分类器
image_classifier = ImageClassifier()

# 添加自定义规则
image_classifier.add_rule(
    name_pattern=r"^btn_.*",  # 名称匹配
    type_hint="button"         # 分类为按钮
)

# 自定义文字分类器
text_classifier = TextClassifier()
text_classifier.add_rule(
    font_size_threshold=24,    # 字号阈值
    type_hint="heading"         # 分类为标题
)
```

### 2. AI 组件识别

```python
from skills.psd_parser.level3_recognize import Recognizer
from skills.psd_parser.common.ai_client import MiniMaxClient

# 配置 AI 客户端
ai_client = MiniMaxClient(api_key="your-api-key")

recognizer = Recognizer(ai_client=ai_client)

# 批量识别（启用 AI）
components = recognizer.recognize(
    layers,
    use_ai=True,
    batch_size=10
)
```

### 3. 自定义切割策略

```python
from skills.psd_parser.level4_strategy import StrategySelector, CanvasAnalyzer

# 自定义策略选择器
selector = StrategySelector()

# 分析画布
canvas_analyzer = CanvasAnalyzer()
canvas_info = canvas_analyzer.analyze(layers)

# 选择最优策略
best_strategy = selector.select(
    components=components,
    canvas_info=canvas_info,
    options=["SMART_MERGE", "GROUP_BY_TYPE"]
)
```

### 4. 批量处理多个 PSD

```python
import os
from pathlib import Path

psd_files = list(Path("designs/").glob("*.psd"))

for psd_path in psd_files:
    print(f"处理: {psd_path.name}")
    
    # 解析
    document = parse_psd(psd_path)
    
    # 分类
    classifier = LayerClassifier()
    classified = classifier.classify(layers)
    
    # 识别
    recognizer = Recognizer()
    components = recognizer.recognize(layers)
    
    # 导出
    output_dir = f"output/{psd_path.stem}"
    exporter = Exporter()
    exporter.export(components, plan, output_dir)
```

### 5. 样式和规格生成

```python
from skills.psd_parser.level6_extractor import Extractor
from skills.psd_parser.level7_generator import Generator

# 提取样式
extractor = Extractor()
styles = extractor.extract(layers)

# 生成规格
generator = Generator()

# 生成 CSS
css_output = generator.generate_css(styles)
print(css_output)

# 生成 Tailwind
tailwind_output = generator.generate_tailwind(styles)
print(tailwind_output)

# 生成 iOS
ios_output = generator.generate_ios(styles)
print(ios_output)

# 生成 Android
android_output = generator.generate_android(styles)
print(android_output)
```

### 6. 文档自动生成

```python
from skills.psd_parser.level8_documentation import (
    ReadmeGenerator,
    ChangelogGenerator,
    ManifestGenerator,
    PreviewGenerator
)

# 生成 README
readme_gen = ReadmeGenerator()
readme = readme_gen.generate(project_path=".")

# 生成 CHANGELOG
changelog_gen = ChangelogGenerator()
changelog = changelog_gen.generate()

# 生成 Manifest
manifest_gen = ManifestGenerator()
manifest = manifest_gen.generate(components)

# 生成 HTML 预览
preview_gen = PreviewGenerator()
html = preview_gen.generate(components, styles)
```

---

## 📖 API 参考

### Level 1: PSD 解析

```python
# 解析 PSD
document = parse_psd(psd_path: str) -> PSDDocument

# 提取页面
pages = extract_pages(psd_path: str) -> List[Page]

# 读取图层
layers = read_layers(psd_path: str, page_index: int) -> List[Layer]

# 图层过滤
filtered = LayerFilter.apply(layers, config: LayerFilter)
```

### Level 2: 分类

```python
# 统一分类器
classified = LayerClassifier().classify(layers) -> Dict[LayerType, List[Layer]]

# 单独分类器
ImageClassifier().classify(layers)
TextClassifier().classify(layers)
VectorClassifier().classify(layers)
GroupClassifier().classify(layers)
DecoratorClassifier().classify(layers)
```

### Level 3: 识别

```python
# 统一识别器
components = Recognizer().recognize(
    layers,
    screenshots_dir: str,
    use_ai: bool = False
) -> List[Component]

# 单独识别器
ScreenshotCapturer().capture(layer, output_dir)
RegionDetector().detect(layer)
ComponentNamer().name(component)
BoundaryAnalyzer().analyze(layer)
FunctionAnalyzer().analyze(layer)
```

### Level 4: 策略

```python
# 生成切割计划
plan = Strategy().generate(
    components,
    strategy_type: str = "SMART_MERGE"
) -> CutPlan

# 单独策略模块
CanvasAnalyzer().analyze(layers)
StrategySelector().select(components, canvas_info)
OverlapDetector().detect(components)
QualityEvaluator().evaluate(plan)
```

### Level 5: 导出

```python
# 导出资产
report = Exporter().export(
    components,
    plan,
    output_dir: str,
    formats: List[str] = ["png"],
    quality: int = 90
) -> ExportReport

# 单独导出模块
AssetExporter().export(component, format, output_path)
FormatConverter().convert(image, format, quality)
NamingManager().generate(component, template)
MetadataAttacher().attach(image, metadata)
```

### Level 6-8: 提取/生成/文档

```python
# 提取
styles = Extractor().extract(layers) -> List[Style]

# 生成
Generator().generate_css(styles) -> str
Generator().generate_tailwind(styles) -> str
Generator().generate_ios(styles) -> str
Generator().generate_android(styles) -> str

# 文档
ReadmeGenerator().generate(project_path)
ChangelogGenerator().generate()
ManifestGenerator().generate(components)
PreviewGenerator().generate(components, styles)
```

---

## 🐛 常见问题

### Q: 提示 "psd-tools not found"

```bash
pip install psd-tools
```

### Q: AI 识别失败

确保设置了正确的 API Key：

```python
import os
os.environ["MINIMAX_API_KEY"] = "your-key"
```

或使用 mock 模式跳过 AI 识别：

```python
recognizer = Recognizer(use_ai=False)
```

### Q: 导出图片质量差

调整导出质量参数：

```python
exporter = Exporter()
report = exporter.export(..., quality=100)  # 最高质量
```

### Q: 找不到 PSD 文件中的图层

检查图层是否被隐藏或锁定：

```python
from skills.psd_parser.level1_parse import LayerFilter

filter_config = LayerFilter(include_hidden=True, include_locked=True)
filtered = LayerFilter.apply(layers, filter_config)
```

---

## 📝 示例代码

更多示例见 [`examples/`](./examples/) 目录：

| 示例 | 说明 |
|------|------|
| `basic_parse.py` | 基础解析示例 |
| `classify_example.py` | 分类使用示例 |
| `recognize_example.py` | 识别使用示例 |
| `strategy_example.py` | 策略使用示例 |
| `export_example.py` | 导出使用示例 |
| `full_workflow.py` | 完整工作流 |

---

## 🔗 相关链接

- [用户指南](./USER_GUIDE.md)
- [CLAUDE.md](./CLAUDE.md)
- [CHANGELOG.md](./CHANGELOG.md)
- [VERSION-PLAN.md](./VERSION-PLAN.md)
