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

### ✅ v0.2 - 分类层（已完成）

**目标：** 实现图层分类 Agent

**任务清单：**
| # | 任务 | 状态 |
|---|------|------|
| 1 | image_classifier | ✅ |
| 2 | text_classifier | ✅ |
| 3 | vector_classifier | ✅ |
| 4 | group_classifier | ✅ |
| 5 | decorator_classifier | ✅ |
| 6 | 分类集成测试 | ✅ |

**交付物：**
- [x] classifier.py - 5 个分类器 + LayerClassifier
- [x] image_classifier.py - 图片子类型细分
- [x] text_classifier.py - 文字类型/语言检测
- [x] __init__.py - 模块导出
- [x] SKILL.md - 技能文档
- [x] test_level2.py - 集成测试（26 个测试用例）

**验收标准：**
- [x] 5 个分类器可独立使用
- [x] 图片子类型细分（button/icon/background 等）
- [x] 文字类型判断（heading/body/label 等）
- [x] 语言检测（zh/en/mixed）
- [x] 批量分类支持
- [x] 集成测试全部通过

**完成时间：** 2026-03-24

**v0.2 复盘：**
- ✅ 5 个分类器全部完成
- ✅ 图片/文字子类型细分完善
- ✅ 启发式规则（名称匹配）已实现
- ⚠️ AI 集成待接入 MiniMax VLM

---

### ✅ v0.3 - 识别层（已完成）

**目标：** 实现组件识别 Agent

**任务清单：**
| # | 任务 | 状态 |
|---|------|------|
| 1 | screenshot_capturer | ✅ |
| 2 | region_detector | ✅ |
| 3 | component_namer | ✅ |
| 4 | boundary_analyzer | ✅ |
| 5 | function_analyzer | ✅ |
| 6 | AI 识别集成 | ✅ |

**交付物：**
- [x] screenshot_capturer.py - 图层截图捕获器（psd-tools + mock 降级）
- [x] region_detector.py - 区域检测器（边界矩形、重叠检测、有效区域）
- [x] component_namer.py - 组件命名器（AI/规则推断、语义化名称）
- [x] boundary_analyzer.py - 边界分析器（边缘类型、质量分数、切割点）
- [x] function_analyzer.py - 功能分析器（交互类型、样式属性、功能描述）
- [x] recognizer.py - 统一识别器（协调所有识别器，批量处理）
- [x] __init__.py - 模块导出
- [x] SKILL.md - 技能文档
- [x] test_level3.py - 集成测试（28 个测试用例）

**验收标准：**
- [x] 5 个识别器可独立使用
- [x] Mock 模式测试通过（无需 PSD 文件）
- [x] 批量处理支持
- [x] 统一识别接口
- [x] 结果缓存
- [x] 集成测试全部通过

**完成时间：** 2026-03-24

**v0.3 复盘：**
- ✅ 5 个识别器全部完成
- ✅ Mock 模式支持无 PSD 环境测试
- ✅ AI 识别支持 MiniMax VLM 接入
- ⚠️ psd-tools 需在生产环境安装以支持真实 PSD 截图

---

### ✅ v0.4 - 策略层（已完成）

**目标：** 实现切割策略 Agent

**任务清单：**
| # | 任务 | 状态 |
|---|------|------|
| 1 | canvas_analyzer | ✅ |
| 2 | strategy_selector | ✅ |
| 3 | overlap_detector | ✅ |
| 4 | quality_evaluator | ✅ |
| 5 | 策略集成测试 | ✅ |

**交付物：**
- [x] canvas_analyzer.py - 画布分析器（密度热力图、切割线识别）
- [x] strategy_selector.py - 策略选择器（5 种策略类型）
- [x] overlap_detector.py - 重叠检测器（遮挡关系、优先级）
- [x] quality_evaluator.py - 质量评估器（切割精度、边缘质量）
- [x] strategy.py - 统一策略器（协调所有模块）
- [x] __init__.py - 模块导出
- [x] SKILL.md - 技能文档
- [x] test_level4.py - 集成测试（29 个测试用例）

**验收标准：**
- [x] 4 个策略模块可独立使用
- [x] Mock 模式测试通过（无需 PSD 文件）
- [x] 批量处理支持
- [x] 统一策略接口
- [x] 计划优化功能
- [x] JSON 导出支持
- [x] 集成测试全部通过

**完成时间：** 2026-03-24

**v0.4 复盘：**
- ✅ 4 个策略模块全部完成
- ✅ Mock 模式支持无 PSD 环境测试
- ✅ 5 种切割策略（FLAT/GROUP_BY_TYPE/GROUP_BY_PAGE/PRESERVE_HIERARCHY/SMART_MERGE）
- ✅ 切割计划优化功能
- ⚠️ 真实 PSD 集成待测试

---

### ✅ v0.5 - 导出层（已完成）

**目标：** 实现资产导出 Agent

**任务清单：**
| # | 任务 | 状态 |
|---|------|------|
| 1 | asset_exporter | ✅ |
| 2 | format_converter | ✅ |
| 3 | naming_manager | ✅ |
| 4 | metadata_attacher | ✅ |
| 5 | 导出集成测试 | ✅ |

**交付物：**
- [x] asset_exporter.py - 资产导出器（PNG/JPG/WebP/SVG）
- [x] format_converter.py - 格式转换器（格式转换、压缩）
- [x] naming_manager.py - 命名管理器（模板、冲突检测）
- [x] metadata_attacher.py - 元数据附加器（EXIF、manifest）
- [x] exporter.py - 统一导出器（协调所有模块）
- [x] __init__.py - 模块导出
- [x] SKILL.md - 技能文档
- [x] test_level5.py - 集成测试（40 个测试用例）

**验收标准：**
- [x] 4 个导出模块可独立使用
- [x] Mock 模式测试通过（无需 PSD 文件）
- [x] 批量处理支持
- [x] 统一导出接口
- [x] manifest.json 生成
- [x] 集成测试全部通过

**完成时间：** 2026-03-24

**v0.5 复盘：**
- ✅ 4 个导出模块全部完成
- ✅ Mock 模式支持无 PSD 环境测试
- ✅ 40 个测试用例全部通过
- ✅ 支持 PNG/JPG/WebP/SVG 格式
- ✅ 命名模板支持（{type}/{name}）
- ⚠️ 真实 PSD 导出待测试

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
| v0.1 | 8 | 8 | 0 | 0 |
| v0.2 | 6 | 6 | 0 | 0 |
| v0.3 | 6 | 6 | 0 | 0 |
| v0.4 | 5 | 5 | 0 | 0 |
| v0.5 | 5 | 5 | 0 | 0 |
| v0.6 | 5 | 0 | 0 | 5 |
| v0.7 | 5 | 0 | 0 | 5 |
| v0.8 | 5 | 0 | 0 | 5 |
| v0.9 | 4 | 0 | 0 | 4 |
| v1.0 | 4 | 0 | 0 | 4 |
| **总计** | **53** | **35** | **0** | **18** |

---

## 🔄 开发规则

1. **小步快跑** - 每个版本控制在 10 个任务以内
2. **每步必测** - 完成任务后立即测试
3. **Git 提交** - 每个功能单独提交
4. **自评复盘** - 版本完成后复盘
5. **文档更新** - 任务完成即更新文档
