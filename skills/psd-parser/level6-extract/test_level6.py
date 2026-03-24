"""
Level 6 - 集成测试
文字/样式提取模块测试
"""

import pytest
import sys
import os
from typing import Dict, List

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from skills.psd_parser.level6_extract import (
    TextReader, TextContent, TextDirection, ParagraphAlignment,
    FontAnalyzer, FontInfo, FontStyle,
    StyleExtractor, LayerStyle, ShadowEffect, BorderEffect, GradientEffect,
    PositionReader, PositionData, AnchorPoint, Alignment, ResponsiveBreakpoint,
    Extractor, ExtractionResult
)


# ==================== Mock 数据 ====================

def create_mock_text_layer(layer_id: str, layer_name: str, text: str = None) -> Dict:
    """创建 Mock 文字图层"""
    return {
        'id': layer_id,
        'name': layer_name,
        'type': 'text',
        'kind': 'text',
        'text': {
            'content': text if text is not None else f"Mock Text for {layer_name}",
            'encoding': 'utf-8',
            'writingDirection': 0,
            'alignment': 0
        }
    }


def create_mock_image_layer(layer_id: str, layer_name: str) -> Dict:
    """创建 Mock 图片图层"""
    return {
        'id': layer_id,
        'name': layer_name,
        'type': 'image',
        'kind': 'pixel'
    }


def create_mock_layer_with_bounds(layer_id: str, layer_name: str, 
                                   x: int, y: int, w: int, h: int) -> Dict:
    """创建带位置信息的图层"""
    return {
        'id': layer_id,
        'name': layer_name,
        'type': 'text',
        'kind': 'text',
        'bounds': {'x': x, 'y': y, 'width': w, 'height': h},
        'opacity': 1.0,
        'blendMode': 'norm'
    }


def create_mock_style_layer(layer_id: str, layer_name: str,
                             opacity: float = 1.0, has_shadow: bool = False,
                             has_border: bool = False, has_gradient: bool = False) -> Dict:
    """创建带样式的图层"""
    style = {'opacity': opacity}
    
    if has_shadow:
        style['shadow'] = {
            'Color': {'red': 0, 'green': 0, 'blue': 0},
            'Opacity': 50,
            'OffsetX': 0,
            'OffsetY': 4,
            'Blur': 8,
            'Spread': 0,
            'BlendMode': 'norm'
        }
    
    if has_border:
        style['border'] = {
            'Color': {'red': 100, 'green': 100, 'blue': 100},
            'Size': 2,
            'Position': 'outside',
            'BlendMode': 'norm'
        }
    
    if has_gradient:
        style['gradient'] = {
            'Colors': [
                {'Color': {'red': 255, 'green': 255, 'blue': 255}},
                {'Color': {'red': 240, 'green': 240, 'blue': 240}}
            ],
            'Stops': [0, 100],
            'Angle': 180,
            'Type': 'linear'
        }
    
    return {
        'id': layer_id,
        'name': layer_name,
        'type': 'layer',
        'style': style
    }


# ==================== TextReader 测试 ====================

class TestTextReader:
    """文字读取器测试"""
    
    def test_init(self):
        """测试初始化"""
        reader = TextReader()
        assert reader is not None
        assert reader._mock_mode is True
    
    def test_read_text_layer(self):
        """测试读取文字图层"""
        reader = TextReader()
        layer = create_mock_text_layer('layer_1', 'Title Text', 'Hello World')
        
        result = reader.read(layer)
        
        assert result is not None
        assert result.text == 'Hello World'
        assert result.encoding == 'utf-8'
        assert result.is_rtl == False
        assert result.has_special_chars == False
    
    def test_read_non_text_layer(self):
        """测试读取非文字图层"""
        reader = TextReader()
        layer = create_mock_image_layer('layer_2', 'Background Image')
        
        result = reader.read(layer)
        
        assert result is None
    
    def test_read_batch(self):
        """测试批量读取"""
        reader = TextReader()
        layers = [
            create_mock_text_layer('layer_1', 'Text 1', 'Text One'),
            create_mock_text_layer('layer_2', 'Text 2', 'Text Two'),
            create_mock_image_layer('layer_3', 'Image 1'),
        ]
        
        results = reader.read_batch(layers)
        
        assert len(results) == 2
        assert results[0].text == 'Text One'
        assert results[1].text == 'Text Two'
    
    def test_text_direction(self):
        """测试 RTL 检测"""
        reader = TextReader()
        layer = create_mock_text_layer('layer_1', 'Arabic', 'مرحبا')
        
        result = reader.read(layer)
        
        assert result is not None
        assert result.is_rtl == True
    
    def test_paragraph_alignment(self):
        """测试段落对齐"""
        reader = TextReader()
        layer = create_mock_text_layer('layer_1', 'Multi-line', 'Line 1\nLine 2\nLine 3')
        
        result = reader.read(layer)
        
        assert result is not None
        assert len(result.paragraphs) == 3


