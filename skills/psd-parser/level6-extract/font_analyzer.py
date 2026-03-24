"""
Level 6 - Font Analyzer
字体分析器 - 从 PSD 提取字体信息
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from skills.common import get_logger, get_error_handler, ErrorCategory, ErrorSeverity


class FontStyle(Enum):
    """字体样式"""
    NORMAL = "normal"
    BOLD = "bold"
    ITALIC = "italic"
    BOLD_ITALIC = "bold_italic"


@dataclass
class FontInfo:
    """字体信息数据类"""
    family: str
    name: str
    size: float
    weight: int
    style: str
    color: str  # hex
    line_height: float
    letter_spacing: float
    underline: bool = False
    strikeout: bool = False
    capital: str = "none"  # none/uppercase/smallcaps


class FontAnalyzer:
    """字体分析器 - 从 PSD 提取字体信息"""
    
    # 常见字体族映射
    FONT_FAMILY_MAP = {
        'arial': 'Arial',
        'helvetica': 'Helvetica',
        'times': 'Times New Roman',
        'georgia': 'Georgia',
        'verdana': 'Verdana',
        'courier': 'Courier New',
        'trebuchet': 'Trebuchet MS',
        'tahoma': 'Tahoma',
        'microsoft': 'Microsoft YaHei',
        'pingfang': 'PingFang SC',
        'hiragino': 'Hiragino Sans',
        'source han': 'Source Han Sans',
        'noto': 'Noto Sans CJK',
    }
    
    # 粗细数值映射
    WEIGHT_MAP = {
        100: 100,  # Thin
        200: 200,  # Extra Light
        300: 300,  # Light
        400: 400,  # Normal
        500: 500,  # Medium
        600: 600,  # Semi Bold
        700: 700,  # Bold
        800: 800,  # Extra Bold
        900: 900,  # Black
    }
    
    def __init__(self):
        self.logger = get_logger("FontAnalyzer")
        self.error_handler = get_error_handler()
        self._mock_mode = True
    
    def analyze(self, layer_info: Dict) -> Optional[FontInfo]:
        """
        分析单个图层的字体信息
        
        Args:
            layer_info: 图层信息字典
            
        Returns:
            FontInfo 或 None（如果不是文字图层）
        """
        try:
            # 检查是否是文字图层
            if not self._is_text_layer(layer_info):
                return None
            
            # 获取字体数据
            text_data = layer_info.get('text', {})
            
            if not text_data:
                # Mock 模式
                return self._create_mock_font(layer_info)
            
            # 提取字体信息
            return self._parse_font_info(text_data, layer_info)
            
        except Exception as e:
            self.error_handler.record(
                task="FontAnalyzer.analyze",
                error=e,
                category=ErrorCategory.PARSE_ERROR,
                severity=ErrorSeverity.MEDIUM,
                context={"layer_id": layer_info.get('id', 'unknown')}
            )
            return self._create_mock_font(layer_info)
    
    def analyze_batch(self, layers: List[Dict]) -> List[FontInfo]:
        """
        批量分析字体信息
        
        Args:
            layers: 图层信息列表
            
        Returns:
            字体信息列表
        """
        results = []
        
        for layer in layers:
            font_info = self.analyze(layer)
            if font_info:
                results.append(font_info)
        
        self.logger.info(f"批量分析字体: {len(results)}/{len(layers)} 个图层")
        
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
    
    def _parse_font_info(self, text_data: Dict, layer_info: Dict) -> FontInfo:
        """解析字体信息"""
        # 从 EngineDict 解析
        engine_dict = text_data.get('EngineDict', {})
        style_run = engine_dict.get('StyleRun', {})
        
        # 获取样式数据
        run_array = style_run.get('RunArray', [])
        if not run_array:
            return self._create_mock_font(layer_info)
        
        # 取第一个 Run 的样式
        first_style = run_array[0].get('RunData', {}).get('StyleSheet', {}).get('StyleSheetData', {})
        
        # 提取字体名称
        font_name = first_style.get('Font', {}).get('name', 'Unknown')
        family = self._normalize_font_family(font_name)
        
        # 提取字体大小
        size = first_style.get('FontSize', 12.0)
        
        # 提取粗细
        weight = first_style.get('FontWeight', 400)
        weight = self._normalize_weight(weight)
        
        # 提取样式
        style = self._determine_style(first_style)
        
        # 提取颜色
        color = self._extract_color(first_style)
        
        # 提取行高
        line_height = first_style.get('Leading', size * 1.2)
        
        # 提取字间距
        letter_spacing = first_style.get('Tracking', 0.0)
        
        # 下划线
        underline = first_style.get('Underline', False)
        
        # 删除线
        strikeout = first_style.get('Strikethrough', False)
        
        # 大小写
        capital = self._get_capital(first_style)
        
        return FontInfo(
            family=family,
            name=font_name,
            size=size,
            weight=weight,
            style=style,
            color=color,
            line_height=line_height,
            letter_spacing=letter_spacing,
            underline=underline,
            strikeout=strikeout,
            capital=capital
        )
    
    def _normalize_font_family(self, font_name: str) -> str:
        """标准化字体族名称"""
        font_lower = font_name.lower()
        
        for key, standard_name in self.FONT_FAMILY_MAP.items():
            if key in font_lower:
                return standard_name
        
        return font_name
    
    def _normalize_weight(self, weight: Any) -> int:
        """标准化粗细值"""
        try:
            weight_int = int(weight)
            return self.WEIGHT_MAP.get(weight_int, 400)
        except (ValueError, TypeError):
            # 如果是字符串（如 "Bold"）
            weight_str = str(weight).lower()
            if 'bold' in weight_str:
                if 'black' in weight_str:
                    return 900
                elif 'semi' in weight_str or 'demi' in weight_str:
                    return 600
                return 700
            elif 'medium' in weight_str:
                return 500
            elif 'light' in weight_str:
                if 'extra' in weight_str:
                    return 200
                return 300
            elif 'thin' in weight_str:
                return 100
            return 400
    
    def _determine_style(self, style_data: Dict) -> str:
        """确定字体样式"""
        is_italic = style_data.get('FontStyle', 0) & 1 == 1
        is_bold = style_data.get('FontWeight', 400) >= 700
        
        if is_bold and is_italic:
            return FontStyle.BOLD_ITALIC.value
        elif is_bold:
            return FontStyle.BOLD.value
        elif is_italic:
            return FontStyle.ITALIC.value
        else:
            return FontStyle.NORMAL.value
    
    def _extract_color(self, style_data: Dict) -> str:
        """提取颜色值"""
        try:
            # 尝试从 Color 字典提取
            color_dict = style_data.get('Color', {})
            if isinstance(color_dict, dict):
                r = color_dict.get('red', 0)
                g = color_dict.get('green', 0)
                b = color_dict.get('blue', 0)
                return f"#{int(r):02x}{int(g):02x}{int(b):02x}"
            
            # 如果是 RGBA 数组
            color_array = style_data.get('FillColor', {}).get('Values', [])
            if len(color_array) >= 3:
                r, g, b = [int(c * 255) for c in color_array[:3]]
                return f"#{r:02x}{g:02x}{b:02x}"
            
        except Exception:
            pass
        
        return "#000000"  # 默认黑色
    
    def _get_capital(self, style_data: Dict) -> str:
        """获取大小写设置"""
        caps = style_data.get('Capitalization', 0)
        if caps == 1:
            return "uppercase"
        elif caps == 2:
            return "smallcaps"
        return "none"
    
    def _create_mock_font(self, layer_info: Dict) -> FontInfo:
        """创建 Mock 字体信息（用于测试）"""
        import hashlib
        
        layer_id = layer_info.get('id', 'unknown')
        layer_name = layer_info.get('name', 'Text')
        
        # 根据图层名称生成不同的字体
        if '标题' in layer_name or 'title' in layer_name.lower() or 'heading' in layer_name.lower():
            family = "Arial"
            size = 24.0
            weight = 700
        elif '正文' in layer_name or 'body' in layer_name.lower():
            family = "PingFang SC"
            size = 14.0
            weight = 400
        else:
            family = "Microsoft YaHei"
            size = 16.0
            weight = 400
        
        # 生成唯一颜色
        hash_val = int(hashlib.md5(layer_id.encode()).hexdigest(), 16)
        r = (hash_val >> 16) & 0xFF
        g = (hash_val >> 8) & 0xFF
        b = hash_val & 0xFF
        color = f"#{r:02x}{g:02x}{b:02x}"
        
        style = "bold" if weight >= 700 else "normal"
        
        return FontInfo(
            family=family,
            name=f"{family}",
            size=size,
            weight=weight,
            style=style,
            color=color,
            line_height=size * 1.5,
            letter_spacing=0.0,
            underline=False,
            strikeout=False,
            capital="none"
        )
