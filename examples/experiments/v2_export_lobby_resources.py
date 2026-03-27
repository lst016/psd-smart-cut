from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import Counter, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from PIL import Image, ImageChops
from psd_tools import PSDImage

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from skills.psd_parser.level5_export.asset_exporter import AssetExporter

try:
    import cv2
    import numpy as np
except Exception:  # pragma: no cover - local fallback only
    cv2 = None
    np = None


BBox = Tuple[int, int, int, int]
Layer = Any


@dataclass
class ResourceSpec:
    resource_id: str
    resource_key: str
    resource_type: str
    display_name: str
    tags: List[str]
    source_builder: Callable[[], Tuple[Image.Image, List[Dict[str, str]]]]
    asset_spec_builder: Optional[Callable[[], Dict[str, Any]]] = None


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


NAMES = {
    "group_3": "\u7ec4 3",
    "group_5": "\u7ec4 5",
    "group_6": "\u7ec4 6",
    "top": "\u9876\u90e8",
    "banner": "BANNER",
    "marquee": "\u5f39\u5e55",
    "tab": "tab",
    "bottom_nav": "\u5e95\u90e8\u680f",
    "user_info": "\u7528\u6237\u4fe1\u606f",
    "wealth": "\u8d22\u5bcc",
    "favorites": "\u6536\u85cf",
    "favorite_default": "\u672a\u6536\u85cf",
    "favorite_active": "\u6536\u85cf",
    "badges": "\u89d2\u6807",
    "hot": "\u70ed\u95e8",
    "hot_text": "\u71b1\u9580",
    "new_text": "\u6700\u65b0",
    "chat": "\u804a\u5929",
    "shape_1": "\u77e9\u5f62 1",
    "shape_2": "\u77e9\u5f62 2",
    "shape_3_copy": "\u77e9\u5f62 3 \u62f7\u8d1d",
    "shape_4": "\u77e9\u5f62 4",
    "shape_13": "\u77e9\u5f62 13",
    "shape_14": "\u77e9\u5f62 14",
    "shape_5": "\u77e9\u5f62 5",
    "ellipse_nav_active": "\u692d\u5706 3 \u62f7\u8d1d 2",
    "triangle": "\u4e09\u89d2\u5f62 1",
    "settings_icon": "\u8bbe \u7f6e-\u6811\u83dc\u5355\u8bbe\u7f6e-copy",
    "wealth_refresh": "04\u8f6c\u6362",
}


