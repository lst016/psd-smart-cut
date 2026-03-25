# Changelog

All notable changes to this project will be documented in this file.

## [1.0.2] - 2026-03-25

### Fixed
- **level1**: `PageInfo.layer_count/hidden_count/locked_count` now computed from `layers` property
  - Changed from stored fields to `@property` getters that auto-calculate from layer list
  - Maintains backward compatibility via setter
- **level6**: `FontAnalyzer._parse_font_info()` now handles `text_data` being `str` instead of `dict`
- **level6**: `TextReader._get_text_direction()` and `_get_paragraph_alignment()` now handle `text_data` being `str`
  - Prevents `AttributeError` when parsing PSD files with unexpected text data format

## [1.0.1] - 2026-03-25

### Fixed
- **level6**: `PositionData` instantiation now includes `breakpoints`, `anchor`, and `alignment` fields
  - Fixed `AttributeError: 'PositionData' object has no attribute 'breakpoints'` in `Extractor.extract()`
  - Updated both `read()` and `_create_mock_position()` methods in `PositionReader`
  - All 38 Level 6 tests now pass
  - Resolved 51 errors in `logs/errors.jsonl`

## [1.0.0] - 2026-03-25

### Added
- **v0.1 - 基础架构**: Project skeleton, core systems, 6 Level 1 modules
- **v0.2 - 分类层**: 5 classifiers (image, text, vector, group, decorator)
- **v0.3 - 识别层**: 5 recognizers (screenshot, region, component, boundary, function)
- **v0.4 - 策略层**: 4 strategy modules (canvas, selector, overlap, quality)
- **v0.5 - 导出层**: 4 export modules (exporter, format, naming, metadata)
- **v0.6 - 提取层**: 4 extractors (text, font, style, position)
- **v0.7 - 生成层**: 4 generators (dimension, position, style, spec validator)
- **v0.8 - 文档层**: 5 document generators (readme, changelog, manifest, preview, aggregator)
- **v0.9 - 集成测试**: End-to-end tests, performance benchmarks, edge case tests
- **v1.0 - 正式发布**: README, user guide, Claude/Cursor integration docs

### Features
- Mock mode support for all modules (no PSD file required for testing)
- Multi-platform style generation (CSS, Tailwind, iOS, Android)
- Responsive breakpoint support
- RTL/LTR text direction detection
- Component relationship visualization (SVG diagrams)
- Comprehensive test coverage (260+ test cases)

### Documentation
- `docs/USER_GUIDE.md` - Complete usage guide
- `docs/CLAUDE.md` - Claude AI integration guide
- `docs/CURSOR.md` - Cursor IDE integration guide
- `docs/RELEASE_NOTES.md` - v1.0 release notes

### Known Issues
- 2 pre-existing test failures in Level 1 and Level 8 (unrelated to core functionality)
- Real PSD file integration testing待 v1.1
