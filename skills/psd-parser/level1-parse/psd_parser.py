"""
PSD Smart Cut - PSD 解析器
封装 psd-tools，提供统一的解析接口
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

# PSD 解析
try:
    from psd_tools import PSDImage
    from psd_tools.api.psd_image import PSDImage as PSDImageClass
    from psd_tools.api.layers import Layer
    PSD_AVAILABLE = True
except ImportError:
    PSD_AVAILABLE = False
    print("警告: psd-tools 未安装，请运行 pip install psd-tools")

from skills.common import get_logger, get_config, get_validator

# ============ 数据类 ============

class LayerType(Enum):
    """图层类型"""
    IMAGE = "image"
    TEXT = "text"
    VECTOR = "vector"
    GROUP = "group"
    DECORATOR = "decorator"
    UNKNOWN = "unknown"

@dataclass
class LayerInfo:
    """图层信息"""
    id: str
    name: str
    kind: str
    visible: bool
    locked: bool
    left: int
    top: int
    right: int
    bottom: int
    width: int
    height: int
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    opacity: float = 1.0
    blend_mode: str = "normal"
    bbox: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @property
    def is_group(self) -> bool:
        return self.kind == "group"
    
    @property
    def is_hidden(self) -> bool:
        return not self.visible
    
    @property
    def bounds(self) -> Tuple[int, int, int, int]:
        return (self.left, self.top, self.right, self.bottom)
    
    @property
    def area(self) -> int:
        return self.width * self.height


@dataclass
class PageInfo:
    """Page 信息"""
    index: int
    name: str
    width: int
    height: int
    layers: List[LayerInfo] = field(default_factory=list)
    # 统计字段通过 layers 自动计算，不再存储
    _layer_count: int = field(default=0, repr=False)
    _hidden_count: int = field(default=0, repr=False)
    _locked_count: int = field(default=0, repr=False)
    
    @property
    def layer_count(self) -> int:
        return self._layer_count if self._layer_count > 0 else len(self.layers)
    
    @layer_count.setter
    def layer_count(self, value: int):
        self._layer_count = value
    
    @property
    def hidden_count(self) -> int:
        return self._hidden_count if self._hidden_count > 0 else sum(1 for l in self.layers if l.is_hidden)
    
    @hidden_count.setter
    def hidden_count(self, value: int):
        self._hidden_count = value
    
    @property
    def locked_count(self) -> int:
        return self._locked_count if self._locked_count > 0 else sum(1 for l in self.layers if l.locked)
    
    @locked_count.setter
    def locked_count(self, value: int):
        self._locked_count = value
    
    def to_dict(self) -> Dict:
        return {
            "index": self.index,
            "name": self.name,
            "width": self.width,
            "height": self.height,
            "layer_count": self.layer_count,
            "hidden_count": self.hidden_count,
            "locked_count": self.locked_count,
            "layers": [l.to_dict() for l in self.layers]
        }


@dataclass
class PSDDocument:
    """PSD 文档"""
    file_path: str
    version: str
    width: int
    height: int
    pages: List[PageInfo] = field(default_factory=list)
    total_layers: int = 0
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "file_path": self.file_path,
            "version": self.version,
            "width": self.width,
            "height": self.height,
            "total_layers": self.total_layers,
            "page_count": len(self.pages),
            "metadata": self.metadata,
            "pages": [p.to_dict() for p in self.pages]
        }
    
    def get_page(self, index: int) -> Optional[PageInfo]:
        """获取指定 page"""
        for page in self.pages:
            if page.index == index:
                return page
        return None
    
    def get_all_layers(self) -> List[LayerInfo]:
        """获取所有页面的图层"""
        layers = []
        for page in self.pages:
            layers.extend(page.layers)
        return layers

# ============ PSD 解析器 ============

class PSDParser:
    """PSD 解析器"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.logger = get_logger("psd-parser")
        self.config = get_config()
        self.validator = get_validator()
        self._psd: Optional[PSDImageClass] = None
        self._document: Optional[PSDDocument] = None
        
        if not PSD_AVAILABLE:
            raise ImportError("psd-tools 未安装")
    
    def parse(self) -> PSDDocument:
        """解析 PSD 文件"""
        self.logger.info(f"开始解析 PSD: {self.file_path}")
        
        # 验证文件
        result = self.validator.validate_psd(str(self.file_path))
        if not result.valid:
            raise ValueError(f"PSD 文件验证失败: {result.errors}")
        
        try:
            self._psd = PSDImage.open(self.file_path)
            self._document = self._build_document()
            self.logger.info(f"解析完成: {len(self._document.pages)} pages, {self._document.total_layers} layers")
            return self._document
        except Exception as e:
            self.logger.error(f"解析失败: {e}")
            raise
    
    def _build_document(self) -> PSDDocument:
        """构建文档对象"""
        if self._psd is None:
            raise RuntimeError("PSD 未加载")
        
        # PSD 没有多 page 概念，创建一个默认 page
        page = PageInfo(
            index=0,
            name=self._psd.name or self.file_path.stem,
            width=self._psd.width,
            height=self._psd.height,
            layers=[]
        )
        
        # 递归解析图层
        layer_id = 0
        for layer in self._psd:
            layer_info = self._parse_layer(layer, parent_id=None, page=page)
            page.layers.append(layer_info)
            layer_id += 1
        
        page.layer_count = len(page.layers)
        page.hidden_count = sum(1 for l in page.layers if l.is_hidden)
        
        document = PSDDocument(
            file_path=str(self.file_path),
            version=str(self._psd.version),
            width=self._psd.width,
            height=self._psd.height,
            pages=[page],
            total_layers=page.layer_count,
            metadata={
                "parsed_at": self._get_timestamp(),
                "psd_tools_version": self._get_psd_tools_version()
            }
        )
        
        return document
    
    def _parse_layer(self, layer: Layer, parent_id: Optional[str], page: PageInfo, depth: int = 0) -> LayerInfo:
        """递归解析图层"""
        layer_id = f"layer_{page.layer_count}"
        page.layer_count += 1
        
        # 获取图层基本信息
        name = layer.name or f"unnamed_layer_{page.layer_count}"
        kind = self._get_layer_kind(layer)
        visible = layer.visible if hasattr(layer, 'visible') else True
        locked = layer.locked if hasattr(layer, 'locked') else False
        
        # 获取边界
        left, top, right, bottom = layer.bbox
        width = right - left
        height = bottom - top
        
        # 获取混合模式和不透明度
        opacity = 1.0
        blend_mode = "normal"
        if hasattr(layer, 'opacity'):
            opacity = layer.opacity / 255.0 if layer.opacity > 1 else layer.opacity
        if hasattr(layer, 'blend_mode'):
            blend_mode = str(layer.blend_mode)
        
        layer_info = LayerInfo(
            id=layer_id,
            name=name,
            kind=kind,
            visible=visible,
            locked=locked,
            left=left,
            top=top,
            right=right,
            bottom=bottom,
            width=width,
            height=height,
            parent_id=parent_id,
            opacity=opacity,
            blend_mode=blend_mode,
            bbox={"x": left, "y": top, "width": width, "height": height}
        )
        
        # 处理组
        if hasattr(layer, '__iter__'):
            for child in layer:
                child_info = self._parse_layer(child, parent_id=layer_id, page=page, depth=depth + 1)
                page.layers.append(child_info)
                layer_info.children.append(child_info.id)
        
        return layer_info
    
    def _get_layer_kind(self, layer: Layer) -> str:
        """获取图层类型"""
        if hasattr(layer, 'is_group') and layer.is_group():
            return "group"
        elif hasattr(layer, 'is_pixels') and layer.is_pixels():
            return "image"
        elif hasattr(layer, 'is_text') and layer.is_text():
            return "text"
        elif hasattr(layer, 'is_vector') and layer.is_vector():
            return "vector"
        else:
            return "unknown"
    
    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _get_psd_tools_version(self) -> str:
        try:
            import psd_tools
            return psd_tools.__version__
        except:
            return "unknown"
    
    def get_page_count(self) -> int:
        """获取页面数量"""
        return len(self._document.pages) if self._document else 0
    
    def get_layer_count(self) -> int:
        """获取图层总数"""
        return self._document.total_layers if self._document else 0
    
    def export_to_json(self, output_path: Optional[str] = None) -> str:
        """导出为 JSON"""
        if not self._document:
            raise RuntimeError("请先调用 parse()")
        
        if output_path is None:
            output_path = str(self.file_path.with_suffix('.json'))
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self._document.to_dict(), f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"已导出 JSON: {output_path}")
        return output_path

# ============ 便捷函数 ============

def parse_psd(file_path: str) -> PSDDocument:
    """解析 PSD 文件"""
    parser = PSDParser(file_path)
    return parser.parse()