def _trim(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    alpha_bbox = image.getchannel("A").getbbox()
    if alpha_bbox:
        return image.crop(alpha_bbox)

    background = Image.new(image.mode, image.size, image.getpixel((0, 0)))
    diff = ImageChops.difference(image, background)
    bbox = diff.getbbox()
    return image.crop(bbox) if bbox else image


def _get_enabled_color_overlay(layer: Layer) -> Optional[Tuple[int, int, int, float]]:
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
    layer: Layer,
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


def _apply_color_overlay(image: Image.Image, overlay: Tuple[int, int, int, float]) -> Image.Image:
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
    projections = []
    for x, y in ((0.0, 0.0), (width - 1.0, 0.0), (0.0, height - 1.0), (width - 1.0, height - 1.0)):
        projections.append((x - center_x) * direction_x + (y - center_y) * direction_y)
    min_projection = min(projections)
    max_projection = max(projections)
    span = max(max_projection - min_projection, 1e-6)

    if reversed_flag:
        # Keep PSD stop order stable here; empirically this matches the exported UI icons better.
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


def _apply_supported_effect_overlays(layer: Layer, image: Image.Image) -> Image.Image:
    color_overlay = _get_enabled_color_overlay(layer)
    if color_overlay is not None:
        return _apply_color_overlay(image, color_overlay)

    gradient_overlay = _get_enabled_gradient_overlay(layer)
    if gradient_overlay is not None:
        return _apply_gradient_overlay(image, gradient_overlay)

    return image


def _normalize_bbox(bbox: Any) -> Optional[BBox]:
    if not bbox:
        return None
    left, top, right, bottom = [int(v) for v in bbox]
    if right <= left or bottom <= top:
        return None
    return left, top, right, bottom


def _union_bbox(boxes: Iterable[Optional[BBox]]) -> Optional[BBox]:
    valid = [box for box in boxes if box]
    if not valid:
        return None
    return (
        min(box[0] for box in valid),
        min(box[1] for box in valid),
        max(box[2] for box in valid),
        max(box[3] for box in valid),
    )


def _layer_bbox(layer: Layer) -> Optional[BBox]:
    return _normalize_bbox(getattr(layer, "bbox", None))


def _render_layer(layer: Layer) -> Optional[Image.Image]:
    for method_name in ("topil", "composite"):
        try:
            method = getattr(layer, method_name)
            image = method()
            if image is not None:
                rendered = image.convert("RGBA")
                rendered = _apply_supported_effect_overlays(layer, rendered)
                return rendered
        except Exception:
            pass

    if hasattr(layer, "__iter__"):
        rendered_children: List[Tuple[Image.Image, BBox]] = []
        for child in layer:
            bbox = _layer_bbox(child)
            image = _render_layer(child)
            if bbox and image is not None:
                rendered_children.append((image, bbox))
        if not rendered_children:
            return None
        bbox = _union_bbox([item_bbox for _, item_bbox in rendered_children])
        if bbox is None:
            return None
        left, top, right, bottom = bbox
        canvas = Image.new("RGBA", (right - left, bottom - top), (0, 0, 0, 0))
        for image, child_bbox in rendered_children:
            canvas.alpha_composite(image, (child_bbox[0] - left, child_bbox[1] - top))
        return canvas

    return None


def _render_layers(layers: Sequence[Layer]) -> Image.Image:
    rendered: List[Tuple[Image.Image, BBox]] = []
    for layer in layers:
        bbox = _layer_bbox(layer)
        image = _render_layer(layer)
        if bbox and image is not None:
            rendered.append((image, bbox))
    if not rendered:
        raise ValueError("No renderable layers found")
    bbox = _union_bbox([item_bbox for _, item_bbox in rendered])
    if bbox is None:
        raise ValueError("No valid bbox found")
    left, top, right, bottom = bbox
    canvas = Image.new("RGBA", (right - left, bottom - top), (0, 0, 0, 0))
    for image, item_bbox in rendered:
        canvas.alpha_composite(image, (item_bbox[0] - left, item_bbox[1] - top))
    return _trim(canvas)


def _build_parent_map(root: Layer) -> Dict[int, Optional[Layer]]:
    parent_map: Dict[int, Optional[Layer]] = {id(root): None}

    def walk(layer: Layer) -> None:
        if not hasattr(layer, "__iter__"):
            return
        for child in layer:
            parent_map[id(child)] = layer
            walk(child)

    walk(root)
    return parent_map


def _lineage(layer: Layer, parent_map: Dict[int, Optional[Layer]]) -> List[Layer]:
    result: List[Layer] = []
    current: Optional[Layer] = layer
    while current is not None:
        result.append(current)
        current = parent_map.get(id(current))
    return result


def _common_ancestor(layers: Sequence[Layer], parent_map: Dict[int, Optional[Layer]]) -> Optional[Layer]:
    if not layers:
        return None
    if len(layers) == 1:
        return layers[0]

    shared_ids = set(id(node) for node in _lineage(layers[0], parent_map))
    for layer in layers[1:]:
        shared_ids &= {id(node) for node in _lineage(layer, parent_map)}
    if not shared_ids:
        return None

    deepest: Optional[Layer] = None
    deepest_depth = -1
    for node in _lineage(layers[0], parent_map):
        if id(node) in shared_ids:
            depth = len(_lineage(node, parent_map))
            if depth > deepest_depth:
                deepest = node
                deepest_depth = depth
    return deepest


def _expand_targets(layers: Sequence[Layer]) -> set[int]:
    target_ids: set[int] = set()

    def walk(layer: Layer) -> None:
        layer_id = id(layer)
        if layer_id in target_ids:
            return
        target_ids.add(layer_id)
        if hasattr(layer, "__iter__"):
            for child in layer:
                walk(child)

    for layer in layers:
        walk(layer)
    return target_ids


def _render_layers_with_context(
    layers: Sequence[Layer],
    parent_map: Dict[int, Optional[Layer]],
) -> Image.Image:
    if len(layers) == 1:
        image = _render_layer(layers[0])
        if image is not None:
            return _trim(image)

    bbox = _union_bbox([_layer_bbox(layer) for layer in layers])
    if bbox is None:
        raise ValueError("No valid bbox found")

    ancestor = _common_ancestor(layers, parent_map)
    target_ids = _expand_targets(layers)
    if ancestor is not None:
        try:
            image = ancestor.composite(
                viewport=bbox,
                force=True,
                apply_icc=True,
                layer_filter=lambda candidate: id(candidate) in target_ids,
            )
            if image is not None:
                rgba = image.convert("RGBA")
                if rgba.getchannel("A").getbbox():
                    return _trim(rgba)
        except Exception:
            pass

    return _render_layers(layers)


def _crop_from_group_render(
    group: Layer,
    crop_bbox: BBox,
) -> Image.Image:
    group_bbox = _layer_bbox(group)
    if group_bbox is None:
        raise ValueError("Missing group bbox")
    rendered = group.composite(force=True, apply_icc=True)
    if rendered is None:
        raise ValueError("Unable to render group context")
    image = rendered.convert("RGBA")
    relative_bbox = (
        crop_bbox[0] - group_bbox[0],
        crop_bbox[1] - group_bbox[1],
        crop_bbox[2] - group_bbox[0],
        crop_bbox[3] - group_bbox[1],
    )
    return _trim(image.crop(relative_bbox))


def _pick_edge_background_color(image: Image.Image) -> Tuple[int, int, int]:
    rgba = image.convert("RGBA")
    width, height = rgba.size
    pixels = rgba.load()
    samples: List[Tuple[int, int, int]] = []

    corner_points = [
        (0, 0),
        (max(0, width - 1), 0),
        (0, max(0, height - 1)),
        (max(0, width - 1), max(0, height - 1)),
    ]
    for cx, cy in corner_points:
        for dx in range(0, min(4, width)):
            for dy in range(0, min(4, height)):
                x = min(max(cx + (-dx if cx else dx), 0), width - 1)
                y = min(max(cy + (-dy if cy else dy), 0), height - 1)
                r, g, b, a = pixels[x, y]
                if a > 0:
                    samples.append((r // 8 * 8, g // 8 * 8, b // 8 * 8))

    if not samples:
        return (0, 0, 0)
    return Counter(samples).most_common(1)[0][0]


def _color_distance(first: Tuple[int, int, int], second: Tuple[int, int, int]) -> int:
    return abs(first[0] - second[0]) + abs(first[1] - second[1]) + abs(first[2] - second[2])


def _strip_edge_connected_background(
    image: Image.Image,
    tolerance: int = 80,
) -> Image.Image:
    rgba = image.convert("RGBA")
    width, height = rgba.size
    pixels = rgba.load()
    bg_color = _pick_edge_background_color(rgba)

    queue: deque[Tuple[int, int]] = deque()
    visited: set[Tuple[int, int]] = set()
    mask = [[False for _ in range(width)] for _ in range(height)]

    def enqueue_if_bg(x: int, y: int) -> None:
        if (x, y) in visited:
            return
        r, g, b, a = pixels[x, y]
        if a == 0:
            visited.add((x, y))
            mask[y][x] = True
            queue.append((x, y))
            return
        if _color_distance((r, g, b), bg_color) <= tolerance:
            visited.add((x, y))
            mask[y][x] = True
            queue.append((x, y))

    corner_points = [
        (0, 0),
        (max(0, width - 1), 0),
        (0, max(0, height - 1)),
        (max(0, width - 1), max(0, height - 1)),
    ]
    for cx, cy in corner_points:
        for dx in range(0, min(4, width)):
            for dy in range(0, min(4, height)):
                x = min(max(cx + (-dx if cx else dx), 0), width - 1)
                y = min(max(cy + (-dy if cy else dy), 0), height - 1)
                enqueue_if_bg(x, y)

    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if nx < 0 or ny < 0 or nx >= width or ny >= height or (nx, ny) in visited:
                continue
            r, g, b, a = pixels[nx, ny]
            if a == 0 or _color_distance((r, g, b), bg_color) <= tolerance:
                visited.add((nx, ny))
                mask[ny][nx] = True
                queue.append((nx, ny))

    result = rgba.copy()
    result_pixels = result.load()
    for y in range(height):
        for x in range(width):
            if mask[y][x]:
                r, g, b, _ = result_pixels[x, y]
                result_pixels[x, y] = (r, g, b, 0)
    return _trim(result)


def _grabcut_refine_foreground(image: Image.Image) -> Image.Image:
    if cv2 is None or np is None:
        return image

    rgba = image.convert("RGBA")
    width, height = rgba.size
    if width < 8 or height < 8:
        return rgba

    seed = _strip_edge_connected_background(rgba)
    seed_alpha = np.array(seed.getchannel("A"))
    rgb = np.array(rgba.convert("RGB"))

    mask = np.full((height, width), cv2.GC_PR_BGD, dtype=np.uint8)
    mask[seed_alpha == 0] = cv2.GC_BGD
    mask[seed_alpha > 0] = cv2.GC_FGD

    # If the seed kept almost everything, give GrabCut a softer probable-FG rectangle.
    if np.count_nonzero(seed_alpha) > width * height * 0.85:
        margin_x = max(2, width // 12)
        margin_y = max(2, height // 12)
        mask[:, :] = cv2.GC_PR_BGD
        mask[margin_y:height - margin_y, margin_x:width - margin_x] = cv2.GC_PR_FGD

    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    try:
        cv2.grabCut(rgb, mask, None, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_MASK)
    except Exception:
        return seed

    alpha = np.where(
        (mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD),
        255,
        0,
    ).astype("uint8")

    result = rgba.copy()
    result.putalpha(Image.fromarray(alpha, mode="L"))
    trimmed = _trim(result)
    if trimmed.getchannel("A").getbbox() is None:
        return seed
    return trimmed


def _extract_context_foreground(group: Layer, crop_bbox: BBox) -> Image.Image:
    crop = _crop_from_group_render(group, crop_bbox)
    stripped = _strip_edge_connected_background(crop)
    refined = _grabcut_refine_foreground(stripped if stripped.getchannel("A").getbbox() else crop)
    if refined.getchannel("A").getbbox():
        return refined
    if stripped.getchannel("A").getbbox():
        return stripped
    return crop


def _find_named_children(layer: Layer, name: str) -> List[Layer]:
    return [child for child in layer if getattr(child, "name", "") == name]


def _first(layer: Layer, name: str) -> Layer:
    matches = _find_named_children(layer, name)
    if not matches:
        raise KeyError(f"Missing child '{name}' under '{getattr(layer, 'name', '<root>')}'")
    return matches[0]


def _nth(layer: Layer, name: str, index: int) -> Layer:
    matches = _find_named_children(layer, name)
    if index >= len(matches):
        raise IndexError(f"Missing child '{name}' index {index} under '{getattr(layer, 'name', '<root>')}'")
    return matches[index]


def _first_visible(layer: Layer, name: str) -> Layer:
    matches = [child for child in _find_named_children(layer, name) if getattr(child, "visible", False)]
    if not matches:
        raise KeyError(f"Missing visible child '{name}' under '{getattr(layer, 'name', '<root>')}'")
    return matches[0]


def _refs(layers: Sequence[Layer]) -> List[Dict[str, str]]:
    return [
        {
            "kind": "psd_group" if layer.is_group() else "psd_layer",
            "id": getattr(layer, "name", "") or "unnamed",
        }
        for layer in layers
    ]


def _save_resource(
    output_dir: Path,
    spec: ResourceSpec,
    image: Image.Image,
    source_refs: List[Dict[str, str]],
    source_path: str,
) -> Dict[str, Any]:
    output_path = output_dir / f"{spec.resource_key}.png"
    image.save(output_path, format="PNG")
    digest = hashlib.sha256(image.convert("RGBA").tobytes()).hexdigest()
    return {
        "schema_version": "2.0",
        "resource_id": spec.resource_id,
        "resource_key": spec.resource_key,
        "resource_type": spec.resource_type,
        "display_name": spec.display_name,
        "format": "png",
        "path": f"resources/png/{spec.resource_key}.png",
        "dimensions": {"width": image.width, "height": image.height},
        "hash": digest,
        "usage_count": 1,
        "source_refs": [{**ref, "path": source_path} for ref in source_refs],
        "tags": spec.tags,
    }


def _build_layer_id_lookup(exporter: AssetExporter, source_path: str, psd: PSDImage) -> Dict[int, str]:
    layer_map = exporter._get_layer_map(source_path, psd)
    return {
        id(info["layer"]): layer_id
        for layer_id, info in layer_map.items()
    }


def _asset_spec_from_layers(
    source_path: str,
    layer_id_lookup: Dict[int, str],
    target_layers: Sequence[Layer],
    *,
    background_layers: Optional[Sequence[Layer]] = None,
    context_layers: Optional[Sequence[Layer]] = None,
    preferred_strategy: str = "",
    render_bbox: Optional[BBox] = None,
) -> Dict[str, Any]:
    target_ids = [layer_id_lookup[id(layer)] for layer in target_layers if id(layer) in layer_id_lookup]
    background_ids = [
        layer_id_lookup[id(layer)]
        for layer in (background_layers or [])
        if id(layer) in layer_id_lookup
    ]
    context_ids = [
        layer_id_lookup[id(layer)]
        for layer in (context_layers or [])
        if id(layer) in layer_id_lookup
    ]

    bbox = render_bbox or _union_bbox([_layer_bbox(layer) for layer in target_layers])
    if bbox is None:
        raise ValueError("Missing render bbox for asset spec")

    payload: Dict[str, Any] = {
        "source_file": source_path,
        "layer_ids": target_ids,
        "bbox": list(bbox),
    }
    if preferred_strategy:
        payload["preferred_strategy"] = preferred_strategy
    if background_ids:
        payload["background_layer_ids"] = background_ids
    if context_ids:
        payload["context_layer_ids"] = context_ids
    return payload


def _render_resource(
    spec: ResourceSpec,
    exporter: AssetExporter,
) -> Tuple[Image.Image, List[Dict[str, str]]]:
    if spec.asset_spec_builder is not None:
        asset_spec = spec.asset_spec_builder()
        image = exporter._render_from_psd_spec(asset_spec)
        if image is None:
            raise ValueError(f"Unable to render asset spec for {spec.resource_key}")
        refs: List[Dict[str, str]] = []
        for layer_id in asset_spec.get("layer_ids", []):
            refs.append({"kind": "psd_layer_ref", "id": layer_id})
        for layer_id in asset_spec.get("background_layer_ids", []):
            refs.append({"kind": "psd_background_ref", "id": layer_id})
        return _trim(image), refs

    return spec.source_builder()


def _artboard(psd: PSDImage, index: int) -> Layer:
    return list(psd)[index - 1]

def _build_specs(psd: PSDImage, exporter: AssetExporter, source_path: str) -> List[ResourceSpec]:
    artboard1 = _artboard(psd, 1)
    artboard2 = _artboard(psd, 2)
    artboard3 = _artboard(psd, 3)
    parent_map = _build_parent_map(psd)
    layer_id_lookup = _build_layer_id_lookup(exporter, source_path, psd)

    top_group = _first(artboard1, NAMES["top"])
    banner_group = _first(artboard1, NAMES["banner"])
    marquee_group = _first(artboard1, NAMES["marquee"])
    marquee_text = list(marquee_group)[0]
    tab_group = _first(artboard1, NAMES["tab"])
    provider_tab_group = _first(artboard3, NAMES["tab"])
    provider_filter_group = _first(provider_tab_group, "组 7")
    card_group = _first(artboard1, NAMES["group_3"])
    badge_root = _first(card_group, NAMES["badges"])
    favorites_root = _first(badge_root, NAMES["favorites"])
    favorite_default = _first(favorites_root, NAMES["favorite_default"])
    favorite_active = _first(favorites_root, NAMES["favorite_active"])
    hot_root = _first(badge_root, NAMES["hot"])
    floating_chat = _first(artboard1, NAMES["group_5"])
    floating_survey = _first(artboard1, NAMES["group_6"])
    bottom_nav = _first(artboard1, NAMES["bottom_nav"])
    questionnaire_cta = _first(artboard1, "qp")
    game_rows = [child for child in card_group if child.is_group() and child.name in {"1", "2", "3"}]
    user_info = _first(top_group, NAMES["user_info"])
    wealth = _first(top_group, NAMES["wealth"])
    chat_panel = _first(artboard2, NAMES["chat"])
    floating_chat_base = _first(floating_chat, "矩形 10")
    floating_chat_icon = _first(floating_chat, "bg-chat")
    floating_chat_label = _first(floating_chat, "聊天")
    floating_chat_badge = _first(floating_chat, "椭圆 4")

    def one(layer: Layer) -> Tuple[Image.Image, List[Dict[str, str]]]:
        return _render_layers_with_context([layer], parent_map), _refs([layer])

    def many(layers: Sequence[Layer]) -> Tuple[Image.Image, List[Dict[str, str]]]:
        return _render_layers_with_context(layers, parent_map), _refs(layers)

    def marquee_background() -> Tuple[Image.Image, List[Dict[str, str]]]:
        marquee_bbox = _layer_bbox(marquee_text)
        banner_bbox = _layer_bbox(banner_group)
        if marquee_bbox is None or banner_bbox is None:
            raise ValueError("Missing marquee or banner bbox")
        left = banner_bbox[0]
        right = banner_bbox[2]
        top = marquee_bbox[1] - 4
        bottom = marquee_bbox[3] + 4
        canvas = Image.new("RGBA", (right - left, bottom - top), (66, 19, 112, 242))
        return canvas, [{"kind": "synthetic", "id": "marquee_background"}]

    hot_rect = _nth(hot_root, NAMES["shape_13"], 0)
    hot_text = _nth(hot_root, NAMES["hot_text"], 0)
    new_rect = _nth(hot_root, NAMES["shape_13"], 2)
    new_text = _first(hot_root, NAMES["new_text"])
    bottom_badge_outer = _nth(bottom_nav, "椭圆 4", 0)
    bottom_badge_inner = _nth(bottom_nav, "椭圆 4", 1)
    bottom_nav_bg_layer = _first(bottom_nav, NAMES["shape_5"])
    bottom_nav_active_bg_layer = _first(bottom_nav, NAMES["ellipse_nav_active"])
    bottom_nav_notice_layer = _first(bottom_nav, "公告 (1) 拷贝")
    bottom_nav_donation_layer = _first(bottom_nav, "icon_donation")
    bottom_nav_welfare_layer = _first(bottom_nav, "标签栏_福利")
    bottom_nav_mail_layer = _first(bottom_nav, "邮箱 (1)")
    bottom_nav_notice_text = _first(bottom_nav, "公告")
    bottom_nav_donation_text = _first(bottom_nav, "支援金")
    bottom_nav_mall_text = _nth(bottom_nav, "商城", 1)
    bottom_nav_gift_text = _first(bottom_nav, "贈禮")
    bottom_nav_mail_text = _first(bottom_nav, "郵箱")
    bottom_nav_mall_primary = _nth(bottom_nav, "商城", 0)
    bottom_nav_mall_layers = [
        bottom_nav_mall_primary,
        _first(bottom_nav, "购物"),
        _first(bottom_nav, "购物 购物车 订购"),
        _nth(bottom_nav, "商城 (1)", 0),
    ]
    nav_context_boxes = {
        "notice": (53, 1503, 99, 1549),
        "donation": (174, 1456, 258, 1551),
        "mall": (321, 1456, 430, 1572),
        "welfare": (507, 1497, 576, 1549),
        "mail": (649, 1511, 694, 1545),
    }
    provider_atg_icon = _first(provider_filter_group, "图层 848")
    provider_o8_icon = _first(provider_filter_group, "图层 856")
    provider_vplus_icon = _first(provider_filter_group, "图层 855")
    provider_stm_icon = _first(provider_filter_group, "图层 849")
    provider_hs_icon = _first(provider_filter_group, "HACK.ST_BIG")
    provider_atg_text = _first(provider_filter_group, "ATG")
    provider_o8_text = _first(provider_filter_group, "O8")
    provider_vplus_text = _first(provider_filter_group, "VPLUS")
    provider_stm_text = _first(provider_filter_group, "STM")
    provider_hs_text = _first(provider_filter_group, "HS")

    card_slots: List[Tuple[str, str, Layer]] = []
    slot_counter = 1
    for row in game_rows:
        for child in row:
            if child.is_group() and _normalize_bbox(getattr(child, "bbox", None)):
                key = f"game_card_{slot_counter:02d}"
                display = f"大厅卡片实例 {slot_counter:02d}"
                card_slots.append((key, display, child))
                slot_counter += 1

    card_shape_layers: List[Layer] = []
    for _, _, card in card_slots:
        for child in card:
            if getattr(child, "kind", "") == "shape":
                card_shape_layers.append(child)
                break

    specs = [
        ResourceSpec(
            resource_id="res_settings_icon",
            resource_key="settings_icon",
            resource_type="icon",
            display_name="设置图标",
            tags=["exported", "header", "shared"],
            source_builder=lambda: one(_first(top_group, NAMES["settings_icon"])),
        ),
        ResourceSpec(
            resource_id="res_wealth_refresh_icon",
            resource_key="wealth_refresh_icon",
            resource_type="icon",
            display_name="财富刷新图标",
            tags=["exported", "header", "shared"],
            source_builder=lambda: one(_first(wealth, NAMES["wealth_refresh"])),
        ),
        ResourceSpec(
            resource_id="res_hero_banner",
            resource_key="hero_banner",
            resource_type="artwork",
            display_name="大厅主 Banner",
            tags=["exported", "banner", "shared"],
            source_builder=lambda: one(banner_group),
        ),
        ResourceSpec(
            resource_id="res_marquee_background",
            resource_key="marquee_background",
            resource_type="bar_skin",
            display_name="跑马灯背景",
            tags=["exported", "marquee", "shared"],
            source_builder=marquee_background,
        ),
        ResourceSpec(
            resource_id="res_tab_normal",
            resource_key="tab_normal",
            resource_type="tab_skin",
            display_name="大厅分类未选中态",
            tags=["exported", "tab", "shared"],
            source_builder=lambda: one(_nth(tab_group, NAMES["shape_2"], 1)),
        ),
        ResourceSpec(
            resource_id="res_tab_active",
            resource_key="tab_active",
            resource_type="tab_skin",
            display_name="大厅分类选中态",
            tags=["exported", "tab", "shared"],
            source_builder=lambda: one(_nth(tab_group, NAMES["shape_2"], 0)),
        ),
        ResourceSpec(
            resource_id="res_tab_dropdown_arrow",
            resource_key="tab_dropdown_arrow",
            resource_type="icon",
            display_name="分类下拉箭头",
            tags=["exported", "tab", "shared"],
            source_builder=lambda: one(_first(tab_group, NAMES["triangle"])),
        ),
        ResourceSpec(
            resource_id="res_provider_atg_entry",
            resource_key="provider_atg_entry",
            resource_type="provider_entry",
            display_name="电子分类 ATG 品牌入口",
            tags=["exported", "provider-filter", "shared"],
            source_builder=lambda: many([provider_atg_icon, provider_atg_text]),
        ),
        ResourceSpec(
            resource_id="res_provider_o8_entry",
            resource_key="provider_o8_entry",
            resource_type="provider_entry",
            display_name="电子分类 O8 品牌入口",
            tags=["exported", "provider-filter", "shared"],
            source_builder=lambda: many([provider_o8_icon, provider_o8_text]),
        ),
        ResourceSpec(
            resource_id="res_provider_vplus_entry",
            resource_key="provider_vplus_entry",
            resource_type="provider_entry",
            display_name="电子分类 VPLUS 品牌入口",
            tags=["exported", "provider-filter", "shared"],
            source_builder=lambda: many([provider_vplus_icon, provider_vplus_text]),
        ),
        ResourceSpec(
            resource_id="res_provider_stm_entry",
            resource_key="provider_stm_entry",
            resource_type="provider_entry",
            display_name="电子分类 STM 品牌入口",
            tags=["exported", "provider-filter", "shared"],
            source_builder=lambda: many([provider_stm_icon, provider_stm_text]),
        ),
        ResourceSpec(
            resource_id="res_provider_hs_entry",
            resource_key="provider_hs_entry",
            resource_type="provider_entry",
            display_name="电子分类 HS 品牌入口",
            tags=["exported", "provider-filter", "shared"],
            source_builder=lambda: many([provider_hs_icon, provider_hs_text]),
        ),
        ResourceSpec(
            resource_id="res_favorite_icon_default",
            resource_key="favorite_icon_default",
            resource_type="icon_state",
            display_name="收藏默认态",
            tags=["exported", "favorite", "shared"],
            source_builder=lambda: one(favorite_default),
        ),
        ResourceSpec(
            resource_id="res_favorite_icon_active",
            resource_key="favorite_icon_active",
            resource_type="icon_state",
            display_name="收藏激活态",
            tags=["exported", "favorite", "shared"],
            source_builder=lambda: one(favorite_active),
        ),
        ResourceSpec(
            resource_id="res_badge_hot",
            resource_key="badge_hot",
            resource_type="badge",
            display_name="热门角标",
            tags=["exported", "badge", "shared"],
            source_builder=lambda: many([hot_rect, hot_text]),
        ),
        ResourceSpec(
            resource_id="res_badge_new",
            resource_key="badge_new",
            resource_type="badge",
            display_name="最新角标",
            tags=["exported", "badge", "shared"],
            source_builder=lambda: many([new_rect, new_text]),
        ),
        ResourceSpec(
            resource_id="res_floating_survey_button",
            resource_key="floating_survey_button",
            resource_type="shortcut_button",
            display_name="左侧问卷快捷按钮",
            tags=["exported", "floating", "shared"],
            source_builder=lambda: one(floating_survey),
        ),
        ResourceSpec(
            resource_id="res_questionnaire_cta_button",
            resource_key="questionnaire_cta_button",
            resource_type="cta_button",
            display_name="问卷活动按钮",
            tags=["exported", "floating", "cta"],
            source_builder=lambda: many(list(questionnaire_cta)),
        ),
        ResourceSpec(
            resource_id="res_chat_entry_icon",
            resource_key="chat_entry_icon",
            resource_type="icon",
            display_name="聊天入口共享图标",
            tags=["exported", "floating", "chat", "shared"],
            source_builder=lambda: one(floating_chat_icon),
        ),
        ResourceSpec(
            resource_id="res_floating_chat_button_base",
            resource_key="floating_chat_button_base",
            resource_type="shortcut_button",
            display_name="左侧聊天按钮主体",
            tags=["exported", "floating", "chat", "component"],
            source_builder=lambda: many([floating_chat_base, floating_chat_icon, floating_chat_label]),
        ),
        ResourceSpec(
            resource_id="res_floating_chat_unread_badge",
            resource_key="floating_chat_unread_badge",
            resource_type="badge",
            display_name="左侧聊天未读气泡",
            tags=["exported", "floating", "chat", "shared"],
            source_builder=lambda: one(floating_chat_badge),
        ),
        ResourceSpec(
            resource_id="res_bottom_nav_bg",
            resource_key="bottom_nav_bg",
            resource_type="nav_skin",
            display_name="底部导航栏背景",
            tags=["exported", "bottom-nav", "shared"],
            source_builder=lambda: one(_first(bottom_nav, NAMES["shape_5"])),
        ),
        ResourceSpec(
            resource_id="res_bottom_nav_active_bg",
            resource_key="bottom_nav_active_bg",
            resource_type="nav_state",
            display_name="底部导航激活底座",
            tags=["exported", "bottom-nav", "shared"],
            source_builder=lambda: one(_first(bottom_nav, NAMES["ellipse_nav_active"])),
        ),
        ResourceSpec(
            resource_id="res_bottom_nav_notice_icon",
            resource_key="bottom_nav_notice_icon",
            resource_type="nav_icon",
            display_name="底部栏公告图标",
            tags=["exported", "bottom-nav", "shared"],
            source_builder=lambda: one(bottom_nav_notice_layer),
        ),
        ResourceSpec(
            resource_id="res_bottom_nav_donation_icon",
            resource_key="bottom_nav_donation_icon",
            resource_type="nav_icon",
            display_name="底部栏支援金图标",
            tags=["exported", "bottom-nav", "shared"],
            source_builder=lambda: one(bottom_nav_donation_layer),
        ),
        ResourceSpec(
            resource_id="res_bottom_nav_mall_icon",
            resource_key="bottom_nav_mall_icon",
            resource_type="nav_icon",
            display_name="底部栏商城图标",
            tags=["exported", "bottom-nav", "shared"],
            source_builder=lambda: one(bottom_nav_mall_primary),
            asset_spec_builder=lambda: _asset_spec_from_layers(
                source_path,
                layer_id_lookup,
                [bottom_nav_mall_primary],
            ),
        ),
        ResourceSpec(
            resource_id="res_bottom_nav_welfare_icon",
            resource_key="bottom_nav_welfare_icon",
            resource_type="nav_icon",
            display_name="底部栏福利图标",
            tags=["exported", "bottom-nav", "shared"],
            source_builder=lambda: one(bottom_nav_welfare_layer),
        ),
        ResourceSpec(
            resource_id="res_bottom_nav_mail_icon",
            resource_key="bottom_nav_mail_icon",
            resource_type="nav_icon",
            display_name="底部栏邮箱图标",
            tags=["exported", "bottom-nav", "shared"],
            source_builder=lambda: one(bottom_nav_mail_layer),
        ),
        ResourceSpec(
            resource_id="res_game_card_small_skin",
            resource_key="game_card_small_skin",
            resource_type="card_skin",
            display_name="大厅小卡片底板",
            tags=["exported", "game-card", "shared"],
            source_builder=lambda: one(card_shape_layers[0]),
        ),
        ResourceSpec(
            resource_id="res_game_card_large_skin",
            resource_key="game_card_large_skin",
            resource_type="card_skin",
            display_name="大厅大卡片底板",
            tags=["exported", "game-card", "shared"],
            source_builder=lambda: one(card_shape_layers[6]),
        ),
    ]

    for index, (resource_key, display_name, card_layer) in enumerate(card_slots, start=1):
        specs.append(
            ResourceSpec(
                resource_id=f"res_{resource_key}",
                resource_key=resource_key,
                resource_type="card_instance",
                display_name=display_name,
                tags=["exported", "game-card", "instance"],
                source_builder=lambda card_layer=card_layer: one(card_layer),
            )
        )
    return specs


def _write_component_analysis(analysis_dir: Path) -> None:
    _write_text(
        analysis_dir / "component-analysis.md",
        """
# 前端分析

## 页面定位

- 页面类型：游戏大厅
- 主页面：大厅默认态
- 衍生状态：聊天展开态、筛选展开态、内容浏览态

## 关键模块

- 顶部信息栏
- Banner 与跑马灯
- 分类 Tab 栏
- 电子分类品牌筛选栏
- 游戏卡片区
- 浮动入口区
- 底部导航栏
- 聊天面板

## 重点组件判断

### TopHeader

顶部账户栏不应直接输出一整张 `top_account_bar_skin`。
更合理的拆法是：
- `profile_capsule`
- `wallet_capsule`
- `settings_icon`
- `refresh_icon`

实现建议：
- `profile_capsule`：优先 CSS
- `wallet_capsule`：优先 CSS
- `settings_icon`：图片资源
- `refresh_icon`：图片资源

### ProviderFilter

画板 3 的电子分类子 Tab 不应忽略。
更合理的拆法是：
- `provider_filter_bar`
- `provider_brand_entry`

实现建议：
- `provider_filter_bar`：优先 CSS
- `provider_brand_entry`：图片资源
- 品牌文案如已融入品牌视觉，一并作为资源输出

### FloatingChatEntry

这不是一张图，而是一个前端组件。

建议拆解：

- `chat_button_base`
- `unread_badge`
- `unread_count_text`

实现建议：

- `chat_button_base`：图片资源
- `unread_badge`：优先 CSS 圆角气泡
- `unread_count_text`：文本

### ChatPanel

这不是优先切整图的资源。

建议拆解：

- `panel_background`
- `chat_icon`
- `message_preview_text`
- `message_counter`

实现建议：

- `panel_background`：优先 CSS
- `chat_icon`：复用共享图标
- `message_preview_text`：文本
- `message_counter`：文本或徽标配置

### BottomNavBar

底部导航应按“共享状态资源 + 文本标签”建模，而不是一律切成栏目项整图。

建议拆解：

- `icon`
- `label_text`
- `active_bg`
- `badge_bg`
- `badge_text`

实现建议：

- `icon`：图片资源
- `label_text`：文本
- `active_bg`：图片资源
- `badge_bg`：优先 CSS
- `badge_text`：文本

### GameCard

游戏卡片应按“共享底板 + 实例主视觉 + 共享角标/收藏图标”建模。

建议拆解：

- `card_skin`
- `cover_artwork`
- `favorite_icon`
- `badge`

实现建议：

- `card_skin`：共享图片
- `cover_artwork`：实例图片
- `favorite_icon`：共享图片
- `badge`：共享资源
""",
    )

    _write_json(
        analysis_dir / "component-analysis.json",
        {
            "page_id": "lobby_home",
            "page_type": "game_lobby",
            "page_states": ["default", "chat_open", "filter_open", "browse_focus"],
            "modules": [
                {
                    "module_id": "top_header",
                    "module_type": "header_bar",
                    "components": [
                        {
                            "component_id": "top_header",
                            "component_type": "header_bar",
                            "subparts": ["profile_capsule", "wallet_capsule", "settings_icon", "refresh_icon"],
                            "states": ["default"],
                        }
                    ],
                },
                {
                    "module_id": "provider_filter",
                    "module_type": "provider_filter_bar",
                    "components": [
                        {
                            "component_id": "provider_brand_entry",
                            "component_type": "provider_brand_entry",
                            "subparts": ["provider_filter_bar", "brand_entry_artwork"],
                            "states": ["default", "selected_filter"],
                        }
                    ],
                },
                {
                    "module_id": "floating_actions",
                    "module_type": "floating_action_stack",
                    "components": [
                        {
                            "component_id": "floating_chat_entry",
                            "component_type": "floating_chat_entry",
                            "subparts": [
                                "chat_button_base",
                                "unread_badge",
                                "unread_count_text",
                            ],
                            "states": ["default", "has_unread"],
                        },
                        {
                            "component_id": "floating_survey_entry",
                            "component_type": "floating_shortcut_entry",
                            "subparts": ["button_artwork"],
                            "states": ["default"],
                        },
                    ],
                },
                {
                    "module_id": "chat_panel",
                    "module_type": "chat_overlay",
                    "components": [
                        {
                            "component_id": "chat_panel",
                            "component_type": "chat_panel",
                            "subparts": [
                                "panel_background",
                                "chat_icon",
                                "message_preview_text",
                                "message_counter",
                            ],
                            "states": ["collapsed", "expanded"],
                        }
                    ],
                },
                {
                    "module_id": "bottom_nav",
                    "module_type": "bottom_navigation",
                    "components": [
                        {
                            "component_id": "bottom_nav_item",
                            "component_type": "bottom_nav_item",
                            "subparts": ["icon", "label_text", "active_bg", "badge_bg", "badge_text"],
                            "states": ["default", "active", "has_badge"],
                        }
                    ],
                },
                {
                    "module_id": "game_cards",
                    "module_type": "game_card_grid",
                    "components": [
                        {
                            "component_id": "game_card",
                            "component_type": "game_card",
                            "subparts": ["card_skin", "cover_artwork", "favorite_icon", "badge"],
                            "states": ["default", "favorited", "tagged"],
                        }
                    ],
                },
            ],
        },
    )


def _write_strategy_decision(strategy_dir: Path, profile: str) -> None:
    _write_json(
        strategy_dir / f"strategy-decision.{profile}.json",
        {
            "page_id": "lobby_home",
            "components": [
                {
                    "component_id": "top_header",
                    "component_type": "header_bar",
                    "implementation": [
                        {
                            "part_id": "profile_capsule",
                            "preferred_mode": "css",
                            "reason": "头像容器与基础圆角底板属于纯色结构，优先前端样式实现",
                        },
                        {
                            "part_id": "wallet_capsule",
                            "preferred_mode": "css",
                            "reason": "财富栏底板可由圆角与渐变样式实现，不必默认切图",
                        },
                        {
                            "part_id": "settings_icon",
                            "preferred_mode": "image",
                            "reason": "设置图标是明确的独立视觉资源",
                        },
                        {
                            "part_id": "refresh_icon",
                            "preferred_mode": "image",
                            "reason": "刷新图标是明确的独立视觉资源",
                        },
                    ],
                },
                {
                    "component_id": "provider_brand_entry",
                    "component_type": "provider_brand_entry",
                    "implementation": [
                        {
                            "part_id": "provider_filter_bar",
                            "preferred_mode": "css",
                            "reason": "电子分类条的底板和分隔更适合前端样式实现",
                        },
                        {
                            "part_id": "brand_entry_artwork",
                            "preferred_mode": "image",
                            "reason": "品牌 logo 与品牌字样组合属于不可稳定 CSS 还原的品牌视觉",
                        },
                    ],
                },
                {
                    "component_id": "floating_chat_entry",
                    "component_type": "floating_chat_entry",
                    "implementation": [
                        {
                            "part_id": "chat_button_base",
                            "preferred_mode": "image",
                            "reason": "主体按钮带图标与底板，直接导出更稳定",
                        },
                        {
                            "part_id": "unread_badge",
                            "preferred_mode": "css",
                            "reason": "红色圆形气泡适合 CSS 构建，避免重复切图",
                        },
                        {
                            "part_id": "unread_count_text",
                            "preferred_mode": "text",
                            "reason": "未读数字必须保持可编辑",
                        },
                    ],
                },
                {
                    "component_id": "chat_panel",
                    "component_type": "chat_panel",
                    "implementation": [
                        {
                            "part_id": "panel_background",
                            "preferred_mode": "css",
                            "reason": "面板背景和圆角样式适合前端样式实现",
                        },
                        {
                            "part_id": "chat_icon",
                            "preferred_mode": "image",
                            "reason": "共享聊天图标可复用到聊天入口和聊天面板",
                        },
                        {
                            "part_id": "message_preview_text",
                            "preferred_mode": "text",
                            "reason": "消息预览属于内容文本，不应烘焙为位图",
                        },
                        {
                            "part_id": "message_counter",
                            "preferred_mode": "text",
                            "reason": "数量或状态文本需要可配置",
                        },
                    ],
                },
                {
                    "component_id": "bottom_nav_item",
                    "component_type": "bottom_nav_item",
                    "implementation": [
                        {
                            "part_id": "icon",
                            "preferred_mode": "image",
                            "reason": "导航图标以 PSD 图层直出最稳定",
                        },
                        {
                            "part_id": "label_text",
                            "preferred_mode": "text",
                            "reason": "导航文案应保持文本",
                        },
                        {
                            "part_id": "active_bg",
                            "preferred_mode": "image",
                            "reason": "选中底座具备固定视觉皮肤",
                        },
                        {
                            "part_id": "badge",
                            "preferred_mode": "css",
                            "reason": "红点与数字都应优先走 CSS + 文本，避免切纯色小资源",
                        },
                    ],
                },
                {
                    "component_id": "game_card",
                    "component_type": "game_card",
                    "implementation": [
                        {
                            "part_id": "card_skin",
                            "preferred_mode": "image",
                            "reason": "卡片底板是稳定共享皮肤",
                        },
                        {
                            "part_id": "cover_artwork",
                            "preferred_mode": "image",
                            "reason": "游戏主视觉实例差异大，应作为实例图片保留",
                        },
                        {
                            "part_id": "favorite_icon",
                            "preferred_mode": "image",
                            "reason": "收藏图标有共享的视觉状态",
                        },
                        {
                            "part_id": "badge",
                            "preferred_mode": "mixed",
                            "reason": "角标背景可共享，文字优先文本或独立资源",
                        },
                    ],
                },
            ],
        },
    )


def _write_resource_task_list(plan_dir: Path, profile: str) -> None:
    _write_json(
        plan_dir / f"resource-task-list.{profile}.json",
        {
            "schema_version": "2.0",
            "job_id": "job_lobby_home_v2_trial_refined",
            "module_id": "lobby_home",
            "strategy": "frontend_analysis_first",
            "tasks": [
                {
                    "task_id": "task_top_header_css_first",
                    "resource_key": "top_header",
                    "component_scope": "top_header",
                    "execution_group": "worker_header_and_tabs",
                    "priority": 1,
                    "must_export": False,
                    "shared": True,
                    "status": "planned",
                    "notes": ["顶部账户栏改为 CSS 优先，不再导出语义不清的 top_account_bar_skin，只保留设置和刷新图标"],
                },
                {
                    "task_id": "task_provider_filter_brand_entries",
                    "resource_key": "provider_brand_entry",
                    "component_scope": "provider_filter",
                    "execution_group": "worker_header_and_tabs",
                    "priority": 1,
                    "must_export": True,
                    "shared": True,
                    "status": "completed",
                    "notes": ["画板 3 电子分类子 Tab 改为品牌入口资源，底板走 CSS，品牌 logo 组合走切图"],
                },
                {
                    "task_id": "task_chat_entry_icon",
                    "resource_key": "chat_entry_icon",
                    "component_scope": "floating_chat_entry",
                    "execution_group": "worker_shortcuts_and_nav",
                    "priority": 1,
                    "must_export": True,
                    "shared": True,
                    "status": "completed",
                    "notes": ["聊天入口和聊天面板共享图标"],
                },
                {
                    "task_id": "task_floating_chat_button_base",
                    "resource_key": "floating_chat_button_base",
                    "component_scope": "floating_chat_entry",
                    "execution_group": "worker_shortcuts_and_nav",
                    "priority": 1,
                    "must_export": True,
                    "shared": False,
                    "status": "completed",
                    "notes": ["聊天入口主体资源，不含未读气泡和数字"],
                },
                {
                    "task_id": "task_floating_chat_unread_badge",
                    "resource_key": "floating_chat_unread_badge",
                    "component_scope": "floating_chat_entry",
                    "execution_group": "worker_shortcuts_and_nav",
                    "priority": 2,
                    "must_export": False,
                    "shared": True,
                    "status": "completed",
                    "notes": ["默认建议 CSS 实现，这里保留一份资源对照"],
                },
                {
                    "task_id": "task_chat_panel_css_first",
                    "resource_key": "chat_panel",
                    "component_scope": "chat_panel",
                    "execution_group": "worker_overlay_states",
                    "priority": 1,
                    "must_export": False,
                    "shared": False,
                    "status": "planned",
                    "notes": ["聊天面板整体不再默认切图，优先走 CSS + 文本 + 共享图标"],
                },
                {
                    "task_id": "task_bottom_nav_component_split",
                    "resource_key": "bottom_nav",
                    "component_scope": "bottom_nav_item",
                    "execution_group": "worker_shortcuts_and_nav",
                    "priority": 1,
                    "must_export": True,
                    "shared": True,
                    "status": "completed",
                    "notes": ["底部导航按 icon + label_text + active_bg 拆解，badge 改为 CSS + 文本优先，不再保留栏目项整图"],
                },
                {
                    "task_id": "task_game_card_component_split",
                    "resource_key": "game_card",
                    "component_scope": "game_card",
                    "execution_group": "worker_card_decorations",
                    "priority": 1,
                    "must_export": True,
                    "shared": True,
                    "status": "completed",
                    "notes": ["卡片按共享底板、实例主视觉、共享收藏图标、共享角标拆解"],
                },
            ],
        },
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    input_dir = repo_root / "input" / "real-psd"
    output_dir = repo_root / "output" / "v2-trial-lobby" / "resources" / "png"
    analysis_dir = repo_root / "output" / "v2-trial-lobby" / "analysis"
    strategy_dir = repo_root / "output" / "v2-trial-lobby" / "strategies"
    plan_dir = repo_root / "output" / "v2-trial-lobby" / "plans"
    strategy_profile = "frontend_web"

    psd_path = next(path for path in input_dir.iterdir() if path.suffix.lower() == ".psd")
    psd = PSDImage.open(psd_path)
    exporter = AssetExporter(str(output_dir))
    source_path = str(psd_path)
    specs = _build_specs(psd, exporter, source_path)

    output_dir.mkdir(parents=True, exist_ok=True)
    analysis_dir.mkdir(parents=True, exist_ok=True)
    strategy_dir.mkdir(parents=True, exist_ok=True)
    plan_dir.mkdir(parents=True, exist_ok=True)
    for file in output_dir.glob("*"):
        if file.is_file():
            file.unlink()
    for folder in (analysis_dir, strategy_dir, plan_dir):
        for file in folder.glob("*"):
            if file.is_file():
                file.unlink()

    resources: List[Dict[str, Any]] = []
    source_ref_path = str(psd_path).replace("\\", "/")
    for spec in specs:
        image, source_refs = _render_resource(spec, exporter)
        resources.append(_save_resource(output_dir, spec, image, source_refs, source_ref_path))

    index_payload = {
        "schema_version": "2.0",
        "package_status": "trial_exported",
        "resources": resources,
    }
    (output_dir / "index.json").write_text(
        json.dumps(index_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _write_component_analysis(analysis_dir)
    _write_strategy_decision(strategy_dir, strategy_profile)
    _write_resource_task_list(plan_dir, strategy_profile)
    print(f"Exported {len(resources)} resources to {output_dir}")


if __name__ == "__main__":
    main()
