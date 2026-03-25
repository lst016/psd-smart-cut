# Claude Integration Guide

**For:** Claude (claude.ai, Claude Code, Claude Desktop)  
**Project:** PSD Smart Cut v1.0.0

---

## Project Overview

PSD Smart Cut is an AI-powered PSD component extraction tool. It parses PSD files, classifies layers, recognizes components via AI vision, generates intelligent cut strategies, and exports production-ready assets.

**Key Entry Points:**
- `skills/psd_parser/level1_parse.py` - PSD parsing
- `skills/psd_parser/level2_classify.py` - Layer classification
- `skills/psd_parser/level3_recognize/` - Component recognition
- `skills/psd_parser/level4_strategy/` - Cut strategy generation
- `skills/psd_parser/level5_export/` - Asset export
- `skills/psd_parser/level6_extract/` - Text/style extraction
- `skills/psd_parser/level7_generate.py` - Spec generation

---

## Project Structure

```
psd-smart-cut/
├── skills/
│   └── psd-parser/
│       ├── level1-parse/        # Level 1: PSD Parsing
│       │   ├── psd_parser.py    # Core parser (parse_psd, PSDDocument)
│       │   ├── page_extractor.py # Page extraction
│       │   ├── layer_reader.py  # Layer reading
│       │   ├── hierarchy_builder.py
│       │   ├── hidden_marker.py
│       │   ├── locked_detector.py
│       │   └── test_level1.py
│       ├── level2_classify.py   # Level 2: Classification
│       ├── level3_recognize/     # Level 3: Recognition
│       │   ├── recognizer.py
│       │   ├── screenshot_capturer.py
│       │   ├── region_detector.py
│       │   ├── component_namer.py
│       │   ├── boundary_analyzer.py
│       │   ├── function_analyzer.py
│       │   └── test_level3.py
│       ├── level4_strategy/      # Level 4: Strategy
│       │   ├── strategy.py
│       │   ├── canvas_analyzer.py
│       │   ├── strategy_selector.py
│       │   ├── overlap_detector.py
│       │   ├── quality_evaluator.py
│       │   └── test_level4.py
│       ├── level5_export/       # Level 5: Export
│       │   ├── exporter.py
│       │   ├── asset_exporter.py
│       │   ├── format_converter.py
│       │   ├── naming_manager.py
│       │   ├── metadata_attacher.py
│       │   └── test_level5.py
│       ├── level6_extract/      # Level 6: Extraction
│       │   ├── extractor.py
│       │   ├── text_reader.py
│       │   ├── font_analyzer.py
│       │   ├── style_extractor.py
│       │   ├── position_reader.py
│       │   └── test_level6.py
│       ├── level7_generate.py   # Level 7: Spec Generation
│       ├── level8_docs.py       # Level 8: Documentation
│       └── level9_integration.py # Level 9: Integration Tests
├── configs/
│   └── config.yaml
├── docs/
│   ├── USER_GUIDE.md
│   ├── VERSION-PLAN.md
│   └── CHANGELOG.md
├── examples/
│   └── basic_parse.py
├── logs/
└── requirements.txt
```

---

## How to Use This Project

### 1. Parse a PSD File

```python
from skills.psd_parser.level1_parse import parse_psd, extract_pages, read_layers, LayerFilter

document = parse_psd("design.psd")
layers = read_layers("design.psd", page_index=0, filter_type=LayerFilter.ALL)
```

### 2. Classify Layers

```python
from skills.psd_parser.level2_classify import LayerClassifier

classifier = LayerClassifier()
classified = classifier.classify(layers)
```

### 3. Recognize Components

```python
from skills.psd_parser.level3_recognize import Recognizer

recognizer = Recognizer()
components = recognizer.recognize(layers, screenshots_dir="screenshots/", use_ai=True)
```

### 4. Generate Strategy

```python
from skills.psd_parser.level4_strategy import Strategy, CutStrategy

strategy = Strategy()
plan = strategy.generate(components, strategy_type=CutStrategy.SMART_MERGE)
```

### 5. Export Assets

```python
from skills.psd_parser.level5_export import Exporter

exporter = Exporter()
report = exporter.export(components, plan, "output/")
```

---

## Common Commands

### Run Tests

```bash
cd ~/Desktop/agent/projects/psd-smart-cut
python -m pytest skills/psd_parser/level1-parse/test_level1.py -v
python -m pytest skills/psd_parser/level3_recognize/test_level3.py -v
python -m pytest skills/psd_parser/level4_strategy/test_level4.py -v
```

### Parse a PSD

```bash
python examples/basic_parse.py path/to/design.psd
```

### Run Integration Tests

```bash
cd skills/psd_parser
python level9_integration/test_integration.py
```

---

## Configuration

Edit `configs/config.yaml`:

```yaml
ai:
  provider: "minimax"  # minimax / openai / claude
  model: "MiniMax-M2.5-highspeed"
  confidence_threshold: 0.8

export:
  format_priority: ["png", "svg"]
  default_quality: 1.0
  scales: [1, 2, 3]

cutting:
  strategy: "smart_canvas"
  min_component_size: 10
```

---

## Example Conversation

**User:** "Process this PSD file and export all buttons as PNG"

**Assistant:** "Here's how to do that with PSD Smart Cut:

```python
from skills.psd_parser.level1_parse import read_layers, LayerFilter
from skills.psd_parser.level2_classify import LayerClassifier
from skills.psd_parser.level5_export import Exporter

# Read layers
layers = read_layers('design.psd', page_index=0)

# Classify to find buttons
classifier = LayerClassifier()
classified = classifier.classify(layers)
buttons = [l for l in classified if l.sub_category == 'button']

# Export
exporter = Exporter()
report = exporter.export(buttons, plan, 'output/buttons/', formats=['png'])
```

---

## Architecture Notes

- **Level 1**: Pure PSD parsing with psd-tools
- **Level 2**: Rule-based + AI classification
- **Level 3**: Vision AI recognition with mock fallback
- **Level 4**: Strategy planning (FLAT, GROUP_BY_TYPE, SMART_MERGE, etc.)
- **Level 5**: Multi-format export with naming management
- **Level 6**: Text/font/style extraction from layers
- **Level 7**: CSS/Tailwind/iOS/Android code generation
- **Level 8**: Auto-generated documentation
- **Level 9**: Integration tests

All levels support mock mode for testing without PSD files.

---

## Development Workflow

1. **Clone:** `git clone https://github.com/lst016/psd-smart-cut.git`
2. **Install:** `pip install -r requirements.txt`
3. **Test:** `python -m pytest skills/psd_parser/level1-parse/test_level1.py -v`
4. **Develop:** Edit modules in `skills/psd_parser/`
5. **Document:** Update `docs/USER_GUIDE.md` and `docs/CHANGELOG.md`

---

## Key Data Classes

| Class | Module | Description |
|-------|--------|-------------|
| `PSDDocument` | level1_parse | Parsed PSD structure |
| `LayerData` | level1_parse | Individual layer info |
| `ClassifiedLayer` | level2_classify | Classified layer result |
| `Component` | level3_recognize | Recognized component |
| `CutPlan` | level4_strategy | Generated cut plan |
| `ExportReport` | level5_export | Export result report |
| `SpecData` | level7_generate | Generated spec |

---

## Troubleshooting

- **Import errors:** Ensure you're in project root or `sys.path.insert(0, 'path/to/skills')`
- **PSD not loading:** Install `psd-tools`: `pip install psd-tools`
- **AI recognition fails:** Set `use_ai=False` to use rule-based fallback
- **Mock mode tests fail:** Check `skills/psd_parser/level9_integration/` for mock data
