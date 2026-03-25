"""
Re-export module for level1-parse (underscore alias)

Allows: from skills.psd_parser.level1_parse import PSDParser, PSDDocument, PageInfo, LayerInfo, PageExtractor, HierarchyBuilder, ...
       and: from skills.psd_parser.level1_parse.psd_parser import PSDParser
       and: from skills.psd_parser.level1_parse.page_extractor import PageExtractor
"""
import importlib
import sys
from pathlib import Path

_this_dir = Path(__file__).parent
_level1_parse_dir = _this_dir / "level1-parse"

# Add level1-parse to sys.path FIRST
if str(_level1_parse_dir) not in sys.path:
    sys.path.insert(0, str(_level1_parse_dir))

# Submodule cache
_submodule_cache = {}

# Module names to load (base name of module files in level1-parse/)
_SUBMODULES = ['psd_parser', 'page_extractor', 'layer_reader', 
               'hierarchy_builder', 'hidden_marker', 'locked_detector']

def _load_submodule(name):
    """Lazily load a submodule from level1-parse directory"""
    if name not in _submodule_cache:
        mod = importlib.import_module(name)
        _submodule_cache[name] = mod
        # Also register in sys.modules under the skills.psd_parser.level1_parse.NAME path
        sys.modules[f'skills.psd_parser.level1_parse.{name}'] = mod
    return _submodule_cache[name]

def __getattr__(name):
    # Handle submodule access: level1_parse.psd_parser -> submodule
    if name in _SUBMODULES:
        return _load_submodule(name)
    
    # Handle re-exported names from all submodules
    for submod_name in _SUBMODULES:
        try:
            mod = _load_submodule(submod_name)
            if hasattr(mod, name):
                val = getattr(mod, name)
                # Cache it in globals too
                globals()[name] = val
                return val
        except Exception:
            pass
    
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# PRE-LOAD ALL submodules
# Order matters: psd_parser first (no internal deps), then others
for _submod_name in _SUBMODULES:
    _load_submodule(_submod_name)

# Pre-register psd_parser in sys.modules under all possible names
_psd = _submodule_cache['psd_parser']
sys.modules['skills.psd_parser.level1_parse.psd_parser'] = _psd

# Re-export ALL public names (not just __all__) from ALL submodules into globals
for _submod_name in _SUBMODULES:
    _mod = _submodule_cache.get(_submod_name)
    if _mod:
        for _name in dir(_mod):
            if not _name.startswith('_'):
                try:
                    val = getattr(_mod, _name)
                    if _name not in globals():
                        globals()[_name] = val
                except Exception:
                    pass

__all__ = [k for k in globals().keys() if not k.startswith('_')]
