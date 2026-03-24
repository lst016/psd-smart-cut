"""
Level 5 - Asset Exporter
资产导出器 - 导出 PSD 组件为图片资产

支持格式: PNG, JPG, WebP, SVG
功能: 单个/批量导出, 自动裁剪, 缩放
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import io
import uuid

from skills.common import get_logger, get_config, get_error_handler, ErrorCategory


@dataclass
class ExportResult:
    """导出结果"""
    success: bool
    asset_id: str
    original_path: str
    exported_path: Optional[str]
    format: str
    width: int
    height: int
    file_size: int
    error: Optional[str] = None


class AssetExporter:
    """
    资产导出器
    
    将 PSD 图层/组件导出为图片资产
    支持 PNG/JPG/WebP/SVG 格式
    """
    
    SUPPORTED_FORMATS = {'png', 'jpg', 'jpeg', 'webp', 'svg'}
    FORMAT_EXTENSIONS = {
        'png': '.png',
        'jpg': '.jpg',
        'jpeg': '.jpg',
        'webp': '.webp',
        'svg': '.svg'
    }
    
    def __init__(self, output_dir: str):
        """
        初始化导出器
        
        Args:
            output_dir: 输出目录路径
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger("asset-exporter")
        self.config = get_config()
        self.error_handler = get_error_handler()
        
        self.logger.info(f"AssetExporter initialized, output_dir={self.output_dir}")
    
    def export(
        self,
        layer_data: bytes,
        format: str = "png",
        scale: float = 1.0,
        asset_id: Optional[str] = None,
        crop_whitespace: bool = True
    ) -> ExportResult:
        """
        导出单个资产
        
        Args:
            layer_data: 图层数据（bytes）
            format: 输出格式 (png/jpg/webp/svg)
            scale: 缩放比例
            asset_id: 资产 ID（可选，自动生成）
            crop_whitespace: 是否裁剪空白区域
            
        Returns:
            ExportResult: 导出结果
        """
        # 参数验证
        format = format.lower()
        if format == 'jpeg':
            format = 'jpg'
        
        if format not in self.SUPPORTED_FORMATS:
            error_msg = f"不支持的格式: {format}"
            self.logger.error(error_msg)
            return ExportResult(
                success=False,
                asset_id=asset_id or str(uuid.uuid4()),
                original_path="",
                exported_path=None,
                format=format,
                width=0,
                height=0,
                file_size=0,
                error=error_msg
            )
        
        # 生成 asset_id
        if not asset_id:
            asset_id = str(uuid.uuid4())[:8]
        
        # 生成输出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{asset_id}_{timestamp}{self.FORMAT_EXTENSIONS.get(format, '.png')}"
        output_path = self.output_dir / filename
        
        try:
            self.logger.info(f"Exporting asset {asset_id}, format={format}, scale={scale}")
            
            # 模拟导出（mock 模式）
            # 真实实现需要使用 PIL/Pillow 处理实际图片数据
            width, height, file_size = self._mock_export(
                layer_data, output_path, format, scale, asset_id
            )
            
            # 如果需要裁剪空白区域
            if crop_whitespace:
                width, height = self._crop_whitespace(output_path, format)
            
            result = ExportResult(
                success=True,
                asset_id=asset_id,
                original_path="mock_psd_layer",
                exported_path=str(output_path),
                format=format,
                width=width,
                height=height,
                file_size=file_size
            )
            
            self.logger.info(f"Asset exported successfully: {output_path}, size={file_size}")
            return result
            
        except Exception as e:
            error_msg = f"导出失败: {str(e)}"
            self.logger.error(error_msg)
            
            self.error_handler.record_error(
                task=f"export_asset_{asset_id}",
                error_message=error_msg,
                error_type=type(e).__name__,
                category=ErrorCategory.EXPORT_ERROR,
                severity="high",
                context={"format": format, "scale": scale}
            )
            
            return ExportResult(
                success=False,
                asset_id=asset_id,
                original_path="",
                exported_path=None,
                format=format,
                width=0,
                height=0,
                file_size=0,
                error=error_msg
            )
    
    def export_batch(
        self,
        assets: List[Dict],
        format: str = "png",
        scale: float = 1.0
    ) -> List[ExportResult]:
        """
        批量导出资产
        
        Args:
            assets: 资产列表，每个资产包含:
                - layer_data: bytes - 图层数据
                - asset_id: str - 资产 ID（可选）
                - name: str - 资产名称（可选）
                - metadata: dict - 元数据（可选）
            format: 输出格式
            scale: 缩放比例
            
        Returns:
            List[ExportResult]: 导出结果列表
        """
        self.logger.info(f"Batch export started, count={len(assets)}, format={format}")
        
        results = []
        for i, asset in enumerate(assets):
            asset_id = asset.get('asset_id', f"asset_{i}")
            
            # 生成唯一文件名
            unique_id = f"{asset_id}_{i}"
            
            result = self.export(
                layer_data=asset.get('layer_data', b''),
                format=format,
                scale=scale,
                asset_id=unique_id,
                crop_whitespace=asset.get('crop_whitespace', True)
            )
            results.append(result)
        
        success_count = sum(1 for r in results if r.success)
        self.logger.info(f"Batch export completed: {success_count}/{len(assets)} succeeded")
        
        return results
    
    def _mock_export(
        self,
        layer_data: bytes,
        output_path: Path,
        format: str,
        scale: float,
        asset_id: str
    ) -> Tuple[int, int, int]:
        """
        模拟导出（mock 模式）
        
        真实实现需要使用 PIL/Pillow 处理实际图片数据
        这里创建简单的测试文件
        
        Args:
            layer_data: 原始图层数据
            output_path: 输出路径
            format: 格式
            scale: 缩放比例
            asset_id: 资产 ID
            
        Returns:
            Tuple[width, height, file_size]
        """
        # 模拟尺寸（基于数据大小估算）
        mock_width = int(200 * scale)
        mock_height = int(150 * scale)
        
        # 创建模拟图片内容
        if format == 'svg':
            svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{mock_width}" height="{mock_height}" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" fill="#f0f0f0"/>
  <text x="10" y="20" font-size="14">Asset {asset_id[:8]}</text>
