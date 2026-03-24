"""
Level 8 - Document Layer Tests
文档层集成测试
"""
import pytest
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from skills.psd_parser.level8_document import (
    ReadmeGenerator,
    ChangelogGenerator,
    ManifestGenerator,
    PreviewGenerator,
    DocAggregator,
    generate_readme,
    generate_changelog,
    generate_manifest,
    generate_preview,
    aggregate_docs
)


class TestReadmeGenerator:
    """README 生成器测试"""
    
    def test_init(self):
        """测试初始化"""
        generator = ReadmeGenerator(mock_mode=True)
        assert generator.mock_mode is True
    
    def test_generate_default(self):
        """测试生成默认 README"""
        generator = ReadmeGenerator(mock_mode=True)
        content = generator.generate()
        
        assert content is not None
        assert len(content) > 0
        assert "# PSD Smart Cut" in content
    
    def test_generate_with_project_info(self):
        """测试使用自定义项目信息生成"""
        generator = ReadmeGenerator(mock_mode=True)
        project_info = {
            "name": "Test Project",
            "description": "A test project",
            "version": "v1.0.0",
            "features": ["Feature 1", "Feature 2"],
            "badges": ["python", "license"]
        }
        
        content = generator.generate(project_info)
        
        assert "Test Project" in content
        assert "A test project" in content
        assert "Feature 1" in content
        assert "Feature 2" in content
    
    def test_generate_badges(self):
        """测试徽章生成"""
        generator = ReadmeGenerator(mock_mode=True)
        badges = generator._generate_badges(["python", "license", "build"])
        
        assert "Python" in badges
        assert "License" in badges
        assert "Build" in badges
    
    def test_save_readme(self, tmp_path):
        """测试保存 README"""
        generator = ReadmeGenerator(mock_mode=True)
        content = generator.generate()
        
        readme_path = tmp_path / "README.md"
        result = generator.save(str(readme_path), content)
        
        assert result is True
        assert readme_path.exists()
        assert readme_path.read_text() == content
    
    def test_auto_detect_features(self):
        """测试自动检测功能"""
        generator = ReadmeGenerator(mock_mode=True)
        features = generator.auto_detect_features()
        
        assert isinstance(features, list)
        assert len(features) > 0


class TestChangelogGenerator:
    """CHANGELOG 生成器测试"""
    
    def test_init(self):
        """测试初始化"""
        generator = ChangelogGenerator(mock_mode=True)
        assert generator.mock_mode is True
    
    def test_parse_git_log_mock(self):
        """测试解析 Mock git log"""
        generator = ChangelogGenerator(mock_mode=True)
        commits = generator.parse_git_log()
        
        assert commits is not None
        assert len(commits) > 0
        assert "hash" in commits[0]
        assert "message" in commits[0]
    
    def test_generate(self):
        """测试生成 CHANGELOG"""
        generator = ChangelogGenerator(mock_mode=True)
        content = generator.generate()
        
        assert content is not None
        assert len(content) > 0
        assert "# Changelog" in content
    
    def test_commit_entry_infer_type(self):
        """测试提交类型推断"""
        from skills.psd_parser.level8_document.changelog_generator import CommitEntry
        
        # feat
        commit = CommitEntry("abc", "feat: add new feature", "author", "date")
        assert commit.type == "feat"
        
        # fix
        commit = CommitEntry("abc", "fix: fix bug", "author", "date")
        assert commit.type == "fix"
        
        # docs
        commit = CommitEntry("abc", "docs: update readme", "author", "date")
        assert commit.type == "docs"
    
    def test_save_changelog(self, tmp_path):
        """测试保存 CHANGELOG"""
        generator = ChangelogGenerator(mock_mode=True)
        content = generator.generate()
        
        changelog_path = tmp_path / "CHANGELOG.md"
        result = generator.save(str(changelog_path), content)
        
        assert result is True
        assert changelog_path.exists()
    
    def test_export_json(self):
        """测试导出 JSON"""
        generator = ChangelogGenerator(mock_mode=True)
        generator.parse_git_log()
        generator.generate()
        
        json_content = generator.export_json()
        
        assert json_content is not None
        data = json.loads(json_content)
        assert "generated_at" in data
        assert "versions" in data


