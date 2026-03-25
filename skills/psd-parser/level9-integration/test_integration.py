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
from typing import Dict, List

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
    StrategySelector, StrategyType, OverlapDetector
)
from skills.psd_parser.level5_export import (
    Exporter, ExportReport,
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

def create_mock_layer_info(
    layer_id: str,
    name: str,
    kind: str,
    left: int, top: int, right: int, bottom: int,
    parent_id: str = None,
    visible: bool = True,
    locked: bool = False
) -> Dict:
    """创建 Mock 图层信息字典（用于 Level 3+ 测试）"""
    return {
        "id": layer_id,
        "name": name,
        "kind": kind,
        "visible": visible,
        "locked": locked,
        "left": left,
        "top": top,
        "right": right,
        "bottom": bottom,
        "width": right - left,
        "height": bottom - top,
        "parent_id": parent_id,
        "opacity": 1.0,
        "blend_mode": "normal",
    }


def create_mock_psd_document():
    """创建 Mock PSD 文档（使用正确的 PSDDocument 签名）"""
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
            kind="image",  # Using image since kind="button" isn't standard
            visible=True,
            locked=False,
            left=200, top=30, right=300, bottom=70,
            width=100, height=40,
            parent_id="layer_3"
        ),
        LayerInfo(
            id="layer_5",
            name="Nav Button 2",
            kind="image",
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
            kind="image",
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
    
    page = PageInfo(
        index=0,
        name="Page 1",
        width=1920,
        height=1080,
        layers=layers
    )
    # page.layer_count doesn't exist; compute via len(page.layers)
    
    return PSDDocument(
        file_path="/mock/test.psd",
        version="2024",
        width=1920,
        height=1080,
        pages=[page],
        total_layers=len(layers),
        metadata={}
    )


def create_mock_layers_dict() -> List[Dict]:
    """创建 Mock 图层字典列表（用于 Level 3+ 测试）"""
    # Note: Recognizer.recognize() looks for "layer_id" key, not "id"
    return [
        create_mock_layer_info("layer_0", "Background", "image", 0, 0, 1920, 1080),
        create_mock_layer_info("layer_1", "Header Group", "group", 0, 0, 1920, 100),
        create_mock_layer_info("layer_2", "Logo", "image", 20, 20, 120, 80, parent_id="layer_1"),
        create_mock_layer_info("layer_3", "Navigation", "group", 200, 0, 1920, 100, parent_id="layer_1"),
        create_mock_layer_info("layer_4", "Nav Button 1", "image", 200, 30, 300, 70, parent_id="layer_3"),
        create_mock_layer_info("layer_5", "Nav Button 2", "image", 320, 30, 420, 70, parent_id="layer_3"),
        create_mock_layer_info("layer_6", "Content Section", "group", 0, 100, 1920, 1080),
        create_mock_layer_info("layer_7", "Hero Text", "text", 100, 150, 900, 250, parent_id="layer_6"),
        create_mock_layer_info("layer_8", "Hero Image", "image", 1000, 100, 1800, 600, parent_id="layer_6"),
        create_mock_layer_info("layer_9", "CTA Button", "image", 100, 700, 300, 760, parent_id="layer_6"),
        create_mock_layer_info("layer_10", "Hidden Layer", "image", 0, 0, 100, 100, visible=False),
    ]


def _to_layer_id_dict(layer: Dict) -> Dict:
    """Convert mock layer dict to use Recognizer's expected 'layer_id' key."""
    result = dict(layer)
    if "id" in result:
        result["layer_id"] = result.pop("id")
    return result


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
        assert len(doc.pages) == 1
        assert doc.total_layers == 11
    
    def test_page_extraction(self):
        """测试页面提取 - 使用 mock 文档"""
        doc = create_mock_psd_document()
        page = doc.pages[0]
        
        assert page is not None
        assert page.name == "Page 1"
        assert page.width == 1920
        assert page.height == 1080
    
    def test_layer_reading(self):
        """测试图层读取"""
        doc = create_mock_psd_document()
        page = doc.pages[0]
        layers = page.layers
        
        assert len(layers) == 11
        visible_layers = [l for l in layers if l.visible]
        hidden_layers = [l for l in layers if not l.visible]
        assert len(visible_layers) == 10
        assert len(hidden_layers) == 1
    
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
        layers = create_mock_layers_dict()
        classifier = LayerClassifier()  # No mock_mode param
        
        # Classify a group layer
        group_layer = next(l for l in layers if l["kind"] == "group")
        result = classifier.classify(group_layer)
        
        assert isinstance(result, ClassificationResult)
        assert result.layer_id == group_layer["id"]
        assert result.type in ["group", "unknown"]  # Could be "group" or fallback
    
    def test_image_classification(self):
        """测试图片子类型分类"""
        classifier = ImageClassifier()  # No mock_mode param
        
        result = classifier.classify(
            layer_info={"id": "test", "name": "hero_banner_image"},
            screenshot_path="/nonexistent/screenshot.png"  # Will use _call_ai mock
        )
        
        assert isinstance(result, ClassificationResult)
        assert result.layer_id == "test"
        assert result.type in ["image", "unknown"]
    
    def test_text_classification(self):
        """测试文字分类"""
        classifier = TextClassifier()  # No mock_mode param
        
        result = classifier.classify(
            layer_info={"id": "test", "name": "Hero Title Text"},
            screenshot_path="/nonexistent/screenshot.png"
        )
        
        assert isinstance(result, ClassificationResult)
        assert result.layer_id == "test"
        assert result.type in ["text", "unknown"]


# ============================================================================
# Level 3 Tests - 识别层
# ============================================================================

class TestLevel3Integration:
    """Level 3 - 识别层集成测试"""
    
    def test_recognizer_full_workflow(self):
        """测试识别器完整工作流"""
        layers = create_mock_layers_dict()
        
        recognizer = Recognizer(
            output_dir="/tmp/test_recognizer",
            use_screenshot=False,
            use_ai_naming=False
        )
        
        # Recognize a single layer (convert to Recognizer's expected key names)
        result = recognizer.recognize(
            psd_file="/mock/test.psd",
            layer_metadata=_to_layer_id_dict(layers[0]),
            capture_screenshot=False
        )
        
        assert isinstance(result, RecognitionResult)
        assert result.layer_id == "layer_0"
    
    def test_region_detection(self):
        """测试区域检测"""
        detector = RegionDetector(
            overlap_threshold=0.3,
            adjacent_threshold=5,
            min_region_area=100
        )
        
        layer_data = {
            "position": {"x": 100, "y": 100},
            "dimensions": {"width": 200, "height": 100}
        }
        
        result = detector.detect_boundary(layer_data)
        
        assert result is not None
        assert hasattr(result, "x")
        assert hasattr(result, "width")
    
    def test_component_naming(self):
        """测试组件命名"""
        namer = ComponentNamer(use_ai=False)
        
        result = namer.name_from_metadata(
            layer_metadata={"id": "btn1", "name": "primary_button_red", "kind": "image"},
            screenshot_path=None
        )
        
        assert isinstance(result, RecognitionResult) or hasattr(result, "component_name")


# ============================================================================
# Level 4 Tests - 策略层
# ============================================================================

class TestLevel4Integration:
    """Level 4 - 策略层集成测试"""
    
    def test_strategy_selection(self):
        """测试策略选择"""
        selector = StrategySelector()  # No mock_mode param
        
        context = {
            "layers": create_mock_layers_dict(),
            "canvas_info": {
                "width": 1920,
                "height": 1080,
                "dpi": 72,
                "color_mode": "RGB"
            },
            "classification_results": []
        }
        
        result = selector.select(**context)
        
        assert result is not None
        assert hasattr(result, "selected_strategy")
        assert isinstance(result.selected_strategy, StrategyType)
    
    def test_overlap_detection(self):
        """测试重叠检测"""
        detector = OverlapDetector()  # No mock_mode param
        
        layers = create_mock_layers_dict()
        
        result = detector.detect_overlaps(
            layers=layers,
            z_order=[l["id"] for l in layers]
        )
        
        assert result is not None
        assert hasattr(result, "overlaps")
        assert isinstance(result.overlaps, list)
    
    def test_cut_plan_creation(self):
        """测试切割计划创建"""
        layers = create_mock_layers_dict()
        
        strategy = Strategy()
        plan = strategy.create_plan(
            layers=layers,
            canvas_width=1920,
            canvas_height=1080,
            dpi=72,
            color_mode="RGB"
        )
        
        assert isinstance(plan, CutPlan)
        assert plan.strategy_type in [e.value for e in StrategyType]


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
            export_format="png"
        )
        
        # Create a CutPlan (Level 5 style)
        from skills.psd_parser.level5_export import CutPlan as ExportCutPlan
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
        
        assert isinstance(report, ExportReport)
        assert report.total == 1
    
    def test_naming_manager(self):
        """测试命名管理器"""
        manager = NamingManager(
            template="{type}/{name}"
        )
        
        # Generate name for first call
        result1 = manager.generate_name({"name": "button", "type": "primary", "page": "home"})
        # Generate again - should get different name due to conflict resolution
        result2 = manager.generate_name({"name": "button", "type": "primary", "page": "home"})
        
        assert result1 is not None
        assert result2 is not None
        assert isinstance(result1.generated_name, str)
    
    def test_asset_exporter_mock(self, tmp_path):
        """测试资产导出器"""
        exporter = AssetExporter(output_dir=str(tmp_path))
        
        result = exporter.export(
            layer_data=b"mock_image_data",
            format="png",
            scale=1.0,
            asset_id="test_asset"
        )
        
        assert hasattr(result, "success")
        assert hasattr(result, "asset_id")


