"""
Level 5 - Export Layer
资产导出层 - 导出 PSD 组件为最终资产

模块:
- asset_exporter: 资产导出器
- format_converter: 格式转换器
- naming_manager: 命名管理器
- metadata_attacher: 元数据附加器
- exporter: 统一导出器

导出格式: PNG, JPG, WebP, SVG

使用示例:
```python
from skills.psd_parser.level5_export import Exporter, CutPlan

# 创建导出器
exporter = Exporter(
    output_dir="./output/assets",
    naming_template="{type}/{name}",
    export_format="png",
    export_scale=1.0
)

# 创建切割计划（来自 Level 4）
plan = CutPlan(
    strategy="FLAT",
    components=[
        {
            "name": "button_primary",
            "type": "button",
            "layer_data": b"...",
            "position": (100, 200)
        }
    ],
    canvas_width=1920,
    canvas_height=1080
)

# 执行导出
report = exporter.export(plan)

# 打印报告
print(exporter.get_report_summary(report))
```

版本: v0.5
"""

# 资产导出器
from .asset_exporter import AssetExporter, ExportResult

# 格式转换器
from .format_converter import FormatConverter, ConversionResult

# 命名管理器
from .naming_manager import NamingManager, NamingResult

# 元数据附加器
from .metadata_attacher import MetadataAttacher, AssetMetadata

# 统一导出器
from .exporter import Exporter, ExportReport, CutPlan

__all__ = [
    # 资产导出器
    'AssetExporter',
    'ExportResult',
    
    # 格式转换器
    'FormatConverter',
    'ConversionResult',
    
    # 命名管理器
    'NamingManager',
    'NamingResult',
    
    # 元数据附加器
    'MetadataAttacher',
    'AssetMetadata',
    
    # 统一导出器
    'Exporter',
    'ExportReport',
    'CutPlan',
]

__version__ = "0.5.0"
