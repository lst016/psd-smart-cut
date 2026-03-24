"""
Level 1 - Locked Detector
检测锁定图层并给出建议
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from skills.common import get_logger, get_error_handler, ErrorCategory
from skills.psd_parser.level1_parse.psd_parser import LayerInfo

@dataclass
class LockReport:
    """锁定报告"""
    layer_id: str
    layer_name: str
    locked: bool
    lock_type: str  # none / full / partial
    risk_level: str  # low / medium / high
    unlock_suggestion: str
    export_compatible: bool

@dataclass
class LockedDetectResult:
    """锁定检测结果"""
    success: bool
    total_layers: int
    locked_count: int
    unlocked_count: int
    reports: List[Dict] = field(default_factory=list)
    summary: Dict = field(default_factory=dict)

class LockedDetector:
    """
    锁定图层检测器
    职责：检测锁定图层，评估风险，给出解锁建议
    """
    
    def __init__(self, layers: List[LayerInfo]):
        self.layers = layers
        self.logger = get_logger("locked-detector")
        self.error_handler = get_error_handler()
    
    def detect(self) -> LockedDetectResult:
        """检测锁定图层"""
        self.logger.info(f"开始检测锁定图层: {len(self.layers)} layers")
        
        reports = []
        locked_count = 0
        unlocked_count = 0
        
        for layer in self.layers:
            report = self._create_report(layer)
            reports.append(report)
            
            if layer.locked:
                locked_count += 1
            else:
                unlocked_count += 1
        
        result = LockedDetectResult(
            success=True,
            total_layers=len(self.layers),
            locked_count=locked_count,
            unlocked_count=unlocked_count,
            reports=reports,
            summary=self._create_summary(locked_count, unlocked_count, reports)
        )
        
        self.logger.info(f"锁定检测完成: {locked_count} locked, {unlocked_count} unlocked")
        return result
    
    def _create_report(self, layer: LayerInfo) -> Dict:
        """创建报告"""
        locked = layer.locked
        lock_type = self._detect_lock_type(layer)
        risk_level = self._assess_risk(layer, locked)
        suggestion = self._get_unlock_suggestion(layer)
        export_ok = self._check_export_compatibility(layer, locked)
        
        return {
            "layer_id": layer.id,
            "layer_name": layer.name,
            "kind": layer.kind,
            "locked": locked,
            "lock_type": lock_type,
            "risk_level": risk_level,
            "unlock_suggestion": suggestion,
            "export_compatible": export_ok,
            "metadata": {
                "width": layer.width,
                "height": layer.height,
                "parent_id": layer.parent_id
            }
        }
    
    def _detect_lock_type(self, layer: LayerInfo) -> str:
        """检测锁定类型"""
        if not layer.locked:
            return "none"
        
        # 这里可以扩展更细的锁定类型检测
        # 目前 psd-tools 只提供简单的 locked 状态
        return "full"
    
    def _assess_risk(self, layer: LayerInfo, locked: bool) -> str:
        """评估风险"""
        if not locked:
            return "low"
        
        # 根据图层类型评估风险
        if layer.kind == "image":
            # 图片锁定风险较低，解锁后可导出
            return "medium"
        elif layer.kind == "group":
            # 组锁定风险较高，可能影响子图层
            return "high"
        elif layer.kind == "text":
            # 文字锁定风险中等
            return "medium"
        else:
            return "medium"
    
    def _get_unlock_suggestion(self, layer: LayerInfo) -> str:
        """获取解锁建议"""
        if not layer.locked:
            return "无需操作"
        
        suggestions = {
            "image": f"图层 {layer.name} 已锁定，建议在 Photoshop 中解锁后再导出",
            "text": f"文字图层 {layer.name} 已锁定，如需修改文字内容请先解锁",
            "vector": f"矢量图层 {layer.name} 已锁定，如需编辑形状请先解锁",
            "group": f"图层组 {layer.name} 已锁定，解锁将影响所有子图层",
            "decorator": f"装饰图层 {layer.name} 已锁定，导出时可能受影响",
            "unknown": f"图层 {layer.name} 已锁定，建议检查是否需要导出"
        }
        
        return suggestions.get(layer.kind, suggestions["unknown"])
    
    def _check_export_compatibility(self, layer: LayerInfo, locked: bool) -> bool:
        """检查导出兼容性"""
        if not locked:
            return True
        
        # 大多数情况下，锁定图层仍然可以导出
        # 但如果需要精确操作，建议解锁
        return True
    
    def _create_summary(self, locked_count: int, unlocked_count: int, reports: List[Dict]) -> Dict:
        """创建摘要"""
        total = locked_count + unlocked_count
        locked_ratio = locked_count / total if total > 0 else 0
        
        # 按风险级别统计
        risk_stats = {"low": 0, "medium": 0, "high": 0}
        for report in reports:
            if report["locked"]:
                risk_stats[report["risk_level"]] += 1
        
        # 按图层类型统计锁定
        kind_stats = {}
        for report in reports:
            if report["locked"]:
                kind = report["kind"]
                kind_stats[kind] = kind_stats.get(kind, 0) + 1
        
        return {
            "locked_ratio": round(locked_ratio, 2),
            "risk_distribution": risk_stats,
            "locked_by_kind": kind_stats,
            "recommendation": self._get_recommendation(locked_count, locked_ratio, risk_stats)
        }
    
    def _get_recommendation(self, locked_count: int, locked_ratio: float, risk_stats: Dict) -> str:
        """获取建议"""
        if locked_count == 0:
            return "所有图层未锁定，可以正常导出"
        elif locked_ratio > 0.3:
            return "锁定图层较多，建议在 Photoshop 中统一处理"
        elif risk_stats["high"] > 0:
            return "存在高风险锁定图层，建议检查图层组"
        else:
            return "锁定图层可以正常导出，无需特殊处理"


# ============ 子模块 ============

class LockStatusChecker:
    """锁定状态检查器"""
    
    def __init__(self, layer: LayerInfo):
        self.layer = layer
    
    def is_locked(self) -> bool:
        return self.layer.locked
    
    def get_lock_info(self) -> Dict:
        return {
            "locked": self.layer.locked,
            "layer_id": self.layer.id,
            "layer_name": self.layer.name
        }


class RiskEvaluator:
    """风险评估器"""
    
    def __init__(self, layer: LayerInfo):
        self.layer = layer
    
    def evaluate(self) -> str:
        if not self.layer.locked:
            return "low"
        
        # 高风险情况
        if self.layer.kind == "group":
            return "high"
        
        # 中风险情况
        if self.layer.kind in ["image", "text"]:
            return "medium"
        
        return "medium"


class UnlockAdvisor:
    """解锁建议器"""
    
    def __init__(self, layers: List[LayerInfo]):
        self.layers = layers
    
    def get_batch_advice(self) -> Dict:
        """批量解锁建议"""
        groups = [l for l in self.layers if l.kind == "group" and l.locked]
        images = [l for l in self.layers if l.kind == "image" and l.locked]
        
        return {
            "recommended_unlocks": len(groups),  # 组建议解锁
            "optional_unlocks": len(images),  # 图片可选
            "can_proceed": True,  # 可以继续导出
            "warnings": [
                f"{len(groups)} 个图层组已锁定，解锁后可编辑子图层"
            ] if groups else []
        }


def detect_locked_layers(layers: List[LayerInfo]) -> LockedDetectResult:
    """检测锁定图层"""
    detector = LockedDetector(layers)
    return detector.detect()
