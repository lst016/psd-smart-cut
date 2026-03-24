"""
Level 7 - Dimension Generator
尺寸生成器 - 生成组件尺寸规格
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from skills.common import get_logger, get_config, get_error_handler, ErrorCategory

# ============ 数据类 ============

@dataclass
class DimensionSpec:
    """尺寸规格"""
    width: int
    height: int
    unit: str = "px"  # px/rem/dp/pt
    min_width: Optional[int] = None
    max_width: Optional[int] = None
    scale_factors: List[float] = field(default_factory=lambda: [1.0, 2.0, 3.0])
    
    def to_dict(self) -> Dict:
        return asdict(self)


# ============ 单位转换 ============

class UnitConverter:
    """单位转换器"""
    
    # 基础单位换算（以 px 为基准）
    BASE_RATIOS = {
        "px": 1.0,
        "rem": 16.0,  # 假设基础字体为 16px
        "dp": 1.0,   # Android dp 与 px 1:1
        "pt": 1.333,  # 72 DPI 下 1pt = 1.333px
    }
    
    @classmethod
    def convert(cls, value: float, from_unit: str, to_unit: str) -> float:
        """单位转换"""
        if from_unit == to_unit:
            return value
        px_value = value * cls.BASE_RATIOS.get(from_unit, 1.0)
        return px_value / cls.BASE_RATIOS.get(to_unit, 1.0)
    
    @classmethod
    def convert_dict(cls, dims: Dict, from_unit: str, to_unit: str) -> Dict:
        """转换尺寸字典"""
        if from_unit == to_unit:
            return dims
        
        scale = cls.BASE_RATIOS.get(from_unit, 1.0) / cls.BASE_RATIOS.get(to_unit, 1.0)
        return {
            "width": int(dims.get("width", 0) * scale),
            "height": int(dims.get("height", 0) * scale)
        }


# ============ 尺寸生成器 ============

class DimensionGenerator:
    """尺寸生成器"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.logger = get_logger("dimension-generator")
        self.config = config or {}
        self.error_handler = get_error_handler()
        
        # 响应式断点配置
        self.breakpoints = self.config.get("breakpoints", {
            "mobile": 480,
            "tablet": 768,
            "desktop": 1024,
            "wide": 1440
        })
        
        # 缩放因子
        self.default_scale_factors = self.config.get("scale_factors", [1.0, 2.0, 3.0])
    
    def generate(self, layer_info: Dict, unit: str = "px") -> DimensionSpec:
        """
        生成单个图层的尺寸规格
        
        Args:
            layer_info: 图层信息字典
            unit: 目标单位 (px/rem/dp/pt)
            
        Returns:
            DimensionSpec: 尺寸规格对象
        """
        try:
            # 提取尺寸信息
            width = layer_info.get("width", 0)
            height = layer_info.get("height", 0)
            
            if width <= 0 or height <= 0:
                self.logger.warning(f"无效尺寸: {width}x{height}")
            
            # 单位转换
            source_unit = layer_info.get("unit", "px")
            if source_unit != unit:
                width = int(UnitConverter.convert(width, source_unit, unit))
                height = int(UnitConverter.convert(height, source_unit, unit))
            
            # 计算响应式尺寸
            min_width = self._calculate_min_width(width, layer_info)
            max_width = self._calculate_max_width(width, layer_info)
            
            # 获取缩放因子
            scale_factors = layer_info.get("scale_factors", self.default_scale_factors)
            
            spec = DimensionSpec(
                width=width,
                height=height,
                unit=unit,
                min_width=min_width,
                max_width=max_width,
                scale_factors=scale_factors
            )
            
            self.logger.debug(f"生成尺寸规格: {width}x{height}{unit}")
            return spec
            
        except Exception as e:
            self.error_handler.record(
                task="dimension_generate",
                error=e,
                category=ErrorCategory.EXPORT_ERROR,
                context={"layer_info": layer_info, "unit": unit}
            )
            # 返回默认值
            return DimensionSpec(
                width=0,
                height=0,
                unit=unit,
                scale_factors=self.default_scale_factors
            )
    
    def generate_batch(self, layers: List[Dict], unit: str = "px") -> List[DimensionSpec]:
        """
        批量生成尺寸规格
        
        Args:
            layers: 图层信息列表
            unit: 目标单位
            
        Returns:
            List[DimensionSpec]: 尺寸规格列表
        """
        results = []
        for layer in layers:
            spec = self.generate(layer, unit)
            results.append(spec)
        
        self.logger.info(f"批量生成 {len(results)} 个尺寸规格")
        return results
    
    def _calculate_min_width(self, width: int, layer_info: Dict) -> Optional[int]:
        """计算最小宽度"""
        # 响应式场景：容器通常有最小宽度
        if layer_info.get("kind") == "group":
            # 组可能需要更小的最小宽度
            return int(width * 0.5)
        
        # 普通图层
        return int(width * 0.75)
    
    def _calculate_max_width(self, width: int, layer_info: Dict) -> Optional[int]:
        """计算最大宽度"""
        # 响应式场景：容器通常有最大宽度
        if layer_info.get("kind") == "group":
            return int(width * 1.5)
        
        return int(width * 1.25)
    
    def calculate_scale_factor(
        self,
        source_size: int,
        target_size: int,
        scale_factors: List[float] = None
    ) -> float:
        """
        计算最佳缩放因子
        
        Args:
            source_size: 源尺寸
            target_size: 目标尺寸
            scale_factors: 可用的缩放因子列表
            
        Returns:
            float: 最佳缩放因子
        """
        if scale_factors is None:
            scale_factors = self.default_scale_factors
        
        if source_size == 0:
            return 1.0
        
        ratio = target_size / source_size
        
        # 找到最接近的缩放因子
        closest = min(scale_factors, key=lambda x: abs(x - ratio))
        return closest
    
    def generate_responsive_sizes(
        self,
        base_width: int,
        base_height: int,
        breakpoints: Dict[str, int] = None
    ) -> Dict[str, Dict]:
        """
        生成响应式尺寸
        
        Args:
            base_width: 基础宽度
            base_height: 基础高度
            breakpoints: 断点配置
            
        Returns:
            Dict: 各断点的尺寸
        """
        if breakpoints is None:
            breakpoints = self.breakpoints
        
        responsive = {}
        
        # 定义断点的缩放比例
        breakpoint_scales = {
            "mobile": 0.5,
            "tablet": 0.75,
            "desktop": 1.0,
            "wide": 1.0
        }
        
        for name, breakpoint in breakpoints.items():
            # 根据断点名称确定缩放比例
            scale = breakpoint_scales.get(name, 1.0)
            
            responsive[name] = {
                "width": int(base_width * scale),
                "height": int(base_height * scale),
                "breakpoint": breakpoint,
                "scale": scale
            }
        
        return responsive


# ============ 便捷函数 ============

def generate_dimension(layer_info: Dict, unit: str = "px") -> DimensionSpec:
    """生成尺寸规格（便捷函数）"""
    generator = DimensionGenerator()
    return generator.generate(layer_info, unit)


def generate_dimensions_batch(layers: List[Dict], unit: str = "px") -> List[DimensionSpec]:
    """批量生成尺寸规格（便捷函数）"""
    generator = DimensionGenerator()
    return generator.generate_batch(layers, unit)
