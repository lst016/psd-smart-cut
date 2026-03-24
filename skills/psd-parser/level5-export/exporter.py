"""
Level 5 - Exporter
统一导出器 - 协调所有导出模块，执行完整导出流程

功能:
- 协调 AssetExporter, FormatConverter, NamingManager, MetadataAttacher
- 执行完整导出流程
- 生成导出报告
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import json

from skills.common import get_logger, get_config, get_error_handler, ErrorCategory
from .asset_exporter import AssetExporter, ExportResult
from .format_converter import FormatConverter, ConversionResult
from .naming_manager import NamingManager, NamingResult
from .metadata_attacher import MetadataAttacher, AssetMetadata


@dataclass
class ExportReport:
    """导出报告"""
    total: int
    success: int
    failed: int
    total_size: int
    assets: List[ExportResult]
    manifest_path: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'total': self.total,
            'success': self.success,
            'failed': self.failed,
            'total_size': self.total_size,
            'total_size_kb': round(self.total_size / 1024, 2),
            'manifest_path': self.manifest_path,
            'metadata': self.metadata,
            'assets': [
                {
                    'asset_id': a.asset_id,
                    'success': a.success,
                    'exported_path': a.exported_path,
                    'format': a.format,
                    'width': a.width,
                    'height': a.height,
                    'file_size': a.file_size,
                    'error': a.error
                }
                for a in self.assets
            ]
        }


@dataclass
class CutPlan:
    """切割计划（来自 Level 4）"""
    strategy: str = "FLAT"
    components: List[Dict] = field(default_factory=list)
    canvas_width: int = 0
    canvas_height: int = 0
    metadata: Dict = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CutPlan':
        """从字典创建"""
        return cls(
            strategy=data.get('strategy', 'FLAT'),
            components=data.get('components', []),
            canvas_width=data.get('canvas_width', 0),
            canvas_height=data.get('canvas_height', 0),
            metadata=data.get('metadata', {})
        )


class Exporter:
    """
    统一导出器
    
    协调所有导出模块，执行完整导出流程
    支持单个组件和批量导出
    """
    
    def __init__(
        self,
        output_dir: str,
        naming_template: str = "{type}/{name}",
        export_format: str = "png",
        export_scale: float = 1.0
    ):
        """
        初始化导出器
        
        Args:
            output_dir: 输出目录
            naming_template: 命名模板
            export_format: 默认导出格式
            export_scale: 默认缩放比例
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.export_format = export_format
        self.export_scale = export_scale
        
        # 初始化各个模块
        self.asset_exporter = AssetExporter(str(self.output_dir))
        self.format_converter = FormatConverter(str(self.output_dir))
        self.naming_manager = NamingManager(naming_template)
        self.metadata_attacher = MetadataAttacher(str(self.output_dir))
        
        # 工具
        self.logger = get_logger("exporter")
        self.config = get_config()
        self.error_handler = get_error_handler()
        
        self.logger.info(f"Exporter initialized, output_dir={self.output_dir}")
    
    def export(
        self,
        plan: CutPlan,
        output_dir: Optional[str] = None,
        export_format: Optional[str] = None,
        naming_template: Optional[str] = None
    ) -> ExportReport:
        """
        执行完整导出流程
        
        Args:
            plan: 切割计划（来自 Level 4）
            output_dir: 输出目录（可选）
            export_format: 导出格式（可选）
            naming_template: 命名模板（可选）
            
        Returns:
            ExportReport: 导出报告
        """
        if output_dir:
            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)
            # 更新子模块的输出目录
            self.asset_exporter.set_output_dir(str(self.output_dir))
            self.format_converter.output_dir = self.output_dir
            self.metadata_attacher.output_dir = self.output_dir
        
        if export_format:
            self.export_format = export_format
        
        if naming_template:
            self.naming_manager.set_template(naming_template)
        
        self.logger.info(f"Export started, plan has {len(plan.components)} components")
        
        # 重置命名管理器
        self.naming_manager.reset()
        
        # 生成名称
        naming_results = self.naming_manager.generate_batch(plan.components)
        
        # 执行导出
        assets: List[ExportResult] = []
        asset_metadata_list: List[AssetMetadata] = []
        
        for i, (component, naming) in enumerate(zip(plan.components, naming_results)):
            try:
                # 准备组件数据
                layer_data = component.get('layer_data', b'')
                component_type = component.get('type', 'unknown')
                component_name = naming.generated_name
                
                # 导出资产
                export_result = self.asset_exporter.export(
                    layer_data=layer_data,
                    format=self.export_format,
                    scale=self.export_scale,
                    asset_id=f"asset_{i}",
                    crop_whitespace=component.get('crop_whitespace', True)
                )
                
                # 如果导出成功，附加元数据
                if export_result.success and export_result.exported_path:
                    # 创建元数据
                    metadata = self.metadata_attacher.create_metadata(
                        component_info={
                            'name': component_name,
                            'type': component_type,
                            'dimensions': (export_result.width, export_result.height),
                            'position': component.get('position', (0, 0)),
                            'source_file': component.get('source_file', ''),
                            'custom_fields': {
                                'format': export_result.format,
                                'file_size': export_result.file_size,
                                'scale': self.export_scale,
                                'strategy': plan.strategy
                            }
                        },
                        layer_ids=component.get('layer_ids', [])
                    )
                    
                    # 附加元数据到图片
                    self.metadata_attacher.attach(export_result.exported_path, metadata)
                    asset_metadata_list.append(metadata)
                
                assets.append(export_result)
                
            except Exception as e:
                error_msg = f"导出组件失败: {str(e)}"
                self.logger.error(error_msg)
                
                # 创建失败的导出结果
                failed_result = ExportResult(
                    success=False,
                    asset_id=f"asset_{i}",
                    original_path=component.get('source_file', ''),
                    exported_path=None,
                    format=self.export_format,
                    width=0,
                    height=0,
                    file_size=0,
                    error=error_msg
                )
                assets.append(failed_result)
        
        # 生成 manifest
        manifest = self.metadata_attacher.generate_manifest(asset_metadata_list)
        manifest_path = str(self.output_dir / 'manifest.json')
        
        # 计算统计
        success_count = sum(1 for a in assets if a.success)
        failed_count = len(assets) - success_count
        total_size = sum(a.file_size for a in assets if a.success)
        
        report = ExportReport(
            total=len(assets),
            success=success_count,
            failed=failed_count,
            total_size=total_size,
            assets=assets,
            manifest_path=manifest_path,
            metadata={
                'plan_strategy': plan.strategy,
                'export_format': self.export_format,
                'export_scale': self.export_scale,
                'canvas_size': (plan.canvas_width, plan.canvas_height),
                'generated_at': datetime.now().isoformat()
            }
        )
        
        self.logger.info(
            f"Export completed: {success_count}/{len(assets)} succeeded, "
            f"total_size={total_size} bytes"
        )
        
        return report
    
    def export_single(
        self,
        component: Dict,
        output_dir: Optional[str] = None,
        export_format: Optional[str] = None
    ) -> ExportResult:
        """
        导出单个组件
        
        Args:
            component: 组件信息
            output_dir: 输出目录（可选）
            export_format: 导出格式（可选）
            
        Returns:
            ExportResult: 导出结果
        """
        if output_dir:
            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)
        
        format_to_use = export_format or self.export_format
        
        self.logger.info(f"Exporting single component: {component.get('name', 'unknown')}")
        
        # 生成名称
        naming = self.naming_manager.generate_name({
            'name': component.get('name', 'unnamed'),
            'type': component.get('type', 'component'),
            'page': component.get('page', 'default')
        })
        
        # 导出
        result = self.asset_exporter.export(
            layer_data=component.get('layer_data', b''),
            format=format_to_use,
            scale=self.export_scale,
            asset_id=component.get('asset_id'),
            crop_whitespace=component.get('crop_whitespace', True)
        )
        
        # 附加元数据
        if result.success and result.exported_path:
            metadata = self.metadata_attacher.create_metadata(
                component_info={
                    'name': naming.generated_name,
                    'type': component.get('type', 'unknown'),
                    'dimensions': (result.width, result.height),
                    'position': component.get('position', (0, 0)),
                    'source_file': component.get('source_file', ''),
                    'custom_fields': {
                        'format': result.format,
                        'file_size': result.file_size,
                        'scale': self.export_scale
                    }
                },
                layer_ids=component.get('layer_ids', [])
            )
            self.metadata_attacher.attach(result.exported_path, metadata)
        
        return result
    
    def export_batch(
        self,
        components: List[Dict],
        output_dir: Optional[str] = None,
        export_format: Optional[str] = None
    ) -> List[ExportResult]:
        """
        批量导出组件
        
        Args:
            components: 组件列表
            output_dir: 输出目录（可选）
            export_format: 导出格式（可选）
            
        Returns:
            List[ExportResult]: 导出结果列表
        """
        if output_dir:
            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)
        
        format_to_use = export_format or self.export_format
        
        self.logger.info(f"Batch export started, count={len(components)}")
        
        # 准备资产数据
        assets = []
        for i, component in enumerate(components):
            asset_data = {
                'layer_data': component.get('layer_data', b''),
                'asset_id': component.get('asset_id', f"asset_{i}"),
                'crop_whitespace': component.get('crop_whitespace', True),
                'name': component.get('name', f"component_{i}"),
                'type': component.get('type', 'component'),
                'page': component.get('page', 'default')
            }
            assets.append(asset_data)
        
        # 批量导出
        results = self.asset_exporter.export_batch(
            assets=assets,
            format=format_to_use,
            scale=self.export_scale
        )
        
        # 批量附加元数据
        for component, result in zip(components, results):
            if result.success and result.exported_path:
                metadata = self.metadata_attacher.create_metadata(
                    component_info={
                        'name': component.get('name', 'unnamed'),
                        'type': component.get('type', 'unknown'),
                        'dimensions': (result.width, result.height),
                        'position': component.get('position', (0, 0)),
                        'custom_fields': {
                            'format': result.format,
                            'file_size': result.file_size
                        }
                    }
                )
                self.metadata_attacher.attach(result.exported_path, metadata)
        
        return results
    
    def get_output_dir(self) -> Path:
        """获取输出目录"""
        return self.output_dir
    
    def get_report_summary(self, report: ExportReport) -> str:
        """
        获取报告摘要文本
        
        Args:
            report: 导出报告
            
        Returns:
            str: 摘要文本
        """
        summary = f"""
=== 导出报告 ===
总数量: {report.total}
成功: {report.success}
失败: {report.failed}
总大小: {report.total_size} bytes ({round(report.total_size / 1024, 2)} KB)
Manifest: {report.manifest_path}
格式: {report.metadata.get('export_format', 'N/A')}
策略: {report.metadata.get('plan_strategy', 'N/A')}
"""
        return summary.strip()
