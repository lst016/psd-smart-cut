"""
Level 1 - 测试文件
"""

import pytest
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from skills.psd_parser.level1_parse import (
    LayerInfo, PageInfo, PSDDocument,
    LayerFilter
)


class TestLayerInfo:
    """LayerInfo 数据类测试"""
    
    def test_layer_creation(self):
        layer = LayerInfo(
            id="layer_0",
            name="Test Layer",
            kind="image",
            visible=True,
            locked=False,
            left=0, top=0, right=100, bottom=100,
            width=100, height=100
        )
        
        assert layer.id == "layer_0"
        assert layer.name == "Test Layer"
        assert layer.kind == "image"
        assert layer.visible == True
        assert layer.locked == False
    
    def test_layer_bounds(self):
        layer = LayerInfo(
            id="layer_1",
            name="Test",
            kind="image",
            visible=True,
            locked=False,
            left=10, top=20, right=110, bottom=120,
            width=100, height=100
        )
        
        assert layer.bounds == (10, 20, 110, 120)
    
    def test_layer_area(self):
        layer = LayerInfo(
            id="layer_2",
            name="Test",
            kind="image",
            visible=True,
            locked=False,
            left=0, top=0, right=100, bottom=100,
            width=100, height=100
        )
        
        assert layer.area == 10000
    
    def test_is_group(self):
        layer = LayerInfo(
            id="group_0",
            name="Group",
            kind="group",
            visible=True,
            locked=False,
            left=0, top=0, right=100, bottom=100,
            width=100, height=100
        )
        
        assert layer.is_group == True
        assert layer.kind == "group"
    
    def test_is_hidden(self):
        visible_layer = LayerInfo(
            id="layer_3",
            name="Visible",
            kind="image",
            visible=True,
            locked=False,
            left=0, top=0, right=100, bottom=100,
            width=100, height=100
        )
        
        hidden_layer = LayerInfo(
            id="layer_4",
            name="Hidden",
            kind="image",
            visible=False,
            locked=False,
            left=0, top=0, right=100, bottom=100,
            width=100, height=100
        )
        
        assert visible_layer.is_hidden == False
        assert hidden_layer.is_hidden == True
    
    def test_to_dict(self):
        layer = LayerInfo(
            id="layer_5",
            name="Test",
            kind="image",
            visible=True,
            locked=False,
            left=0, top=0, right=100, bottom=100,
            width=100, height=100
        )
        
        d = layer.to_dict()
        assert isinstance(d, dict)
        assert d['id'] == "layer_5"
        assert d['name'] == "Test"


class TestPageInfo:
    """PageInfo 数据类测试"""
    
    def test_page_creation(self):
        page = PageInfo(
            index=0,
            name="Page 1",
            width=1920,
            height=1080
        )
        
        assert page.index == 0
        assert page.name == "Page 1"
        assert page.width == 1920
        assert page.height == 1080
        assert page.layer_count == 0
    
    def test_page_with_layers(self):
        page = PageInfo(
            index=0,
            name="Page 1",
            width=1920,
            height=1080,
            layers=[
                LayerInfo(
                    id="layer_0",
                    name="Layer 1",
                    kind="image",
                    visible=True,
                    locked=False,
                    left=0, top=0, right=100, bottom=100,
                    width=100, height=100
                ),
                LayerInfo(
                    id="layer_1",
                    name="Layer 2",
                    kind="text",
                    visible=False,
                    locked=False,
                    left=0, top=0, right=50, bottom=50,
                    width=50, height=50
                )
            ]
        )
        
        assert page.layer_count == 2
        assert page.hidden_count == 1


class TestLayerFilter:
    """LayerFilter 枚举测试"""
    
    def test_filter_values(self):
        assert LayerFilter.ALL.value == "all"
        assert LayerFilter.VISIBLE.value == "visible"
        assert LayerFilter.HIDDEN.value == "hidden"
        assert LayerFilter.LOCKED.value == "locked"
        assert LayerFilter.IMAGES.value == "images"


class TestHierarchyBuilder:
    """层级树构建器测试"""
    
    def test_simple_hierarchy(self):
        from skills.psd_parser.level1_parse.hierarchy_builder import HierarchyBuilder
        
        layers = [
            LayerInfo(
                id="root_1",
                name="Root 1",
                kind="group",
                visible=True,
                locked=False,
                left=0, top=0, right=100, bottom=100,
                width=100, height=100,
                parent_id=None
            ),
            LayerInfo(
                id="child_1",
                name="Child 1",
                kind="image",
                visible=True,
                locked=False,
                left=0, top=0, right=50, bottom=50,
                width=50, height=50,
                parent_id="root_1"
            )
        ]
        
        builder = HierarchyBuilder(layers)
        tree = builder.build()
        
        assert tree.total_nodes == 2
        assert len(tree.roots) == 1
        assert tree.roots[0].id == "root_1"
        assert len(tree.roots[0].children) == 1


class TestHiddenMarker:
    """隐藏标记器测试"""
    
    def test_mark_hidden_layers(self):
        from skills.psd_parser.level1_parse.hidden_marker import HiddenMarker
        
        layers = [
            LayerInfo(
                id="layer_0",
                name="Visible Layer",
                kind="image",
                visible=True,
                locked=False,
                left=0, top=0, right=100, bottom=100,
                width=100, height=100
            ),
            LayerInfo(
                id="layer_1",
                name="Hidden Layer",
                kind="image",
                visible=False,
                locked=False,
                left=0, top=0, right=100, bottom=100,
                width=100, height=100
            )
        ]
        
        marker = HiddenMarker(layers)
        result = marker.mark()
        
        assert result.success == True
        assert result.total_layers == 2
        assert result.visible_count == 1
        assert result.hidden_count == 1


class TestLockedDetector:
    """锁定检测器测试"""
    
    def test_detect_locked_layers(self):
        from skills.psd_parser.level1_parse.locked_detector import LockedDetector
        
        layers = [
            LayerInfo(
                id="layer_0",
                name="Unlocked Layer",
                kind="image",
                visible=True,
                locked=False,
                left=0, top=0, right=100, bottom=100,
                width=100, height=100
            ),
            LayerInfo(
                id="layer_1",
                name="Locked Layer",
                kind="image",
                visible=True,
                locked=True,
                left=0, top=0, right=100, bottom=100,
                width=100, height=100
            )
        ]
        
        detector = LockedDetector(layers)
        result = detector.detect()
        
        assert result.success == True
        assert result.total_layers == 2
        assert result.locked_count == 1
        assert result.unlocked_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
