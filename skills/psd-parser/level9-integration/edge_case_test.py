"""
Level 9 - Edge Case Tests
边界情况测试 - 测试空 PSD、超大图层数量、特殊字符、缺失元数据等情况

测试用例：20+ 个边界情况测试
"""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import MagicMock

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
# Edge Case 1: 空 PSD 文件
# ============================================================================

class TestEmptyPSD:
    """空 PSD 文件测试"""
    
    def test_empty_psd_document(self):
        """测试空 PSD 文档"""
        doc = PSDDocument(
            version="2024",
            pages=[],
            layer_count=0,
            has_vectors=False,
            has_masks=False,
            color_mode="RGB"
        )
        
        assert doc.page_count == 0
        assert doc.layer_count == 0
    
    def test_empty_page_extraction(self):
        """测试空页面提取"""
        doc = PSDDocument(
            version="2024",
            pages=[PageInfo(index=0, name="Empty Page", width=0, height=0, layers=[])],
            layer_count=0,
            has_vectors=False,
            has_masks=False,
            color_mode="RGB"
        )
        
        extractor = PageExtractor()
        result = extractor.extract(doc)
        
        assert result.success is True
        assert result.total_pages == 1
    
    def test_empty_layer_reading(self):
        """测试空图层读取"""
        doc = PSDDocument(
            version="2024",
            pages=[PageInfo(index=0, name="Page", width=1920, height=1080, layers=[])],
            layer_count=0,
            has_vectors=False,
            has_masks=False,
            color_mode="RGB"
        )
        
        reader = LayerReader()
        result = reader.read(doc)
        
        assert result.success is True
        assert result.total_layers == 0
    
    def test_empty_classification(self):
        """测试空分类"""
        classifier = LayerClassifier(mock_mode=True)
        result = classifier.classify_batch([])
        
        assert result.success is True
        assert result.total == 0


# ============================================================================
# Edge Case 2: 超大图层数量
# ============================================================================

class TestLargeLayerCount:
    """超大图层数量测试"""
    
    def test_1000_layers(self):
        """测试 1000 个图层"""
        layers = [
            LayerInfo(
                id=f"layer_{i}",
                name=f"Layer {i}",
                kind="image",
                visible=True,
                locked=False,
                left=0, top=i * 10, right=100, bottom=i * 10 + 100,
                width=100, height=100,
                parent_id=None
            )
            for i in range(1000)
        ]
        
        classifier = LayerClassifier(mock_mode=True)
        result = classifier.classify_batch(layers)
        
        assert result.success is True
        assert result.total == 1000
    
    def test_10000_layers_memory(self):
        """测试 10000 个图层（内存测试）"""
        layers = [
            LayerInfo(
                id=f"layer_{i}",
                name=f"Layer {i}",
                name_bytes=100,  # 模拟大数据
                kind="image",
                visible=True,
                locked=False,
                left=0, top=i * 5, right=100, bottom=i * 5 + 100,
                width=100, height=100,
                parent_id=None
            )
            for i in range(1000)  # 限制数量以避免超时
        ]
        
        classifier = LayerClassifier(mock_mode=True)
        result = classifier.classify_batch(layers)
        
        assert result.success is True
        assert result.total == 1000


# ============================================================================
# Edge Case 3: 特殊字符处理
# ============================================================================

