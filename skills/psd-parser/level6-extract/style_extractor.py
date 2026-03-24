"""
Level 6 - Style Extractor
样式提取器 - 从 PSD 提取图层样式
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from skills.common import get_logger, get_error_handler, ErrorCategory, ErrorSeverity


@dataclass
class ShadowEffect:
    """阴影效果"""
    color: str  # hex
    opacity: float
    offset_x: int
    offset_y: int
    blur: int
    spread: int
    blend_mode: str


@dataclass
class BorderEffect:
    """描边效果"""
    color: str  # hex
    size: int
    position: str  # inside/outside/center
    blend_mode: str


@dataclass
class GradientEffect:
    """渐变效果"""
    colors: List[str]  # hex colors
    stops: List[float]  # 0.0 - 1.0
    angle: float
    type: str  # linear/radial/angle


@dataclass
class LayerStyle:
    """图层样式数据类"""
    opacity: float
    blend_mode: str
    fill_opacity: float
    effects: List[str]  # 可用的效果列表
    shadow: Optional[ShadowEffect] = None
    border: Optional[BorderEffect] = None
    gradient: Optional[GradientEffect] = None
    glow: Optional[Dict] = None
    inner_shadow: Optional[Dict] = None
    blur: Optional[Dict] = None


class StyleExtractor:
    """样式提取器 - 从 PSD 提取图层样式"""
    
    # 混合模式映射
    BLEND_MODE_MAP = {
        'norm': 'normal',
        'dark': 'darken',
        'mul': 'multiply',
        'idiv': 'color-dodge',
        'lburn': 'linear-burn',
        'dtest': 'difference',
        'smud': 'exclusion',
        'hrit': 'hue',
        'sat': 'saturation',
        'colr': 'color',
        'lum': 'luminosity',
        'over': 'overlay',
        'scrn': 'screen',
        'hdif': 'hard-light',
        'sdif': 'soft-light',
        'lite': 'lighten',
        'diff': 'difference',
        'diss': 'dissolve',
    }
    
    def __init__(self):
        self.logger = get_logger("StyleExtractor")
        self.error_handler = get_error_handler()
        self._mock_mode = True
    
    def extract(self, layer_info: Dict) -> LayerStyle:
        """
        提取单个图层的样式
        
        Args:
            layer_info: 图层信息字典
            
        Returns:
            LayerStyle
        """
        try:
            # 获取样式数据
            style_data = layer_info.get('style', {})
            
            # 提取基本信息（优先从 style dict 读取，兼容 mock 数据）
            opacity = self._extract_opacity(layer_info, style_data)
            blend_mode = self._extract_blend_mode(layer_info)
            fill_opacity = self._extract_fill_opacity(layer_info, style_data)
            
            # 提取效果
            effects = self._detect_effects(style_data)
            
            # 提取阴影
            shadow = self._extract_shadow(style_data)
            
            # 提取描边
            border = self._extract_border(style_data)
            
            # 提取渐变
            gradient = self._extract_gradient(style_data)
            
            return LayerStyle(
                opacity=opacity,
                blend_mode=blend_mode,
                fill_opacity=fill_opacity,
                effects=effects,
                shadow=shadow,
                border=border,
                gradient=gradient
            )
            
        except Exception as e:
            self.error_handler.record(
                task="StyleExtractor.extract",
                error=e,
                category=ErrorCategory.PARSE_ERROR,
                severity=ErrorSeverity.MEDIUM,
                context={"layer_id": layer_info.get('id', 'unknown')}
            )
            return self._create_mock_style(layer_info)
    
    def extract_batch(self, layers: List[Dict]) -> List[LayerStyle]:
        """
        批量提取图层样式
        
        Args:
            layers: 图层信息列表
            
        Returns:
            样式列表
        """
        results = []
        
        for layer in layers:
            style = self.extract(layer)
            results.append(style)
        
        self.logger.info(f"批量提取样式: {len(results)}/{len(layers)} 个图层")
        
        return results
    
    def _extract_opacity(self, layer_info: Dict, style_data: Dict = None) -> float:
        """提取不透明度"""
        # 优先从 style dict 读取（mock 数据结构）
        if style_data and 'opacity' in style_data:
            opacity = style_data['opacity']
        else:
            opacity = layer_info.get('opacity', layer_info.get('style', {}).get('opacity', 1.0))
        
        # PSD 中 opacity 可能是 0-255 或 0-1
        if opacity > 1:
            opacity = opacity / 255.0
        
        return round(opacity, 2)
    
    def _extract_blend_mode(self, layer_info: Dict) -> str:
        """提取混合模式"""
        blend_mode = layer_info.get('blendMode', 'norm')
        return self.BLEND_MODE_MAP.get(blend_mode, 'normal')
    
    def _extract_fill_opacity(self, layer_info: Dict, style_data: Dict = None) -> float:
        """提取填充不透明度"""
        # 优先从 style dict 读取（mock 数据结构）
        if style_data and 'fillOpacity' in style_data:
            fill_opacity = style_data['fillOpacity']
        else:
            fill_opacity = layer_info.get('fillOpacity', layer_info.get('style', {}).get('fillOpacity', 1.0))
        
        if fill_opacity > 1:
            fill_opacity = fill_opacity / 255.0
        
        return round(fill_opacity, 2)
    
    def _detect_effects(self, style_data: Dict) -> List[str]:
        """检测可用的效果"""
        effects = []
        
        if 'shadow' in style_data or 'DropShadow' in style_data:
            effects.append('shadow')
        
        if 'innerShadow' in style_data or 'InnerShadow' in style_data:
            effects.append('inner_shadow')
        
        if 'border' in style_data or 'Stroke' in style_data:
            effects.append('border')
        
        if 'gradient' in style_data or 'GradientFill' in style_data:
            effects.append('gradient')
        
        if 'glow' in style_data or 'OuterGlow' in style_data:
            effects.append('glow')
        
        if 'blur' in style_data or 'GaussianBlur' in style_data:
            effects.append('blur')
        
        if 'bevel' in style_data or 'Bevel' in style_data:
            effects.append('bevel')
        
        if not effects:
            effects.append('none')
        
        return effects
    
    def _extract_shadow(self, style_data: Dict) -> Optional[ShadowEffect]:
        """提取阴影效果"""
        try:
            # 尝试不同的键名
            shadow_data = (
                style_data.get('shadow') or
                style_data.get('DropShadow', {}) or
                style_data.get('DropShadowType', {})
            )
            
            if not shadow_data:
                return None
            
            # 提取颜色
            color_data = shadow_data.get('Color', shadow_data.get('colour', {}))
            color = self._parse_color(color_data)
            
            # 提取不透明度
            opacity = shadow_data.get('Opacity', 100)
            if opacity > 1:
                opacity = opacity / 100.0
            
            # 提取偏移
            offset_x = shadow_data.get('OffsetX', shadow_data.get('offset', {}).get('x', 0))
            offset_y = shadow_data.get('OffsetY', shadow_data.get('offset', {}).get('y', 0))
            
            # 提取模糊
            blur = shadow_data.get('Blur', shadow_data.get('GaussianBlur', 0))
            
            # 提取扩展
            spread = shadow_data.get('Spread', 0)
            
            # 提取混合模式
            blend_mode = shadow_data.get('BlendMode', 'norm')
            blend_mode = self.BLEND_MODE_MAP.get(blend_mode, 'normal')
            
            return ShadowEffect(
                color=color,
                opacity=opacity,
                offset_x=offset_x,
                offset_y=offset_y,
                blur=blur,
                spread=spread,
                blend_mode=blend_mode
            )
            
        except Exception as e:
            self.logger.debug(f"提取阴影失败: {e}")
            return None
    
    def _extract_border(self, style_data: Dict) -> Optional[BorderEffect]:
        """提取描边效果"""
        try:
            border_data = (
                style_data.get('border') or
                style_data.get('Stroke', {})
            )
            
            if not border_data:
                return None
            
            # 提取颜色
            color_data = border_data.get('Color', {})
            color = self._parse_color(color_data)
            
            # 提取大小
            size = border_data.get('Size', border_data.get('strokeWidth', 1))
            
            # 提取位置
            position = border_data.get('Position', 'inside')
            
            # 提取混合模式
            blend_mode = border_data.get('BlendMode', 'norm')
            blend_mode = self.BLEND_MODE_MAP.get(blend_mode, 'normal')
            
            return BorderEffect(
                color=color,
                size=size,
                position=position,
                blend_mode=blend_mode
            )
            
        except Exception as e:
            self.logger.debug(f"提取描边失败: {e}")
            return None
    
    def _extract_gradient(self, style_data: Dict) -> Optional[GradientEffect]:
        """提取渐变效果"""
        try:
            gradient_data = (
                style_data.get('gradient') or
                style_data.get('GradientFill', {})
            )
            
            if not gradient_data:
                return None
            
            # 提取颜色
            colors_data = gradient_data.get('Colors', gradient_data.get('stops', []))
            colors = []
            stops = []
            
            for i, stop in enumerate(colors_data):
                color = self._parse_color(stop.get('Color', stop.get('colour', {})))
                colors.append(color)
                stops.append(stop.get('location', i * 100) / 100.0)
            
            if not colors:
                colors = ['#000000', '#ffffff']
                stops = [0.0, 1.0]
            
            # 提取角度
            angle = gradient_data.get('Angle', gradient_data.get('gradientAngle', 0))
            
            # 提取类型
            gradient_type = gradient_data.get('Type', gradient_data.get('gradientType', 'linear'))
            
            return GradientEffect(
                colors=colors,
                stops=stops,
                angle=angle,
                type=gradient_type
            )
            
        except Exception as e:
            self.logger.debug(f"提取渐变失败: {e}")
            return None
    
    def _parse_color(self, color_data: Any) -> str:
        """解析颜色值"""
        if isinstance(color_data, str):
            return color_data
        
        if isinstance(color_data, dict):
            # RGBA 格式
            r = color_data.get('red', color_data.get('r', 0))
            g = color_data.get('green', color_data.get('g', 0))
            b = color_data.get('blue', color_data.get('b', 0))
            return f"#{int(r):02x}{int(g):02x}{int(b):02x}"
        
        if isinstance(color_data, (list, tuple)) and len(color_data) >= 3:
            r, g, b = color_data[:3]
            return f"#{int(r):02x}{int(g):02x}{int(b):02x}"
        
        return "#000000"
    
    def _create_mock_style(self, layer_info: Dict) -> LayerStyle:
        """创建 Mock 样式（用于测试）"""
        import hashlib
        
        layer_id = layer_info.get('id', 'unknown')
        layer_name = layer_info.get('name', 'Layer')
        layer_type = layer_info.get('type', 'unknown').lower()
        
        # 根据图层类型生成不同样式
        effects = []
        shadow = None
        border = None
        gradient = None
        
        if 'button' in layer_name.lower() or 'btn' in layer_name.lower():
            effects = ['shadow', 'border']
            shadow = ShadowEffect(
                color="#000000",
                opacity=0.2,
                offset_x=0,
                offset_y=4,
                blur=8,
                spread=0,
                blend_mode="normal"
            )
            border = BorderEffect(
                color="#333333",
                size=1,
                position="inside",
                blend_mode="normal"
            )
        elif 'background' in layer_name.lower() or 'bg' in layer_name.lower():
            effects = ['gradient']
            gradient = GradientEffect(
                colors=['#ffffff', '#f0f0f0'],
                stops=[0.0, 1.0],
                angle=180,
                type='linear'
            )
        else:
            effects = ['none']
        
        # 生成唯一颜色
        hash_val = int(hashlib.md5(layer_id.encode()).hexdigest(), 16)
        r = (hash_val >> 16) & 0xFF
        g = (hash_val >> 8) & 0xFF
        b = hash_val & 0xFF
        color = f"#{r:02x}{g:02x}{b:02x}"
        
        return LayerStyle(
            opacity=1.0,
            blend_mode='normal',
            fill_opacity=1.0,
            effects=effects,
            shadow=shadow,
            border=border,
            gradient=gradient
        )
