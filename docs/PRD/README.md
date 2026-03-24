# PSD Smart Cut - 产品需求文档

**版本：** v0.1  
**日期：** 2026-03-24  
**状态：** 开发中  

---

## 🎯 产品概述

**产品名称：** PSD Smart Cut  
**产品类型：** AI 驱动的 PSD 智能切图工作流系统  
**核心价值：** 将设计师提供的 PSD 文件自动转化为开发团队可用的资源包  

---

## 📋 核心功能

| 功能 | 说明 |
|------|------|
| PSD 解析 | 多 Page 支持，嵌套图层解析 |
| AI 识别 | 自动识别组件（登录框/banner/轮播图等） |
| 智能切图 | 智能画布切割，背景/内容分离 |
| 文档生成 | Markdown + JSON 规范文档 |
| 多 Agent 协作 | 120+ 原子化 Agent，职责单一 |

---

## 👥 目标用户

| 用户 | 场景 |
|------|------|
| 开发团队 | 接收 AI 处理的 PSD 资源包 |
| UI 设计师 | 提供 PSD，获取规范文档 |
| AI Agent | 使用工作流处理 PSD（Claude/Cursor/Claw） |

---

## 🏗️ 系统架构

### Agent 分层

```
Level 1: 解析层     → page-extractor, layer-reader, hierarchy-builder
Level 2: 分类层     → image/text/vector/group/decorator-classifier
Level 3: 识别层     → screenshot, region-detector, component-namer
Level 4: 策略层     → canvas-analyzer, strategy-selector
Level 5: 导出层     → asset-exporter, naming-manager
Level 6: 提取层     → text-reader, font-analyzer, style-extractor
Level 7: 生成层     → dimension/position/style-generator
Level 8: 文档层     → readme-generator, manifest-generator
```

### 技术栈

| 组件 | 技术选型 |
|------|----------|
| PSD 解析 | psd-tools (Python) |
| AI 识别 | MiniMax VLM / GPT-4V |
| 工作流编排 | OpenClaw subagent / Lobster |
| 输出格式 | PNG + JSON Schema |
| 文档格式 | Markdown |

---

## 📁 输出结构

```
output/
├── assets/
│   └── {page-name}/
│       ├── images/          # 切片图片
│       ├── vectors/        # SVG 矢量
│       └── text/           # 纯文字
├── specs/
│   ├── manifest.json       # 整体清单
│   ├── assets.json         # 资产规格
│   └── components.json     # 组件定义
└── docs/
    ├── README.md           # 总览文档
    ├── CHANGELOG.md        # 变更记录
    └── COMPONENT_MAP.md    # 组件地图
```

---

## 📊 版本计划

| 版本 | 阶段 | 目标 |
|------|------|------|
| v0.1 | 基础架构 | 项目结构、核心系统、PSD 解析 |
| v0.2 | 分类层 | 图层分类 Agent |
| v0.3 | 识别层 | 组件识别 Agent |
| v0.4 | 策略层 | 切割策略 Agent |
| v0.5 | 导出层 | 资产导出 Agent |
| v0.6 | 提取层 | 文字/样式提取 |
| v0.7 | 生成层 | 规格生成 |
| v0.8 | 文档层 | 文档生成 |
| v0.9 | 集成测试 | 端到端测试 |
| v1.0 | 交付 | 正式发布 |

---

## ✅ 验收标准

- [ ] PSD 文件可正常解析
- [ ] 多 Page 支持
- [ ] 图层分类准确率 > 80%
- [ ] 组件识别合理
- [ ] JSON 规范完整
- [ ] Markdown 文档可读
- [ ] 可被 Claude/Cursor/Claw 调用
