# Release Notes - v1.0.0

**Version:** 1.0.0  
**Release Date:** 2026-03-25  
**Status:** Initial Release

---

## 📦 Downloads

- **Source Code:** [psd-smart-cut-v1.0.0.tar.gz](https://github.com/lst016/psd-smart-cut/archive/refs/tags/v1.0.0.tar.gz)
- **Zip Archive:** [psd-smart-cut-v1.0.0.zip](https://github.com/lst016/psd-smart-cut/archive/refs/tags/v1.0.0.zip)

---

## 🎉 What's New

### Complete 8-Layer Architecture

PSD Smart Cut v1.0.0 is the first stable release featuring a complete 8-layer agent pipeline:

| Layer | Module | Status |
|-------|--------|--------|
| Level 1 | PSD Parsing | ✅ Complete |
| Level 2 | Layer Classification | ✅ Complete |
| Level 3 | Component Recognition | ✅ Complete |
| Level 4 | Cut Strategy | ✅ Complete |
| Level 5 | Asset Export | ✅ Complete |
| Level 6 | Text/Style Extraction | ✅ Complete |
| Level 7 | Spec Generation | ✅ Complete |
| Level 8 | Documentation | ✅ Complete |

### Key Features

- **Multi-page PSD Support** - Parse PSD files with multiple pages/artboards
- **Nested Layer Parsing** - Handle complex nested layer hierarchies
- **AI Vision Recognition** - Optional AI-powered component recognition (MiniMax/OpenAI)
- **Smart Cut Strategies** - 5 strategies: FLAT, GROUP_BY_TYPE, GROUP_BY_PAGE, PRESERVE_HIERARCHY, SMART_MERGE
- **Multi-format Export** - PNG, JPG, WebP, SVG with 1x/2x/3x scale support
- **Spec Generation** - CSS, Tailwind, iOS, Android code generation
- **Mock Mode Testing** - Full test coverage without requiring PSD files

---

## 📋 Full Changelog

### Features

- **Level 1 - PSD Parsing**
  - `parse_psd()` - Core PSD document parser
  - `extract_pages()` - Multi-page extraction
  - `read_layers()` - Layer reading with filters (ALL/VISIBLE/HIDDEN/LOCKED)
  - Hierarchy tree builder
  - Hidden layer marker
  - Locked layer detector

- **Level 2 - Layer Classification**
  - Image classifier (button/icon/background/photo/illustration)
  - Text classifier (heading/body/label)
  - Vector classifier
  - Group classifier
  - Decorator classifier
  - Language detection (zh/en/mixed)

- **Level 3 - Component Recognition**
  - Screenshot capturer with psd-tools + mock fallback
  - Region detector (boundary, overlap, valid area)
  - Component namer (AI/rule-based)
  - Boundary analyzer (edge type, quality score, cut points)
  - Function analyzer (interaction type, style attributes)

- **Level 4 - Cut Strategy**
  - Canvas analyzer (density heatmap, cut line detection)
  - Strategy selector (5 strategy types)
  - Overlap detector (occlusion relationship, priority)
  - Quality evaluator (cut precision, edge quality)
  - Plan optimizer

- **Level 5 - Asset Export**
  - PNG/JPG/WebP/SVG export
  - Format converter with compression
  - Naming manager (template, conflict detection)
  - Metadata attacher (EXIF, manifest.json)
  - Batch processing

- **Level 6 - Text/Style Extraction**
  - Text reader (content, encoding, RTL, paragraphs, alignment)
  - Font analyzer (family, size, weight, color, line height)
  - Style extractor (opacity, blend mode, shadow, stroke, gradient)
  - Position reader (coordinates, rotation, anchor, responsive breakpoints)

- **Level 7 - Spec Generation**
  - Dimension generator (px/rem/dp/pt/em/vh/vw/%)
  - Position generator (CSS position, Flex/Grid)
  - Style generator (CSS, Tailwind, iOS, Android)
  - Spec validator (completeness, conflict, syntax)
  - JSON Schema definition

- **Level 8 - Documentation**
  - README generator (badges, feature list)
  - CHANGELOG generator (git log parsing)
  - Manifest generator (JSON/YAML)
  - HTML preview generator (component cards, relation graph)
  - Doc aggregator (validation, index)

---

## 🧪 Testing

### Test Coverage

| Level | Test File | Test Cases |
|-------|-----------|------------|
| Level 1 | test_level1.py | Core functionality |
| Level 2 | test_level2.py | 26 test cases |
| Level 3 | test_level3.py | 28 test cases |
| Level 4 | test_level4.py | 29 test cases |
| Level 5 | test_level5.py | 40 test cases |
| Level 6 | test_level6.py | 38 test cases |
| Level 7 | test_level7.py | 50 test cases |
| Level 8 | test_level8.py | Integration tests |
| Level 9 | test_integration.py | 40+ test cases |

**Total: 250+ test cases**

### Running Tests

```bash
# All tests
python -m pytest skills/psd_parser/ -v

# Mock mode (no PSD file needed)
python -m pytest skills/psd_parser/level9_integration/ -v
```

---

## 🛠️ Installation

```bash
git clone https://github.com/lst016/psd-smart-cut.git
cd psd-smart-cut
pip install -r requirements.txt

# Optional: AI features
pip install minimax-api  # MiniMax VLM
pip install openai        # OpenAI vision
```

---

## 📖 Documentation

- [User Guide](./USER_GUIDE.md) - Complete usage documentation
- [CLAUDE.md](./CLAUDE.md) - Claude AI integration guide
- [CURSOR.md](./CURSOR.md) - Cursor IDE integration guide
- [CHANGELOG.md](./CHANGELOG.md) - Detailed change history
- [VERSION-PLAN.md](./VERSION-PLAN.md) - Development roadmap

---

## 🔮 Roadmap

### v1.1 (Planned)

- [ ] CLI tool with full workflow
- [ ] Web UI dashboard
- [ ] Real PSD file integration tests
- [ ] Additional AI providers (Claude, Gemini)
- [ ] Batch processing support

### v1.2 (Planned)

- [ ] Figma plugin integration
- [ ] Cloud deployment support
- [ ] Team collaboration features
- [ ] Advanced conflict detection
- [ ] Custom export templates

---

## 🙏 Credits

**Lead Developer:** 牛牛 (AI Assistant)  
**Project:** psd-smart-cut  
**License:** MIT

---

## 📝 License

MIT License - see [LICENSE](../LICENSE) file.
