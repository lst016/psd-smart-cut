"""
Re-export module for level2-classify (underscore alias)
Allows: from skills.psd_parser.level2_classify import ...
Uses __getattr__ for lazy loading to avoid circular import issues.
"""
import importlib

_package = None

def _get_package():
    global _package
    if _package is None:
        _package = importlib.import_module('skills.psd-parser.level2-classify')
    return _package

# Submodules of this level (not in its __init__.py)
_SUBMODULES = frozenset(['classifier', 'image_classifier', 'text_classifier'])

def __getattr__(name):
    pkg = _get_package()
    
    # First check if it's a package-level export (from __init__.py)
    if hasattr(pkg, name):
        val = getattr(pkg, name)
        globals()[name] = val
        return val
    
    # Then check if it's a submodule
    if name in _SUBMODULES:
        mod = importlib.import_module(f'skills.psd-parser.level2-classify.{name}')
        globals()[name] = mod
        return mod
    
    raise AttributeError(f"module 'skills.psd_parser.level2_classify' has no attribute {name!r}")

def __dir__():
    pkg = _get_package()
    return sorted(set(dir(pkg)) | _SUBMODULES)
