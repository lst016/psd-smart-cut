"""
Level 9 - Performance Tests
性能基准测试 - 测试各模块响应时间、内存使用和批量处理能力

测试内容：
- 各模块响应时间基准
- 内存使用监控
- 批量处理能力测试
- 生成性能报告
"""

import pytest
import sys
import time
import json
import tracemalloc
import gc
from pathlib import Path
from unittest.mock import MagicMock, patch

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from skills.psd_parser.level1_parse import (
    PSDDocument, PageInfo, LayerInfo,
    PSDParser, PageExtractor, LayerReader, HierarchyBuilder
)
from skills.psd_parser.level2_classify import (
    LayerType, LayerClassifier, ImageClassifier, TextClassifier
)
from skills.psd_parser.level3_recognize import (
    Recognizer, RecognitionResult, RegionDetector, ComponentNamer
)
from skills.psd_parser.level4_strategy import (
    Strategy, CutPlan, CutRegion,
    StrategySelector, StrategyType, CanvasAnalyzer, OverlapDetector
)
from skills.psd_parser.level5_export import (
    Exporter, ExportReport, CutPlan as ExportCutPlan,
    AssetExporter, NamingManager
)
from skills.psd_parser.level6_extract import (
    Extractor, ExtractionResult, TextReader, StyleExtractor, PositionReader
)
from skills.psd_parser.level7_generate import (
    SpecGenerator, SpecResult, ComponentSpec,
    DimensionGenerator, StyleGenerator, SpecValidator
)
from skills.psd_parser.level8_document import (
    ReadmeGenerator, ManifestGenerator, PreviewGenerator, DocAggregator
)


# ============================================================================
# 性能基准配置
# ============================================================================

BENCHMARK_CONFIG = {
    "iterations": 100,
    "warmup_runs": 10,
    "memory_samples": 5,
    "batch_sizes": [1, 10, 50, 100]
}


# ============================================================================
# Mock 数据生成器
# ============================================================================

