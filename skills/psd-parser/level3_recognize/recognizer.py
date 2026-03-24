"""
Level 3 - 统一识别器 (Recognizer)
协调所有识别器，提供统一接口

集成：
- ScreenshotCapturer: 图层截图捕获
- RegionDetector: 区域检测
- ComponentNamer: 组件命名
- BoundaryAnalyzer: 边界分析
- FunctionAnalyzer: 功能分析
"""
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from skills.common import get_logger, get_config, get_error_handler, ErrorCategory

from .screenshot_capturer import ScreenshotCapturer, ScreenshotResult
from .region_detector import RegionDetector, RegionResult
from .component_namer import ComponentNamer, NamingResult
from .boundary_analyzer import BoundaryAnalyzer, BoundaryResult
from .function_analyzer import FunctionAnalyzer, FunctionResult


@dataclass
class RecognitionResult:
    """
    统一识别结果

    综合所有识别器的输出。
    """
    layer_id: str
    component_name: str = ""
    component_type: str = "unknown"
    boundary: Dict[str, Any] = field(default_factory=dict)
    functions: List[str] = field(default_factory=list)
    interaction_types: List[str] = field(default_factory=list)
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 子识别器结果（原始数据）
    screenshot_result: Optional[ScreenshotResult] = None
    region_result: Optional[RegionResult] = None
    naming_result: Optional[NamingResult] = None
    boundary_result: Optional[BoundaryResult] = None
    function_result: Optional[FunctionResult] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "layer_id": self.layer_id,
            "component_name": self.component_name,
            "component_type": self.component_type,
            "boundary": self.boundary,
            "functions": self.functions,
            "interaction_types": self.interaction_types,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }

    @property
    def success(self) -> bool:
        """是否识别成功"""
        return bool(self.layer_id) and self.component_type != "unknown"