class TestManifestGenerator:
    """Manifest 生成器测试"""
    
    def test_init(self):
        """测试初始化"""
        generator = ManifestGenerator(mock_mode=True)
        assert generator.mock_mode is True
    
    def test_generate_mock_components(self):
        """测试生成 Mock 组件"""
        generator = ManifestGenerator(mock_mode=True)
        components = generator._generate_mock_components()
        
        assert components is not None
        assert len(components) > 0
        assert "id" in components[0]
        assert "name" in components[0]
    
    def test_generate_manifest(self):
        """测试生成 Manifest"""
        generator = ManifestGenerator(mock_mode=True)
        manifest = generator.generate()
        
        assert manifest is not None
        data = json.loads(manifest)
        assert "version" in data
        assert "total_components" in data
        assert "entries" in data
    
    def test_generate_yaml(self):
        """测试生成 YAML 格式"""
        generator = ManifestGenerator(mock_mode=True)
        yaml_content = generator.generate_yaml()
        
        assert yaml_content is not None
        assert "version:" in yaml_content
        assert "entries:" in yaml_content
    
    def test_extract_specs(self):
        """测试提取规格"""
        generator = ManifestGenerator(mock_mode=True)
        component = {
            "dimensions": {"width": 100, "height": 50},
            "position": {"x": 10, "y": 20},
            "visible": True,
            "locked": False
        }
        
        specs = generator._extract_specs(component)
        
        assert specs["width"] == 100
        assert specs["height"] == 50
        assert specs["x"] == 10
        assert specs["y"] == 20
    
    def test_save_manifest(self, tmp_path):
        """测试保存 Manifest"""
        generator = ManifestGenerator(mock_mode=True)
        manifest = generator.generate()
        
        manifest_path = tmp_path / "manifest.json"
        result = generator.save(str(manifest_path), manifest)
        
        assert result is True
        assert manifest_path.exists()
    
    def test_load_manifest(self, tmp_path):
        """测试加载 Manifest"""
        generator = ManifestGenerator(mock_mode=True)
        manifest = generator.generate()
        
        manifest_path = tmp_path / "manifest.json"
        generator.save(str(manifest_path), manifest)
        
        loaded = generator.load(str(manifest_path))
        
        assert loaded is not None
        assert loaded.version == "1.0.0"


class TestPreviewGenerator:
    """Preview 生成器测试"""
    
    def test_init(self):
        """测试初始化"""
        generator = PreviewGenerator(mock_mode=True)
        assert generator.mock_mode is True
    
    def test_generate_html(self):
        """测试生成 HTML"""
        generator = PreviewGenerator(mock_mode=True)
        html = generator.generate()
        
        assert html is not None
        assert len(html) > 0
        assert "<!DOCTYPE html>" in html
        assert "</html>" in html
        assert "PSD Smart Cut" in html
    
    def test_generate_with_components(self):
        """测试使用自定义组件生成"""
        generator = PreviewGenerator(mock_mode=True)
        components = [
            {"id": "c1", "name": "Component 1", "type": "button",
             "dimensions": {"width": 100, "height": 50}, "position": {"x": 0, "y": 0}}
        ]
        
        html = generator.generate(components)
        
        assert "Component 1" in html
        assert "button" in html
    
    def test_type_colors(self):
        """测试类型颜色映射"""
        generator = PreviewGenerator(mock_mode=True)
        
        assert generator.TYPE_COLORS["image"] == "#4CAF50"
        assert generator.TYPE_COLORS["text"] == "#2196F3"
        assert generator.TYPE_COLORS["button"] == "#E91E63"
    
    def test_generate_svg_diagram(self):
        """测试生成 SVG 关系图"""
        generator = PreviewGenerator(mock_mode=True)
        components = generator._generate_mock_components()
        
        svg = generator._generate_svg_diagram(components)
        
        assert svg is not None
        assert "<svg" in svg
        assert "</svg>" in svg
    
    def test_generate_component_card(self):
        """测试生成组件卡片"""
        generator = PreviewGenerator(mock_mode=True)
        component = {
            "id": "c1",
            "name": "Test Button",
            "type": "button",
            "dimensions": {"width": 100, "height": 50},
            "position": {"x": 10, "y": 20}
        }
        
        card = generator._generate_component_card(component)
        
        assert "Test Button" in card
        assert "button" in card
        assert "100" in card
        assert "50" in card
    
    def test_save_preview(self, tmp_path):
        """测试保存 Preview"""
        generator = PreviewGenerator(mock_mode=True)
        html = generator.generate()
        
        preview_path = tmp_path / "preview.html"
        result = generator.save(str(preview_path), html)
        
        assert result is True
        assert preview_path.exists()


