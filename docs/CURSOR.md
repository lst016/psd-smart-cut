# Cursor Integration Guide

**For:** Cursor IDE  
**Project:** PSD Smart Cut v1.0.0

---

## Project Overview

PSD Smart Cut is an AI-powered PSD component extraction tool with an 8-layer agent architecture.

**Project Root:** `~/Desktop/agent/projects/psd-smart-cut/`

---

## Cursor-Specific Setup

### 1. Project Root Configuration

Add to `.cursor/mcp.json` or Cursor settings:

```json
{
  "projectRoot": "~/Desktop/agent/projects/psd-smart-cut"
}
```

### 2. Python Path

For imports to work correctly, add to `.cursor/settings.json`:

```json
{
  "python.analysis.extraPaths": [
    "~/Desktop/agent/projects/psd-smart-cut"
  ]
}
```

### 3. Recommended Cursor Extensions

- **Python** (Microsoft) - Python language support
- **Pylance** - Type checking and IntelliSense
- **GitLens** - Git integration
- **Error Lens** - Inline error highlighting

---

## Project Structure

```
psd-smart-cut/
├── skills/
│   └── psd-parser/
│       ├── level1-parse/     # Level 1: PSD Parsing
│       ├── level2_classify.py # Level 2: Classification
│       ├── level3_recognize/  # Level 3: Recognition
│       ├── level4_strategy/   # Level 4: Strategy
│       ├── level5_export/    # Level 5: Export
│       ├── level6-extract/    # Level 6: Extraction
│       ├── level7_generate.py # Level 7: Spec Generation
│       └── level9_integration.py # Integration
├── configs/
│   └── config.yaml
├── docs/
│   ├── USER_GUIDE.md
│   ├── CLAUDE.md
│   ├── VERSION-PLAN.md
│   └── CHANGELOG.md
├── examples/
│   └── basic_parse.py
└── requirements.txt
```

---

## How to Use This Project

### Quick Start Code

```python
# Add to sys.path for imports
import sys
sys.path.insert(0, '~/Desktop/agent/projects/psd-smart-cut')

from skills.psd_parser.level1_parse import parse_psd, read_layers, LayerFilter
from skills.psd_parser.level2_classify import LayerClassifier

# Parse
document = parse_psd("design.psd")
layers = read_layers("design.psd", page_index=0)

# Classify
classifier = LayerClassifier()
classified = classifier.classify(layers)
```

---

## Development Workflow

### 1. Running Tests

```bash
# From project root
cd ~/Desktop/agent/projects/psd-smart-cut

# Run specific level tests
python -m pytest skills/psd_parser/level1-parse/test_level1.py -v

# Run all tests
python -m pytest skills/psd_parser/ -v

# Run with coverage
python -m pytest skills/psd_parser/ --cov=. --cov-report=html
```

### 2. Running Examples

```bash
python examples/basic_parse.py path/to/design.psd
```

### 3. Debugging

Set breakpoints in `skills/psd_parser/` modules. For pytest debugging:

```bash
python -m pytest skills/psd_parser/level1-parse/test_level1.py --pdb
```

---

## Module Reference

### Level 1 - Parsing (`skills/psd_parser/level1_parse/`)

```python
from skills.psd_parser.level1_parse import (
    parse_psd,        # Main parser: parse_psd(file_path) -> PSDDocument
    extract_pages,    # Extract pages: extract_pages(file_path) -> PageResult
    read_layers,      # Read layers: read_layers(file_path, page_index, filter_type)
    LayerFilter,      # Enum: ALL, VISIBLE, HIDDEN, LOCKED
    PSDDocument       # Data class with .version, .width, .height, .get_page_count()
)
```

### Level 2 - Classification (`skills/psd_parser/level2_classify.py`)

```python
from skills.psd_parser.level2_classify import LayerClassifier

classifier = LayerClassifier()
classified = classifier.classify(layers)  # -> List[ClassifiedLayer]
```

### Level 3 - Recognition (`skills/psd_parser/level3_recognize/`)

```python
from skills.psd_parser.level3_recognize import Recognizer

recognizer = Recognizer()
components = recognizer.recognize(layers, screenshots_dir="screenshots/", use_ai=True)
```

### Level 4 - Strategy (`skills/psd_parser/level4_strategy/`)

