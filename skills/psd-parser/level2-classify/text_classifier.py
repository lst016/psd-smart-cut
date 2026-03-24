"""
Level 2 - Text Classifier
文字类型分类器
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from skills.common import get_logger, get_config

class TextType(Enum):
    """文字类型"""
    HEADING = "heading"      # 标题
    SUBHEADING = "subheading"  # 副标题
    BODY = "body"           # 正文
    LABEL = "label"         # 标签
    BUTTON_TEXT = "button_text"  # 按钮文字
    LINK = "link"           # 链接
    PLACEHOLDER = "placeholder"  # 占位符
    CAPTION = "caption"     # 说明文字
    MENU = "menu"           # 菜单
    UNKNOWN = "unknown"

class TextLanguage(Enum):
    """文字语言"""
    CHINESE = "zh"
    ENGLISH = "en"
    MIXED = "mixed"
    UNKNOWN = "unknown"

@dataclass
class TextClassificationResult:
    """文字分类结果"""
    layer_id: str
    text_type: str
    language: str
    confidence: float
    reason: str
    extract_as_text: bool   # 是否提取为文字
    extract_as_image: bool # 是否提取为图片

class TextTypeClassifier:
    """
    文字类型分类器
    职责：判断文字类型和提取方式
    """
    
    def __init__(self):
        self.logger = get_logger("text-type-classifier")
        self.config = get_config()
    
    def classify(self, layer_info: Dict) -> TextClassificationResult:
        """
        分类文字类型
        
        Args:
            layer_info: 图层信息
        
        Returns:
            TextClassificationResult
        """
        self.logger.info(f"文字类型分类: {layer_info.get('name')}")
        
        name = layer_info.get('name', '').lower()
        
        # 基于名称猜测
        text_type = self._guess_by_name(name)
        language = self._detect_language(name)
        
        # 判断提取方式
        extract_as_text = self._should_extract_as_text(text_type)
        extract_as_image = self._should_extract_as_image(text_type)
        
        return TextClassificationResult(
            layer_id=layer_info.get('id'),
            text_type=text_type,
            language=language.value,
            confidence=0.8,
            reason=f"基于名称 '{layer_info.get('name')}' 判断",
            extract_as_text=extract_as_text,
            extract_as_image=extract_as_image
        )
    
    def _guess_by_name(self, name: str) -> str:
        """基于名称猜测类型"""
        if any(k in name for k in ['title', '标题', 'h1', 'h2', 'h3']):
            return TextType.HEADING.value
        elif any(k in name for k in ['subtitle', '副标题', 'h4']):
            return TextType.SUBHEADING.value
        elif any(k in name for k in ['btn', 'button', '按钮']):
            return TextType.BUTTON_TEXT.value
        elif any(k in name for k in ['label', '标签', 'tag']):
            return TextType.LABEL.value
        elif any(k in name for k in ['link', '链接', 'a_']):
            return TextType.LINK.value
        elif any(k in name for k in ['placeholder', '提示', 'hint']):
            return TextType.PLACEHOLDER.value
        elif any(k in name for k in ['caption', '说明', 'desc']):
            return TextType.CAPTION.value
        elif any(k in name for k in ['menu', '菜单', 'nav']):
            return TextType.MENU.value
        elif any(k in name for k in ['body', '正文', 'content', 'p_']):
            return TextType.BODY.value
        else:
            return TextType.UNKNOWN.value
    
    def _detect_language(self, name: str) -> TextLanguage:
        """检测语言"""
        # 简单判断：是否包含中文
        has_chinese = any('\u4e00' <= c <= '\u9fff' for c in name)
        has_english = any(c.isalpha() for c in name)
        
        if has_chinese and has_english:
            return TextLanguage.MIXED
        elif has_chinese:
            return TextLanguage.CHINESE
        elif has_english:
            return TextLanguage.ENGLISH
        else:
            return TextLanguage.UNKNOWN
    
    def _should_extract_as_text(self, text_type: str) -> bool:
        """判断是否提取为文字"""
        # 重要文字应该提取为文字
        important_types = [
            TextType.HEADING.value,
            TextType.SUBHEADING.value,
            TextType.BODY.value,
            TextType.LABEL.value,
            TextType.MENU.value
        ]
        return text_type in important_types
    
    def _should_extract_as_image(self, text_type: str) -> bool:
        """判断是否提取为图片"""
        # 装饰性文字可能只需要图片
        return True  # 两种都提供，让开发选择


def classify_text_type(layer_info: Dict) -> TextClassificationResult:
    """分类文字类型"""
    classifier = TextTypeClassifier()
    return classifier.classify(layer_info)