# ==================== FontAnalyzer 测试 ====================

class TestFontAnalyzer:
    """字体分析器测试"""
    
    def test_init(self):
        """测试初始化"""
        analyzer = FontAnalyzer()
        assert analyzer is not None
    
    def test_analyze_text_layer(self):
        """测试分析文字图层"""
        analyzer = FontAnalyzer()
        layer = create_mock_text_layer('layer_1', 'Title', 'Title Text')
        
        result = analyzer.analyze(layer)
        
        assert result is not None
        assert result.family is not None
        assert result.size > 0
        assert result.weight > 0
        assert result.color.startswith('#')
    
    def test_analyze_non_text_layer(self):
        """测试分析非文字图层"""
        analyzer = FontAnalyzer()
        layer = create_mock_image_layer('layer_1', 'Image')
        
        result = analyzer.analyze(layer)
        
        assert result is None
    
    def test_analyze_batch(self):
        """测试批量分析"""
        analyzer = FontAnalyzer()
        layers = [
            create_mock_text_layer('layer_1', 'Text 1', 'Text One'),
            create_mock_image_layer('layer_2', 'Image 1'),
            create_mock_text_layer('layer_3', 'Text 2', 'Text Two'),
        ]
        
        results = analyzer.analyze_batch(layers)
        
        assert len(results) == 2
    
    def test_font_style_detection(self):
        """测试字体样式检测"""
        analyzer = FontAnalyzer()
        layer = create_mock_text_layer('layer_1', 'Header', 'Header Text')
        
        result = analyzer.analyze(layer)
        
        assert hasattr(result, 'family')
        assert hasattr(result, 'name')
        assert hasattr(result, 'size')
        assert hasattr(result, 'weight')
        assert hasattr(result, 'style')
        assert hasattr(result, 'color')
        assert hasattr(result, 'line_height')
        assert hasattr(result, 'letter_spacing')
    
    def test_font_color_extraction(self):
        """测试字体颜色提取"""
        analyzer = FontAnalyzer()
        layer = create_mock_text_layer('layer_1', 'Colored Text', 'Test')
        
        result = analyzer.analyze(layer)
        
        assert result.color is not None
        assert result.color.startswith('#')


# ==================== StyleExtractor 测试 ====================

class TestStyleExtractor:
    """样式提取器测试"""
    
    def test_init(self):
        """测试初始化"""
        extractor = StyleExtractor()
        assert extractor is not None
    
    def test_extract_image_layer(self):
        """测试提取图片图层样式"""
        extractor = StyleExtractor()
        layer = create_mock_style_layer('layer_1', 'Button')
        
        result = extractor.extract(layer)
        
        assert result is not None
        assert result.opacity == 1.0
        assert result.blend_mode == 'normal'
        assert 'none' in result.effects
    
    def test_extract_with_shadow(self):
        """测试提取阴影效果"""
        extractor = StyleExtractor()
        layer = create_mock_style_layer('layer_1', 'Button', has_shadow=True)
        
        result = extractor.extract(layer)
        
        assert 'shadow' in result.effects
        assert result.shadow is not None
        assert result.shadow.offset_y == 4
        assert result.shadow.blur == 8
    
    def test_extract_batch(self):
        """测试批量提取"""
        extractor = StyleExtractor()
        layers = [
            create_mock_style_layer('layer_1', 'Style 1'),
            create_mock_style_layer('layer_2', 'Style 2'),
            create_mock_style_layer('layer_3', 'Style 3'),
        ]
        
        results = extractor.extract_batch(layers)
        
        assert len(results) == 3
        assert all(r.opacity == 1.0 for r in results)
    
    def test_blend_mode_mapping(self):
        """测试混合模式映射"""
        extractor = StyleExtractor()
        layer = create_mock_style_layer('layer_1', 'Styled Layer')
        
        result = extractor.extract(layer)
        
        assert result.blend_mode is not None
    
    def test_fill_opacity(self):
        """测试填充不透明度"""
        extractor = StyleExtractor()
        layer = create_mock_style_layer('layer_1', 'Semi-transparent', opacity=0.8)
        
        result = extractor.extract(layer)
        
        assert result.opacity == 0.8