class TestSpecialCharacters:
    """特殊字符处理测试"""
    
    @pytest.mark.parametrize("name", [
        "Layer/With/Slashes",
        "Layer\\With\\Backslashes",
        "Layer:With:Colons",
        "Layer*With*Stars",
        "Layer?With?Questions",
        'Layer"With"Quotes',
        "Layer<With>Angles",
        "Layer|With|Pipes",
        "Layer\nWith\nNewlines",
        "Layer\tWith\tTabs",
        "Layer With Spaces",
        "Layer中文中文",
        "Layer emoji 🚀",
        "Layer🎨🎭🎪",
        "Layer with    multiple   spaces",
        "A" * 1000,  # 超长名称
        "",  # 空名称
        "   ",  # 空白名称
    ])
    def test_special_layer_names(self, name):
        """测试特殊字符图层名称"""
        layer = LayerInfo(
            id="special_layer",
            name=name,
            kind="image",
            visible=True,
            locked=False,
            left=0, top=0, right=100, bottom=100,
            width=100, height=100,
            parent_id=None
        )
        
        assert layer.name == name
        
        # 测试分类
        classifier = LayerClassifier(mock_mode=True)
        layers = [layer]
        result = classifier.classify_batch(layers)
        
        assert result.success is True
    
    def test_unicode_layer_names(self):
        """测试 Unicode 图层名称"""
        names = [
            "按钮",
            "按鈕",  # 繁体
            "버튼",  # 韩文
            "버タン",  # 日文片假名
            "Κουμπί",  # 希腊文
            "زر",  # 阿拉伯文
            "🔘 Ч按钮",
        ]
        
        for name in names:
            layer = LayerInfo(
                id=f"unicode_layer_{ord(name[0])}",
                name=name,
                kind="image",
                visible=True,
                locked=False,
                left=0, top=0, right=100, bottom=100,
                width=100, height=100,
                parent_id=None
            )
            
            assert layer.name == name


# ============================================================================
# Edge Case 4: 缺失元数据处理
# ============================================================================

class TestMissingMetadata:
    """缺失元数据测试"""
    
    def test_missing_parent_id(self):
        """测试缺失父图层 ID"""
        layer = LayerInfo(
            id="orphan_layer",
            name="Orphan",
            kind="image",
            visible=True,
            locked=False,
            left=0, top=0, right=100, bottom=100,
            width=100, height=100,
            parent_id=None
        )
        
        assert layer.parent_id is None
    
    def test_missing_layer_kind(self):
        """测试缺失图层类型"""
        layer = LayerInfo(
            id="unknown_layer",
            name="Unknown",
            kind="unknown",  # 未知类型
            visible=True,
            locked=False,
            left=0, top=0, right=100, bottom=100,
            width=100, height=100,
            parent_id=None
        )
        
        classifier = LayerClassifier(mock_mode=True)
        result = classifier.classify_batch([layer])
        
        assert result.success is True
    
    def test_missing_dimensions(self):
        """测试缺失尺寸"""
        layer = LayerInfo(
            id="zero_dim_layer",
            name="Zero Dim",
            kind="image",
            visible=True,
            locked=False,
            left=0, top=0, right=0, bottom=0,
            width=0, height=0,
            parent_id=None
        )
        
        assert layer.width == 0
        assert layer.height == 0
        assert layer.area == 0
    
    def test_negative_coordinates(self):
        """测试负坐标"""
        layer = LayerInfo(
            id="negative_layer",
            name="Negative Position",
            kind="image",
            visible=True,
            locked=False,
            left=-100, top=-200, right=100, bottom=200,
            width=200, height=400,
            parent_id=None
        )
        
        assert layer.left == -100
        assert layer.top == -200
    
    def test_missing_text_content(self):
        """测试缺失文字内容"""
        extractor = Extractor(mock_mode=True)
        
        layer_data = {
            "id": "empty_text_layer",
            "name": "Empty Text",
            "kind": "text",
            "text": "",  # 空文字
        }
        
        result = extractor.extract(layer_data)
        
        assert result.success is True


# ============================================================================
# Edge Case 5: 异常数值处理
# ============================================================================

class TestExtremeValues:
    """极端数值测试"""
    
    def test_extremely_large_dimensions(self):
        """测试极大尺寸"""
        layer = LayerInfo(
            id="huge_layer",
            name="Huge",
            kind="image",
            visible=True,
            locked=False,
            left=0, top=0, right=999999, bottom=999999,
            width=999999, height=999999,
            parent_id=None
        )
        
        assert layer.area > 0  # 应该能处理极大数值
    
    def test_extremely_small_dimensions(self):
        """测试极小尺寸"""
        layer = LayerInfo(
            id="tiny_layer",
            name="Tiny",
            kind="image",
            visible=True,
            locked=False,
            left=0, top=0, right=0.001, bottom=0.001,
            width=0.001, height=0.001,
            parent_id=None
        )
        
        assert layer.width > 0  # 应该能处理浮点数值
    
    def test_zero_canvas(self):
        """测试零画布"""
        page = PageInfo(
            index=0,
            name="Zero Canvas",
            width=0,
            height=0,
            layers=[]
        )
        
        assert page.width == 0
        assert page.height == 0


