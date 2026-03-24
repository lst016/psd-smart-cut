"""
Level 5 - Export Layer Tests
资产导出层测试（Mock 模式）

测试覆盖:
- AssetExporter: 导出单个/批量资产
- FormatConverter: 格式转换、压缩
- NamingManager: 命名生成、冲突检测
- MetadataAttacher: 元数据附加、manifest 生成
- Exporter: 完整导出流程
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from skills.psd_parser.level5_export import (
    AssetExporter, ExportResult,
    FormatConverter, ConversionResult,
    NamingManager, NamingResult,
    MetadataAttacher, AssetMetadata,
    Exporter, ExportReport, CutPlan
)


# ============ Fixtures ============

@pytest.fixture
def temp_output_dir():
    """临时输出目录"""
    temp_dir = tempfile.mkdtemp(prefix="level5_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_layer_data():
    """模拟图层数据"""
    return b'\x89PNG\r\n\x1a\n' + b'\x00' * 1024


@pytest.fixture
def sample_components():
    """模拟组件列表"""
    return [
        {
            "name": "button_primary",
            "type": "button",
            "layer_data": b'\x00' * 512,
            "position": (100, 200),
            "source_file": "design.psd"
        },
        {
            "name": "icon_home",
            "type": "icon",
            "layer_data": b'\x00' * 256,
            "position": (50, 50)
        },
        {
            "name": "background_main",
            "type": "background",
            "layer_data": b'\x00' * 1024,
            "position": (0, 0)
        }
    ]


# ============ AssetExporter Tests ============

class TestAssetExporter:
    """AssetExporter 测试"""
    
    def test_init(self, temp_output_dir):
        """测试初始化"""
        exporter = AssetExporter(temp_output_dir)
        assert exporter.output_dir == Path(temp_output_dir)
        assert exporter.output_dir.exists()
    
    def test_export_single_png(self, temp_output_dir, sample_layer_data):
        """测试导出单个 PNG 资产"""
        exporter = AssetExporter(temp_output_dir)
        
        result = exporter.export(
            layer_data=sample_layer_data,
            format="png",
            scale=1.0,
            asset_id="test_001"
        )
        
        assert result.success is True
        assert result.asset_id == "test_001"
        assert result.format == "png"
        assert result.width > 0
        assert result.height > 0
        assert result.file_size > 0
        assert result.exported_path is not None
        assert Path(result.exported_path).exists()
    
    def test_export_single_jpg(self, temp_output_dir, sample_layer_data):
        """测试导出单个 JPG 资产"""
        exporter = AssetExporter(temp_output_dir)
        
        result = exporter.export(
            layer_data=sample_layer_data,
            format="jpg",
            scale=1.0
        )
        
        assert result.success is True
        assert result.format == "jpg"
    
    def test_export_single_webp(self, temp_output_dir, sample_layer_data):
        """测试导出单个 WebP 资产"""
        exporter = AssetExporter(temp_output_dir)
        
        result = exporter.export(
            layer_data=sample_layer_data,
            format="webp"
        )
        
        assert result.success is True
        assert result.format == "webp"
    
    def test_export_single_svg(self, temp_output_dir, sample_layer_data):
        """测试导出单个 SVG 资产"""
        exporter = AssetExporter(temp_output_dir)
        
        result = exporter.export(
            layer_data=sample_layer_data,
            format="svg"
        )
        
        assert result.success is True
        assert result.format == "svg"
    
    def test_export_unsupported_format(self, temp_output_dir, sample_layer_data):
        """测试不支持的格式"""
        exporter = AssetExporter(temp_output_dir)
        
        result = exporter.export(
            layer_data=sample_layer_data,
            format="bmp"
        )
        
        assert result.success is False
        assert result.error is not None
        assert "不支持" in result.error
    
    def test_export_batch(self, temp_output_dir, sample_components):
        """测试批量导出"""
        exporter = AssetExporter(temp_output_dir)
        
        results = exporter.export_batch(
            assets=sample_components,
            format="png"
        )
        
        assert len(results) == 3
        assert all(r.success for r in results)
        assert all(r.format == "png" for r in results)
    
    def test_export_with_scale(self, temp_output_dir, sample_layer_data):
        """测试缩放导出"""
        exporter = AssetExporter(temp_output_dir)
        
        result = exporter.export(
            layer_data=sample_layer_data,
            format="png",
            scale=2.0
        )
        
        assert result.success is True
        assert result.width >= 200  # 基础 200 * 2.0


# ============ FormatConverter Tests ============

class TestFormatConverter:
    """FormatConverter 测试"""
    
    @pytest.fixture
    def sample_image(self, temp_output_dir):
        """创建测试图片"""
        image_path = Path(temp_output_dir) / "test.png"
        # 创建一个最小的有效 PNG
        png_data = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
            0x00, 0x00, 0x00, 0xC8, 0x00, 0x00, 0x00, 0x96,
            0x08, 0x02, 0x00, 0x00, 0x00, 0xD3, 0x10, 0x3F,
            0x31, 0x00, 0x00, 0x00, 0x1A, 0x49, 0x44, 0x41,
            0x54, 0x78, 0x9C, 0x62, 0xF8, 0x0F, 0x00, 0x01,
            0x01, 0x01, 0x00, 0x18, 0xDD, 0x8D, 0xB4, 0x00,
            0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,
            0x42, 0x60, 0x82
        ])
        image_path.write_bytes(png_data)
        return str(image_path)
    
    def test_init(self, temp_output_dir):
        """测试初始化"""
        converter = FormatConverter(temp_output_dir)
        assert converter.output_dir == Path(temp_output_dir)
    
    def test_convert_png_to_jpg(self, sample_image, temp_output_dir):
        """测试 PNG 转 JPG"""
        converter = FormatConverter(temp_output_dir)
        
        result = converter.convert(
            input_path=sample_image,
            output_format="jpg",
            quality=90
        )
        
        assert result.success is True
        assert result.output_path is not None
        assert result.format == "jpg"
        assert result.converted_size > 0
    
    def test_convert_png_to_webp(self, sample_image, temp_output_dir):
        """测试 PNG 转 WebP"""
        converter = FormatConverter(temp_output_dir)
        
        result = converter.convert(
            input_path=sample_image,
            output_format="webp",
            quality=85
        )
        
        assert result.success is True
        assert result.format == "webp"
    
    def test_convert_batch(self, temp_output_dir):
        """测试批量转换"""
        # 创建多个测试图片
        input_paths = []
        for i in range(3):
            path = Path(temp_output_dir) / f"input_{i}.png"
            png_data = bytes([0x89, 0x50, 0x4E, 0x47] + [i] * 100)
            path.write_bytes(png_data)
            input_paths.append(str(path))
        
        converter = FormatConverter(temp_output_dir)
        
        results = converter.convert_batch(
            input_paths=input_paths,
            output_format="webp"
        )
        
        assert len(results) == 3
        assert all(r.success for r in results)
    
    def test_compress(self, sample_image, temp_output_dir):
        """测试压缩"""
        converter = FormatConverter(temp_output_dir)
        
        result = converter.compress(
            input_path=sample_image,
            target_size_kb=1
        )
        
        assert result.success is True
        # 压缩后应该小于等于原始大小
        assert result.converted_size <= result.original_size
    
    def test_convert_nonexistent_file(self, temp_output_dir):
        """测试不存在的文件"""
        converter = FormatConverter(temp_output_dir)
        
        result = converter.convert(
            input_path="/nonexistent/file.png",
            output_format="jpg"
        )
        
        assert result.success is False
        assert "不存在" in result.error


# ============ NamingManager Tests ============

class TestNamingManager:
    """NamingManager 测试"""
    
    def test_init_default_template(self):
        """测试默认模板初始化"""
        namer = NamingManager()
        assert namer.template == "{type}/{name}"
    
    def test_init_custom_template(self):
        """测试自定义模板"""
        namer = NamingManager(template="{page}/{type}/{name}")
        assert namer.template == "{page}/{type}/{name}"
    
    def test_generate_name_simple(self):
        """测试简单命名"""
        namer = NamingManager(template="{name}")
        
        result = namer.generate_name({
            "name": "button",
            "type": "button"
        })
        
        assert result.generated_name == "button"
        assert result.is_unique is True
    
    def test_generate_name_with_type(self):
        """测试带类型的命名"""
        namer = NamingManager(template="{type}/{name}")
        
        result = namer.generate_name({
            "name": "submit",
            "type": "button"
        })
        
        assert result.generated_name == "button/submit"
    
    def test_generate_name_with_page(self):
        """测试带页面的命名"""
        namer = NamingManager(template="{page}/{type}/{name}")
        
        result = namer.generate_name({
            "name": "logo",
            "type": "icon",
            "page": "home"
        })
        
        assert result.generated_name == "home/icon/logo"
    
    def test_generate_name_with_index(self):
        """测试带索引的命名"""
        namer = NamingManager(template="{type}/{name}_{index}")
        
        result = namer.generate_name({
            "name": "btn",
            "type": "button",
            "index": 5
        })
        
        assert "005" in result.generated_name
    
    def test_generate_name_sanitize(self):
        """测试名称清理"""
        namer = NamingManager(template="{name}")
        
        result = namer.generate_name({
            "name": "hello world?<>|test"
        })
        
        # 非法字符应该被替换
        assert "?" not in result.generated_name
        assert "<" not in result.generated_name
    
    def test_generate_batch(self):
        """测试批量命名"""
        namer = NamingManager(template="{type}/{name}")
        
        components = [
            {"name": "btn1", "type": "button"},
            {"name": "btn2", "type": "button"},
            {"name": "icon1", "type": "icon"}
        ]
        
        results = namer.generate_batch(components)
        
        assert len(results) == 3
        assert all(r.is_unique for r in results)
    
    def test_resolve_conflicts(self):
        """测试冲突解决"""
        namer = NamingManager()
        
        names = ["button/submit", "button/submit", "icon/home"]
        resolved = namer.resolve_conflicts(names)
        
        assert len(resolved) == 3
        assert resolved[0] == "button/submit"
        assert resolved[1] != "button/submit"  # 应该有后缀
        assert resolved[2] == "icon/home"
    
    def test_validate_name_valid(self):
        """测试有效名称验证"""
        namer = NamingManager()
        
        is_valid, error = namer.validate_name("button/submit")
        
        assert is_valid is True
        assert error is None
    
    def test_validate_name_empty(self):
        """测试空名称验证"""
        namer = NamingManager()
        
        is_valid, error = namer.validate_name("")
        
        assert is_valid is False
        assert "空" in error
    
    def test_validate_name_reserved_chars(self):
        """测试非法字符验证"""
        namer = NamingManager()
        
        is_valid, error = namer.validate_name("test<>:file")
        
        assert is_valid is False
        assert "非法字符" in error
    
    def test_reset(self):
        """测试重置"""
        namer = NamingManager()
        
        namer.generate_name({"name": "test", "type": "button"})
        assert len(namer.get_used_names()) == 1
        
        namer.reset()
        assert len(namer.get_used_names()) == 0


# ============ MetadataAttacher Tests ============

class TestMetadataAttacher:
    """MetadataAttacher 测试"""
    
    def test_init(self, temp_output_dir):
        """测试初始化"""
        attacher = MetadataAttacher(temp_output_dir)
        assert attacher.output_dir == Path(temp_output_dir)
    
    def test_create_metadata(self, temp_output_dir):
        """测试创建元数据"""
        attacher = MetadataAttacher(temp_output_dir)
        
        metadata = attacher.create_metadata({
            "name": "test_button",
            "type": "button",
            "dimensions": (100, 50),
            "position": (10, 20)
        })
        
        assert metadata.component_name == "test_button"
        assert metadata.component_type == "button"
        assert metadata.dimensions == (100, 50)
        assert metadata.position == (10, 20)
        assert metadata.asset_id is not None
    
    def test_attach_metadata(self, temp_output_dir, sample_layer_data):
        """测试附加元数据"""
        attacher = MetadataAttacher(temp_output_dir)
        
        # 先导出图片
        exporter = AssetExporter(temp_output_dir)
        result = exporter.export(layer_data=sample_layer_data, format="png")
        
        # 创建并附加元数据
        metadata = attacher.create_metadata({
            "name": "test_asset",
            "type": "test"
        })
        
        success = attacher.attach(result.exported_path, metadata)
        
        assert success is True
        # 检查 sidecar 文件是否存在
        meta_path = Path(result.exported_path + ".meta.json")
        assert meta_path.exists()
    
    def test_extract_metadata(self, temp_output_dir, sample_layer_data):
        """测试提取元数据"""
        attacher = MetadataAttacher(temp_output_dir)
        
        # 导出并附加元数据
        exporter = AssetExporter(temp_output_dir)
        result = exporter.export(layer_data=sample_layer_data, format="png")
        
        metadata = attacher.create_metadata({
            "name": "extract_test",
            "type": "extract"
        })
        attacher.attach(result.exported_path, metadata)
        
        # 提取元数据
        extracted = attacher.extract(result.exported_path)
        
        assert extracted is not None
        assert extracted.component_name == "extract_test"
        assert extracted.component_type == "extract"
    
    def test_generate_manifest(self, temp_output_dir):
        """测试生成 manifest"""
        attacher = MetadataAttacher(temp_output_dir)
        
        assets = [
            AssetMetadata(
                asset_id="1",
                component_name="btn1",
                component_type="button",
                custom_fields={"file_size": 1024, "format": "png"}
            ),
            AssetMetadata(
                asset_id="2",
                component_name="icon1",
                component_type="icon",
                custom_fields={"file_size": 512, "format": "webp"}
            )
        ]
        
        manifest = attacher.generate_manifest(assets)
        
        assert manifest["total_assets"] == 2
        assert manifest["assets_by_type"]["button"] == 1
        assert manifest["assets_by_type"]["icon"] == 1
        assert manifest["summary"]["total_size_bytes"] == 1536
    
    def test_validate_metadata(self, temp_output_dir):
        """测试元数据验证"""
        attacher = MetadataAttacher(temp_output_dir)
        
        # 有效元数据
        valid_metadata = AssetMetadata(
            asset_id="test123",
            component_name="test",
            component_type="button"
        )
        
        is_valid, errors = attacher.validate_metadata(valid_metadata)
        assert is_valid is True
        assert len(errors) == 0
        
        # 无效元数据（缺少必需字段）
        invalid_metadata = AssetMetadata(
            asset_id="",
            component_name="",
            component_type=""
        )
        
        is_valid, errors = attacher.validate_metadata(invalid_metadata)
        assert is_valid is False
        assert len(errors) > 0


# ============ Exporter Tests ============

class TestExporter:
    """Exporter 测试"""
    
    def test_init(self, temp_output_dir):
        """测试初始化"""
        exporter = Exporter(
            output_dir=temp_output_dir,
            naming_template="{type}/{name}",
            export_format="png"
        )
        
        assert exporter.output_dir == Path(temp_output_dir)
        assert exporter.export_format == "png"
    
    def test_export_single_component(self, temp_output_dir, sample_layer_data):
        """测试导出单个组件"""
        exporter = Exporter(output_dir=temp_output_dir)
        
        component = {
            "name": "single_test",
            "type": "button",
            "layer_data": sample_layer_data
        }
        
        result = exporter.export_single(component)
        
        assert result.success is True
        assert result.format == "png"
    
    def test_export_batch_components(self, temp_output_dir, sample_components):
        """测试批量导出组件"""
        exporter = Exporter(output_dir=temp_output_dir)
        
        results = exporter.export_batch(sample_components)
        
        assert len(results) == 3
        assert all(r.success for r in results)
    
    def test_export_with_cutplan(self, temp_output_dir, sample_components):
        """测试使用 CutPlan 导出"""
        exporter = Exporter(output_dir=temp_output_dir)
        
        plan = CutPlan(
            strategy="FLAT",
            components=sample_components,
            canvas_width=1920,
            canvas_height=1080
        )
        
        report = exporter.export(plan)
        
        assert isinstance(report, ExportReport)
        assert report.total == 3
        assert report.success == 3
        assert report.failed == 0
        assert report.total_size > 0
        assert report.manifest_path.endswith("manifest.json")
    
    def test_export_different_formats(self, temp_output_dir, sample_layer_data):
        """测试不同格式导出"""
        formats = ["png", "jpg", "webp", "svg"]
        
        for fmt in formats:
            temp_dir = tempfile.mkdtemp(prefix=f"format_test_{fmt}_")
            exporter = Exporter(output_dir=temp_dir, export_format=fmt)
            
            component = {
                "name": f"test_{fmt}",
                "type": "test",
                "layer_data": sample_layer_data
            }
            
            result = exporter.export_single(component, export_format=fmt)
            assert result.success is True, f"Format {fmt} failed"
            
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_get_report_summary(self, temp_output_dir, sample_components):
        """测试报告摘要"""
        exporter = Exporter(output_dir=temp_output_dir)
        
        plan = CutPlan(
            strategy="GROUP_BY_TYPE",
            components=sample_components
        )
        
        report = exporter.export(plan)
        summary = exporter.get_report_summary(report)
        
        assert "导出报告" in summary
        assert "总数量: 3" in summary
        assert "成功: 3" in summary


# ============ Integration Tests ============

class TestLevel5Integration:
    """Level 5 集成测试"""
    
    def test_full_export_workflow(self, temp_output_dir, sample_layer_data):
        """测试完整导出工作流"""
        # 1. 创建导出器
        exporter = Exporter(
            output_dir=temp_output_dir,
            naming_template="{type}/{name}",
            export_format="png",
            export_scale=1.0
        )
        
        # 2. 准备组件
        components = [
            {
                "name": "home_button",
                "type": "button",
                "layer_data": sample_layer_data,
                "position": (100, 100),
                "source_file": "design.psd"
            },
            {
                "name": "settings_icon",
                "type": "icon",
                "layer_data": sample_layer_data,
                "position": (50, 50)
            }
        ]
        
        # 3. 创建计划
        plan = CutPlan(
            strategy="FLAT",
            components=components,
            canvas_width=1920,
            canvas_height=1080,
            metadata={"version": "1.0"}
        )
        
        # 4. 执行导出
        report = exporter.export(plan)
        
        # 5. 验证结果
        assert report.total == 2
        assert report.success == 2
        assert report.manifest_path is not None
        
        # 6. 检查 manifest 文件
        manifest_path = Path(report.manifest_path)
        assert manifest_path.exists()
        
        import json
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        assert manifest["total_assets"] == 2
        assert "button" in manifest["assets_by_type"]
        assert "icon" in manifest["assets_by_type"]


# ============ Run Tests ============

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
