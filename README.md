# PSD Smart Cut

AI 驱动的 PSD 智能切图工作流系统

## 项目状态

**当前版本：** v0.1 - 基础架构（开发中）

## 功能

- ✅ PSD 多 Page 解析
- ✅ 嵌套图层识别
- 🔄 Level 1-8 原子化 Agent
- 🔄 AI 智能切图
- 🔄 Markdown + JSON 文档生成

## 快速开始

```bash
# 克隆项目
git clone https://github.com/lst016/psd-smart-cut.git
cd psd-smart-cut

# 安装依赖
pip install psd-tools pillow

# 运行示例
python examples/basic_parse.py your_file.psd
```

## 项目结构

```
psd-smart-cut/
├── docs/               # 文档
│   ├── PRD/           # 产品需求文档
│   └── specs/          # 技能规范
├── skills/            # Agent 技能
│   ├── psd-parser/    # PSD 解析
│   └── common/        # 通用模块
├── configs/           # 配置文件
├── output/            # 输出目录
├── tests/             # 测试
└── examples/          # 示例
```

## 版本历史

See [CHANGELOG.md](docs/CHANGELOG.md)

## 许可证

MIT
