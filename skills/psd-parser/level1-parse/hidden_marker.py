"""
Level 1 - Hidden Marker
标记隐藏图层
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from skills.common import get_logger, get_error_handler, ErrorCategory
from skills.psd_parser.level1_parse.psd_parser import LayerInfo

@dataclass
class HiddenMark:
    """隐藏标记"""
    layer_id: str
    layer_name: str
    mark_type: str  # hidden / conditionally_hidden / marked_for_export
    reason: str
    action_suggested: str

@dataclass
class HiddenMarkResult:
    """隐藏标记结果"""
    success: bool
    total_layers: int
    hidden_count: int
    visible_count: int
    marks: List[Dict] = field(default_factory=list)
    summary: Dict = field(default_factory=dict)

class HiddenMarker:
    """
    隐藏图层标记器
    职责：检测并标记隐藏图层，给出处理建议
    """
    
    def __init__(self, layers: List[LayerInfo]):
        self.layers = layers
        self.logger = get_logger("hidden-marker")
        self.error_handler = get_error_handler()
    
    def mark(self) -> HiddenMarkResult:
        """标记隐藏图层"""
        self.logger.info(f"开始标记隐藏图层: {len(self.layers)} layers")
        
        marks = []
        hidden_count = 0
        visible_count = 0
        
        for layer in self.layers:
            if not layer.visible:
                hidden_count += 1
                mark = self._create_mark(layer, "hidden")
            else:
                visible_count += 1
                mark = self._create_mark(layer, "visible")
            
            marks.append(mark)
        
        result = HiddenMarkResult(
            success=True,
            total_layers=len(self.layers),
            hidden_count=hidden_count,
            visible_count=visible_count,
            marks=marks,
            summary=self._create_summary(hidden_count, visible_count)
        )
        
        self.logger.info(f"隐藏图层标记完成: {hidden_count} hidden, {visible_count} visible")
        return result
    
    def _create_mark(self, layer: LayerInfo, mark_type: str) -> Dict:
        """创建标记"""
        reason = ""
        action = ""
        
        if mark_type == "hidden":
            reason = f"图层 {layer.name} 可见性为 False"
            # 根据图层类型给出建议
            if layer.is_group:
                action = "需要导出组内容时可能需要临时显示"
            elif layer.kind == "image":
                action = "可能需要导出，请确认是否保留"
            elif layer.kind == "decorator":
                action = "装饰图层，可跳过"
            else:
                action = "根据实际需求决定是否导出"
        else:
            reason = "图层可见"
            action = "正常导出"
        
        return {
            "layer_id": layer.id,
            "layer_name": layer.name,
            "kind": layer.kind,
            "mark_type": mark_type,
            "reason": reason,
            "action_suggested": action,
            "metadata": {
                "width": layer.width,
                "height": layer.height,
                "parent_id": layer.parent_id
            }
        }
    
    def _create_summary(self, hidden_count: int, visible_count: int) -> Dict:
        """创建摘要"""
        total = hidden_count + visible_count
        hidden_ratio = hidden_count / total if total > 0 else 0
        
        return {
            "hidden_ratio": round(hidden_ratio, 2),
            "recommendation": self._get_recommendation(hidden_ratio, hidden_count)
        }
    
    def _get_recommendation(self, hidden_ratio: float, hidden_count: int) -> str:
        """获取建议"""
        if hidden_count == 0:
            return "所有图层可见，无需特殊处理"
        elif hidden_ratio > 0.5:
            return "隐藏图层比例较高，建议检查设计稿"
        elif hidden_ratio > 0.3:
            return "部分图层隐藏，可能是有意为之，请确认"
        else:
            return "隐藏图层比例正常"


# ============ 子模块 ============

class VisibilityChecker:
    """可见性检查器"""
    
    def __init__(self, layer: LayerInfo):
        self.layer = layer
    
    def is_explicitly_hidden(self) -> bool:
        """是否明确隐藏"""
        return not self.layer.visible
    
    def will_render_hidden(self) -> bool:
        """渲染时是否隐藏（考虑父级）"""
        if not self.layer.visible:
            return True
        return False


class MarkAggregator:
    """标记聚合器"""
    
    def __init__(self, marks: List[Dict]):
        self.marks = marks
    
    def aggregate_by_kind(self) -> Dict[str, int]:
        """按类型聚合"""
        result = {}
        for mark in self.marks:
            kind = mark.get('kind', 'unknown')
            if mark['mark_type'] == 'hidden':
                key = f"{kind}_hidden"
            else:
                key = f"{kind}_visible"
            result[key] = result.get(key, 0) + 1
        return result
    
    def get_hidden_layers(self) -> List[Dict]:
        """获取所有隐藏图层"""
        return [m for m in self.marks if m['mark_type'] == 'hidden']
    
    def get_export_recommended(self) -> List[Dict]:
        """获取建议导出的隐藏图层"""
        hidden = self.get_hidden_layers()
        return [
            m for m in hidden
            if 'export' in m.get('action_suggested', '').lower()
        ]


def mark_hidden_layers(layers: List[LayerInfo]) -> HiddenMarkResult:
    """标记隐藏图层"""
    marker = HiddenMarker(layers)
    return marker.mark()
