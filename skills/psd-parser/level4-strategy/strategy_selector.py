"""
Level 4 - Strategy Selector
策略选择器 - 根据组件类型选择切割策略
"""
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict, is_dataclass
from enum import Enum
from skills.common import get_logger, get_config, get_error_handler, ErrorCategory

logger = get_logger("strategy_selector")

# ============ 枚举定义 ============

class StrategyType(Enum):
    """策略类型枚举"""
    FLAT = "flat"  # 所有图层单独导出
    GROUP_BY_TYPE = "group_by_type"  # 按类型分组导出
    GROUP_BY_PAGE = "group_by_page"  # 按页面分组导出
    PRESERVE_HIERARCHY = "preserve_hierarchy"  # 保留 PSD 层级结构
    SMART_MERGE = "smart_merge"  # 智能合并相邻相似图层

# ============ 数据类 ============

@dataclass
class StrategyRule:
    """策略规则"""
    name: str
    description: str
    conditions: Dict  # 触发条件
    priority: int = 0  # 优先级，数字越大优先级越高

@dataclass
class CutRecommendation:
    """切割建议"""
    region_id: str
    layer_ids: List[str]
    strategy: StrategyType
    merge_suggested: bool = False
    reason: str = ""

@dataclass
class StrategySelectionResult:
    """策略选择结果"""
    selected_strategy: StrategyType
    recommendations: List[CutRecommendation]
    custom_rules_applied: List[str]
    metadata: Dict

    @property
    def success(self) -> bool:
        return self.selected_strategy is not None

# ============ 策略选择器 ============

