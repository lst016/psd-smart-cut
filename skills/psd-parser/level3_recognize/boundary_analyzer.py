"""
Level 3 - Boundary Analyzer
边界分析器

分析组件边界，检测边缘类型（直线/曲线/不规则），计算边界质量分数，
识别切割点。
"""
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from skills.common import get_logger, get_config, get_error_handler, ErrorCategory


import enum


class EdgeType(enum.Enum):
    """边缘类型"""
    HORIZONTAL = "horizontal"      # 水平直线边缘
    VERTICAL = "vertical"          # 垂直直线边缘
    DIAGONAL = "diagonal"         # 对角线边缘
    CURVE = "curve"               # 曲线边缘
    IRREGULAR = "irregular"       # 不规则边缘


@dataclass
class CutPoint:
    """切割点"""
    x: int
    y: int
    edge_type: str
    quality: float  # 0-1，切割质量
    reason: str


@dataclass
class BoundaryResult:
    """边界分析结果"""
    success: bool
    layer_id: str
    edge_type: str = "unknown"
    quality_score: float = 0.0
    cut_points: List[Dict] = field(default_factory=list)
    edge_details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class BoundaryAnalyzer:
    """
    边界分析器

    分析组件边界特征，检测边缘类型，计算边界质量分数，
    识别适合切割的位置点。
    """

    def __init__(
        self,
        quality_threshold: float = 0.7,
        min_cut_distance: int = 10
    ):
        """
        Args:
            quality_threshold: 切割质量阈值
            min_cut_distance: 最小切割点间距
        """
        self.quality_threshold = quality_threshold
        self.min_cut_distance = min_cut_distance
        self.logger = get_logger("boundary-analyzer")
        self.config = get_config()
        self.error_handler = get_error_handler()

    def _detect_edge_type_from_boundary(
        self,
        boundary: Dict[str, Any]
    ) -> Tuple[EdgeType, float]:
        """
        从边界信息检测边缘类型和计算质量分数

        Args:
            boundary: 边界字典 {x, y, width, height}

        Returns:
            (边缘类型, 质量分数)
        """
        width = boundary.get("width", 0)
        height = boundary.get("height", 0)

        if width == 0 or height == 0:
            return EdgeType.IRREGULAR, 0.0

        aspect_ratio = width / height

        # 根据宽高比判断边缘类型
        if aspect_ratio > 10:
            # 非常扁平的区域，可能是水平分割线
            return EdgeType.HORIZONTAL, min(1.0, width / (height * 20))
        elif aspect_ratio < 0.1:
            # 非常窄高的区域，可能是垂直分割线
            return EdgeType.VERTICAL, min(1.0, height / (width * 20))
        elif 0.5 <= aspect_ratio <= 2.0:
            # 接近正方形，边缘规则
            return EdgeType.HORIZONTAL, 0.85
        else:
            # 介于两者之间
            return EdgeType.IRREGULAR, 0.5

    def _find_cut_points(
        self,
        boundary: Dict[str, Any],
        edge_type: EdgeType
    ) -> List[CutPoint]:
        """
        识别切割点

        基于边界特征找到适合作为切割起始点的位置。

        Args:
            boundary: 边界信息
            edge_type: 边缘类型

        Returns:
            CutPoint 列表
        """
        cut_points = []
        x = boundary.get("x", 0)
        y = boundary.get("y", 0)
        width = boundary.get("width", 0)
        height = boundary.get("height", 0)

        if edge_type == EdgeType.HORIZONTAL:
            # 水平边缘：从左到右扫描，找到突变点
            # 简化：四角和边中点都是候选切割点
            cut_points.append(CutPoint(
                x=x, y=y, edge_type="top_left",
                quality=0.9, reason="左上角起点"
            ))
            cut_points.append(CutPoint(
                x=x + width, y=y, edge_type="top_right",
                quality=0.9, reason="右上角起点"
            ))
            cut_points.append(CutPoint(
                x=x, y=y + height, edge_type="bottom_left",
                quality=0.8, reason="左下角"
            ))
            cut_points.append(CutPoint(
                x=x + width, y=y + height, edge_type="bottom_right",
                quality=0.8, reason="右下角"
            ))
            # 边缘中点
            cut_points.append(CutPoint(
                x=x + width // 2, y=y, edge_type="top_center",
                quality=0.7, reason="顶部中点"
            ))

        elif edge_type == EdgeType.VERTICAL:
            # 垂直边缘
            cut_points.append(CutPoint(
                x=x, y=y, edge_type="top_left",
                quality=0.9, reason="左上角起点"
            ))
            cut_points.append(CutPoint(
                x=x, y=y + height, edge_type="bottom_left",
                quality=0.9, reason="左下角起点"
            ))
            cut_points.append(CutPoint(
                x=x + width, y=y, edge_type="top_right",
                quality=0.8, reason="右上角"
            ))
            cut_points.append(CutPoint(
                x=x + width, y=y + height, edge_type="bottom_right",
                quality=0.8, reason="右下角"
            ))
            # 边缘中点
            cut_points.append(CutPoint(
                x=x, y=y + height // 2, edge_type="left_center",
                quality=0.7, reason="左侧中点"
            ))

        else:
            # 不规则或曲线：四角都是候选
            for corner_x, corner_y, corner_name in [
                (x, y, "top_left"),
                (x + width, y, "top_right"),
                (x, y + height, "bottom_left"),
                (x + width, y + height, "bottom_right"),
            ]:
                cut_points.append(CutPoint(
                    x=corner_x, y=corner_y, edge_type=corner_name,
                    quality=0.6, reason=f"不规则边缘角落: {corner_name}"
                ))

        # 按质量排序，过滤低质量
        cut_points = sorted(cut_points, key=lambda p: p.quality, reverse=True)

        # 过滤距离过近的切割点
        filtered = []
        for cp in cut_points:
            too_close = any(
                abs(cp.x - fp.x) < self.min_cut_distance and
                abs(cp.y - fp.y) < self.min_cut_distance
                for fp in filtered
            )
            if not too_close:
                filtered.append(cp)

        return filtered

    def _calculate_quality_score(
        self,
        boundary: Dict[str, Any],
        edge_type: EdgeType,
        layer_metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        计算边界质量分数

        综合考虑边界规则性、图层类型、尺寸比例等因素。

        Args:
            boundary: 边界信息
            edge_type: 边缘类型
            layer_metadata: 额外元数据

        Returns:
            质量分数 0-1
        """
        width = boundary.get("width", 0)
        height = boundary.get("height", 0)

        if width == 0 or height == 0:
            return 0.0

        # 基础分数（根据边缘类型）
        base_scores = {
            EdgeType.HORIZONTAL: 0.85,
            EdgeType.VERTICAL: 0.85,
            EdgeType.DIAGONAL: 0.6,
            EdgeType.CURVE: 0.5,
            EdgeType.IRREGULAR: 0.4,
        }
        score = base_scores.get(edge_type, 0.5)

        # 尺寸惩罚：太小或太大的区域质量下降
        area = width * height
        if area < 100:  # 太小
            score *= 0.7
        elif area > 1000000:  # 太大（全屏级别）
            score *= 0.8

        # 宽高比惩罚：极端比例质量下降
        aspect_ratio = max(width / height, height / width)
        if aspect_ratio > 10:
            score *= 0.8

        # 图层类型加成
        if layer_metadata:
            kind = layer_metadata.get("kind", layer_metadata.get("type", ""))
            if kind == "vector":
                score = min(1.0, score + 0.1)  # 矢量图层边界更清晰
            elif kind == "text":
                score = min(1.0, score + 0.05)

        return round(score, 3)

    def analyze(
        self,
        boundary: Dict[str, Any],
        layer_metadata: Optional[Dict[str, Any]] = None
    ) -> BoundaryResult:
        """
        完整边界分析

        Args:
            boundary: 边界字典 {x, y, width, height}
            layer_metadata: 可选的图层元数据

        Returns:
            BoundaryResult
        """
        layer_id = boundary.get("layer_id", layer_metadata.get("layer_id", "unknown") if layer_metadata else "unknown")

        try:
            # 1. 检测边缘类型
            edge_type, _ = self._detect_edge_type_from_boundary(boundary)

            # 2. 计算质量分数
            quality_score = self._calculate_quality_score(boundary, edge_type, layer_metadata)

            # 3. 识别切割点
            cut_points = self._find_cut_points(boundary, edge_type)

            result = BoundaryResult(
                success=True,
                layer_id=layer_id,
                edge_type=edge_type.value,
                quality_score=quality_score,
                cut_points=[
                    {
                        "x": cp.x,
                        "y": cp.y,
                        "edge_type": cp.edge_type,
                        "quality": cp.quality,
                        "reason": cp.reason
                    }
                    for cp in cut_points
                ],
                edge_details={
                    "aspect_ratio": round(boundary.get("width", 0) / max(1, boundary.get("height", 1)), 3),
                    "area": boundary.get("width", 0) * boundary.get("height", 0),
                    "boundary": boundary
                }
            )

            self.logger.debug(
                f"边界分析完成: layer_id={layer_id}, "
                f"edge_type={edge_type.value}, quality={quality_score}"
            )

            return result

        except Exception as e:
            self.logger.error(f"边界分析失败: {e}")
            self.error_handler.record(
                task="boundary_analyze",
                error=e,
                category=ErrorCategory.PARSE_ERROR,
                context={"layer_id": layer_id}
            )
            return BoundaryResult(
                success=False,
                layer_id=layer_id,
                error=str(e)
            )

    def batch_analyze(
        self,
        items: List[Dict[str, Any]]
    ) -> List[BoundaryResult]:
        """
        批量边界分析

        Args:
            items: 项目列表，每个包含 boundary 和可选的 layer_metadata

        Returns:
            BoundaryResult 列表
        """
        results = []
        for item in items:
            boundary = item.get("boundary", item)
            layer_metadata = item.get("layer_metadata")
            result = self.analyze(boundary, layer_metadata)
            results.append(result)

        avg_quality = sum(r.quality_score for r in results if r.success) / max(1, len(results))
        self.logger.info(f"批量边界分析完成: {len(results)} 个，平均质量={avg_quality:.2f}")

        return results

    def get_best_cut_points(
        self,
        results: List[BoundaryResult],
        top_n: int = 5
    ) -> List[Dict]:
        """
        从多个边界分析结果中提取最佳切割点

        Args:
            results: BoundaryResult 列表
            top_n: 返回前 N 个最佳切割点

        Returns:
            最佳切割点列表
        """
        all_points = []

        for result in results:
            if result.success:
                for cp in result.cut_points:
                    all_points.append({
                        **cp,
                        "layer_id": result.layer_id,
                        "source_quality": result.quality_score
                    })

        # 按综合分数排序
        def _combined_score(cp):
            return cp["quality"] * 0.6 + cp["source_quality"] * 0.4

        all_points.sort(key=_combined_score, reverse=True)

        return all_points[:top_n]
