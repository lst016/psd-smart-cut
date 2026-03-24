"""
Level 2 - Image Classifier
图片类型分类器
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from skills.common import get_logger, get_config

class ImageSubCategory(Enum):
    """图片子类型"""
    BUTTON = "button"
    ICON = "icon"
    BACKGROUND = "background"
    PHOTO = "photo"
    ILLUSTRATION = "illustration"
    DECORATION = "decoration"
    COMPONENT = "component"
    BANNER = "banner"
    CARD = "card"
    AVATAR = "avatar"
    UNKNOWN = "unknown"

@dataclass
class ImageClassificationResult:
    """图片分类结果"""
    layer_id: str
    sub_category: str
    confidence: float
    reason: str
    is_interactive: bool  # 是否可交互
    needs_export: bool    # 是否需要导出

class ImageTypeClassifier:
    """
    图片类型细分分类器
    职责：将图片图层细分为具体类型
    """
    
    def __init__(self):
        self.logger = get_logger("image-type-classifier")
        self.config = get_config()
    
    def classify(self, layer_info: Dict, screenshot_path: str) -> ImageClassificationResult:
        """
        分类图片类型
        
        Args:
            layer_info: 图层信息
            screenshot_path: 截图路径
        
        Returns:
            ImageClassificationResult
        """
        self.logger.info(f"图片类型分类: {layer_info.get('name')}")
        
        # 调用 AI 进行细分
        # 这里应该调用 MiniMax VLM
        # 暂时返回模拟结果
        
        name = layer_info.get('name', '').lower()
        
        # 基于名称的启发式判断
        sub_category = self._guess_by_name(name)
        is_interactive = self._is_interactive(sub_category)
        needs_export = self._needs_export(sub_category)
        
        return ImageClassificationResult(
            layer_id=layer_info.get('id'),
            sub_category=sub_category,
            confidence=0.8,
            reason=f"基于名称 '{layer_info.get('name')}' 判断",
            is_interactive=is_interactive,
            needs_export=needs_export
        )
    
    def _guess_by_name(self, name: str) -> str:
        """基于名称猜测类型"""
        if any(k in name for k in ['btn', 'button', '按钮']):
            return ImageSubCategory.BUTTON.value
        elif any(k in name for k in ['icon', '图标', 'icon_']):
            return ImageSubCategory.ICON.value
        elif any(k in name for k in ['bg', 'background', '背景', '底图']):
            return ImageSubCategory.BACKGROUND.value
        elif any(k in name for k in ['photo', '图片', 'img_']):
            return ImageSubCategory.PHOTO.value
        elif any(k in name for k in ['illustration', '插画', 'illus']):
            return ImageSubCategory.ILLUSTRATION.value
        elif any(k in name for k in ['banner', '轮播', 'slider']):
            return ImageSubCategory.BANNER.value
        elif any(k in name for k in ['card', '卡片']):
            return ImageSubCategory.CARD.value
        elif any(k in name for k in ['avatar', '头像', 'user_']):
            return ImageSubCategory.AVATAR.value
        elif any(k in name for k in ['decoration', '装饰', 'deco']):
            return ImageSubCategory.DECORATION.value
        else:
            return ImageSubCategory.UNKNOWN.value
    
    def _is_interactive(self, sub_category: str) -> bool:
        """判断是否可交互"""
        interactive_types = [
            ImageSubCategory.BUTTON.value,
            ImageSubCategory.ICON.value,
            ImageSubCategory.CARD.value
        ]
        return sub_category in interactive_types
    
    def _needs_export(self, sub_category: str) -> bool:
        """判断是否需要导出"""
        # 背景通常作为 CSS 背景，不需要单独导出
        no_export_types = [
            ImageSubCategory.BACKGROUND.value
        ]
        return sub_category not in no_export_types


def classify_image_type(layer_info: Dict, screenshot_path: str) -> ImageClassificationResult:
    """分类图片类型"""
    classifier = ImageTypeClassifier()
    return classifier.classify(layer_info, screenshot_path)
