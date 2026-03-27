# Changelog

All notable changes to this project will be documented in this file.

## [1.0.3] - 2026-03-25

### Fixed
- **level9**: `edge_case_test.py` and `performance_test.py` mock `PSDDocument` now use correct interface fields (`file_path`, `width`, `height`, `total_layers`)

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
- Project skeleton and core systems
- Multi-level PSD parsing, classification, recognition, strategy, export, extract, generation, and documentation workflows
- CLI and runtime integration entrypoints
- Test suite and integration coverage

### Notes
- This repository later adopted a cleaner documentation layout under `docs/`.
- Early historical records may still contain legacy encoding artifacts from the original draft files.
