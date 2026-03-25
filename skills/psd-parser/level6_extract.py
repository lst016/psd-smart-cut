"""
Re-export module for level6-extract (underscore alias)
Allows: from skills.psd_parser.level6_extract import ...
Uses __getattr__ for lazy loading to avoid circular import issues.
"""
import importlib

_package = None

def _get_package():
    global _package
    if _package is None:
        _package = importlib.import_module('skills.psd-parser.level6-extract')
    return _package

_SUBMODULES = frozenset([
    'text_reader', 'font_analyzer', 'style_extractor',
    'position_reader', 'extractor'
])

def __getattr__(name):
    pkg = _get_package()
    if hasattr(pkg, name):
        val = getattr(pkg, name)
        globals()[name] = val
        return val
    if name in _SUBMODULES:
        mod = importlib.import_module(f'skills.psd-parser.level6-extract.{name}')
        globals()[name] = mod
        return mod
    raise AttributeError(f"module 'skills.psd_parser.level6_extract' has no attribute {name!r}")

def __dir__():
    pkg = _get_package()
    return sorted(set(dir(pkg)) | _SUBMODULES)
