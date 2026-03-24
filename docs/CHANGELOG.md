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

## [v0.2] - 分类层

### Planned
- [ ] image_classifier
- [ ] text_classifier
- [ ] vector_classifier
- [ ] group_classifier
- [ ] decorator_classifier
- [ ] 分类集成测试

---

## [v0.3] - 识别层

### Planned
- [ ] screenshot_capturer
- [ ] region_detector
- [ ] component_namer
- [ ] boundary_analyzer
- [ ] function_analyzer
- [ ] AI 识别集成

---

## [v0.4] - 策略层

### Planned
- [ ] canvas_analyzer
- [ ] strategy_selector
- [ ] overlap_detector
- [ ] quality_evaluator
- [ ] 策略集成测试

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
