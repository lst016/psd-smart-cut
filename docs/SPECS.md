# PSD Smart Cut - 技能规范

**版本：** v0.1  
**目标：** 原子化、可复用、强边界  

---

## 🎯 设计原则

### 核心原则

| 原则 | 说明 |
|------|------|
| **单一职责** | 每个 Agent 只做一件事 |
| **强边界** | 输入/输出/职责明确 |
| **上下文隔离** | 单任务不超过 2-3 个工具调用 |
| **可独立验证** | 每个子任务可单独测试 |
| **标准化输出** | 每个节点输出格式统一 |

---

## 📦 Agent 规范

### 标准 Agent 结构

```yaml
agent:
  name: {agent-name}
  level: {1-8}
  input:
    type: {输入类型}
    schema: {JSON Schema}
  output:
    type: {输出类型}
    schema: {JSON Schema}
  modules:
    - name: {module-name}
      action: {具体操作}
  error-handling:
    - case: {错误情况}
      action: {处理方式}
```

### Level 1: 解析层

| Agent | 职责 | 输入 | 输出 |
|-------|------|------|------|
| page-extractor | 提取 Page | PSD | Page 列表 |
| layer-reader | 读取图层 | Page | Layer 列表 |
| hierarchy-builder | 构建层级树 | Layer 列表 | Tree |
| hidden-marker | 标记隐藏 | Layer | 标记列表 |
| locked-detector | 检测锁定 | Layer | 锁定报告 |

### Level 2: 分类层

| Agent | 职责 | 输入 | 输出 |
|-------|------|------|------|
| image-classifier | 图片分类 | Layer | 类型=图片 |
| text-classifier | 文字分类 | Layer | 类型=文字 |
| vector-classifier | 矢量分类 | Layer | 类型=矢量 |
| group-classifier | 组分类 | Layer | 类型=组 |
| decorator-classifier | 装饰分类 | Layer | 类型=装饰 |

### Level 3-8: 识别/策略/导出/提取/生成/文档层

（详见各层级详细规范）

---

## 🔧 通用模块

### 系统层（所有 Agent 共享）

```yaml
common:
  - name: error-handler
    description: 统一错误处理
  - name: config-loader
    description: 配置加载
  - name: logger
    description: 日志记录
  - name: validator
    description: 输入输出校验
  - name: metrics
    description: 指标记录
```

---

## 📝 JSON Schema 规范

### Asset Schema

```json
{
  "id": "string",
  "name": "string",
  "type": "image|text|vector|group|decorator",
  "dimensions": {
    "width": "number",
    "height": "number"
  },
  "position": {
    "x": "number",
    "y": "number"
  },
  "export": {
    "format": "png|svg",
    "path": "string",
    "quality": "number"
  },
  "metadata": {
    "page": "string",
    "parent": "string",
    "children": ["string"],
    "hidden": "boolean",
    "locked": "boolean"
  }
}
```

### Manifest Schema

```json
{
  "version": "string",
  "psd_name": "string",
  "pages": [
    {
      "name": "string",
      "components": "number",
      "assets": "number"
    }
  ],
  "summary": {
    "total_components": "number",
    "total_assets": "number"
  }
}
```

---

## 🔄 调用流程

```
用户/Agent
    ↓
Orchestrator（编排器）
    ↓
Level 1-8 Agents（按顺序/并行执行）
    ↓
输出验证
    ↓
文档生成
    ↓
交付
```

---

## 📊 版本管理

每个版本完成后：
1. Git 提交（`git add . && git commit -m "feat: v0.x description"`)
2. 自评复盘
3. 更新 CHANGELOG.md
4. 开始下一个版本
