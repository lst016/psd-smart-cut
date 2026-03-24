"""
Level 6 - Position Reader
位置读取器 - 从 PSD 提取图层位置和尺寸信息
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from skills.common import get_logger, get_error_handler, ErrorCategory, ErrorSeverity


class AnchorPoint(Enum):
    """锚点位置枚举"""
    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    CENTER_LEFT = "center_left"
    CENTER = "center"
    CENTER_RIGHT = "center_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"


class Alignment(Enum):
    """对齐方式枚举"""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"
    TOP = "top"
    BOTTOM = "bottom"


@dataclass
class ResponsiveBreakpoint:
    """响应式断点数据类"""
    name: str           # 断点名称 (mobile/tablet/desktop/wide)
    min_width: float    # 最小宽度
    max_width: float    # 最大宽度
    scale_factor: float # 缩放因子
    description: str    # 描述


@dataclass
class PositionData:
    """位置数据类"""
    x: float          # 左上角 X
    y: float          # 左上角 Y
    width: float      # 宽度
    height: float     # 高度
    right: float      # 右下角 X
    bottom: float     # 右下角 Y
    center_x: float   # 中心 X
    center_y: float   # 中心 Y
    is_visible: bool  # 是否可见
    is_locked: bool   # 是否锁定
    rotation: float   # 旋转角度（度）
    bounding_box: Dict = field(default_factory=dict)
    breakpoints: List['ResponsiveBreakpoint'] = field(default_factory=list)
    anchor: AnchorPoint = AnchorPoint.TOP_LEFT
    alignment: Alignment = Alignment.LEFT


# 别名兼容
PositionInfo = PositionData


class PositionReader:
    """位置读取器 - 从 PSD 提取图层位置和尺寸"""
    
    def __init__(self, canvas_width: int = 1440, canvas_height: int = 900):
        self.logger = get_logger("PositionReader")
        self.error_handler = get_error_handler()
        self._mock_mode = True
        self._canvas_width = canvas_width
        self._canvas_height = canvas_height
    
    def read(self, layer_info: Dict) -> PositionData:
        """
        读取单个图层的位置信息
        
        Args:
            layer_info: 图层信息字典
            
        Returns:
            PositionData
        """
        try:
            # 获取边界信息
            bbox = self._extract_bbox(layer_info)
            
            # 获取位置
            x = bbox.get('x', bbox.get('left', 0))
            y = bbox.get('y', bbox.get('top', 0))
            width = bbox.get('width', 0)
            height = bbox.get('height', 0)
            
            # 计算其他边界
            right = x + width
            bottom = y + height
            center_x = x + width / 2
            center_y = y + height / 2
            
            # 获取可见性
            is_visible = layer_info.get('visible', True)
            is_locked = layer_info.get('locked', False)
            
            # 获取旋转角度
            rotation = self._extract_rotation(layer_info)
            
            return PositionData(
                x=x,
                y=y,
                width=width,
                height=height,
                right=right,
                bottom=bottom,
                center_x=center_x,
                center_y=center_y,
                is_visible=is_visible,
                is_locked=is_locked,
                rotation=rotation,
                bounding_box=bbox
            )
            
        except Exception as e:
            self.error_handler.record(
                task="PositionReader.read",
                error=e,
                category=ErrorCategory.PARSE_ERROR,
                severity=ErrorSeverity.MEDIUM,
                context={"layer_id": layer_info.get('id', 'unknown')}
            )
            return self._create_mock_position(layer_info)
    
    def read_batch(self, layers: List[Dict]) -> List[PositionData]:
        """
        批量读取图层位置信息
        
        Args:
            layers: 图层信息列表
            
        Returns:
            位置数据列表
        """
        results = []
        
        for layer in layers:
            position = self.read(layer)
            results.append(position)
        
        self.logger.info(f"批量读取位置: {len(results)}/{len(layers)} 个图层")
        
        return results
    
    def _extract_bbox(self, layer_info: Dict) -> Dict:
        """提取边界框信息"""
        # 优先从 bbox/bounds 获取
        if 'bbox' in layer_info:
            return layer_info['bbox']
        if 'bounds' in layer_info:
            return layer_info['bounds']
        
        # 从单独的字段获取
        bbox = {
            'left': layer_info.get('left', 0),
            'top': layer_info.get('top', 0),
            'right': layer_info.get('right', 0),
            'bottom': layer_info.get('bottom', 0),
        }
        
        # 计算宽高
        bbox['x'] = bbox['left']
        bbox['y'] = bbox['top']
        bbox['width'] = bbox['right'] - bbox['left']
        bbox['height'] = bbox['bottom'] - bbox['top']
        
        return bbox
    
    def _extract_rotation(self, layer_info: Dict) -> float:
        """提取旋转角度"""
        rotation = layer_info.get('rotation', 0)
        if 'transform' in layer_info:
            transform = layer_info['transform']
            if isinstance(transform, list) and len(transform) >= 6:
                rotation = 0
        return rotation
    
    def get_bounds(self, layer_info: Dict) -> Tuple[float, float, float, float]:
        """获取边界 (left, top, right, bottom)"""
        position = self.read(layer_info)
        return (position.x, position.y, position.right, position.bottom)
    
    def get_dimensions(self, layer_info: Dict) -> Tuple[float, float]:
        """获取尺寸 (width, height)"""
        position = self.read(layer_info)
        return (position.width, position.height)
    
    def get_center(self, layer_info: Dict) -> Tuple[float, float]:
        """获取中心点 (center_x, center_y)"""
        position = self.read(layer_info)
        return (position.center_x, position.center_y)
    
    def is_in_bounds(self, position: PositionData, canvas_width: float, canvas_height: float) -> bool:
        """检查位置是否在画布边界内"""
        return (
            0 <= position.x < canvas_width and
            0 <= position.y < canvas_height and
            0 < position.right <= canvas_width and
            0 < position.bottom <= canvas_height
        )
    
    def is_overlapping(self, pos1: PositionData, pos2: PositionData) -> bool:
        """检查两个图层是否重叠"""
        return not (
            pos1.right <= pos2.x or
            pos1.x >= pos2.right or
            pos1.bottom <= pos2.y or
            pos1.y >= pos2.bottom
        )
    
    def calculate_overlap_area(self, pos1: PositionData, pos2: PositionData) -> float:
        """计算重叠区域面积"""
        if not self.is_overlapping(pos1, pos2):
            return 0.0
        overlap_left = max(pos1.x, pos2.x)
        overlap_top = max(pos1.y, pos2.y)
        overlap_right = min(pos1.right, pos2.right)
        overlap_bottom = min(pos1.bottom, pos2.bottom)
        overlap_width = overlap_right - overlap_left
        overlap_height = overlap_bottom - overlap_top
        return overlap_width * overlap_height
    
    def get_distance_to(self, pos1: PositionData, pos2: PositionData) -> float:
        """计算两个图层中心点之间的距离"""
        dx = pos1.center_x - pos2.center_x
        dy = pos1.center_y - pos2.center_y
        return (dx ** 2 + dy ** 2) ** 0.5
    
    def _create_mock_position(self, layer_info: Dict) -> PositionData:
        """创建 Mock 位置信息（用于测试）"""
        import hashlib
        
        layer_id = layer_info.get('id', 'unknown')
        layer_name = layer_info.get('name', 'Layer')
        
        hash_val = int(hashlib.md5(layer_id.encode()).hexdigest(), 16)
        
        x = float((hash_val >> 24) & 0xFF) * 10
        y = float((hash_val >> 16) & 0xFF) * 10
        width = float((hash_val >> 8) & 0xFF) * 2 + 50
        height = float(hash_val & 0xFF) * 2 + 30
        
        right = x + width
        bottom = y + height
        center_x = x + width / 2
        center_y = y + height / 2
        
        is_visible = 'hidden' not in layer_name.lower() and 'hide' not in layer_name.lower()
        is_locked = 'locked' in layer_name.lower() or 'lock' in layer_name.lower()
        
        return PositionData(
            x=x,
            y=y,
            width=width,
            height=height,
            right=right,
            bottom=bottom,
            center_x=center_x,
            center_y=center_y,
            is_visible=is_visible,
            is_locked=is_locked,
            rotation=0.0,
            bounding_box={
                'x': x, 'y': y,
                'width': width, 'height': height,
                'left': x, 'top': y, 'right': right, 'bottom': bottom
            }
        )
