"""
Re-export module for level9-integration (underscore alias)
Allows: from skills.psd_parser.level9_integration import ...
Uses __getattr__ for lazy loading to avoid circular import issues.
"""
import importlib

_package = None

def _get_package():
    global _package
    if _package is None:
        _package = importlib.import_module('skills.psd-parser.level9-integration')
    return _package

_SUBMODULES = frozenset(['pipeline', 'test_integration', 'performance_test', 'edge_case_test'])

def __getattr__(name):
    pkg = _get_package()
    if hasattr(pkg, name):
        val = getattr(pkg, name)
        globals()[name] = val
        return val
    if name in _SUBMODULES:
        mod = importlib.import_module(f'skills.psd-parser.level9-integration.{name}')
        globals()[name] = mod
        return mod
    raise AttributeError(f"module 'skills.psd_parser.level9_integration' has no attribute {name!r}")

def __dir__():
    pkg = _get_package()
    return sorted(set(dir(pkg)) | _SUBMODULES)
