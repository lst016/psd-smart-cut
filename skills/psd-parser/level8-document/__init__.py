"""
Level 8 - Document Layer
文档生成层

包含：
- README.md 生成器
- CHANGELOG.md 生成器
- manifest.json 生成器
- HTML 预览页生成器
- 文档聚合器
"""

from .readme_generator import ReadmeGenerator, generate_readme
from .changelog_generator import ChangelogGenerator, generate_changelog
from .manifest_generator import ManifestGenerator, generate_manifest
from .preview_generator import PreviewGenerator, generate_preview
from .doc_aggregator import DocAggregator, aggregate_docs

__all__ = [
    # README 生成器
    "ReadmeGenerator",
    "generate_readme",
    
    # CHANGELOG 生成器
    "ChangelogGenerator",
    "generate_changelog",
    
    # Manifest 生成器
    "ManifestGenerator",
    "generate_manifest",
    
    # Preview 生成器
    "PreviewGenerator",
    "generate_preview",
    
    # 文档聚合器
    "DocAggregator",
    "aggregate_docs",
]

__version__ = "0.8.0"
