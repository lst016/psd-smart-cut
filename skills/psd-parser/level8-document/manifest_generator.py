"""
Level 8 - Manifest Generator
资产清单生成器
"""
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
import json
import sys
import yaml

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from skills.common import get_logger, get_config, get_error_handler, ErrorHandler, ErrorCategory, ErrorSeverity

logger = get_logger("manifest_generator")


@dataclass
class ManifestEntry:
    """资产清单条目"""
    id: str
    name: str
    type: str
    specs: Dict[str, Any]
    assets: List[str]
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)


@dataclass
class Manifest:
    """完整的资产清单"""
    version: str
    generated_at: str
    total_components: int
    entries: List[ManifestEntry]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "version": self.version,
            "generated_at": self.generated_at,
            "total_components": self.total_components,
            "entries": [e.to_dict() for e in self.entries],
            "metadata": self.metadata,
        }


class ManifestGenerator:
    """资产清单生成器"""
    
    # 组件类型
    COMPONENT_TYPES = [
        "image", "text", "vector", "group", "decorator",
        "button", "icon", "background", "heading", "body",
        "label", "divider", "container", "card", "modal"
    ]
    
    # 规格字段
    SPEC_FIELDS = [
        "width", "height", "depth", "color_mode",
        "has_alpha", "visible", "locked"
    ]
    
    def __init__(self, mock_mode: bool = True):
        """
        初始化清单生成器
        
        Args:
            mock_mode: 是否使用 mock 模式（默认 True）
        """
        self.mock_mode = mock_mode
        self.logger = get_logger("manifest_generator")
        self.error_handler = get_error_handler()
    
    def generate(self, components: Optional[List[Dict]] = None) -> str:
        """
        生成资产清单
        
        Args:
            components: 组件列表（可选，为空时使用 mock 数据）
        
        Returns:
            JSON 格式的清单字符串
        """
        if components is None:
            components = [] if self.mock_mode else self._generate_mock_components()
        
        # 创建清单条目
        entries = []
        for comp in components:
            entry = self._create_manifest_entry(comp)
            entries.append(entry)
        
        # 创建完整清单
        from datetime import datetime
        manifest = Manifest(
            version="1.0.0",
            generated_at=datetime.now().isoformat(),
            total_components=len(entries),
            entries=entries,
            metadata=self._generate_metadata(components)
        )
        
        return json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2)
    
    def generate_yaml(self, components: Optional[List[Dict]] = None) -> str:
        """
        生成 YAML 格式的清单
        
        Args:
            components: 组件列表（可选）
        
        Returns:
            YAML 格式的清单字符串
        """
        data = json.loads(self.generate(components))
        return yaml.dump(data, allow_unicode=True, default_flow_style=False)
    
    def _create_manifest_entry(self, component: Dict) -> ManifestEntry:
        """从组件数据创建清单条目"""
        # 提取规格
        specs = self._extract_specs(component)
        
        # 提取资产文件
        assets = self._extract_assets(component)
        
        return ManifestEntry(
            id=component.get("id", "unknown"),
            name=component.get("name", "Unnamed"),
            type=component.get("type", "unknown"),
            specs=specs,
            assets=assets
        )
    
    def _extract_specs(self, component: Dict) -> Dict:
        """提取组件规格"""
        specs = {}
        
        # 尺寸规格
        if "dimensions" in component:
            dims = component["dimensions"]
            specs["width"] = dims.get("width", 0)
            specs["height"] = dims.get("height", 0)
        
        # 位置规格
        if "position" in component:
            pos = component["position"]
            specs["x"] = pos.get("x", 0)
            specs["y"] = pos.get("y", 0)
        
        # 样式规格
        if "style" in component:
            specs["style"] = component["style"]
        
        # 层级规格
        if "depth" in component:
            specs["depth"] = component["depth"]
        
        # 可见性规格
        if "visible" in component:
            specs["visible"] = component["visible"]
        
        # 锁定状态
        if "locked" in component:
            specs["locked"] = component["locked"]
        
        return specs
    
    def _extract_assets(self, component: Dict) -> List[str]:
        """提取组件关联的资产文件"""
        assets = []
        
        # 直接的资产列表
        if "assets" in component:
            assets.extend(component["assets"])
        
        # 导出的文件
        if "exported_files" in component:
            assets.extend(component["exported_files"])
        
        # 缩略图
        if "thumbnail" in component:
            assets.append(component["thumbnail"])
        
        # 移除重复
        return list(set(assets))
    
    def _generate_metadata(self, components: List[Dict]) -> Dict:
        """生成清单元数据"""
        # 按类型统计
        type_counts = {}
        for comp in components:
            comp_type = comp.get("type", "unknown")
            type_counts[comp_type] = type_counts.get(comp_type, 0) + 1
        
        # 计算总尺寸
        total_width = 0
        total_height = 0
        for comp in components:
            if "dimensions" in comp:
                dims = comp["dimensions"]
                total_width += dims.get("width", 0)
                total_height += dims.get("height", 0)
        
        return {
            "type_statistics": type_counts,
            "total_dimensions": {
                "width": total_width,
                "height": total_height
            },
            "format_version": "1.0"
        }
    
    def _generate_mock_components(self) -> List[Dict]:
        """生成 Mock 组件数据"""
        return [
            {
                "id": "comp-001",
                "name": "Header Logo",
                "type": "image",
                "dimensions": {"width": 200, "height": 60},
                "position": {"x": 0, "y": 0},
                "style": {"format": "png", "mode": "RGBA"},
                "visible": True,
                "locked": False,
                "assets": ["output/images/header-logo.png"],
                "thumbnail": "output/thumbnails/comp-001.png"
            },
            {
                "id": "comp-002",
                "name": "Main Title",
                "type": "text",
                "dimensions": {"width": 400, "height": 48},
                "position": {"x": 50, "y": 100},
                "style": {
                    "font_family": "Arial",
                    "font_size": 24,
                    "font_weight": "bold",
                    "color": "#333333"
                },
                "visible": True,
                "locked": False,
                "assets": [],
                "text_content": "Welcome to PSD Smart Cut"
            },
            {
                "id": "comp-003",
                "name": "Primary Button",
                "type": "button",
                "dimensions": {"width": 120, "height": 40},
                "position": {"x": 50, "y": 200},
                "style": {
                    "background_color": "#007AFF",
                    "border_radius": 8,
                    "text_color": "#FFFFFF"
                },
                "visible": True,
                "locked": False,
                "assets": ["output/images/primary-button.png"],
                "thumbnail": "output/thumbnails/comp-003.png"
            },
            {
                "id": "comp-004",
                "name": "Icon Set",
                "type": "group",
                "dimensions": {"width": 320, "height": 80},
                "position": {"x": 50, "y": 300},
                "children": [
                    {"id": "icon-001", "name": "Home Icon", "type": "icon"},
                    {"id": "icon-002", "name": "Search Icon", "type": "icon"},
                    {"id": "icon-003", "name": "User Icon", "type": "icon"},
                    {"id": "icon-004", "name": "Settings Icon", "type": "icon"}
                ],
                "visible": True,
                "locked": False,
                "assets": ["output/images/icons/"]
            },
            {
                "id": "comp-005",
                "name": "Background Container",
                "type": "background",
                "dimensions": {"width": 1920, "height": 1080},
                "position": {"x": 0, "y": 0},
                "style": {
                    "background_color": "#F5F5F5",
                    "background_image": None
                },
                "visible": True,
                "locked": True,
                "assets": []
            },
            {
                "id": "comp-006",
                "name": "Card Component",
                "type": "card",
                "dimensions": {"width": 300, "height": 200},
                "position": {"x": 100, "y": 400},
                "style": {
                    "background_color": "#FFFFFF",
                    "border_radius": 12,
                    "shadow": "0 4px 12px rgba(0,0,0,0.1)"
                },
                "visible": True,
                "locked": False,
                "assets": ["output/images/card-bg.png"],
                "thumbnail": "output/thumbnails/comp-006.png"
            },
            {
                "id": "comp-007",
                "name": "Divider Line",
                "type": "divider",
                "dimensions": {"width": 200, "height": 1},
                "position": {"x": 50, "y": 380},
                "style": {
                    "color": "#E0E0E0",
                    "thickness": 1
                },
                "visible": True,
                "locked": False,
                "assets": []
            },
            {
                "id": "comp-008",
                "name": "Footer Label",
                "type": "label",
                "dimensions": {"width": 100, "height": 20},
                "position": {"x": 50, "y": 650},
                "style": {
                    "font_family": "Arial",
                    "font_size": 12,
                    "color": "#888888"
                },
                "visible": True,
                "locked": False,
                "text_content": "© 2026 Company"
            }
        ]
    
    def save(self, output_path: str, manifest: str) -> bool:
        """
        保存清单文件
        
        Args:
            output_path: 输出文件路径
            manifest: 清单内容
        
        Returns:
            是否保存成功
        """
        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, "w", encoding="utf-8") as f:
                f.write(manifest)
            
            self.logger.info(f"Manifest 已保存到: {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"保存 Manifest 失败: {e}")
            self.error_handler.record(
                task="save_manifest",
                error=e,
                category=ErrorCategory.IO_ERROR,
                severity=ErrorSeverity.MEDIUM,
                context={"output_path": output_path}
            )
            return False
    
    def load(self, manifest_path: str) -> Optional[Manifest]:
        """
        加载清单文件
        
        Args:
            manifest_path: 清单文件路径
        
        Returns:
            Manifest 对象或 None
        """
        try:
            path = Path(manifest_path)
            if not path.exists():
                self.logger.error(f"Manifest 文件不存在: {manifest_path}")
                return None
            
            with open(path, "r", encoding="utf-8") as f:
                if path.suffix in [".yaml", ".yml"]:
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
            
            # 解析条目
            entries = [
                ManifestEntry(**entry) for entry in data.get("entries", [])
            ]
            
            return Manifest(
                version=data.get("version", "1.0.0"),
                generated_at=data.get("generated_at", ""),
                total_components=data.get("total_components", 0),
                entries=entries,
                metadata=data.get("metadata", {})
            )
            
        except Exception as e:
            self.logger.error(f"加载 Manifest 失败: {e}")
            self.error_handler.record(
                task="load_manifest",
                error=e,
                category=ErrorCategory.IO_ERROR,
                severity=ErrorSeverity.MEDIUM,
                context={"manifest_path": manifest_path}
            )
            return None
    
    def get_component_summary(self, manifest: Manifest) -> Dict:
        """
        获取组件摘要统计
        
        Args:
            manifest: Manifest 对象
        
        Returns:
            摘要统计字典
        """
        summary = {
            "total": manifest.total_components,
            "by_type": {},
            "with_assets": 0,
            "locked": 0,
            "invisible": 0
        }
        
        for entry in manifest.entries:
            # 按类型统计
            if entry.type not in summary["by_type"]:
                summary["by_type"][entry.type] = 0
            summary["by_type"][entry.type] += 1
            
            # 有资产的
            if entry.assets:
                summary["with_assets"] += 1
            
            # 锁定的
            if entry.specs.get("locked", False):
                summary["locked"] += 1
            
            # 不可见的
            if not entry.specs.get("visible", True):
                summary["invisible"] += 1
        
        return summary


# 便捷函数
def generate_manifest(components: Optional[List[Dict]] = None, output_path: Optional[str] = None) -> str:
    """
    生成资产清单的便捷函数
    
    Args:
        components: 组件列表
        output_path: 输出路径（可选）
    
    Returns:
        JSON 格式的清单
    """
    generator = ManifestGenerator(mock_mode=True)
    manifest = generator.generate(components)
    
    if output_path:
        generator.save(output_path, manifest)
    
    return manifest


if __name__ == "__main__":
    # 测试
    generator = ManifestGenerator(mock_mode=True)
    
    print("生成 Manifest...")
    manifest = generator.generate()
    print(manifest[:600])
    print("...")
    print(f"\n总长度: {len(manifest)} 字符")
    
    # 测试 YAML 格式
    print("\n生成 YAML 格式...")
    yaml_content = generator.generate_yaml()
    print(yaml_content[:400])
