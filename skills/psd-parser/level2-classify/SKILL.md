# Level 2 - 分类层

## 技能名称和用途

**技能名称：** `level2-classify`  
**所属模块：** `skills/psd-parser/level2-classify`  
**用途：** AI 驱动的 PSD 图层分类器，将 PSD 文件中的图层自动分类为图片、文字、矢量、组或装饰图层。

**核心功能：**
- 自动识别图层类型（图片/文字/矢量/组/装饰）
- 图片子类型细分（按钮、图标、背景、插画等）
- 文字类型判断（标题、正文、标签、按钮文字等）
- 批量分类支持
- AI 集成能力

---

## 分类器架构

```
level2-classify/
├── __init__.py              # 模块导出
├── classifier.py           # 核心分类器（5个分类器）
├── image_classifier.py     # 图片类型细分
└── text_classifier.py      # 文字类型细分
```

### 核心组件

| 组件 | 文件 | 说明 |
|------|------|------|
| LayerType | classifier.py | 图层类型枚举 |
| ClassificationResult | classifier.py | 单个分类结果 |
| BatchClassificationResult | classifier.py | 批量分类结果 |
| ImageSubCategory | image_classifier.py | 图片子类型枚举 |
| TextType | text_classifier.py | 文字类型枚举 |
| TextLanguage | text_classifier.py | 文字语言枚举 |

---

## 5 个分类器职责

### 1. ImageClassifier（图片分类器）

**职责：** 判断图层是否为图片类型

**分类逻辑：**
- 调用 AI 分析图层截图
- 基于启发式规则辅助判断（名称匹配）
- 返回分类结果和置信度

**配置参数：**
- `image_threshold`: 图片分类阈值（默认 0.7）

**输出：** `ClassificationResult`

---

### 2. TextClassifier（文字分类器）

**职责：** 判断图层是否为文字类型

**分类逻辑：**
- 检测图层是否有文字内容
- 调用 AI 分析文字属性
- 返回分类结果

**输出：** `ClassificationResult`

---

### 3. VectorClassifier（矢量分类器）

**职责：** 判断图层是否为矢量图层（形状、路径）

**分类逻辑：**
- 检测矢量标记（如 Bbox、VectorData）
- AI 辅助判断矢量属性
- 返回分类结果

**输出：** `ClassificationResult`

---

### 4. GroupClassifier（组分类器）

**职责：** 判断图层是否为图层组（Group）

**分类逻辑：**
- 检测图层节点头部标记（SectionDividerSetting）
- 分析组内子图层数量
- AI 辅助判断组类型

**输出：** `ClassificationResult`

---

### 5. DecoratorClassifier（装饰分类器）

**职责：** 判断图层是否为装饰性图层（分割线、背景、形状等）

**分类逻辑：**
- 检测装饰性特征（纯色填充、无文字）
- AI 辅助判断装饰类型
- 返回分类结果

**输出：** `ClassificationResult`

---

## 使用示例

### 基本使用

```python
from skills.psd_parser.level2_classify import (
    LayerClassifier,
    classify_layers,
    ImageTypeClassifier,
    TextTypeClassifier
)

# 初始化分类器
classifier = LayerClassifier()

# 分类单个图层
layer_info = {
    'id': 'layer_001',
    'name': 'btn_submit',
    'type': 'image'
}
result = classifier.classify(layer_info, screenshot_path='./screenshot.png')
print(f"分类结果: {result.type}, 置信度: {result.confidence}")

# 批量分类
layers = [
    {'id': 'layer_001', 'name': 'logo', 'type': 'image'},
    {'id': 'layer_002', 'name': 'title', 'type': 'text'},
    {'id': 'layer_003', 'name': 'bg_shape', 'type': 'shape'}
]
batch_result = classifier.classify_batch(layers, screenshot_dir='./screenshots')
print(f"成功: {batch_result.classified}/{batch_result.total}")
```

### 图片子类型细分

```python
from skills.psd_parser.level2_classify import (
    ImageTypeClassifier,
    ImageSubCategory,
    classify_image_type
)

image_classifier = ImageTypeClassifier()

# 细分图片类型
layer_info = {'id': 'layer_001', 'name': 'icon_home'}
result = image_classifier.classify(layer_info, screenshot_path='./icon.png')

print(f"子类型: {result.sub_category}")
print(f"可交互: {result.is_interactive}")
print(f"需导出: {result.needs_export}")
```

