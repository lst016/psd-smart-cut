"""
Level 5 - Format Converter
格式转换器 - 图片格式转换、压缩、优化

支持格式: PNG, JPG, WebP, SVG
功能: 格式转换, 压缩, 保持透明度, 批量处理
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import os
import shutil

from skills.common import get_logger, get_config, get_error_handler, ErrorCategory


@dataclass
class ConversionResult:
    """格式转换结果"""
    success: bool
    input_path: str
    output_path: Optional[str]
    original_size: int
    converted_size: int
    compression_ratio: float
    format: str
    error: Optional[str] = None


class FormatConverter:
    """
    格式转换器
    
    支持 PNG/JPG/WebP/SVG 之间的转换
    支持压缩和质量控制
    """
    
    SUPPORTED_FORMATS = {'png', 'jpg', 'jpeg', 'webp', 'svg'}
    FORMAT_EXTENSIONS = {
        'png': '.png',
        'jpg': '.jpg',
        'jpeg': '.jpg',
        'webp': '.webp',
        'svg': '.svg'
    }
    
    # 格式转换映射
    CONVERSION_SUPPORT = {
        'png': ['jpg', 'webp', 'svg'],
        'jpg': ['png', 'webp', 'svg'],
        'jpeg': ['png', 'webp', 'svg'],
        'webp': ['png', 'jpg', 'svg'],
        'svg': ['png', 'jpg', 'webp']
    }
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        初始化格式转换器
        
        Args:
            output_dir: 输出目录（可选，默认与输入相同目录）
        """
        self.output_dir = Path(output_dir) if output_dir else None
        self.logger = get_logger("format-converter")
        self.config = get_config()
        self.error_handler = get_error_handler()
        
        self.logger.info(f"FormatConverter initialized, output_dir={self.output_dir}")
    
    def convert(
        self,
        input_path: str,
        output_format: str,
        quality: int = 90,
        preserve_transparency: bool = True
    ) -> ConversionResult:
        """
        转换单个图片格式
        
        Args:
            input_path: 输入文件路径
            output_format: 输出格式 (png/jpg/webp/svg)
            quality: 输出质量 (1-100)
            preserve_transparency: 是否保持透明度
            
        Returns:
            ConversionResult: 转换结果
        """
        input_path = Path(input_path)
        output_format = output_format.lower()
        
        if output_format == 'jpeg':
            output_format = 'jpg'
        
        # 验证输入文件
        if not input_path.exists():
            error_msg = f"输入文件不存在: {input_path}"
            self.logger.error(error_msg)
            return ConversionResult(
                success=False,
                input_path=str(input_path),
                output_path=None,
                original_size=0,
                converted_size=0,
                compression_ratio=0.0,
                format=output_format,
                error=error_msg
            )
        
        # 验证格式支持
        input_ext = input_path.suffix.lower().lstrip('.')
        if input_ext == 'jpeg':
            input_ext = 'jpg'
        
        if input_ext not in self.SUPPORTED_FORMATS:
            error_msg = f"不支持的输入格式: {input_ext}"
            self.logger.error(error_msg)
            return ConversionResult(
                success=False,
                input_path=str(input_path),
                output_path=None,
                original_size=0,
                converted_size=0,
                compression_ratio=0.0,
                format=output_format,
                error=error_msg
            )
        
        if output_format not in self.SUPPORTED_FORMATS:
            error_msg = f"不支持的输出格式: {output_format}"
            self.logger.error(error_msg)
            return ConversionResult(
                success=False,
                input_path=str(input_path),
                output_path=None,
                original_size=0,
                converted_size=0,
                compression_ratio=0.0,
                format=output_format,
                error=error_msg
            )
        
        # 验证转换支持
        if output_format not in self.CONVERSION_SUPPORT.get(input_ext, []):
            error_msg = f"不支持从 {input_ext} 转换为 {output_format}"
            self.logger.error(error_msg)
            return ConversionResult(
                success=False,
                input_path=str(input_path),
                output_path=None,
                original_size=0,
                converted_size=0,
                compression_ratio=0.0,
                format=output_format,
                error=error_msg
            )
        
        # 生成输出路径
        if self.output_dir:
            output_dir = self.output_dir
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            output_dir = input_path.parent
        
        output_filename = f"{input_path.stem}_converted.{self.FORMAT_EXTENSIONS.get(output_format, '.png')}"
        output_path = output_dir / output_filename
        
        try:
            self.logger.info(f"Converting {input_path} -> {output_path}, format={output_format}, quality={quality}")
            
            # 获取原始文件大小
            original_size = input_path.stat().st_size
            
            # 执行转换（mock 模式）
            converted_size = self._mock_convert(
                input_path, output_path, output_format, quality, preserve_transparency
            )
            
            # 计算压缩比
            compression_ratio = (original_size - converted_size) / original_size if original_size > 0 else 0.0
            
            result = ConversionResult(
                success=True,
                input_path=str(input_path),
                output_path=str(output_path),
                original_size=original_size,
                converted_size=converted_size,
                compression_ratio=compression_ratio,
                format=output_format
            )
            
            self.logger.info(f"Conversion successful: {output_path}, ratio={compression_ratio:.2%}")
            return result
            
        except Exception as e:
            error_msg = f"转换失败: {str(e)}"
            self.logger.error(error_msg)
            
            self.error_handler.record_error(
                task=f"convert_{input_path.name}",
                error_message=error_msg,
                error_type=type(e).__name__,
                category=ErrorCategory.EXPORT_ERROR,
                severity="high",
                context={"input_format": input_ext, "output_format": output_format}
            )
            
            return ConversionResult(
                success=False,
                input_path=str(input_path),
                output_path=None,
                original_size=0,
                converted_size=0,
                compression_ratio=0.0,
                format=output_format,
                error=error_msg
            )
    
    def convert_batch(
        self,
        input_paths: List[str],
        output_format: str,
        quality: int = 90,
        preserve_transparency: bool = True
    ) -> List[ConversionResult]:
        """
        批量转换图片格式
        
        Args:
            input_paths: 输入文件路径列表
            output_format: 输出格式
            quality: 输出质量
            preserve_transparency: 是否保持透明度
            
        Returns:
            List[ConversionResult]: 转换结果列表
        """
        self.logger.info(f"Batch conversion started, count={len(input_paths)}, format={output_format}")
        
        results = []
        for input_path in input_paths:
            result = self.convert(input_path, output_format, quality, preserve_transparency)
            results.append(result)
        
        success_count = sum(1 for r in results if r.success)
        self.logger.info(f"Batch conversion completed: {success_count}/{len(input_paths)} succeeded")
        
        return results
    
    def compress(
        self,
        input_path: str,
        target_size_kb: int,
        output_format: Optional[str] = None
    ) -> ConversionResult:
        """
        压缩图片到目标大小
        
        Args:
            input_path: 输入文件路径
            target_size_kb: 目标大小（KB）
            output_format: 输出格式（可选，默认与输入相同）
            
        Returns:
            ConversionResult: 转换结果
        """
        input_path = Path(input_path)
        
        if not input_path.exists():
            error_msg = f"输入文件不存在: {input_path}"
            self.logger.error(error_msg)
            return ConversionResult(
                success=False,
                input_path=str(input_path),
                output_path=None,
                original_size=0,
                converted_size=0,
                compression_ratio=0.0,
                format=output_format or input_path.suffix.lstrip('.'),
                error=error_msg
            )
        
        # 确定输出格式
        if not output_format:
            output_format = input_path.suffix.lower().lstrip('.')
            if output_format == 'jpeg':
                output_format = 'jpg'
        
        # 生成输出路径
        if self.output_dir:
            output_dir = self.output_dir
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            output_dir = input_path.parent
        
        output_filename = f"{input_path.stem}_compressed.{self.FORMAT_EXTENSIONS.get(output_format, '.png')}"
        output_path = output_dir / output_filename
        
        try:
            self.logger.info(f"Compressing {input_path} to target {target_size_kb}KB")
            
            # 获取原始文件大小
            original_size = input_path.stat().st_size
            target_size_bytes = target_size_kb * 1024
            
            # 计算目标质量
            # 简单的线性估算（真实实现需要迭代）
            quality = min(100, max(10, int(100 * target_size_bytes / original_size)))
            
            # 执行压缩
            converted_size = self._mock_convert(
                input_path, output_path, output_format, quality, preserve_transparency=True
            )
            
            # 计算压缩比
            compression_ratio = (original_size - converted_size) / original_size if original_size > 0 else 0.0
            
            result = ConversionResult(
                success=True,
                input_path=str(input_path),
                output_path=str(output_path),
                original_size=original_size,
                converted_size=converted_size,
                compression_ratio=compression_ratio,
                format=output_format
            )
            
            self.logger.info(f"Compression completed: {output_path}, size={converted_size} bytes")
            return result
            
        except Exception as e:
            error_msg = f"压缩失败: {str(e)}"
            self.logger.error(error_msg)
            
            return ConversionResult(
                success=False,
                input_path=str(input_path),
                output_path=None,
                original_size=0,
                converted_size=0,
                compression_ratio=0.0,
                format=output_format,
                error=error_msg
            )
    
    def _mock_convert(
        self,
        input_path: Path,
        output_path: Path,
        output_format: str,
        quality: int,
        preserve_transparency: bool
    ) -> int:
        """
        模拟格式转换
        
        真实实现需要:
        - PNG/JPG/WebP: 使用 PIL/Pillow
        - SVG: 使用 cairosvg
        
        Args:
            input_path: 输入路径
            output_path: 输出路径
            output_format: 输出格式
            quality: 质量
            preserve_transparency: 是否保持透明
            
        Returns:
            转换后文件大小
        """
        original_size = input_path.stat().st_size
        
        if output_format == 'svg':
            # SVG 转换（简化实现）
            svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg">
  <title>Converted from {input_path.name}</title>
  <rect width="100" height="100" fill="#cccccc"/>
</svg>'''
            output_path.write_text(svg_content, encoding='utf-8')
            return len(svg_content.encode('utf-8'))
        else:
            # PNG/JPG/WebP - 简单复制并模拟压缩效果
            content = input_path.read_bytes()
            
            # 模拟压缩效果
            if quality < 50:
                # 高压缩
                compressed = content[:max(100, len(content) // 2)]
            elif quality < 80:
                # 中等压缩
                compressed = content[:max(100, int(len(content) * 0.7))]
            else:
                # 低压缩/高质量
                compressed = content[:max(100, int(len(content) * 0.9))]
            
            output_path.write_bytes(compressed)
            return len(compressed)
    
    def get_format_info(self, file_path: str) -> Dict:
        """
        获取文件格式信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict: 格式信息
        """
        path = Path(file_path)
        if not path.exists():
            return {"error": "File not found"}
        
        ext = path.suffix.lower().lstrip('.')
        if ext == 'jpeg':
            ext = 'jpg'
        
        size = path.stat().st_size
        
        return {
            "format": ext,
            "size_bytes": size,
            "size_kb": round(size / 1024, 2),
            "supported": ext in self.SUPPORTED_FORMATS
        }
