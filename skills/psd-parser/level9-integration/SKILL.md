# Level 9 - Integration Tests

**版本：** v0.9.0  
**模块：** `skills.psd-parser.level9-integration`  
**状态：** ✅ 已完成

---

## 功能概述

Level 9 是 PSD Smart Cut 项目的集成测试层，负责端到端工作流验证、性能基准测试和边界情况测试。

---

## 目录结构

```
level9-integration/
├── SKILL.md              # 本文档
├── __init__.py           # 模块初始化
├── test_integration.py    # 端到端集成测试
├── performance_test.py    # 性能基准测试
└── edge_case_test.py      # 边界情况测试
```

---

## 测试内容

### 1. 端到端集成测试 (`test_integration.py`)

验证 8 个 layer 模块的完整工作流：

| Level | 模块 | 测试内容 |
|-------|------|----------|
| Level 1 | PSD 解析 | Mock PSD 解析、页面提取、图层读取、层级构建 |
| Level 2 | 分类层 | 图层分类、图片/文字子类型分类 |
| Level 3 | 识别层 | 组件识别、区域检测、组件命名 |
| Level 4 | 策略层 | 策略选择、重叠检测、切割计划 |
| Level 5 | 导出层 | 资产导出、命名管理、格式转换 |
| Level 6 | 提取层 | 文字提取、样式提取、位置提取 |
| Level 7 | 生成层 | 尺寸生成、样式生成、规格验证 |
| Level 8 | 文档层 | README、Manifest、Preview 生成 |

**测试用例数：** 40+

### 2. 性能基准测试 (`performance_test.py`)

| 指标 | 测试内容 |
|------|----------|
| 响应时间 | 各模块单次操作响应时间 |
| 批量处理 | 不同批量大小（1/10/50/100）的处理性能 |
| 内存使用 | 大型 PSD（200+ 图层）的内存占用 |
| 可扩展性 | 图层数量增长对性能的影响 |

**基准配置：**
- 迭代次数：100 次
- 预热次数：10 次
- 内存采样：5 次

### 3. 边界情况测试 (`edge_case_test.py`)

| 类别 | 测试用例 |
|------|----------|
| 空 PSD | 空文档、空页面、空图层列表 |
| 超大数量 | 1000+ 图层处理 |
| 特殊字符 | Unicode、路径分隔符、空白字符、超长名称 |
| 缺失元数据 | 缺失父 ID、缺失类型、缺失尺寸、负坐标 |
| 极端数值 | 极大/极小尺寸、零画布 |
| 嵌套层级 | 深度嵌套（10+层）、循环引用、孤儿图层 |
| 可见性状态 | 全部隐藏、全部锁定 |
| 数据一致性 | 边界计算、数量一致性 |

**测试用例数：** 20+

---

## 使用方法

### 运行所有测试

```bash
cd ~/Desktop/agent/projects/psd-smart-cut
python3 -m pytest skills/psd-parser/level9-integration/ -v
```

### 运行特定测试

```bash
# 只运行集成测试
python3 -m pytest skills/psd-parser/level9-integration/test_integration.py -v

# 只运行性能测试
python3 -m pytest skills/psd-parser/level9-integration/performance_test.py -v

# 只运行边界测试
python3 -m pytest skills/psd-parser/level9-integration/edge_case_test.py -v
```

### 运行特定测试类

```bash
# 运行端到端测试
python3 -m pytest skills/psd-parser/level9-integration/test_integration.py::TestEndToEndIntegration -v

# 运行性能基准测试
python3 -m pytest skills/psd-parser/level9-integration/performance_test.py::TestPerformanceBaseline -v

# 运行边界情况测试
python3 -m pytest skills/psd-parser/level9-integration/edge_case_test.py::TestEmptyPSD -v
```

### 运行带覆盖率报告的测试

```bash
python3 -m pytest skills/psd-parser/level9-integration/ -v --cov=skills.psd-parser.level1_parse --cov=skills.psd-parser.level2_classify --cov-report=term-missing
```

### 运行性能测试（带详细输出）

```bash
python3 -m pytest skills/psd-parser/level9-integration/performance_test.py -v -s
```

---

## Mock 数据

测试使用完全 Mock 的数据，无需真实的 PSD 文件：

### Mock PSD 文档

```python
from test_integration import create_mock_psd_document

doc = create_mock_psd_document()
# 生成包含 11 个图层的示例文档
```

### Mock 大型 PSD

```python
from performance_test import create_large_psd_document

doc = create_large_psd_document(layer_count=100)
# 生成指定数量的图层
```

---

## 性能基准

### 预期性能指标

| 模块 | 操作 | 预期时间 |
|------|------|----------|
| Level 1 | PageExtractor.extract | < 100ms |
| Level 1 | LayerReader.read | < 100ms |
| Level 1 | HierarchyBuilder.build | < 50ms |
| Level 2 | LayerClassifier.classify_batch (50) | < 500ms |
| Level 3 | Recognizer.recognize_batch (50) | < 1000ms |
| Level 4 | StrategySelector.select | < 100ms |
| Level 5 | Exporter.export (10) | < 1000ms |
| Level 6 | Extractor.extract | < 50ms |
| Level 7 | SpecGenerator.generate | < 50ms |
| Level 8 | ReadmeGenerator.generate | < 500ms |

### 内存使用

- 基础内存：< 50MB
- 100 图层处理：< 80MB
- 200 图层处理：< 100MB

---

## 边界情况覆盖

### 测试覆盖的场景

1. **空输入处理**
   - 空 PSD 文档
   - 空图层列表
   - 空页面

2. **极端数值**
   - 超大图层数量（1000+）
   - 超大尺寸（999999x999999）
   - 极小尺寸（0.001x0.001）
   - 零画布

3. **特殊字符**
   - Unicode 文字（中文、韩文、日文等）
   - 路径分隔符（/、\、:）
   - 特殊符号（*、?、"、|）
   - 超长名称（1000+ 字符）

4. **数据异常**
   - 缺失必需字段
   - 负坐标
   - 循环引用
   - 孤儿图层

---

## 持续集成

### CI 配置示例

```yaml
# .github/workflows/test.yml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install pytest pytest-cov
      - name: Run integration tests
        run: python3 -m pytest skills/psd-parser/level9-integration/ -v
```

---

## 故障排查

### 测试失败

1. 检查 Python 版本（需要 3.8+）
2. 确保所有依赖已安装
3. 检查路径是否正确

### 性能不达标

1. 检查系统负载
2. 增加预热迭代次数
3. 查看内存使用情况

### ImportError

```bash
# 确保项目根目录在 PYTHONPATH
export PYTHONPATH=$PYTHONPATH:~/Desktop/agent/projects/psd-smart-cut
```

---

## 贡献指南

添加新的集成测试：

1. 在对应的测试文件中添加测试类
2. 遵循命名规范：`Test<Level><Feature>`
3. 添加详细的文档字符串
4. 确保测试用例独立，不依赖外部状态

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.9.0 | 2026-03-25 | 初始版本，包含集成测试、性能测试、边界测试 |
