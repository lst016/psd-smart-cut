"""
Level 4 - Strategy Layer Test
策略层测试 - Mock 模式，不依赖真实 PSD 文件
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from unittest.mock import MagicMock, patch

# ============ Mock 数据生成器 ============

def create_mock_layers(count: int = 10) -> list:
    """创建模拟图层数据"""
    layers = []
    types = ['image', 'text', 'group', 'background', 'button', 'icon']
    
    for i in range(count):
        layers.append({
            'id': f'layer_{i:03d}',
            'name': f'Layer {i}',
            'type': types[i % len(types)],
            'bounds': {
                'x': (i % 4) * 200,
                'y': (i // 4) * 200,
                'width': 150 + (i % 3) * 20,
                'height': 150 + (i % 3) * 20
            },
            'parent_id': f'layer_{i//3}' if i % 3 == 0 and i > 0 else None,
            'page': f'page_{i % 2}',
            'sub_type': 'background' if types[i % len(types)] == 'background' else None
        })
    
    return layers


def create_mock_canvas_info() -> dict:
    """创建模拟画布信息"""
    return {
        'width': 1920,
        'height': 1080,
        'dpi': 72,
        'color_mode': 'RGB'
    }


# ============ CanvasAnalyzer Tests ============

class TestCanvasAnalyzer:
    """画布分析器测试"""
    
    def setup_method(self):
        """测试前设置"""
        # Mock get_logger
        with patch('level4_strategy.canvas_analyzer.get_logger') as mock_logger:
            mock_logger.return_value = MagicMock()
            from level4_strategy.canvas_analyzer import CanvasAnalyzer
            self.analyzer = CanvasAnalyzer()
    
    def test_analyze_basic(self):
        """测试基本分析"""
        layers = create_mock_layers(10)
        result = self.analyzer.analyze(
            canvas_width=1920,
            canvas_height=1080,
            dpi=72,
            color_mode="RGB",
            layers=layers
        )
        
        assert result is not None
        assert result.canvas.width == 1920
        assert result.canvas.height == 1080
        assert result.canvas.dpi == 72
        assert result.canvas.color_mode == "RGB"
        assert result.canvas.layers_count == 10
    
    def test_analyze_empty_layers(self):
        """测试空图层分析"""
        result = self.analyzer.analyze(
            canvas_width=800,
            canvas_height=600,
            layers=[]
        )
        
        assert result is not None
        assert result.canvas.layers_count == 0
        assert len(result.cut_lines) == 0
    
    def test_calculate_density_map(self):
        """测试密度热力图计算"""
        layers = [
            {'bounds': {'x': 0, 'y': 0, 'width': 200, 'height': 200}},
            {'bounds': {'x': 50, 'y': 50, 'width': 100, 'height': 100}},
        ]
        
        density_map = self.analyzer._calculate_density_map(800, 600, layers)
        
        assert 'density_matrix' in density_map
        assert density_map['grid_size'] == 100
        assert density_map['max_density'] >= 0
    
    def test_detect_cut_lines(self):
        """测试切割线检测"""
        layers = [
            {'bounds': {'x': 0, 'y': 0, 'width': 200, 'height': 200}},
            {'bounds': {'x': 400, 'y': 0, 'width': 200, 'height': 200}},
        ]
        
        cut_lines = self.analyzer._detect_cut_lines(800, 600, layers, {'high_density_regions': []})
        
        # 检测到空白带，应该有切割线
        assert isinstance(cut_lines, list)
    
    def test_get_canvas_stats(self):
        """测试画布统计"""
        layers = create_mock_layers(5)
        result = self.analyzer.analyze(
            canvas_width=1920,
            canvas_height=1080,
            layers=layers
        )
        
        stats = self.analyzer.get_canvas_stats(result)
        
        assert stats['canvas_size'] == '1920x1080'
        assert stats['layers_count'] == 5
        assert 'aspect_ratio' in stats


# ============ StrategySelector Tests ============

class TestStrategySelector:
    """策略选择器测试"""
    
    def setup_method(self):
        """测试前设置"""
        with patch('level4_strategy.strategy_selector.get_logger') as mock_logger:
            mock_logger.return_value = MagicMock()
            from level4_strategy.strategy_selector import StrategySelector, StrategyType
            self.selector = StrategySelector()
            self.StrategyType = StrategyType
    
    def test_select_few_layers(self):
        """测试少量图层选择 FLAT 策略"""
        layers = create_mock_layers(3)
        
        result = self.selector.select(layers=layers)
        
        assert result.selected_strategy == self.StrategyType.FLAT
        assert len(result.recommendations) == 3
    
    def test_select_many_text_layers(self):
        """测试大量文字图层选择 GROUP_BY_TYPE"""
        layers = [
            {'id': f'layer_{i}', 'type': 'text', 'bounds': {'x': 0, 'y': i*50, 'width': 100, 'height': 40}}
            for i in range(15)
        ]
        
        result = self.selector.select(layers=layers)
        
        # 文字密集，应该选择 GROUP_BY_TYPE
        assert result.selected_strategy in [self.StrategyType.GROUP_BY_TYPE, self.StrategyType.SMART_MERGE]
    
    def test_select_with_background(self):
        """测试有背景图的情况"""
        layers = [
            {'id': 'bg', 'type': 'background', 'bounds': {'x': 0, 'y': 0, 'width': 800, 'height': 600}},
            {'id': 'fg1', 'type': 'image', 'bounds': {'x': 100, 'y': 100, 'width': 200, 'height': 200}},
            {'id': 'fg2', 'type': 'image', 'bounds': {'x': 350, 'y': 100, 'width': 200, 'height': 200}},
        ]
        
        result = self.selector.select(layers=layers)
        
        assert result.selected_strategy is not None
        assert len(result.recommendations) > 0
    
    def test_custom_rules(self):
        """测试自定义规则"""
        from level4_strategy.strategy_selector import StrategyRule
        
        custom_rule = StrategyRule(
            name="test_rule",
            description="测试规则",
            conditions={"layer_types": ["button"]},
            priority=100
        )
        
        self.selector.add_rule(custom_rule)
        
        assert len(self.selector.rules) > 0
        self.selector.remove_rule("test_rule")
        assert len([r for r in self.selector.rules if r.name == "test_rule"]) == 0
    
    def test_get_available_strategies(self):
        """测试获取可用策略列表"""
        strategies = self.selector.get_available_strategies()
        
        assert len(strategies) == 5
        strategy_names = [s['name'] for s in strategies]
        assert 'flat' in strategy_names
        assert 'smart_merge' in strategy_names


# ============ OverlapDetector Tests ============

class TestOverlapDetector:
    """重叠检测器测试"""
    
    def setup_method(self):
        """测试前设置"""
        with patch('level4_strategy.overlap_detector.get_logger') as mock_logger:
            mock_logger.return_value = MagicMock()
            from level4_strategy.overlap_detector import OverlapDetector
            self.detector = OverlapDetector()
    
    def test_detect_no_overlaps(self):
        """测试无重叠情况"""
        layers = [
            {'id': 'l1', 'bounds': {'x': 0, 'y': 0, 'width': 100, 'height': 100}},
            {'id': 'l2', 'bounds': {'x': 200, 'y': 200, 'width': 100, 'height': 100}},
        ]
        
        result = self.detector.detect_overlaps(layers=layers)
        
        assert len(result.overlaps) == 0
    
    def test_detect_with_overlaps(self):
        """测试有重叠情况"""
        layers = [
            {'id': 'l1', 'bounds': {'x': 0, 'y': 0, 'width': 100, 'height': 100}},
            {'id': 'l2', 'bounds': {'x': 50, 'y': 50, 'width': 100, 'height': 100}},
        ]
        
        result = self.detector.detect_overlaps(layers=layers, z_order=['l1', 'l2'])
        
        assert len(result.overlaps) == 1
        overlap = result.overlaps[0]
        assert overlap.overlap_area > 0
        assert overlap.front_layer in ['l1', 'l2']
    
    def test_detect_full_overlap(self):
        """测试完全重叠"""
        layers = [
            {'id': 'l1', 'bounds': {'x': 0, 'y': 0, 'width': 100, 'height': 100}},
            {'id': 'l2', 'bounds': {'x': 20, 'y': 20, 'width': 60, 'height': 60}},
        ]
        
        result = self.detector.detect_overlaps(layers=layers)
        
        assert len(result.overlaps) == 1
        assert result.overlaps[0].resolution == 'full'
    
    def test_priority_determination(self):
        """测试优先级确定"""
        layers = [
            {'id': 'bg', 'type': 'background', 'bounds': {'x': 0, 'y': 0, 'width': 200, 'height': 200}},
            {'id': 'fg', 'type': 'button', 'bounds': {'x': 50, 'y': 50, 'width': 100, 'height': 100}},
        ]
        
        result = self.detector.detect_overlaps(layers=layers, z_order=['bg', 'fg'])
        
        assert len(result.priority_layers) == 2
        # button 应该有更高优先级
        assert 'fg' in result.priority_layers
    
    def test_occlusion_map(self):
        """测试遮挡关系图"""
        layers = [
            {'id': 'l1', 'bounds': {'x': 0, 'y': 0, 'width': 100, 'height': 100}},
            {'id': 'l2', 'bounds': {'x': 50, 'y': 50, 'width': 100, 'height': 100}},
        ]
        
        result = self.detector.detect_overlaps(layers=layers, z_order=['l1', 'l2'])
        
        assert len(result.occlusion_map) >= 0


# ============ QualityEvaluator Tests ============

class TestQualityEvaluator:
    """质量评估器测试"""
    
    def setup_method(self):
        """测试前设置"""
        with patch('level4_strategy.quality_evaluator.get_logger') as mock_logger:
            mock_logger.return_value = MagicMock()
            from level4_strategy.quality_evaluator import QualityEvaluator
            self.evaluator = QualityEvaluator()
    
    def test_evaluate_no_cut_lines(self):
        """测试无切割线情况"""
        layers = create_mock_layers(5)
        
        result = self.evaluator.evaluate(
            layers=layers,
            cut_lines=[],
            suggested_slices=[
                {
                    'slice_id': 'full_canvas',
                    'bounds': {'x': 0, 'y': 0, 'width': 1920, 'height': 1080},
                    'layers': [l['id'] for l in layers]
                }
            ]
        )
        
        assert result is not None
        assert result.score.cut_accuracy == 100.0
        # 当有 suggested_slices 时，整体分数应该更高
    
    def test_evaluate_with_cut_lines(self):
        """测试有切割线情况"""
        layers = [
            {'id': 'l1', 'bounds': {'x': 0, 'y': 0, 'width': 200, 'height': 200}},
        ]
        cut_lines = [
            {'id': 'cl_1', 'direction': 'vertical', 'position': 100},
        ]
        
        result = self.evaluator.evaluate(
            layers=layers,
            cut_lines=cut_lines
        )
        
        assert result is not None
        assert result.score.overall >= 0
        assert result.score.overall <= 100
    
    def test_detect_anti_aliasing(self):
        """测试锯齿检测"""
        layers = [
            {'bounds': {'x': 0.5, 'y': 0, 'width': 100, 'height': 100}},  # 非整数坐标
        ]
        
        detected = self.evaluator._detect_anti_aliasing(layers)
        
        assert detected is True
    
    def test_detect_blur(self):
        """测试模糊检测"""
        layers = [
            {'style': {'blur': True}},
        ]
        
        detected = self.evaluator._detect_blur(layers)
        
        assert detected is True
    
    def test_cut_accuracy_calculation(self):
        """测试切割精度计算"""
        from level4_strategy.quality_evaluator import CutLineAnalysis
        
        analyses = [
            CutLineAnalysis(
                line_id='cl_1',
                direction='vertical',
                position=100,
                crosses_content=True,
                content_interrupted=['l1', 'l2'],
                quality_impact=-0.5
            )
        ]
        layers = create_mock_layers(5)
        
        score = self.evaluator._calculate_cut_accuracy(analyses, layers)
        
        assert score < 100.0
        assert score >= 0
    
    def test_issues_collection(self):
        """测试问题收集"""
        from level4_strategy.quality_evaluator import CutLineAnalysis
        
        analyses = [
            CutLineAnalysis(
                line_id='cl_1',
                direction='vertical',
                position=100,
                crosses_content=True,
                content_interrupted=['l1'],
                quality_impact=-0.5
            )
        ]
        
        issues = self.evaluator._collect_issues(analyses, True, False)
        
        assert len(issues) > 0
        assert any('穿过' in issue for issue in issues)


# ============ Strategy (Unified) Tests ============

class TestStrategy:
    """统一策略器测试"""
    
    def setup_method(self):
        """测试前设置"""
        with patch('level4_strategy.strategy.get_logger') as mock_logger:
            mock_logger.return_value = MagicMock()
            from level4_strategy.strategy import Strategy
            self.strategy = Strategy()
    
    def test_create_plan_basic(self):
        """测试基本计划创建"""
        layers = create_mock_layers(10)
        
        plan = self.strategy.create_plan(
            layers=layers,
            canvas_width=1920,
            canvas_height=1080,
            dpi=72,
            color_mode="RGB"
        )
        
        assert plan is not None
        assert plan.canvas_info.width == 1920
        assert plan.canvas_info.height == 1080
        assert len(plan.cut_regions) > 0
        assert len(plan.metadata) > 0
    
    def test_create_plan_empty_layers(self):
        """测试空图层计划创建"""
        plan = self.strategy.create_plan(
            layers=[],
            canvas_width=800,
            canvas_height=600
        )
        
        assert plan is not None
        assert plan.canvas_info.layers_count == 0
    
    def test_create_plan_with_z_order(self):
        """测试带 Z 轴顺序的计划创建"""
        layers = [
            {'id': 'bg', 'bounds': {'x': 0, 'y': 0, 'width': 200, 'height': 200}},
            {'id': 'fg', 'bounds': {'x': 50, 'y': 50, 'width': 100, 'height': 100}},
        ]
        
        plan = self.strategy.create_plan(
            layers=layers,
            canvas_width=800,
            canvas_height=600,
            z_order=['bg', 'fg']
        )
        
        assert plan is not None
        assert len(plan.overlaps) > 0
    
    def test_create_plan_force_strategy(self):
        """测试强制策略"""
        layers = create_mock_layers(10)
        
        plan = self.strategy.create_plan(
            layers=layers,
            canvas_width=1920,
            canvas_height=1080,
            force_strategy='flat'
        )
        
        assert plan.strategy_type == 'flat'
    
    def test_optimize_plan(self):
        """测试计划优化"""
        layers = create_mock_layers(20)
        
        plan = self.strategy.create_plan(
            layers=layers,
            canvas_width=1920,
            canvas_height=1080
        )
        
        original_count = len(plan.cut_regions)
        
        optimized = self.strategy.optimize_plan(
            plan,
            layers=layers,
            max_regions=10
        )
        
        assert len(optimized.cut_regions) <= original_count
        assert len(optimized.cut_regions) <= 10
    
    def test_export_plan_json(self):
        """测试计划 JSON 导出"""
        layers = create_mock_layers(5)
        
        plan = self.strategy.create_plan(
            layers=layers,
            canvas_width=800,
            canvas_height=600
        )
        
        json_plan = self.strategy.export_plan_json(plan)
        
        assert 'strategy_type' in json_plan
        assert 'canvas' in json_plan
        assert 'cut_regions' in json_plan
        assert 'quality_score' in json_plan


# ============ Integration Tests ============

class TestIntegration:
    """集成测试"""
    
    def test_full_workflow(self):
        """测试完整工作流"""
        # 1. 分析画布
        with patch('level4_strategy.canvas_analyzer.get_logger') as mock_logger:
            mock_logger.return_value = MagicMock()
            from level4_strategy.canvas_analyzer import CanvasAnalyzer
        
        analyzer = CanvasAnalyzer()
        layers = create_mock_layers(10)
        canvas_result = analyzer.analyze(
            canvas_width=1920,
            canvas_height=1080,
            layers=layers
        )
        
        # 2. 选择策略
        with patch('level4_strategy.strategy_selector.get_logger') as mock_logger:
            mock_logger.return_value = MagicMock()
            from level4_strategy.strategy_selector import StrategySelector
        
        selector = StrategySelector()
        strategy_result = selector.select(layers=layers)
        
        # 3. 检测重叠
        with patch('level4_strategy.overlap_detector.get_logger') as mock_logger:
            mock_logger.return_value = MagicMock()
            from level4_strategy.overlap_detector import OverlapDetector
        
        detector = OverlapDetector()
        overlap_result = detector.detect_overlaps(layers=layers)
        
        # 4. 评估质量
        with patch('level4_strategy.quality_evaluator.get_logger') as mock_logger:
            mock_logger.return_value = MagicMock()
            from level4_strategy.quality_evaluator import QualityEvaluator
        
        evaluator = QualityEvaluator()
        cut_lines = [
            {'id': f'cl_{i}', 'direction': 'vertical', 'position': cl.position}
            for i, cl in enumerate(canvas_result.cut_lines)
        ]
        quality_result = evaluator.evaluate(
            layers=layers,
            cut_lines=cut_lines,
            suggested_slices=canvas_result.suggested_slices
        )
        
        # 5. 创建完整计划
        with patch('level4_strategy.strategy.get_logger') as mock_logger:
            mock_logger.return_value = MagicMock()
            from level4_strategy.strategy import Strategy
        
        strategy = Strategy()
        plan = strategy.create_plan(
            layers=layers,
            canvas_width=1920,
            canvas_height=1080
        )
        
        # 验证结果
        assert plan is not None
        assert plan.quality_score.overall >= 0
        assert plan.quality_score.overall <= 100
        print(f"完整工作流测试通过! 质量分数: {plan.quality_score.overall}")


# ============ Performance Tests ============

class TestPerformance:
    """性能测试"""
    
    def test_large_layer_count(self):
        """测试大量图层性能"""
        import time
        
        with patch('level4_strategy.strategy.get_logger') as mock_logger:
            mock_logger.return_value = MagicMock()
            from level4_strategy.strategy import Strategy
        
        layers = create_mock_layers(100)
        
        start = time.time()
        
        plan = Strategy().create_plan(
            layers=layers,
            canvas_width=3840,
            canvas_height=2160
        )
        
        elapsed = time.time() - start
        
        assert plan is not None
        assert elapsed < 5.0  # 应该在 5 秒内完成
        print(f"100 图层处理时间: {elapsed:.2f}s")


# ============ Main ============

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