class Recognizer:
    """
    统一识别器

    协调所有识别器，提供从 PSD 图层到完整识别结果的一站式服务。
    支持批量处理和结果缓存。
    """

    def __init__(
        self,
        output_dir: str = "./output",
        use_screenshot: bool = True,
        use_ai_naming: bool = False,
        cache_dir: str = "./output/.cache"
    ):
        """
        Args:
            output_dir: 输出目录
            use_screenshot: 是否捕获图层截图
            use_ai_naming: 是否使用 AI 命名（需要 MiniMax API）
            cache_dir: 缓存目录
        """
        self.output_dir = Path(output_dir)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.use_screenshot = use_screenshot
        self.use_ai_naming = use_ai_naming

        self.logger = get_logger("recognizer")
        self.config = get_config()
        self.error_handler = get_error_handler()

        # 初始化子识别器
        screenshot_dir = self.output_dir / "screenshots"
        self.screenshot_capturer = ScreenshotCapturer(str(screenshot_dir))
        self.region_detector = RegionDetector()
        self.component_namer = ComponentNamer(use_ai=use_ai_naming)
        self.boundary_analyzer = BoundaryAnalyzer()
        self.function_analyzer = FunctionAnalyzer()

        # 结果缓存
        self._result_cache: Dict[str, RecognitionResult] = {}
        self._cache_enabled = True

    def _get_cache_key(self, layer_id: str, psd_file: str) -> str:
        """生成缓存键"""
        return f"{Path(psd_file).stem}:{layer_id}"

    def recognize(
        self,
        psd_file: str,
        layer_metadata: Dict[str, Any],
        capture_screenshot: bool = True
    ) -> RecognitionResult:
        """
        识别单个图层

        Args:
            psd_file: PSD 文件路径
            layer_metadata: 图层元数据（应包含 layer_id, name, type, position, dimensions）
            capture_screenshot: 是否捕获截图

        Returns:
            RecognitionResult
        """
        layer_id = layer_metadata.get("layer_id", "unknown")

        # 检查缓存
        cache_key = self._get_cache_key(layer_id, psd_file)
        if self._cache_enabled and cache_key in self._result_cache:
            self.logger.debug(f"从缓存返回: {cache_key}")
            return self._result_cache[cache_key]

        self.logger.info(f"开始识别图层: layer_id={layer_id}")

        result = RecognitionResult(layer_id=layer_id)

        try:
            # 1. 截图捕获（可选）
            if capture_screenshot and self.use_screenshot:
                screenshot_result = self.screenshot_capturer.capture_layer(
                    psd_file=psd_file,
                    layer_id=layer_id,
                    scale=1.0
                )
                result.screenshot_result = screenshot_result
                if screenshot_result.success:
                    result.metadata["screenshot_path"] = screenshot_result.screenshot_path
                    result.metadata["screenshot_width"] = screenshot_result.width
                    result.metadata["screenshot_height"] = screenshot_result.height

            # 2. 区域检测
            region_result = self.region_detector.analyze(layer_metadata)
            result.region_result = region_result
            if region_result.success:
                result.boundary = region_result.effective_boundary or region_result.raw_boundary or {}

            # 3. 组件命名
            naming_result = self.component_namer.name_from_metadata(
                layer_metadata=layer_metadata,
                screenshot_path=result.metadata.get("screenshot_path")
            )
            result.naming_result = naming_result
            if naming_result.success:
                result.component_name = naming_result.component_name
                result.component_type = naming_result.component_type
                result.confidence = naming_result.confidence
                result.metadata["naming_source"] = naming_result.metadata.get("source")

            # 4. 边界分析
            boundary_result = self.boundary_analyzer.analyze(
                boundary=result.boundary or layer_metadata,
                layer_metadata=layer_metadata
            )
            result.boundary_result = boundary_result
            if boundary_result.success:
                if not result.boundary:
                    result.boundary = boundary_result.edge_details.get("boundary", {})
                result.metadata["edge_type"] = boundary_result.edge_type
                result.metadata["quality_score"] = boundary_result.quality_score
                result.metadata["cut_points"] = boundary_result.cut_points

            # 5. 功能分析
            function_result = self.function_analyzer.analyze(
                layer_metadata=layer_metadata,
                component_type=result.component_type,
                component_name=result.component_name
            )
            result.function_result = function_result
            if function_result.success:
                result.functions = function_result.functions
                result.interaction_types = function_result.interaction_types
                result.metadata["style_attributes"] = function_result.style_attributes
                result.metadata["description"] = function_result.description
                result.metadata["accessibility_hints"] = function_result.accessibility_hints

            # 6. 综合置信度
            confidences = [
                c for c in [
                    result.confidence,
                    boundary_result.quality_score if boundary_result.success else 0,
                    0.8 if function_result.success else 0,
                ] if c > 0
            ]
            if confidences:
                result.confidence = round(sum(confidences) / len(confidences), 3)

            # 写入缓存
            self._result_cache[cache_key] = result

            self.logger.info(
                f"识别完成: layer_id={layer_id}, "
                f"type={result.component_type}, "
                f"name={result.component_name}, "
                f"confidence={result.confidence}"
            )

            return result

        except Exception as e:
            self.logger.error(f"识别失败: {e}")
            self.error_handler.record(
                task="recognize",
                error=e,
                category=ErrorCategory.PARSE_ERROR,
                context={"psd_file": psd_file, "layer_id": layer_id}
            )
            error_result = RecognitionResult(layer_id=layer_id)
            error_result.metadata["error"] = str(e)
            return error_result

    def batch_recognize(
        self,
        psd_file: str,
        layers_metadata: List[Dict[str, Any]],
        capture_screenshots: bool = True,
        parallel: bool = False
    ) -> List[RecognitionResult]:
        """
        批量识别图层

        Args:
            psd_file: PSD 文件路径
            layers_metadata: 图层元数据列表
            capture_screenshots: 是否捕获截图
            parallel: 是否并行处理（当前仅支持串行）

        Returns:
            RecognitionResult 列表
        """
        self.logger.info(f"批量识别 {len(layers_metadata)} 个图层")

        results = []
        for i, layer_metadata in enumerate(layers_metadata):
            self.logger.debug(f"进度: {i + 1}/{len(layers_metadata)}")

            result = self.recognize(
                psd_file=psd_file,
                layer_metadata=layer_metadata,
                capture_screenshot=capture_screenshots
            )
            results.append(result)

        success_count = sum(1 for r in results if r.success)
        avg_confidence = sum(r.confidence for r in results if r.success) / max(1, success_count)

        self.logger.info(
            f"批量识别完成: {success_count}/{len(layers_metadata)} 成功, "
            f"平均置信度={avg_confidence:.2f}"
        )

        return results

    def recognize_and_save(
        self,
        psd_file: str,
        layers_metadata: List[Dict[str, Any]],
        output_file: Optional[str] = None
    ) -> Tuple[List[RecognitionResult], str]:
        """
        识别并保存结果

        Args:
            psd_file: PSD 文件路径
            layers_metadata: 图层元数据列表
            output_file: 输出文件路径（JSON）

        Returns:
            (RecognitionResult 列表, 输出文件路径)
        """
        results = self.batch_recognize(psd_file, layers_metadata)

        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = str(self.output_dir / f"recognition_results_{timestamp}.json")

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        import json
        output_data = {
            "psd_file": psd_file,
            "timestamp": datetime.now().isoformat(),
            "total_layers": len(results),
            "success_count": sum(1 for r in results if r.success),
            "results": [r.to_dict() for r in results]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        self.logger.info(f"结果已保存: {output_path}")

        return results, str(output_path)

    def clear_cache(self):
        """清空缓存"""
        self._result_cache.clear()
        self.logger.info("缓存已清空")

    def get_summary(self, results: List[RecognitionResult]) -> Dict[str, Any]:
        """
        生成识别结果摘要

        Args:
            results: RecognitionResult 列表

        Returns:
            摘要字典
        """
        success_results = [r for r in results if r.success]

        # 按组件类型统计
        type_counts: Dict[str, int] = {}
        for r in success_results:
            type_counts[r.component_type] = type_counts.get(r.component_type, 0) + 1

        # 按交互类型统计
        interaction_counts: Dict[str, int] = {}
        for r in success_results:
            for it in r.interaction_types:
                interaction_counts[it] = interaction_counts.get(it, 0) + 1

        return {
            "total": len(results),
            "success": len(success_results),
            "failed": len(results) - len(success_results),
            "avg_confidence": round(
                sum(r.confidence for r in success_results) / max(1, len(success_results)),
                3
            ),
            "component_types": dict(sorted(type_counts.items(), key=lambda x: x[1], reverse=True)),
            "interaction_types": dict(sorted(interaction_counts.items(), key=lambda x: x[1], reverse=True)),
            "total_functions": len(set(f for r in success_results for f in r.functions)),
        }
