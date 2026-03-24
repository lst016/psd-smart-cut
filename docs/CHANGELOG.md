# Changelog

All notable changes to this project will be documented in this file.

## [v0.1] - 2026-03-24 - 基础架构 ✅

### Added
- 项目目录结构创建
- Git 仓库初始化
- PRD 文档
- 技能规范文档
- 版本计划文档
- 核心配置文件 (config.yaml)
- 通用模块 (error_handler, logger, validator, metrics)
- PSD 解析器 (psd_parser.py)
- Page 提取器 (page_extractor.py)
- Layer 读取器 (layer_reader.py)
- 层级树构建器 (hierarchy_builder.py)
- 隐藏图层标记器 (hidden_marker.py)
- 锁定图层检测器 (locked_detector.py)
- 单元测试 (test_level1.py)

### Completed
- [x] config.yaml 配置文件
- [x] error_handler.py 错误处理
- [x] logger.py 日志系统
- [x] psd_parser.py PSD 解析
- [x] Level 1 Agents 实现
- [x] 单元测试

---

## [v0.2] - 分类层 ✅

### Added
- classifier.py - 5 个分类器 + LayerClassifier
- image_classifier.py - 图片子类型细分 (button/icon/background/photo/illustration 等)
- text_classifier.py - 文字类型/语言检测
- __init__.py - 模块导出
- SKILL.md - 技能文档
- test_level2.py - 集成测试（26 个测试用例）

### Completed
- [x] ImageClassifier - 图片分类器
- [x] TextClassifier - 文字分类器
- [x] VectorClassifier - 矢量分类器
- [x] GroupClassifier - 组分类器
- [x] DecoratorClassifier - 装饰分类器
- [x] LayerClassifier - 统一分类接口
- [x] ImageSubCategory - 图片子类型枚举
- [x] TextType - 文字类型枚举
- [x] TextLanguage - 语言检测枚举
- [x] 集成测试 - 26 个测试用例全部通过

---

## [v0.3] - 识别层 ✅

### Added
- screenshot_capturer.py - 图层截图捕获器（psd-tools + mock 降级）
- region_detector.py - 区域检测器（边界矩形、重叠检测、有效区域）
- component_namer.py - 组件命名器（AI/规则推断、语义化名称）
- boundary_analyzer.py - 边界分析器（边缘类型、质量分数、切割点）
- function_analyzer.py - 功能分析器（交互类型、样式属性、功能描述）
- recognizer.py - 统一识别器（协调所有识别器，批量处理）
- __init__.py - 模块导出
- SKILL.md - 技能文档
- test_level3.py - 集成测试（28 个测试用例）

### Completed
- [x] ScreenshotCapturer - 图层截图捕获器
- [x] RegionDetector - 区域检测器
- [x] ComponentNamer - 组件命名器
- [x] BoundaryAnalyzer - 边界分析器
- [x] FunctionAnalyzer - 功能分析器
- [x] Recognizer - 统一识别接口
- [x] 集成测试 - 28 个测试用例全部通过（mock 模式）

---

## [v0.4] - 策略层 ✅

### Added
- canvas_analyzer.py - 画布分析器（密度热力图、切割线识别）
- strategy_selector.py - 策略选择器（FLAT/GROUP_BY_TYPE/GROUP_BY_PAGE/PRESERVE_HIERARCHY/SMART_MERGE）
- overlap_detector.py - 重叠检测器（遮挡关系、优先级确定）
- quality_evaluator.py - 质量评估器（切割精度、边缘质量、效率）
- strategy.py - 统一策略器（协调所有模块、生成切割计划）
- __init__.py - 模块导出
- SKILL.md - 技能文档
- test_level4.py - 集成测试（29 个测试用例）

### Completed
- [x] CanvasAnalyzer - 画布分析器
- [x] StrategySelector - 策略选择器
- [x] OverlapDetector - 重叠检测器
- [x] QualityEvaluator - 质量评估器
- [x] Strategy - 统一策略接口
- [x] 集成测试 - 29 个测试用例全部通过（mock 模式）

---

## [v0.5] - 导出层

### Planned
- [ ] asset_exporter
- [ ] format_converter
- [ ] naming_manager
- [ ] metadata_attacher
- [ ] 导出集成测试

---

## [v0.6] - 提取层

### Planned
- [ ] text_reader
- [ ] font_analyzer
- [ ] style_extractor
- [ ] position_reader
- [ ] 提取集成测试

---

## [v0.7] - 生成层

### Planned
- [ ] dimension_generator
- [ ] position_generator
- [ ] style_generator
- [ ] spec_validator
- [ ] JSON Schema 定义

---

## [v0.8] - 文档层

### Planned
- [ ] readme_generator
- [ ] changelog_generator
- [ ] manifest_generator
- [ ] preview_generator
- [ ] doc_aggregator

---

## [v0.9] - 集成测试

### Planned
- [ ] 完整流程测试
- [ ] 性能测试
- [ ] 边界情况测试
- [ ] 文档完善

---

## [v1.0] - 正式发布

### Planned
- [ ] README 完善
- [ ] 使用文档
- [ ] Claude/Cursor 集成
- [ ] GitHub Release