</svg>'''
            output_path.write_text(svg_content, encoding='utf-8')
            file_size = len(svg_content.encode('utf-8'))
        else:
            # PNG/JPG/WebP - 创建简单的二进制占位符
            # 真实实现需要使用 PIL 将 layer_data 转换为图片
            # 这里创建最小有效的 PNG 文件
            png_header = bytes([
                0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
                0x00, 0x00, 0x00, 0x0D,  # IHDR length
                0x49, 0x48, 0x44, 0x52,  # IHDR
                0x00, 0x00, 0x00, 0xC8,  # width: 200
                0x00, 0x00, 0x00, 0x96,  # height: 150
                0x08, 0x02,  # bit depth 8, color type 2 (RGB)
                0x00, 0x00, 0x00,  # compression, filter, interlace
                0x00, 0x00, 0x00, 0x00,  # CRC placeholder
            ])
            
            # 添加一些数据
            placeholder_data = png_header + layer_data[:1024]
            output_path.write_bytes(placeholder_data)
            file_size = len(placeholder_data)
        
        return mock_width, mock_height, file_size
    
    def _crop_whitespace(self, image_path: Path, format: str) -> Tuple[int, int]:
        """
        裁剪空白区域（mock 实现）
        
        真实实现需要:
        1. 使用 PIL 打开图片
        2. 分析alpha通道或边框颜色
        3. 计算实际内容边界
        4. 裁剪并保存
        
        Args:
            image_path: 图片路径
            format: 格式
            
        Returns:
            Tuple[new_width, new_height]
        """
        # Mock: 返回原始尺寸
        # 真实实现需要分析并裁剪空白
        if format == 'svg':
            content = image_path.read_text(encoding='utf-8')
            # 简单解析 SVG 尺寸
            import re
            width_match = re.search(r'width="(\d+)"', content)
            height_match = re.search(r'height="(\d+)"', content)
            if width_match and height_match:
                return int(width_match.group(1)), int(height_match.group(1))
        
        # 返回模拟尺寸
        return 200, 150
    
    def get_output_dir(self) -> Path:
        """获取输出目录"""
        return self.output_dir
    
    def set_output_dir(self, output_dir: str) -> None:
        """设置输出目录"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Output dir changed to: {self.output_dir}")
