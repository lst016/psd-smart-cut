# PSD Smart Cut - User Guide

**Version:** v1.0.0  
**Last Updated:** 2026-03-25

---

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Configuration](#configuration)
5. [Complete Workflow](#complete-workflow)
6. [API Reference](#api-reference)
7. [FAQ](#faq)
8. [Troubleshooting](#troubleshooting)

---

## Overview

PSD Smart Cut is an AI-powered PSD component extraction tool. It parses PSD files, classifies layers, recognizes components via AI vision, generates intelligent cut strategies, and exports production-ready assets.

**Key Features:**
- Multi-page PSD parsing with nested layer support
- AI-driven component recognition (buttons, icons, banners, etc.)
- Smart cutting strategies (FLAT, GROUP_BY_TYPE, SMART_MERGE, etc.)
- Multi-format export (PNG, JPG, WebP, SVG)
- Automatic CSS/Tailwind/iOS/Android spec generation
- Documentation auto-generation (README, CHANGELOG, manifest)

---

## Installation

### Requirements

- Python >= 3.10
- pip

### Steps

```bash
# Clone the repository
git clone https://github.com/lst016/psd-smart-cut.git
cd psd-smart-cut

# Install dependencies
pip install -r requirements.txt

# Optional: Install AI dependencies for vision features
pip install minimax-api  # MiniMax VLM
# or
pip install openai       # OpenAI vision
```

---

## Quick Start

### 1. Parse a PSD File

```python
from skills.psd_parser.level1_parse import parse_psd, extract_pages, read_layers, LayerFilter

# Parse PSD structure
document = parse_psd("design.psd")
print(f"Pages: {document.get_page_count()}")
print(f"Total layers: {document.total_layers}")

# Extract pages
pages = extract_pages("design.psd")
for page in pages.pages:
    print(f"  - {page['name']}: {page['width']}x{page['height']}")

# Read layers (with filter)
layers = read_layers("design.psd", page_index=0, filter_type=LayerFilter.ALL)
print(f"Layers: {layers.layer_count}")
```

### 2. Classify Layers

```python
from skills.psd_parser.level2_classify import LayerClassifier

classifier = LayerClassifier()
classified = classifier.classify(layers)

for layer in classified:
    print(f"  {layer.name}: {layer.category} ({layer.sub_category})")
```

### 3. Recognize Components (with AI)

```python
from skills.psd_parser.level3_recognize import Recognizer

recognizer = Recognizer()
components = recognizer.recognize(
    layers,
    screenshots_dir="screenshots/",
    use_ai=True  # Set to False for rule-based only
)

for comp in components:
    print(f"  {comp.name}: {comp.type} @ {comp.bounds}")
```

### 4. Generate Cut Strategy

```python
from skills.psd_parser.level4_strategy import Strategy, CutStrategy

strategy = Strategy()
plan = strategy.generate(
    components,
    strategy_type=CutStrategy.SMART_MERGE,
    optimize=True
)

print(f"Cut plan: {plan.total_cuts} cuts, {plan.estimated_time:.2f}s")
```

### 5. Export Assets

```python
from skills.psd_parser.level5_export import Exporter

exporter = Exporter()
report = exporter.export(
    components,
    plan,
    output_dir="output/",
    formats=["png", "jpg"]
)

print(f"Exported: {report.total_files} files")
print(f"Manifest: {report.manifest_path}")
```

---

## Configuration

Edit `configs/config.yaml`:

```yaml
# AI Provider Configuration
ai:
  provider: "minimax"  # minimax / openai / claude
  model: "MiniMax-M2.5-highspeed"
  vision_model: "MiniMax-VLM"
  confidence_threshold: 0.8

# Export Configuration
export:
  format_priority:
    - "png"
    - "svg"
  default_quality: 1.0
  scales: [1, 2, 3]  # Export at multiple scales
  naming:
    convention: "snake_case"
    language: "en"
    include_page: true

# Cutting Strategy
cutting:
  strategy: "smart_canvas"
  separate_background: true
  min_component_size: 10
  overlap_threshold: 0.1

# Output
output:
  base_dir: "./output"
  structure:
    - "assets/{page_name}"
    - "specs"
    - "docs"
  create_preview: true
  manifest_format: "json"
```

### Key Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `ai.provider` | minimax | AI vision provider |
| `ai.confidence_threshold` | 0.8 | Min confidence for AI recognition |
| `export.default_quality` | 1.0 | JPEG/WebP quality (0-1) |
| `export.scales` | [1,2,3] | Export scales (for @2x, @3x) |
| `cutting.strategy` | smart_canvas | Cut strategy type |
| `cutting.min_component_size` | 10 | Min pixel size to export |

---

## Complete Workflow

```python
"""
PSD Smart Cut - Complete Workflow Example
"""

from skills.psd_parser.level1_parse import parse_psd, read_layers, LayerFilter
from skills.psd_parser.level2_classify import LayerClassifier
from skills.psd_parser.level3_recognize import Recognizer
from skills.psd_parser.level4_strategy import Strategy, CutStrategy
from skills.psd_parser.level5_export import Exporter
import yaml

def process_psd(psd_path, output_dir="output", use_ai=True):
    """Complete PSD processing pipeline"""
    
    # Load config
    with open("configs/config.yaml") as f:
        config = yaml.safe_load(f)
    
    print("=" * 50)
    print("PSD Smart Cut - Processing")
    print("=" * 50)
    
    # Level 1: Parse
    print("\n[1/5] Parsing PSD...")
    document = parse_psd(psd_path)
    layers = read_layers(psd_path, page_index=0, filter_type=LayerFilter.ALL)
    print(f"  Found {layers.layer_count} layers")
    
    # Level 2: Classify
    print("\n[2/5] Classifying layers...")
    classifier = LayerClassifier()
    classified = classifier.classify(layers)
    print(f"  Classified {len(classified)} layers")
    
    # Level 3: Recognize
    print("\n[3/5] Recognizing components...")
    recognizer = Recognizer()
    components = recognizer.recognize(
        classified,
        screenshots_dir=f"{output_dir}/screenshots/",
        use_ai=use_ai
    )
    print(f"  Recognized {len(components)} components")
    
    # Level 4: Strategy
    print("\n[4/5] Generating cut strategy...")
    strategy = Strategy()
    plan = strategy.generate(
        components,
        strategy_type=CutStrategy.SMART_MERGE,
        optimize=True
    )
    print(f"  Generated plan with {plan.total_cuts} cuts")
    
    # Level 5: Export
    print("\n[5/5] Exporting assets...")
    exporter = Exporter()
    report = exporter.export(
        components,
        plan,
        output_dir=f"{output_dir}/assets/",
        formats=["png"]
    )
    print(f"  Exported {report.total_files} files")
    
    print("\n" + "=" * 50)
    print("Done! Output: " + output_dir)
    print("=" * 50)
    
    return report

# Usage
if __name__ == "__main__":
    report = process_psd("design.psd", "output/")
```

---

## API Reference

### Level 1 - PSD Parsing

```python
from skills.psd_parser.level1_parse import (
    parse_psd,        # Parse PSD file structure
    extract_pages,    # Extract page/mask info
    read_layers,      # Read layers with filtering
    LayerFilter,      # ALL / VISIBLE / HIDDEN / LOCKED
    PSDDocument       # Document data class
)
```

### Level 2 - Classification

```python
from skills.psd_parser.level2_classify import (
    LayerClassifier,   # Main classifier
    ImageClassifier,   # Image subclassifier
    TextClassifier,    # Text layer classifier
    VectorClassifier,  # Vector/shape classifier
    GroupClassifier,   # Group classifier
    DecoratorClassifier
)
```

### Level 3 - Recognition

```python
from skills.psd_parser.level3_recognize import (
    Recognizer,           # Main recognizer
    ScreenshotCapturer,    # Capture layer screenshots
    RegionDetector,       # Detect component regions
    ComponentNamer,        # Name components
    BoundaryAnalyzer,      # Analyze cut boundaries
    FunctionAnalyzer       # Analyze component function
)
```

### Level 4 - Strategy

```python
from skills.psd_parser.level4_strategy import (
    Strategy,             # Main strategy generator
    CanvasAnalyzer,        # Analyze canvas density
    StrategySelector,      # Select cut strategy
    OverlapDetector,       # Detect overlaps
    QualityEvaluator,      # Evaluate cut quality
    CutStrategy            # Strategy type enum
)
```

### Level 5 - Export

```python
from skills.psd_parser.level5_export import (
    Exporter,              # Main exporter
    AssetExporter,         # Export individual assets
    FormatConverter,       # Convert between formats
    NamingManager,         # Manage file naming
    MetadataAttacher       # Attach metadata
)
```

### Level 6 - Extraction

```python
from skills.psd_parser.level6_extract import (
    Extractor,             # Main extractor
    TextReader,            # Read text content
    FontAnalyzer,          # Analyze font properties
    StyleExtractor,        # Extract style (shadow, gradient, etc.)
    PositionReader         # Read position/size
)
```

### Level 7 - Generation

```python
from skills.psd_parser.level7_generate import (
    Generator,              # Main spec generator
    DimensionGenerator,     # Generate dimensions
    PositionGenerator,      # Generate position CSS
    StyleGenerator,         # Generate CSS/Tailwind/iOS/Android
    SpecValidator           # Validate specs
)
```

---

## FAQ

### Q: What PSD formats are supported?

A: `.psd` and `.psb` formats are fully supported via `psd-tools`.

### Q: Do I need AI API keys?

A: No. AI features are optional. The system works with rule-based fallback if AI is disabled (`use_ai=False`).

### Q: What image formats can be exported?

A: PNG, JPG, WebP, and SVG are supported.

### Q: Can I run tests without a PSD file?

A: Yes! All modules support mock mode for testing without actual PSD files.

### Q: How do I customize naming conventions?

A: Edit `configs/config.yaml` → `export.naming` section. Supports `snake_case`, `camelCase`, `kebab-case`.

### Q: What cut strategies are available?

A: FLAT, GROUP_BY_TYPE, GROUP_BY_PAGE, PRESERVE_HIERARCHY, SMART_MERGE. See `level4_strategy.py`.

### Q: How do I contribute?

A: See [docs/CLAUDE.md](./CLAUDE.md) for development guidelines.

---

## Troubleshooting

### Error: "psd-tools not found"

```bash
pip install psd-tools
```

### Error: "No module named 'yaml'"

```bash
pip install PyYAML
```

### Error: "AI recognition failed"

- Check your API key configuration in `configs/config.yaml`
- Or disable AI: `recognizer.recognize(layers, use_ai=False)`

### Slow performance with large PSDs

- Reduce `max_workers` in `configs/config.yaml`
- Enable cache: `performance.cache_enabled: true`

### Export produces wrong dimensions

- Check `export.scales` in config
- Verify `cutting.min_component_size` is not too large

---

## Support

- **GitHub Issues:** https://github.com/lst016/psd-smart-cut/issues
- **Documentation:** [docs/](./)
- **Changelog:** [docs/CHANGELOG.md](./CHANGELOG.md)
