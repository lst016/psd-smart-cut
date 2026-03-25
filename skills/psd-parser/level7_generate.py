"""
Re-export module for level7-generate (underscore alias)
Allows: from skills.psd_parser.level7_generate import ...
Uses __getattr__ for lazy loading to avoid circular import issues.
"""
import importlib

_package = None

def _get_package():
    global _package
    if _package is None:
        _package = importlib.import_module('skills.psd-parser.level7-generate')
    return _package

_SUBMODULES = frozenset([
    'dimension_generator', 'position_generator', 'style_generator',
    'spec_validator', 'schema', 'generator'
])

def __getattr__(name):
    pkg = _get_package()
    if hasattr(pkg, name):
        val = getattr(pkg, name)
        globals()[name] = val
        return val
    if name in _SUBMODULES:
        mod = importlib.import_module(f'skills.psd-parser.level7-generate.{name}')
        globals()[name] = mod
        return mod
    raise AttributeError(f"module 'skills.psd_parser.level7_generate' has no attribute {name!r}")

def __dir__():
    pkg = _get_package()
    return sorted(set(dir(pkg)) | _SUBMODULES)