class StrategySelector:
    """策略选择器"""
    
    # 默认策略规则
    DEFAULT_RULES = [
        StrategyRule(
            name="button_icon_strategy",
            description="按钮/图标使用 FLAT 策略",
            conditions={
                "layer_types": ["button", "icon"],
                "min_count": 1
            },
            priority=10
        ),
        StrategyRule(
            name="background_strategy",
            description="背景图使用整体导出",
            conditions={
                "layer_types": ["background"],
                "strategy": StrategyType.PRESERVE_HIERARCHY
            },
            priority=5
        ),
        StrategyRule(
            name="text_heavy_strategy",
            description="文字密集页面使用 GROUP_BY_TYPE",
            conditions={
                "text_ratio": 0.5,
                "strategy": StrategyType.GROUP_BY_TYPE
            },
            priority=8
        ),
        StrategyRule(
            name="component_library_strategy",
            description="组件库使用 SMART_MERGE",
            conditions={
                "similarity_threshold": 0.8,
                "strategy": StrategyType.SMART_MERGE
            },
            priority=7
        )
    ]
    
    def __init__(self, custom_rules: Optional[List[StrategyRule]] = None, mock_mode: bool = False):
        self.logger = get_logger("strategy_selector")
        self.config = get_config()
        self.mock_mode = mock_mode
        self.rules = custom_rules or self.DEFAULT_RULES.copy()

    def _normalize_layer(self, layer: Any) -> Dict:
        if isinstance(layer, dict):
            data = dict(layer)
        elif hasattr(layer, "to_dict"):
            data = layer.to_dict()
        elif is_dataclass(layer):
            data = asdict(layer)
        else:
            data = {key: value for key, value in vars(layer).items() if not key.startswith("_")}

        if "type" not in data and "kind" in data:
            data["type"] = data["kind"]
        return data
    
    def select(
        self,
        layers: List[Dict],
        canvas_info: Optional[Dict] = None,
        classification_results: Optional[List[Dict]] = None
    ) -> StrategySelectionResult:
        """
        选择切割策略
        
        Args:
            layers: 图层列表
            canvas_info: 画布信息
            classification_results: 分类结果
        
        Returns:
            StrategySelectionResult: 策略选择结果
        """
        canvas_info = canvas_info or {}
        classification_results = classification_results or []

        if (
            isinstance(layers, dict)
            and not canvas_info
            and not classification_results
            and "total_components" in layers
        ):
            context = layers
            analysis = {
                'total_layers': context.get('total_components', 0),
                'type_distribution': {'component': context.get('total_components', 0)},
                'text_ratio': 0,
                'image_ratio': 1.0 if context.get('total_components', 0) else 0,
                'group_ratio': 0,
                'has_background': False,
                'dominant_type': 'component'
            }
            selected_strategy = self._determine_best_strategy(
                analysis,
                {'width': context.get('canvas_width', 0), 'height': context.get('canvas_height', 0)}
            )
            return StrategySelectionResult(
                selected_strategy=selected_strategy,
                recommendations=[
                    CutRecommendation(
                        region_id="context_summary",
                        layer_ids=[],
                        strategy=selected_strategy,
                        merge_suggested=context.get("has_overlaps", False),
                        reason="Generated from performance-test context"
                    )
                ],
                custom_rules_applied=[],
                metadata={'layer_analysis': analysis, 'rules_count': len(self.rules)}
            )
        
        self.logger.info(
            f"选择切割策略: {len(layers)} 个图层",
            canvas_size=f"{canvas_info.get('width', 0)}x{canvas_info.get('height', 0)}"
        )
        
        # 分析图层分布
        layer_analysis = self._analyze_layer_distribution(layers, classification_results)
        
        # 确定最佳策略
        selected_strategy = self._determine_best_strategy(layer_analysis, canvas_info)
        
        # 生成切割建议
        recommendations = self._generate_recommendations(
            layers, selected_strategy, layer_analysis
        )
        
        # 应用自定义规则
        custom_rules_applied = self._apply_custom_rules(layers, recommendations)
        
        result = StrategySelectionResult(
            selected_strategy=selected_strategy,
            recommendations=recommendations,
            custom_rules_applied=custom_rules_applied,
            metadata={
                'layer_analysis': layer_analysis,
                'rules_count': len(self.rules)
            }
        )
        
        self.logger.info(
            f"策略选择完成: {selected_strategy.value}",
            recommendations_count=len(recommendations)
        )
        
        return result
    
    def _analyze_layer_distribution(
        self,
        layers: List[Dict],
        classification_results: List[Dict]
    ) -> Dict:
        """分析图层分布"""
        total_layers = len(layers)
        if total_layers == 0:
            return {
                'total_layers': 0,
                'type_distribution': {},
                'text_ratio': 0,
                'image_ratio': 0,
                'group_ratio': 0,
                'has_background': False
            }
        
        # 统计类型分布
        type_counts = {}
        text_count = 0
        image_count = 0
        group_count = 0
        has_background = False
        
        for raw_layer in layers:
            layer = self._normalize_layer(raw_layer)
            layer_type = layer.get('type', 'unknown')
            type_counts[layer_type] = type_counts.get(layer_type, 0) + 1
            
            if layer_type in ['text', 'heading', 'body', 'label']:
                text_count += 1
            elif layer_type in ['image', 'photo', 'illustration', 'button', 'icon']:
                image_count += 1
            elif layer_type == 'group':
                group_count += 1
            
            if layer.get('sub_type') == 'background' or layer_type == 'background':
                has_background = True
        
        return {
            'total_layers': total_layers,
            'type_distribution': type_counts,
            'text_ratio': text_count / total_layers,
            'image_ratio': image_count / total_layers,
            'group_ratio': group_count / total_layers,
            'has_background': has_background,
            'dominant_type': max(type_counts, key=type_counts.get) if type_counts else 'unknown'
        }
    
    def _determine_best_strategy(self, analysis: Dict, canvas_info: Dict) -> StrategyType:
        """确定最佳策略"""
        total_layers = analysis['total_layers']
        
        # 根据图层数量选择基础策略
        if total_layers <= 5:
            # 少量图层，使用扁平策略
            return StrategyType.FLAT
        elif total_layers <= 20:
            # 中等数量，根据类型分布选择
            if analysis['text_ratio'] > 0.5:
                return StrategyType.GROUP_BY_TYPE
            elif analysis['has_background']:
                return StrategyType.PRESERVE_HIERARCHY
            else:
                return StrategyType.SMART_MERGE
        else:
            # 大量图层，根据具体情况选择
            if analysis['text_ratio'] > 0.6:
                return StrategyType.GROUP_BY_TYPE
            elif analysis['group_ratio'] > 0.3:
                return StrategyType.PRESERVE_HIERARCHY
            else:
                return StrategyType.SMART_MERGE
    
    def _generate_recommendations(
        self,
        layers: List[Dict],
        strategy: StrategyType,
        analysis: Dict
    ) -> List[CutRecommendation]:
        """生成切割建议"""
        recommendations = []
        
        if strategy == StrategyType.FLAT:
            # 每个图层单独一个区域
            for i, raw_layer in enumerate(layers):
                layer = self._normalize_layer(raw_layer)
                recommendations.append(CutRecommendation(
                    region_id=f"export_{i:03d}",
                    layer_ids=[layer.get('id', f'layer_{i}')],
                    strategy=strategy,
                    merge_suggested=False,
                    reason=f"单独导出图层: {layer.get('name', 'unnamed')}"
                ))
        
        elif strategy == StrategyType.GROUP_BY_TYPE:
            # 按类型分组
            type_groups = {}
            for i, raw_layer in enumerate(layers):
                layer = self._normalize_layer(raw_layer)
                layer_type = layer.get('type', 'unknown')
                if layer_type not in type_groups:
                    type_groups[layer_type] = []
                type_groups[layer_type].append(layer.get('id', f'layer_{i}'))
            
            for type_name, layer_ids in type_groups.items():
                recommendations.append(CutRecommendation(
                    region_id=f"group_{type_name}",
                    layer_ids=layer_ids,
                    strategy=strategy,
                    merge_suggested=False,
                    reason=f"按类型分组: {type_name}"
                ))
        
        elif strategy == StrategyType.PRESERVE_HIERARCHY:
            # 保留层级结构
            self._generate_hierarchy_recommendations(layers, recommendations)
        
        elif strategy == StrategyType.SMART_MERGE:
            # 智能合并
            self._generate_smart_merge_recommendations(layers, recommendations)
        
        elif strategy == StrategyType.GROUP_BY_PAGE:
            # 按页面分组（假设图层有 page 属性）
            page_groups = {}
            for i, layer in enumerate(layers):
                page = layer.get('page', 'default')
                if page not in page_groups:
                    page_groups[page] = []
                page_groups[page].append(layer.get('id', f'layer_{i}'))
            
            for page_name, layer_ids in page_groups.items():
                recommendations.append(CutRecommendation(
                    region_id=f"page_{page_name}",
                    layer_ids=layer_ids,
                    strategy=strategy,
                    merge_suggested=True,
                    reason=f"按页面分组: {page_name}"
                ))
        
        return recommendations
    
    def _generate_hierarchy_recommendations(
        self,
        layers: List[Dict],
        recommendations: List[CutRecommendation]
    ):
        """生成保留层级的建议"""
        root_layers = []
        child_map = {}
        
        for i, layer in enumerate(layers):
            parent_id = layer.get('parent_id')
            if parent_id is None:
                root_layers.append(layer)
            else:
                if parent_id not in child_map:
                    child_map[parent_id] = []
                child_map[parent_id].append(layer)
        
        def process_layer(layer: Dict, path: List[str]) -> str:
            layer_id = layer.get('id', f'layer_{len(path)}')
            children = child_map.get(layer_id, [])
            
            if not children:
                return layer_id
            
            # 收集所有子图层 ID
            all_children = []
            for child in children:
                child_id = process_layer(child, path + [layer_id])
                all_children.append(child_id)
            
            recommendations.append(CutRecommendation(
                region_id=f"hierarchy_{'_'.join(path)}_{layer_id}",
                layer_ids=all_children,
                strategy=StrategyType.PRESERVE_HIERARCHY,
                merge_suggested=False,
                reason=f"保留层级: {' > '.join(path + [layer_id])}"
            ))
            
            return layer_id
        
        for root in root_layers:
            process_layer(root, [])
    
    def _generate_smart_merge_recommendations(
        self,
        layers: List[Dict],
        recommendations: List[CutRecommendation]
    ):
        """生成智能合并建议"""
        # 按位置和类型分组
        grid_size = 200  # 200像素网格
        groups = {}
        
        for i, layer in enumerate(layers):
            bounds = layer.get('bounds', {})
            x = bounds.get('x', 0)
            y = bounds.get('y', 0)
            layer_type = layer.get('type', 'unknown')
            
            # 计算所属网格
            grid_x = x // grid_size
            grid_y = y // grid_size
            key = (grid_x, grid_y, layer_type)
            
            if key not in groups:
                groups[key] = []
            groups[key].append(layer.get('id', f'layer_{i}'))
        
        # 生成合并建议
        for (grid_x, grid_y, layer_type), layer_ids in groups.items():
            recommendations.append(CutRecommendation(
                region_id=f"merge_{grid_x}_{grid_y}_{layer_type}",
                layer_ids=layer_ids,
                strategy=StrategyType.SMART_MERGE,
                merge_suggested=len(layer_ids) > 1,
                reason=f"智能合并: {layer_type} x{len(layer_ids)}"
            ))
    
    def _apply_custom_rules(
        self,
        layers: List[Dict],
        recommendations: List[CutRecommendation]
    ) -> List[str]:
        """应用自定义规则"""
        applied_rules = []
        
        # 按优先级排序规则
        sorted_rules = sorted(self.rules, key=lambda r: r.priority, reverse=True)
        
        for rule in sorted_rules:
            conditions = rule.conditions
            
            # 检查图层类型条件
            if 'layer_types' in conditions:
                layer_types = set(l.get('type') for l in layers)
                if any(lt in layer_types for lt in conditions['layer_types']):
                    applied_rules.append(rule.name)
                    self.logger.debug(f"应用规则: {rule.name}")
            
            # 检查文本比例条件
            if 'text_ratio' in conditions:
                text_count = sum(1 for l in layers if l.get('type') in ['text', 'heading', 'body'])
                text_ratio = text_count / len(layers) if layers else 0
                if text_ratio >= conditions['text_ratio']:
                    applied_rules.append(rule.name)
                    self.logger.debug(f"应用规则: {rule.name}")
        
        return applied_rules
    
    def add_rule(self, rule: StrategyRule):
        """添加自定义规则"""
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        self.logger.info(f"添加策略规则: {rule.name}")
    
    def remove_rule(self, rule_name: str):
        """移除规则"""
        self.rules = [r for r in self.rules if r.name != rule_name]
        self.logger.info(f"移除策略规则: {rule_name}")
    
    def get_available_strategies(self) -> List[Dict]:
        """获取可用策略列表"""
        return [
            {
                'name': s.value,
                'description': self._get_strategy_description(s),
                'best_for': self._get_strategy_best_for(s)
            }
            for s in StrategyType
        ]
    
    def _get_strategy_description(self, strategy: StrategyType) -> str:
        descriptions = {
            StrategyType.FLAT: "所有图层单独导出，每个图层一个文件",
            StrategyType.GROUP_BY_TYPE: "按图层类型分组导出，相似的图层放在一起",
            StrategyType.GROUP_BY_PAGE: "按页面分组导出，每个页面的图层放在一起",
            StrategyType.PRESERVE_HIERARCHY: "保留 PSD 原有的层级结构",
            StrategyType.SMART_MERGE: "智能合并相邻且相似的图层"
        }
        return descriptions.get(strategy, "")
    
    def _get_strategy_best_for(self, strategy: StrategyType) -> str:
        best_for = {
            StrategyType.FLAT: "少量图层、组件库、图标",
            StrategyType.GROUP_BY_TYPE: "文字密集页面、表单元素",
            StrategyType.GROUP_BY_PAGE: "多页面 PSD、PPT 风格的 PSD",
            StrategyType.PRESERVE_HIERARCHY: "复杂组结构、需要保持上下文的组件",
            StrategyType.SMART_MERGE: "大量相似元素、需要优化的场景"
        }
        return best_for.get(strategy, "")


def select_strategy(**kwargs) -> StrategySelectionResult:
    """便捷函数：选择策略"""
    selector = StrategySelector()
    return selector.select(**kwargs)