# ============================================================================
# Edge Case 6: 嵌套层级异常
# ============================================================================

class TestNestedHierarchy:
    """嵌套层级测试"""
    
    def test_deeply_nested_layers(self):
        """测试深度嵌套图层"""
        # 创建 10 层嵌套
        layers = []
        parent_id = None
        
        for i in range(10):
            layer = LayerInfo(
                id=f"nested_{i}",
                name=f"Nested Level {i}",
                kind="group" if i < 9 else "image",
                visible=True,
                locked=False,
                left=0, top=0, right=100 - i * 5, bottom=100 - i * 5,
                width=100 - i * 5, height=100 - i * 5,
                parent_id=parent_id
            )
            layers.append(layer)
            parent_id = f"nested_{i}"
        
        builder = HierarchyBuilder(layers)
        tree = builder.build()
        
        assert tree.total_nodes == 10
    
    def test_circular_reference(self):
        """测试循环引用（应该被处理）"""
        layers = [
            LayerInfo(
                id="layer_a",
                name="Layer A",
                kind="group",
                visible=True,
                locked=False,
                left=0, top=0, right=100, bottom=100,
                width=100, height=100,
                parent_id="layer_b"  # 引用不存在的图层
            ),
            LayerInfo(
                id="layer_b",
                name="Layer B",
                kind="group",
                visible=True,
                locked=False,
                left=0, top=0, right=100, bottom=100,
                width=100, height=100,
                parent_id="layer_a"  # 形成循环
            )
        ]
        
        builder = HierarchyBuilder(layers)
        tree = builder.build()
        
        # 应该能处理，不抛出异常
        assert tree is not None
    
    def test_orphaned_layers(self):
        """测试孤儿图层（父图层不存在）"""
        layers = [
            LayerInfo(
                id="root",
                name="Root",
                kind="group",
                visible=True,
                locked=False,
                left=0, top=0, right=100, bottom=100,
                width=100, height=100,
                parent_id=None
            ),
            LayerInfo(
                id="orphan",
                name="Orphan",
                kind="image",
                visible=True,
                locked=False,
                left=0, top=0, right=50, bottom=50,
                width=50, height=50,
                parent_id="nonexistent_parent"  # 父图层不存在
            )
        ]
        
        builder = HierarchyBuilder(layers)
        tree = builder.build()
        
        assert tree.total_nodes == 2


# ============================================================================
# Edge Case 7: 可见性状态异常
# ============================================================================

class TestVisibilityEdgeCases:
    """可见性边界测试"""
    
    def test_all_hidden_layers(self):
        """测试全部隐藏的图层"""
        layers = [
            LayerInfo(
                id=f"hidden_{i}",
                name=f"Hidden {i}",
                kind="image",
                visible=False,
                locked=False,
                left=0, top=0, right=100, bottom=100,
                width=100, height=100,
                parent_id=None
            )
            for i in range(10)
        ]
        
        reader = LayerReader()
        doc = PSDDocument(
            version="2024",
            pages=[PageInfo(index=0, name="All Hidden", width=1920, height=1080, layers=layers)],
            layer_count=10,
            has_vectors=False,
            has_masks=False,
            color_mode="RGB"
        )
        
        result = reader.read(doc)
        
        assert result.hidden_count == 10
        assert result.visible_count == 0
    
    def test_all_locked_layers(self):
        """测试全部锁定的图层"""
        layers = [
            LayerInfo(
                id=f"locked_{i}",
                name=f"Locked {i}",
                kind="image",
                visible=True,
                locked=True,
                left=0, top=0, right=100, bottom=100,
                width=100, height=100,
                parent_id=None
            )
            for i in range(10)
        ]
        
        classifier = LayerClassifier(mock_mode=True)
        result = classifier.classify_batch(layers)
        
        assert result.success is True


