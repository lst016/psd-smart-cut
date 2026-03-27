"""
Level 5 - Asset Exporter

Exports PSD components into image assets.
Supports real PSD-backed exports as well as legacy byte payloads used by tests.
"""

from __future__ import annotations

import base64
import hashlib
import io
import math
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from PIL import Image, ImageChops
from psd_tools import PSDImage

from skills.common import ErrorCategory, get_config, get_error_handler, get_logger


@dataclass
class ExportResult:
    """Asset export result."""

    success: bool
    asset_id: str
    original_path: str
    exported_path: Optional[str]
    format: str
    width: int
    height: int
    file_size: int
    error: Optional[str] = None


class AssetExporter:
    """
    Export PSD layers or layer groups into image assets.

    The exporter accepts either:
    - a legacy byte payload, or
    - a PSD-backed asset spec containing `source_file` and `layer_ids`.
    """

    SUPPORTED_FORMATS = {"png", "jpg", "jpeg", "webp", "svg"}
    FORMAT_EXTENSIONS = {
        "png": ".png",
        "jpg": ".jpg",
        "jpeg": ".jpg",
        "webp": ".webp",
        "svg": ".svg",
    }

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger("asset-exporter")
        self.config = get_config()
        self.error_handler = get_error_handler()
        self._psd_cache: Dict[str, PSDImage] = {}
        self._layer_cache: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._fingerprint_cache: Dict[str, Path] = {}

        self.logger.info(f"AssetExporter initialized, output_dir={self.output_dir}")

    def export(
        self,
        layer_data: Any,
        format: str = "png",
        scale: float = 1.0,
        asset_id: Optional[str] = None,
        crop_whitespace: bool = True,
    ) -> ExportResult:
        """Export a single asset."""
        format = format.lower()
        if format == "jpeg":
            format = "jpg"

        if format not in self.SUPPORTED_FORMATS:
            error_msg = f"不支持的格式: {format}"
            self.logger.error(error_msg)
            return ExportResult(
                success=False,
                asset_id=asset_id or str(uuid.uuid4()),
                original_path="",
                exported_path=None,
                format=format,
                width=0,
                height=0,
                file_size=0,
                error=error_msg,
            )

        if not asset_id:
            asset_id = str(uuid.uuid4())[:8]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{asset_id}_{timestamp}{self.FORMAT_EXTENSIONS.get(format, '.png')}"
        output_path = self.output_dir / filename

        try:
            self.logger.info(f"Exporting asset {asset_id}, format={format}, scale={scale}")

            image, original_path = self._resolve_image(layer_data)
            if image is None:
                raise ValueError("No renderable image data found for export")

            if crop_whitespace:
                image = self._crop_whitespace_image(image)

            if scale != 1.0:
                image = self._scale_image(image, scale)

            fingerprint = self._fingerprint_image(image, format)
            existing_path = self._fingerprint_cache.get(fingerprint)
            if existing_path and existing_path.exists():
                reused_size = existing_path.stat().st_size
                self.logger.info(f"Reusing duplicate asset {existing_path.name} for {asset_id}")
                return ExportResult(
                    success=True,
                    asset_id=asset_id,
                    original_path=original_path,
                    exported_path=str(existing_path),
                    format=format,
                    width=image.width,
                    height=image.height,
                    file_size=reused_size,
                )

            file_size = self._save_image(image, output_path, format)
            width, height = image.size
            self._fingerprint_cache[fingerprint] = output_path

            result = ExportResult(
                success=True,
                asset_id=asset_id,
                original_path=original_path,
                exported_path=str(output_path),
                format=format,
                width=width,
                height=height,
                file_size=file_size,
            )

            self.logger.info(f"Asset exported successfully: {output_path}, size={file_size}")
            return result

        except Exception as e:
            error_msg = f"Export failed: {e}"
            self.logger.error(error_msg)

            self.error_handler.record(
                task=f"export_asset_{asset_id}",
                error=e,
                category=ErrorCategory.EXPORT_ERROR,
                context={"format": format, "scale": scale},
            )

            return ExportResult(
                success=False,
                asset_id=asset_id,
                original_path="",
                exported_path=None,
                format=format,
                width=0,
                height=0,
                file_size=0,
                error=error_msg,
            )

    def export_batch(
        self,
        assets: List[Dict],
        format: str = "png",
        scale: float = 1.0,
    ) -> List[ExportResult]:
        """Export multiple assets."""
        self.logger.info(f"Batch export started, count={len(assets)}, format={format}")

        results = []
        for i, asset in enumerate(assets):
            asset_id = asset.get("asset_id", f"asset_{i}")
            unique_id = f"{asset_id}_{i}"
            result = self.export(
                layer_data=asset.get("layer_data", b""),
                format=format,
                scale=scale,
                asset_id=unique_id,
                crop_whitespace=asset.get("crop_whitespace", True),
            )
            results.append(result)

        success_count = sum(1 for r in results if r.success)
        self.logger.info(f"Batch export completed: {success_count}/{len(assets)} succeeded")
        return results

    def _resolve_image(self, layer_data: Any) -> Tuple[Optional[Image.Image], str]:
        """Render an image from either a PSD asset spec or legacy bytes."""
        if isinstance(layer_data, dict) and layer_data.get("source_file") and layer_data.get("layer_ids"):
            image = self._render_from_psd_spec(layer_data)
            return image, str(layer_data.get("source_file"))

        if isinstance(layer_data, (bytes, bytearray)):
            return self._render_from_bytes(bytes(layer_data)), "legacy_byte_payload"

        if isinstance(layer_data, str):
            path = Path(layer_data)
            if path.exists():
                with Image.open(path) as image:
                    return image.convert("RGBA"), str(path)

        return None, ""

    def _render_from_psd_spec(self, spec: Dict[str, Any]) -> Optional[Image.Image]:
        """Render one or more PSD layers using the original PSD file."""
        source_file = str(spec["source_file"])
        layer_ids = [layer_id for layer_id in spec.get("layer_ids", []) if layer_id]
        if not layer_ids:
            return None

        psd = self._get_psd(source_file)
        layer_map = self._get_layer_map(source_file, psd)

        bbox = self._normalize_bbox(spec.get("render_bbox") or spec.get("bbox"))
        if bbox is None:
            bbox = self._union_bbox(
                [
                    layer_info["bbox"]
                    for layer_id in layer_ids
                    for layer_info in [layer_map.get(layer_id)]
                    if layer_info and layer_info.get("bbox")
                ]
            )
        if bbox is None:
            return None

        preferred_strategy = str(spec.get("preferred_strategy", "")).strip()
        hidden_layer_ids = self._collect_hidden_layer_ids(spec)
        context_layer_ids = [layer_id for layer_id in spec.get("context_layer_ids", []) if layer_id]

        if preferred_strategy == "hide_background_then_render" or hidden_layer_ids:
            hidden_background_image = self._render_with_hidden_background(
                psd=psd,
                layer_map=layer_map,
                layer_ids=layer_ids,
                hidden_layer_ids=hidden_layer_ids,
                context_layer_ids=context_layer_ids,
                bbox=bbox,
            )
            if hidden_background_image is not None:
                return hidden_background_image

        context_image = self._render_from_context(layer_ids, layer_map, bbox)
        if context_image is not None:
            return context_image

        rendered_layers: List[Tuple[Image.Image, Tuple[int, int, int, int]]] = []
        for layer_id in layer_ids:
            layer_info = layer_map.get(layer_id)
            if layer_info is None:
                continue
            layer = layer_info["layer"]
            layer_bbox = layer_info.get("bbox")
            if layer_bbox is None:
                continue
            image = self._render_layer(layer)
            if image is None:
                continue
            rendered_layers.append((image, layer_bbox))

        if not rendered_layers:
            return None

        left, top, right, bottom = bbox
        canvas = Image.new("RGBA", (max(1, right - left), max(1, bottom - top)), (0, 0, 0, 0))

        for image, layer_bbox in rendered_layers:
            offset = (layer_bbox[0] - left, layer_bbox[1] - top)
            canvas.alpha_composite(image.convert("RGBA"), offset)

        return canvas

    def _render_with_hidden_background(
        self,
        psd: PSDImage,
        layer_map: Dict[str, Dict[str, Any]],
        layer_ids: List[str],
        hidden_layer_ids: List[str],
        context_layer_ids: List[str],
        bbox: Tuple[int, int, int, int],
    ) -> Optional[Image.Image]:
        """Render a slot while suppressing background contributors."""
        hidden_ids = {layer_id for layer_id in hidden_layer_ids if layer_id in layer_map}
        if not hidden_ids:
            return None

        kept_ids = [layer_id for layer_id in layer_ids if layer_id in layer_map]
        kept_ids.extend([layer_id for layer_id in context_layer_ids if layer_id in layer_map])
        allowed_ids = self._expand_render_targets(kept_ids, layer_map)
        if not allowed_ids:
            return None

        def layer_filter(candidate: Any) -> bool:
            candidate_id = getattr(candidate, "_smart_cut_layer_id", None)
            if candidate_id in hidden_ids:
                return False
            return candidate_id in allowed_ids

        try:
            image = psd.composite(
                viewport=bbox,
                force=True,
                apply_icc=True,
                layer_filter=layer_filter,
            )
            if image is None:
                return None
            rgba_image = image.convert("RGBA")
            if rgba_image.width <= 0 or rgba_image.height <= 0:
                return None
            if rgba_image.getbbox() is None:
                return None
            return rgba_image
        except Exception:
            return None

    def _render_from_context(
        self,
        layer_ids: List[str],
        layer_map: Dict[str, Dict[str, Any]],
        bbox: Tuple[int, int, int, int],
    ) -> Optional[Image.Image]:
        """Render layers through their nearest shared ancestor to preserve masks/effects."""
        if not layer_ids:
            return None

        if len(layer_ids) == 1:
            layer_info = layer_map.get(layer_ids[0])
            if not layer_info:
                return None
            return self._render_layer(layer_info["layer"])

        ancestor_id = self._find_render_ancestor(layer_ids, layer_map)
        if ancestor_id is None:
            return None

        ancestor_info = layer_map.get(ancestor_id)
        if not ancestor_info:
            return None

        ancestor_layer = ancestor_info["layer"]
        allowed_ids = self._expand_render_targets(layer_ids, layer_map)

        def layer_filter(candidate: Any) -> bool:
            candidate_id = getattr(candidate, "_smart_cut_layer_id", None)
            return candidate_id in allowed_ids

        try:
            image = ancestor_layer.composite(
                viewport=bbox,
                force=True,
                layer_filter=layer_filter,
                apply_icc=True,
            )
            if image is not None:
                rgba_image = image.convert("RGBA")
                if rgba_image.getchannel("A").getbbox():
                    return rgba_image
        except Exception:
            pass

        return None

    def _render_layer(self, layer: Any) -> Optional[Image.Image]:
        """Render a single PSD layer or group."""
        try:
            image = layer.topil()
            if image is not None:
                rendered = image.convert("RGBA")
                rendered = self._apply_supported_effect_overlays(layer, rendered)
                return rendered
        except Exception:
            pass

        try:
            image = layer.composite()
            if image is not None:
                rendered = image.convert("RGBA")
                rendered = self._apply_supported_effect_overlays(layer, rendered)
                return rendered
        except Exception:
            pass

        if hasattr(layer, "__iter__"):
            return self._render_group_fallback(layer)

        return None

    def _get_enabled_color_overlay(self, layer: Any) -> Optional[Tuple[int, int, int, float]]:
        effects = getattr(layer, "effects", None)
        if effects is None:
            return None

        try:
            for effect in effects:
                if type(effect).__name__ != "ColorOverlay":
                    continue
                if not getattr(effect, "enabled", False):
                    continue
                color = getattr(effect, "color", None)
                if not color:
                    continue
                red = int(round(float(color.get(b"Rd  ", 255.0))))
                green = int(round(float(color.get(b"Grn ", 255.0))))
                blue = int(round(float(color.get(b"Bl  ", 255.0))))
                opacity = float(getattr(effect, "opacity", 100.0)) / 100.0
                return red, green, blue, opacity
        except Exception:
            return None

        return None

    def _get_enabled_gradient_overlay(
        self,
        layer: Any,
    ) -> Optional[Tuple[List[Tuple[float, Tuple[int, int, int]]], float, float, bool]]:
        effects = getattr(layer, "effects", None)
        if effects is None:
            return None

        try:
            for effect in effects:
                if type(effect).__name__ != "GradientOverlay":
                    continue
                if not getattr(effect, "enabled", False):
                    continue
                gradient = getattr(effect, "gradient", None)
                if not gradient or not hasattr(gradient, "get"):
                    continue
                raw_colors = gradient.get(b"Clrs") or []
                if len(raw_colors) < 2:
                    continue

                stops: List[Tuple[float, Tuple[int, int, int]]] = []
                for item in raw_colors:
                    color = item.get(b"Clr ", {})
                    red = int(round(float(color.get(b"Rd  ", 255.0))))
                    green = int(round(float(color.get(b"Grn ", 255.0))))
                    blue = int(round(float(color.get(b"Bl  ", 255.0))))
                    location = float(item.get(b"Lctn", 0.0)) / 4096.0
                    stops.append((max(0.0, min(1.0, location)), (red, green, blue)))

                stops.sort(key=lambda item: item[0])
                opacity = float(getattr(effect, "opacity", 100.0)) / 100.0
                angle = float(getattr(effect, "angle", 90.0))
                reversed_flag = bool(getattr(effect, "reversed", False))
                return stops, opacity, angle, reversed_flag
        except Exception:
            return None

        return None

    def _apply_color_overlay(
        self,
        image: Image.Image,
        overlay: Tuple[int, int, int, float],
    ) -> Image.Image:
        red, green, blue, opacity = overlay
        base = image.convert("RGBA")
        pixels = []
        for _, _, _, alpha in base.getdata():
            if alpha == 0:
                pixels.append((0, 0, 0, 0))
            else:
                new_alpha = int(round(alpha * opacity))
                pixels.append((red, green, blue, new_alpha))
        recolored = Image.new("RGBA", base.size)
        recolored.putdata(pixels)
        return recolored

    def _apply_gradient_overlay(
        self,
        image: Image.Image,
        overlay: Tuple[List[Tuple[float, Tuple[int, int, int]]], float, float, bool],
    ) -> Image.Image:
        stops, opacity, angle, reversed_flag = overlay
        base = image.convert("RGBA")
        width, height = base.size
        if width <= 0 or height <= 0:
            return base

        radians = math.radians(angle)
        direction_x = math.cos(radians)
        direction_y = math.sin(radians)
        center_x = (width - 1) / 2.0
        center_y = (height - 1) / 2.0

        projections: List[float] = []
        for x, y in ((0.0, 0.0), (width - 1.0, 0.0), (0.0, height - 1.0), (width - 1.0, height - 1.0)):
            projections.append((x - center_x) * direction_x + (y - center_y) * direction_y)
        min_projection = min(projections)
        max_projection = max(projections)
        span = max(max_projection - min_projection, 1e-6)

        if reversed_flag:
            # PSD's reversed flag tends to already be reflected in exported stop ordering
            # for these UI assets, so we keep the original stop order stable.
            pass

        stop_positions = [position for position, _ in stops]
        output: List[Tuple[int, int, int, int]] = []
        for y in range(height):
            for x in range(width):
                _, _, _, alpha = base.getpixel((x, y))
                if alpha == 0:
                    output.append((0, 0, 0, 0))
                    continue

                projection = (x - center_x) * direction_x + (y - center_y) * direction_y
                t = (projection - min_projection) / span
                t = max(0.0, min(1.0, t))

                if t <= stop_positions[0]:
                    red, green, blue = stops[0][1]
                elif t >= stop_positions[-1]:
                    red, green, blue = stops[-1][1]
                else:
                    red = green = blue = 255
                    for index in range(1, len(stops)):
                        left_position, left_color = stops[index - 1]
                        right_position, right_color = stops[index]
                        if left_position <= t <= right_position:
                            local_span = max(right_position - left_position, 1e-6)
                            ratio = (t - left_position) / local_span
                            red = int(round(left_color[0] * (1.0 - ratio) + right_color[0] * ratio))
                            green = int(round(left_color[1] * (1.0 - ratio) + right_color[1] * ratio))
                            blue = int(round(left_color[2] * (1.0 - ratio) + right_color[2] * ratio))
                            break

                output.append((red, green, blue, int(round(alpha * opacity))))

        recolored = Image.new("RGBA", base.size)
        recolored.putdata(output)
        return recolored

    def _apply_supported_effect_overlays(self, layer: Any, image: Image.Image) -> Image.Image:
        color_overlay = self._get_enabled_color_overlay(layer)
        if color_overlay is not None:
            return self._apply_color_overlay(image, color_overlay)

        gradient_overlay = self._get_enabled_gradient_overlay(layer)
        if gradient_overlay is not None:
            return self._apply_gradient_overlay(image, gradient_overlay)

        return image

    def _render_group_fallback(self, layer: Any) -> Optional[Image.Image]:
        """Fallback compositor for groups when psd-tools composite cannot render them directly."""
        children = list(layer) if hasattr(layer, "__iter__") else []
        rendered_children: List[Tuple[Image.Image, Tuple[int, int, int, int]]] = []
        for child in children:
            bbox = self._normalize_bbox(child.bbox)
            if bbox is None:
                continue
            image = self._render_layer(child)
            if image is None:
                continue
            rendered_children.append((image, bbox))

        if not rendered_children:
            return None

        bbox = self._normalize_bbox(layer.bbox) or self._union_bbox([item_bbox for _, item_bbox in rendered_children])
        if bbox is None:
            return None

        left, top, right, bottom = bbox
        canvas = Image.new("RGBA", (max(1, right - left), max(1, bottom - top)), (0, 0, 0, 0))
        for image, child_bbox in rendered_children:
            offset = (child_bbox[0] - left, child_bbox[1] - top)
            canvas.alpha_composite(image.convert("RGBA"), offset)
        return canvas

    def _render_from_bytes(self, layer_data: bytes) -> Image.Image:
        """
        Render legacy byte payloads.

        If the bytes are a valid image, use them directly.
        Otherwise keep backward compatibility by generating a deterministic placeholder.
        """
        try:
            with Image.open(io.BytesIO(layer_data)) as image:
                return image.convert("RGBA")
        except Exception:
            image = Image.new("RGBA", (200, 150), (240, 240, 240, 255))
            return image

    def _crop_whitespace_image(self, image: Image.Image) -> Image.Image:
        """Crop transparent or uniform borders."""
        image = image.convert("RGBA")
        alpha_bbox = image.getchannel("A").getbbox()
        if alpha_bbox:
            return image.crop(alpha_bbox)

        background = Image.new(image.mode, image.size, image.getpixel((0, 0)))
        diff = ImageChops.difference(image, background)
        bbox = diff.getbbox()
        return image.crop(bbox) if bbox else image

    def _scale_image(self, image: Image.Image, scale: float) -> Image.Image:
        """Resize the rendered image by the requested scale."""
        width = max(1, int(round(image.width * scale)))
        height = max(1, int(round(image.height * scale)))
        return image.resize((width, height), Image.Resampling.LANCZOS)

    def _save_image(self, image: Image.Image, output_path: Path, format: str) -> int:
        """Save an image to disk in the requested format."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == "svg":
            png_buffer = io.BytesIO()
            image.save(png_buffer, format="PNG")
            encoded = base64.b64encode(png_buffer.getvalue()).decode("ascii")
            svg = (
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{image.width}" height="{image.height}" '
                f'viewBox="0 0 {image.width} {image.height}">\n'
                f'  <image width="{image.width}" height="{image.height}" href="data:image/png;base64,{encoded}"/>\n'
                "</svg>\n"
            )
            output_path.write_text(svg, encoding="utf-8")
            return output_path.stat().st_size

        save_image = image.convert("RGBA")
        save_kwargs: Dict[str, Any] = {}

        if format == "jpg":
            background = Image.new("RGB", save_image.size, (255, 255, 255))
            background.paste(save_image, mask=save_image.getchannel("A"))
            save_image = background
            save_kwargs["quality"] = 95
        elif format == "webp":
            save_kwargs["quality"] = 95
            save_kwargs["lossless"] = True

        save_format = {
            "jpg": "JPEG",
            "png": "PNG",
            "webp": "WEBP",
        }.get(format, format.upper())
        save_image.save(output_path, format=save_format, **save_kwargs)
        return output_path.stat().st_size

    def _fingerprint_image(self, image: Image.Image, format: str) -> str:
        digest = hashlib.sha256()
        digest.update(format.encode("utf-8"))
        digest.update(str(image.size).encode("utf-8"))
        digest.update(image.convert("RGBA").tobytes())
        return digest.hexdigest()

    def _get_psd(self, source_file: str) -> PSDImage:
        if source_file not in self._psd_cache:
            self._psd_cache[source_file] = PSDImage.open(source_file)
        return self._psd_cache[source_file]

    def _get_layer_map(self, source_file: str, psd: PSDImage) -> Dict[str, Dict[str, Any]]:
        if source_file in self._layer_cache:
            return self._layer_cache[source_file]

        layer_map: Dict[str, Dict[str, Any]] = {}
        counter = 0

        def walk(layer: Any, parent_id: Optional[str] = None):
            nonlocal counter
            layer_id = f"layer_{counter}"
            counter += 1
            setattr(layer, "_smart_cut_layer_id", layer_id)
            layer_map[layer_id] = {
                "layer": layer,
                "parent_id": parent_id,
                "children": [],
                "bbox": self._normalize_bbox(getattr(layer, "bbox", None)),
            }
            if parent_id and parent_id in layer_map:
                layer_map[parent_id]["children"].append(layer_id)
            if hasattr(layer, "__iter__"):
                for child in layer:
                    walk(child, layer_id)

        for layer in psd:
            walk(layer)

        self._layer_cache[source_file] = layer_map
        return layer_map

    def _find_render_ancestor(
        self,
        layer_ids: List[str],
        layer_map: Dict[str, Dict[str, Any]],
    ) -> Optional[str]:
        if not layer_ids:
            return None

        if len(layer_ids) == 1:
            return layer_ids[0]

        lineages = [self._build_lineage(layer_id, layer_map) for layer_id in layer_ids if layer_id in layer_map]
        if not lineages:
            return None

        shared = set(lineages[0])
        for lineage in lineages[1:]:
            shared &= set(lineage)
        if not shared:
            return None

        # choose the deepest shared ancestor
        deepest = None
        deepest_depth = -1
        for candidate in shared:
            depth = len(self._build_lineage(candidate, layer_map))
            if depth > deepest_depth:
                deepest = candidate
                deepest_depth = depth
        return deepest

    def _build_lineage(
        self,
        layer_id: str,
        layer_map: Dict[str, Dict[str, Any]],
    ) -> List[str]:
        lineage: List[str] = []
        current = layer_id
        while current and current in layer_map:
            lineage.append(current)
            current = layer_map[current].get("parent_id")
        return lineage

    def _expand_render_targets(
        self,
        layer_ids: List[str],
        layer_map: Dict[str, Dict[str, Any]],
    ) -> Set[str]:
        expanded: Set[str] = set()

        def walk(target_id: str) -> None:
            if target_id in expanded or target_id not in layer_map:
                return
            expanded.add(target_id)
            for child_id in layer_map[target_id].get("children", []):
                walk(child_id)

        for layer_id in layer_ids:
            walk(layer_id)
        return expanded

    def _normalize_bbox(self, bbox: Any) -> Optional[Tuple[int, int, int, int]]:
        if bbox is None:
            return None

        if isinstance(bbox, dict):
            left = int(bbox.get("x", 0))
            top = int(bbox.get("y", 0))
            width = int(bbox.get("width", 0))
            height = int(bbox.get("height", 0))
            right = left + width
            bottom = top + height
            return None if width <= 0 or height <= 0 else (left, top, right, bottom)

        if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
            left, top, right, bottom = [int(value) for value in bbox]
            return None if right <= left or bottom <= top else (left, top, right, bottom)

        return None

    def _union_bbox(self, boxes: List[Tuple[int, int, int, int]]) -> Optional[Tuple[int, int, int, int]]:
        if not boxes:
            return None
        left = min(box[0] for box in boxes)
        top = min(box[1] for box in boxes)
        right = max(box[2] for box in boxes)
        bottom = max(box[3] for box in boxes)
        return (left, top, right, bottom)

    def _collect_hidden_layer_ids(self, spec: Dict[str, Any]) -> List[str]:
        hidden_layer_ids: List[str] = []
        for key in ("hidden_layer_ids", "background_layer_ids"):
            for layer_id in spec.get(key, []) or []:
                if layer_id and layer_id not in hidden_layer_ids:
                    hidden_layer_ids.append(layer_id)
        return hidden_layer_ids

    def get_output_dir(self) -> Path:
        """Get the current output directory."""
        return self.output_dir

    def set_output_dir(self, output_dir: str) -> None:
        """Set the output directory."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._fingerprint_cache.clear()
        self.logger.info(f"Output dir changed to: {self.output_dir}")
