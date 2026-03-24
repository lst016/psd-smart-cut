"""
Level 3 - Component Namer
组件命名器

基于截图和元数据命名组件，使用 AI（MiniMax VLM）识别组件类型，
生成语义化名称，支持批量命名。
"""
import sys
import json
import base64
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from skills.common import get_logger, get_config, get_error_handler, ErrorCategory


@dataclass
class NamingResult:
    """命名结果"""
    success: bool
    layer_id: str
    component_name: str = ""
    component_type: str = ""  # button, input, card, etc.
    confidence: float = 0.0
    reasoning: str = ""
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============ 组件类型映射 ============

KNOWN_COMPONENT_TYPES = {
    "button": ["按钮", "btn", "button", "submit", "确认", "登录", "注册"],
    "input": ["输入框", "input", "textfield", "搜索", "搜索框"],
    "card": ["卡片", "card", "面板", "panel", "容器"],
    "icon": ["图标", "icon", "logo", "标识"],
    "text": ["文本", "text", "标题", "heading", "paragraph"],
    "image": ["图片", "image", "照片", "photo", "banner"],
    "navigation": ["导航", "nav", "菜单", "menu", "tab"],
    "list": ["列表", "list", "item", "条目"],
    "modal": ["弹窗", "modal", "对话框", "dialog"],
    "checkbox": ["复选框", "checkbox", "check"],
    "radio": ["单选框", "radio"],
    "toggle": ["开关", "toggle", "switch"],
    "dropdown": ["下拉框", "dropdown", "select"],
    "tooltip": ["提示", "tooltip", "气泡"],
    "badge": ["徽章", "badge", "标签"],
    "divider": ["分割线", "divider", "separator"],
    "avatar": ["头像", "avatar", "用户图"],
    "progress": ["进度条", "progress", "loading"],
}


def guess_type_from_name(name: str, layer_type: str = "") -> str:
    """
    从图层名称和类型猜测组件类型

    Args:
        name: 图层名称
        layer_type: 图层类型（如 "pixel", "text"）

    Returns:
        猜测的组件类型
    """
    name_lower = name.lower()

    # 优先检测图层类型
    if layer_type == "text":
        if any(k in name_lower for k in ["title", "heading", "标题"]):
            return "heading"
        # 文本图层中的输入类组件
        if any(k in name_lower for k in ["input", "输入", "搜索", "search"]):
            return "input"
        return "text"

    if layer_type == "vector":
        if any(k in name_lower for k in ["icon", "图标", "logo"]):
            return "icon"

    # 关键词匹配
    for component_type, keywords in KNOWN_COMPONENT_TYPES.items():
        if any(k in name_lower for k in keywords):
            return component_type

    return "unknown"


def generate_component_name(
    layer_name: str,
    component_type: str,
    index: int = 0,
    context: Optional[Dict] = None
) -> str:
    """
    基于图层名称和类型生成语义化组件名

    Args:
        layer_name: 原始图层名称
        component_type: 组件类型
        index: 序号（同类组件从 1 开始计数）
        context: 上下文信息（如父图层名称）

    Returns:
        语义化组件名称
    """
    # 清理图层名称（去掉序号前缀如 "123_"）
    cleaned = layer_name
    import re
    cleaned = re.sub(r'^\d+[_:]?', '', cleaned)
    cleaned = re.sub(r'[_\-]+$', '', cleaned)

    # 去除 PSD 图层后缀
    for suffix in ["_copy", "_copy2", "_group", "_compound"]:
        if cleaned.endswith(suffix):
            cleaned = cleaned[:-len(suffix)]

    # 生成语义化名称
    type_prefix_map = {
        "button": "Button",
        "input": "Input",
        "card": "Card",
        "icon": "Icon",
        "text": "Text",
        "heading": "Heading",
        "image": "Image",
        "navigation": "Nav",
        "list": "List",
        "list_item": "ListItem",
        "modal": "Modal",
        "checkbox": "Checkbox",
        "radio": "Radio",
        "toggle": "Toggle",
        "dropdown": "Dropdown",
        "tooltip": "Tooltip",
        "badge": "Badge",
        "divider": "Divider",
        "avatar": "Avatar",
        "progress": "Progress",
        "unknown": "Element",
    }

    prefix = type_prefix_map.get(component_type, "Element")

    # 尝试从名称提取语义词
    semantic_words = []
    for word in re.findall(r'[\u4e00-\u9fa5a-zA-Z]+', cleaned):
        if len(word) >= 2:
            semantic_words.append(word.capitalize())

    if semantic_words:
        base_name = "".join(semantic_words[:3])  # 最多取前 3 个词
    else:
        base_name = f"Component{index}" if index > 0 else "Component"

    if index > 0:
        return f"{prefix}{base_name}{index}"
    return f"{prefix}{base_name}"


