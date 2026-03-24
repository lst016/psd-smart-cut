"""
Level 4 - Strategy Layer
策略层 - 切割策略 Agent，决定如何切割 PSD 组件

模块：
- CanvasAnalyzer: 画布分析器
- StrategySelector: 策略选择器
- OverlapDetector: 重叠检测器
- QualityEvaluator: 质量评估器
- Strategy: 统一策略器
"""

from .canvas_analyzer import (
    CanvasInfo,
    CutLine,
    CanvasAnalysisResult,
    CanvasAnalyzer,
    analyze_canvas
)

from .strategy_selector import (
    StrategyType,
    StrategyRule,
    CutRecommendation,
    StrategySelectionResult,
    StrategySelector,
    select_strategy
)

from .overlap_detector import (
    OverlapInfo,
    OverlapAnalysisResult,
    OverlapDetector,
    detect_overlaps
)

from .quality_evaluator import (
    QualityScore,
    CutLineAnalysis,
    QualityEvaluationResult,
    QualityEvaluator,
    evaluate_quality
)

from .strategy import (
    CutRegion,
    CutPlan,
    Strategy,
    create_cut_plan
)

__all__ = [
    # Canvas Analyzer
    'CanvasInfo',
    'CutLine',
    'CanvasAnalysisResult',
    'CanvasAnalyzer',
    'analyze_canvas',
    
    # Strategy Selector
    'StrategyType',
    'StrategyRule',
    'CutRecommendation',
    'StrategySelectionResult',
    'StrategySelector',
    'select_strategy',
    
    # Overlap Detector
    'OverlapInfo',
    'OverlapAnalysisResult',
    'OverlapDetector',
    'detect_overlaps',
    
    # Quality Evaluator
    'QualityScore',
    'CutLineAnalysis',
    'QualityEvaluationResult',
    'QualityEvaluator',
    'evaluate_quality',
    
    # Strategy
    'CutRegion',
    'CutPlan',
    'Strategy',
    'create_cut_plan'
]
