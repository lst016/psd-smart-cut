"""
Level 7 - Spec Generator
统一生成器 - 协调所有生成模块
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime

from skills.common import get_logger, get_config, get_error_handler, ErrorCategory
from .dimension_generator import DimensionGenerator, DimensionSpec
from .position_generator import PositionGenerator, PositionSpec
from .style_generator import StyleGenerator, StyleSpec
from .spec_validator import SpecValidator, ValidationResult
from .schema import (
    SCHEMA_VERSION,
    SCHEMA_NAME,
    COMPONENT_SCHEMA,
    COMPONENT_COLLECTION_SCHEMA
)

# ============ 数据类 ============

@dataclass
class SpecResult:
    """规格生成结果"""
    component_id: str
    name: str
    dimension: DimensionSpec
    position: PositionSpec
    style: StyleSpec
    schema_version: str = SCHEMA_VERSION
    raw_data: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.component_id,
            "name": self.name,
            "schema_version": self.schema_version,
            "dimensions": self.dimension.to_dict(),
            "position": self.position.to_dict(),
            "style": self.style.to_dict(),
            "raw_data": self.raw_data
        }


@dataclass
class ComponentSpec:
    """组件规格（完整版）"""
    id: str
    name: str
    type: str = "unknown"
    layer_id: Optional[str] = None
    dimensions: Dict = field(default_factory=dict)
    position: Dict = field(default_factory=dict)
    style: Dict = field(default_factory=dict)
    responsive: Dict = field(default_factory=dict)
    children: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class GenerationReport:
    """生成报告"""
    total: int = 0
    success: int = 0
    failed: int = 0
    duration_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "total": self.total,
            "success": self.success,
            "failed": self.failed,
            "duration_seconds": self.duration_seconds,
            "errors": self.errors
        }


# ============ 规格生成器 ============

class SpecGenerator:
    """统一规格生成器"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.logger = get_logger("spec-generator")
        self.config = config or {}
        self.error_handler = get_error_handler()
        
        # 初始化子生成器
        self.dimension_gen = DimensionGenerator(config)
        self.position_gen = PositionGenerator(config)
        self.style_gen = StyleGenerator(config)
        self.validator = SpecValidator(config)
        
        # 配置
        self.default_unit = self.config.get("default_unit", "px")
        self.enable_validation = self.config.get("enable_validation", True)
        self.enable_tailwind = self.config.get("enable_tailwind", True)
        self.enable_native_styles = self.config.get("enable_native_styles", True)
    
    def generate(
        self,
        layer_info: Dict,
        canvas_size: Optional[Dict] = None,
        generate_children: bool = True
    ) -> ComponentSpec:
        """
        生成单个组件规格
        
        Args:
            layer_info: 图层信息
            canvas_size: 画布尺寸
            generate_children: 是否生成子组件
            
        Returns:
            ComponentSpec: 组件规格
        """
        start_time = datetime.now()
        
        try:
            # 提取基本信息
            component_id = layer_info.get("id", f"comp_{id(layer_info)}")
            name = layer_info.get("name", "Unnamed")
            layer_type = layer_info.get("kind", "unknown")
            
            # 生成尺寸规格
            dimension = self.dimension_gen.generate(layer_info, self.default_unit)
            
            # 生成位置规格
            position = self.position_gen.generate(layer_info, canvas_size)
            
            # 生成样式规格
            style = self._generate_style(layer_info)
            
            # 生成响应式规格
            responsive = self._generate_responsive(dimension, layer_info)
            
            # 处理子组件
            children = []
            if generate_children and "children" in layer_info:
                children_data = layer_info["children"]
                if isinstance(children_data, list):
                    for child in children_data:
                        child_spec = self.generate(child, canvas_size, generate_children=True)
                        children.append(child_spec.to_dict())
            
            # 构建规格
            spec = ComponentSpec(
                id=component_id,
                name=name,
                type=layer_type,
                layer_id=layer_info.get("id"),
                dimensions=dimension.to_dict(),
                position=position.to_dict(),
                style=style.to_dict(),
                responsive=responsive,
                children=children,
                metadata={
                    "generated_at": datetime.now().isoformat(),
                    "generator": SCHEMA_NAME,
                    "generator_version": SCHEMA_VERSION
                }
            )
            
            # 验证
            if self.enable_validation:
                self._validate_spec(spec)
            
            self.logger.debug(f"生成组件规格: {name} ({component_id})")
            return spec
            
        except Exception as e:
            self.error_handler.record(
                task="spec_generate",
                error=e,
                category=ErrorCategory.EXPORT_ERROR,
                context={"layer_info": layer_info}
            )
            
            # 返回最小规格
            return ComponentSpec(
                id=layer_info.get("id", "unknown"),
                name=layer_info.get("name", "Error Component"),
                type="error"
            )
    
    def generate_batch(
        self,
        layers: List[Dict],
        canvas_size: Optional[Dict] = None
    ) -> tuple:
        """
        批量生成组件规格
        
        Args:
            layers: 图层列表
            canvas_size: 画布尺寸
            
        Returns:
            tuple: (specs, report)
        """
        start_time = datetime.now()
        
        specs = []
        errors = []
        
        for i, layer in enumerate(layers):
            try:
                spec = self.generate(layer, canvas_size)
                specs.append(spec)
            except Exception as e:
                errors.append(f"Layer {i}: {str(e)}")
                self.logger.error(f"生成失败: {e}")
        
        # 计算耗时
        duration = (datetime.now() - start_time).total_seconds()
        
        # 生成报告
        report = GenerationReport(
            total=len(layers),
            success=len(specs),
            failed=len(errors),
            duration_seconds=duration,
            errors=errors
        )
        
        self.logger.info(
            f"批量生成完成: {len(specs)}/{len(layers)} 成功, "
            f"耗时 {duration:.2f}s"
        )
        
        return specs, report
    
    def generate_collection(
        self,
        layers: List[Dict],
        source_file: str,
        canvas_size: Dict
    ) -> Dict:
        """
        生成组件集合
        
        Args:
            layers: 图层列表
            source_file: 源文件
            canvas_size: 画布尺寸
            
        Returns:
            Dict: 组件集合
        """
        specs, report = self.generate_batch(layers, canvas_size)
        
        collection = {
            "schema_version": SCHEMA_VERSION,
            "source_file": source_file,
            "canvas": canvas_size,
            "components": [s.to_dict() for s in specs],
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "generator": SCHEMA_NAME,
                "generator_version": SCHEMA_VERSION,
                "report": report.to_dict()
            }
        }
        
        return collection
    
    def _generate_style(self, layer_info: Dict) -> StyleSpec:
        """生成样式规格"""
        # 提取样式信息
        style_info = {}
        
        # 颜色
        colors = {}
        if "fill_color" in layer_info:
            colors["fill"] = layer_info["fill_color"]
        if "stroke_color" in layer_info:
            colors["stroke"] = layer_info["stroke_color"]
        if "background_color" in layer_info:
            colors["background"] = layer_info["background_color"]
        
        if colors:
            style_info["colors"] = colors
        
        # 字体
        if "font" in layer_info:
            style_info["font"] = layer_info["font"]
        
        # 边框
        if "border" in layer_info:
            style_info["border"] = layer_info["border"]
        
        # 阴影
        if "shadow" in layer_info:
            style_info["shadow"] = layer_info["shadow"]
        
        # 不透明度
        if "opacity" in layer_info:
            style_info["opacity"] = layer_info["opacity"]
        
        # 圆角
        if "border_radius" in layer_info:
            style_info["border_radius"] = layer_info["border_radius"]
        
        # 混合模式
        if "blend_mode" in layer_info:
            style_info["blend_mode"] = layer_info["blend_mode"]
        
        return self.style_gen.generate(style_info)
    
    def _generate_responsive(
        self,
        dimension: DimensionSpec,
        layer_info: Dict
    ) -> Dict:
        """生成响应式规格"""
        responsive = {}
        
        # 生成各断点的尺寸
        breakpoints = ["mobile", "tablet", "desktop", "wide"]
        breakpoint_scales = {
            "mobile": 0.5,
            "tablet": 0.75,
            "desktop": 1.0,
            "wide": 1.0
        }
        
        for bp in breakpoints:
            scale = breakpoint_scales.get(bp, 1.0)
            responsive[bp] = {
                "width": int(dimension.width * scale),
                "height": int(dimension.height * scale),
                "unit": dimension.unit,
                "scale": scale
            }
        
        return responsive
    
    def _validate_spec(self, spec: ComponentSpec) -> ValidationResult:
        """验证规格"""
        spec_dict = spec.to_dict()
        return self.validator.validate(spec_dict)
    
    def export_to_json(self, collection: Dict, output_path: str) -> str:
        """导出为 JSON"""
        import json
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(collection, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"导出规格到: {output_path}")
        return output_path


# ============ 便捷函数 ============

def generate_spec(
    layer_info: Dict,
    canvas_size: Optional[Dict] = None
) -> ComponentSpec:
    """生成组件规格（便捷函数）"""
    generator = SpecGenerator()
    return generator.generate(layer_info, canvas_size)


def generate_specs_batch(
    layers: List[Dict],
    canvas_size: Optional[Dict] = None
) -> List[ComponentSpec]:
    """批量生成组件规格（便捷函数）"""
    generator = SpecGenerator()
    specs, _ = generator.generate_batch(layers, canvas_size)
    return specs


def generate_collection(
    layers: List[Dict],
    source_file: str,
    canvas_size: Dict
) -> Dict:
    """生成组件集合（便捷函数）"""
    generator = SpecGenerator()
    return generator.generate_collection(layers, source_file, canvas_size)
