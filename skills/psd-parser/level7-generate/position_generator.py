"""
Level 7 - Position Generator
位置生成器 - 生成 CSS/Flex/Grid 布局规格
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from skills.common import get_logger, get_config, get_error_handler, ErrorCategory

# ============ 数据类 ============

@dataclass
class PositionSpec:
    """位置规格"""
    position_type: str = "relative"  # static/relative/absolute/fixed/sticky
    top: Optional[str] = None
    right: Optional[str] = None
    bottom: Optional[str] = None
    left: Optional[str] = None
    margin: Dict[str, str] = field(default_factory=lambda: {
        "top": "0", "right": "0", "bottom": "0", "left": "0"
    })
    padding: Dict[str, str] = field(default_factory=lambda: {
        "top": "0", "right": "0", "bottom": "0", "left": "0"
    })
    flex_props: Optional[Dict[str, str]] = None
    grid_props: Optional[Dict[str, str]] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


# ============ 布局类型枚举 ============

class LayoutType:
    """布局类型"""
    STATIC = "static"
    RELATIVE = "relative"
    ABSOLUTE = "absolute"
    FIXED = "fixed"
    STICKY = "sticky"
    FLEX = "flex"
    GRID = "grid"


# ============ 位置生成器 ============

class PositionGenerator:
    """位置生成器"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.logger = get_logger("position-generator")
        self.config = config or {}
        self.error_handler = get_error_handler()
        
        # 默认画布尺寸
        self.default_canvas_size = self.config.get("default_canvas_size", {
            "width": 1920,
            "height": 1080
        })
    
    def generate(self, position_info: Dict, canvas_size: Optional[Dict] = None) -> PositionSpec:
        """
        生成单个位置规格
        
        Args:
            position_info: 位置信息字典
            canvas_size: 画布尺寸 {"width": int, "height": int}
            
        Returns:
            PositionSpec: 位置规格对象
        """
        try:
            if canvas_size is None:
                canvas_size = self.default_canvas_size
            
            # 确定定位类型
            position_type = self._determine_position_type(position_info, canvas_size)
            
            # 生成坐标
            top, right, bottom, left = self._generate_coordinates(
                position_info, canvas_size, position_type
            )
            
            # 生成边距
            margin = self._generate_margin(position_info)
            
            # 生成内边距
            padding = self._generate_padding(position_info)
            
            # 生成 Flex 属性（如果有）
            flex_props = self._generate_flex_props(position_info)
            
            # 生成 Grid 属性（如果有）
            grid_props = self._generate_grid_props(position_info)
            
            spec = PositionSpec(
                position_type=position_type,
                top=top,
                right=right,
                bottom=bottom,
                left=left,
                margin=margin,
                padding=padding,
                flex_props=flex_props,
                grid_props=grid_props
            )
            
            self.logger.debug(f"生成位置规格: {position_type}")
            return spec
            
        except Exception as e:
            self.error_handler.record(
                task="position_generate",
                error=e,
                category=ErrorCategory.EXPORT_ERROR,
                context={"position_info": position_info}
            )
            return PositionSpec()
    
    def generate_batch(
        self,
        positions: List[Dict],
        canvas_size: Optional[Dict] = None
    ) -> List[PositionSpec]:
        """
        批量生成位置规格
        
        Args:
            positions: 位置信息列表
            canvas_size: 画布尺寸
            
        Returns:
            List[PositionSpec]: 位置规格列表
        """
        results = []
        for pos in positions:
            spec = self.generate(pos, canvas_size)
            results.append(spec)
        
        self.logger.info(f"批量生成 {len(results)} 个位置规格")
        return results
    
    def _determine_position_type(
        self,
        position_info: Dict,
        canvas_size: Dict
    ) -> str:
        """确定定位类型"""
        # 如果指定了类型，使用指定类型
        if "position_type" in position_info:
            return position_info["position_type"]
        
        # 根据图层属性推断
        kind = position_info.get("kind", "")
        layer_type = position_info.get("layer_type", "")
        
        # 组通常使用 relative
        if kind == "group":
            return LayoutType.RELATIVE
        
        # 装饰元素可能使用 absolute
        if layer_type == "decorator":
            # 检查是否是全屏定位
            bounds = position_info.get("bbox", {})
            if bounds.get("x", 0) == 0 and bounds.get("y", 0) == 0:
                if bounds.get("width") == canvas_size.get("width") and \
                   bounds.get("height") == canvas_size.get("height"):
                    return LayoutType.ABSOLUTE
        
        # 默认使用 relative
        return LayoutType.RELATIVE
    
    def _generate_coordinates(
        self,
        position_info: Dict,
        canvas_size: Dict,
        position_type: str
    ) -> tuple:
        """生成坐标值"""
        top = None
        right = None
        bottom = None
        left = None
        
        # 从 bbox 获取位置
        bbox = position_info.get("bbox", {})
        x = bbox.get("x", 0)
        y = bbox.get("y", 0)
        
        if position_type in [LayoutType.ABSOLUTE, LayoutType.FIXED, LayoutType.STICKY]:
            # 这些类型需要具体的坐标
            top = f"{y}px" if y > 0 else None
            left = f"{x}px" if x > 0 else None
            
            # 计算 right 和 bottom
            width = bbox.get("width", 0)
            height = bbox.get("height", 0)
            
            canvas_width = canvas_size.get("width", 1920)
            canvas_height = canvas_size.get("height", 1080)
            
            right_val = canvas_width - x - width
            bottom_val = canvas_height - y - height
            
            if right_val > 0:
                right = f"{right_val}px"
            if bottom_val > 0:
                bottom = f"{bottom_val}px"
        else:
            # relative 定位通常不需要具体坐标
            # 但可以记录原始偏移
            if x != 0 or y != 0:
                # 使用 transform 而非 top/left
                self.logger.debug(f"使用相对定位，偏移: ({x}, {y})")
        
        return top, right, bottom, left
    
    def _generate_margin(self, position_info: Dict) -> Dict[str, str]:
        """生成外边距"""
        margin = position_info.get("margin", {})
        
        if not margin:
            # 检查是否有 margin_* 属性
            return {
                "top": f"{margin.get('top', margin.get('margin_top', 0))}px",
                "right": f"{margin.get('right', margin.get('margin_right', 0))}px",
                "bottom": f"{margin.get('bottom', margin.get('margin_bottom', 0))}px",
                "left": f"{margin.get('left', margin.get('margin_left', 0))}px"
            }
        
        return {
            "top": f"{margin.get('top', 0)}px",
            "right": f"{margin.get('right', 0)}px",
            "bottom": f"{margin.get('bottom', 0)}px",
            "left": f"{margin.get('left', 0)}px"
        }
    
    def _generate_padding(self, position_info: Dict) -> Dict[str, str]:
        """生成内边距"""
        padding = position_info.get("padding", {})
        
        if not padding:
            return {
                "top": "0px",
                "right": "0px",
                "bottom": "0px",
                "left": "0px"
            }
        
        return {
            "top": f"{padding.get('top', 0)}px",
            "right": f"{padding.get('right', 0)}px",
            "bottom": f"{padding.get('bottom', 0)}px",
            "left": f"{padding.get('left', 0)}px"
        }
    
    def _generate_flex_props(self, position_info: Dict) -> Optional[Dict[str, str]]:
        """生成 Flex 属性"""
        flex = position_info.get("flex")
        
        if flex is None:
            # 检查是否是 flex 子元素
            parent_layout = position_info.get("parent_layout")
            if parent_layout == "flex":
                return self._generate_default_flex_props(position_info)
            return None
        
        if flex is False:
            return None
        
        return {
            "display": "flex",
            "flex_direction": flex.get("direction", "row"),
            "justify_content": flex.get("justify", "flex-start"),
            "align_items": flex.get("align", "stretch"),
            "flex_wrap": flex.get("wrap", "nowrap"),
            "gap": flex.get("gap", "0px")
        }
    
    def _generate_default_flex_props(self, position_info: Dict) -> Dict[str, str]:
        """生成默认 Flex 属性"""
        kind = position_info.get("kind", "")
        
        if kind == "group":
            return {
                "display": "flex",
                "flex_direction": "column",
                "justify_content": "flex-start",
                "align_items": "stretch"
            }
        
        return {
            "display": "flex",
            "flex_direction": "row"
        }
    
    def _generate_grid_props(self, position_info: Dict) -> Optional[Dict[str, str]]:
        """生成 Grid 属性"""
        grid = position_info.get("grid")
        
        if grid is None:
            return None
        
        if grid is False:
            return None
        
        return {
            "display": "grid",
            "grid_template_columns": grid.get("columns", "none"),
            "grid_template_rows": grid.get("rows", "none"),
            "gap": grid.get("gap", "0px"),
            "grid_area": grid.get("area", "auto")
        }
    
    def generate_layout_context(
        self,
        layer_info: Dict,
        canvas_size: Dict
    ) -> Dict:
        """
        生成布局上下文（包含父布局信息）
        
        Args:
            layer_info: 图层信息
            canvas_size: 画布尺寸
            
        Returns:
            Dict: 布局上下文
        """
        parent_id = layer_info.get("parent_id")
        kind = layer_info.get("kind", "")
        
        # 判断是否是 flex/grid 容器
        if kind == "group":
            # 检查子元素数量
            children = layer_info.get("children", [])
            if len(children) > 1:
                # 多子元素使用 flex
                return {
                    "layout_type": "flex",
                    "is_container": True,
                    "flex_direction": "column",
                    "children_count": len(children)
                }
        
        return {
            "layout_type": "static",
            "is_container": False
        }


# ============ 便捷函数 ============

def generate_position(
    position_info: Dict,
    canvas_size: Optional[Dict] = None
) -> PositionSpec:
    """生成位置规格（便捷函数）"""
    generator = PositionGenerator()
    return generator.generate(position_info, canvas_size)


def generate_positions_batch(
    positions: List[Dict],
    canvas_size: Optional[Dict] = None
) -> List[PositionSpec]:
    """批量生成位置规格（便捷函数）"""
    generator = PositionGenerator()
    return generator.generate_batch(positions, canvas_size)
