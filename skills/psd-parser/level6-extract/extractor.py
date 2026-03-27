"""
Level 6 - Extractor
统一提取器 - 协调所有提取模块，输出完整提取结果
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from skills.common import get_logger, get_error_handler, ErrorCategory, ErrorSeverity

from .text_reader import TextReader, TextContent, TextDirection, ParagraphAlignment
from .font_analyzer import FontAnalyzer, FontInfo, FontStyle
from .style_extractor import StyleExtractor, LayerStyle, ShadowEffect, BorderEffect, GradientEffect
from .position_reader import PositionReader, PositionData


@dataclass
class ExtractionResult:
    """提取结果数据类"""
    layer_id: str
    layer_name: str
    layer_type: str
    text: Optional[TextContent]
    font: Optional[FontInfo]
    style: Optional[LayerStyle]
    position: Optional[PositionData]
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return "error" not in self.metadata
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        result = {
            'layer_id': self.layer_id,
            'layer_name': self.layer_name,
            'layer_type': self.layer_type,
            'text': None,
            'font': None,
            'style': None,
            'position': None,
            'metadata': self.metadata
        }
        
        if self.text:
            result['text'] = {
                'text': self.text.text,
                'encoding': self.text.encoding,
                'is_rtl': self.text.is_rtl,
                'has_special_chars': self.text.has_special_chars,
                'paragraphs': self.text.paragraphs,
                'direction': self.text.direction.value,
                'alignment': self.text.alignment.value
            }
        
        if self.font:
            result['font'] = {
                'family': self.font.family,
                'name': self.font.name,
                'size': self.font.size,
                'weight': self.font.weight,
                'style': self.font.style,
                'color': self.font.color,
                'line_height': self.font.line_height,
                'letter_spacing': self.font.letter_spacing,
                'underline': self.font.underline,
                'strikeout': self.font.strikeout,
                'capital': self.font.capital
            }
        
        if self.style:
            result['style'] = {
                'opacity': self.style.opacity,
                'blend_mode': self.style.blend_mode,
                'fill_opacity': self.style.fill_opacity,
                'effects': self.style.effects,
                'shadow': None,
                'border': None,
                'gradient': None
            }
            
            if self.style.shadow:
                result['style']['shadow'] = {
                    'color': self.style.shadow.color,
                    'opacity': self.style.shadow.opacity,
                    'offset_x': self.style.shadow.offset_x,
                    'offset_y': self.style.shadow.offset_y,
                    'blur': self.style.shadow.blur,
                    'spread': self.style.shadow.spread,
                    'blend_mode': self.style.shadow.blend_mode
                }
            
            if self.style.border:
                result['style']['border'] = {
                    'color': self.style.border.color,
                    'size': self.style.border.size,
                    'position': self.style.border.position,
                    'blend_mode': self.style.border.blend_mode
                }
            
            if self.style.gradient:
                result['style']['gradient'] = {
                    'colors': self.style.gradient.colors,
                    'stops': self.style.gradient.stops,
                    'angle': self.style.gradient.angle,
                    'type': self.style.gradient.type
                }
        
        if self.position:
            result['position'] = {
                'x': self.position.x,
                'y': self.position.y,
                'width': self.position.width,
                'height': self.position.height,
                'rotation': self.position.rotation,
                'anchor': self.position.anchor.value if hasattr(self.position.anchor, 'value') else str(self.position.anchor),
                'alignment': self.position.alignment.value if hasattr(self.position.alignment, 'value') else str(self.position.alignment),
                'breakpoints': [
                    {'name': bp.name, 'x': bp.x, 'y': bp.y, 'width': bp.width, 'height': bp.height}
                    for bp in self.position.breakpoints
                ]
            }
        
        return result


class Extractor:
    """统一提取器 - 协调所有提取模块"""
    
    def __init__(self, canvas_width: int = 1440, canvas_height: int = 900, mock_mode: bool = False):
        self.logger = get_logger("Extractor")
        self.error_handler = get_error_handler()
        self.mock_mode = mock_mode
        self.text_reader = TextReader()
        self.font_analyzer = FontAnalyzer()
        self.style_extractor = StyleExtractor()
        self.position_reader = PositionReader(canvas_width, canvas_height)
    
    def extract(self, layer_info: Dict) -> ExtractionResult:
        """提取单个图层的完整信息"""
        layer_id = layer_info.get('id', 'unknown')
        layer_name = layer_info.get('name', 'Unknown')
        layer_type = layer_info.get('type') or layer_info.get('kind', 'unknown')
        
        self.logger.info(f"提取图层: {layer_id} - {layer_name}")
        
        try:
            text = self.text_reader.read(layer_info)
            font = self.font_analyzer.analyze(layer_info)
            style = self.style_extractor.extract(layer_info)
            position = self.position_reader.read(layer_info)
            metadata = self._build_metadata(layer_info, text, font, style, position)
            
            return ExtractionResult(
                layer_id=layer_id, layer_name=layer_name, layer_type=layer_type,
                text=text, font=font, style=style, position=position, metadata=metadata
            )
            
        except Exception as e:
            self.error_handler.record(
                task="Extractor.extract",
                error=e,
                category=ErrorCategory.PARSE_ERROR,
                severity=ErrorSeverity.HIGH,
                context={"layer_id": layer_id}
            )
            return ExtractionResult(
                layer_id=layer_id, layer_name=layer_name, layer_type=layer_type,
                text=None, font=None, style=None, position=None,
                metadata={'error': str(e)}
            )
    
    def extract_batch(self, layers: List[Dict]) -> List[ExtractionResult]:
        """批量提取图层信息"""
        self.logger.info(f"批量提取: {len(layers)} 个图层")
        results = []
        for layer in layers:
            result = self.extract(layer)
            results.append(result)
        
        stats = self._compute_stats(results)
        self.logger.info(f"批量提取完成: 总={len(results)}, 文字={stats['text_count']}, 字体={stats['font_count']}, 样式={stats['style_count']}, 位置={stats['position_count']}")
        return results
    
    def extract_by_type(self, layers: List[Dict], layer_type: str) -> List[ExtractionResult]:
        """按类型提取图层"""
        filtered = [layer for layer in layers if layer.get('type', '').lower() == layer_type.lower()]
        self.logger.info(f"按类型提取: type={layer_type}, count={len(filtered)}")
        return self.extract_batch(filtered)
    
    def _build_metadata(self, layer_info: Dict, text, font, style, position) -> Dict:
        """构建元数据"""
        metadata = {'source': 'psd-smart-cut', 'version': 'v0.6'}
        metadata['is_text_layer'] = text is not None
        if style:
            metadata['has_effects'] = len(style.effects) > 0 and 'none' not in style.effects
            metadata['effects_list'] = [e for e in style.effects if e != 'none']
        if position and position.breakpoints:
            metadata['responsive'] = True
            metadata['breakpoint_names'] = [bp.name for bp in position.breakpoints]
        metadata['has_raw_data'] = bool(layer_info.get('text') or layer_info.get('style'))
        return metadata
    
    def _compute_stats(self, results: List[ExtractionResult]) -> Dict:
        """计算统计信息"""
        stats = {'total': len(results), 'text_count': 0, 'font_count': 0, 'style_count': 0, 'position_count': 0}
        for result in results:
            if result.text: stats['text_count'] += 1
            if result.font: stats['font_count'] += 1
            if result.style: stats['style_count'] += 1
            if result.position: stats['position_count'] += 1
        return stats
    
    def export_results(self, results: List[ExtractionResult], format: str = 'dict') -> Any:
        """导出提取结果"""
        if format == 'dict':
            return [r.to_dict() for r in results]
        elif format == 'json':
            import json
            return json.dumps([r.to_dict() for r in results], ensure_ascii=False, indent=2)
        elif format == 'list':
            return [{'layer_id': r.layer_id, 'layer_name': r.layer_name, 'layer_type': r.layer_type,
                     'has_text': r.text is not None, 'has_font': r.font is not None,
                     'has_style': r.style is not None, 'has_position': r.position is not None} for r in results]
        else:
            raise ValueError(f"不支持的导出格式: {format}")
