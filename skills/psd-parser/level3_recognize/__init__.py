"""
Level 3 - 识别层 (Recognition Layer)

基于截图和元数据识别 UI 组件类型、边界和功能。

主要模块：
- ScreenshotCapturer: 图层截图捕获器
- RegionDetector: 区域检测器
- ComponentNamer: 组件命名器
- BoundaryAnalyzer: 边界分析器
- FunctionAnalyzer: 功能分析器
- Recognizer: 统一识别器（整合所有模块）
"""

from .screenshot_capturer import ScreenshotCapturer, ScreenshotResult
from .region_detector import (
    RegionDetector,
    RegionResult,
    Rect,
    EdgeType,
    OverlapStrategy,
)
from .component_namer import (
    ComponentNamer,
    NamingResult,
    guess_type_from_name,
    generate_component_name,
)
from .boundary_analyzer import (
    BoundaryAnalyzer,
    BoundaryResult,
    EdgeType as BoundaryEdgeType,
    CutPoint,
)
from .function_analyzer import (
    FunctionAnalyzer,
    FunctionResult,
    StyleAttributes,
    InteractionType,
)
from .recognizer import Recognizer, RecognitionResult

__all__ = [
    # Screenshot
    "ScreenshotCapturer",
    "ScreenshotResult",
    # Region
    "RegionDetector",
    "RegionResult",
    "Rect",
    "EdgeType",
    "OverlapStrategy",
    # Component Namer
    "ComponentNamer",
    "NamingResult",
    "guess_type_from_name",
    "generate_component_name",
    # Boundary
    "BoundaryAnalyzer",
    "BoundaryResult",
    "CutPoint",
    # Function
    "FunctionAnalyzer",
    "FunctionResult",
    "StyleAttributes",
    "InteractionType",
    # Main
    "Recognizer",
    "RecognitionResult",
]

__version__ = "0.3.0"