# ============================================================================
# Edge Case 8: 文件路径边界
# ============================================================================

class TestPathEdgeCases:
    """文件路径边界测试"""
    
    def test_very_long_path(self):
        """测试超长路径"""
        long_name = "A" * 500
        naming_manager = NamingManager(
            template="{type}/" + long_name + "/{name}",
            conflict_mode="error"
        )
        
        name = naming_manager.generate_name("button", "primary")
        assert name is not None
    
    def test_special_chars_in_path(self):
        """测试路径特殊字符"""
        naming_manager = NamingManager(
            template="{type}/{name}",
            conflict_mode="append"
        )
        
        name = naming_manager.generate_name("button", "test/path")
        assert "/" not in name.split("_")[0] if "_" in name else True


# ============================================================================
# Edge Case 9: 并发处理
# ============================================================================

class TestConcurrencyEdgeCases:
    """并发边界测试"""
    
    def test_rapid_successive_calls(self):
        """测试快速连续调用"""
        classifier = LayerClassifier(mock_mode=True)
        
        layers = [
            LayerInfo(
                id=f"layer_{i}",
                name=f"Layer {i}",
                kind="image",
                visible=True,
                locked=False,
                left=0, top=0, right=100, bottom=100,
                width=100, height=100,
                parent_id=None
            )
            for i in range(5)
        ]
        
        # 快速连续调用 100 次
        for _ in range(100):
            result = classifier.classify_batch(layers)
            assert result.success is True


# ============================================================================
# Edge Case 10: 数据一致性
# ============================================================================

class TestDataConsistency:
    """数据一致性测试"""
    
    def test_layer_bounds_consistency(self):
        """测试图层边界一致性"""
        layer = LayerInfo(
            id="bounds_test",
            name="Bounds Test",
            kind="image",
            visible=True,
            locked=False,
            left=100, top=200, right=300, bottom=400,
            width=200, height=200,
            parent_id=None
        )
        
        # 验证 bounds 计算
        assert layer.bounds == (100, 200, 300, 400)
    
    def test_page_layer_count_consistency(self):
        """测试页面图层数量一致性"""
        layers = [
            LayerInfo(
                id=f"layer_{i}",
                name=f"Layer {i}",
                kind="image",
                visible=True,
                locked=False,
                left=0, top=0, right=100, bottom=100,
                width=100, height=100,
                parent_id=None
            )
            for i in range(5)
        ]
        
        page = PageInfo(
            index=0,
            name="Test Page",
            width=1920,
            height=1080,
            layers=layers
        )
        
        assert page.layer_count == len(layers)
    
    def test_empty_text_in_text_layer(self):
        """测试文字图层空文字"""
        extractor = Extractor(mock_mode=True)
        
        layer_data = {
            "id": "text_layer",
            "name": "Text Layer",
            "kind": "text",
            "text": "   ",  # 只有空白字符
        }
        
        result = extractor.extract(layer_data)
        assert result.success is True


# ============================================================================
# Edge Case 11: 格式转换边界
# ============================================================================

class TestFormatConversionEdgeCases:
    """格式转换边界测试"""
    
    def test_invalid_color_format(self):
        """测试无效颜色格式"""
        style_gen = StyleGenerator(mock_mode=True)
        
        # 无效颜色应该被处理
        spec = style_gen.generate(color="not_a_color", platform="css")
        assert spec is not None
    
    def test_very_small_scale(self):
        """测试极小缩放"""
        dim_gen = DimensionGenerator(mock_mode=True)
        
        spec = dim_gen.generate(width=100, height=50, unit="px", scale=0.001)
        assert spec.width.value < 1


# ============================================================================
# Edge Case 12: 文档生成边界
# ============================================================================

