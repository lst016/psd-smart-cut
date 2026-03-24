"""
Level 3 - Function Analyzer
功能分析器

分析组件功能（按钮/输入框/卡片等），判断交互类型，
提取样式属性，生成功能描述。
"""
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass, field

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from skills.common import get_logger, get_config, get_error_handler, ErrorCategory


# ============ 交互类型定义 ============

class InteractionType:
    """交互类型常量"""
    CLICK = "click"
    INPUT = "input"
    HOVER = "hover"
    SCROLL = "scroll"
    DRAG = "drag"
    TOGGLE = "toggle"
    SELECT = "select"
    NAVIGATE = "navigate"
    DISPLAY = "display"  # 仅展示，无交互
    UNKNOWN = "unknown"


# ============ 样式属性提取 ============

@dataclass
class StyleAttributes:
    """样式属性"""
    # 尺寸
    width: int = 0
    height: int = 0
    # 颜色
    background_color: Optional[str] = None
    text_color: Optional[str] = None
    border_color: Optional[str] = None
    border_width: int = 0
    border_radius: int = 0
    # 字体
    font_size: int = 0
    font_weight: str = ""
    font_family: str = ""
    text_align: str = ""
    # 布局
    opacity: float = 1.0
    visibility: str = "visible"
    # 装饰
    has_shadow: bool = False
    has_gradient: bool = False
    is_filled: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "width": self.width,
            "height": self.height,
            "background_color": self.background_color,
            "text_color": self.text_color,
            "border_color": self.border_color,
            "border_width": self.border_width,
            "border_radius": self.border_radius,
            "font_size": self.font_size,
            "font_weight": self.font_weight,
            "font_family": self.font_family,
            "text_align": self.text_align,
            "opacity": self.opacity,
            "visibility": self.visibility,
            "has_shadow": self.has_shadow,
            "has_gradient": self.has_gradient,
            "is_filled": self.is_filled,
        }


@dataclass
class FunctionResult:
    """功能分析结果"""
    success: bool
    layer_id: str
    component_type: str
    interaction_types: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    style_attributes: Optional[Dict] = None
    description: str = ""
    accessibility_hints: List[str] = field(default_factory=list)
    error: Optional[str] = None


# ============ 组件功能规则 ============

COMPONENT_FUNCTION_RULES: Dict[str, Dict[str, Any]] = {
    "button": {
        "interaction_types": [InteractionType.CLICK],
        "functions": ["触发动作", "提交表单", "确认操作"],
        "description": "可点击的按钮组件，用于触发操作",
    },
    "input": {
        "interaction_types": [InteractionType.INPUT],
        "functions": ["文本输入", "搜索", "表单填写"],
        "description": "文本输入框，用于用户输入内容",
    },
    "card": {
        "interaction_types": [InteractionType.DISPLAY, InteractionType.CLICK],
        "functions": ["信息展示", "内容容器", "可点击跳转"],
        "description": "卡片容器，用于组织和展示信息",
    },
    "icon": {
        "interaction_types": [InteractionType.CLICK, InteractionType.HOVER],
        "functions": ["功能标识", "操作提示", "装饰"],
        "description": "图标组件，用于视觉标识和操作引导",
    },
    "text": {
        "interaction_types": [InteractionType.DISPLAY],
        "functions": ["文本展示", "信息传达"],
        "description": "文本组件，用于展示静态信息",
    },
    "heading": {
        "interaction_types": [InteractionType.DISPLAY],
        "functions": ["标题展示", "内容引导", "层级结构"],
        "description": "标题组件，用于页面或区块的标题",
    },
    "image": {
        "interaction_types": [InteractionType.DISPLAY, InteractionType.CLICK],
        "functions": ["图片展示", "视觉内容", "可点击查看大图"],
        "description": "图片组件，用于展示图像内容",
    },
    "navigation": {
        "interaction_types": [InteractionType.CLICK, InteractionType.HOVER],
        "functions": ["页面导航", "功能跳转", "菜单切换"],
        "description": "导航组件，用于页面间跳转和功能切换",
    },
    "list": {
        "interaction_types": [InteractionType.SCROLL, InteractionType.SELECT],
        "functions": ["列表展示", "多项选择", "滚动浏览"],
        "description": "列表组件，用于展示多项相关内容",
    },
    "modal": {
        "interaction_types": [InteractionType.CLICK],
        "functions": ["弹窗展示", "聚焦操作", "信息确认"],
        "description": "模态弹窗，用于聚焦用户注意力和操作",
    },
    "checkbox": {
        "interaction_types": [InteractionType.CLICK, InteractionType.TOGGLE],
        "functions": ["多选", "状态切换", "表单选项"],
        "description": "复选框组件，用于多选操作",
    },
    "radio": {
        "interaction_types": [InteractionType.CLICK, InteractionType.SELECT],
        "functions": ["单选", "选项切换", "表单选项"],
        "description": "单选框组件，用于单选操作",
    },
    "toggle": {
        "interaction_types": [InteractionType.TOGGLE],
        "functions": ["开关切换", "状态变更", "设置选项"],
        "description": "开关组件，用于二元状态切换",
    },
    "dropdown": {
        "interaction_types": [InteractionType.CLICK, InteractionType.SELECT],
        "functions": ["下拉选择", "选项展开", "表单输入"],
        "description": "下拉选择框，用于从多个选项中选择",
    },
    "tooltip": {
        "interaction_types": [InteractionType.HOVER],
        "functions": ["提示信息", "操作说明", "帮助提示"],
        "description": "工具提示组件，用于显示附加信息",
    },
    "badge": {
        "interaction_types": [InteractionType.DISPLAY],
        "functions": ["数量展示", "状态标识", "新内容提示"],
        "description": "徽章组件，用于显示数量或状态",
    },
    "divider": {
        "interaction_types": [InteractionType.DISPLAY],
        "functions": ["视觉分隔", "内容分区", "区域划分"],
        "description": "分割线组件，用于视觉上分隔内容",
    },
    "avatar": {
        "interaction_types": [InteractionType.DISPLAY, InteractionType.CLICK],
        "functions": ["用户标识", "头像展示", "个人中心入口"],
        "description": "头像组件，用于展示用户图片",
    },
    "progress": {
        "interaction_types": [InteractionType.DISPLAY],
        "functions": ["进度展示", "加载状态", "完成度提示"],
        "description": "进度条组件，用于展示进度或加载状态",
    },
    "unknown": {
        "interaction_types": [InteractionType.UNKNOWN],
        "functions": ["未知功能"],
        "description": "未知组件类型",
    },
}


