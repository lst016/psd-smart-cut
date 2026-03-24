# Level 8 - Document Layer (文档层)

**版本：** v0.8  
**状态：** ✅ 已完成  
**日期：** 2026-03-25  

---

## 📋 概述

文档层负责生成和管理项目的各类文档，包括 README、CHANGELOG、资产清单、HTML 预览页等。

---

## 🧩 组件列表

| 组件 | 文件 | 功能 |
|------|------|------|
| README 生成器 | `readme_generator.py` | 生成项目 README.md |
| CHANGELOG 生成器 | `changelog_generator.py` | 解析 git log 生成变更日志 |
| Manifest 生成器 | `manifest_generator.py` | 生成资产清单 JSON/YAML |
| Preview 生成器 | `preview_generator.py` | 生成 HTML 预览页 |
| 文档聚合器 | `doc_aggregator.py` | 聚合、验证文档完整性 |

---

## 🔧 使用方法

### 1. README 生成器

```python
from skills.psd_parser.level8_document import ReadmeGenerator, generate_readme

# 使用类
generator = ReadmeGenerator(mock_mode=True)
content = generator.generate(project_info)
generator.save("README.md", content)

# 使用便捷函数
content = generate_readme(
    project_info={"name": "My Project"},
    output_path="README.md"
)
```

**project_info 参数：**
```python
{
    "name": "项目名称",
    "description": "项目描述",
    "version": "v0.8",
    "features": ["功能1", "功能2"],
    "installation": "安装说明",
    "usage": "使用示例",
    "badges": ["python", "license", "build"],
    "structure": "目录结构字符串"
}
```

---

### 2. CHANGELOG 生成器

```python
from skills.psd_parser.level8_document import ChangelogGenerator, generate_changelog

# 使用类
generator = ChangelogGenerator(mock_mode=True)
commits = generator.parse_git_log()
content = generator.generate(from_version="v0.7")
generator.save("CHANGELOG.md", content)

# 使用便捷函数
content = generate_changelog(
    from_version="v0.7",
    output_path="CHANGELOG.md"
)
```

**支持的变更类型：**
- `feat` - 新功能
- `fix` - Bug 修复
- `docs` - 文档更新
- `style` - 格式调整
- `refactor` - 重构
- `perf` - 性能优化
- `test` - 测试相关
- `chore` - 构建/CI

---

### 3. Manifest 生成器

```python
from skills.psd_parser.level8_document import ManifestGenerator, generate_manifest

# 使用类
generator = ManifestGenerator(mock_mode=True)
json_content = generator.generate(components)
yaml_content = generator.generate_yaml(components)
generator.save("manifest.json", json_content)

# 使用便捷函数
content = generate_manifest(
    components=[...],
    output_path="manifest.json"
)
```

**组件数据结构：**
```python
{
    "id": "comp-001",
    "name": "组件名称",
    "type": "button|image|text|...",
    "dimensions": {"width": 100, "height": 50},
    "position": {"x": 0, "y": 0},
    "style": {...},
    "assets": ["file1.png", "file2.png"],
    "thumbnail": "thumb.png"
}
```

---

### 4. Preview 生成器

```python
from skills.psd_parser.level8_document import PreviewGenerator, generate_preview

# 使用类
generator = PreviewGenerator(mock_mode=True)
html = generator.generate(components, assets_dir="./output")
generator.save("preview.html", html)

# 使用便捷函数
html = generate_preview(
    components=[...],
    assets_dir="./output",
    output_path="preview.html"
)
```

**预览页特性：**
- 📋 组件卡片列表
- 🔗 组件关系图（SVG）
- 📊 统计信息面板
- 🎨 类型颜色区分

---

### 5. 文档聚合器

```python
from skills.psd_parser.level8_document import DocAggregator, aggregate_docs

# 使用类
aggregator = DocAggregator(mock_mode=True)
result = aggregator.aggregate("./docs")
validation = aggregator.validate("./docs")

# 使用便捷函数
result = aggregate_docs(
    output_dir="./docs",
    validate=True
)
```

**聚合结果：**
```python
{
    "output_dir": "./docs",
    "documents": [...],
    "index": {...},
    "structure": "目录结构字符串",
    "total_docs": 8,
    "required_docs": 3,
    "optional_docs": 5,
    "validation": {
        "valid": True,
        "errors": [],
        "warnings": [...]
    }
}
```

---

## 🧪 测试

```bash
cd ~/Desktop/agent/projects/psd-smart-cut
python -m pytest skills/psd-parser/level8-document/test_level8.py -v
```

---

## 📁 输出文件

| 文件 | 说明 |
|------|------|
| `README.md` | 项目主文档 |
| `CHANGELOG.md` | 版本变更日志 |
| `manifest.json` | 资产清单 |
| `preview.html` | 组件预览页 |
| `index.json` | 文档索引 |

---

## 🔄 Mock 模式

所有生成器默认使用 mock 模式，可以在没有真实 git log 和 PSD 文件的情况下进行测试。

```python
# 启用 mock 模式（默认）
generator = ReadmeGenerator(mock_mode=True)

# 禁用 mock 模式（使用真实数据）
generator = ReadmeGenerator(mock_mode=False)
```

---

## 📝 更新日志

### v0.8.0 (2026-03-25)
- ✅ 添加 README 生成器
- ✅ 添加 CHANGELOG 生成器
- ✅ 添加 Manifest 生成器
- ✅ 添加 Preview 生成器
- ✅ 添加文档聚合器
- ✅ 添加单元测试
