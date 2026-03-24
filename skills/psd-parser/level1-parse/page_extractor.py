"""
Level 1 - Page Extractor
提取 PSD 中的 Page 信息
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from skills.common import get_logger, get_error_handler, ErrorCategory
from skills.psd_parser.level1_parse.psd_parser import PSDParser, PageInfo

@dataclass
class PageExtractResult:
    """Page 提取结果"""
    success: bool
    page_count: int
    pages: List[Dict] = field(default_factory=list)
    default_page_index: int = 0
    error: Optional[str] = None

class PageExtractor:
    """
    Page 提取器
    职责：列出所有 Page，提取 Page 基本信息
    """
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.logger = get_logger("page-extractor")
        self.error_handler = get_error_handler()
        self.parser: Optional[PSDParser] = None
    
    def extract(self, page_index: Optional[int] = None) -> PageExtractResult:
        """
        提取 Page 信息
        
        Args:
            page_index: 指定 Page 索引，None 表示所有 Page
        
        Returns:
            PageExtractResult: 提取结果
        """
        self.logger.info(f"开始提取 Page: {self.file_path}")
        
        try:
            # 解析 PSD
            self.parser = PSDParser(str(self.file_path))
            document = self.parser.parse()
            
            if page_index is not None:
                # 提取指定 Page
                page = document.get_page(page_index)
                if page is None:
                    return PageExtractResult(
                        success=False,
                        page_count=0,
                        error=f"Page {page_index} 不存在"
                    )
                pages = [page.to_dict()]
            else:
                # 提取所有 Page
                pages = [p.to_dict() for p in document.pages]
            
            result = PageExtractResult(
                success=True,
                page_count=len(pages),
                pages=pages,
                default_page_index=0
            )
            
            self.logger.info(f"Page 提取完成: {result.page_count} pages")
            return result
            
        except Exception as e:
            error_msg = f"Page 提取失败: {str(e)}"
            self.logger.error(error_msg)
            self.error_handler.record(
                task="page-extractor",
                error=e,
                category=ErrorCategory.PARSE_ERROR
            )
            return PageExtractResult(
                success=False,
                page_count=0,
                error=error_msg
            )
    
    def list_pages(self) -> List[str]:
        """列出所有 Page 名称"""
        result = self.extract()
        if result.success:
            return [p['name'] for p in result.pages]
        return []
    
    def get_page_summary(self, page_index: int = 0) -> Optional[Dict]:
        """获取 Page 摘要信息"""
        result = self.extract(page_index)
        if result.success and result.pages:
            page = result.pages[0]
            return {
                "name": page['name'],
                "width": page['width'],
                "height": page['height'],
                "layer_count": page['layer_count'],
                "hidden_count": page['hidden_count']
            }
        return None


# ============ 子模块 ============

class PageLister:
    """Page 列表器"""
    
    def __init__(self, parser: PSDParser):
        self.parser = parser
    
    def list(self) -> List[Dict]:
        """列出所有 Page"""
        document = self.parser.parse()
        return [
            {
                "index": p.index,
                "name": p.name,
                "width": p.width,
                "height": p.height
            }
            for p in document.pages
        ]


class PageSelector:
    """Page 选择器"""
    
    def __init__(self, parser: PSDParser):
        self.parser = parser
    
    def select(self, index: Optional[int] = None, name: Optional[str] = None) -> Optional[PageInfo]:
        """
        选择 Page
        
        Args:
            index: Page 索引
            name: Page 名称
        
        Returns:
            PageInfo 或 None
        """
        document = self.parser.parse()
        
        if index is not None:
            return document.get_page(index)
        
        if name is not None:
            for page in document.pages:
                if page.name == name:
                    return page
        
        return None


class PageExporter:
    """Page 导出器"""
    
    def __init__(self, parser: PSDParser):
        self.parser = parser
        self.logger = get_logger("page-exporter")
    
    def export(self, page_index: int, output_dir: str) -> str:
        """
        导出 Page 数据
        
        Returns:
            输出文件路径
        """
        import json
        
        document = self.parser.parse()
        page = document.get_page(page_index)
        
        if page is None:
            raise ValueError(f"Page {page_index} 不存在")
        
        output_path = Path(output_dir) / f"page_{page_index}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(page.to_dict(), f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Page 已导出: {output_path}")
        return str(output_path)


# ============ 便捷函数 ============

def extract_pages(file_path: str, page_index: Optional[int] = None) -> PageExtractResult:
    """提取 Page"""
    extractor = PageExtractor(file_path)
    return extractor.extract(page_index)
