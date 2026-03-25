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

## [v0.5] - 导出层 ✅

### Added
- asset_exporter.py - 资产导出器（PNG/JPG/WebP/SVG 格式）
- format_converter.py - 格式转换器（格式转换、压缩、优化）
- naming_manager.py - 命名管理器（模板变量、冲突检测、规范化）
- metadata_attacher.py - 元数据附加器（EXIF、manifest.json）
- exporter.py - 统一导出器（协调所有模块、生成报告）
- __init__.py - 模块导出
- SKILL.md - 技能文档
- test_level5.py - 集成测试（40 个测试用例）

### Completed
- [x] AssetExporter - 资产导出器
- [x] FormatConverter - 格式转换器
- [x] NamingManager - 命名管理器
- [x] MetadataAttacher - 元数据附加器
- [x] Exporter - 统一导出接口
- [x] 集成测试 - 40 个测试用例全部通过（mock 模式）

---

## [v0.6] - 提取层 ✅

### Added
- text_reader.py - 文字读取器（文字内容、编码、RTL、特殊字符、段落、对齐）
- font_analyzer.py - 字体分析器（字体族、大小、粗细、颜色、行高、字间距）
- style_extractor.py - 样式提取器（不透明度、混合模式、阴影、描边、渐变）
- position_reader.py - 位置读取器（坐标、尺寸、旋转、锚点、对齐、响应式断点）
- extractor.py - 统一提取器（协调所有模块、批量处理、JSON 导出）
- __init__.py - 模块导出
- SKILL.md - 技能文档
- test_level6.py - 集成测试（38 个测试用例）

### Completed
- [x] TextReader - 文字读取器
- [x] FontAnalyzer - 字体分析器
- [x] StyleExtractor - 样式提取器
- [x] PositionReader - 位置读取器
- [x] Extractor - 统一提取器
- [x] 集成测试 - 38 个测试用例全部通过（mock 模式）

---

## [v0.7] - 生成层 ✅

### Added
- dimension_generator.py - 尺寸生成器（多单位、响应式、缩放因子、单位转换）
- position_generator.py - 位置生成器（CSS position、Flex/Grid、边距/内边距）
- style_generator.py - 样式生成器（CSS、Tailwind、iOS、Android、主题变量）
- spec_validator.py - 规格验证器（完整性、冲突检测、CSS 语法、断点验证）
- schema.py - JSON Schema 定义（组件规格、组件集合规格）
- generator.py - 统一生成器（协调所有模块、批量处理、JSON 导出）
- __init__.py - 模块导出
- SKILL.md - 技能文档
- test_level7.py - 集成测试（50 个测试用例）

### Completed
- [x] DimensionGenerator - 尺寸生成器
- [x] PositionGenerator - 位置生成器
- [x] StyleGenerator - 样式生成器
- [x] SpecValidator - 规格验证器
- [x] SpecGenerator - 统一生成器
- [x] 集成测试 - 50 个测试用例全部通过（mock 模式）

---

## [v0.8] - 文档层 ✅

### Added
- readme_generator.py - README 生成器（徽章、功能列表、安装/使用示例）
- changelog_generator.py - CHANGELOG 生成器（git log 解析、版本分组）
- manifest_generator.py - 资产清单生成器（JSON/YAML 导出）
- preview_generator.py - HTML 预览页生成器（组件卡片、关系图、统计）
- doc_aggregator.py - 文档聚合器（验证、索引、目录结构）
- __init__.py - 模块导出
- SKILL.md - 技能文档
- test_level8.py - 集成测试

### Completed
- [x] ReadmeGenerator - README 生成器
- [x] ChangelogGenerator - CHANGELOG 生成器
- [x] ManifestGenerator - 资产清单生成器
- [x] PreviewGenerator - HTML 预览页生成器
- [x] DocAggregator - 文档聚合器
- [x] 集成测试 - mock 模式测试通过

---

## [v0.9] - 集成测试 ✅

### Added
- `level9-integration/test_integration.py` - 端到端集成测试（40+ 测试用例）
- `level9-integration/performance_test.py` - 性能基准测试
- `level9-integration/edge_case_test.py` - 边界情况测试（20+ 测试用例）
- `level9-integration/SKILL.md` - 技能文档
- `level9-integration/__init__.py` - 模块初始化

### Completed
- [x] 端到端集成测试 - Level 1-8 全部模块工作流测试
- [x] 性能基准测试 - 各模块响应时间、内存使用、批量处理能力
- [x] 边界情况测试 - 空 PSD、超大图层数量、特殊字符、缺失元数据
- [x] Mock 模式支持无 PSD 环境测试

---

## [v1.0] - 正式发布

### Planned
- [ ] README 完善
- [ ] 使用文档
- [ ] Claude/Cursor 集成
- [ ] GitHub Release