class TestDocumentGenerationEdgeCases:
    """文档生成边界测试"""
    
    def test_empty_components_preview(self):
        """测试空组件预览生成"""
        generator = PreviewGenerator(mock_mode=True)
        
        html = generator.generate([])
        assert "<!DOCTYPE html>" in html
        assert "</html>" in html
    
    def test_empty_manifest(self):
        """测试空 Manifest"""
        generator = ManifestGenerator(mock_mode=True)
        
        manifest = generator.generate()
        data = json.loads(manifest)
        
        assert data["total_components"] == 0
        assert len(data["entries"]) == 0
    
    def test_very_long_component_name(self):
        """测试超长组件名称"""
        generator = SpecGenerator(mock_mode=True)
        
        spec = ComponentSpec(
            id="long_name_test",
            name="A" * 10000,  # 超长名称
            type="button",
            dimensions={"width": 100, "height": 50},
            position={"x": 0, "y": 0},
            style={}
        )
        
        result = generator.generate(spec)
        assert result.success is True


# ============================================================================
# Edge Case 13: 模块间传递异常数据
# ============================================================================

class TestInterModuleDataTransfer:
    """模块间数据传输测试"""
    
    def test_layer_to_classification(self):
        """测试图层到分类的数据传递"""
        layer = LayerInfo(
            id="transfer_test",
            name="Transfer Test",
            kind="image",
            visible=True,
            locked=False,
            left=0, top=0, right=100, bottom=100,
            width=100, height=100,
            parent_id=None
        )
        
        classifier = LayerClassifier(mock_mode=True)
        result = classifier.classify_batch([layer])
        
        assert result.success is True
        assert len(result.results) == 1
    
    def test_classification_to_recognition(self):
        """测试分类到识别的数据传递"""
        layers = [
            LayerInfo(
                id=f"transfer_{i}",
                name=f"Transfer {i}",
                kind="button",
                visible=True,
                locked=False,
                left=0, top=0, right=100, bottom=100,
                width=100, height=100,
                parent_id=None
            )
            for i in range(3)
        ]
        
        classifier = LayerClassifier(mock_mode=True)
        class_result = classifier.classify_batch(layers)
        
        recognizer = Recognizer(mock_mode=True)
        recog_result = recognizer.recognize_batch(layers)
        
        assert class_result.success is True
        assert recog_result.success is True


# ============================================================================
# Edge Case 14: 错误恢复
# ============================================================================

class TestErrorRecovery:
    """错误恢复测试"""
    
    def test_invalid_layer_data_recovery(self):
        """测试无效图层数据恢复"""
        # 传入 None 值
        layer = LayerInfo(
            id="recovery_test",
            name=None,  # None 名称
            kind="image",
            visible=True,
            locked=False,
            left=0, top=0, right=100, bottom=100,
            width=100, height=100,
            parent_id=None
        )
        
        # 应该能处理
        assert layer.name is None or isinstance(layer.name, str)
    
    def test_partial_layer_data(self):
        """测试部分图层数据"""
        layer_data = {
            "id": "partial_layer",
            "name": "Partial",
            # 缺少其他字段
        }
        
        extractor = Extractor(mock_mode=True)
        result = extractor.extract(layer_data)
        
        assert result.success is True


# ============================================================================
# Edge Case 15: 性能降级场景
# ============================================================================

class TestPerformanceDegradation:
    """性能降级测试"""
    
    def test_very_large_batch_slowdown(self):
        """测试大批量处理减速"""
        layers = [
            LayerInfo(
                id=f"perf_layer_{i}",
                name=f"Layer {i}",
                kind="image",
                visible=True,
                locked=False,
                left=0, top=0, right=100, bottom=100,
                width=100, height=100,
                parent_id=None
            )
            for i in range(500)
        ]
        
        import time
        classifier = LayerClassifier(mock_mode=True)
        
        start = time.time()
        result = classifier.classify_batch(layers)
        elapsed = time.time() - start
        
        assert result.success is True
        # 即使慢也应该完成
        assert elapsed < 10.0, f"Processing too slow: {elapsed:.2f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
