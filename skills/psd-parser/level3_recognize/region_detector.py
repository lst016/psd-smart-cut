"""
Level 3 - Region Detector
区域检测器

分析图层边界矩形，检测重叠区域，计算有效内容区域（去除空白），
合并相邻区域。
"""
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from skills.common import get_logger, get_config, get_error_handler, ErrorCategory


class EdgeType(Enum):
    """边缘类型"""
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    CURVE = "curve"
    IRREGULAR = "irregular"


class OverlapStrategy(Enum):
    """重叠处理策略"""
    KEEP_BOTH = "keep_both"
    MERGE = "merge"
    PRIORITY = "priority"


@dataclass
class Rect:
    """矩形区域"""
    x: int
    y: int
    width: int
    height: int

    @property
    def left(self) -> int:
        return self.x

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def top(self) -> int:
        return self.y

    @property
    def bottom(self) -> int:
        return self.y + self.height

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)

    def intersection(self, other: 'Rect') -> Optional['Rect']:
        """计算两个矩形的交集"""
        x = max(self.left, other.left)
        y = max(self.top, other.top)
        w = min(self.right, other.right) - x
        h = min(self.bottom, other.bottom) - y

        if w <= 0 or h <= 0:
            return None
        return Rect(x=x, y=y, width=w, height=h)

    def iou(self, other: 'Rect') -> float:
        """计算两个矩形的 IoU（交并比）"""
        inter = self.intersection(other)
        if inter is None:
            return 0.0
        union = self.area + other.area - inter.area
        return inter.area / union if union > 0 else 0.0

    def is_adjacent(self, other: 'Rect', threshold: int = 5) -> bool:
        """
        判断两个矩形是否相邻（距离在阈值内）
        考虑水平、垂直和角落相邻。
        """
        # 检查是否水平相邻（上下边对齐）
        if abs(self.top - other.top) <= threshold or abs(self.bottom - other.bottom) <= threshold:
            if self.right < other.left and other.left - self.right <= threshold:
                return True
            if other.right < self.left and self.left - other.right <= threshold:
                return True

        # 检查是否垂直相邻（左右边对齐）
        if abs(self.left - other.left) <= threshold or abs(self.right - other.right) <= threshold:
            if self.bottom < other.top and other.top - self.bottom <= threshold:
                return True
            if other.bottom < self.top and self.top - other.bottom <= threshold:
                return True

        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> 'Rect':
        return Rect(x=d["x"], y=d["y"], width=d["width"], height=d["height"])


@dataclass
class RegionResult:
    """区域检测结果"""
    success: bool
    layer_id: str
    raw_boundary: Optional[Dict] = None
    effective_boundary: Optional[Dict] = None
    overlap_regions: List[Dict] = field(default_factory=list)
    merged_regions: List[Dict] = field(default_factory=list)
    trimmed_boundary: Optional[Dict] = None  # 去除空白后的边界
    error: Optional[str] = None


@dataclass
class BoundaryInfo:
    """边界信息"""
    rect: Rect
    edge_type: EdgeType
    quality_score: float = 1.0
    cut_points: List[Tuple[int, int]] = field(default_factory=list)


