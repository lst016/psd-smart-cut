"""
Level 7 - Spec Validator
规格验证器 - 验证组件规格的完整性和正确性
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from skills.common import get_logger, get_config, get_error_handler, ErrorCategory

# ============ 数据类 ============

@dataclass
class ValidationError:
    """验证错误"""
    field: str
    message: str
    severity: str = "error"  # error/warning/info
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ValidationResult:
    """验证结果"""
    valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "valid": self.valid,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings]
        }
    
    @property
    def error_count(self) -> int:
        return len(self.errors)
    
    @property
    def warning_count(self) -> int:
        return len(self.warnings)


# ============ CSS 验证器 ============

class CSSValidator:
    """CSS 语法验证器"""
    
    # 有效的 CSS 属性
    VALID_PROPERTIES = {
        # 尺寸
        "width", "height", "min-width", "max-width", "min-height", "max-height",
        # 定位
        "position", "top", "right", "bottom", "left", "z-index",
        # 边距
        "margin", "margin-top", "margin-right", "margin-bottom", "margin-left",
        # 内边距
        "padding", "padding-top", "padding-right", "padding-bottom", "padding-left",
        # 边框
        "border", "border-width", "border-style", "border-color",
        "border-top", "border-right", "border-bottom", "border-left",
        "border-radius",
        # 背景
        "background", "background-color", "background-image", "background-position",
        "background-size", "background-repeat",
        # 字体
        "font", "font-family", "font-size", "font-weight", "font-style",
        "line-height", "letter-spacing", "text-align", "text-decoration",
        # 颜色
        "color", "opacity",
        # 显示
        "display", "flex", "flex-direction", "justify-content", "align-items",
        "flex-wrap", "flex-grow", "flex-shrink", "flex-basis", "gap",
        "grid", "grid-template-columns", "grid-template-rows", "grid-gap",
        # 效果
        "box-shadow", "transform", "transition", "animation",
        "mix-blend-mode",
        # 其他
        "overflow", "visibility", "cursor", "pointer-events"
    }
    
    # 有效的 position 值
    VALID_POSITION_VALUES = {"static", "relative", "absolute", "fixed", "sticky"}
    
    # 有效的 display 值
    VALID_DISPLAY_VALUES = {
        "none", "block", "inline", "inline-block", "flex", "inline-flex",
        "grid", "inline-grid", "table", "inline-table", "list-item"
    }
    
    # 有效的 flex-direction 值
    VALID_FLEX_DIRECTIONS = {
        "row", "row-reverse", "column", "column-reverse"
    }
    
    # 有效的 justify-content 值
    VALID_JUSTIFY_CONTENT = {
        "flex-start", "flex-end", "center", "space-between", "space-around",
        "space-evenly", "start", "end", "left", "right"
    }
    
    # 有效的 align-items 值
    VALID_ALIGN_ITEMS = {
        "stretch", "flex-start", "flex-end", "center", "baseline", "start", "end"
    }
    
    @classmethod
    def validate_property(cls, property_name: str, value: str) -> List[ValidationError]:
        """验证单个 CSS 属性"""
        errors = []
        
        # 检查属性名是否有效
        if property_name not in cls.VALID_PROPERTIES:
            # 允许自定义变量
            if not property_name.startswith("--") and not property_name.startswith("-"):
                errors.append(ValidationError(
                    field=f"css.{property_name}",
                    message=f"未知的 CSS 属性: {property_name}",
                    severity="warning"
                ))
        
        # 验证 position
        if property_name == "position":
            if value not in cls.VALID_POSITION_VALUES:
                errors.append(ValidationError(
                    field="css.position",
                    message=f"无效的 position 值: {value}",
                    severity="error"
                ))
        
        # 验证 display
        if property_name == "display":
            if value not in cls.VALID_DISPLAY_VALUES:
                errors.append(ValidationError(
                    field="css.display",
                    message=f"无效的 display 值: {value}",
                    severity="error"
                ))
        
        # 验证 flex-direction
        if property_name == "flex-direction":
            if value not in cls.VALID_FLEX_DIRECTIONS:
                errors.append(ValidationError(
                    field="css.flex-direction",
                    message=f"无效的 flex-direction 值: {value}",
                    severity="error"
                ))
        
        # 验证 justify-content
        if property_name == "justify-content":
            if value not in cls.VALID_JUSTIFY_CONTENT:
                errors.append(ValidationError(
                    field="css.justify-content",
                    message=f"无效的 justify-content 值: {value}",
                    severity="error"
                ))
        
        # 验证 align-items
        if property_name == "align-items":
            if value not in cls.VALID_ALIGN_ITEMS:
                errors.append(ValidationError(
                    field="css.align-items",
                    message=f"无效的 align-items 值: {value}",
                    severity="error"
                ))
        
        # 验证数值属性
        numeric_props = {
            "width", "height", "min-width", "max-width", "min-height", "max-height",
            "top", "right", "bottom", "left", "z-index",
            "margin", "margin-top", "margin-right", "margin-bottom", "margin-left",
            "padding", "padding-top", "padding-right", "padding-bottom", "padding-left",
            "border-width", "border-radius",
            "font-size", "line-height", "letter-spacing",
            "opacity", "flex-grow", "flex-shrink", "flex-basis"
        }
        
        if property_name in numeric_props:
            if property_name == "z-index":
                # z-index 可以是 auto 或整数
                if value != "auto" and not value.lstrip('-').isdigit():
                    errors.append(ValidationError(
                        field=f"css.{property_name}",
                        message=f"无效的 {property_name} 值: {value}",
                        severity="error"
                    ))
            elif not any(unit in str(value) for unit in ["px", "rem", "em", "%", "vh", "vw", "pt"]):
                if not value.replace(".", "").replace("-", "").isdigit():
                    errors.append(ValidationError(
                        field=f"css.{property_name}",
                        message=f"数值属性需要单位: {property_name}: {value}",
                        severity="warning"
                    ))
        
        return errors
    
    @classmethod
    def validate_css_dict(cls, css: Dict[str, str]) -> List[ValidationError]:
        """验证 CSS 字典"""
        errors = []
        
        for prop, value in css.items():
            prop_errors = cls.validate_property(prop, str(value))
            errors.extend(prop_errors)
        
        return errors


# ============ 规格验证器 ============

class SpecValidator:
    """规格验证器"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.logger = get_logger("spec-validator")
        self.config = config or {}
        self.error_handler = get_error_handler()
        self.css_validator = CSSValidator()
        
        # 响应式断点
        self.breakpoints = self.config.get("breakpoints", {
            "mobile": 480,
            "tablet": 768,
            "desktop": 1024,
            "wide": 1440
        })
    
    def validate(self, spec: Dict) -> ValidationResult:
        """
        验证单个规格
        
        Args:
            spec: 规格字典
            
        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        warnings = []
        
        # 验证必需字段
        required_fields = ["id", "name"]
        for field in required_fields:
            if field not in spec:
                errors.append(ValidationError(
                    field=field,
                    message=f"缺少必需字段: {field}",
                    severity="error"
                ))
        
        # 验证 dimensions
        if "dimensions" in spec:
            dim_errors, dim_warnings = self._validate_dimensions(spec["dimensions"])
            errors.extend(dim_errors)
            warnings.extend(dim_warnings)
        
        # 验证 position
        if "position" in spec:
            pos_errors, pos_warnings = self._validate_position(spec["position"])
            errors.extend(pos_errors)
            warnings.extend(pos_warnings)
        
        # 验证 style
        if "style" in spec:
            style_errors, style_warnings = self._validate_style(spec["style"])
            errors.extend(style_errors)
            warnings.extend(style_warnings)
        
        # 验证 children
        if "children" in spec:
            child_warnings = self._validate_children(spec["children"])
            warnings.extend(child_warnings)
        
        # 验证响应式断点
        if "responsive" in spec:
            resp_errors, resp_warnings = self._validate_responsive(spec["responsive"])
            errors.extend(resp_errors)
            warnings.extend(resp_warnings)
        
        result = ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
        
        if not result.valid:
            self.logger.warning(f"规格验证失败: {len(errors)} 个错误")
        elif warnings:
            self.logger.info(f"规格验证通过: {len(warnings)} 个警告")
        else:
            self.logger.debug(f"规格验证通过")
        
        return result
    
    def validate_batch(self, specs: List[Dict]) -> List[ValidationResult]:
        """
        批量验证规格
        
        Args:
            specs: 规格列表
            
        Returns:
            List[ValidationResult]: 验证结果列表
        """
        results = []
        for spec in specs:
            result = self.validate(spec)
            results.append(result)
        
        # 汇总统计
        total_errors = sum(r.error_count for r in results)
        total_warnings = sum(r.warning_count for r in results)
        
        self.logger.info(
            f"批量验证 {len(results)} 个规格: "
            f"{total_errors} 错误, {total_warnings} 警告"
        )
        
        return results
    
    def _validate_dimensions(
        self, dimensions: Dict
    ) -> tuple:
        """验证尺寸规格"""
        errors = []
        warnings = []
        
        # 必需字段
        if "width" not in dimensions:
            errors.append(ValidationError(
                field="dimensions.width",
                message="缺少 width 字段",
                severity="error"
            ))
        
        if "height" not in dimensions:
            errors.append(ValidationError(
                field="dimensions.height",
                message="缺少 height 字段",
                severity="error"
            ))
        
        # 数值检查
        if "width" in dimensions:
            width = dimensions["width"]
            if isinstance(width, (int, float)) and width <= 0:
                errors.append(ValidationError(
                    field="dimensions.width",
                    message=f"width 必须大于 0: {width}",
                    severity="error"
                ))
        
        if "height" in dimensions:
            height = dimensions["height"]
            if isinstance(height, (int, float)) and height <= 0:
                errors.append(ValidationError(
                    field="dimensions.height",
                    message=f"height 必须大于 0: {height}",
                    severity="error"
                ))
        
        # 单位检查
        valid_units = {"px", "rem", "dp", "pt", "em", "vh", "vw", "%"}
        unit = dimensions.get("unit", "px")
        if unit not in valid_units:
            warnings.append(ValidationError(
                field="dimensions.unit",
                message=f"非标准单位: {unit}",
                severity="warning"
            ))
        
        # min/max 宽度检查
        min_width = dimensions.get("min_width")
        max_width = dimensions.get("max_width")
        width = dimensions.get("width", 0)
        
        if min_width is not None and width > 0:
            if min_width > width:
                errors.append(ValidationError(
                    field="dimensions.min_width",
                    message=f"min_width 大于 width: {min_width} > {width}",
                    severity="error"
                ))
        
        if max_width is not None and width > 0:
            if max_width < width:
                errors.append(ValidationError(
                    field="dimensions.max_width",
                    message=f"max_width 小于 width: {max_width} < {width}",
                    severity="error"
                ))
        
        if min_width is not None and max_width is not None:
            if min_width > max_width:
                errors.append(ValidationError(
                    field="dimensions",
                    message=f"min_width 大于 max_width: {min_width} > {max_width}",
                    severity="error"
                ))
        
        # 缩放因子检查
        scale_factors = dimensions.get("scale_factors", [])
        if not scale_factors:
            warnings.append(ValidationError(
                field="dimensions.scale_factors",
                message="缺少缩放因子",
                severity="warning"
            ))
        else:
            for sf in scale_factors:
                if sf <= 0:
                    errors.append(ValidationError(
                        field="dimensions.scale_factors",
                        message=f"无效的缩放因子: {sf}",
                        severity="error"
                    ))
        
        return errors, warnings
    
    def _validate_position(
        self, position: Dict
    ) -> tuple:
        """验证位置规格"""
        errors = []
        warnings = []
        
        # position_type 检查
        position_type = position.get("position_type", "relative")
        valid_types = {"static", "relative", "absolute", "fixed", "sticky"}
        if position_type not in valid_types:
            errors.append(ValidationError(
                field="position.position_type",
                message=f"无效的 position_type: {position_type}",
                severity="error"
            ))
        
        # 坐标检查
        coords = ["top", "right", "bottom", "left"]
        for coord in coords:
            value = position.get(coord)
            if value is not None:
                if not isinstance(value, str):
                    errors.append(ValidationError(
                        field=f"position.{coord}",
                        message=f"{coord} 必须是字符串: {value}",
                        severity="error"
                    ))
        
        # margin/padding 检查
        for prop in ["margin", "padding"]:
            if prop in position:
                prop_data = position[prop]
                if not isinstance(prop_data, dict):
                    errors.append(ValidationError(
                        field=f"position.{prop}",
                        message=f"{prop} 必须是字典",
                        severity="error"
                    ))
        
        # flex_props 检查
        flex_props = position.get("flex_props")
        if flex_props is not None:
            if not isinstance(flex_props, dict):
                errors.append(ValidationError(
                    field="position.flex_props",
                    message="flex_props 必须是字典",
                    severity="error"
                ))
        
        # grid_props 检查
        grid_props = position.get("grid_props")
        if grid_props is not None:
            if not isinstance(grid_props, dict):
                errors.append(ValidationError(
                    field="position.grid_props",
                    message="grid_props 必须是字典",
                    severity="error"
                ))
        
        return errors, warnings
    
    def _validate_style(
        self, style: Dict
    ) -> tuple:
        """验证样式规格"""
        errors = []
        warnings = []
        
        # CSS 验证
        if "css" in style:
            css = style["css"]
            if not isinstance(css, dict):
                errors.append(ValidationError(
                    field="style.css",
                    message="css 必须是字典",
                    severity="error"
                ))
            else:
                css_errors = CSSValidator.validate_css_dict(css)
                errors.extend([
                    ValidationError(field=f"style.{e.field}", message=e.message, severity=e.severity)
                    for e in css_errors
                ])
        
        # Tailwind 验证
        if "tailwind" in style:
            tailwind = style["tailwind"]
            if not isinstance(tailwind, list):
                errors.append(ValidationError(
                    field="style.tailwind",
                    message="tailwind 必须是列表",
                    severity="error"
                ))
        
        # iOS 验证
        if "ios" in style:
            ios = style["ios"]
            if not isinstance(ios, dict):
                errors.append(ValidationError(
                    field="style.ios",
                    message="ios 必须是字典",
                    severity="error"
                ))
        
        # Android 验证
        if "android" in style:
            android = style["android"]
            if not isinstance(android, dict):
                errors.append(ValidationError(
                    field="style.android",
                    message="android 必须是字典",
                    severity="error"
                ))
        
        # theme_vars 验证
        if "theme_vars" in style:
            theme_vars = style["theme_vars"]
            if not isinstance(theme_vars, dict):
                errors.append(ValidationError(
                    field="style.theme_vars",
                    message="theme_vars 必须是字典",
                    severity="error"
                ))
        
        return errors, warnings
    
    def _validate_children(
        self, children: List
    ) -> List[ValidationError]:
        """验证子元素"""
        warnings = []
        
        if not isinstance(children, list):
            warnings.append(ValidationError(
                field="children",
                message="children 必须是列表",
                severity="error"
            ))
        
        return warnings
    
    def _validate_responsive(
        self, responsive: Dict
    ) -> tuple:
        """验证响应式规格"""
        errors = []
        warnings = []
        
        if not isinstance(responsive, dict):
            errors.append(ValidationError(
                field="responsive",
                message="responsive 必须是字典",
                severity="error"
            ))
            return errors, warnings
        
        # 检查断点
        for breakpoint, value in responsive.items():
            if breakpoint not in self.breakpoints:
                warnings.append(ValidationError(
                    field=f"responsive.{breakpoint}",
                    message=f"未知的断点: {breakpoint}",
                    severity="warning"
                ))
            
            if not isinstance(value, dict):
                errors.append(ValidationError(
                    field=f"responsive.{breakpoint}",
                    message=f"断点值必须是字典: {breakpoint}",
                    severity="error"
                ))
        
        return errors, warnings
    
    def check_conflicts(self, spec: Dict) -> List[ValidationError]:
        """检查冲突属性"""
        errors = []
        
        # position 与 flex/grid 冲突
        position_type = spec.get("position", {}).get("position_type", "static")
        flex_props = spec.get("position", {}).get("flex_props")
        grid_props = spec.get("position", {}).get("grid_props")
        
        if position_type in ["absolute", "fixed", "sticky"]:
            if flex_props:
                errors.append(ValidationError(
                    field="position.flex_props",
                    message="absolute/fixed/sticky 定位与 flex 冲突",
                    severity="warning"
                ))
            if grid_props:
                errors.append(ValidationError(
                    field="position.grid_props",
                    message="absolute/fixed/sticky 定位与 grid 冲突",
                    severity="warning"
                ))
        
        # display 与 flex_props/grid_props 冲突
        display = spec.get("style", {}).get("css", {}).get("display")
        if display == "flex" and flex_props is None:
            errors.append(ValidationError(
                field="style.css.display",
                message="display: flex 但缺少 flex_props",
                severity="warning"
            ))
        
        if display == "grid" and grid_props is None:
            errors.append(ValidationError(
                field="style.css.display",
                message="display: grid 但缺少 grid_props",
                severity="warning"
            ))
        
        return errors


# ============ 便捷函数 ============

def validate_spec(spec: Dict) -> ValidationResult:
    """验证规格（便捷函数）"""
    validator = SpecValidator()
    return validator.validate(spec)


def validate_specs_batch(specs: List[Dict]) -> List[ValidationResult]:
    """批量验证规格（便捷函数）"""
    validator = SpecValidator()
    return validator.validate_batch(specs)
