# PSD Smart Cut

> AI-powered PSD component extraction and smart cutting workflow system.

**Status: v0.9 - 集成测试完成** | [中文文档](./docs/USER_GUIDE.md) | [使用指南](./docs/usage.md)

---

## ✨ 功能特性

### 🏗️ 9 层架构 pipeline

| Level | 模块 | 功能 | 状态 |
|-------|------|------|------|
| **L1** | PSD 解析层 | Page 提取、Layer 读取、层级树构建、隐藏/锁定图层检测 | ✅ 完成 |
| **L2** | 分类层 | 图片/文字/矢量/组/装饰 五大分类器 + 子类型细分 | ✅ 完成 |
| **L3** | 识别层 | 截图捕获、区域检测、组件命名、边界分析、功能分析 | ✅ 完成 |
| **L4** | 策略层 | 画布分析、切割策略选择、重叠检测、质量评估 | ✅ 完成 |
| **L5** | 导出层 | 资产导出、格式转换、命名管理、元数据附加 | ✅ 完成 |
| **L6** | 提取层 | 文字读取、字体分析、样式提取、位置读取 | ✅ 完成 |
| **L7** | 生成层 | 尺寸/位置/样式生成器，CSS/Tailwind/iOS/Android 多平台输出 | ✅ 完成 |
| **L8** | 文档层 | README/CHANGELOG/Manifest/HTML 预览 自动生成 | ✅ 完成 |
| **L9** | 集成测试 | 端到端测试、性能测试、边界情况测试 | ✅ 完成 |

### 🤖 AI 能力

- **智能分类**：基于启发式规则 + AI 模型自动识别图层类型
- **组件识别**：支持按钮、图标、横幅、相册等 12+ 组件类型识别
- **语义命名**：AI 驱动的语义化组件命名
- **多平台规格**：自动生成 CSS/Tailwind/iOS/Android 代码

### 📦 导出格式

| 格式 | 支持 | 说明 |
|------|------|------|
| PNG | ✅ | 无损压缩，支持透明 |
| JPG | ✅ | 有损压缩，可调质量 |
| WebP | ✅ | 现代格式，压缩率高 |
| SVG | ✅ | 矢量导出（部分） |

### 🔧 切割策略

| 策略 | 说明 |
|------|------|
| `FLAT` | 扁平化导出所有图层 |
| `GROUP_BY_TYPE` | 按类型分组（image/text/vector） |
| `GROUP_BY_PAGE` | 按页面分组 |
| `PRESERVE_HIERARCHY` | 保持 PSD 层级结构 |
| `SMART_MERGE` | 智能合并重叠区域 |

---

## 📁 项目结构

```
psd-smart-cut/
├── skills/
│   └── psd-parser/
│       ├── level1-parse/          # PSD 解析层
│       ├── level2_classify/       # 分类层
│       ├── level3_recognize/      # 识别层
│       ├── level4_strategy/        # 策略层
│       ├── level5_export/          # 导出层
│       ├── level6_extractor/       # 提取层
│       ├── level7_generator/       # 生成层
│       ├── level8_documentation/   # 文档层
│       └── level9_integration/    # 集成测试
├── configs/
│   └── config.yaml                # 配置文件
├── docs/                          # 文档
│   ├── USER_GUIDE.md             # 用户指南
│   ├── usage.md                  # 使用文档
│   ├── CHANGELOG.md              # 变更日志
│   └── VERSION-PLAN.md           # 版本计划
├── examples/                      # 示例
│   ├── basic_parse.py            # 基础解析
│   ├── classify_example.py        # 分类示例
│   ├── recognize_example.py       # 识别示例
│   ├── strategy_example.py        # 策略示例
│   ├── export_example.py          # 导出示例
│   └── full_workflow.py          # 完整工作流
├── requirements.txt
└── README.md
```

---

## 🚀 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/lst016/psd-smart-cut.git
cd psd-smart-cut

# 安装依赖
pip install -r requirements.txt

# 可选：AI 功能依赖
pip install minimax-api openai
```

### Python API

#### 1. 基础解析

```python
from skills.psd_parser.level1_parse import parse_psd, extract_pages, read_layers

# 解析 PSD 文件
document = parse_psd("design.psd")

# 提取所有页面
pages = extract_pages("design.psd")
print(f"发现 {len(pages)} 个页面")

