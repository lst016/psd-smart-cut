"""
Level 2 - 分类层
AI 驱动的图层分类器
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict, is_dataclass
from enum import Enum

from skills.common import get_logger, get_config, get_error_handler, ErrorCategory

# 分类类型
class LayerType(Enum):
    """图层类型"""
    IMAGE = "image"
    TEXT = "text"
    VECTOR = "vector"
    GROUP = "group"
    DECORATOR = "decorator"
    UNKNOWN = "unknown"

@dataclass
class ClassificationResult:
    """分类结果"""
    layer_id: str
    layer_name: str
    type: str
    confidence: float
    reason: str
    sub_category: Optional[str] = None
    metadata: Dict = field(default_factory=dict)

@dataclass
class BatchClassificationResult:
    """批量分类结果"""
    success: bool
    total: int
    classified: int
    failed: int
    results: List[Dict] = field(default_factory=list)
    error: Optional[str] = None

# ============ 分类器基类 ============

class BaseClassifier:
    """分类器基类"""
    
    def __init__(self):
        self.logger = get_logger("classifier")
        self.config = get_config()
        self.error_handler = get_error_handler()
    
    def _call_ai(self, prompt: str, image_path: str) -> Dict:
        """调用 AI 进行分类"""
        # 这里应该调用 MiniMax VLM 或其他 AI API
        # 暂时返回模拟结果
        self.logger.info(f"调用 AI 分类: {image_path}")
        return {"type": "unknown", "confidence": 0.0, "reason": "待实现"}


# ============ 图片分类器 ============

class ImageClassifier(BaseClassifier):
    """
    图片分类器
    职责：判断 Layer 是否为图片类型
    """
    
    def __init__(self):
        super().__init__()
        self.threshold = self.config.get('classification.image_threshold', 0.7)
    
    def classify(self, layer_info: Dict, screenshot_path: str) -> ClassificationResult:
        """分类单个 Layer"""
        self.logger.info(f"图片分类: {layer_info.get('name')}")
        
        # 调用 AI
        result = self._call_ai(
            prompt="分析这张图片，判断它是什么类型的UI元素（按钮/图标/背景/图片/装饰）",
            image_path=screenshot_path
        )
        
        return ClassificationResult(
            layer_id=layer_info.get('id'),
            layer_name=layer_info.get('name'),
            type=result.get('type', 'image'),
            confidence=result.get('confidence', 0.0),
            reason=result.get('reason', ''),
            sub_category=result.get('sub_category'),
            metadata=layer_info
        )
    
    def classify_batch(self, layers: List[Dict], screenshot_dir: str) -> BatchClassificationResult:
        """批量分类"""
        results = []
        failed = 0
        
        for layer in layers:
            try:
                screenshot_path = os.path.join(screenshot_dir, f"{layer['id']}.png")
                result = self.classify(layer, screenshot_path)
                results.append({
                    "layer_id": result.layer_id,
                    "type": result.type,
                    "confidence": result.confidence,
                    "reason": result.reason
                })
            except Exception as e:
                failed += 1
                self.error_handler.record(
                    task="image-classifier",
                    error=e,
                    category=ErrorCategory.CLASSIFY_ERROR
                )
        
        return BatchClassificationResult(
            success=failed == 0,
            total=len(layers),
            classified=len(layers) - failed,
            failed=failed,
            results=results
        )


# ============ 文字分类器 ============

class TextClassifier(BaseClassifier):
    """
    文字分类器
    职责：判断 Layer 是否为文字类型
    """
    
    def __init__(self):
        super().__init__()
        self.threshold = self.config.get('classification.text_threshold', 0.8)
    
    def classify(self, layer_info: Dict, screenshot_path: str) -> ClassificationResult:
        """分类单个 Layer"""
        self.logger.info(f"文字分类: {layer_info.get('name')}")
        
        result = self._call_ai(
            prompt="分析这张图片，判断是否包含文字内容，文字的语言和用途",
            image_path=screenshot_path
        )
        
        return ClassificationResult(
            layer_id=layer_info.get('id'),
            layer_name=layer_info.get('name'),
            type="text",
            confidence=result.get('confidence', 0.0),
            reason=result.get('reason', ''),
            sub_category=result.get('sub_category'),
            metadata=layer_info
        )


# ============ 矢量分类器 ============

class VectorClassifier(BaseClassifier):
    """
    矢量分类器
    职责：判断 Layer 是否为矢量图形
    """
    
    def __init__(self):
        super().__init__()
        self.threshold = self.config.get('classification.vector_threshold', 0.75)
    
    def classify(self, layer_info: Dict) -> ClassificationResult:
        """分类单个 Layer（基于元数据）"""
        self.logger.info(f"矢量分类: {layer_info.get('name')}")
        
        # 矢量通常在 PSD 中有特定属性
        kind = layer_info.get('kind', '')
        
        if kind == 'vector':
            return ClassificationResult(
                layer_id=layer_info.get('id'),
                layer_name=layer_info.get('name'),
                type="vector",
                confidence=1.0,
                reason="PSD 标记为矢量图层"
            )
        
        # 尝试 AI 识别
        return ClassificationResult(
            layer_id=layer_info.get('id'),
            layer_name=layer_info.get('name'),
            type="vector",
            confidence=0.5,
            reason="需要 AI 进一步确认",
            metadata=layer_info
        )


# ============ 组分类器 ============

class GroupClassifier(BaseClassifier):
    """
    组分类器
    职责：判断 Layer 是否为图层组
    """
    
    def __init__(self):
        super().__init__()
    
    def classify(self, layer_info: Dict) -> ClassificationResult:
        """分类单个 Layer"""
        self.logger.info(f"组分类: {layer_info.get('name')}")
        
        kind = layer_info.get('kind', '')
        is_group = layer_info.get('is_group', False)
        
        if kind == 'group' or is_group:
            # 分析组内子图层
            children = layer_info.get('children', [])
            return ClassificationResult(
                layer_id=layer_info.get('id'),
                layer_name=layer_info.get('name'),
                type="group",
                confidence=1.0,
                reason=f"图层组，包含 {len(children)} 个子图层",
                sub_category=self._categorize_group(children),
                metadata=layer_info
            )
        
        return ClassificationResult(
            layer_id=layer_info.get('id'),
            layer_name=layer_info.get('name'),
            type="unknown",
            confidence=0.0,
            reason="非图层组",
            metadata=layer_info
        )
    
    def _categorize_group(self, children: List) -> str:
        """分类组的用途"""
        if not children:
            return "empty"
        elif len(children) == 1:
            return "single"
        elif len(children) <= 5:
            return "small"
        else:
            return "large"


# ============ 装饰分类器 ============

class DecoratorClassifier(BaseClassifier):
    """
    装饰分类器
    职责：判断 Layer 是否为装饰性元素
    """
    
    def __init__(self):
        super().__init__()
        self.threshold = self.config.get('classification.decorator_threshold', 0.6)
    
    def classify(self, layer_info: Dict, screenshot_path: str) -> ClassificationResult:
        """分类单个 Layer"""
        self.logger.info(f"装饰分类: {layer_info.get('name')}")
        
        result = self._call_ai(
            prompt="分析这张图片，判断是否为装饰性元素（边框/阴影/渐变/图标/分隔线）",
            image_path=screenshot_path
        )
        
        is_decorator = result.get('confidence', 0) > self.threshold
        
        return ClassificationResult(
            layer_id=layer_info.get('id'),
            layer_name=layer_info.get('name'),
            type="decorator" if is_decorator else "content",
            confidence=result.get('confidence', 0.0),
            reason=result.get('reason', ''),
            sub_category=result.get('sub_category'),
            metadata=layer_info
        )


# ============ 统一分类器 ============

class LayerClassifier:
    """
    统一分类器
    职责：协调所有分类器进行分类
    """
    
    def __init__(self, mock_mode: bool = False):
        self.logger = get_logger("layer-classifier")
        self.mock_mode = mock_mode
        self.image_classifier = ImageClassifier()
        self.text_classifier = TextClassifier()
        self.vector_classifier = VectorClassifier()
        self.group_classifier = GroupClassifier()
        self.decorator_classifier = DecoratorClassifier()

    def _normalize_layer_info(self, layer_info: Any) -> Dict[str, Any]:
        """Accept dicts and dataclass-style layer objects from older tests."""
        if isinstance(layer_info, dict):
            data = dict(layer_info)
        elif hasattr(layer_info, "to_dict"):
            data = layer_info.to_dict()
        elif is_dataclass(layer_info):
            data = asdict(layer_info)
        else:
            data = {
                key: value for key, value in vars(layer_info).items()
                if not key.startswith("_")
            }

        if "layer_id" not in data and "id" in data:
            data["layer_id"] = data["id"]
        if "type" not in data and "kind" in data:
            data["type"] = data["kind"]
        if "bbox" not in data and all(key in data for key in ("left", "top", "width", "height")):
            data["bbox"] = {
                "x": data.get("left", 0),
                "y": data.get("top", 0),
                "width": data.get("width", 0),
                "height": data.get("height", 0),
            }

        return data
    
    def classify(self, layer_info: Dict, screenshot_path: Optional[str] = None) -> ClassificationResult:
        layer_info = self._normalize_layer_info(layer_info)
        """分类单个 Layer"""
        kind = layer_info.get('kind', 'unknown')
        
        # 1. 首先检查是否为组
        if kind == 'group':
            return self.group_classifier.classify(layer_info)
        
        # 2. 检查是否为矢量
        if kind == 'vector':
            return self.vector_classifier.classify(layer_info)
        
        # 3. 其他类型需要 AI 辅助判断
        if screenshot_path and os.path.exists(screenshot_path):
            # 调用多个分类器，综合判断
            image_result = self.image_classifier.classify(layer_info, screenshot_path)
            text_result = self.text_classifier.classify(layer_info, screenshot_path)
            decorator_result = self.decorator_classifier.classify(layer_info, screenshot_path)
            
            # 选择置信度最高的
            results = [
                (image_result, image_result.confidence),
                (text_result, text_result.confidence),
                (decorator_result, decorator_result.confidence)
            ]
            results.sort(key=lambda x: x[1], reverse=True)
            
            return results[0][0]
        else:
            # 无截图，基于元数据判断
            return self._classify_by_metadata(layer_info)
    
    def _classify_by_metadata(self, layer_info: Dict) -> ClassificationResult:
        """基于元数据分类"""
        kind = layer_info.get('kind', 'unknown')
        
        if kind == 'image':
            return ClassificationResult(
                layer_id=layer_info.get('id'),
                layer_name=layer_info.get('name'),
                type="image",
                confidence=0.8,
                reason="PSD 标记为像素图层"
            )
        elif kind == 'text':
            return ClassificationResult(
                layer_id=layer_info.get('id'),
                layer_name=layer_info.get('name'),
                type="text",
                confidence=0.9,
                reason="PSD 标记为文字图层"
            )
        else:
            return ClassificationResult(
                layer_id=layer_info.get('id'),
                layer_name=layer_info.get('name'),
                type="unknown",
                confidence=0.0,
                reason="无法确定类型",
                metadata=layer_info
            )
    
    def classify_batch(self, layers: List[Dict], screenshot_dir: str = "") -> BatchClassificationResult:
        """批量分类"""
        results = []
        failed = 0
        
        for layer in layers:
            normalized_layer = self._normalize_layer_info(layer)
            try:
                screenshot_path = os.path.join(screenshot_dir, f"{normalized_layer['id']}.png")
                result = self.classify(
                    normalized_layer,
                    screenshot_path if os.path.exists(screenshot_path) else None
                )
                results.append({
                    "layer_id": result.layer_id,
                    "type": result.type,
                    "confidence": result.confidence,
                    "reason": result.reason,
                    "sub_category": result.sub_category
                })
            except Exception as e:
                failed += 1
                self.logger.error(f"分类失败: {layer.get('name')}: {e}")
        
        return BatchClassificationResult(
            success=failed == 0,
            total=len(layers),
            classified=len(layers) - failed,
            failed=failed,
            results=results
        )


# ============ 便捷函数 ============

def classify_layers(layers: List[Dict], screenshot_dir: str) -> BatchClassificationResult:
    """分类 Layers"""
    classifier = LayerClassifier()
    return classifier.classify_batch(layers, screenshot_dir)
