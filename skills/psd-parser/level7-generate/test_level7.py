"""
Level 7 - Generate Layer Tests
规格生成层测试
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from skills.psd_parser.level7_generate import (
    # Dimension
    DimensionSpec,
    DimensionGenerator,
    UnitConverter,
    generate_dimension,
    generate_dimensions_batch,
    
    # Position
    PositionSpec,
    PositionGenerator,
    LayoutType,
    generate_position,
    generate_positions_batch,
    
    # Style
    StyleSpec,
    StyleGenerator,
    ColorConverter,
    generate_style,
    generate_styles_batch,
    
    # Validator
    ValidationError,
    ValidationResult,
    SpecValidator,
    CSSValidator,
    validate_spec,
    validate_specs_batch,
    
    # Schema
    SCHEMA_VERSION,
    SCHEMA_NAME,
    COMPONENT_SCHEMA,
    get_schema,
    validate_against_schema,
    
    # Generator
    SpecResult,
    ComponentSpec,
    GenerationReport,
    SpecGenerator,
    generate_spec,
    generate_specs_batch,
    generate_collection
)


# ============ Mock 数据 ============

MOCK_LAYER_INFO = {
    "id": "layer_1",
    "name": "Test Button",
    "kind": "image",
    "visible": True,
    "locked": False,
    "left": 100,
    "top": 100,
    "right": 300,
    "bottom": 150,
    "width": 200,
    "height": 50,
    "opacity": 1.0,
    "blend_mode": "normal",
    "bbox": {"x": 100, "y": 100, "width": 200, "height": 50}
}

MOCK_CANVAS_SIZE = {"width": 1920, "height": 1080}

MOCK_STYLE_INFO = {
    "colors": {
        "primary": "#3498db",
        "background": "#ffffff",
        "text": "#333333"
    },
    "font": {
        "family": "Arial",
        "size": 14,
        "weight": 400,
        "line_height": 1.5
    },
    "border": {
        "width": 1,
        "style": "solid",
        "color": "#e0e0e0"
    },
    "shadow": {
        "x": 0,
        "y": 2,
        "blur": 4,
        "spread": 0,
        "color": "rgba(0,0,0,0.1)"
    },
    "border_radius": 8,
    "opacity": 1.0
}


# ============ DimensionGenerator Tests ============

class TestDimensionGenerator:
    """尺寸生成器测试"""
    
    def test_generate_basic(self):
        """测试基本生成"""
        gen = DimensionGenerator()
        spec = gen.generate(MOCK_LAYER_INFO, unit="px")
        
        assert isinstance(spec, DimensionSpec)
        assert spec.width == 200
        assert spec.height == 50
        assert spec.unit == "px"
        assert 1.0 in spec.scale_factors
    
    def test_generate_with_rem(self):
        """测试 rem 单位转换"""
        gen = DimensionGenerator()
        spec = gen.generate(MOCK_LAYER_INFO, unit="rem")
        
        assert spec.unit == "rem"
        # 200px = 12.5rem (200/16)
        assert spec.width == 12
    
    def test_generate_batch(self):
        """测试批量生成"""
        gen = DimensionGenerator()
        layers = [MOCK_LAYER_INFO, {**MOCK_LAYER_INFO, "id": "layer_2", "width": 100, "height": 100}]
        
        specs = gen.generate_batch(layers, unit="px")
        
        assert len(specs) == 2
        assert specs[0].width == 200
        assert specs[1].width == 100
    
    def test_calculate_scale_factor(self):
        """测试缩放因子计算"""
        gen = DimensionGenerator()
        
        scale = gen.calculate_scale_factor(100, 200)
        assert scale == 2.0
        
        scale = gen.calculate_scale_factor(100, 150)
        assert scale == 1.0  # 最接近的
    
    def test_generate_responsive_sizes(self):
        """测试响应式尺寸生成"""
        gen = DimensionGenerator()
        
        responsive = gen.generate_responsive_sizes(200, 50)
        
        assert "mobile" in responsive
        assert "tablet" in responsive
        assert "desktop" in responsive
        assert responsive["mobile"]["width"] == 100  # 0.5x
        assert responsive["tablet"]["width"] == 150  # 0.75x


class TestUnitConverter:
    """单位转换器测试"""
    
    def test_convert_px_to_rem(self):
        """测试 px 转 rem"""
        result = UnitConverter.convert(16, "px", "rem")
        assert result == 1.0
    
    def test_convert_same_unit(self):
        """测试相同单位"""
        result = UnitConverter.convert(100, "px", "px")
        assert result == 100


# ============ PositionGenerator Tests ============

class TestPositionGenerator:
    """位置生成器测试"""
    
    def test_generate_basic(self):
        """测试基本生成"""
        gen = PositionGenerator()
        spec = gen.generate(MOCK_LAYER_INFO, MOCK_CANVAS_SIZE)
        
        assert isinstance(spec, PositionSpec)
        assert spec.position_type in ["relative", "absolute"]
    
    def test_generate_absolute(self):
        """测试绝对定位"""
        gen = PositionGenerator()
        # 全屏装饰元素应该使用 absolute
        info = {
            **MOCK_LAYER_INFO,
            "layer_type": "decorator",
            "bbox": {"x": 0, "y": 0, "width": 1920, "height": 1080}
        }
        spec = gen.generate(info, MOCK_CANVAS_SIZE)
        
        assert spec.position_type == "absolute"
    
    def test_generate_margin(self):
        """测试边距生成"""
        gen = PositionGenerator()
        info = {**MOCK_LAYER_INFO, "margin": {"top": 10, "right": 20}}
        spec = gen.generate(info, MOCK_CANVAS_SIZE)
        
        assert spec.margin["top"] == "10px"
        assert spec.margin["right"] == "20px"
    
    def test_generate_padding(self):
        """测试内边距生成"""
        gen = PositionGenerator()
        info = {**MOCK_LAYER_INFO, "padding": {"top": 5}}
        spec = gen.generate(info, MOCK_CANVAS_SIZE)
        
        assert spec.padding["top"] == "5px"
    
    def test_generate_batch(self):
        """测试批量生成"""
        gen = PositionGenerator()
        positions = [MOCK_LAYER_INFO, {**MOCK_LAYER_INFO, "id": "layer_2"}]
        
        specs = gen.generate_batch(positions, MOCK_CANVAS_SIZE)
        
        assert len(specs) == 2


class TestLayoutType:
    """布局类型测试"""
    
    def test_layout_types(self):
        """测试布局类型常量"""
        assert LayoutType.STATIC == "static"
        assert LayoutType.RELATIVE == "relative"
        assert LayoutType.ABSOLUTE == "absolute"
        assert LayoutType.FLEX == "flex"
        assert LayoutType.GRID == "grid"


# ============ StyleGenerator Tests ============

class TestStyleGenerator:
    """样式生成器测试"""
    
    def test_generate_basic(self):
        """测试基本样式生成"""
        gen = StyleGenerator()
        spec = gen.generate(MOCK_STYLE_INFO)
        
        assert isinstance(spec, StyleSpec)
        assert "css" in spec.to_dict()
        assert "tailwind" in spec.to_dict()
        assert "ios" in spec.to_dict()
        assert "android" in spec.to_dict()
    
    def test_generate_colors(self):
        """测试颜色生成"""
        gen = StyleGenerator()
        spec = gen.generate({"colors": {"primary": "#3498db"}})
        
        assert "--color-primary" in spec.css
        assert len(spec.ios) > 0
        assert len(spec.android) > 0
    
    def test_generate_font(self):
        """测试字体生成"""
        gen = StyleGenerator()
        spec = gen.generate({"font": {"family": "Arial", "size": 14}})
        
        assert "font-family" in spec.css
        assert "font-size" in spec.css
    
    def test_generate_border(self):
        """测试边框生成"""
        gen = StyleGenerator()
        spec = gen.generate({"border": {"width": 1, "style": "solid", "color": "#000"}})
        
        assert "border-width" in spec.css
        assert "border-style" in spec.css
    
    def test_generate_shadow(self):
        """测试阴影生成"""
        gen = StyleGenerator()
        spec = gen.generate({"shadow": {"x": 0, "y": 2, "blur": 4, "color": "rgba(0,0,0,0.1)"}})
        
        assert "box-shadow" in spec.css
    
    def test_generate_batch(self):
        """测试批量生成"""
        gen = StyleGenerator()
        styles = [MOCK_STYLE_INFO, {"colors": {"primary": "#fff"}}]
        
        specs = gen.generate_batch(styles)
        
        assert len(specs) == 2
    
    def test_merge_styles(self):
        """测试样式合并"""
        gen = StyleGenerator()
        spec1 = gen.generate({"colors": {"primary": "#3498db"}})
        spec2 = gen.generate({"colors": {"secondary": "#e74c3c"}})
        
        merged = gen.merge_styles([spec1, spec2])
        
        assert len(merged.css) >= 2


class TestColorConverter:
    """颜色转换测试"""
    
    def test_hex_to_rgba(self):
        """测试 HEX 转 RGBA"""
        result = ColorConverter.hex_to_rgba("#3498db", 0.5)
        assert "rgba" in result
        assert "0.5" in result
    
    def test_hex_to_ios(self):
        """测试 HEX 转 iOS"""
        result = ColorConverter.hex_to_ios("#3498db")
        assert "UIColor" in result
    
    def test_hex_to_android(self):
        """测试 HEX 转 Android"""
        result = ColorConverter.hex_to_android("#3498db")
        assert result.startswith("#")


# ============ SpecValidator Tests ============

class TestCSSValidator:
    """CSS 验证器测试"""
    
    def test_validate_valid_property(self):
        """测试有效属性"""
        errors = CSSValidator.validate_property("width", "100px")
        assert len(errors) == 0
    
    def test_validate_invalid_property(self):
        """测试无效属性"""
        errors = CSSValidator.validate_property("invalid-prop", "value")
        assert len(errors) > 0
    
    def test_validate_position(self):
        """测试 position 验证"""
        errors = CSSValidator.validate_property("position", "invalid")
        assert len(errors) == 1
        
        errors = CSSValidator.validate_property("position", "relative")
        assert len(errors) == 0
    
    def test_validate_flex_direction(self):
        """测试 flex-direction 验证"""
        errors = CSSValidator.validate_property("flex-direction", "row")
        assert len(errors) == 0
        
        errors = CSSValidator.validate_property("flex-direction", "invalid")
        assert len(errors) == 1


class TestSpecValidator:
    """规格验证器测试"""
    
    def test_validate_valid_spec(self):
        """测试有效规格"""
        validator = SpecValidator()
        spec = {
            "id": "comp_1",
            "name": "Test",
            "dimensions": {"width": 100, "height": 50},
            "position": {"position_type": "relative"},
            "style": {"css": {"width": "100px"}}
        }
        
        result = validator.validate(spec)
        
        assert result.valid
    
    def test_validate_missing_required(self):
        """测试缺少必需字段"""
        validator = SpecValidator()
        spec = {
            "dimensions": {"width": 100}
        }
        
        result = validator.validate(spec)
        
        assert not result.valid
        assert result.error_count > 0
    
    def test_validate_invalid_dimensions(self):
        """测试无效尺寸"""
        validator = SpecValidator()
        spec = {
            "id": "comp_1",
            "name": "Test",
            "dimensions": {"width": -10, "height": 50}
        }
        
        result = validator.validate(spec)
        
        assert not result.valid
    
    def test_validate_batch(self):
        """测试批量验证"""
        validator = SpecValidator()
        specs = [
            {"id": "comp_1", "name": "Test 1"},
            {"id": "comp_2", "name": "Test 2"}
        ]
        
        results = validator.validate_batch(specs)
        
        assert len(results) == 2
    
    def test_check_conflicts(self):
        """测试冲突检查"""
        validator = SpecValidator()
        spec = {
            "position": {
                "position_type": "absolute",
                "flex_props": {"display": "flex"}
            }
        }
        
        errors = validator.check_conflicts(spec)
        
        assert len(errors) > 0


# ============ Schema Tests ============

class TestSchema:
    """Schema 测试"""
    
    def test_schema_version(self):
        """测试 Schema 版本"""
        assert SCHEMA_VERSION == "1.0.0"
    
    def test_get_schema(self):
        """测试获取 Schema"""
        schema = get_schema("component")
        assert schema is not None
        assert "properties" in schema
    
    def test_validate_against_schema(self):
        """测试 Schema 验证"""
        data = {
            "id": "comp_1",
            "name": "Test",
            "dimensions": {"width": 100, "height": 50}
        }
        
        assert validate_against_schema(data, "component")
    
    def test_validate_against_schema_missing_required(self):
        """测试缺少必需字段"""
        data = {
            "name": "Test Only"
        }
        
        assert not validate_against_schema(data, "component")


# ============ Generator Tests ============

class TestSpecGenerator:
    """统一生成器测试"""
    
    def test_generate_basic(self):
        """测试基本生成"""
        gen = SpecGenerator()
        spec = gen.generate(MOCK_LAYER_INFO, MOCK_CANVAS_SIZE)
        
        assert isinstance(spec, ComponentSpec)
        assert spec.id == "layer_1"
        assert spec.name == "Test Button"
        assert "dimensions" in spec.to_dict()
    
    def test_generate_with_children(self):
        """测试带子组件生成"""
        gen = SpecGenerator()
        layer = {
            **MOCK_LAYER_INFO,
            "children": [
                {**MOCK_LAYER_INFO, "id": "child_1", "name": "Child 1"}
            ]
        }
        
        spec = gen.generate(layer, MOCK_CANVAS_SIZE, generate_children=True)
        
        assert len(spec.children) == 1
    
    def test_generate_batch(self):
        """测试批量生成"""
        gen = SpecGenerator()
        layers = [MOCK_LAYER_INFO, {**MOCK_LAYER_INFO, "id": "layer_2"}]
        
        specs, report = gen.generate_batch(layers, MOCK_CANVAS_SIZE)
        
        assert len(specs) == 2
        assert isinstance(report, GenerationReport)
        assert report.success == 2
    
    def test_generate_collection(self):
        """测试集合生成"""
        gen = SpecGenerator()
        layers = [MOCK_LAYER_INFO]
        
        collection = gen.generate_collection(
            layers,
            source_file="test.psd",
            canvas_size=MOCK_CANVAS_SIZE
        )
        
        assert "schema_version" in collection
        assert "components" in collection
        assert len(collection["components"]) == 1
    
    def test_dimension_spec(self):
        """测试 DimensionSpec"""
        spec = DimensionSpec(
            width=100,
            height=50,
            unit="px",
            scale_factors=[1.0, 2.0]
        )
        
        assert spec.width == 100
        assert spec.height == 50
        assert "width" in spec.to_dict()
    
    def test_position_spec(self):
        """测试 PositionSpec"""
        spec = PositionSpec(
            position_type="relative",
            margin={"top": "10px"},
            padding={"top": "5px"}
        )
        
        assert spec.position_type == "relative"
        assert "margin" in spec.to_dict()
    
    def test_style_spec(self):
        """测试 StyleSpec"""
        spec = StyleSpec(
            css={"width": "100px"},
            tailwind=["w-full"],
            ios={"backgroundColor": "#fff"}
        )
        
        assert len(spec.css) == 1
        assert len(spec.tailwind) == 1


# ============ Convenience Functions Tests ============

class TestConvenienceFunctions:
    """便捷函数测试"""
    
    def test_generate_dimension(self):
        """测试便捷尺寸生成"""
        spec = generate_dimension(MOCK_LAYER_INFO)
        assert isinstance(spec, DimensionSpec)
    
    def test_generate_dimensions_batch(self):
        """测试便捷批量尺寸生成"""
        specs = generate_dimensions_batch([MOCK_LAYER_INFO])
        assert len(specs) == 1
    
    def test_generate_position(self):
        """测试便捷位置生成"""
        spec = generate_position(MOCK_LAYER_INFO, MOCK_CANVAS_SIZE)
        assert isinstance(spec, PositionSpec)
    
    def test_generate_style(self):
        """测试便捷样式生成"""
        spec = generate_style(MOCK_STYLE_INFO)
        assert isinstance(spec, StyleSpec)
    
    def test_validate_spec_func(self):
        """测试便捷验证"""
        spec = {"id": "comp_1", "name": "Test"}
        result = validate_spec(spec)
        assert isinstance(result, ValidationResult)
    
    def test_generate_spec_func(self):
        """测试便捷生成"""
        spec = generate_spec(MOCK_LAYER_INFO, MOCK_CANVAS_SIZE)
        assert isinstance(spec, ComponentSpec)
    
    def test_generate_specs_batch_func(self):
        """测试便捷批量生成"""
        specs = generate_specs_batch([MOCK_LAYER_INFO], MOCK_CANVAS_SIZE)
        assert len(specs) == 1


# ============ Run Tests ============

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