### 文字类型细分

```python
from skills.psd_parser.level2_classify import (
    TextTypeClassifier,
    TextType,
    TextLanguage,
    classify_text_type
)

text_classifier = TextTypeClassifier()

# 细分文字类型
layer_info = {'id': 'layer_001', 'name': 'title_main'}
result = text_classifier.classify(layer_info)

print(f"文字类型: {result.text_type}")
print(f"语言: {result.language}")
print(f"提取为文字: {result.extract_as_text}")
print(f"提取为图片: {result.extract_as_image}")
```

### 快捷函数

```python
from skills.psd_parser.level2_classify import (
    classify_layers,
    classify_image_type,
    classify_text_type
)

# 快捷分类
results = classify_layers(layers, screenshot_dir='./screenshots')

# 快捷图片分类
img_result = classify_image_type(layer_info, screenshot_path='./img.png')

# 快捷文字分类
txt_result = classify_text_type(layer_info)
```

---

## AI 集成说明

### AI 分类流程

```
图层信息 + 截图 → AI 模型 → 分类结果
                            ↓
                       置信度分数
```

### 当前 AI 集成

**分类器基类 `BaseClassifier` 提供 AI 调用接口：**

```python
class BaseClassifier:
    def _call_ai(self, prompt: str, image_path: str) -> Dict:
        """调用 AI 进行分类"""
        # 调用 MiniMax VLM 或其他 AI API
        return {"type": "unknown", "confidence": 0.0, "reason": "待实现"}
```

### 扩展 AI 能力

如需启用真实 AI 分类，实现 `_call_ai` 方法：

```python
class ImageClassifier(BaseClassifier):
    def _call_ai(self, prompt: str, image_path: str) -> Dict:
        # 调用 MiniMax VLM
        # result = minimax_vlm.analyze(
        #     image=image_path,
        #     prompt=prompt
        # )
        return {
            "type": "button",
            "confidence": 0.95,
            "reason": "蓝色渐变背景，符合按钮样式"
        }
```

### 当前实现状态

- ✅ 基础分类器架构
- ✅ 启发式规则（名称匹配）
- ⏳ AI 集成（待接入 MiniMax VLM）
- ⏳ 置信度校准（待优化）

---

## 枚举值参考

### LayerType（图层类型）

| 值 | 说明 |
|----|------|
| `IMAGE` | 图片类型 |
| `TEXT` | 文字类型 |
| `VECTOR` | 矢量类型 |
| `GROUP` | 组类型 |
| `DECORATOR` | 装饰类型 |
| `UNKNOWN` | 未知类型 |

### ImageSubCategory（图片子类型）

| 值 | 说明 | 可交互 |
|----|------|--------|
| `BUTTON` | 按钮 | ✅ |
| `ICON` | 图标 | ✅ |
| `BACKGROUND` | 背景 | ❌ |
| `PHOTO` | 照片 | ❌ |
| `ILLUSTRATION` | 插画 | ❌ |
| `DECORATION` | 装饰 | ❌ |
| `COMPONENT` | 组件 | ✅ |
| `BANNER` | 横幅 | ❌ |
| `CARD` | 卡片 | ✅ |
| `AVATAR` | 头像 | ✅ |
| `UNKNOWN` | 未知 | ❌ |

### TextType（文字类型）

| 值 | 说明 | 提取方式 |
|----|------|----------|
| `HEADING` | 标题 | 文字 |
| `SUBHEADING` | 副标题 | 文字 |
| `BODY` | 正文 | 文字 |
| `LABEL` | 标签 | 文字 |
| `BUTTON_TEXT` | 按钮文字 | 文字 |
| `LINK` | 链接 | 文字 |
| `PLACEHOLDER` | 占位符 | 文字 |
| `CAPTION` | 说明文字 | 文字 |
| `MENU` | 菜单 | 文字 |
| `UNKNOWN` | 未知 | 文字 |

### TextLanguage（文字语言）

| 值 | 说明 |
|----|------|
| `CHINESE` | 中文 |
| `ENGLISH` | 英文 |
| `MIXED` | 混合 |
| `UNKNOWN` | 未知 |

---

## 维护记录

- **2026-03-24:** 初始创建，包含 5 个分类器 + 图片/文字细分
