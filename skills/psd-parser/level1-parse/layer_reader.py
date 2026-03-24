"""
Level 1 - Layer Reader
读取 PSD 中的 Layer 信息
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from skills.common import get_logger, get_error_handler, ErrorCategory
from skills.psd_parser.level1_parse.psd_parser import PSDParser, LayerInfo

class LayerFilter(Enum):
    """图层过滤器"""
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
    """Layer 读取结果"""
    success: bool
    layer_count: int
    layers: List[Dict] = field(default_factory=list)
    filter_applied: Optional[str] = None
    error: Optional[str] = None

class LayerReader:
    """
    Layer 读取器
    职责：读取指定 Page 的所有图层
    """
    
    def __init__(self, file_path: str, page_index: int = 0):
        self.file_path = Path(file_path)
        self.page_index = page_index
        self.logger = get_logger("layer-reader")
        self.error_handler = get_error_handler()
        self.parser: Optional[PSDParser] = None
    
    def read(self, filter_type: LayerFilter = LayerFilter.ALL) -> LayerReadResult:
        """
        读取 Layer 信息
        
        Args:
            filter_type: 过滤类型
        
        Returns:
            LayerReadResult: 读取结果
        """
        self.logger.info(f"开始读取 Layer: {self.file_path}, page={self.page_index}")
        
        try:
            # 解析 PSD
            self.parser = PSDParser(str(self.file_path))
            document = self.parser.parse()
            
            page = document.get_page(self.page_index)
            if page is None:
                return LayerReadResult(
                    success=False,
                    layer_count=0,
                    error=f"Page {self.page_index} 不存在"
                )
            
            # 应用过滤器
            layers = self._apply_filter(page.layers, filter_type)
            
            result = LayerReadResult(
                success=True,
                layer_count=len(layers),
                layers=[l.to_dict() for l in layers],
                filter_applied=filter_type.value
            )
            
            self.logger.info(f"Layer 读取完成: {result.layer_count} layers (filter: {filter_type.value})")
            return result
            
        except Exception as e:
            error_msg = f"Layer 读取失败: {str(e)}"
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
        """应用过滤器"""
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
        """获取指定 Layer"""
        result = self.read()
        if result.success:
            for layer_dict in result.layers:
                if layer_dict['id'] == layer_id:
                    return LayerInfo(**layer_dict)
        return None
    
    def get_layer_tree(self) -> Optional[Dict]:
        """获取 Layer 树形结构"""
        result = self.read()
        if result.success:
            return self._build_tree(result.layers)
        return None
    
    def _build_tree(self, layers: List[Dict]) -> Dict:
        """构建树形结构"""
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


# ============ 子模块 ============

class LayerLister:
    """Layer 列表器"""
    
    def __init__(self, page_info):
        self.page_info = page_info
    
    def list(self, include_hidden: bool = True) -> List[Dict]:
        """列出所有 Layer"""
        layers = []
        for layer in self.page_info.layers:
            if include_hidden or layer.visible:
                layers.append(layer.to_dict())
        return layers
    
    def list_by_kind(self) -> Dict[str, List]:
        """按类型分组列出"""
        groups = {}
        for layer in self.page_info.layers:
            kind = layer.kind
            if kind not in groups:
                groups[kind] = []
            groups[kind].append(layer.to_dict())
        return groups


class LayerFilterModule:
    """Layer 过滤器"""
    
    def __init__(self, layers: List[LayerInfo]):
        self.layers = layers
    
    def filter_by_size(self, min_width: int = 0, min_height: int = 0) -> List[LayerInfo]:
        """按尺寸过滤"""
        return [
            l for l in self.layers
            if l.width >= min_width and l.height >= min_height
        ]
    
    def filter_by_name(self, pattern: str) -> List[LayerInfo]:
        """按名称过滤（支持通配符 *）"""
        import fnmatch
        return [l for l in self.layers if fnmatch.fnmatch(l.name.lower(), pattern.lower())]
    
    def filter_by_area(self, max_area: int = 1000000) -> List[LayerInfo]:
        """按面积过滤"""
        return [l for l in self.layers if l.area <= max_area]


class LayerMetadataReader:
    """Layer 元数据读取器"""
    
    def __init__(self, layer: LayerInfo):
        self.layer = layer
    
    def read_opacity(self) -> float:
        """读取不透明度"""
        return self.layer.opacity
    
    def read_blend_mode(self) -> str:
        """读取混合模式"""
        return self.layer.blend_mode
    
    def read_bbox(self) -> Dict:
        """读取边界框"""
        return self.layer.bbox
    
    def read_full_metadata(self) -> Dict:
        """读取完整元数据"""
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


# ============ 便捷函数 ============

def read_layers(file_path: str, page_index: int = 0, filter_type: LayerFilter = LayerFilter.ALL) -> LayerReadResult:
    """读取 Layers"""
    reader = LayerReader(file_path, page_index)
    return reader.read(filter_type)
