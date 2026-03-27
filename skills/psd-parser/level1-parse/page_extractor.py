"""
Level 1 - Page Extractor
鎻愬彇 PSD 涓殑 Page 淇℃伅
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from skills.common import get_logger, get_error_handler, ErrorCategory
from skills.psd_parser.level1_parse.psd_parser import PSDParser, PageInfo


@dataclass
class PageExtractResult:
    """Page 鎻愬彇缁撴灉"""
    success: bool
    page_count: int
    pages: List[Dict] = field(default_factory=list)
    default_page_index: int = 0
    error: Optional[str] = None

    @property
    def total_pages(self) -> int:
        return self.page_count


class PageExtractor:
    """
    Page 鎻愬彇鍣?
    鑱岃矗锛氬垪鍑烘墍鏈?Page锛屾彁鍙?Page 鍩烘湰淇℃伅
    """

    def __init__(self, file_path: str = ""):
        self.file_path = Path(file_path)
        self.logger = get_logger("page-extractor")
        self.error_handler = get_error_handler()
        self.parser: Optional[PSDParser] = None

    def _load_document(self, source: Optional[Any] = None):
        """Support both PSDDocument objects and file-path based parsing."""
        if source is not None and hasattr(source, "pages"):
            return source

        file_path = source or str(self.file_path)
        if not file_path:
            raise ValueError("file_path is required when no PSDDocument is provided")

        self.parser = PSDParser(str(file_path))
        return self.parser.parse()

    def extract(
        self,
        source_or_page_index: Optional[Any] = None,
        page_index: Optional[int] = None
    ) -> PageExtractResult:
        """
        鎻愬彇 Page 淇℃伅

        Args:
            page_index: 鎸囧畾 Page 绱㈠紩锛孨one 琛ㄧず鎵€鏈?Page

        Returns:
            PageExtractResult: 鎻愬彇缁撴灉
        """
        source = source_or_page_index
        if isinstance(source_or_page_index, int) and page_index is None:
            page_index = source_or_page_index
            source = None

        self.logger.info(f"寮€濮嬫彁鍙?Page: {source or self.file_path}")

        try:
            document = self._load_document(source)

            if page_index is not None:
                page = document.get_page(page_index)
                if page is None:
                    return PageExtractResult(
                        success=False,
                        page_count=0,
                        error=f"Page {page_index} does not exist"
                    )
                pages = [page.to_dict()]
            else:
                pages = [p.to_dict() for p in document.pages]

            result = PageExtractResult(
                success=True,
                page_count=len(pages),
                pages=pages,
                default_page_index=0
            )

            self.logger.info(f"Page 鎻愬彇瀹屾垚: {result.page_count} pages")
            return result

        except Exception as e:
            error_msg = f"Page 鎻愬彇澶辫触: {str(e)}"
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
        """鍒楀嚭鎵€鏈?Page 鍚嶇О"""
        result = self.extract()
        if result.success:
            return [p['name'] for p in result.pages]
        return []

    def get_page_summary(self, page_index: int = 0) -> Optional[Dict]:
        """鑾峰彇 Page 鎽樿淇℃伅"""
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


# ============ 瀛愭ā鍧?============

class PageLister:
    """Page 鍒楄〃鍣?"""

    def __init__(self, parser: PSDParser):
        self.parser = parser

    def list(self) -> List[Dict]:
        """鍒楀嚭鎵€鏈?Page"""
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
    """Page 閫夋嫨鍣?"""

    def __init__(self, parser: PSDParser):
        self.parser = parser

    def select(self, index: Optional[int] = None, name: Optional[str] = None) -> Optional[PageInfo]:
        """
        閫夋嫨 Page

        Args:
            index: Page 绱㈠紩
            name: Page 鍚嶇О

        Returns:
            PageInfo 鎴?None
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
    """Page 瀵煎嚭鍣?"""

    def __init__(self, parser: PSDParser):
        self.parser = parser
        self.logger = get_logger("page-exporter")

    def export(self, page_index: int, output_dir: str) -> str:
        """
        瀵煎嚭 Page 鏁版嵁

        Returns:
            杈撳嚭鏂囦欢璺緞
        """
        import json

        document = self.parser.parse()
        page = document.get_page(page_index)

        if page is None:
            raise ValueError(f"Page {page_index} does not exist")

        output_path = Path(output_dir) / f"page_{page_index}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(page.to_dict(), f, ensure_ascii=False, indent=2)

        self.logger.info(f"Page 宸插鍑? {output_path}")
        return str(output_path)


# ============ 渚挎嵎鍑芥暟 ============

def extract_pages(file_path: str, page_index: Optional[int] = None) -> PageExtractResult:
    """鎻愬彇 Page"""
    extractor = PageExtractor(file_path)
    return extractor.extract(page_index)
