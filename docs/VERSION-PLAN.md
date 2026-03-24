# PSD Smart Cut - 版本计划

**当前版本：** v0.1  
**开始日期：** 2026-03-24  
**目标完成日期：** 待定  

---

## 📋 版本路线图

### ✅ v0.1 - 基础架构（已完成）

**目标：** 建立项目骨架，核心系统

**任务清单：**

| # | 任务 | 状态 | 负责人 |
|---|------|------|--------|
| 1 | 项目目录结构 | ✅ | 牛牛 |
| 2 | Git 初始化 | ✅ | 牛牛 |
| 3 | 核心配置文件 | ✅ | 牛牛 |
| 4 | 错误处理系统 | ✅ | 牛牛 |
| 5 | 日志系统 | ✅ | 牛牛 |
| 6 | PSD 解析封装 | ✅ | 牛牛 |
| 7 | Level 1 Agents | ✅ | 牛牛 |
| 8 | 单元测试 | ✅ | 牛牛 |

**交付物：**
- [x] 完整的目录结构
- [x] config.yaml
- [x] error_handler.py
- [x] logger.py
- [x] psd_parser.py
- [x] page_extractor skill
- [x] layer_reader skill
- [x] hierarchy_builder skill
- [x] hidden_marker skill
- [x] locked_detector skill

**验收标准：**
- [x] 可成功解析 PSD 文件
- [x] 可提取 Page 列表
- [x] 可读取 Layer 列表
- [x] 错误处理正常
- [x] 日志记录正常

**完成时间：** 2026-03-24

**v0.1 复盘：**
- ✅ 项目结构清晰，模块化良好
- ✅ 6 个 Level 1 模块全部完成
- ✅ 单元测试覆盖核心功能
- ⚠️ psd-tools 依赖需在环境安装

---

### 🔲 v0.2 - 分类层

**目标：** 实现图层分类 Agent

**任务清单：**
| # | 任务 | 状态 |
|---|------|------|
| 1 | image_classifier | ⏳ |
| 2 | text_classifier | ⏳ |
| 3 | vector_classifier | ⏳ |
| 4 | group_classifier | ⏳ |
| 5 | decorator_classifier | ⏳ |
| 6 | 分类集成测试 | ⏳ |

---

### 🔲 v0.3 - 识别层

**目标：** 实现组件识别 Agent

**任务清单：**
| # | 任务 | 状态 |
|---|------|------|
| 1 | screenshot_capturer | ⏳ |
| 2 | region_detector | ⏳ |
| 3 | component_namer | ⏳ |
| 4 | boundary_analyzer | ⏳ |
| 5 | function_analyzer | ⏳ |
| 6 | AI 识别集成 | ⏳ |

---

### 🔲 v0.4 - 策略层

**目标：** 实现切割策略 Agent

**任务清单：**
| # | 任务 | 状态 |
|---|------|------|
| 1 | canvas_analyzer | ⏳ |
| 2 | strategy_selector | ⏳ |
| 3 | overlap_detector | ⏳ |
| 4 | quality_evaluator | ⏳ |
| 5 | 策略集成测试 | ⏳ |

---

### 🔲 v0.5 - 导出层

**目标：** 实现资产导出 Agent

**任务清单：**
| # | 任务 | 状态 |
|---|------|------|
| 1 | asset_exporter | ⏳ |
| 2 | format_converter | ⏳ |
| 3 | naming_manager | ⏳ |
| 4 | metadata_attacher | ⏳ |
| 5 | 导出集成测试 | ⏳ |

---

### 🔲 v0.6 - 提取层

**目标：** 实现文字/样式提取

**任务清单：**
| # | 任务 | 状态 |
|---|------|------|
| 1 | text_reader | ⏳ |
| 2 | font_analyzer | ⏳ |
| 3 | style_extractor | ⏳ |
| 4 | position_reader | ⏳ |
| 5 | 提取集成测试 | ⏳ |

---

### 🔲 v0.7 - 生成层

**目标：** 实现规格生成

**任务清单：**
| # | 任务 | 状态 |
|---|------|------|
| 1 | dimension_generator | ⏳ |
| 2 | position_generator | ⏳ |
| 3 | style_generator | ⏳ |
| 4 | spec_validator | ⏳ |
| 5 | JSON Schema 定义 | ⏳ |

---

### 🔲 v0.8 - 文档层

**目标：** 实现文档生成

**任务清单：**
| # | 任务 | 状态 |
|---|------|------|
| 1 | readme_generator | ⏳ |
| 2 | changelog_generator | ⏳ |
| 3 | manifest_generator | ⏳ |
| 4 | preview_generator | ⏳ |
| 5 | doc_aggregator | ⏳ |

---

### 🔲 v0.9 - 集成测试

**目标：** 端到端测试

**任务清单：**
| # | 任务 | 状态 |
|---|------|------|
| 1 | 完整流程测试 | ⏳ |
| 2 | 性能测试 | ⏳ |
| 3 | 边界情况测试 | ⏳ |
| 4 | 文档完善 | ⏳ |

---

### 🚀 v1.0 - 正式发布

**目标：** 交付可用产品

**任务清单：**
| # | 任务 | 状态 |
|---|------|------|
| 1 | README 完善 | ⏳ |
| 2 | 使用文档 | ⏳ |
| 3 | Claude/Cursor 集成 | ⏳ |
| 4 | GitHub Release | ⏳ |

---

## 📊 进度统计

| 版本 | 任务数 | 完成 | 进行中 | 待开始 |
|------|--------|------|--------|--------|
| v0.1 | 8 | 2 | 0 | 6 |
| v0.2 | 6 | 0 | 0 | 6 |
| v0.3 | 6 | 0 | 0 | 6 |
| v0.4 | 5 | 0 | 0 | 5 |
| v0.5 | 5 | 0 | 0 | 5 |
| v0.6 | 5 | 0 | 0 | 5 |
| v0.7 | 5 | 0 | 0 | 5 |
| v0.8 | 5 | 0 | 0 | 5 |
| v0.9 | 4 | 0 | 0 | 4 |
| v1.0 | 4 | 0 | 0 | 4 |
| **总计** | **53** | **2** | **0** | **51** |

---

## 🔄 开发规则

1. **小步快跑** - 每个版本控制在 10 个任务以内
2. **每步必测** - 完成任务后立即测试
3. **Git 提交** - 每个功能单独提交
4. **自评复盘** - 版本完成后复盘
5. **文档更新** - 任务完成即更新文档
