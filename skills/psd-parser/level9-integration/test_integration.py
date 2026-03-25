"""
Level 9 - Integration Tests
端到端集成测试 - 验证 8 个 layer 模块的完整工作流

测试内容：
- Mock PSD 文件解析
- 各层模块串联测试（level1-8）
- 验证最终输出格式
"""

import pytest
import sys
import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from skills.psd_parser.level1_parse import (
    PSDDocument, PageInfo, LayerInfo,
    PSDParser, PageExtractor, LayerReader, HierarchyBuilder
)
from skills.psd_parser.level2_classify import (
    LayerType, ClassificationResult,
    LayerClassifier, ImageClassifier, TextClassifier
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
# Mock 数据生成器
# ============================================================================

def create_mock_psd_document():
    """创建 Mock PSD 文档"""
    layers = [
        LayerInfo(
            id="layer_0",
            name="Background",
            kind="image",
            visible=True,
            locked=False,
            left=0, top=0, right=1920, bottom=1080,
            width=1920, height=1080,
            parent_id=None
        ),
        LayerInfo(
            id="layer_1",
            name="Header Group",
            kind="group",
            visible=True,
            locked=False,
            left=0, top=0, right=1920, bottom=100,
            width=1920, height=100,
            parent_id=None
        ),
        LayerInfo(
            id="layer_2",
            name="Logo",
            kind="image",
            visible=True,
            locked=False,
            left=20, top=20, right=120, bottom=80,
            width=100, height=60,
            parent_id="layer_1"
        ),
        LayerInfo(
            id="layer_3",
            name="Navigation",
            kind="group",
            visible=True,
            locked=False,
            left=200, top=0, right=1920, bottom=100,
            width=1720, height=100,
            parent_id="layer_1"
        ),
        LayerInfo(
            id="layer_4",
            name="Nav Button 1",
            kind="button",
            visible=True,
            locked=False,
            left=200, top=30, right=300, bottom=70,
            width=100, height=40,
            parent_id="layer_3"
        ),
        LayerInfo(
            id="layer_5",
            name="Nav Button 2",
            kind="button",
            visible=True,
            locked=False,
            left=320, top=30, right=420, bottom=70,
            width=100, height=40,
            parent_id="layer_3"
        ),
        LayerInfo(
            id="layer_6",
            name="Content Section",
            kind="group",
            visible=True,
            locked=False,
            left=0, top=100, right=1920, bottom=1080,
            width=1920, height=980,
            parent_id=None
        ),
        LayerInfo(
            id="layer_7",
            name="Hero Text",
            kind="text",
            visible=True,
            locked=False,
            left=100, top=150, right=900, bottom=250,
            width=800, height=100,
            parent_id="layer_6"
        ),
        LayerInfo(
            id="layer_8",
            name="Hero Image",
            kind="image",
            visible=True,
            locked=False,
            left=1000, top=100, right=1800, bottom=600,
            width=800, height=500,
            parent_id="layer_6"
        ),
        LayerInfo(
            id="layer_9",
            name="CTA Button",
            kind="button",
            visible=True,
            locked=False,
            left=100, top=700, right=300, bottom=760,
            width=200, height=60,
            parent_id="layer_6"
        ),
        LayerInfo(
            id="layer_10",
            name="Hidden Layer",
            kind="image",
            visible=False,
            locked=False,
            left=0, top=0, right=100, bottom=100,
            width=100, height=100,
            parent_id=None
        ),
    ]
    
    pages = [
        PageInfo(
            index=0,
            name="Page 1",
            width=1920,
            height=1080,
            layers=layers
        )
    ]
    
    return PSDDocument(
        version="2024",
        pages=pages,
        layer_count=len(layers),
        has_vectors=False,
        has_masks=False,
        color_mode="RGB"
    )


def create_mock_recognition_results(layers):
    """创建 Mock 识别结果"""
    results = []
    for layer in layers:
        if layer.is_group or layer.is_hidden:
            continue
        
        result = RecognitionResult(
            layer_id=layer.id,
            component_type=layer.kind if layer.kind != "image" else "illustration",
            confidence=0.85,
            region={
                "left": layer.left,
                "top": layer.top,
                "right": layer.right,
                "bottom": layer.bottom
            },
            metadata={
                "name": layer.name,
                "parent_id": layer.parent_id
            }
        )
        results.append(result)
    return results


# ============================================================================
# Level 1 Tests - PSD 解析
# ============================================================================

class TestLevel1Integration:
    """Level 1 - PSD 解析层集成测试"""
    
    def test_parse_mock_psd(self):
        """测试解析 Mock PSD 文档"""
        doc = create_mock_psd_document()
        
        assert doc is not None
        assert doc.version == "2024"
        assert doc.page_count == 1
        assert doc.layer_count == 11
        assert doc.has_vectors is False
    
    def test_page_extraction(self):
        """测试页面提取"""
        doc = create_mock_psd_document()
        extractor = PageExtractor()
        
        result = extractor.extract(doc)
        
        assert result.success is True
        assert result.total_pages == 1
        assert len(result.pages) == 1
        assert result.pages[0].name == "Page 1"
    
    def test_layer_reading(self):
        """测试图层读取"""
        doc = create_mock_psd_document()
        reader = LayerReader()
        
        result = reader.read(doc)
        
        assert result.success is True
        assert result.total_layers == 11
        assert result.visible_count == 10
        assert result.hidden_count == 1
    
    def test_hierarchy_building(self):
        """测试层级树构建"""
        doc = create_mock_psd_document()
        layers = doc.pages[0].layers
        
        builder = HierarchyBuilder(layers)
        tree = builder.build()
        
        assert tree.total_nodes == 11
        assert len(tree.roots) == 4  # Background, Header Group, Content Section, Hidden Layer


# ============================================================================
# Level 2 Tests - 分类层
# ============================================================================

class TestLevel2Integration:
    """Level 2 - 分类层集成测试"""
    
    def test_layer_classification(self):
        """测试图层分类"""
        layers = create_mock_psd_document().pages[0].layers
        classifier = LayerClassifier(mock_mode=True)
        
        results = classifier.classify_batch(layers)
        
        assert results.success is True
        assert results.total == 11
        assert len(results.results) == 11
        
        # 验证分类结果
        type_counts = {}
        for result in results.results:
            layer_type = result.type.value
            type_counts[layer_type] = type_counts.get(layer_type, 0) + 1
        
        assert type_counts.get("group", 0) == 3  # Header Group, Navigation, Content Section
        assert type_counts.get("button", 0) == 3  # Nav Button 1, Nav Button 2, CTA Button
        assert type_counts.get("text", 0) == 1   # Hero Text
    
    def test_image_classification(self):
        """测试图片子类型分类"""
        classifier = ImageClassifier(mock_mode=True)
        
        result = classifier.classify("hero_banner_image")
        
        assert result.category == "image"
    
    def test_text_classification(self):
        """测试文字分类"""
        classifier = TextClassifier(mock_mode=True)
        
        result = classifier.classify("Hero Title Text")
        
        assert result.text_type.value in ["heading", "body", "label"]


# ============================================================================
# Level 3 Tests - 识别层
# ============================================================================

class TestLevel3Integration:
    """Level 3 - 识别层集成测试"""
    
    def test_recognizer_full_workflow(self):
        """测试识别器完整工作流"""
        layers = create_mock_psd_document().pages[0].layers
        
        recognizer = Recognizer(mock_mode=True)
        results = recognizer.recognize_batch(layers)
        
        assert results.success is True
        assert len(results.results) > 0
    
    def test_region_detection(self):
        """测试区域检测"""
        detector = RegionDetector(mock_mode=True)
        
        rect = {"left": 100, "top": 100, "right": 300, "bottom": 200}
        result = detector.detect(rect)
        
        assert result.success is True
        assert result.width == 200
        assert result.height == 100
    
    def test_component_naming(self):
        """测试组件命名"""
        namer = ComponentNamer(mock_mode=True)
        
        result = namer.name("primary_button_red", "button")
        
        assert result.success is True
        assert result.name is not None


# ============================================================================
# Level 4 Tests - 策略层
# ============================================================================

class TestLevel4Integration:
    """Level 4 - 策略层集成测试"""
    
    def test_strategy_selection(self):
        """测试策略选择"""
        selector = StrategySelector(mock_mode=True)
        
        context = {
            "total_components": 10,
            "has_overlaps": False,
            "canvas_width": 1920,
            "canvas_height": 1080
        }
        
        result = selector.select(context)
        
        assert result.success is True
        assert result.selected_strategy in [e.value for e in StrategyType]
    
    def test_overlap_detection(self):
        """测试重叠检测"""
        detector = OverlapDetector(mock_mode=True)
        
        layers = create_mock_psd_document().pages[0].layers
        
        result = detector.detect(layers)
        
        assert result.success is True
    
    def test_cut_plan_creation(self):
        """测试切割计划创建"""
        layers = create_mock_psd_document().pages[0].layers
        
        regions = [
            CutRegion(
                id="region_1",
                layer_id="layer_4",
                bounds={"left": 200, "top": 30, "right": 300, "bottom": 70},
                priority=1
            ),
            CutRegion(
                id="region_2",
                layer_id="layer_9",
                bounds={"left": 100, "top": 700, "right": 300, "bottom": 760},
                priority=1
            )
        ]
        
        plan = CutPlan(
            strategy=StrategyType.FLAT,
            regions=regions,
            canvas_width=1920,
            canvas_height=1080
        )
        
        assert len(plan.regions) == 2
        assert plan.canvas_width == 1920


# ============================================================================
# Level 5 Tests - 导出层
# ============================================================================

class TestLevel5Integration:
    """Level 5 - 导出层集成测试"""
    
    def test_export_cut_plan(self, tmp_path):
        """测试导出切割计划"""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        exporter = Exporter(
            output_dir=str(output_dir),
            naming_template="{type}/{name}",
            export_format="png",
            mock_mode=True
        )
        
        plan = ExportCutPlan(
            strategy="FLAT",
            components=[
                {
                    "name": "button_primary",
                    "type": "button",
                    "layer_data": b"mock_data",
                    "position": (100, 200)
                }
            ],
            canvas_width=1920,
            canvas_height=1080
        )
        
        report = exporter.export(plan)
        
        assert report.success is True
        assert report.total == 1
    
    def test_naming_manager(self):
        """测试命名管理器"""
        manager = NamingManager(
            template="{type}/{name}",
            conflict_mode="append"
        )
        
        name1 = manager.generate_name("button", "primary")
        name2 = manager.generate_name("button", "primary")
        
        assert name1 != name2  # 冲突检测应该添加后缀
    
    def test_asset_exporter_mock(self):
        """测试资产导出器 Mock 模式"""
        exporter = AssetExporter(mock_mode=True)
        
        result = exporter.export(
            layer_data=b"mock_image_data",
            format="png",
            scale=1.0,
            output_path="/tmp/test.png"
        )
        
        assert result.success is True


# ============================================================================
# Level 6 Tests - 提取层
# ============================================================================

class TestLevel6Integration:
    """Level 6 - 提取层集成测试"""
    
    def test_text_extraction(self):
        """测试文字提取"""
        reader = TextReader(mock_mode=True)
        
        layer_data = {
            "text": "Hello World",
            "font_family": "Arial",
            "font_size": 24
        }
        
        result = reader.read(layer_data)
        
        assert result.success is True
    
    def test_style_extraction(self):
        """测试样式提取"""
        extractor = StyleExtractor(mock_mode=True)
        
        layer_data = {
            "opacity": 0.8,
            "blend_mode": "normal"
        }
        
        result = extractor.extract(layer_data)
        
        assert result.success is True
    
    def test_position_extraction(self):
        """测试位置提取"""
        reader = PositionReader(mock_mode=True)
        
        layer_data = {
            "left": 100,
            "top": 200,
            "right": 300,
            "bottom": 400
        }
        
        result = reader.read(layer_data)
        
        assert result.success is True
        assert result.x == 100
        assert result.y == 200
    
    def test_extractor_full_workflow(self):
        """测试提取器完整工作流"""
        extractor = Extractor(mock_mode=True)
        
        layer_data = {
            "id": "layer_1",
            "name": "Test Layer",
            "kind": "text",
            "text": "Sample Text",
            "font_family": "Arial",
            "font_size": 16,
            "opacity": 1.0,
            "blend_mode": "normal",
            "left": 0,
            "top": 0,
            "right": 200,
            "bottom": 50
        }
        
        result = extractor.extract(layer_data)
        
        assert result.success is True


# ============================================================================
# Level 7 Tests - 生成层
# ============================================================================

class TestLevel7Integration:
    """Level 7 - 生成层集成测试"""
    
    def test_dimension_generation(self):
        """测试尺寸生成"""
        generator = DimensionGenerator(mock_mode=True)
        
        spec = generator.generate(
            width=100,
            height=50,
            unit="px",
            scale=1.0
        )
        
        assert spec.width.value == 100
        assert spec.width.unit == "px"
    
    def test_style_generation(self):
        """测试样式生成"""
        generator = StyleGenerator(mock_mode=True)
        
        spec = generator.generate(
            color="#FF5733",
            platform="css"
        )
        
        assert spec is not None
    
    def test_spec_validator(self):
        """测试规格验证"""
        validator = SpecValidator(mock_mode=True)
        
        spec = {
            "id": "comp_1",
            "name": "Button",
            "dimensions": {"width": 100, "height": 50},
            "style": {"color": "#FF0000"}
        }
        
        result = validator.validate(spec)
        
        assert result.valid is True
    
    def test_spec_generator_full_workflow(self):
        """测试规格生成器完整工作流"""
        generator = SpecGenerator(mock_mode=True)
        
        component = ComponentSpec(
            id="test_comp_1",
            name="Test Button",
            type="button",
            dimensions={"width": 100, "height": 50},
            position={"x": 10, "y": 20},
            style={"background": "#FF5733"}
        )
        
        result = generator.generate(component)
        
        assert result.success is True


# ============================================================================
# Level 8 Tests - 文档层
# ============================================================================

class TestLevel8Integration:
    """Level 8 - 文档层集成测试"""
    
    def test_readme_generation(self):
        """测试 README 生成"""
        generator = ReadmeGenerator(mock_mode=True)
        
        content = generator.generate()
        
        assert content is not None
        assert len(content) > 0
        assert "# PSD Smart Cut" in content
    
    def test_manifest_generation(self):
        """测试 Manifest 生成"""
        generator = ManifestGenerator(mock_mode=True)
        
        manifest = generator.generate()
        
        assert manifest is not None
        data = json.loads(manifest)
        assert "version" in data
        assert "entries" in data
    
    def test_preview_generation(self):
        """测试 Preview HTML 生成"""
        generator = PreviewGenerator(mock_mode=True)
        
        html = generator.generate()
        
        assert html is not None
        assert "<!DOCTYPE html>" in html
        assert "</html>" in html
    
    def test_doc_aggregator(self):
        """测试文档聚合器"""
        aggregator = DocAggregator(mock_mode=True)
        
        result = aggregator.validate("./docs")
        
        assert result is not None


# ============================================================================
# End-to-End Integration Tests
# ============================================================================

class TestEndToEndIntegration:
    """端到端集成测试"""
    
    def test_full_pipeline_single_layer(self):
        """测试完整流程 - 单图层"""
        # Step 1: 解析 PSD
        doc = create_mock_psd_document()
        layers = doc.pages[0].layers
        
        # Step 2: 分类图层
        classifier = LayerClassifier(mock_mode=True)
        classify_result = classifier.classify_batch(layers[:1])
        assert classify_result.success is True
        
        # Step 3: 识别组件
        recognizer = Recognizer(mock_mode=True)
        recog_result = recognizer.recognize_batch(layers[:1])
        assert recog_result.success is True
        
        # Step 4: 生成规格
        generator = SpecGenerator(mock_mode=True)
        spec = ComponentSpec(
            id="e2e_1",
            name="EndToEnd Button",
            type="button",
            dimensions={"width": 100, "height": 40},
            position={"x": 50, "y": 100},
            style={"background": "#007BFF"}
        )
        spec_result = generator.generate(spec)
        assert spec_result.success is True
        
        # Step 5: 生成文档
        manifest = ManifestGenerator(mock_mode=True).generate()
        assert manifest is not None
    
    def test_full_pipeline_multiple_layers(self):
        """测试完整流程 - 多图层"""
        doc = create_mock_psd_document()
        layers = doc.pages[0].layers
        
        # 分类所有图层
        classifier = LayerClassifier(mock_mode=True)
        classify_result = classifier.classify_batch(layers)
        assert classify_result.success is True
        assert classify_result.total == 11
        
        # 识别所有图层
        recognizer = Recognizer(mock_mode=True)
        recog_result = recognizer.recognize_batch(layers)
        assert recog_result.success is True
        
        # 生成规格
        generator = SpecGenerator(mock_mode=True)
        specs = []
        for i, layer in enumerate(layers[:3]):
            spec = ComponentSpec(
                id=f"e2e_{i}",
                name=layer.name,
                type=layer.kind,
                dimensions={"width": layer.width, "height": layer.height},
                position={"x": layer.left, "y": layer.top},
                style={}
            )
            specs.append(spec)
        
        results = generator.generate_batch(specs)
        assert len(results) == 3
    
    def test_full_pipeline_with_export(self, tmp_path):
        """测试完整流程 - 含导出"""
        output_dir = tmp_path / "export_output"
        output_dir.mkdir()
        
        # 解析
        doc = create_mock_psd_document()
        
        # 分类
        classifier = LayerClassifier(mock_mode=True)
        classify_result = classifier.classify_batch(doc.pages[0].layers[:2])
        
        # 导出
        exporter = Exporter(
            output_dir=str(output_dir),
            naming_template="{type}/{name}",
            mock_mode=True
        )
        
        plan = ExportCutPlan(
            strategy="FLAT",
            components=[{
                "name": "test_button",
                "type": "button",
                "layer_data": b"export_data",
                "position": (100, 200)
            }],
            canvas_width=1920,
            canvas_height=1080
        )
        
        report = exporter.export(plan)
        assert report.success is True
        assert report.total == 1
    
    def test_full_pipeline_with_all_doc_generators(self, tmp_path):
        """测试完整流程 - 含所有文档生成"""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        
        # 生成所有文档
        readme = ReadmeGenerator(mock_mode=True).generate()
        changelog = ReadmeGenerator(mock_mode=True).generate()  # 复用 ReadmeGenerator 作为 mock
        manifest = ManifestGenerator(mock_mode=True).generate()
        preview = PreviewGenerator(mock_mode=True).generate()
        
        # 保存文档
        (docs_dir / "README.md").write_text(readme)
        (docs_dir / "CHANGELOG.md").write_text(changelog)
        (docs_dir / "manifest.json").write_text(manifest)
        (docs_dir / "preview.html").write_text(preview)
        
        # 聚合文档
        aggregator = DocAggregator(mock_mode=True)
        result = aggregator.aggregate(str(docs_dir))
        
        assert result["total_docs"] == 4


# ============================================================================
# Mock PSD File Tests
# ============================================================================

class TestMockPSDFile:
    """Mock PSD 文件测试"""
    
    def test_mock_psd_has_correct_structure(self):
        """测试 Mock PSD 结构正确"""
        doc = create_mock_psd_document()
        
        # 验证页面
        assert doc.page_count == 1
        page = doc.pages[0]
        assert page.width == 1920
        assert page.height == 1080
        
        # 验证图层数量
        assert len(page.layers) == 11
        
        # 验证层级结构
        root_layers = [l for l in page.layers if l.parent_id is None]
        assert len(root_layers) == 4
    
    def test_mock_layer_properties(self):
        """测试 Mock 图层属性"""
        layers = create_mock_psd_document().pages[0].layers
        
        # 查找特定图层
        logo = next((l for l in layers if l.name == "Logo"), None)
        assert logo is not None
        assert logo.width == 100
        assert logo.height == 60
        assert logo.parent_id == "layer_1"
        
        # 查找隐藏图层
        hidden = next((l for l in layers if l.is_hidden), None)
        assert hidden is not None
        assert hidden.visible is False
    
    def test_mock_psd_serialization(self):
        """测试 Mock PSD 序列化"""
        doc = create_mock_psd_document()
        
        # 转换为字典
        data = {
            "version": doc.version,
            "page_count": doc.page_count,
            "layer_count": doc.layer_count,
            "pages": [
                {
                    "name": p.name,
                    "width": p.width,
                    "height": p.height,
                    "layer_count": p.layer_count
                }
                for p in doc.pages
            ]
        }
        
        # 验证序列化
        assert data["version"] == "2024"
        assert data["page_count"] == 1
        assert data["pages"][0]["width"] == 1920
        
        # JSON 序列化
        json_str = json.dumps(data, indent=2)
        assert json_str is not None
        assert len(json_str) > 0


# ============================================================================
# Batch Processing Tests
# ============================================================================

class TestBatchProcessing:
    """批量处理测试"""
    
    def test_batch_classification_performance(self):
        """测试批量分类性能"""
        layers = create_mock_psd_document().pages[0].layers
        classifier = LayerClassifier(mock_mode=True)
        
        start = time.time()
        result = classifier.classify_batch(layers)
        elapsed = time.time() - start
        
        assert result.success is True
        assert elapsed < 1.0  # 应在 1 秒内完成
    
    def test_batch_recognition_performance(self):
        """测试批量识别性能"""
        layers = create_mock_psd_document().pages[0].layers
        recognizer = Recognizer(mock_mode=True)
        
        start = time.time()
        result = recognizer.recognize_batch(layers)
        elapsed = time.time() - start
        
        assert result.success is True
        assert elapsed < 2.0  # 应在 2 秒内完成
    
    def test_batch_spec_generation_performance(self):
        """测试批量规格生成性能"""
        specs = [
            ComponentSpec(
                id=f"batch_{i}",
                name=f"Component {i}",
                type="button",
                dimensions={"width": 100, "height": 50},
                position={"x": i * 100, "y": 0},
                style={}
            )
            for i in range(10)
        ]
        
        generator = SpecGenerator(mock_mode=True)
        
        start = time.time()
        results = generator.generate_batch(specs)
        elapsed = time.time() - start
        
        assert len(results) == 10
        assert elapsed < 1.0  # 应在 1 秒内完成


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
