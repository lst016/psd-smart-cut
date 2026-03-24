"""
Level 3 - Screenshot Capturer
图层截图捕获器

从 PSD 导出单个图层的截图，支持指定分辨率。
"""
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

# 引入公共模块
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from skills.common import get_logger, get_config, get_error_handler, ErrorCategory

try:
    from psd_tools import PSDImage
    from PIL import Image
    PSD_TOOLS_AVAILABLE = True
except ImportError:
    PSD_TOOLS_AVAILABLE = False


@dataclass
class ScreenshotResult:
    """截图捕获结果"""
    success: bool
    layer_id: str
    screenshot_path: Optional[str] = None
    width: int = 0
    height: int = 0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ScreenshotCapturer:
    """
    图层截图捕获器

    使用 psd-tools 渲染图层并导出为 PNG 图片。
    支持指定分辨率缩放。
    """

    def __init__(self, output_dir: str = "./output/screenshots"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger("screenshot-capturer")
        self.config = get_config()
        self.error_handler = get_error_handler()

        if not PSD_TOOLS_AVAILABLE:
            self.logger.warning("psd-tools 未安装，将使用 mock 模式")

    def _get_psd_layer(self, psd_file: str, layer_id: str) -> Optional[Any]:
        """
        从 PSD 文件中获取指定图层

        Args:
            psd_file: PSD 文件路径
            layer_id: 图层 ID（支持数字 ID 或图层名称）

        Returns:
            图层对象，失败返回 None
        """
        if not PSD_TOOLS_AVAILABLE:
            return None

        try:
            psd = PSDImage.open(psd_file)
            # 尝试按 ID 查找（psd-tools 的 layer.id 是整数）
            for layer in psd:
                if str(layer.id) == str(layer_id) or layer.name == str(layer_id):
                    return layer
            return None
        except Exception as e:
            self.logger.error(f"读取 PSD 图层失败: {e}")
            return None

    def capture_layer(
        self,
        psd_file: str,
        layer_id: str,
        scale: float = 1.0,
        background_color: Optional[tuple] = None
    ) -> ScreenshotResult:
        """
        捕获单个图层截图

        Args:
            psd_file: PSD 文件路径
            layer_id: 图层 ID 或名称
            scale: 缩放比例，1.0 表示原尺寸
            background_color: 背景色 RGBA 元组，默认透明

        Returns:
            ScreenshotResult 对象
        """
        self.logger.info(f"捕获图层截图: layer_id={layer_id}, scale={scale}")

        if not PSD_TOOLS_AVAILABLE:
            return self._mock_capture(layer_id, scale)

        try:
            layer = self._get_psd_layer(psd_file, layer_id)
            if layer is None:
                return ScreenshotResult(
                    success=False,
                    layer_id=layer_id,
                    error=f"图层未找到: {layer_id}"
                )

            # 使用 psd-tools 渲染图层
            # topil() 会将图层渲染为 PIL Image
            image = layer.topil()

            if image is None:
                return ScreenshotResult(
                    success=False,
                    layer_id=layer_id,
                    error="图层渲染失败"
                )

            # 应用缩放
            if scale != 1.0:
                new_width = int(image.width * scale)
                new_height = int(image.height * scale)
                image = image.resize((new_width, new_height), Image.LANCZOS)
                self.logger.debug(f"缩放后尺寸: {new_width}x{new_height}")

            # 保存文件
            output_path = self.output_dir / f"layer_{layer_id}.png"
            image.save(str(output_path), "PNG")

            result = ScreenshotResult(
                success=True,
                layer_id=layer_id,
                screenshot_path=str(output_path),
                width=image.width,
                height=image.height,
                metadata={
                    "original_width": layer.size[0],
                    "original_height": layer.size[1],
                    "scale": scale,
                    "layer_name": layer.name,
                }
            )

            self.logger.info(f"截图保存成功: {output_path}")
            return result

        except Exception as e:
            error_result = ScreenshotResult(
                success=False,
                layer_id=layer_id,
                error=str(e)
            )
            self.error_handler.record(
                task="capture_layer",
                error=e,
                category=ErrorCategory.EXPORT_ERROR,
                context={"psd_file": psd_file, "layer_id": layer_id}
            )
            self.logger.error(f"截图捕获失败: {e}")
            return error_result

    def _mock_capture(self, layer_id: str, scale: float) -> ScreenshotResult:
        """
        Mock 模式：在 psd-tools 不可用时生成占位图
        用于测试和开发环境。
        """
        self.logger.warning(f"使用 mock 模式生成占位截图: layer_id={layer_id}")

        # 生成一个随机颜色的占位图（用于开发测试）
        try:
            from PIL import Image
            import random

            width = int(100 * scale)
            height = int(80 * scale)
            color = (
                random.randint(200, 255),
                random.randint(200, 255),
                random.randint(200, 255),
                255
            )
            image = Image.new("RGBA", (width, height), color)

            output_path = self.output_dir / f"layer_{layer_id}_mock.png"
            image.save(str(output_path), "PNG")

            return ScreenshotResult(
                success=True,
                layer_id=layer_id,
                screenshot_path=str(output_path),
                width=width,
                height=height,
                metadata={"mock": True, "scale": scale}
            )
        except Exception as e:
            return ScreenshotResult(
                success=False,
                layer_id=layer_id,
                error=f"Mock 模式失败: {e}"
            )

    def capture_layers(
        self,
        psd_file: str,
        layer_ids: List[str],
        scale: float = 1.0
    ) -> List[ScreenshotResult]:
        """
        批量捕获图层截图

        Args:
            psd_file: PSD 文件路径
            layer_ids: 图层 ID 列表
            scale: 缩放比例

        Returns:
            ScreenshotResult 列表
        """
        self.logger.info(f"批量捕获 {len(layer_ids)} 个图层")
        results = []

        for layer_id in layer_ids:
            result = self.capture_layer(psd_file, layer_id, scale)
            results.append(result)

        success_count = sum(1 for r in results if r.success)
        self.logger.info(f"批量捕获完成: {success_count}/{len(layer_ids)} 成功")

        return results

    def cleanup(self, screenshot_path: str) -> bool:
        """
        清理临时截图文件

        Args:
            screenshot_path: 截图文件路径

        Returns:
            是否清理成功
        """
        try:
            path = Path(screenshot_path)
            if path.exists():
                path.unlink()
                self.logger.debug(f"已清理截图: {screenshot_path}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"清理截图失败: {e}")
            return False