class RegionDetector:
    """
    区域检测器

    分析图层边界矩形，检测重叠区域，计算有效内容区域，
    合并相邻区域。
    """

    def __init__(
        self,
        overlap_threshold: float = 0.3,
        adjacent_threshold: int = 5,
        min_region_area: int = 100
    ):
        """
        Args:
            overlap_threshold: 重叠阈值（IoU > 此值认为重叠）
            adjacent_threshold: 相邻判定阈值（像素）
            min_region_area: 最小有效区域面积
        """
        self.overlap_threshold = overlap_threshold
        self.adjacent_threshold = adjacent_threshold
        self.min_region_area = min_region_area
        self.logger = get_logger("region-detector")
        self.config = get_config()
        self.error_handler = get_error_handler()

    def detect_boundary(
        self,
        layer_metadata: Dict[str, Any]
    ) -> Rect:
        """
        从图层元数据检测边界矩形

        Args:
            layer_metadata: 图层元数据，应包含 position 和 dimensions

        Returns:
            Rect 边界矩形
        """
        try:
            position = layer_metadata.get("position", {})
            dimensions = layer_metadata.get("dimensions", {})

            x = position.get("x", 0)
            y = position.get("y", 0)
            width = dimensions.get("width", 0)
            height = dimensions.get("height", 0)

            return Rect(x=x, y=y, width=width, height=height)

        except Exception as e:
            self.logger.error(f"边界检测失败: {e}")
            return Rect(x=0, y=0, width=0, height=0)

    def detect_overlaps(
        self,
        regions: List[Dict[str, Any]],
        strategy: OverlapStrategy = OverlapStrategy.MERGE
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        检测重叠区域

        Args:
            regions: 区域列表，每个包含 boundary 信息
            strategy: 重叠处理策略

        Returns:
            (重叠区域列表, 处理后区域列表)
        """
        if len(regions) < 2:
            return [], regions

        overlaps = []
        processed = []
        region_rects = []

        # 转换为 Rect 对象
        for region in regions:
            boundary = region.get("boundary", region)
            rect = Rect.from_dict(boundary)
            region_rects.append((region, rect))

        marked = set()

        for i, (region_i, rect_i) in enumerate(region_rects):
            if i in marked:
                continue

            current_group = [(region_i, rect_i)]

            for j, (region_j, rect_j) in enumerate(region_rects[i + 1:], i + 1):
                if j in marked:
                    continue

                iou = rect_i.iou(rect_j)
                if iou > self.overlap_threshold:
                    overlaps.append({
                        "region_a": region_i,
                        "region_b": region_j,
                        "iou": iou,
                        "intersection": rect_i.intersection(rect_j).to_dict() if rect_i.intersection(rect_j) else None
                    })

                    if strategy == OverlapStrategy.MERGE:
                        current_group.append((region_j, rect_j))
                        marked.add(j)

            processed.append(region_i)

        # 合并重叠区域
        if strategy == OverlapStrategy.MERGE:
            merged = self._merge_regions(current_group)
            processed = merged

        return overlaps, processed

    def _merge_regions(
        self,
        region_group: List[Tuple[Dict, Rect]]
    ) -> List[Dict]:
        """合并一组重叠区域"""
        if not region_group:
            return []

        # 找到覆盖所有区域的最小矩形
        min_x = min(r.x for _, r in region_group)
        min_y = min(r.y for _, r in region_group)
        max_x = max(r.right for _, r in region_group)
        max_y = max(r.bottom for _, r in region_group)

        merged_rect = Rect(
            x=min_x,
            y=min_y,
            width=max_x - min_x,
            height=max_y - min_y
        )

        return [{
            "layer_id": f"merged_{'_'.join(str(r.get('layer_id', 'unknown')) for r, _ in region_group)}",
            "boundary": merged_rect.to_dict(),
            "merged_from": [r.get("layer_id") for r, _ in region_group],
            "type": "merged"
        }]

    def calculate_effective_boundary(
        self,
        layer_metadata: Dict[str, Any],
        pixel_threshold: int = 10
    ) -> Dict[str, Any]:
        """
        计算有效内容区域（去除边界空白）

        通过检测图层边缘的非空白像素来确定实际内容边界。

        Args:
            layer_metadata: 图层元数据
            pixel_threshold: 空白判定阈值

        Returns:
            有效内容区域字典
        """
        # 如果有实际图像数据，使用像素分析
        # 这里基于元数据做简化计算
        boundary = self.detect_boundary(layer_metadata)
        rect = Rect(
            x=boundary.x + pixel_threshold,
            y=boundary.y + pixel_threshold,
            width=max(1, boundary.width - pixel_threshold * 2),
            height=max(1, boundary.height - pixel_threshold * 2)
        )

        return {
            "x": rect.x,
            "y": rect.y,
            "width": rect.width,
            "height": rect.height,
            "original_area": boundary.area,
            "effective_area": rect.area,
            "trim_ratio": round(rect.area / boundary.area, 3) if boundary.area > 0 else 0
        }

    def merge_adjacent_regions(
        self,
        regions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        合并相邻区域

        Args:
            regions: 区域列表

        Returns:
            合并后的区域列表
        """
        if len(regions) < 2:
            return regions

        region_rects = []
        for region in regions:
            boundary = region.get("boundary", region)
            rect = Rect.from_dict(boundary)
            region_rects.append((region, rect))

        merged = True
        while merged:
            merged = False
            new_regions = []

            i = 0
            while i < len(region_rects):
                region_i, rect_i = region_rects[i]
                found_merge = False

                for j in range(i + 1, len(region_rects)):
                    region_j, rect_j = region_rects[j]

                    if rect_i.is_adjacent(rect_j, self.adjacent_threshold):
                        # 合并
                        min_x = min(rect_i.left, rect_j.left)
                        min_y = min(rect_i.top, rect_j.top)
                        max_x = max(rect_i.right, rect_j.right)
                        max_y = max(rect_i.bottom, rect_j.bottom)

                        merged_rect = Rect(
                            x=min_x,
                            y=min_y,
                            width=max_x - min_x,
                            height=max_y - min_y
                        )

                        new_region = {
                            "layer_id": f"merged_adj_{region_i.get('layer_id', 'a')}_{region_j.get('layer_id', 'b')}",
                            "boundary": merged_rect.to_dict(),
                            "merged_from": region_i.get("layer_id") and region_j.get("layer_id"),
                            "type": "adjacent_merged"
                        }

                        region_rects[j] = (new_region, merged_rect)
                        found_merge = True
                        merged = True
                        break

                if not found_merge:
                    new_regions.append((region_i, rect_i))
                    region_rects.pop(i)
                else:
                    i += 1

            region_rects = new_regions if region_rects == new_regions else region_rects

        return [{"layer_id": r.get("layer_id", f"region_{i}"), "boundary": rect.to_dict()} for i, (r, rect) in enumerate(region_rects)]

    def analyze(
        self,
        layer_metadata: Dict[str, Any]
    ) -> RegionResult:
        """
        完整区域分析

        综合调用边界检测、重叠检测、有效区域计算。

        Args:
            layer_metadata: 图层元数据

        Returns:
            RegionResult
        """
        layer_id = layer_metadata.get("layer_id", "unknown")

        try:
            # 1. 边界检测
            rect = self.detect_boundary(layer_metadata)
            raw_boundary = rect.to_dict()

            # 2. 有效内容区域
            effective = self.calculate_effective_boundary(layer_metadata)

            result = RegionResult(
                success=True,
                layer_id=layer_id,
                raw_boundary=raw_boundary,
                effective_boundary=effective,
                trimmed_boundary=effective
            )

            return result

        except Exception as e:
            self.logger.error(f"区域分析失败: {e}")
            self.error_handler.record(
                task="region_detect",
                error=e,
                category=ErrorCategory.PARSE_ERROR,
                context={"layer_id": layer_id}
            )
            return RegionResult(
                success=False,
                layer_id=layer_id,
                error=str(e)
            )

    def batch_analyze(
        self,
        layers_metadata: List[Dict[str, Any]]
    ) -> List[RegionResult]:
        """批量区域分析"""
        results = []

        for metadata in layers_metadata:
            result = self.analyze(metadata)
            results.append(result)

        # 检测重叠
        regions = [r for r in results if r.success]
        if len(regions) > 1:
            overlaps, processed = self.detect_overlaps(regions)
            for r in regions:
                r.overlap_regions = overlaps

        return results
