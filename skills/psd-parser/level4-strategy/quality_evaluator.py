"""
Level 4 - Quality Evaluator
质量评估器 - 评估切割质量
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from skills.common import get_logger, get_config, get_error_handler, ErrorCategory

logger = get_logger("quality_evaluator")

# ============ 数据类 ============

@dataclass
class QualityScore:
    """质量分数"""
    overall: float  # 0-100
    cut_accuracy: float  # 切割精度 0-100
    edge_quality: float  # 边缘质量 0-100
    completeness: float  # 内容完整度 0-100
    efficiency: float  # 切割效率 0-100
    issues: List[str]  # 发现的问题
    suggestions: List[str]  # 改进建议

@dataclass
class CutLineAnalysis:
    """切割线分析"""
    line_id: str
    direction: str
    position: int
    crosses_content: bool
    content_interrupted: List[str]  # 被切割打断的内容
    quality_impact: float  # 对质量的影响 -1 to 1

@dataclass
class QualityEvaluationResult:
    """质量评估结果"""
    score: QualityScore
    cut_line_analysis: List[CutLineAnalysis]
    anti_aliasing_detected: bool
    blur_detected: bool
    recommended_adjustments: List[Dict]

# ============ 质量评估器 ============

class QualityEvaluator:
    """质量评估器"""
    
    def __init__(self):
        self.logger = get_logger("quality_evaluator")
        self.config = get_config()
    
    def evaluate(
        self,
        layers: List[Dict],
        cut_lines: List[Dict],
        suggested_slices: Optional[List[Dict]] = None,
        canvas_info: Optional[Dict] = None
    ) -> QualityEvaluationResult:
        """
        评估切割质量
        
        Args:
            layers: 图层列表
            cut_lines: 切割线列表
            suggested_slices: 建议的切片
            canvas_info: 画布信息
        
        Returns:
            QualityEvaluationResult: 质量评估结果
        """
        suggested_slices = suggested_slices or []
        canvas_info = canvas_info or {}
        
        self.logger.info(
            f"评估切割质量: {len(layers)} 个图层, {len(cut_lines)} 条切割线",
            slices_count=len(suggested_slices)
        )
        
        # 分析切割线
        cut_line_analysis = self._analyze_cut_lines(layers, cut_lines)
        
        # 检测锯齿
        anti_aliasing_detected = self._detect_anti_aliasing(layers)
        
        # 检测模糊
        blur_detected = self._detect_blur(layers)
        
        # 计算各项分数
        cut_accuracy = self._calculate_cut_accuracy(cut_line_analysis, layers)
        edge_quality = self._calculate_edge_quality(cut_line_analysis, layers, anti_aliasing_detected)
        completeness = self._calculate_completeness(layers, suggested_slices)
        efficiency = self._calculate_efficiency(layers, suggested_slices, canvas_info)
        
        # 计算总分
        overall = (
            cut_accuracy * 0.3 +
            edge_quality * 0.25 +
            completeness * 0.25 +
            efficiency * 0.2
        )
        
        # 收集问题和建议
        issues = self._collect_issues(cut_line_analysis, anti_aliasing_detected, blur_detected)
        suggestions = self._generate_suggestions(
            cut_line_analysis, issues, layers, cut_lines
        )
        
        # 生成推荐调整
        recommended_adjustments = self._generate_adjustments(
            cut_line_analysis, cut_lines
        )
        
        score = QualityScore(
            overall=overall,
            cut_accuracy=cut_accuracy,
            edge_quality=edge_quality,
            completeness=completeness,
            efficiency=efficiency,
            issues=issues,
            suggestions=suggestions
        )
        
        result = QualityEvaluationResult(
            score=score,
            cut_line_analysis=cut_line_analysis,
            anti_aliasing_detected=anti_aliasing_detected,
            blur_detected=blur_detected,
            recommended_adjustments=recommended_adjustments
        )
        
        self.logger.info(
            f"质量评估完成: overall={overall:.1f}",
            cut_accuracy=cut_accuracy,
            edge_quality=edge_quality,
            completeness=completeness,
            efficiency=efficiency
        )
        
        return result
    
    def _analyze_cut_lines(
        self,
        layers: List[Dict],
        cut_lines: List[Dict]
    ) -> List[CutLineAnalysis]:
        """分析每条切割线"""
        analyses = []
        
        for i, cut_line in enumerate(cut_lines):
            direction = cut_line.get('direction', 'vertical')
            position = cut_line.get('position', 0)
            
            crosses_content = False
            content_interrupted = []
            quality_impact = 0.0
            
            for layer in layers:
                bounds = layer.get('bounds', {})
                x = bounds.get('x', 0)
                y = bounds.get('y', 0)
                w = bounds.get('width', 0)
                h = bounds.get('height', 0)
                
                if direction == 'vertical':
                    # 检查切割线是否穿过图层
                    if x < position < x + w and y < position < y + h:
                        crosses_content = True
                        content_interrupted.append(layer.get('id', 'unknown'))
                        
                        # 计算影响程度
                        cut_at = position - x
                        edge_distance = min(cut_at, w - cut_at)
                        if edge_distance < 5:
                            quality_impact = max(quality_impact, -0.5)  # 切割靠近边缘
                        elif edge_distance < w * 0.2:
                            quality_impact = max(quality_impact, -0.3)
                        else:
                            quality_impact = max(quality_impact, -0.1)
                
                elif direction == 'horizontal':
                    if x < position < x + w and y < position < y + h:
                        crosses_content = True
                        content_interrupted.append(layer.get('id', 'unknown'))
                        
                        cut_at = position - y
                        edge_distance = min(cut_at, h - cut_at)
                        if edge_distance < 5:
                            quality_impact = max(quality_impact, -0.5)
                        elif edge_distance < h * 0.2:
                            quality_impact = max(quality_impact, -0.3)
                        else:
                            quality_impact = max(quality_impact, -0.1)
            
            analyses.append(CutLineAnalysis(
                line_id=cut_line.get('id', f'cut_{i}'),
                direction=direction,
                position=position,
                crosses_content=crosses_content,
                content_interrupted=content_interrupted,
                quality_impact=quality_impact
            ))
        
        return analyses
    
    def _detect_anti_aliasing(self, layers: List[Dict]) -> bool:
        """检测锯齿"""
        # 启发式检测：如果图层边界与像素网格不对齐，可能有锯齿
        for layer in layers:
            bounds = layer.get('bounds', {})
            x = bounds.get('x', 0)
            y = bounds.get('y', 0)
            w = bounds.get('width', 0)
            h = bounds.get('height', 0)
            
            # 检查是否有非整数坐标
            if isinstance(x, float) or isinstance(y, float):
                return True
            if isinstance(w, float) or isinstance(h, float):
                return True
            
            # 检查是否有奇怪的尺寸（可能经过缩放）
            if w > 0 and h > 0:
                aspect = w / h
                if aspect < 0.1 or aspect > 10:
                    # 非常窄或非常宽的图层
                    return True
        
        return False
    
    def _detect_blur(self, layers: List[Dict]) -> bool:
        """检测模糊"""
        for layer in layers:
            style = layer.get('style', {})
            
            # 检查模糊效果
            if style.get('blur') or style.get('gaussian_blur'):
                return True
            
            # 检查透明度
            opacity = style.get('opacity', 1.0)
            if opacity < 0.5:
                return True  # 半透明可能导致模糊感
            
            # 检查混合模式
            blend_mode = style.get('blend_mode', 'normal')
            if blend_mode in ['overlay', 'soft_light', 'hard_light', 'screen', 'multiply']:
                return True  # 这些混合模式可能产生模糊效果
        
        return False
    
    def _calculate_cut_accuracy(
        self,
        cut_analyses: List[CutLineAnalysis],
        layers: List[Dict]
    ) -> float:
        """计算切割精度"""
        if not cut_analyses:
            return 100.0  # 没有切割线，精度满分
        
        total_score = 100.0
        penalty_per_crossing = 10.0
        
        for analysis in cut_analyses:
            if analysis.crosses_content:
                num_interrupted = len(analysis.content_interrupted)
                penalty = penalty_per_crossing * num_interrupted
                total_score -= penalty
        
        return max(0.0, min(100.0, total_score))
    
    def _calculate_edge_quality(
        self,
        cut_analyses: List[CutLineAnalysis],
        layers: List[Dict],
        anti_aliasing: bool
    ) -> float:
        """计算边缘质量"""
        score = 100.0
        
        # 惩罚穿过内容的切割线
        for analysis in cut_analyses:
            if analysis.quality_impact < 0:
                score += analysis.quality_impact * 30  # 转换为 0-100 范围
        
        # 惩罚锯齿
        if anti_aliasing:
            score -= 15
        
        return max(0.0, min(100.0, score))
    
    def _calculate_completeness(
        self,
        layers: List[Dict],
        slices: List[Dict]
    ) -> float:
        """计算内容完整度"""
        if not layers:
            return 100.0
        
        # 统计被包含在切片中的图层
        covered_layers = set()
        for slice_info in slices:
            for layer_id in slice_info.get('layers', []):
                covered_layers.add(layer_id)
        
        all_layer_ids = set(l.get('id') for l in layers)
        coverage = len(covered_layers & all_layer_ids) / len(all_layer_ids) if all_layer_ids else 1.0
        
        return coverage * 100
    
    def _calculate_efficiency(
        self,
        layers: List[Dict],
        slices: List[Dict],
        canvas_info: Dict
    ) -> float:
        """计算切割效率"""
        if not slices:
            return 0.0
        
        canvas_area = canvas_info.get('width', 1) * canvas_info.get('height', 1)
        
        # 计算切片的总输出面积
        total_slice_area = 0
        for slice_info in slices:
            bounds = slice_info.get('bounds', {})
            w = bounds.get('width', 0)
            h = bounds.get('height', 0)
            total_slice_area += w * h
        
        # 效率 = 图层总面积 / 切片总面积（越接近 1 越好）
        layer_area = 0
        for layer in layers:
            bounds = layer.get('bounds', {})
            w = bounds.get('width', 1)
            h = bounds.get('height', 1)
            layer_area += w * h
        
        if total_slice_area == 0:
            return 0.0
        
        efficiency = layer_area / total_slice_area
        
        # 转换为 0-100 分数
        # 效率在 0.7-1.0 之间是最好的
        if 0.7 <= efficiency <= 1.0:
            return 100.0
        elif efficiency > 1.0:
            # 输出面积小于图层面积，可能有遗漏
            return max(0.0, 100 - (efficiency - 1.0) * 50)
        else:
            # 输出面积过大，有很多空白
            return max(0.0, efficiency * 100)
    
    def _collect_issues(
        self,
        cut_analyses: List[CutLineAnalysis],
        anti_aliasing: bool,
        blur: bool
    ) -> List[str]:
        """收集问题"""
        issues = []
        
        # 切割线穿过内容
        crossing_lines = [a for a in cut_analyses if a.crosses_content]
        if crossing_lines:
            issues.append(
                f"{len(crossing_lines)} 条切割线穿过了图层内容"
            )
        
        # 锯齿
        if anti_aliasing:
            issues.append("检测到锯齿，可能影响边缘质量")
        
        # 模糊
        if blur:
            issues.append("检测到模糊效果，可能需要特殊处理")
        
        # 切割线太靠近边缘
        near_edge = [a for a in cut_analyses if abs(a.quality_impact + 0.5) < 0.1]
        if near_edge:
            issues.append(
                f"{len(near_edge)} 条切割线太靠近图层边缘"
            )
        
        return issues
    
    def _generate_suggestions(
        self,
        cut_analyses: List[CutLineAnalysis],
        issues: List[str],
        layers: List[Dict],
        cut_lines: List[Dict]
    ) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        # 基于问题生成建议
        for issue in issues:
            if "穿过了图层内容" in issue:
                suggestions.append(
                    "建议调整切割线位置，避开图层中心区域"
                )
            if "锯齿" in issue:
                suggestions.append(
                    "建议使用 2x 分辨率导出以减少锯齿"
                )
            if "模糊" in issue:
                suggestions.append(
                    "建议检查图层的模糊效果，确保导出时保持一致"
                )
            if "太靠近图层边缘" in issue:
                suggestions.append(
                    "建议将切割线移动到图层边缘或留出至少 5px 边距"
                )
        
        # 检查切片数量
        if len(cut_lines) > len(layers) * 0.5:
            suggestions.append(
                f"切割线数量({len(cut_lines)})较多，可能产生较多小文件"
            )
        
        # 如果没有问题
        if not suggestions:
            suggestions.append("切割质量良好，无需调整")
        
        return suggestions
    
    def _generate_adjustments(
        self,
        cut_analyses: List[CutLineAnalysis],
        cut_lines: List[Dict]
    ) -> List[Dict]:
        """生成推荐调整"""
        adjustments = []
        
        for analysis in cut_analyses:
            if analysis.crosses_content:
                # 建议移动切割线
                if analysis.direction == 'vertical':
                    # 尝试移动到图层左边缘或右边缘
                    suggestions = []
                    for layer_id in analysis.content_interrupted:
                        suggestions.append({
                            'type': 'move_cut_line',
                            'line_id': analysis.line_id,
                            'original_position': analysis.position,
                            'suggested_positions': [
                                f"left_of_layer:{layer_id}",
                                f"right_of_layer:{layer_id}"
                            ],
                            'reason': '避开图层内容'
                        })
                    adjustments.extend(suggestions)
                else:
                    # 水平切割线
                    for layer_id in analysis.content_interrupted:
                        adjustments.append({
                            'type': 'move_cut_line',
                            'line_id': analysis.line_id,
                            'original_position': analysis.position,
                            'suggested_positions': [
                                f"above_layer:{layer_id}",
                                f"below_layer:{layer_id}"
                            ],
                            'reason': '避开图层内容'
                        })
        
        return adjustments


def evaluate_quality(**kwargs) -> QualityEvaluationResult:
    """便捷函数：评估质量"""
    evaluator = QualityEvaluator()
    return evaluator.evaluate(**kwargs)
