"""
Level 4 - Overlap Detector
重叠检测器 - 检测图层之间的重叠关系
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from skills.common import get_logger, get_config, get_error_handler, ErrorCategory

logger = get_logger("overlap_detector")

# ============ 数据类 ============

@dataclass
class OverlapInfo:
    """重叠信息"""
    layer_a: str
    layer_b: str
    overlap_rect: Tuple[int, int, int, int]  # x, y, w, h
    overlap_area: int
    percentage_a: float  # layer_a 被覆盖百分比
    percentage_b: float  # layer_b 被覆盖百分比
    front_layer: str  # 在前面的图层
    resolution: str  # 'full'/'partial'/'edge'

@dataclass
class OverlapAnalysisResult:
    """重叠分析结果"""
    overlaps: List[OverlapInfo]
    occlusion_map: Dict[str, List[str]]  # 图层 -> 被其遮挡的图层列表
    priority_layers: List[str]  # 切割优先级图层
    suggestions: List[str]  # 去重叠建议

# ============ 重叠检测器 ============

class OverlapDetector:
    """重叠检测器"""
    
    def __init__(self):
        self.logger = get_logger("overlap_detector")
        self.config = get_config()
    
    def detect_overlaps(
        self,
        layers: List[Dict],
        z_order: Optional[List[str]] = None
    ) -> OverlapAnalysisResult:
        """
        检测图层重叠
        
        Args:
            layers: 图层列表
            z_order: Z 轴顺序（前面的图层排在前面）
        
        Returns:
            OverlapAnalysisResult: 重叠分析结果
        """
        z_order = z_order or [l.get('id') for l in layers]
        
        self.logger.info(
            f"检测重叠: {len(layers)} 个图层",
            z_order_length=len(z_order)
        )
        
        # 构建 ID 到图层的映射
        layer_map = {l.get('id'): l for l in layers}
        
        # 计算所有重叠对
        overlaps = []
        for i, layer_a in enumerate(layers):
            for layer_b in layers[i + 1:]:
                overlap = self._check_overlap(layer_a, layer_b, layer_map, z_order)
                if overlap:
                    overlaps.append(overlap)
        
        # 构建遮挡关系图
        occlusion_map = self._build_occlusion_map(overlaps)
        
        # 确定切割优先级
        priority_layers = self._determine_priority(layers, overlaps, occlusion_map)
        
        # 生成去重叠建议
        suggestions = self._generate_suggestions(overlaps, occlusion_map)
        
        result = OverlapAnalysisResult(
            overlaps=overlaps,
            occlusion_map=occlusion_map,
            priority_layers=priority_layers,
            suggestions=suggestions
        )
        
        self.logger.info(
            f"检测完成: {len(overlaps)} 对重叠",
            priority_count=len(priority_layers)
        )
        
        return result
    
    def _check_overlap(
        self,
        layer_a: Dict,
        layer_b: Dict,
        layer_map: Dict,
        z_order: List[str]
    ) -> Optional[OverlapInfo]:
        """检查两个图层是否重叠"""
        bounds_a = layer_a.get('bounds', {})
        bounds_b = layer_b.get('bounds', {})
        
        # 获取边界
        ax = bounds_a.get('x', 0)
        ay = bounds_a.get('y', 0)
        aw = bounds_a.get('width', 0)
        ah = bounds_a.get('height', 0)
        
        bx = bounds_b.get('x', 0)
        by = bounds_b.get('y', 0)
        bw = bounds_b.get('width', 0)
        bh = bounds_b.get('height', 0)
        
        # 计算重叠区域
        x1 = max(ax, bx)
        y1 = max(ay, by)
        x2 = min(ax + aw, bx + bw)
        y2 = min(ay + ah, by + bh)
        
        if x1 >= x2 or y1 >= y2:
            return None  # 无重叠
        
        overlap_w = x2 - x1
        overlap_h = y2 - y1
        overlap_area = overlap_w * overlap_h
        
        # 计算面积百分比
        area_a = aw * ah
        area_b = bw * bh
        
        percentage_a = (overlap_area / area_a * 100) if area_a > 0 else 0
        percentage_b = (overlap_area / area_b * 100) if area_b > 0 else 0
        
        # 确定前面的图层（根据 Z 轴顺序）
        id_a = layer_a.get('id')
        id_b = layer_b.get('id')
        
        try:
            index_a = z_order.index(id_a)
            index_b = z_order.index(id_b)
            front_layer = id_a if index_a > index_b else id_b
        except ValueError:
            front_layer = id_a  # 默认
        
        # 确定重叠类型
        resolution = self._classify_overlap(
            overlap_w, overlap_h, overlap_area,
            aw, ah, bw, bh,
            percentage_a, percentage_b
        )
        
        return OverlapInfo(
            layer_a=id_a,
            layer_b=id_b,
            overlap_rect=(x1, y1, overlap_w, overlap_h),
            overlap_area=overlap_area,
            percentage_a=percentage_a,
            percentage_b=percentage_b,
            front_layer=front_layer,
            resolution=resolution
        )
    
    def _classify_overlap(
        self,
        overlap_w: int,
        overlap_h: int,
        overlap_area: int,
        aw: int,
        ah: int,
        bw: int,
        bh: int,
        percentage_a: float,
        percentage_b: float
    ) -> str:
        """
        分类重叠类型
        
        Returns:
            'full': 完全重叠（一图层被完全包含在另一图层中）
            'partial': 部分重叠
            'edge': 边缘重叠（重叠区域很小）
        """
        # 检查是否是完全包含
        area_a = aw * ah
        area_b = bw * bh
        
        if area_a > 0 and overlap_area >= area_a * 0.9:
            return 'full'  # layer_a 被完全覆盖
        if area_b > 0 and overlap_area >= area_b * 0.9:
            return 'full'  # layer_b 被完全覆盖
        
        # 检查边缘重叠
        min_area = min(area_a, area_b)
        if min_area > 0 and overlap_area < min_area * 0.1:
            return 'edge'
        
        return 'partial'
    
    def _build_occlusion_map(self, overlaps: List[OverlapInfo]) -> Dict[str, List[str]]:
        """构建遮挡关系图"""
        occlusion_map: Dict[str, List[str]] = {}
        
        for overlap in overlaps:
            front = overlap.front_layer
            back = overlap.layer_b if front == overlap.layer_a else overlap.layer_a
            
            if front not in occlusion_map:
                occlusion_map[front] = []
            if back not in occlusion_map[front]:
                occlusion_map[front].append(back)
        
        return occlusion_map
    
    def _determine_priority(
        self,
        layers: List[Dict],
        overlaps: List[OverlapInfo],
        occlusion_map: Dict[str, List[str]]
    ) -> List[str]:
        """
        确定切割优先级
        
        优先级规则：
        1. 被遮挡最多的图层优先级最低
        2. 遮挡别人的图层优先级较高
        3. 重要组件（按钮、图标）优先级较高
        """
        # 计算每个图层的遮挡得分
        occlusion_scores = {}
        
        for layer in layers:
            layer_id = layer.get('id')
            occlusion_scores[layer_id] = 0
        
        # 加分：遮挡别人
        for overlap in overlaps:
            front = overlap.front_layer
            if front in occlusion_scores:
                occlusion_scores[front] += overlap.overlap_area
        
        # 减分：被遮挡
        for front, backs in occlusion_map.items():
            for back in backs:
                if back in occlusion_scores:
                    occlusion_scores[back] -= 1000  # 固定惩罚
        
        # 重要组件加权
        priority_boost = {
            'button': 500,
            'icon': 400,
            'text': 300,
            'heading': 350,
            'label': 200
        }
        
        for layer in layers:
            layer_id = layer.get('id')
            layer_type = layer.get('type', '')
            if layer_type in priority_boost:
                occlusion_scores[layer_id] = occlusion_scores.get(layer_id, 0) + priority_boost[layer_type]
        
        # 按得分排序（高到低）
        priority_layers = sorted(
            occlusion_scores.keys(),
            key=lambda x: occlusion_scores.get(x, 0),
            reverse=True
        )
        
        return priority_layers
    
    def _generate_suggestions(
        self,
        overlaps: List[OverlapInfo],
        occlusion_map: Dict[str, List[str]]
    ) -> List[str]:
        """生成去重叠建议"""
        suggestions = []
        
        # 分析完全重叠
        full_overlaps = [o for o in overlaps if o.resolution == 'full']
        if full_overlaps:
            suggestions.append(
                f"发现 {len(full_overlaps)} 对完全重叠，建议检查图层可见性"
            )
        
        # 分析边缘重叠
        edge_overlaps = [o for o in overlaps if o.resolution == 'edge']
        if edge_overlaps:
            suggestions.append(
                f"发现 {len(edge_overlaps)} 对边缘重叠，可能是抗锯齿效果"
            )
        
        # 分析大面积重叠
        large_overlaps = [o for o in overlaps if o.overlap_area > 10000]  # 100x100
        if large_overlaps:
            suggestions.append(
                f"发现 {len(large_overlaps)} 对大面积重叠，可能需要调整图层顺序"
            )
        
        # 生成具体建议
        if not suggestions:
            suggestions.append("未检测到明显的重叠问题")
        
        return suggestions
    
    def get_overlap_matrix(self, overlaps: List[OverlapInfo]) -> Dict:
        """获取重叠矩阵（用于可视化）"""
        all_layers = set()
        for overlap in overlaps:
            all_layers.add(overlap.layer_a)
            all_layers.add(overlap.layer_b)
        
        sorted_layers = sorted(all_layers)
        n = len(sorted_layers)
        layer_to_idx = {l: i for i, l in enumerate(sorted_layers)}
        
        # 创建矩阵
        matrix = [[0 for _ in range(n)] for _ in range(n)]
        
        for overlap in overlaps:
            i = layer_to_idx.get(overlap.layer_a)
            j = layer_to_idx.get(overlap.layer_b)
            if i is not None and j is not None:
                matrix[i][j] = overlap.overlap_area
                matrix[j][i] = overlap.overlap_area
        
        return {
            'layers': sorted_layers,
            'matrix': matrix,
            'size': n
        }


def detect_overlaps(**kwargs) -> OverlapAnalysisResult:
    """便捷函数：检测重叠"""
    detector = OverlapDetector()
    return detector.detect_overlaps(**kwargs)