# ==================== PositionReader 测试 ====================

class TestPositionReader:
    """位置读取器测试"""
    
    def test_init(self):
        """测试初始化"""
        reader = PositionReader()
        assert reader is not None
        assert reader._canvas_width == 1440
        assert reader._canvas_height == 900
    
    def test_read_position(self):
        """测试读取位置"""
        reader = PositionReader()
        layer = create_mock_layer_with_bounds('layer_1', 'Box', 100, 200, 300, 400)
        
        result = reader.read(layer)
        
        assert result is not None
        assert result.x == 100
        assert result.y == 200
        assert result.width == 300
        assert result.height == 400
    
    def test_read_batch(self):
        """测试批量读取"""
        reader = PositionReader()
        layers = [
            create_mock_layer_with_bounds('layer_1', 'Box 1', 0, 0, 100, 100),
            create_mock_layer_with_bounds('layer_2', 'Box 2', 100, 100, 200, 200),
            create_mock_layer_with_bounds('layer_3', 'Box 3', 300, 300, 150, 150),
        ]
        
        results = reader.read_batch(layers)
        
        assert len(results) == 3
        assert results[0].x == 0
        assert results[1].width == 200
        assert results[2].height == 150


# ==================== Extractor 测试 ====================

class TestExtractor:
    """统一提取器测试"""
    
    def test_init_default(self):
        """测试默认初始化"""
        extractor = Extractor()
        assert extractor is not None
        assert extractor.text_reader is not None
        assert extractor.font_analyzer is not None
        assert extractor.style_extractor is not None
        assert extractor.position_reader is not None
    
    def test_extract_all_text_layer(self):
        """测试提取文字图层"""
        extractor = Extractor()
        layer = {
            'id': 'layer_1',
            'name': 'Complete Layer',
            'type': 'text',
            'kind': 'text',
            'text': {'content': 'Test Text'},
            'bounds': {'x': 100, 'y': 200, 'width': 300, 'height': 100},
            'opacity': 0.8,
            'blendMode': 'norm'
        }
        
        result = extractor.extract(layer)
        
        assert result is not None
        assert result.layer_id == 'layer_1'
        assert result.layer_name == 'Complete Layer'
        assert result.text is not None
        assert result.position is not None
    
    def test_extract_all_image_layer(self):
        """测试提取图片图层"""
        extractor = Extractor()
        layer = {
            'id': 'layer_2',
            'name': 'Image Layer',
            'type': 'image',
            'bounds': {'x': 0, 'y': 0, 'width': 500, 'height': 300}
        }
        
        result = extractor.extract(layer)
        
        assert result is not None
        assert result.layer_id == 'layer_2'
        assert result.text is None
        assert result.position is not None
    
    def test_extract_all_button_layer(self):
        """测试提取按钮图层"""
        extractor = Extractor()
        layer = {
            'id': 'layer_3',
            'name': 'Button',
            'type': 'button',
            'bounds': {'x': 720, 'y': 400, 'width': 200, 'height': 50},
            'style': {
                'shadow': {
                    'Color': {'red': 0, 'green': 0, 'blue': 0},
                    'Opacity': 50,
                    'OffsetX': 0,
                    'OffsetY': 4,
                    'Blur': 8,
                    'Spread': 0,
                    'BlendMode': 'norm'
                }
            }
        }
        
        result = extractor.extract(layer)
        
        assert result is not None
        assert result.style is not None
        assert 'shadow' in result.style.effects
    
    def test_extract_batch(self):
        """测试批量提取"""
        extractor = Extractor()
        layers = [
            create_mock_text_layer('layer_1', 'Text 1', 'Text'),
            create_mock_image_layer('layer_2', 'Image 1'),
            create_mock_layer_with_bounds('layer_3', 'Box 1', 0, 0, 100, 100),
        ]
        
        results = extractor.extract_batch(layers)
        
        assert len(results) == 3
        assert results[0].text is not None
    
    def test_extract_text_only(self):
        """测试仅提取文字"""
        extractor = Extractor()
        layer = create_mock_text_layer('layer_1', 'Text 1', 'Test')
        
        result = extractor.extract(layer)
        
        assert result.text is not None
    
    def test_extract_font_only(self):
        """测试仅提取字体"""
        extractor = Extractor()
        layer = create_mock_text_layer('layer_1', 'Text 1', 'Test')
        
        result = extractor.extract(layer)
        
        assert result.font is not None
    
    def test_extract_style_only(self):
        """测试仅提取样式"""
        extractor = Extractor()
        layer = create_mock_image_layer('layer_1', 'Image')
        
        result = extractor.extract(layer)
        
        assert result.style is not None
    
    def test_extract_position_only(self):
        """测试仅提取位置"""
        extractor = Extractor()
        layer = create_mock_layer_with_bounds('layer_1', 'Box 1', 0, 0, 100, 100)
        
        result = extractor.extract(layer)
        
        assert result.position is not None
    
    def test_to_dict(self):
        """测试导出为字典"""
        extractor = Extractor()
        layer = create_mock_text_layer('layer_1', 'Text 1', 'Test')
        
        result = extractor.extract(layer)
        result_dict = result.to_dict()
        
        assert 'layer_id' in result_dict
        assert 'text' in result_dict
    
    def test_to_json(self):
        """测试导出为 JSON"""
        import json
        
        extractor = Extractor()
        layers = [create_mock_text_layer('layer_1', 'Text 1', 'Test')]
        
        results = extractor.extract_batch(layers)
        exported = extractor.export_results(results, format='json')
        
        assert isinstance(exported, str)
        data = json.loads(exported)
        assert len(data) == 1
    
    def test_to_summary(self):
        """测试导出为摘要"""
        extractor = Extractor()
        layers = [create_mock_text_layer('layer_1', 'Text 1', 'Test')]
        
        results = extractor.extract_batch(layers)
        summary = extractor.export_results(results, format='list')
        
        assert isinstance(summary, list)
        assert len(summary) == 1
        assert 'has_text' in summary[0]
    
    def test_get_statistics(self):
        """测试获取统计信息"""
        extractor = Extractor()
        layers = [
            create_mock_text_layer('layer_1', 'Text 1', 'Test'),
            create_mock_image_layer('layer_2', 'Image 1'),
        ]
        
        results = extractor.extract_batch(layers)
        
        # 检查统计信息在日志中
        assert len(results) == 2


# ==================== 边界情况测试 ====================

class TestLevel6EdgeCases:
    """边界情况测试"""
    
    def test_missing_layer_fields(self):
        """测试缺少字段"""
        extractor = Extractor()
        layer = {'id': 'minimal', 'name': 'Minimal'}
        
        result = extractor.extract(layer)
        
        assert result is not None
        assert result.layer_id == 'minimal'
    
    def test_none_layer(self):
        """测试 None 图层"""
        extractor = Extractor()
        
        result = extractor.extract({})
        
        assert result is not None
    
    def test_empty_text(self):
        """测试空文字"""
        reader = TextReader()
        layer = create_mock_text_layer('layer_1', 'Empty', '')
        
        result = reader.read(layer)
        
        assert result is not None
        assert result.text == ''
    
    def test_special_characters(self):
        """测试特殊字符"""
        reader = TextReader()
        layer = create_mock_text_layer('layer_1', 'Special', 'Hello\u200bWorld')
        
        result = reader.read(layer)
        
        assert result is not None
        assert result.has_special_chars is True


# ==================== 运行测试 ====================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