def create_large_psd_document(layer_count=100):
    """创建大型 Mock PSD 文档"""
    layers = []
    for i in range(layer_count):
        layer = LayerInfo(
            id=f"layer_{i}",
            name=f"Layer {i}",
            kind="image" if i % 3 == 0 else "button" if i % 3 == 1 else "text",
            visible=True,
            locked=False,
            left=(i % 10) * 100,
            top=(i // 10) * 100,
            right=(i % 10) * 100 + 100,
            bottom=(i // 10) * 100 + 100,
            width=100,
            height=100,
            parent_id=None
        )
        layers.append(layer)
    
    pages = [
        PageInfo(
            index=0,
            name="Page 1",
            width=1920,
            height=1080 * ((layer_count // 10) + 1),
            layers=layers
        )
    ]
    
    return PSDDocument(
        file_path="mock_large.psd",
        version="2024",
        width=1920,
        height=1080 * ((layer_count // 10) + 1),
        pages=pages,
        total_layers=len(layers)
    )


# ============================================================================
# 性能报告生成器
# ============================================================================

class PerformanceReport:
    """性能报告生成器"""
    
    def __init__(self):
        self.results = {}
    
    def add_result(self, module: str, operation: str, 
                   duration: float, memory_mb: float = 0):
        """添加性能结果"""
        if module not in self.results:
            self.results[module] = []
        
        self.results[module].append({
            "operation": operation,
            "duration_ms": round(duration * 1000, 3),
            "memory_mb": round(memory_mb, 3),
            "timestamp": time.time()
        })
    
    def get_summary(self, module: str) -> dict:
        """获取模块性能摘要"""
        if module not in self.results:
            return {}
        
        results = self.results[module]
        durations = [r["duration_ms"] for r in results]
        memories = [r["memory_mb"] for r in results]
        
        return {
            "module": module,
            "operations": len(results),
            "avg_duration_ms": round(sum(durations) / len(durations), 3) if durations else 0,
            "min_duration_ms": round(min(durations), 3) if durations else 0,
            "max_duration_ms": round(max(durations), 3) if durations else 0,
            "avg_memory_mb": round(sum(memories) / len(memories), 3) if memories else 0,
            "total_duration_ms": round(sum(durations), 3)
        }
    
    def get_all_summaries(self) -> list:
        """获取所有模块性能摘要"""
        return [self.get_summary(module) for module in self.results.keys()]
    
    def export_json(self) -> str:
        """导出为 JSON 格式"""
        data = {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "config": BENCHMARK_CONFIG,
            "results": self.results,
            "summaries": self.get_all_summaries()
        }
        return json.dumps(data, indent=2)
    
    def print_report(self):
        """打印性能报告"""
        print("\n" + "=" * 80)
        print("PERFORMANCE BENCHMARK REPORT")
        print("=" * 80)
        
        for summary in self.get_all_summaries():
            print(f"\n📊 {summary['module']}")
            print(f"   Operations: {summary['operations']}")
            print(f"   Avg Duration: {summary['avg_duration_ms']} ms")
            print(f"   Min Duration: {summary['min_duration_ms']} ms")
            print(f"   Max Duration: {summary['max_duration_ms']} ms")
            print(f"   Total Duration: {summary['total_duration_ms']} ms")
            if summary['avg_memory_mb'] > 0:
                print(f"   Avg Memory: {summary['avg_memory_mb']} MB")
        
        print("\n" + "=" * 80)


# ============================================================================
# 性能测试类
# ============================================================================

class TestPerformanceBaseline:
    """性能基准测试"""
    
    @pytest.fixture
    def report(self):
        """创建性能报告生成器"""
        return PerformanceReport()
    
    @pytest.fixture
    def mock_psd(self):
        """创建 Mock PSD"""
        return create_large_psd_document(50)
    
    # Level 1 Performance Tests
    def test_level1_page_extraction_performance(self, mock_psd, report):
        """Level 1 - 页面提取性能测试"""
        extractor = PageExtractor()
        
        for _ in range(BENCHMARK_CONFIG["warmup_runs"]):
            extractor.extract(mock_psd)
        
        gc.collect()
        tracemalloc.start()
        
        durations = []
        for _ in range(BENCHMARK_CONFIG["iterations"]):
            start = time.time()
            result = extractor.extract(mock_psd)
            durations.append(time.time() - start)
            assert result.success is True
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        avg_duration = sum(durations) / len(durations)
        memory_mb = peak / (1024 * 1024)
        
        report.add_result("Level1_PageExtractor", "extract", avg_duration, memory_mb)
        
        # 性能断言
        assert avg_duration < 0.1, f"Page extraction too slow: {avg_duration * 1000:.2f}ms"
        print(f"\nLevel 1 - Page Extraction: {avg_duration * 1000:.3f}ms, Memory: {memory_mb:.3f}MB")
    
    def test_level1_layer_reading_performance(self, mock_psd, report):
        """Level 1 - 图层读取性能测试"""
        reader = LayerReader()
        
        durations = []
        for _ in range(BENCHMARK_CONFIG["iterations"]):
            start = time.time()
            result = reader.read(mock_psd)
            durations.append(time.time() - start)
            assert result.success is True
        
        avg_duration = sum(durations) / len(durations)
        report.add_result("Level1_LayerReader", "read", avg_duration)
        
        assert avg_duration < 0.1, f"Layer reading too slow: {avg_duration * 1000:.2f}ms"
        print(f"\nLevel 1 - Layer Reading: {avg_duration * 1000:.3f}ms")
    
    def test_level1_hierarchy_build_performance(self, mock_psd, report):
        """Level 1 - 层级构建性能测试"""
        layers = mock_psd.pages[0].layers
        builder = HierarchyBuilder(layers)
        
        durations = []
        for _ in range(BENCHMARK_CONFIG["iterations"]):
            start = time.time()
            tree = builder.build()
            durations.append(time.time() - start)
        
        avg_duration = sum(durations) / len(durations)
        report.add_result("Level1_HierarchyBuilder", "build", avg_duration)
        
        assert avg_duration < 0.05, f"Hierarchy build too slow: {avg_duration * 1000:.2f}ms"
        print(f"\nLevel 1 - Hierarchy Build: {avg_duration * 1000:.3f}ms")


class TestLevel2Performance:
    """Level 2 - 分类层性能测试"""
    
    @pytest.fixture
    def mock_layers(self):
        """创建 Mock 图层列表"""
        return create_large_psd_document(50).pages[0].layers
    
    def test_classification_performance(self, mock_layers, report):
        """分类性能测试"""
        classifier = LayerClassifier(mock_mode=True)
        
        durations = []
        for _ in range(BENCHMARK_CONFIG["iterations"]):
            start = time.time()
            result = classifier.classify_batch(mock_layers)
            durations.append(time.time() - start)
            assert result.success is True
        
        avg_duration = sum(durations) / len(durations)
        report.add_result("Level2_Classifier", "classify_batch", avg_duration)
        
        assert avg_duration < 0.5, f"Classification too slow: {avg_duration * 1000:.2f}ms"
        print(f"\nLevel 2 - Classification: {avg_duration * 1000:.3f}ms for {len(mock_layers)} layers")


class TestLevel3Performance:
    """Level 3 - 识别层性能测试"""
    
    @pytest.fixture
    def mock_layers(self):
        """创建 Mock 图层列表"""
        return create_large_psd_document(50).pages[0].layers
    
    def test_recognition_performance(self, mock_layers, report):
        """识别性能测试"""
        recognizer = Recognizer(mock_mode=True)
        
        durations = []
        for _ in range(BENCHMARK_CONFIG["iterations"]):
            start = time.time()
            result = recognizer.recognize_batch(mock_layers)
            durations.append(time.time() - start)
            assert result.success is True
        
        avg_duration = sum(durations) / len(durations)
        report.add_result("Level3_Recognizer", "recognize_batch", avg_duration)
        
        assert avg_duration < 1.0, f"Recognition too slow: {avg_duration * 1000:.2f}ms"
        print(f"\nLevel 3 - Recognition: {avg_duration * 1000:.3f}ms for {len(mock_layers)} layers")


class TestLevel4Performance:
    """Level 4 - 策略层性能测试"""
    
    def test_strategy_selection_performance(self, report):
        """策略选择性能测试"""
        selector = StrategySelector(mock_mode=True)
        
        context = {
            "total_components": 50,
            "has_overlaps": False,
            "canvas_width": 1920,
            "canvas_height": 1080
        }
        
        durations = []
        for _ in range(BENCHMARK_CONFIG["iterations"]):
            start = time.time()
            result = selector.select(context)
            durations.append(time.time() - start)
            assert result.success is True
        
        avg_duration = sum(durations) / len(durations)
        report.add_result("Level4_StrategySelector", "select", avg_duration)
        
        assert avg_duration < 0.1, f"Strategy selection too slow: {avg_duration * 1000:.2f}ms"
        print(f"\nLevel 4 - Strategy Selection: {avg_duration * 1000:.3f}ms")


class TestLevel5Performance:
    """Level 5 - 导出层性能测试"""
    
    def test_export_performance(self, tmp_path, report):
        """导出性能测试"""
        output_dir = tmp_path / "perf_output"
        output_dir.mkdir()
        
        exporter = Exporter(
            output_dir=str(output_dir),
            naming_template="{type}/{name}",
            mock_mode=True
        )
        
        plan = ExportCutPlan(
            strategy="FLAT",
            components=[
                {
                    "name": f"component_{i}",
                    "type": "button",
                    "layer_data": b"x" * 1000,
                    "position": (i * 10, i * 10)
                }
                for i in range(10)
            ],
            canvas_width=1920,
            canvas_height=1080
        )
        
        durations = []
        for _ in range(BENCHMARK_CONFIG["iterations"] // 10):
            start = time.time()
            result = exporter.export(plan)
            durations.append(time.time() - start)
            assert result.success is True
        
        avg_duration = sum(durations) / len(durations)
        report.add_result("Level5_Exporter", "export", avg_duration)
        
        assert avg_duration < 1.0, f"Export too slow: {avg_duration * 1000:.2f}ms"
        print(f"\nLevel 5 - Export: {avg_duration * 1000:.3f}ms")


class TestLevel6Performance:
    """Level 6 - 提取层性能测试"""
    
    def test_extraction_performance(self, report):
        """提取性能测试"""
        extractor = Extractor(mock_mode=True)
        
        layer_data = {
            "id": "perf_test",
            "name": "Performance Test Layer",
            "kind": "text",
            "text": "Sample text for performance testing",
            "font_family": "Arial",
            "font_size": 16,
            "opacity": 1.0,
            "blend_mode": "normal",
            "left": 0,
            "top": 0,
            "right": 200,
            "bottom": 50
        }
        
        durations = []
        for _ in range(BENCHMARK_CONFIG["iterations"]):
            start = time.time()
            result = extractor.extract(layer_data)
            durations.append(time.time() - start)
            assert result.success is True
        
        avg_duration = sum(durations) / len(durations)
        report.add_result("Level6_Extractor", "extract", avg_duration)
        
        assert avg_duration < 0.05, f"Extraction too slow: {avg_duration * 1000:.2f}ms"
        print(f"\nLevel 6 - Extraction: {avg_duration * 1000:.3f}ms")


class TestLevel7Performance:
    """Level 7 - 生成层性能测试"""
    
    def test_spec_generation_performance(self, report):
        """规格生成性能测试"""
        generator = SpecGenerator(mock_mode=True)
        
        spec = ComponentSpec(
            id="perf_test",
            name="Performance Test Component",
            type="button",
            dimensions={"width": 100, "height": 50},
            position={"x": 10, "y": 20},
            style={"background": "#FF5733"}
        )
        
        durations = []
        for _ in range(BENCHMARK_CONFIG["iterations"]):
            start = time.time()
            result = generator.generate(spec)
            durations.append(time.time() - start)
            assert result.success is True
        
        avg_duration = sum(durations) / len(durations)
        report.add_result("Level7_SpecGenerator", "generate", avg_duration)
        
        assert avg_duration < 0.05, f"Spec generation too slow: {avg_duration * 1000:.2f}ms"
        print(f"\nLevel 7 - Spec Generation: {avg_duration * 1000:.3f}ms")
    
    def test_batch_spec_generation_performance(self, report):
        """批量规格生成性能测试"""
        generator = SpecGenerator(mock_mode=True)
        
        specs = [
            ComponentSpec(
                id=f"batch_{i}",
                name=f"Batch Component {i}",
                type="button",
                dimensions={"width": 100, "height": 50},
                position={"x": i * 10, "y": 0},
                style={}
            )
            for i in range(50)
        ]
        
        durations = []
        for _ in range(BENCHMARK_CONFIG["iterations"] // 5):
            start = time.time()
            results = generator.generate_batch(specs)
            durations.append(time.time() - start)
            assert len(results) == 50
        
        avg_duration = sum(durations) / len(durations)
        report.add_result("Level7_SpecGenerator", "generate_batch_50", avg_duration)
        
        assert avg_duration < 0.5, f"Batch generation too slow: {avg_duration * 1000:.2f}ms"
        print(f"\nLevel 7 - Batch Spec Generation (50): {avg_duration * 1000:.3f}ms")


class TestLevel8Performance:
    """Level 8 - 文档层性能测试"""
    
    def test_readme_generation_performance(self, report):
        """README 生成性能测试"""
        generator = ReadmeGenerator(mock_mode=True)
        
        durations = []
        for _ in range(BENCHMARK_CONFIG["iterations"] // 10):
            start = time.time()
            content = generator.generate()
            durations.append(time.time() - start)
            assert len(content) > 0
        
        avg_duration = sum(durations) / len(durations)
        report.add_result("Level8_ReadmeGenerator", "generate", avg_duration)
        
        assert avg_duration < 0.5, f"README generation too slow: {avg_duration * 1000:.2f}ms"
        print(f"\nLevel 8 - README Generation: {avg_duration * 1000:.3f}ms")
    
    def test_manifest_generation_performance(self, report):
        """Manifest 生成性能测试"""
        generator = ManifestGenerator(mock_mode=True)
        
        durations = []
        for _ in range(BENCHMARK_CONFIG["iterations"] // 10):
            start = time.time()
            manifest = generator.generate()
            durations.append(time.time() - start)
            assert manifest is not None
        
        avg_duration = sum(durations) / len(durations)
        report.add_result("Level8_ManifestGenerator", "generate", avg_duration)
        
        assert avg_duration < 0.2, f"Manifest generation too slow: {avg_duration * 1000:.2f}ms"
        print(f"\nLevel 8 - Manifest Generation: {avg_duration * 1000:.3f}ms")
    
    def test_preview_generation_performance(self, report):
        """Preview HTML 生成性能测试"""
        generator = PreviewGenerator(mock_mode=True)
        
        durations = []
        for _ in range(BENCHMARK_CONFIG["iterations"] // 20):
            start = time.time()
            html = generator.generate()
            durations.append(time.time() - start)
            assert html is not None
        
        avg_duration = sum(durations) / len(durations)
        report.add_result("Level8_PreviewGenerator", "generate", avg_duration)
        
        assert avg_duration < 1.0, f"Preview generation too slow: {avg_duration * 1000:.2f}ms"
        print(f"\nLevel 8 - Preview Generation: {avg_duration * 1000:.3f}ms")


class TestMemoryUsage:
    """内存使用测试"""
    
    def test_memory_usage_large_psd(self):
        """大型 PSD 内存使用测试"""
        gc.collect()
        tracemalloc.start()
        
        # 创建大型 PSD
        doc = create_large_psd_document(200)
        
        # 执行操作
        layers = doc.pages[0].layers
        classifier = LayerClassifier(mock_mode=True)
        result = classifier.classify_batch(layers)
        
        assert result.success is True
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        peak_mb = peak / (1024 * 1024)
        print(f"\nMemory Usage (200 layers): Current={current / (1024 * 1024):.3f}MB, Peak={peak_mb:.3f}MB")
        
        # 内存峰值应该小于 100MB
        assert peak_mb < 100, f"Memory usage too high: {peak_mb:.2f}MB"
    
    def test_memory_leak_detection(self):
        """内存泄漏检测"""
        gc.collect()
        tracemalloc.start()
        
        classifier = LayerClassifier(mock_mode=True)
        layers = create_large_psd_document(50).pages[0].layers
        
        # 执行多次操作
        for _ in range(10):
            result = classifier.classify_batch(layers)
            assert result.success is True
        
        gc.collect()
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        current_mb = current / (1024 * 1024)
        peak_mb = peak / (1024 * 1024)
        
        print(f"\nMemory Leak Test: Current={current_mb:.3f}MB, Peak={peak_mb:.3f}MB")
        
        # 当前内存应该接近初始状态（允许一些增长）
        assert current_mb < 50, f"Potential memory leak: {current_mb:.2f}MB"


class TestBatchProcessingCapacity:
    """批量处理能力测试"""
    
    @pytest.mark.parametrize("batch_size", [1, 10, 50, 100])
    def test_batch_processing_capacity(self, batch_size):
        """批量处理能力测试"""
        layers = create_large_psd_document(batch_size).pages[0].layers
        
        classifier = LayerClassifier(mock_mode=True)
        
        start = time.time()
        result = classifier.classify_batch(layers)
        elapsed = time.time() - start
        
        assert result.success is True
        assert result.total == batch_size
        
        print(f"\nBatch Processing ({batch_size} layers): {elapsed * 1000:.3f}ms")
        
        # 性能应该接近线性
        expected_max = batch_size * 0.01  # 每层 10ms 基准
        assert elapsed < expected_max, f"Batch processing too slow: {elapsed:.3f}s for {batch_size} layers"
    
    @pytest.mark.parametrize("batch_size", [10, 50])
    def test_batch_recognition_capacity(self, batch_size):
        """批量识别能力测试"""
        layers = create_large_psd_document(batch_size).pages[0].layers
        
        recognizer = Recognizer(mock_mode=True)
        
        start = time.time()
        result = recognizer.recognize_batch(layers)
        elapsed = time.time() - start
        
        assert result.success is True
        
        print(f"\nBatch Recognition ({batch_size} layers): {elapsed * 1000:.3f}ms")


class TestScalability:
    """可扩展性测试"""
    
    def test_layer_count_scaling(self):
        """图层数量扩展测试"""
        sizes = [10, 50, 100]
        times = []
        
        for size in sizes:
            layers = create_large_psd_document(size).pages[0].layers
            classifier = LayerClassifier(mock_mode=True)
            
            start = time.time()
            result = classifier.classify_batch(layers)
            elapsed = time.time() - start
            
            assert result.success is True
            times.append(elapsed)
            
            print(f"Size {size}: {elapsed * 1000:.3f}ms")
        
        # 验证扩展性：时间增长应该接近线性
        # 50 -> 100 应该小于 3x 增长
        ratio = times[2] / times[1] if times[1] > 0 else 1
        assert ratio < 3.0, f"Scaling issue detected: {ratio:.2f}x time increase from 50 to 100 layers"


# ============================================================================
# 性能报告测试
# ============================================================================

class TestPerformanceReport:
    """性能报告测试"""
    
    def test_report_generation(self):
        """测试报告生成"""
        report = PerformanceReport()
        
        report.add_result("TestModule", "test_op", 0.1, 10.5)
        report.add_result("TestModule", "test_op", 0.15, 11.0)
        report.add_result("AnotherModule", "another_op", 0.2, 5.0)
        
        summary = report.get_summary("TestModule")
        assert summary["module"] == "TestModule"
        assert summary["operations"] == 2
        assert summary["avg_duration_ms"] == 125.0  # (100 + 150) / 2
        
        summaries = report.get_all_summaries()
        assert len(summaries) == 2
    
    def test_report_json_export(self):
        """测试报告 JSON 导出"""
        report = PerformanceReport()
        report.add_result("Module1", "op1", 0.1)
        
        json_str = report.export_json()
        data = json.loads(json_str)
        
        assert "generated_at" in data
        assert "results" in data
        assert "Module1" in data["results"]
    
    def test_report_print(self, capsys):
        """测试报告打印"""
        report = PerformanceReport()
        report.add_result("PrintTest", "print_op", 0.05)
        
        report.print_report()
        
        captured = capsys.readouterr()
        assert "PERFORMANCE BENCHMARK REPORT" in captured.out
        assert "PrintTest" in captured.out


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
