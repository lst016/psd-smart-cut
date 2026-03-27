"""
Level 4 - Strategy
统一策略器 - 协调所有策略模块，生成完整切割计划
"""
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from skills.common import get_logger, get_config, get_error_handler, ErrorCategory
from .canvas_analyzer import CanvasAnalyzer, CanvasInfo, CanvasAnalysisResult
from .strategy_selector import StrategySelector, StrategyType, StrategySelectionResult
from .overlap_detector import OverlapDetector, OverlapInfo, OverlapAnalysisResult
from .quality_evaluator import QualityEvaluator, QualityScore, QualityEvaluationResult

logger = get_logger("strategy")

# ============ 数据类 ============

@dataclass
class CutRegion:
    """切割区域"""
    region_id: str
    layer_ids: List[str]
    bounds: Tuple[int, int, int, int]  # x, y, w, h
    cut_type: str  # 'export'/'merge'/'ignore'
    reason: str

@dataclass
class CutPlan:
    """切割计划"""
    strategy_type: str
    canvas_info: CanvasInfo
    cut_regions: List[CutRegion]
    overlaps: List[OverlapInfo]
    quality_score: QualityScore
    metadata: Dict

    @property
    def cut_groups(self) -> List[CutRegion]:
        """Backward-compatible alias used by older docs/examples."""
        return self.cut_regions

# ============ 统一策略器 ============