# 读取第一页的所有图层
layers = read_layers("design.psd", page_index=0)
for layer in layers:
    print(f"图层: {layer.name}, 类型: {layer.kind}")
```

#### 2. 图层分类

```python
from skills.psd_parser.level2_classify import LayerClassifier

classifier = LayerClassifier()
classified = classifier.classify(layers)

for layer_type, type_layers in classified.items():
    print(f"{layer_type}: {len(type_layers)} 个图层")
```

#### 3. 组件识别

```python
from skills.psd_parser.level3_recognize import Recognizer

recognizer = Recognizer()
components = recognizer.recognize(layers, screenshots_dir="screenshots/")

for comp in components:
    print(f"{comp.name} - {comp.component_type} @ {comp.bounds}")
```

#### 4. 切割策略

```python
from skills.psd_parser.level4_strategy import Strategy

strategy = Strategy()
plan = strategy.generate(components)

print(f"切割计划: {plan.strategy_type}")
print(f"导出 {len(plan.cut_groups)} 个分组")
```

#### 5. 资产导出

```python
from skills.psd_parser.level5_export import Exporter

exporter = Exporter()
report = exporter.export(components, plan, "output/")

print(f"已导出 {report.total_exported} 个资源")
print(f"manifest: {report.manifest_path}")
```

#### 6. 完整工作流

```python
from skills.psd_parser.level9_integration import run_full_pipeline

# 一行命令执行完整流程
result = run_full_pipeline(
    psd_path="design.psd",
    output_dir="./output",
    strategy="SMART_MERGE",
    formats=["png", "webp"]
)
```

### CLI 命令行

```bash
# 基本解析
python examples/basic_parse.py your_file.psd

# 完整流程
python -m skills.cli process design.psd --output ./output

# 指定策略
python -m skills.cli process design.psd --strategy SMART_MERGE --formats png,webp

# Mock 模式测试（无需 PSD 文件）
python -m pytest skills/psd-parser/level9_integration/ -v
```

---

## 🏛️ 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        PSD 文件输入                               │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Level 1: PSD 解析层                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────┐ │
│  │Page提取器│ │Layer读取器│ │层级构建器│ │隐藏标记器│ │锁定检测│ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └───────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Level 2: 分类层                                                  │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐    │
│  │图片分类│ │文字分类│ │矢量分类│ │组分类  │ │装饰分类  │    │
│  └────────┘ └────────┘ └────────┘ └────────┘ └──────────┘    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Level 3: 识别层                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────┐ │
│  │截图捕获器│ │区域检测器│ │组件命名器│ │边界分析器│ │功能分析│ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └───────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Level 4: 策略层                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │画布分析器│ │策略选择器│ │重叠检测器│ │质量评估器│           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Level 5: 导出层                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │资产导出器│ │格式转换器│ │命名管理器│ │元数据附加│           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Level 6-8: 提取/生成/文档层                                      │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐       │
│  │文字提取│ │样式提取│ │规格生成│ │文档生成│ │预览生成│       │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘       │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  输出: PNG/JPG/WebP/SVG 资源 + CSS/Tailwind/iOS/Android 规格     │
│       + README/CHANGELOG/Manifest/HTML 文档                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧪 测试

```bash
# 运行所有级别测试
cd skills/psd-parser
python -m pytest level1-parse/test_level1.py -v
python -m pytest level2_classify/ -v
python -m pytest level3_recognize/ -v
python -m pytest level4_strategy/ -v
python -m pytest level5_export/ -v
python -m pytest level6_extractor/ -v
python -m pytest level7_generator/ -v
python -m pytest level8_documentation/ -v
python -m pytest level9_integration/ -v

# Mock 模式测试（无需 PSD 文件）
python -m pytest level9_integration/ -v --mock
```

---

## 📚 文档

| 文档 | 说明 |
|------|------|
| [USER_GUIDE.md](./docs/USER_GUIDE.md) | 用户指南 |
| [usage.md](./docs/usage.md) | 详细使用文档 |
| [CHANGELOG.md](./docs/CHANGELOG.md) | 变更日志 |
| [VERSION-PLAN.md](./docs/VERSION-PLAN.md) | 版本计划 |
| [CLAUDE.md](./docs/CLAUDE.md) | Claude 集成指南 |

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

MIT License