class ComponentNamer:
    """
    组件命名器

    基于截图和元数据，使用 AI（MiniMax VLM）识别组件类型，
    生成语义化名称。
    """

    def __init__(self, use_ai: bool = True):
        """
        Args:
            use_ai: 是否使用 AI 识别（需要 MiniMax MCP）
        """
        self.use_ai = use_ai
        self.logger = get_logger("component-namer")
        self.config = get_config()
        self.error_handler = get_error_handler()
        self._name_cache: Dict[str, NamingResult] = {}

    def _call_minimax_vlm(
        self,
        image_path: str,
        prompt: str
    ) -> Optional[Dict[str, Any]]:
        """
        调用 MiniMax VLM 进行图像识别

        Args:
            image_path: 截图路径
            prompt: 提示词

        Returns:
            AI 响应结果
        """
        if not self.use_ai:
            return None

        try:
            # 使用 OpenClaw 的 image 工具进行图像分析
            # 这里通过 MCP 调用 MiniMax VLM
            # 由于是 skill 内部调用，我们通过 subprocess 调用 minimax-mcp
            import subprocess
            import tempfile

            # 构造 prompt
            full_prompt = f"""{prompt}

请以 JSON 格式返回，字段：
- component_type: 组件类型（button/input/card/icon/text/image/navigation/list/modal/checkbox/radio/toggle/dropdown/tooltip/badge/divider/avatar/progress/unknown）
- component_name: 语义化英文名称
- confidence: 置信度 0-1
- reasoning: 识别理由

只返回 JSON，不要其他文字。"""

            # 使用 curl 调用 MiniMax API（如果有 API Key）
            api_key = self.config.get("minimax.api_key") or os.environ.get("MINIMAX_API_KEY")
            api_host = self.config.get("minimax.api_host") or "https://api.minimax.com"

            if api_key:
                with open(image_path, "rb") as f:
                    image_data = base64.b64encode(f.read()).decode()

                result = subprocess.run(
                    [
                        "curl", "-s", "-X", "POST",
                        f"{api_host}/v1/image_understanding",
                        "-H", f"Authorization: Bearer {api_key}",
                        "-H", "Content-Type: application/json",
                        "-d", json.dumps({
                            "model": "MiniMax-M2.5-highspeed",
                            "messages": [
                                {"role": "user", "content": [
                                    {"type": "image_url", "image_url": f"data:image/png;base64,{image_data}"},
                                    {"type": "text", "text": full_prompt}
                                ]}
                            ]
                        })
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    response = json.loads(result.stdout)
                    return response.get("choices", [{}])[0].get("message", {}).get("content")

            return None

        except Exception as e:
            self.logger.warning(f"MiniMax VLM 调用失败: {e}")
            return None

    def name_from_metadata(
        self,
        layer_metadata: Dict[str, Any],
        screenshot_path: Optional[str] = None
    ) -> NamingResult:
        """
        基于元数据（和可选的截图）命名组件

        Args:
            layer_metadata: 图层元数据
            screenshot_path: 截图路径（可选）

        Returns:
            NamingResult
        """
        layer_id = layer_metadata.get("layer_id", "unknown")
        layer_name = layer_metadata.get("name", layer_metadata.get("layer_name", ""))
        layer_type = layer_metadata.get("type", layer_metadata.get("kind", ""))

        # 检查缓存
        cache_key = f"{layer_id}:{screenshot_path or 'no_screenshot'}"
        if cache_key in self._name_cache:
            return self._name_cache[cache_key]

        try:
            # 1. 优先使用 AI 识别
            ai_result = None
            if screenshot_path and self.use_ai:
                ai_result = self._call_minimax_vlm(
                    screenshot_path,
                    prompt=f"识别这个 UI 组件的类型和名称，图层原始名称是：{layer_name}"
                )

            # 2. 基于元数据推断
            if ai_result:
                try:
                    result_data = json.loads(ai_result)
                    component_type = result_data.get("component_type", "unknown")
                    component_name = result_data.get("component_name", "")
                    confidence = float(result_data.get("confidence", 0.5))
                except json.JSONDecodeError:
                    component_type = guess_type_from_name(layer_name, layer_type)
                    component_name = generate_component_name(layer_name, component_type)
                    confidence = 0.5
            else:
                component_type = guess_type_from_name(layer_name, layer_type)
                component_name = generate_component_name(layer_name, component_type)
                confidence = 0.6

            # 如果名称为空，使用图层名
            if not component_name:
                component_name = layer_name or f"Component_{layer_id}"

            result = NamingResult(
                success=True,
                layer_id=layer_id,
                component_name=component_name,
                component_type=component_type,
                confidence=confidence,
                reasoning=f"基于 {'AI识别' if ai_result else '规则推断'}: 图层名={layer_name}, 类型={layer_type}",
                metadata={
                    "original_name": layer_name,
                    "ai_used": ai_result is not None,
                    "source": "ai" if ai_result else "rule_based"
                }
            )

            self._name_cache[cache_key] = result
            return result

        except Exception as e:
            self.logger.error(f"组件命名失败: {e}")
            self.error_handler.record(
                task="component_name",
                error=e,
                category=ErrorCategory.AI_ERROR,
                context={"layer_id": layer_id}
            )
            return NamingResult(
                success=False,
                layer_id=layer_id,
                error=str(e)
            )

    def batch_name(
        self,
        items: List[Dict[str, Any]],
        screenshot_key: str = "screenshot_path"
    ) -> List[NamingResult]:
        """
        批量命名组件

        Args:
            items: 组件列表，每个包含 layer_metadata 和可选的 screenshot_path
            screenshot_key: 截图字段的 key

        Returns:
            NamingResult 列表
        """
        self.logger.info(f"批量命名 {len(items)} 个组件")

        results = []
        for i, item in enumerate(items):
            layer_metadata = item.get("layer_metadata", item)
            screenshot_path = item.get(screenshot_key)

            # 同类组件计数
            layer_type = layer_metadata.get("type", "")
            layer_name = layer_metadata.get("name", "")

            result = self.name_from_metadata(layer_metadata, screenshot_path)

            # 更新序号
            if result.success and result.component_name:
                same_type_count = sum(
                    1 for r in results
                    if r.success and r.component_type == result.component_type
                )
                if same_type_count > 0:
                    # 重新生成带序号的名称
                    new_name = generate_component_name(
                        layer_name,
                        result.component_type,
                        index=same_type_count + 1
                    )
                    result.component_name = new_name

            results.append(result)

        success_count = sum(1 for r in results if r.success)
        self.logger.info(f"批量命名完成: {success_count}/{len(items)} 成功")

        return results

    def clear_cache(self):
        """清空缓存"""
        self._name_cache.clear()