class Strategy:
    """统一策略器"""
    
    def __init__(self):
        self.logger = get_logger("strategy")
        self.config = get_config()
        
        # 初始化各模块
        self.canvas_analyzer = CanvasAnalyzer()
        self.strategy_selector = StrategySelector()
        self.overlap_detector = OverlapDetector()
        self.quality_evaluator = QualityEvaluator()
    
    def create_plan(
        self,
        layers: List[Dict],
        canvas_width: int,
        canvas_height: int,
        dpi: int = 72,
        color_mode: str = "RGB",
        z_order: Optional[List[str]] = None,
        classification_results: Optional[List[Dict]] = None,
        force_strategy: Optional[str] = None
    ) -> CutPlan:
        """
        创建切割计划
        
        Args:
            layers: 图层列表
            canvas_width: 画布宽度
            canvas_height: 画布高度
            dpi: 分辨率
            color_mode: 颜色模式
            z_order: Z 轴顺序
            classification_results: 分类结果
            force_strategy: 强制使用的策略类型
        
        Returns:
            CutPlan: 切割计划
        """
        z_order = z_order or [l.get('id') for l in layers]
        classification_results = classification_results or []
        
        self.logger.info(
            f"创建切割计划: {len(layers)} 个图层, {canvas_width}x{canvas_height}",
            force_strategy=force_strategy
        )
        
        # 1. 分析画布
        canvas_result = self.canvas_analyzer.analyze(
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            dpi=dpi,
            color_mode=color_mode,
            layers=layers
        )
        
        # 2. 选择策略
        canvas_info_dict = {
            'width': canvas_width,
            'height': canvas_height,
            'dpi': dpi,
            'color_mode': color_mode
        }
        
        strategy_result = self.strategy_selector.select(
            layers=layers,
            canvas_info=canvas_info_dict,
            classification_results=classification_results
        )
        
        # 如果指定了强制策略
        if force_strategy:
            try:
                forced = StrategyType(force_strategy)
                strategy_result.selected_strategy = forced
                self.logger.info(f"使用强制策略: {forced.value}")
            except ValueError:
                self.logger.warning(f"无效的策略类型: {force_strategy}")
        
        # 3. 检测重叠
        overlap_result = self.overlap_detector.detect_overlaps(
            layers=layers,
            z_order=z_order
        )
        
        # 4. 评估质量
        cut_lines = [
            {'id': f'cl_{i}', 'direction': cl.direction, 'position': cl.position}
            for i, cl in enumerate(canvas_result.cut_lines)
        ]
        
        suggested_slices = canvas_result.suggested_slices
        
        quality_result = self.quality_evaluator.evaluate(
            layers=layers,
            cut_lines=cut_lines,
            suggested_slices=suggested_slices,
            canvas_info=canvas_info_dict
        )
        
        # 5. 生成切割区域
        cut_regions = self._generate_cut_regions(
            layers=layers,
            strategy=strategy_result.selected_strategy,
            recommendations=strategy_result.recommendations,
            suggested_slices=suggested_slices,
            overlap_result=overlap_result
        )
        
        # 6. 构建元数据
        metadata = {
            'canvas_analysis': self.canvas_analyzer.get_canvas_stats(canvas_result),
            'strategy_selection': {
                'selected': strategy_result.selected_strategy.value,
                'rules_applied': strategy_result.custom_rules_applied,
                'recommendations_count': len(strategy_result.recommendations)
            },
            'overlap_analysis': {
                'overlap_pairs': len(overlap_result.overlaps),
                'priority_layers': overlap_result.priority_layers[:10],  # 前10个
                'suggestions': overlap_result.suggestions
            },
            'quality_metrics': {
                'overall': quality_result.score.overall,
                'cut_accuracy': quality_result.score.cut_accuracy,
                'edge_quality': quality_result.score.edge_quality,
                'completeness': quality_result.score.completeness,
                'efficiency': quality_result.score.efficiency
            },
            'anti_aliasing': quality_result.anti_aliasing_detected,
            'blur_detected': quality_result.blur_detected,
            'adjustments': quality_result.recommended_adjustments
        }
        
        plan = CutPlan(
            strategy_type=strategy_result.selected_strategy.value,
            canvas_info=canvas_result.canvas,
            cut_regions=cut_regions,
            overlaps=overlap_result.overlaps,
            quality_score=quality_result.score,
            metadata=metadata
        )
        
        self.logger.info(
            f"切割计划创建完成: {len(cut_regions)} 个区域",
            quality_score=quality_result.score.overall
        )
        
        return plan
    
    def _generate_cut_regions(
        self,
        layers: List[Dict],
        strategy: StrategyType,
        recommendations: List,
        suggested_slices: List[Dict],
        overlap_result: OverlapAnalysisResult
    ) -> List[CutRegion]:
        """生成切割区域"""
        regions = []
        
        # 从建议切片生成区域
        for slice_info in suggested_slices:
            bounds = slice_info.get('bounds', {})
            layer_ids = slice_info.get('layers', [])
            
            if not layer_ids:
                continue
            
            # 确定切割类型
            cut_type = self._determine_cut_type(
                layers, layer_ids, strategy, overlap_result
            )
            
            regions.append(CutRegion(
                region_id=slice_info.get('slice_id', 'unknown'),
                layer_ids=layer_ids,
                bounds=(
                    bounds.get('x', 0),
                    bounds.get('y', 0),
                    bounds.get('width', 0),
                    bounds.get('height', 0)
                ),
                cut_type=cut_type,
                reason=slice_info.get('reason', '')
            ))
        
        # 如果没有生成任何区域，使用默认区域
        if not regions:
            regions.append(CutRegion(
                region_id='full_canvas',
                layer_ids=[l.get('id') for l in layers],
                bounds=(0, 0, 0, 0),  # 需要从画布信息填充
                cut_type='export',
                reason='默认区域'
            ))
        
        return regions
    
    def _determine_cut_type(
        self,
        layers: List[Dict],
        layer_ids: List[str],
        strategy: StrategyType,
        overlap_result: OverlapAnalysisResult
    ) -> str:
        """确定切割类型"""
        # 获取这些图层的类型
        layer_types = set()
        for layer in layers:
            if layer.get('id') in layer_ids:
                layer_types.add(layer.get('type', 'unknown'))
        
        # 检查是否与其他区域重叠
        region_layers = {l.get('id') for l in layers if l.get('id') in layer_ids}
        has_overlap = False
        for overlap in overlap_result.overlaps:
            if overlap.layer_a in region_layers or overlap.layer_b in region_layers:
                has_overlap = True
                break
        
        # 根据策略和重叠情况决定类型
        if strategy == StrategyType.SMART_MERGE:
            return 'merge'
        elif has_overlap:
            return 'export'  # 有重叠，需要单独导出以避免问题
        elif 'background' in layer_types:
            return 'export'  # 背景图单独导出
        elif len(layer_ids) == 1:
            return 'export'  # 单个图层单独导出
        else:
            return 'merge'  # 多个相似图层可以合并
    
    def optimize_plan(
        self,
        plan: CutPlan,
        layers: List[Dict],
        max_regions: int = 50,
        min_region_area: int = 100
    ) -> CutPlan:
        """
        优化切割计划
        
        Args:
            plan: 原始计划
            layers: 图层列表
            max_regions: 最大区域数
            min_region_area: 最小区域面积
        
        Returns:
            CutPlan: 优化后的计划
        """
        self.logger.info(
            f"优化切割计划: {len(plan.cut_regions)} -> {max_regions} 区域"
        )
        
        # 过滤掉太小的区域
        optimized_regions = [
            r for r in plan.cut_regions
            if r.bounds[2] * r.bounds[3] >= min_region_area
        ]
        
        # 如果区域太多，合并小区域
        if len(optimized_regions) > max_regions:
            self.logger.info(f"区域数量超过限制，合并小区域")
            optimized_regions = self._merge_small_regions(
                optimized_regions, layers, max_regions
            )
        
        # 更新计划
        plan.cut_regions = optimized_regions
        
        self.logger.info(
            f"优化完成: {len(optimized_regions)} 个区域",
            total_area=sum(r.bounds[2] * r.bounds[3] for r in optimized_regions)
        )
        
        return plan
    
    def _merge_small_regions(
        self,
        regions: List[CutRegion],
        layers: List[Dict],
        target_count: int
    ) -> List[CutRegion]:
        """合并小区域"""
        if len(regions) <= target_count:
            return regions
        
        # 按面积排序
        sorted_regions = sorted(
            regions,
            key=lambda r: r.bounds[2] * r.bounds[3]
        )
        
        # 合并最小的区域到相邻区域
        while len(sorted_regions) > target_count:
            smallest = sorted_regions.pop(0)
            
            # 找到最近的区域
            min_distance = float('inf')
            merge_target = None
            merge_idx = None
            
            for i, other in enumerate(sorted_regions):
                dist = abs(smallest.bounds[0] - other.bounds[0]) + \
                       abs(smallest.bounds[1] - other.bounds[1])
                if dist < min_distance:
                    min_distance = dist
                    merge_target = other
                    merge_idx = i
            
            # 合并
            if merge_target:
                merged_bounds = (
                    min(smallest.bounds[0], merge_target.bounds[0]),
                    min(smallest.bounds[1], merge_target.bounds[1]),
                    max(smallest.bounds[0] + smallest.bounds[2],
                        merge_target.bounds[0] + merge_target.bounds[2]) -
                    min(smallest.bounds[0], merge_target.bounds[0]),
                    max(smallest.bounds[1] + smallest.bounds[3],
                        merge_target.bounds[1] + merge_target.bounds[3]) -
                    min(smallest.bounds[1], merge_target.bounds[1])
                )
                
                sorted_regions[merge_idx] = CutRegion(
                    region_id=f"merged_{len(sorted_regions)}",
                    layer_ids=smallest.layer_ids + merge_target.layer_ids,
                    bounds=merged_bounds,
                    cut_type='merge',
                    reason='合并小区域'
                )
        
        return sorted_regions
    
    def export_plan_json(self, plan: CutPlan) -> Dict:
        """导出计划为 JSON 格式"""
        return {
            'strategy_type': plan.strategy_type,
            'canvas': {
                'width': plan.canvas_info.width,
                'height': plan.canvas_info.height,
                'dpi': plan.canvas_info.dpi,
                'color_mode': plan.canvas_info.color_mode,
                'layers_count': plan.canvas_info.layers_count
            },
            'cut_regions': [
                {
                    'region_id': r.region_id,
                    'layer_ids': r.layer_ids,
                    'bounds': {
                        'x': r.bounds[0],
                        'y': r.bounds[1],
                        'width': r.bounds[2],
                        'height': r.bounds[3]
                    },
                    'cut_type': r.cut_type,
                    'reason': r.reason
                }
                for r in plan.cut_regions
            ],
            'overlaps': [
                {
                    'layer_a': o.layer_a,
                    'layer_b': o.layer_b,
                    'overlap_rect': {
                        'x': o.overlap_rect[0],
                        'y': o.overlap_rect[1],
                        'width': o.overlap_rect[2],
                        'height': o.overlap_rect[3]
                    },
                    'overlap_area': o.overlap_area,
                    'percentage_a': o.percentage_a,
                    'percentage_b': o.percentage_b,
                    'front_layer': o.front_layer,
                    'resolution': o.resolution
                }
                for o in plan.overlaps
            ],
            'quality_score': {
                'overall': plan.quality_score.overall,
                'cut_accuracy': plan.quality_score.cut_accuracy,
                'edge_quality': plan.quality_score.edge_quality,
                'completeness': plan.quality_score.completeness,
                'efficiency': plan.quality_score.efficiency,
                'issues': plan.quality_score.issues,
                'suggestions': plan.quality_score.suggestions
            },
            'metadata': plan.metadata
        }


def create_cut_plan(**kwargs) -> CutPlan:
    """便捷函数：创建切割计划"""
    strategy = Strategy()
    return strategy.create_plan(**kwargs)