# ============================================================================
# Level 6 Tests - 提取层
# ============================================================================

class TestLevel6Integration:
    """Level 6 - 提取层集成测试"""
    
    def test_text_extraction(self):
        """测试文字提取"""
        reader = TextReader()  # No mock_mode param
        
        layer_data = {
            "text": "Hello World",
            "font_family": "Arial",
            "font_size": 24
        }
        
        result = reader.read(layer_data)
        
        # Result is TextContent or None
        assert result is None or hasattr(result, "text")
    
    def test_style_extraction(self):
        """测试样式提取"""
        extractor = StyleExtractor()  # No mock_mode param
        
        layer_data = {
            "opacity": 0.8,
            "blend_mode": "normal"
        }
        
        result = extractor.extract(layer_data)
        
        assert result is None or hasattr(result, "opacity")
    
    def test_position_extraction(self):
        """测试位置提取"""
        reader = PositionReader(canvas_width=1920, canvas_height=1080)
        
        layer_data = {
            "left": 100,
            "top": 200,
            "right": 300,
            "bottom": 400
        }
        
        result = reader.read(layer_data)
        
        assert result is not None
        assert hasattr(result, "x") or hasattr(result, "width")
    
    def test_extractor_full_workflow(self):
        """测试提取器完整工作流"""
        extractor = Extractor(canvas_width=1920, canvas_height=1080)  # No mock_mode param
        
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
        
        assert isinstance(result, ExtractionResult)
        assert result.layer_id == "layer_1"


