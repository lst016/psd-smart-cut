"""PSD Smart Cut - PSD Parser Module

Uses __getattr__ for lazy loading of each level to avoid circular
import issues (since source files inside level dirs import via
underscore paths like skills.psd_parser.level1_parse.*).
"""
import importlib

_LEVELS = [
    'level1-parse', 'level2-classify', 'level3_recognize',
    'level4-strategy', 'level5-export', 'level6-extract',
    'level7-generate', 'level8-document', 'level9-integration',
]

_loaded_levels = {}

def __getattr__(name):
    # name is like 'level1_parse' (underscore version of 'level1-parse')
    for _level in _LEVELS:
        _underscore_name = _level.replace('-', '_')
        if _underscore_name == name:
            if _level not in _loaded_levels:
                _loaded_levels[_level] = importlib.import_module(
                    f'skills.psd-parser.{_level}'
                )
            return _loaded_levels[_level]
    raise AttributeError(f"module 'skills.psd_parser' has no attribute {name!r}")

def __dir__():
    return [_l.replace('-', '_') for _l in _LEVELS]