class TestDocAggregator:
    """文档聚合器测试"""
    
    def test_init(self):
        """测试初始化"""
        aggregator = DocAggregator(mock_mode=True)
        assert aggregator.mock_mode is True
    
    def test_aggregate(self, tmp_path):
        """测试聚合文档"""
        # 创建测试目录和文件
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "README.md").write_text("# Test README")
        (docs_dir / "CHANGELOG.md").write_text("# Changelog")
        
        aggregator = DocAggregator(mock_mode=True)
        result = aggregator.aggregate(str(docs_dir))
        
        assert result["output_dir"] == str(docs_dir)
        assert result["total_docs"] > 0
        assert "index" in result
        assert "structure" in result
    
    def test_validate_success(self, tmp_path):
        """测试验证成功"""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        
        # 创建必需的文档
        (docs_dir / "README.md").write_text("# README")
        (docs_dir / "CHANGELOG.md").write_text("# Changelog")
        (docs_dir / "VERSION-PLAN.md").write_text("# Version Plan")
        
        aggregator = DocAggregator(mock_mode=True)
        result = aggregator.validate(str(docs_dir))
        
        assert result.valid is True
        assert len(result.errors) == 0
    
    def test_validate_missing_required(self, tmp_path):
        """测试验证缺失必需文档"""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        
        # 只创建 README
        (docs_dir / "README.md").write_text("# README")
        
        aggregator = DocAggregator(mock_mode=True)
        result = aggregator.validate(str(docs_dir))
        
        assert result.valid is False
        assert len(result.errors) > 0
    
    def test_get_missing_docs(self):
        """测试获取缺失文档列表"""
        aggregator = DocAggregator(mock_mode=True)
        # 使用默认空列表
        aggregator._documents = []
        
        # 手动添加一些文档状态
        from skills.psd_parser.level8_document.doc_aggregator import DocumentInfo
        aggregator._documents = [
            DocumentInfo("path1", "README.md", "markdown", 100, True, True),
            DocumentInfo("path2", "CHANGELOG.md", "markdown", 0, False, True),
            DocumentInfo("path3", "preview.html", "html", 0, False, False),
        ]
        
        missing = aggregator.get_missing_docs()
        assert "CHANGELOG.md" in missing
        assert "README.md" not in missing
    
    def test_get_present_docs(self):
        """测试获取存在的文档列表"""
        aggregator = DocAggregator(mock_mode=True)
        from skills.psd_parser.level8_document.doc_aggregator import DocumentInfo
        aggregator._documents = [
            DocumentInfo("path1", "README.md", "markdown", 100, True, True),
            DocumentInfo("path2", "CHANGELOG.md", "markdown", 0, False, True),
        ]
        
        present = aggregator.get_present_docs()
        assert "README.md" in present
        assert "CHANGELOG.md" not in present


class TestConvenienceFunctions:
    """便捷函数测试"""
    
    def test_generate_readme(self):
        """测试便捷函数 generate_readme"""
        content = generate_readme()
        assert content is not None
        assert len(content) > 0
    
    def test_generate_changelog(self):
        """测试便捷函数 generate_changelog"""
        content = generate_changelog()
        assert content is not None
        assert len(content) > 0
    
    def test_generate_manifest(self):
        """测试便捷函数 generate_manifest"""
        content = generate_manifest()
        assert content is not None
        data = json.loads(content)
        assert "entries" in data
    
    def test_generate_preview(self):
        """测试便捷函数 generate_preview"""
        content = generate_preview()
        assert content is not None
        assert "<!DOCTYPE html>" in content
    
    def test_aggregate_docs(self):
        """测试便捷函数 aggregate_docs"""
        result = aggregate_docs(output_dir="./docs", validate=False)
        assert result is not None
        assert "documents" in result


class TestIntegration:
    """集成测试"""
    
    def test_full_document_generation(self, tmp_path):
        """测试完整文档生成流程"""
        # 生成所有文档
        readme_content = generate_readme()
        changelog_content = generate_changelog()
        manifest_content = generate_manifest()
        preview_content = generate_preview()
        
        # 保存到临时目录
        (tmp_path / "README.md").write_text(readme_content)
        (tmp_path / "CHANGELOG.md").write_text(changelog_content)
        (tmp_path / "manifest.json").write_text(manifest_content)
        (tmp_path / "preview.html").write_text(preview_content)
        
        # 验证文件存在
        assert (tmp_path / "README.md").exists()
        assert (tmp_path / "CHANGELOG.md").exists()
        assert (tmp_path / "manifest.json").exists()
        assert (tmp_path / "preview.html").exists()
        
        # 验证内容
        assert "# PSD Smart Cut" in (tmp_path / "README.md").read_text()
        assert "# Changelog" in (tmp_path / "CHANGELOG.md").read_text()
        
        # 使用聚合器验证
        result = aggregate_docs(str(tmp_path), validate=True)
        assert result["total_docs"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