```python
from skills.psd_parser.level4_strategy import Strategy, CutStrategy

strategy = Strategy()
plan = strategy.generate(components, strategy_type=CutStrategy.SMART_MERGE, optimize=True)
```

### Level 5 - Export (`skills/psd_parser/level5_export/`)

```python
from skills.psd_parser.level5_export import Exporter

exporter = Exporter()
report = exporter.export(components, plan, output_dir="output/", formats=["png"])
```

---

## Configuration File

Edit `configs/config.yaml` to customize behavior:

```yaml
ai:
  provider: "minimax"  # minimax / openai / claude
  vision_model: "MiniMax-VLM"
  confidence_threshold: 0.8

export:
  format_priority: ["png", "jpg", "webp", "svg"]
  default_quality: 1.0
  scales: [1, 2, 3]

cutting:
  strategy: "smart_canvas"
  min_component_size: 10

output:
  base_dir: "./output"
  create_preview: true
```

---

## Cursor Chat Examples

### "Explain this layer classifier"

```python
# In Cursor Chat, you can ask:
# "Explain how skills/psd_parser/level2_classify.py works"
# or
# "Show me the LayerClassifier class and its methods"
```

### "Add a new classifier"

Create `skills/psd_parser/level2_classify/` and add:
- `shape_classifier.py` - For shape/solid color detection
- `update __init__.py` to export the new classifier
- Add tests in `test_level2.py`

### "Fix the export naming"

Check `skills/psd_parser/level5_export/naming_manager.py`:
- `NamingManager.apply_template()` - Template variables
- `NamingManager.resolve_conflicts()` - Conflict resolution

---

## Code Snippets

### Parse PSD and Print Structure

```python
import sys
sys.path.insert(0, '~/Desktop/agent/projects/psd-smart-cut')

from skills.psd_parser.level1_parse import parse_psd

doc = parse_psd("design.psd")
print(f"PSD: {doc.width}x{doc.height}")
print(f"Pages: {doc.get_page_count()}")
print(f"Layers: {doc.total_layers}")
```

### Classify All Layers

```python
from skills.psd_parser.level2_classify import LayerClassifier

classifier = LayerClassifier()
results = classifier.classify(layers)

for r in results:
    print(f"{r.name}: {r.category} / {r.sub_category}")
```

### Run Full Pipeline

```python
from skills.psd_parser.level1_parse import parse_psd, read_layers, LayerFilter
from skills.psd_parser.level2_classify import LayerClassifier
from skills.psd_parser.level3_recognize import Recognizer
from skills.psd_parser.level4_strategy import Strategy, CutStrategy
from skills.psd_parser.level5_export import Exporter

layers = read_layers("design.psd", page_index=0)
classified = LayerClassifier().classify(layers)
components = Recognizer().recognize(classified, use_ai=False)
plan = Strategy().generate(components, strategy_type=CutStrategy.SMART_MERGE)
report = Exporter().export(components, plan, "output/")
```

---

## Testing with Cursor

### Run Tests in Terminal

```bash
cd ~/Desktop/agent/projects/psd-smart-cut
python -m pytest skills/psd_parser/level1-parse/test_level1.py -v
```

### Debug Test Failures

```bash
python -m pytest skills/psd_parser/level1-parse/test_level1.py --pdb -v
```

### Test Coverage

```bash
python -m pytest skills/psd_parser/ --cov=skills --cov-report=term-missing
```

---

## Key Files

| File | Purpose |
|------|---------|
| `skills/psd_parser/level1-parse/psd_parser.py` | Core PSD parsing |
| `skills/psd_parser/level2_classify.py` | Layer classification |
| `skills/psd_parser/level3_recognize/recognizer.py` | Component recognition |
| `skills/psd_parser/level4_strategy/strategy.py` | Cut strategy planning |
| `skills/psd_parser/level5_export/exporter.py` | Asset export |
| `configs/config.yaml` | Configuration |
| `docs/USER_GUIDE.md` | Full user documentation |

---

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError`, ensure:
1. You're running from project root
2. Or use: `sys.path.insert(0, '~/Desktop/agent/projects/psd-smart-cut')`

### PSD File Not Loading

```bash
pip install psd-tools
```

### AI Features Not Working

Set `use_ai=False` in `recognizer.recognize()` or configure API keys in `configs/config.yaml`.

### Tests Failing

All modules support mock mode. Check test files in each level directory for mock data.
