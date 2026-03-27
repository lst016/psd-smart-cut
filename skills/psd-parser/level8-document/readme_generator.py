"""
Level 8 - README Generator
README 生成器
"""
from typing import Dict, List, Optional
from pathlib import Path
import locale
import re
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from skills.common import get_logger, get_config

logger = get_logger("readme_generator")


class ReadmeGenerator:
    """README 生成器 - 生成项目 README.md"""
    
    # 徽章颜色映射
    BADGE_COLORS = {
        "python": "3776AB",
        "version": "3776AB",
        "license": "MIT",
        "build": "passing",
        "coverage": "green",
        "stars": "yellow",
        "forks": "gray",
    }
    
    # 支持的徽章类型
    SUPPORTED_BADGES = [
        "python", "license", "build", "coverage", "stars", "forks"
    ]
    
    def __init__(self, mock_mode: bool = True):
        """
        初始化 README 生成器
        
        Args:
            mock_mode: 是否使用 mock 模式（默认 True）
        """
        self.mock_mode = mock_mode
        self.logger = get_logger("readme_generator")
        
        # 尝试加载配置
        try:
            self.config = get_config()
        except Exception:
            self.config = None
    
    def generate(self, project_info: Optional[Dict] = None) -> str:
        """
        生成 README.md 内容
        
        Args:
            project_info: 项目信息字典，包含：
                - name: 项目名称
                - description: 项目描述
                - version: 版本号
                - features: 功能列表
                - installation: 安装说明
                - usage: 使用示例
                - badges: 自定义徽章
        
        Returns:
            README.md 内容的字符串
        """
        if project_info is None:
            project_info = self._get_default_project_info()
        
        sections = []
        
        # 1. 标题和徽章
        sections.append(self._generate_header(project_info))
        
        # 2. 徽章
        badges = self._generate_badges(project_info.get("badges", []))
        if badges:
            sections.append(badges)
            sections.append("")
        
        # 3. 项目简介
        sections.append(self._generate_description(project_info))
        
        # 4. 功能列表
        features = project_info.get("features", [])
        if features:
            sections.append(self._generate_features(features))
        
        # 5. 安装说明
        sections.append(self._generate_installation(project_info))
        
        # 6. 使用示例
        sections.append(self._generate_usage(project_info))
        
        # 7. 目录结构
        sections.append(self._generate_structure(project_info))
        
        # 8. 贡献指南
        sections.append(self._generate_contributing())
        
        # 9. 许可证
        sections.append(self._generate_license(project_info))
        
        return "\n\n".join(sections)
    
    def _get_default_project_info(self) -> Dict:
        """获取默认项目信息（mock 模式）"""
        return {
            "name": "PSD Smart Cut",
            "description": "智能 PSD 切图工具 - AI 驱动的 PSD 文件自动分析和切割解决方案",
            "version": "v0.8",
            "features": [
                "PSD/PSB 文件解析",
                "AI 智能图层分类",
                "组件自动识别",
                "智能切割策略",
                "多格式导出",
                "文字/样式提取",
                "规格自动生成",
                "文档自动生成",
            ],
            "installation": self._get_mock_installation(),
            "usage": self._get_mock_usage(),
            "badges": ["python", "license", "build"],
        }
    
    def _get_mock_installation(self) -> str:
        """获取 mock 安装说明"""
        return """```bash
# 克隆项目
git clone https://github.com/your-repo/psd-smart-cut.git
cd psd-smart-cut

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\\Scripts\\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装 psd-tools（可选，用于真实 PSD 解析）
pip install psd-tools
```"""
    
    def _get_mock_usage(self) -> str:
        """获取 mock 使用示例"""
        return """```python
from skills.psd_parser import PSDParser

# 初始化解析器
parser = PSDParser()

# 解析 PSD 文件
result = parser.parse("design.psd")

# 获取图层列表
layers = result.get("layers", [])
print(f"找到 {len(layers)} 个图层")

# 导出资产
from skills.psd_parser.level5_export import Exporter
exporter = Exporter()
exporter.export(layers, output_dir="./output")
```"""
    
    def _generate_header(self, project_info: Dict) -> str:
        """生成标题"""
        name = project_info.get("name", "Project")
        version = project_info.get("version", "")
        
        if version:
            return f"# {name}\n\n> {version}"
        return f"# {name}"
    
    def _generate_description(self, project_info: Dict) -> str:
        """生成项目描述"""
        description = project_info.get("description", "")
        return f"## 项目简介\n\n{description}"
    
    def _generate_features(self, features: List[str]) -> str:
        """生成功能列表"""
        lines = ["## 功能特性\n"]
        
        for feature in features:
            lines.append(f"- {feature}")
        
        return "\n".join(lines)
    
    def _generate_installation(self, project_info: Dict) -> str:
        """生成安装说明"""
        installation = project_info.get("installation", "")
        return f"## 安装\n\n{installation}"
    
    def _generate_usage(self, project_info: Dict) -> str:
        """生成使用示例"""
        usage = project_info.get("usage", "")
        return f"## 使用\n\n{usage}"
    
    def _generate_structure(self, project_info: Dict) -> str:
        """生成目录结构"""
        structure = project_info.get("structure", self._get_default_structure())
        
        lines = ["## 目录结构\n"]
        lines.append("```")
        lines.append(structure)
        lines.append("```")
        
        return "\n".join(lines)
    
    def _get_default_structure(self) -> str:
        """获取默认目录结构"""
        return """psd-smart-cut/
├── configs/              # 配置文件
├── docs/                 # 文档
│   ├── CHANGELOG.md
│   ├── SPECS.md
│   └── VERSION-PLAN.md
├── examples/              # 示例文件
├── logs/                 # 日志文件
├── output/               # 输出目录
├── skills/               # 技能模块
│   ├── common/           # 通用工具
│   └── psd-parser/       # PSD 解析器
│       ├── level1-parse/     # 解析层
│       ├── level2-classify/  # 分类层
│       ├── level3_recognize/ # 识别层
│       ├── level4-strategy/  # 策略层
│       ├── level5-export/    # 导出层
│       ├── level6-extract/    # 提取层
│       ├── level7-generate/   # 生成层
│       └── level8-document/   # 文档层
├── tests/                # 测试文件
├── README.md
├── requirements.txt
└── VERSION"""
    
    def _generate_contributing(self) -> str:
        """生成贡献指南"""
        return """## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request"""
    
    def _generate_license(self, project_info: Dict) -> str:
        """生成许可证信息"""
        license_name = project_info.get("license", "MIT")
        return f"## 许可证\n\n本项目基于 {license_name} 许可证开源。"""
    
    def _generate_badges(self, badge_types: List[str]) -> str:
        """
        生成徽章（badge）
        
        Args:
            badge_types: 徽章类型列表
        
        Returns:
            徽章 Markdown 字符串
        """
        badges = []
        
        for badge_type in badge_types:
            badge = self._generate_badge(badge_type)
            if badge:
                badges.append(badge)
        
        return " ".join(badges) if badges else ""
    
    def _generate_badge(self, badge_type: str) -> str:
        """生成单个徽章"""
        badge_map = {
            "python": ("Python", "3.8+", "3776AB"),
            "license": ("License", "MIT", "MIT"),
            "build": ("Build", "passing", "4AC71B"),
            "coverage": ("Coverage", "100%", "green"),
            "stars": ("Stars", "0", "yellow"),
            "forks": ("Forks", "0", "gray"),
        }
        
        if badge_type not in badge_map:
            return ""
        
        label, status, color = badge_map[badge_type]
        
        # 使用 shields.io 徽章服务
        return f"![{label}](https://img.shields.io/badge/{label}-{status}-{color})"
    
    def save(self, output_path: str, content: str) -> bool:
        """
        保存 README.md 文件
        
        Args:
            output_path: 输出文件路径
            content: README 内容
        
        Returns:
            是否保存成功
        """
        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            encoding = locale.getpreferredencoding(False) or "utf-8"
            with open(path, "w", encoding=encoding) as f:
                f.write(content)
            
            self.logger.info(f"README 已保存到: {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"保存 README 失败: {e}")
            return False
    
    def auto_detect_features(self) -> List[str]:
        """
        自动检测项目功能列表
        
        Returns:
            检测到的功能列表
        """
        features = []
        
        # 检测各层是否存在
        level_dirs = {
            "level1-parse": "PSD 解析",
            "level2-classify": "图层分类",
            "level3_recognize": "组件识别",
            "level4-strategy": "切割策略",
            "level5-export": "资产导出",
            "level6-extract": "文字/样式提取",
            "level7-generate": "规格生成",
            "level8-document": "文档生成",
        }
        
        skills_dir = Path(__file__).parent.parent
        for level, feature in level_dirs.items():
            level_path = skills_dir / level
            if level_path.exists():
                features.append(feature)
        
        return features


# 便捷函数
def generate_readme(project_info: Optional[Dict] = None, output_path: Optional[str] = None) -> str:
    """
    生成 README 的便捷函数
    
    Args:
        project_info: 项目信息
        output_path: 输出路径（可选）
    
    Returns:
        README 内容
    """
    generator = ReadmeGenerator(mock_mode=True)
    content = generator.generate(project_info)
    
    if output_path:
        generator.save(output_path, content)
    
    return content


if __name__ == "__main__":
    # 测试
    generator = ReadmeGenerator(mock_mode=True)
    
    print("生成 README...")
    content = generator.generate()
    print(content[:500])
    print("...")
    print(f"\n总长度: {len(content)} 字符")
