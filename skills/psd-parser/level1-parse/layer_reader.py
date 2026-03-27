"""
Level 1 - Layer Reader
璇诲彇 PSD 涓殑 Layer 淇℃伅
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from skills.common import get_logger, get_error_handler, ErrorCategory
from skills.psd_parser.level1_parse.psd_parser import PSDParser, LayerInfo


class LayerFilter(Enum):
    """鍥惧眰杩囨护鍣?"""
    ALL = "all"
    VISIBLE = "visible"
    HIDDEN = "hidden"
    LOCKED = "locked"
    UNLOCKED = "unlocked"
    IMAGES = "images"
    TEXTS = "texts"
    VECTORS = "vectors"
    GROUPS = "groups"


@dataclass
class LayerReadResult:
    """Layer 璇诲彇缁撴灉"""
    success: bool
    layer_count: int
    layers: List[Dict] = field(default_factory=list)
    filter_applied: Optional[str] = None
    error: Optional[str] = None

    @property
    def total_layers(self) -> int:
        return self.layer_count

    @property
    def hidden_count(self) -> int:
        return sum(1 for layer in self.layers if not layer.get("visible", True))

    @property
    def visible_count(self) -> int:
        return sum(1 for layer in self.layers if layer.get("visible", True))


class LayerReader:
    """
    Layer 璇诲彇鍣?
    鑱岃矗锛氳鍙栨寚瀹?Page 鐨勬墍鏈夊浘灞?
    """

    def __init__(self, file_path: str = "", page_index: int = 0):
        self.file_path = Path(file_path)
        self.page_index = page_index
        self.logger = get_logger("layer-reader")
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

    def read(
        self,
        source_or_filter_type: Optional[Any] = None,
        filter_type: LayerFilter = LayerFilter.ALL
    ) -> LayerReadResult:
        """
        璇诲彇 Layer 淇℃伅

        Args:
            filter_type: 杩囨护绫诲瀷

        Returns:
            LayerReadResult: 璇诲彇缁撴灉
        """
        source = source_or_filter_type
        if isinstance(source_or_filter_type, LayerFilter):
            source = None
            filter_type = source_or_filter_type

        self.logger.info(f"寮€濮嬭鍙?Layer: {source or self.file_path}, page={self.page_index}")

        try:
            document = self._load_document(source)

            page = document.get_page(self.page_index)
            if page is None:
                return LayerReadResult(
                    success=False,
                    layer_count=0,
                    error=f"Page {self.page_index} does not exist"
                )

            layers = self._apply_filter(page.layers, filter_type)

            result = LayerReadResult(
                success=True,
                layer_count=len(layers),
                layers=[l.to_dict() for l in layers],
                filter_applied=filter_type.value
            )

            self.logger.info(f"Layer 璇诲彇瀹屾垚: {result.layer_count} layers (filter: {filter_type.value})")
            return result

        except Exception as e:
            error_msg = f"Layer 璇诲彇澶辫触: {str(e)}"
            self.logger.error(error_msg)
            self.error_handler.record(
                task="layer-reader",
                error=e,
                category=ErrorCategory.PARSE_ERROR
            )
            return LayerReadResult(
                success=False,
                layer_count=0,
                error=error_msg
            )

    def _apply_filter(self, layers: List[LayerInfo], filter_type: LayerFilter) -> List[LayerInfo]:
        """搴旂敤杩囨护鍣?"""
        if filter_type == LayerFilter.ALL:
            return layers
        elif filter_type == LayerFilter.VISIBLE:
            return [l for l in layers if l.visible]
        elif filter_type == LayerFilter.HIDDEN:
            return [l for l in layers if not l.visible]
        elif filter_type == LayerFilter.LOCKED:
            return [l for l in layers if l.locked]
        elif filter_type == LayerFilter.UNLOCKED:
            return [l for l in layers if not l.locked]
        elif filter_type == LayerFilter.IMAGES:
            return [l for l in layers if l.kind == "image"]
        elif filter_type == LayerFilter.TEXTS:
            return [l for l in layers if l.kind == "text"]
        elif filter_type == LayerFilter.VECTORS:
            return [l for l in layers if l.kind == "vector"]
        elif filter_type == LayerFilter.GROUPS:
            return [l for l in layers if l.kind == "group"]
        else:
            return layers

    def get_layer(self, layer_id: str) -> Optional[LayerInfo]:
        """鑾峰彇鎸囧畾 Layer"""
        result = self.read()
        if result.success:
            for layer_dict in result.layers:
                if layer_dict['id'] == layer_id:
                    return LayerInfo(**layer_dict)
        return None

    def get_layer_tree(self) -> Optional[Dict]:
        """鑾峰彇 Layer 鏍戝舰缁撴瀯"""
        result = self.read()
        if result.success:
            return self._build_tree(result.layers)
        return None

    def _build_tree(self, layers: List[Dict]) -> Dict:
        """鏋勫缓鏍戝舰缁撴瀯"""
        layer_map = {l['id']: {**l, 'children': []} for l in layers}
        roots = []

        for layer in layers:
            layer_node = layer_map[layer['id']]
            parent_id = layer.get('parent_id')

            if parent_id and parent_id in layer_map:
                layer_map[parent_id]['children'].append(layer_node)
            else:
                roots.append(layer_node)

        return {"roots": roots, "total": len(layers)}


# ============ 瀛愭ā鍧?============

class LayerLister:
    """Layer 鍒楄〃鍣?"""

    def __init__(self, page_info):
        self.page_info = page_info

    def list(self, include_hidden: bool = True) -> List[Dict]:
        """鍒楀嚭鎵€鏈?Layer"""
        layers = []
        for layer in self.page_info.layers:
            if include_hidden or layer.visible:
                layers.append(layer.to_dict())
        return layers

    def list_by_kind(self) -> Dict[str, List]:
        """鎸夌被鍨嬪垎缁勫垪鍑?"""
        groups = {}
        for layer in self.page_info.layers:
            kind = layer.kind
            if kind not in groups:
                groups[kind] = []
            groups[kind].append(layer.to_dict())
        return groups


class LayerFilterModule:
    """Layer 杩囨护鍣?"""

    def __init__(self, layers: List[LayerInfo]):
        self.layers = layers

    def filter_by_size(self, min_width: int = 0, min_height: int = 0) -> List[LayerInfo]:
        """鎸夊昂瀵歌繃婊?"""
        return [
            l for l in self.layers
            if l.width >= min_width and l.height >= min_height
        ]

    def filter_by_name(self, pattern: str) -> List[LayerInfo]:
        """鎸夊悕绉拌繃婊わ紙鏀寔閫氶厤绗?*锛?"""
        import fnmatch
        return [l for l in self.layers if fnmatch.fnmatch(l.name.lower(), pattern.lower())]

    def filter_by_area(self, max_area: int = 1000000) -> List[LayerInfo]:
        """鎸夐潰绉繃婊?"""
        return [l for l in self.layers if l.area <= max_area]


class LayerMetadataReader:
    """Layer 鍏冩暟鎹鍙栧櫒"""

    def __init__(self, layer: LayerInfo):
        self.layer = layer

    def read_opacity(self) -> float:
        """璇诲彇涓嶉€忔槑搴?"""
        return self.layer.opacity

    def read_blend_mode(self) -> str:
        """璇诲彇娣峰悎妯″紡"""
        return self.layer.blend_mode

    def read_bbox(self) -> Dict:
        """璇诲彇杈圭晫妗?"""
        return self.layer.bbox

    def read_full_metadata(self) -> Dict:
        """璇诲彇瀹屾暣鍏冩暟鎹?"""
        return {
            "id": self.layer.id,
            "name": self.layer.name,
            "kind": self.layer.kind,
            "visible": self.layer.visible,
            "locked": self.layer.locked,
            "opacity": self.layer.opacity,
            "blend_mode": self.layer.blend_mode,
            "dimensions": {
                "width": self.layer.width,
                "height": self.layer.height
            },
            "position": {
                "left": self.layer.left,
                "top": self.layer.top,
                "right": self.layer.right,
                "bottom": self.layer.bottom
            },
            "bbox": self.layer.bbox,
            "parent_id": self.layer.parent_id,
            "children": self.layer.children
        }


# ============ 渚挎嵎鍑芥暟 ============

def read_layers(file_path: str, page_index: int = 0, filter_type: LayerFilter = LayerFilter.ALL) -> LayerReadResult:
    """璇诲彇 Layers"""
    reader = LayerReader(file_path, page_index)
    return reader.read(filter_type)