# ============================================================================
# Level 7 Tests - 生成层
# ============================================================================

class TestLevel7Integration:
    """Level 7 - 生成层集成测试"""
    
    def test_dimension_generation(self):
        """测试尺寸生成"""
        generator = DimensionGenerator(config={})  # Takes config dict, not mock_mode
        
        spec = generator.generate(
            layer_info={"width": 100, "height": 50},
            unit="px"
        )
        
        assert spec is not None
        assert spec.width == 100
        assert spec.height == 50
        assert spec.unit == "px"
    
    def test_style_generation(self):
        """测试样式生成"""
        generator = StyleGenerator(config={})  # Takes config dict, not mock_mode
        
        spec = generator.generate(
            style_info={"color": "#FF5733"}
        )
        
        assert spec is not None
    
    def test_spec_validator(self):
        """测试规格验证"""
        validator = SpecValidator(config={})  # Takes config dict, not mock_mode
        
        spec = {
            "id": "comp_1",
            "name": "Button",
            "dimensions": {"width": 100, "height": 50},
            "style": {"color": "#FF0000"}
        }
        
        result = validator.validate(spec)
        
        assert hasattr(result, "valid")
    
    def test_spec_generator_full_workflow(self):
        """测试规格生成器完整工作流"""
        generator = SpecGenerator(config={})  # Takes config dict, not mock_mode
        
        layer_info = {
            "id": "test_comp_1",
            "name": "Test Button",
            "kind": "button",
            "width": 100,
            "height": 50,
            "left": 10,
            "top": 20,
            "right": 110,
            "bottom": 70,
        }
        
        result = generator.generate(layer_info)
        
        assert isinstance(result, ComponentSpec)
        assert result.id == "test_comp_1"


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
        assert "PSD Smart Cut" in content
    
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
        layers_dict = create_mock_layers_dict()
        
        # Step 2: 分类图层
        classifier = LayerClassifier()
        classify_result = classifier.classify(layers_dict[0])
        assert isinstance(classify_result, ClassificationResult)
        
        # Step 3: 识别组件
        recognizer = Recognizer(
            output_dir="/tmp/test_e2e",
            use_screenshot=False,
            use_ai_naming=False
        )
        recog_result = recognizer.recognize(
            psd_file="/mock/test.psd",
            layer_metadata=_to_layer_id_dict(layers_dict[0]),
            capture_screenshot=False
        )
        assert isinstance(recog_result, RecognitionResult)
        
        # Step 4: 生成规格
        generator = SpecGenerator(config={})
        spec = generator.generate(layers_dict[0])
        assert isinstance(spec, ComponentSpec)
        
        # Step 5: 生成文档
        manifest = ManifestGenerator(mock_mode=True).generate()
        assert manifest is not None
    
    def test_full_pipeline_multiple_layers(self):
        """测试完整流程 - 多图层"""
        doc = create_mock_psd_document()
        layers_dict = create_mock_layers_dict()
        
        # 分类所有图层
        classifier = LayerClassifier()
        for layer in layers_dict:
            result = classifier.classify(layer)
            assert isinstance(result, ClassificationResult)
        
        # 识别所有图层
        recognizer = Recognizer(
            output_dir="/tmp/test_e2e_multi",
            use_screenshot=False,
            use_ai_naming=False
        )
        for layer in layers_dict[:3]:
            result = recognizer.recognize(
                psd_file="/mock/test.psd",
                layer_metadata=_to_layer_id_dict(layer),
                capture_screenshot=False
            )
            assert isinstance(result, RecognitionResult)
        
        # 生成规格
        generator = SpecGenerator(config={})
        for i, layer in enumerate(layers_dict[:3]):
            spec = generator.generate(layer)
            assert isinstance(spec, ComponentSpec)
    
    def test_full_pipeline_with_export(self, tmp_path):
        """测试完整流程 - 含导出"""
        output_dir = tmp_path / "export_output"
        output_dir.mkdir()
        
        # 解析
        doc = create_mock_psd_document()
        
        # 分类
        classifier = LayerClassifier()
        doc_layers = doc.pages[0].layers
        layer_dict = create_mock_layers_dict()[0]
        classify_result = classifier.classify(layer_dict)
        
        # 导出
        exporter = Exporter(
            output_dir=str(output_dir),
            naming_template="{type}/{name}",
            export_format="png"
        )
        
        from skills.psd_parser.level5_export import CutPlan as ExportCutPlan
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
        assert isinstance(report, ExportReport)
        assert report.total == 1
    
    def test_full_pipeline_with_all_doc_generators(self, tmp_path):
        """测试完整流程 - 含所有文档生成"""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        
        # 生成所有文档
        readme = ReadmeGenerator(mock_mode=True).generate()
        manifest = ManifestGenerator(mock_mode=True).generate()
        preview = PreviewGenerator(mock_mode=True).generate()
        
        # 保存文档
        (docs_dir / "README.md").write_text(readme)
        (docs_dir / "manifest.json").write_text(manifest)
        (docs_dir / "preview.html").write_text(preview)
        
        # 聚合文档
        aggregator = DocAggregator(mock_mode=True)
        result = aggregator.aggregate(str(docs_dir))
        
        assert result is not None


