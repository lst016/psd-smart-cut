"""
Level 9 - Integration Tests
端到端集成测试、性能基准测试、边界情况测试

模块：
- test_integration: 端到端集成测试
- performance_test: 性能基准测试
- edge_case_test: 边界情况测试
"""

from .test_integration import (
    create_mock_psd_document,
    create_mock_recognition_results,
)

__version__ = "0.9.0"

__all__ = [
    "create_mock_psd_document",
    "create_mock_recognition_results",
]
