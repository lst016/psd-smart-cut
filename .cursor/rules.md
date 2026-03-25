# Cursor IDE 集成配置

> 为 Cursor 提供 PSD Smart Cut 项目上下文和开发规范。

## 项目概述

**PSD Smart Cut** - AI-powered PSD component extraction and smart cutting workflow system.

- **架构**: 9 层 Pipeline (Level 1-9)
- **语言**: Python 3.10+
- **测试**: pytest + mock 模式

## 项目结构

```
psd-smart-cut/
├── skills/psd-parser/      # 核心解析模块
│   ├── level1-parse/       # PSD 解析层
│   ├── level2_classify/    # 分类层
│   ├── level3_recognize/   # 识别层
│   ├── level4_strategy/     # 策略层
│   ├── level5_export/      # 导出层
│   ├── level6_extractor/   # 提取层
│   ├── level7_generator/   # 生成层
│   ├── level8_documentation/  # 文档层
│   └── level9_integration/ # 集成测试
├── docs/                   # 文档
├── examples/               # 示例代码
└── configs/               # 配置文件
```

## 开发规范

### 代码风格

- 使用 **Black** 格式化代码
- 使用 **isort** 排序导入
- 类型提示必须完整

```bash
# 格式化
black skills/
isort skills/

# 类型检查
mypy skills/
```

### 测试规范

- 每个模块必须有对应的测试文件
- 使用 mock 模式支持无 PSD 测试
- 测试覆盖率目标 > 80%

```bash
# 运行测试
pytest skills/psd-parser/ -v

# 带覆盖率
pytest skills/psd-parser/ --cov=. --cov-report=html
```

### 提交规范

- 提交信息使用中文
- 格式: `type(scope): subject`
- 类型: feat/fix/docs/style/refactor/test/chore

```bash
git commit -m "feat(level2): 添加图片子类型分类器"
```

## 模块开发指南

### 添加新分类器

```python
# skills/psd_parser/level2_classify/
# 1. 创建新的分类器文件
# 2. 继承 BaseClassifier
# 3. 实现 classify() 方法
# 4. 添加测试用例
```

### 添加新识别器

```python
# skills/psd_parser/level3_recognize/
# 1. 创建新的识别器文件
# 2. 继承 BaseRecognizer
# 3. 实现 recognize() 方法
# 4. 更新 Recognizer 统一接口
```

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt

# 开发模式安装
pip install -e .

# 运行示例
python examples/basic_parse.py your_file.psd

# 完整工作流
python -m skills.cli process design.psd --output ./output
```

## 相关文档

- [用户指南](./docs/USER_GUIDE.md)
- [使用文档](./docs/usage.md)
- [CLAUDE 集成](./docs/CLAUDE.md)
- [CHANGELOG](./docs/CHANGELOG.md)
