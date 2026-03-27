# Claude Integration Guide

This guide is for using PSD Smart Cut from Claude-based environments.

## Recommended Entry Points

Use the standard import path:

```python
from skills.psd_parser.level1_parse import parse_psd, extract_pages, read_layers
from skills.psd_parser.level9_integration import run_full_pipeline
```

Avoid relying on the legacy `skills/psd-parser/...` filesystem naming in example code. The supported public package path is `skills.psd_parser`.

## Suggested Working Style

For Claude Code or similar agentic workflows:

1. start with `python -m skills.cli --help`
2. verify dependencies with `pip install -r requirements.txt`
3. use `examples/basic_parse.py` for a small Level 1 smoke test
4. use `run_full_pipeline(...)` for end-to-end orchestration

## Useful Commands

```bash
python -m skills.cli --help
python -m skills.cli process design.psd --output ./output
python -m pytest skills/psd-parser -q
```

## Repository Map

```text
skills/
|-- cli.py
|-- psd_parser/                # stable public import alias
`-- psd-parser/                # implementation modules
    |-- level1-parse/
    |-- level2-classify/
    |-- level3_recognize/
    |-- level4-strategy/
    |-- level5-export/
    |-- level6-extract/
    |-- level7-generate/
    |-- level8-document/
    `-- level9-integration/
```

## Notes

- The repository currently includes one maintained example script: `examples/basic_parse.py`.
- CLI support is intentionally small and centered on the `process` command.
- If AI dependencies are not installed, lower-level parsing and many compatibility-oriented tests still work.
