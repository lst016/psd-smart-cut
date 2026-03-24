"""
Level 1 - Hierarchy Builder
构建图层层级树
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from skills.common import get_logger, get_error_handler, ErrorCategory
from skills.psd_parser.level1_parse.psd_parser import PSDParser, LayerInfo, PageInfo

@dataclass
class HierarchyNode:
    """层级树节点"""
    id: str
    name: str
    kind: str
    depth: int
    children: List['HierarchyNode'] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    parent_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind,
            "depth": self.depth,
            "children": [c.to_dict() for c in self.children],
            "metadata": self.metadata,
            "parent_id": self.parent_id
        }

@dataclass
class HierarchyTree:
    """层级树"""
    roots: List[HierarchyNode] = field(default_factory=list)
    total_nodes: int = 0
    max_depth: int = 0
    node_map: Dict[str, HierarchyNode] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "roots": [r.to_dict() for r in self.roots],
            "total_nodes": self.total_nodes,
            "max_depth": self.max_depth
        }
    
    def get_node(self, node_id: str) -> Optional[HierarchyNode]:
        return self.node_map.get(node_id)
    
    def get_ancestors(self, node_id: str) -> List[HierarchyNode]:
        """获取祖先节点"""
        ancestors = []
        node = self.get_node(node_id)
        while node and node.parent_id:
            parent = self.get_node(node.parent_id)
            if parent:
                ancestors.append(parent)
                node = parent
            else:
                break
        return ancestors
    
    def get_descendants(self, node_id: str) -> List[HierarchyNode]:
        """获取后代节点"""
        descendants = []
        node = self.get_node(node_id)
        if node:
            self._collect_descendants(node, descendants)
        return descendants
    
    def _collect_descendants(self, node: HierarchyNode, result: List):
        for child in node.children:
            result.append(child)
            self._collect_descendants(child, result)


class HierarchyBuilder:
    """
    层级树构建器
    职责：根据 Layer 列表构建层级树结构
    """
    
    def __init__(self, layers: List[LayerInfo]):
        self.layers = layers
        self.logger = get_logger("hierarchy-builder")
        self.error_handler = get_error_handler()
        self._node_map: Dict[str, HierarchyNode] = {}
        self._tree: Optional[HierarchyTree] = None
    
    def build(self) -> HierarchyTree:
        """构建层级树"""
        self.logger.info(f"开始构建层级树: {len(self.layers)} layers")
        
        try:
            # 第一遍：创建所有节点
            for layer in self.layers:
                self._create_node(layer)
            
            # 第二遍：建立父子关系
            for layer in self.layers:
                self._link_parent(layer)
            
            # 第三遍：构建根节点列表
            roots = []
            max_depth = 0
            for layer in self.layers:
                node = self._node_map[layer.id]
                if layer.parent_id is None:
                    roots.append(node)
                max_depth = max(max_depth, node.depth)
            
            self._tree = HierarchyTree(
                roots=roots,
                total_nodes=len(self.layers),
                max_depth=max_depth,
                node_map=self._node_map
            )
            
            self.logger.info(f"层级树构建完成: {self._tree.total_nodes} nodes, max_depth={max_depth}")
            return self._tree
            
        except Exception as e:
            self.logger.error(f"层级树构建失败: {e}")
            self.error_handler.record(
                task="hierarchy-builder",
                error=e,
                category=ErrorCategory.PARSE_ERROR
            )
            raise
    
    def _create_node(self, layer: LayerInfo):
        """创建节点"""
        node = HierarchyNode(
            id=layer.id,
            name=layer.name,
            kind=layer.kind,
            depth=self._calculate_depth(layer),
            metadata={
                "visible": layer.visible,
                "locked": layer.locked,
                "width": layer.width,
                "height": layer.height,
                "opacity": layer.opacity,
                "blend_mode": layer.blend_mode
            },
            parent_id=layer.parent_id
        )
        self._node_map[layer.id] = node
    
    def _calculate_depth(self, layer: LayerInfo) -> int:
        """计算节点深度"""
        depth = 0
        parent_id = layer.parent_id
        while parent_id and parent_id in self._node_map:
            depth += 1
            parent = self._node_map[parent_id]
            parent_id = parent.parent_id
        return depth
    
    def _link_parent(self, layer: LayerInfo):
        """建立父子链接"""
        if layer.parent_id and layer.parent_id in self._node_map:
            parent_node = self._node_map[layer.parent_id]
            child_node = self._node_map[layer.id]
            parent_node.children.append(child_node)
    
    def prune_empty_groups(self) -> HierarchyTree:
        """修剪空组"""
        if not self._tree:
            raise RuntimeError("请先调用 build()")
        
        pruned_roots = []
        for root in self._tree.roots:
            pruned = self._prune_node(root)
            if pruned:
                pruned_roots.append(pruned)
        
        self._tree.roots = pruned_roots
        return self._tree
    
    def _prune_node(self, node: HierarchyNode) -> Optional[HierarchyNode]:
        """递归修剪"""
        node.children = [
            child for child in node.children
            if self._prune_node(child)
        ]
        
        # 如果是组且没有子节点，检查是否应该保留
        if node.kind == "group" and len(node.children) == 0:
            # 保留空组（可能是隐藏的组）
            pass
        
        return node
    
    def get_subtree(self, node_id: str) -> Optional[HierarchyNode]:
        """获取子树"""
        node = self._node_map.get(node_id)
        return node
    
    def validate(self) -> bool:
        """验证树结构"""
        if not self._tree:
            return False
        
        # 检查根节点数量
        if len(self._tree.roots) == 0 and self._tree.total_nodes > 0:
            self.logger.warning("树没有根节点但有节点")
            return False
        
        # 检查父子关系一致性
        for node_id, node in self._tree.node_map.items():
            for child in node.children:
                if child.parent_id != node_id:
                    self.logger.error(f"父子关系不一致: {child.id}")
                    return False
        
        return True


# ============ 子模块 ============

class TreePruner:
    """树修剪器"""
    
    def __init__(self, tree: HierarchyTree):
        self.tree = tree
    
    def prune_by_size(self, min_size: int = 1) -> HierarchyTree:
        """按尺寸修剪"""
        for root in self.tree.roots:
            self._prune_node_by_size(root, min_size)
        return self.tree
    
    def _prune_node_by_size(self, node: HierarchyNode, min_size: int):
        node.children = [
            child for child in node.children
            if self._should_keep(child, min_size)
        ]
        for child in node.children:
            self._prune_node_by_size(child, min_size)
    
    def _should_keep(self, node: HierarchyNode, min_size: int) -> bool:
        w = node.metadata.get('width', 0)
        h = node.metadata.get('height', 0)
        return w >= min_size or h >= min_size


class TreeValidator:
    """树验证器"""
    
    def __init__(self, tree: HierarchyTree):
        self.tree = tree
        self.logger = get_logger("tree-validator")
    
    def validate(self) -> Dict[str, Any]:
        """验证树结构"""
        issues = []
        
        # 检查循环引用
        for node_id in self.tree.node_map:
            if self._has_cycle(node_id):
                issues.append(f"循环引用: {node_id}")
        
        # 检查孤立节点
        for node_id, node in self.tree.node_map.items():
            if node.parent_id and node.parent_id not in self.tree.node_map:
                issues.append(f"孤立节点: {node_id}")
        
        # 检查深度一致性
        for node_id, node in self.tree.node_map.items():
            expected_depth = self._calculate_depth(node_id)
            if node.depth != expected_depth:
                issues.append(f"深度不一致: {node_id}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "total_nodes": self.tree.total_nodes,
            "max_depth": self.tree.max_depth
        }
    
    def _has_cycle(self, node_id: str) -> bool:
        visited = set()
        current = node_id
        while current:
            if current in visited:
                return True
            visited.add(current)
            node = self.tree.node_map.get(current)
            current = node.parent_id if node else None
        return False
    
    def _calculate_depth(self, node_id: str) -> int:
        depth = 0
        node = self.tree.node_map.get(node_id)
        while node and node.parent_id:
            depth += 1
            node = self.tree.node_map.get(node.parent_id)
        return depth


def build_hierarchy(layers: List[LayerInfo]) -> HierarchyTree:
    """构建层级树"""
    builder = HierarchyBuilder(layers)
    return builder.build()
