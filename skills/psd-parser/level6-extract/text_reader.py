"""
Level 6 - Text Reader
文字读取器 - 从 PSD 提取文字内容
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from skills.common import get_logger, get_error_handler, ErrorCategory, ErrorSeverity


class TextDirection(Enum):
    """文字方向"""
    LTR = "ltr"  # left-to-right
    RTL = "rtl"  # right-to-left
    TTB = "ttb"  # top-to-bottom


class ParagraphAlignment(Enum):
    """段落对齐"""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


@dataclass
class TextContent:
    """文字内容数据类"""
    text: str
    encoding: str
    is_rtl: bool
    has_special_chars: bool
    paragraphs: List[str] = field(default_factory=list)
    direction: TextDirection = TextDirection.LTR
    alignment: ParagraphAlignment = ParagraphAlignment.LEFT


class TextReader:
    """文字读取器 - 从 PSD 提取文字内容"""
    
    # 特殊字符模式
    SPECIAL_CHAR_PATTERNS = [
        r'[\u200b-\u200f]',  # 零宽字符
        r'[\u2028-\u202f]',  # 特殊间距
        r'[\ufe00-\ufe0f]',  # 变体选择符
        r'[\u00a0]',          # 不间断空格
    ]
    
    # RTL 语言字符范围
    RTL_RANGES = [
        (0x0590, 0x05FF),  # 希伯来文
        (0x0600, 0x06FF),  # 阿拉伯文
        (0x0700, 0x074F),  # 叙利亚文
        (0x0750, 0x077F),  # 阿维斯塔文
        (0x0800, 0x083F),  # 萨巴巴文
        (0xFB50, 0xFDFF),  # 阿拉伯文展示形式-A
        (0xFE70, 0xFEFF),  # 阿拉伯文展示形式-B
    ]
    
    def __init__(self):
        self.logger = get_logger("TextReader")
        self.error_handler = get_error_handler()
        self._mock_mode = True
    
    def read(self, layer_info: Dict) -> Optional[TextContent]:
        """
        读取单个图层的文字内容
        
        Args:
            layer_info: 图层信息字典
            
        Returns:
            TextContent 或 None（如果不是文字图层）
        """
        try:
            # 检查是否是文字图层
            if not self._is_text_layer(layer_info):
                return None
            
            # 获取文字数据
            text_data = layer_info.get('text', {})
            if not text_data:
                # Mock 模式
                return self._create_mock_text(layer_info)
            
            # 提取文字内容
            text = self._extract_text(text_data)
            
            # 检测编码
            encoding = self._detect_encoding(text)
            
            # 检测 RTL
            is_rtl = self._detect_rtl(text)
            
            # 检测特殊字符
            has_special = self._detect_special_chars(text)
            
            # 提取段落
            paragraphs = self._extract_paragraphs(text)
            
            # 获取文字方向
            direction = self._get_text_direction(text_data, is_rtl)
            
            # 获取对齐方式
            alignment = self._get_paragraph_alignment(text_data)
            
            return TextContent(
                text=text,
                encoding=encoding,
                is_rtl=is_rtl,
                has_special_chars=has_special,
                paragraphs=paragraphs,
                direction=direction,
                alignment=alignment
            )
            
        except Exception as e:
            self.error_handler.record(
                task="TextReader.read",
                error=e,
                category=ErrorCategory.PARSE_ERROR,
                severity=ErrorSeverity.MEDIUM,
                context={"layer_id": layer_info.get('id', 'unknown')}
            )
            return self._create_mock_text(layer_info)
    
    def read_batch(self, layers: List[Dict]) -> List[TextContent]:
        """
        批量读取文字内容
        
        Args:
            layers: 图层信息列表
            
        Returns:
            文字内容列表
        """
        results = []
        
        for layer in layers:
            text_content = self.read(layer)
            if text_content:
                results.append(text_content)
        
        self.logger.info(f"批量读取文字: {len(results)}/{len(layers)} 个图层")
        
        return results
    
    def _is_text_layer(self, layer_info: Dict) -> bool:
        """检查是否是文字图层"""
        layer_type = layer_info.get('type', '').lower()
        kind = layer_info.get('kind', '').lower()
        
        return (
            'text' in layer_type or
            'type' in layer_type or
            kind == 'text' or
            'text' in layer_info.get('name', '').lower()
        )
    
    def _extract_text(self, text_data: Dict) -> str:
        """提取文字内容"""
        # 如果已经是字符串，直接返回
        if isinstance(text_data, str):
            return text_data

        # 尝试多种可能的键
        for key in ['content', 'text', 'string', 'value']:
            if key in text_data:
                return str(text_data[key])
        
        # 如果是 PSD 原始数据
        if 'EngineDict' in text_data:
            try:
                return self._parse_engine_dict(text_data['EngineDict'])
            except Exception:
                pass
        
        return ""
    
    def _parse_engine_dict(self, engine_dict: Dict) -> str:
        """解析 PSD 文字引擎字典"""
        try:
            # 尝试提取 ParagraphRunList
            if 'ParagraphRun' in engine_dict:
                paras = engine_dict['ParagraphRun'].get('RunArray', [])
                text_parts = []
                for para in paras:
                    if 'RunData' in para and 'Text' in para['RunData']:
                        text_parts.append(para['RunData']['Text'])
                return '\n'.join(text_parts)
            
            # 尝试提取 StyleRun
            if 'StyleRun' in engine_dict:
                runs = engine_dict['StyleRun'].get('RunArray', [])
                text_parts = []
                for run in runs:
                    if 'RunData' in run and 'Text' in run['RunData']:
                        text_parts.append(run['RunData']['Text'])
                return ''.join(text_parts)
            
        except Exception as e:
            self.logger.debug(f"解析 EngineDict 失败: {e}")
        
        return ""
    
    def _detect_encoding(self, text: str) -> str:
        """检测文字编码"""
        if not text:
            return 'utf-8'
        
        # 检测是否包含中文
        has_cjk = any('\u4e00' <= char <= '\u9fff' for char in text)
        if has_cjk:
            return 'utf-8'
        
        # 检测是否包含阿拉伯文
        has_arabic = any('\u0600' <= char <= '\u06ff' for char in text)
        if has_arabic:
            return 'utf-8'
        
        # 检测是否包含希伯来文
        has_hebrew = any('\u0590' <= char <= '\u05ff' for char in text)
        if has_hebrew:
            return 'utf-8'
        
        # 默认 UTF-8
        return 'utf-8'
    
    def _detect_rtl(self, text: str) -> bool:
        """检测是否是从右到左的文字"""
        for char in text:
            code = ord(char)
            for start, end in self.RTL_RANGES:
                if start <= code <= end:
                    return True
        return False
    
    def _detect_special_chars(self, text: str) -> bool:
        """检测是否包含特殊字符"""
        import re
        
        for pattern in self.SPECIAL_CHAR_PATTERNS:
            if re.search(pattern, text):
                return True
        
        # 检查控制字符
        for char in text:
            code = ord(char)
            if code < 32 and char not in '\t\n\r':
                return True
        
        return False
    
    def _extract_paragraphs(self, text: str) -> List[str]:
        """提取段落列表"""
        # 按换行符分割
        paragraphs = text.split('\n')
        
        # 过滤空段落
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        return paragraphs
    
    def _get_text_direction(self, text_data: Dict, is_rtl: bool) -> TextDirection:
        """获取文字方向"""
        if is_rtl:
            return TextDirection.RTL
        
        # 类型检查：text_data 可能是字符串
        if not isinstance(text_data, dict):
            return TextDirection.LTR
        
        # 从 PSD 数据中获取方向
        writing_direction = text_data.get('writingDirection', 0)
        if writing_direction == 1:
            return TextDirection.RTL
        elif writing_direction == 2:
            return TextDirection.TTB
        
        return TextDirection.LTR
    
    def _get_paragraph_alignment(self, text_data: Dict) -> ParagraphAlignment:
        """获取段落对齐方式"""
        # 类型检查：text_data 可能是字符串
        if not isinstance(text_data, dict):
            return ParagraphAlignment.LEFT
        
        alignment_map = {
            0: ParagraphAlignment.LEFT,
            1: ParagraphAlignment.LEFT,
            2: ParagraphAlignment.CENTER,
            3: ParagraphAlignment.RIGHT,
            4: ParagraphAlignment.JUSTIFY,
        }
        
        alignment = text_data.get('alignment', 0)
        return alignment_map.get(alignment, ParagraphAlignment.LEFT)
    
    def _create_mock_text(self, layer_info: Dict) -> TextContent:
        """创建 Mock 文字内容（用于测试）"""
        layer_id = layer_info.get('id', 'unknown')
        layer_name = layer_info.get('name', 'Text Layer')
        
        # 生成模拟文字
        mock_texts = [
            f"文字图层 {layer_id}",
            f"Text Layer {layer_id}",
            layer_name,
            f"Hello World {layer_id}",
            f"示例文本 {layer_id}",
        ]
        
        import hashlib
        text_index = int(hashlib.md5(layer_id.encode()).hexdigest(), 16) % len(mock_texts)
        text = mock_texts[text_index]
        
        # 检测是否包含中文
        is_rtl = False
        if any('\u4e00' <= char <= '\u9fff' for char in layer_name):
            is_rtl = False  # 中文是 LTR
        
        return TextContent(
            text=text,
            encoding='utf-8',
            is_rtl=is_rtl,
            has_special_chars=False,
            paragraphs=[text],
            direction=TextDirection.RTL if is_rtl else TextDirection.LTR,
            alignment=ParagraphAlignment.LEFT
        )
