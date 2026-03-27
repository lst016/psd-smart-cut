"""
Level 8 - Preview Generator
HTML 预览页生成器
"""
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import base64
import json
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from skills.common import get_logger, get_config, get_error_handler, ErrorHandler, ErrorCategory, ErrorSeverity

logger = get_logger("preview_generator")


class PreviewGenerator:
    """HTML 预览页生成器"""
    
    # 组件类型颜色映射
    TYPE_COLORS = {
        "image": "#4CAF50",
        "text": "#2196F3",
        "vector": "#9C27B0",
        "group": "#FF9800",
        "decorator": "#607D8B",
        "button": "#E91E63",
        "icon": "#00BCD4",
        "background": "#795548",
        "heading": "#3F51B5",
        "body": "#009688",
        "label": "#8BC34A",
        "divider": "#9E9E9E",
        "container": "#FF5722",
        "card": "#673AB7",
        "modal": "#F44336",
        "unknown": "#CCCCCC"
    }
    
    def __init__(self, mock_mode: bool = True):
        """
        初始化预览页生成器
        
        Args:
            mock_mode: 是否使用 mock 模式（默认 True）
        """
        self.mock_mode = mock_mode
        self.logger = get_logger("preview_generator")
        self.error_handler = get_error_handler()
    
    def generate(self, components: Optional[List[Dict]] = None, assets_dir: Optional[str] = None) -> str:
        """
        生成 HTML 预览页
        
        Args:
            components: 组件列表（可选，为空时使用 mock 数据）
            assets_dir: 资产目录路径（可选）
        
        Returns:
            HTML 内容的字符串
        """
        if components is None:
            components = self._generate_mock_components()
        
        if assets_dir is None:
            assets_dir = "./output"
        
        # 生成 HTML
        html_parts = []
        
        # HTML 头部
        html_parts.append(self._generate_html_head())
        
        # 页面内容
        html_parts.append(self._generate_page_header(components))
        
        # 组件列表
        html_parts.append(self._generate_components_section(components))
        
        # 组件关系图
        html_parts.append(self._generate_relationship_diagram(components))
        
        # 统计信息
        html_parts.append(self._generate_statistics(components))
        
        # HTML 尾部
        html_parts.append(self._generate_html_tail())
        
        return "\n".join(html_parts)
    
    def _generate_html_head(self) -> str:
        """生成 HTML 头部"""
        return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PSD Smart Cut - 组件预览</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background-color: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            border-radius: 12px;
            margin-bottom: 30px;
            text-align: center;
        }
        
        header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .section {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .section h2 {
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        
        .stat-card h3 {
            font-size: 2em;
            margin-bottom: 5px;
        }
        
        .stat-card p {
            opacity: 0.9;
            font-size: 0.9em;
        }
        
        .component-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
        }
        
        .component-card {
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 20px;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .component-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        }
        
        .component-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .component-name {
            font-weight: bold;
            font-size: 1.1em;
        }
        
        .component-type {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            color: white;
        }
        
        .component-details {
            font-size: 0.9em;
            color: #666;
        }
        
        .component-details p {
            margin: 5px 0;
        }
        
        .thumbnail {
            width: 100%;
            height: 120px;
            background-color: #f0f0f0;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 15px;
            overflow: hidden;
        }
        
        .thumbnail img {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }
        
        .thumbnail-placeholder {
            color: #999;
            font-size: 0.9em;
        }
        
        .diagram-container {
            width: 100%;
            height: 500px;
            background-color: #fafafa;
            border-radius: 8px;
            overflow: hidden;
        }
        
        .diagram-container svg {
            width: 100%;
            height: 100%;
        }
        
        .legend {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-top: 20px;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .legend-color {
            width: 16px;
            height: 16px;
            border-radius: 4px;
        }
        
        .type-counts {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        
        .type-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            background-color: #f0f0f0;
            border-radius: 20px;
            font-size: 0.85em;
        }
        
        .type-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }
        
        footer {
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">"""
    
    def _generate_page_header(self, components: List[Dict]) -> str:
        """生成页面头部"""
        total = len(components)
        return f"""
        <header>
            <h1>PSD Smart Cut</h1>
            <p>组件预览报告 - 共 {total} 个组件</p>
        </header>
    """
    
    def _generate_components_section(self, components: List[Dict]) -> str:
        """生成组件列表区块"""
        cards = []
        for comp in components:
            card = self._generate_component_card(comp)
            cards.append(card)
        
        return f"""
        <div class="section">
            <h2>组件列表</h2>
            <div class="component-grid">
                {chr(10).join(cards)}
            </div>
        </div>
    """
    
    def _generate_component_card(self, comp: Dict) -> str:
        """生成单个组件卡片"""
        comp_id = comp.get("id", "unknown")
        name = comp.get("name", "Unnamed")
        comp_type = comp.get("type", "unknown")
        color = self.TYPE_COLORS.get(comp_type, self.TYPE_COLORS["unknown"])
        
        # 尺寸信息
        dims = comp.get("dimensions", {})
        width = dims.get("width", 0)
        height = dims.get("height", 0)
        
        # 位置信息
        pos = comp.get("position", {})
        x = pos.get("x", 0)
        y = pos.get("y", 0)
        
        # 缩略图
        thumbnail = comp.get("thumbnail", "")
        thumbnail_html = self._generate_thumbnail_html(thumbnail, name)
        
        return f"""
        <div class="component-card">
            <div class="component-header">
                <span class="component-name">{name}</span>
                <span class="component-type" style="background-color: {color}">{comp_type}</span>
            </div>
            {thumbnail_html}
            <div class="component-details">
                <p><strong>ID:</strong> {comp_id}</p>
                <p><strong>尺寸:</strong> {width} × {height}</p>
                <p><strong>位置:</strong> ({x}, {y})</p>
            </div>
        </div>"""
    
    def _generate_thumbnail_html(self, thumbnail: str, name: str) -> str:
        """生成缩略图 HTML"""
        if thumbnail:
            # 检查是否是 base64 或路径
            if thumbnail.startswith("data:"):
                return f'<div class="thumbnail"><img src="{thumbnail}" alt="{name}"></div>'
            else:
                return f'''<div class="thumbnail">
                    <span class="thumbnail-placeholder">[asset] {name}</span>
                </div>'''
        else:
            return f'''<div class="thumbnail">
                <span class="thumbnail-placeholder">[asset] {name}</span>
            </div>'''
    
    def _generate_relationship_diagram(self, components: List[Dict]) -> str:
        """生成组件关系图"""
        # 生成 SVG 关系图
        svg_content = self._generate_svg_diagram(components)
        
        # 生成图例
        legend = self._generate_legend()
        
        return f"""
        <div class="section">
            <h2>组件关系图</h2>
            <div class="diagram-container">
                {svg_content}
            </div>
            <div class="legend">
                {legend}
            </div>
        </div>
    """
    
    def _generate_svg_diagram(self, components: List[Dict]) -> str:
        """生成 SVG 内容"""
        svg_parts = []
        
        # 网格背景
        svg_parts.append('''<!-- 网格背景 -->
        <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#e0e0e0" stroke-width="0.5"/>
            </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />''')
        
        # 绘制组件节点
        for i, comp in enumerate(components[:20]):  # 限制最多显示20个
            comp_type = comp.get("type", "unknown")
            name = comp.get("name", "Unnamed")
            color = self.TYPE_COLORS.get(comp_type, self.TYPE_COLORS["unknown"])
            
            # 计算位置（网格布局）
            row = i // 5
            col = i % 5
            x = 100 + col * 220
            y = 80 + row * 150
            
            # 绘制节点
            svg_parts.append(f'''
            <!-- {name} -->
            <g transform="translate({x}, {y})">
                <rect x="0" y="0" width="180" height="80" rx="8" 
                      fill="{color}" opacity="0.2" stroke="{color}" stroke-width="2"/>
                <text x="90" y="30" text-anchor="middle" font-size="12" font-weight="bold">{name[:15]}</text>
                <text x="90" y="50" text-anchor="middle" font-size="10" fill="#666">{comp_type}</text>
                <text x="90" y="68" text-anchor="middle" font-size="9" fill="#999">ID: {comp.get('id', 'N/A')[:10]}</text>
            </g>''')
        
        # 绘制连接线（组关系）
        for i, comp in enumerate(components[:15]):
            if "children" in comp:
                parent_x = 100 + (i % 5) * 220 + 90
                parent_y = 80 + (i // 5) * 150
                
                for j, child in enumerate(comp.get("children", [])[:4]):
                    child_x = 100 + ((i + 1) % 5) * 220 + 90
                    child_y = 80 + ((i // 5) + 1) * 150 + j * 25
                    
                    svg_parts.append(f'''
                    <line x1="{parent_x}" y1="{parent_y + 40}" 
                          x2="{child_x}" y2="{child_y}" 
                          stroke="#999" stroke-width="1" stroke-dasharray="4,4"/>''')
        
        svg_body = "\n".join(svg_parts)
        return f'<svg viewBox="0 0 1200 500" xmlns="http://www.w3.org/2000/svg">{svg_body}</svg>'
    
    def _generate_legend(self) -> str:
        """生成图例"""
        legend_items = []
        for comp_type, color in sorted(self.TYPE_COLORS.items()):
            if comp_type != "unknown":
                legend_items.append(f'''
                <div class="legend-item">
                    <div class="legend-color" style="background-color: {color}"></div>
                    <span>{comp_type}</span>
                </div>''')
        
        return "".join(legend_items)
    
    def _generate_statistics(self, components: List[Dict]) -> str:
        """生成统计区块"""
        # 计算统计
        total = len(components)
        with_assets = sum(1 for c in components if c.get("assets") or c.get("exported_files"))
        
        # 按类型统计
        type_counts = {}
        for comp in components:
            t = comp.get("type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1
        
        # 统计 HTML
        type_badges = []
        for t, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            color = self.TYPE_COLORS.get(t, self.TYPE_COLORS["unknown"])
            type_badges.append(f'''
                <span class="type-badge">
                    <span class="type-dot" style="background-color: {color}"></span>
                    {t}: {count}
                </span>''')
        
        return f"""
        <div class="section">
            <h2>统计信息</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>{total}</h3>
                    <p>总组件数</p>
                </div>
                <div class="stat-card">
                    <h3>{with_assets}</h3>
                    <p>有资产</p>
                </div>
                <div class="stat-card">
                    <h3>{len(type_counts)}</h3>
                    <p>类型数</p>
                </div>
            </div>
            <h3 style="margin-bottom: 15px;">类型分布</h3>
            <div class="type-counts">
                {''.join(type_badges)}
            </div>
        </div>
    """
    
    def _generate_html_tail(self) -> str:
        """生成 HTML 尾部"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"""
        <footer>
            <p>生成时间: {timestamp} | PSD Smart Cut v0.8</p>
        </footer>
    </div>
</body>
</html>"""
    
    def _generate_mock_components(self) -> List[Dict]:
        """生成 Mock 组件数据"""
        return [
            {"id": "comp-001", "name": "Header Logo", "type": "image", 
             "dimensions": {"width": 200, "height": 60}, "position": {"x": 0, "y": 0}},
            {"id": "comp-002", "name": "Main Title", "type": "heading", 
             "dimensions": {"width": 400, "height": 48}, "position": {"x": 50, "y": 100}},
            {"id": "comp-003", "name": "Primary Button", "type": "button", 
             "dimensions": {"width": 120, "height": 40}, "position": {"x": 50, "y": 200},
             "assets": ["btn-primary.png"]},
            {"id": "comp-004", "name": "Icon Set", "type": "group", 
             "dimensions": {"width": 320, "height": 80}, "position": {"x": 50, "y": 300},
             "children": [
                 {"id": "icon-001", "name": "Home", "type": "icon"},
                 {"id": "icon-002", "name": "Search", "type": "icon"},
                 {"id": "icon-003", "name": "User", "type": "icon"}
             ]},
            {"id": "comp-005", "name": "Background", "type": "background", 
             "dimensions": {"width": 1920, "height": 1080}, "position": {"x": 0, "y": 0}},
            {"id": "comp-006", "name": "Card Component", "type": "card", 
             "dimensions": {"width": 300, "height": 200}, "position": {"x": 100, "y": 400},
             "assets": ["card-bg.png"], "thumbnail": "card-thumb.png"},
            {"id": "comp-007", "name": "Divider", "type": "divider", 
             "dimensions": {"width": 200, "height": 1}, "position": {"x": 50, "y": 380}},
            {"id": "comp-008", "name": "Footer Label", "type": "label", 
             "dimensions": {"width": 100, "height": 20}, "position": {"x": 50, "y": 650}},
            {"id": "comp-009", "name": "Body Text", "type": "body", 
             "dimensions": {"width": 500, "height": 100}, "position": {"x": 50, "y": 150}},
            {"id": "comp-010", "name": "Modal Dialog", "type": "modal", 
             "dimensions": {"width": 400, "height": 300}, "position": {"x": 300, "y": 200}},
        ]
    
    def generate_thumbnail(self, image_path: str) -> str:
        """
        生成缩略图（返回 base64 或路径）
        
        Args:
            image_path: 原图路径
        
        Returns:
            缩略图路径或 base64
        """
        try:
            path = Path(image_path)
            
            if not path.exists():
                return ""
            
            # 对于真实图片，可以进行缩放处理
            # 这里简化处理，直接返回原路径
            return image_path
            
        except Exception as e:
            self.logger.error(f"生成缩略图失败: {e}")
            return ""
    
    def save(self, output_path: str, content: str) -> bool:
        """
        保存 HTML 预览页
        
        Args:
            output_path: 输出文件路径
            content: HTML 内容
        
        Returns:
            是否保存成功
        """
        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            
            self.logger.info(f"Preview 已保存到: {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"保存 Preview 失败: {e}")
            self.error_handler.record(
                task="save_preview",
                error=e,
                category=ErrorCategory.IO_ERROR,
                severity=ErrorSeverity.MEDIUM,
                context={"output_path": output_path}
            )
            return False


# 便捷函数
def generate_preview(components: Optional[List[Dict]] = None, assets_dir: Optional[str] = None, 
                     output_path: Optional[str] = None) -> str:
    """
    生成预览页的便捷函数
    
    Args:
        components: 组件列表
        assets_dir: 资产目录
        output_path: 输出路径（可选）
    
    Returns:
        HTML 内容
    """
    generator = PreviewGenerator(mock_mode=True)
    html = generator.generate(components, assets_dir)
    
    if output_path:
        generator.save(output_path, html)
    
    return html


if __name__ == "__main__":
    # 测试
    generator = PreviewGenerator(mock_mode=True)
    
    print("生成 Preview HTML...")
    html = generator.generate()
    print(f"HTML 长度: {len(html)} 字符")
    print(html[:500])
    print("...")
