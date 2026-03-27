# PSD Smart Cut User Guide

**Version:** v1.0.0  
**Last Updated:** 2026-03-25

## Overview

PSD Smart Cut is a Python-based PSD processing toolkit. It focuses on:

- parsing PSD structure into pages and layers
- classifying layers into higher-level categories
- optionally running recognition flows
- building cut and export plans
- exporting assets and manifests

The most reliable public entrypoints today are the `skills.psd_parser.*` import path and the CLI command `python -m skills.cli process ...`.

## Installation

Requirements:

- Python 3.10+
- pip

Install dependencies:

```bash
pip install -r requirements.txt
```

Optional AI dependencies:

```bash
pip install openai minimax-api
```

## Quick Start

### Parse a PSD

```python
from skills.psd_parser.level1_parse import LayerFilter, extract_pages, parse_psd, read_layers

document = parse_psd("design.psd")
print(document.page_count)
print(document.total_layers)

pages = extract_pages("design.psd")
for page in pages.pages:
    print(page["name"], page["width"], page["height"])

layers = read_layers("design.psd", page_index=0, filter_type=LayerFilter.ALL)
print(layers.layer_count)
```

### Run the full pipeline

```python
from skills.psd_parser.level9_integration import run_full_pipeline

result = run_full_pipeline(
    psd_path="design.psd",
    output_dir="./output",
    strategy="SMART_MERGE",
    formats=["png", "webp"],
)

print(result.output_dir)
print(result.manifest_paths)
```

### Use the CLI

```bash
python -m skills.cli --help
python -m skills.cli process design.psd --output ./output
python -m skills.cli process design.psd --strategy SMART_MERGE --formats png,webp
```

## Project Workflow

The runtime flow is organized into nine stages:

1. Level 1: PSD parsing
2. Level 2: layer classification
3. Level 3: recognition
4. Level 4: strategy planning
5. Level 5: export
6. Level 6: text and style extraction
7. Level 7: spec generation
8. Level 8: documentation generation
9. Level 9: integration workflow

In daily usage, most consumers only need:

- `skills.psd_parser.level1_parse`
- `skills.psd_parser.level9_integration.run_full_pipeline`
- `python -m skills.cli process ...`

## Testing

Run the validated package suite:

```bash
python -m pytest skills/psd-parser -q
```

Smoke checks:

```bash
python -m skills.cli --help
python examples/basic_parse.py
python -m compileall skills examples
```

## Troubleshooting

### `psd-tools` import error

Install the parser dependency:

```bash
pip install psd-tools
```

### No PSD file available during testing

You can still verify the repository with:

```bash
python -m pytest skills/psd-parser -q
python -m skills.cli --help
```

### Recognition stage is not needed

Use:

```bash
python -m skills.cli process design.psd --no-recognizer
```

## Related Docs

- [Usage Guide](./usage.md)
- [Change Log](./CHANGELOG.md)
- [Release Notes](./RELEASE_NOTES.md)
- [Version Plan](./VERSION-PLAN.md)