class FunctionAnalyzer:
    """
    功能分析器

    分析组件功能、交互类型、样式属性，生成功能描述。
    """

    def __init__(self):
        self.logger = get_logger("function-analyzer")
        self.config = get_config()
        self.error_handler = get_error_handler()

    def _extract_style_attributes(
        self,
        layer_metadata: Dict[str, Any]
    ) -> StyleAttributes:
        """
        从图层元数据提取样式属性

        Args:
            layer_metadata: 图层元数据

        Returns:
            StyleAttributes
        """
        style = StyleAttributes()

        # 尺寸
        dimensions = layer_metadata.get("dimensions", {})
        style.width = dimensions.get("width", 0)
        style.height = dimensions.get("height", 0)

        # 样式属性
        fill = layer_metadata.get("fill", {})
        if isinstance(fill, dict):
            style.background_color = fill.get("color", "")
            style.is_filled = fill.get("visible", True)
        elif isinstance(fill, list) and len(fill) > 0:
            style.background_color = fill[0].get("color", "") if isinstance(fill[0], dict) else str(fill[0])
            style.is_filled = True

        # 边框
        border = layer_metadata.get("border", {})
        if isinstance(border, dict):
            style.border_color = border.get("color", "")
            style.border_width = border.get("width", 0)
            style.border_radius = border.get("radius", 0)

        # 文本属性
        text = layer_metadata.get("text", {})
        if isinstance(text, dict):
            style.font_size = text.get("size", 0)
            style.font_weight = text.get("weight", "")
            style.font_family = text.get("font_family", "")
            style.text_color = text.get("color", "")
            style.text_align = text.get("align", "")

        # 效果
        effects = layer_metadata.get("effects", {})
        style.has_shadow = effects.get("shadow", False)
        style.has_gradient = effects.get("gradient", False)

        # 透明度
        style.opacity = layer_metadata.get("opacity", 1.0)

        return style

    def _infer_interaction_from_style(
        self,
        style: StyleAttributes,
        component_type: str
    ) -> List[str]:
        """
        根据样式属性推断交互类型

        Args:
            style: 样式属性
            component_type: 组件类型

        Returns:
            交互类型列表
        """
        interactions = list(COMPONENT_FUNCTION_RULES.get(component_type, {}).get("interaction_types", []))

        # 根据样式特征调整
        if component_type == "unknown":
            # 未知类型，根据样式特征推断
            if style.border_width > 0 and style.border_radius > 0:
                interactions = [InteractionType.CLICK]
            elif style.is_filled and style.background_color:
                interactions = [InteractionType.DISPLAY]
            else:
                interactions = [InteractionType.DISPLAY]

        # 有hover效果说明支持hover交互
        if style.has_shadow:
            if InteractionType.HOVER not in interactions:
                interactions.append(InteractionType.HOVER)

        return list(set(interactions))  # 去重

    def _generate_description(
        self,
        component_type: str,
        component_name: str,
        style: StyleAttributes,
        functions: List[str]
    ) -> str:
        """
        生成功能描述

        Args:
            component_type: 组件类型
            component_name: 组件名称
            style: 样式属性
            functions: 功能列表

        Returns:
            功能描述字符串
        """
        base_desc = COMPONENT_FUNCTION_RULES.get(component_type, {}).get("description", "未知组件")

        # 构建完整描述
        parts = [base_desc]

        if component_name:
            parts.insert(0, f"【{component_name}】")

        # 添加尺寸信息
        if style.width > 0 and style.height > 0:
            parts.append(f"尺寸 {style.width}x{style.height}")

        # 添加样式特征
        style_features = []
        if style.has_shadow:
            style_features.append("有阴影")
        if style.has_gradient:
            style_features.append("有渐变")
        if style.border_radius > 0:
            style_features.append(f"圆角 {style.border_radius}px")

        if style_features:
            parts.append(" | ".join(style_features))

        return " ".join(parts)

    def _get_accessibility_hints(
        self,
        component_type: str,
        interaction_types: List[str],
        style: StyleAttributes
    ) -> List[str]:
        """
        生成无障碍提示

        Args:
            component_type: 组件类型
            interaction_types: 交互类型
            style: 样式属性

        Returns:
            无障碍提示列表
        """
        hints = []

        # 基础无障碍
        if InteractionType.CLICK in interaction_types:
            hints.append("可通过 Tab 键聚焦")
            hints.append("可通过 Enter 或 Space 激活")

        if InteractionType.INPUT in interaction_types:
            hints.append("可通过键盘输入内容")
            hints.append("建议提供 label 标签")

        if InteractionType.TOGGLE in interaction_types:
            hints.append("状态切换应提供视觉反馈")

        # 文本可访问性
        if component_type in ["text", "heading"] and style.font_size < 14:
            hints.append("字号较小，建议提供放大选项")

        return hints

    def analyze(
        self,
        layer_metadata: Dict[str, Any],
        component_type: Optional[str] = None,
        component_name: Optional[str] = None
    ) -> FunctionResult:
        """
        完整功能分析

        Args:
            layer_metadata: 图层元数据
            component_type: 已知组件类型（可选）
            component_name: 已知组件名称（可选）

        Returns:
            FunctionResult
        """
        layer_id = layer_metadata.get("layer_id", "unknown")

        try:
            # 1. 确定组件类型
            if not component_type:
                component_type = layer_metadata.get("component_type", "unknown")

            # 2. 提取样式属性
            style = self._extract_style_attributes(layer_metadata)

            # 3. 推断交互类型
            interaction_types = self._infer_interaction_from_style(style, component_type)

            # 4. 获取功能列表
            functions = list(COMPONENT_FUNCTION_RULES.get(component_type, {}).get("functions", ["未知功能"]))

            # 5. 生成功能描述
            description = self._generate_description(
                component_type,
                component_name or "",
                style,
                functions
            )

            # 6. 生成无障碍提示
            accessibility_hints = self._get_accessibility_hints(
                component_type,
                interaction_types,
                style
            )

            result = FunctionResult(
                success=True,
                layer_id=layer_id,
                component_type=component_type,
                interaction_types=interaction_types,
                functions=functions,
                style_attributes=style.to_dict(),
                description=description,
                accessibility_hints=accessibility_hints
            )

            self.logger.debug(
                f"功能分析完成: layer_id={layer_id}, "
                f"type={component_type}, interactions={interaction_types}"
            )

            return result

        except Exception as e:
            self.logger.error(f"功能分析失败: {e}")
            self.error_handler.record(
                task="function_analyze",
                error=e,
                category=ErrorCategory.PARSE_ERROR,
                context={"layer_id": layer_id}
            )
            return FunctionResult(
                success=False,
                layer_id=layer_id,
                component_type="unknown",
                error=str(e)
            )

    def batch_analyze(
        self,
        items: List[Dict[str, Any]]
    ) -> List[FunctionResult]:
        """
        批量功能分析

        Args:
            items: 项目列表，每个包含 layer_metadata 和可选的 component_type

        Returns:
            FunctionResult 列表
        """
        results = []
        for item in items:
            layer_metadata = item.get("layer_metadata", item)
            component_type = item.get("component_type")
            component_name = item.get("component_name")

            result = self.analyze(layer_metadata, component_type, component_name)
            results.append(result)

        success_count = sum(1 for r in results if r.success)
        self.logger.info(f"批量功能分析完成: {success_count}/{len(items)} 成功")

        return results

    def get_interaction_summary(
        self,
        results: List[FunctionResult]
    ) -> Dict[str, Any]:
        """
        从多个分析结果中汇总交互信息

        Args:
            results: FunctionResult 列表

        Returns:
            交互汇总
        """
        all_interactions: Set[str] = set()
        all_functions: Set[str] = set()
        type_counts: Dict[str, int] = {}

        for result in results:
            if result.success:
                all_interactions.update(result.interaction_types)
                all_functions.update(result.functions)
                ct = result.component_type
                type_counts[ct] = type_counts.get(ct, 0) + 1

        return {
            "total_components": len(results),
            "interaction_types": sorted(list(all_interactions)),
            "all_functions": sorted(list(all_functions)),
            "component_type_counts": dict(sorted(type_counts.items(), key=lambda x: x[1], reverse=True)),
            "clickable_count": sum(
                1 for r in results
                if r.success and InteractionType.CLICK in r.interaction_types
            ),
            "input_count": sum(
                1 for r in results
                if r.success and InteractionType.INPUT in r.interaction_types
            ),
        }