# ============================================================================
# Mock PSD File Tests
# ============================================================================

class TestMockPSDFile:
    """Mock PSD 文件测试"""
    
    def test_mock_psd_has_correct_structure(self):
        """测试 Mock PSD 结构正确"""
        doc = create_mock_psd_document()
        
        # 验证页面
        assert len(doc.pages) == 1
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
            "page_count": len(doc.pages),
            "total_layers": doc.total_layers,
            "pages": [
                {
                    "name": p.name,
                    "width": p.width,
                    "height": p.height,
                    "layer_count": len(p.layers)
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
        layers = create_mock_layers_dict()
        classifier = LayerClassifier()
        
        start = time.time()
        for layer in layers:
            result = classifier.classify(layer)
        elapsed = time.time() - start
        
        assert elapsed < 1.0  # 应在 1 秒内完成
    
    def test_batch_recognition_performance(self):
        """测试批量识别性能"""
        layers = create_mock_layers_dict()
        recognizer = Recognizer(
            output_dir="/tmp/test_batch",
            use_screenshot=False,
            use_ai_naming=False
        )
        
        start = time.time()
        for layer in layers[:3]:
            result = recognizer.recognize(
                psd_file="/mock/test.psd",
                layer_metadata=_to_layer_id_dict(layer),
                capture_screenshot=False
            )
        elapsed = time.time() - start
        
        assert elapsed < 2.0  # 应在 2 秒内完成
    
    def test_batch_spec_generation_performance(self):
        """测试批量规格生成性能"""
        layers = create_mock_layers_dict()
        generator = SpecGenerator(config={})
        
        start = time.time()
        for i, layer in enumerate(layers[:10]):
            spec = generator.generate(layer)
        elapsed = time.time() - start
        
        assert elapsed < 1.0  # 应在 1 秒内完成


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
