"""Runtime pipeline orchestration for PSD Smart Cut."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
import re
import shutil
from typing import Any, Dict, List, Optional, Tuple

from skills.psd_parser.level1_parse import parse_psd
from skills.psd_parser.level2_classify import LayerClassifier
from skills.psd_parser.level3_recognize import Recognizer
from skills.psd_parser.level4_strategy import Strategy
from skills.psd_parser.level5_export import CutPlan as ExportCutPlan
from skills.psd_parser.level5_export import ExportReport, Exporter

try:
    from psd_tools import PSDImage
except ImportError:  # pragma: no cover - exercised only in constrained envs
    PSDImage = None


@dataclass
class PipelineResult:
    psd_path: str
    output_dir: str
    total_layers: int
    strategy: str
    export_formats: List[str]
    classification_results: List[Dict[str, Any]] = field(default_factory=list)
    recognition_results: List[Dict[str, Any]] = field(default_factory=list)
    export_reports: Dict[str, ExportReport] = field(default_factory=dict)
    manifest_paths: Dict[str, str] = field(default_factory=dict)
    analysis_paths: Dict[str, str] = field(default_factory=dict)

    @property
    def export_report(self) -> Optional[ExportReport]:
        if not self.export_reports:
            return None
        return next(iter(self.export_reports.values()))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "psd_path": self.psd_path,
            "output_dir": self.output_dir,
            "total_layers": self.total_layers,
            "strategy": self.strategy,
            "export_formats": self.export_formats,
            "classification_results": self.classification_results,
            "recognition_results": self.recognition_results,
            "manifest_paths": self.manifest_paths,
            "analysis_paths": self.analysis_paths,
            "export_reports": {
                fmt: report.to_dict() for fmt, report in self.export_reports.items()
            },
        }


_GENERIC_NAME_PATTERNS = [
    re.compile(r"^layer\s*\d+$", re.IGNORECASE),
    re.compile(r"^图层\s*\d+$"),
    re.compile(r"^矩形\s*.+$"),
    re.compile(r"^椭圆\s*.+$"),
    re.compile(r"^形状\s*.+$"),
    re.compile(r"^\d+$"),
    re.compile(r"^画板.*$"),
]

_NOISE_EXACT_NAMES = {
    "bg",
    "top",
    "tt",
    "分割",
    "文本区域",
}

_BUTTON_HINTS = ("btn", "button", "按钮")
_TAB_HINTS = ("tab",)
_BANNER_HINTS = ("banner",)
_PANEL_HINTS = ("popup", "dialog", "modal", "弹窗", "面板")
_TEXT_ROLE_NAMES = {
    "ios",
    "android",
    "on",
    "off",
    "开",
    "開",
    "關",
    "关",
}


def _flatten_layers(document) -> List[Dict[str, Any]]:
    layers: List[Dict[str, Any]] = []
    for page in document.pages:
        for layer in page.layers:
            layer_dict = layer.to_dict() if hasattr(layer, "to_dict") else dict(layer)
            layer_dict.setdefault("page", page.name)
            layers.append(layer_dict)
    return layers


def _is_renderable_layer(layer: Dict[str, Any]) -> bool:
    width = layer.get("width", 0)
    height = layer.get("height", 0)
    return bool(width and height and width > 0 and height > 0)


def _is_group_layer(layer: Dict[str, Any]) -> bool:
    return layer.get("kind") == "group" or bool(layer.get("children"))


def _normalize_text(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n").strip()


def _is_semantic_name(name: str) -> bool:
    if not name:
        return False
    normalized = name.strip()
    if not normalized:
        return False
    if normalized.lower() in _NOISE_EXACT_NAMES:
        return False
    for pattern in _GENERIC_NAME_PATTERNS:
        if pattern.match(normalized):
            return False
    return True


def _contains_hint(name: str, hints: Tuple[str, ...]) -> bool:
    lowered = name.lower()
    return any(hint in lowered for hint in hints)


def _slug_text(value: str) -> str:
    text = value.replace("\n", " ").strip()
    text = re.sub(r"\s+", "_", text)
    return text.strip("_")


def _build_psd_layer_records(psd_path: str) -> Dict[str, Dict[str, Any]]:
    if PSDImage is None:
        return {}

    psd = PSDImage.open(psd_path)
    records: Dict[str, Dict[str, Any]] = {}
    counter = 0

    def walk(layer: Any, parent_id: Optional[str] = None) -> None:
        nonlocal counter
        layer_id = f"layer_{counter}"
        counter += 1
        bbox = getattr(layer, "bbox", None)
        if bbox:
            bbox_tuple = (int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3]))
        else:
            bbox_tuple = None
        text_value = getattr(layer, "text", None)
        if isinstance(text_value, str):
            text_value = _normalize_text(text_value)

        records[layer_id] = {
            "id": layer_id,
            "parent_id": parent_id,
            "children": [],
            "name": getattr(layer, "name", "") or "",
            "kind": getattr(layer, "kind", "unknown") or "unknown",
            "visible": bool(getattr(layer, "visible", True)),
            "text": text_value,
            "bbox": bbox_tuple,
            "width": max(0, bbox_tuple[2] - bbox_tuple[0]) if bbox_tuple else 0,
            "height": max(0, bbox_tuple[3] - bbox_tuple[1]) if bbox_tuple else 0,
        }

        if parent_id and parent_id in records:
            records[parent_id]["children"].append(layer_id)

        if layer.is_group():
            for child in layer:
                walk(child, layer_id)

    for root in psd:
        walk(root)
    return records


def _build_depths(layers_by_id: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
    depths: Dict[str, int] = {}

    def compute(layer_id: str) -> int:
        if layer_id in depths:
            return depths[layer_id]
        parent_id = layers_by_id.get(layer_id, {}).get("parent_id")
        depth = 0 if not parent_id else compute(parent_id) + 1
        depths[layer_id] = depth
        return depth

    for layer_id in layers_by_id:
        compute(layer_id)
    return depths


def _is_text_record(record: Dict[str, Any]) -> bool:
    return record.get("kind") == "type" or bool(record.get("text"))


def _record_area(record: Dict[str, Any]) -> int:
    return int(record.get("width", 0)) * int(record.get("height", 0))


def _classify_child_role(record: Dict[str, Any], container_area: int) -> str:
    if _is_text_record(record):
        return "text"

    kind = (record.get("kind") or "").lower()
    area_ratio = _record_area(record) / max(container_area, 1)

    if kind in {"shape", "solidcolorfill"}:
        return "background" if area_ratio >= 0.45 else "decoration"
    if kind in {"pixel", "smartobject"}:
        return "icon" if area_ratio <= 0.35 else "artwork"
    if kind == "group":
        return "nested_component"
    return "artwork" if area_ratio >= 0.5 else "decoration"


def _summarize_text_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    summary: List[Dict[str, Any]] = []
    for record in records:
        text_value = _normalize_text(record.get("text") or record.get("name") or "")
        if not text_value:
            continue
        summary.append(
            {
                "layer_id": record["id"],
                "name": record.get("name", ""),
                "text": text_value,
                "bbox": list(record["bbox"]) if record.get("bbox") else None,
            }
        )
    return summary


def _union_bbox(boxes: List[Tuple[int, int, int, int]]) -> Optional[Tuple[int, int, int, int]]:
    if not boxes:
        return None
    return (
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    )


def _component_bbox(
    export_layer_ids: List[str],
    record: Dict[str, Any],
    psd_records: Dict[str, Dict[str, Any]],
) -> Tuple[int, int, int, int]:
    boxes = [
        psd_records[layer_id]["bbox"]
        for layer_id in export_layer_ids
        if layer_id in psd_records and psd_records[layer_id].get("bbox")
    ]
    merged = _union_bbox(boxes)
    if merged:
        return merged
    if record.get("bbox"):
        return record["bbox"]
    return (0, 0, 0, 0)


def _bbox_area(bbox: Optional[Tuple[int, int, int, int]]) -> int:
    if not bbox:
        return 0
    return max(0, int(bbox[2]) - int(bbox[0])) * max(0, int(bbox[3]) - int(bbox[1]))


def _bbox_intersection(
    first: Optional[Tuple[int, int, int, int]],
    second: Optional[Tuple[int, int, int, int]],
) -> Optional[Tuple[int, int, int, int]]:
    if not first or not second:
        return None
    left = max(first[0], second[0])
    top = max(first[1], second[1])
    right = min(first[2], second[2])
    bottom = min(first[3], second[3])
    if right <= left or bottom <= top:
        return None
    return (left, top, right, bottom)


def _bbox_overlap_ratio(
    inner: Optional[Tuple[int, int, int, int]],
    outer: Optional[Tuple[int, int, int, int]],
) -> float:
    if not inner or not outer:
        return 0.0
    intersection = _bbox_intersection(inner, outer)
    if not intersection:
        return 0.0
    return _bbox_area(intersection) / max(_bbox_area(inner), 1)


def _guess_group_component_type(
    layer: Dict[str, Any],
    record: Dict[str, Any],
    child_records: List[Dict[str, Any]],
) -> Optional[str]:
    name = record.get("name") or layer.get("name") or ""
    lowered = name.lower()
    text_children = [child for child in child_records if _is_text_record(child)]
    visual_children = [child for child in child_records if not _is_text_record(child)]
    group_children = [child for child in child_records if child.get("kind") == "group"]

    if _contains_hint(name, _TAB_HINTS) and len(text_children) >= 2 and visual_children:
        return "tab_control"
    if _contains_hint(name, _BANNER_HINTS):
        return "banner"
    if _contains_hint(name, _PANEL_HINTS) and len(child_records) <= 8 and len(group_children) <= 1:
        return "panel"
    if _contains_hint(name, _BUTTON_HINTS) and visual_children and len(group_children) <= 1:
        return "button"
    if len(group_children) == 1 and len(text_children) >= 1:
        switch_group = group_children[0]
        switch_name = (switch_group.get("name") or "").lower()
        if switch_name.startswith("btn"):
            return "toggle_row"
    if (
        len(text_children) >= 1
        and visual_children
        and len(child_records) <= 6
        and len(group_children) <= 1
        and _is_semantic_name(name)
    ):
        return "component"
    if _is_semantic_name(name) and visual_children and len(child_records) <= 5 and len(group_children) <= 1:
        return "artwork_group"
    return None


def _build_group_component(
    layer: Dict[str, Any],
    psd_records: Dict[str, Dict[str, Any]],
    layers_by_id: Dict[str, Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    layer_id = layer.get("id")
    if not layer_id or layer_id not in psd_records:
        return None

    record = psd_records[layer_id]
    child_records = [
        psd_records[child_id]
        for child_id in record.get("children", [])
        if child_id in psd_records and psd_records[child_id].get("visible", True)
    ]
    if not child_records:
        return None

    component_type = _guess_group_component_type(layer, record, child_records)
    if component_type is None:
        return None

    container_area = max(_record_area(record), 1)
    roles: Dict[str, List[str]] = {
        "background": [],
        "text": [],
        "icon": [],
        "artwork": [],
        "decoration": [],
        "nested_component": [],
    }
    text_records: List[Dict[str, Any]] = []

    for child_record in child_records:
        role = _classify_child_role(child_record, container_area)
        roles.setdefault(role, []).append(child_record["id"])
        if role == "text":
            text_records.append(child_record)

    export_layer_ids: List[str] = []
    if component_type == "toggle_row":
        export_layer_ids.extend(roles.get("nested_component", []))
    else:
        for role in ("background", "icon", "artwork", "decoration", "nested_component"):
            export_layer_ids.extend(roles.get(role, []))

    export_layer_ids = [child_id for child_id in export_layer_ids if child_id in psd_records]
    if not export_layer_ids:
        export_layer_ids = [layer_id]

    export_bbox = _component_bbox(export_layer_ids, record, psd_records)
    component_bbox = _union_bbox(
        [bbox for bbox in [record.get("bbox"), export_bbox] if bbox]
    ) or export_bbox
    text_entries = _summarize_text_records(text_records)

    component_name = layer.get("name") or layer_id
    if component_type == "button" and text_entries:
        label = _slug_text(text_entries[0]["text"])
        if label:
            component_name = f"button_{label}"
    if component_type == "toggle_row" and text_entries:
        preferred_entry = next(
            (
                entry
                for entry in text_entries
                if entry["text"].replace("\n", " ").strip().lower() not in _TEXT_ROLE_NAMES
            ),
            text_entries[0],
        )
        label = preferred_entry["text"].replace("\n", " ").strip()
        if label:
            component_name = f"toggle_{label}"

    frontend_hints = {
        "prefer_text_rendering": bool(text_entries),
        "component_family": component_type,
    }
    export_decision = {
        "image_layers": export_layer_ids,
        "text_layers": roles.get("text", []),
        "mode": "hybrid" if text_entries else "image_only",
    }

    if component_type == "toggle_row":
        label_entry = next(
            (
                entry
                for entry in text_entries
                if entry["text"].replace("\n", " ").strip().lower() not in _TEXT_ROLE_NAMES
            ),
            None,
        )
        state_entry = next(
            (
                entry
                for entry in text_entries
                if entry["text"].replace("\n", " ").strip().lower() in _TEXT_ROLE_NAMES
            ),
            None,
        )
        frontend_hints["prefer_text_rendering"] = True
        frontend_hints["component_family"] = "toggle_row"
        frontend_hints["contains_switch_control"] = True
        export_decision["component_bbox"] = list(component_bbox)
        export_decision["switch_bbox"] = list(export_bbox)
        export_decision["asset_role"] = "switch_control"
    else:
        export_decision["component_bbox"] = list(component_bbox)

    return {
        "id": layer_id,
        "name": component_name,
        "type": component_type,
        "page": layer.get("page"),
        "position": (component_bbox[0], component_bbox[1]),
        "width": max(0, component_bbox[2] - component_bbox[0]),
        "height": max(0, component_bbox[3] - component_bbox[1]),
        "layer_ids": [layer_id, *record.get("children", [])],
        "source_file": layer.get("source_file", ""),
        "render_bbox": component_bbox,
        "layer_data": {
            "source_file": layer.get("source_file", ""),
            "layer_ids": export_layer_ids,
            "bbox": export_bbox,
            "render_bbox": export_bbox,
            "component_name": component_name,
        },
        "custom_fields": {
            "component_id": layer_id,
            "component_source": "group",
            "component_type": component_type,
            "text_as_metadata": bool(text_entries),
            "text_entries": text_entries,
            "layer_roles": roles,
            "export_layer_ids": export_layer_ids,
            "export_decision": export_decision,
            "frontend_hints": frontend_hints,
            "subcomponents": {
                "switch_control": {
                    "layer_ids": roles.get("nested_component", []),
                    "bbox": list(export_bbox),
                }
            }
            if component_type == "toggle_row"
            else {},
            "label_entry": label_entry if component_type == "toggle_row" else None,
            "state_entry": state_entry if component_type == "toggle_row" else None,
        },
    }


def _build_leaf_component(
    layer: Dict[str, Any],
    psd_records: Dict[str, Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    layer_id = layer.get("id")
    if not layer_id or not _is_semantic_name(layer.get("name", "")):
        return None
    if not _is_renderable_layer(layer) or _is_group_layer(layer):
        return None

    record = psd_records.get(layer_id, {})
    if _is_text_record(record):
        return None

    name = layer.get("name", "")
    component_type = "banner" if _contains_hint(name, _BANNER_HINTS) else "artwork"
    bbox = (
        layer.get("left", 0),
        layer.get("top", 0),
        layer.get("right", layer.get("left", 0) + layer.get("width", 0)),
        layer.get("bottom", layer.get("top", 0) + layer.get("height", 0)),
    )
    return {
        "id": layer_id,
        "name": name or layer_id,
        "type": component_type,
        "page": layer.get("page"),
        "position": (bbox[0], bbox[1]),
        "width": max(0, bbox[2] - bbox[0]),
        "height": max(0, bbox[3] - bbox[1]),
        "layer_ids": [layer_id],
        "source_file": layer.get("source_file", ""),
        "render_bbox": bbox,
        "layer_data": {
            "source_file": layer.get("source_file", ""),
            "layer_ids": [layer_id],
            "bbox": bbox,
            "component_name": name or layer_id,
        },
        "custom_fields": {
            "component_id": layer_id,
            "component_source": "leaf",
            "component_type": component_type,
            "text_as_metadata": False,
            "text_entries": [],
            "layer_roles": {"artwork": [layer_id]},
            "export_layer_ids": [layer_id],
            "export_decision": {
                "image_layers": [layer_id],
                "text_layers": [],
                "mode": "image_only",
            },
            "frontend_hints": {
                "prefer_text_rendering": False,
                "component_family": component_type,
            },
        },
    }


def _component_export_layers(component: Dict[str, Any]) -> List[str]:
    custom_fields = component.get("custom_fields", {})
    export_layer_ids = custom_fields.get("export_layer_ids")
    if isinstance(export_layer_ids, list) and export_layer_ids:
        return export_layer_ids
    layer_data = component.get("layer_data", {})
    layer_ids = layer_data.get("layer_ids")
    if isinstance(layer_ids, list):
        return layer_ids
    return []


def _build_region_background_component(
    region_id: str,
    region_record: Dict[str, Any],
    psd_records: Dict[str, Dict[str, Any]],
    used_layer_ids: set[str],
    source_file: str,
    page_name: str,
    region_purpose: str,
) -> Optional[Dict[str, Any]]:
    region_bbox = region_record.get("bbox")
    region_area = _bbox_area(region_bbox)
    if not region_bbox or region_area <= 0:
        return None

    background_ids: List[str] = []
    for child_id in region_record.get("children", []):
        record = psd_records.get(child_id)
        if not record or not record.get("visible", True) or _is_text_record(record):
            continue
        bbox = record.get("bbox")
        if not bbox:
            continue
        overlap_ratio = _bbox_overlap_ratio(bbox, region_bbox)
        area_ratio = _bbox_area(bbox) / max(region_area, 1)
        normalized_name = (record.get("name") or "").strip().lower()
        if overlap_ratio < 0.85:
            continue
        if normalized_name == "图层 0":
            continue
        if area_ratio < 0.45 and normalized_name not in {"bg", "top"}:
            continue
        if child_id in used_layer_ids:
            continue
        background_ids.append(child_id)

    if not background_ids:
        return None

    component_name = f"{region_purpose}_background"
    return {
        "id": f"{region_id}__background",
        "region_id": region_id,
        "name": component_name,
        "type": "region_background",
        "page": page_name,
        "position": (region_bbox[0], region_bbox[1]),
        "width": max(0, region_bbox[2] - region_bbox[0]),
        "height": max(0, region_bbox[3] - region_bbox[1]),
        "layer_ids": background_ids,
        "source_file": source_file,
        "render_bbox": region_bbox,
        "layer_data": {
            "source_file": source_file,
            "layer_ids": background_ids,
            "bbox": region_bbox,
            "component_name": component_name,
        },
        "custom_fields": {
            "component_id": f"{region_id}__background",
            "component_source": "synthetic_region",
            "component_type": "region_background",
            "text_as_metadata": False,
            "text_entries": [],
            "layer_roles": {"background": background_ids},
            "export_layer_ids": background_ids,
            "export_decision": {
                "image_layers": background_ids,
                "text_layers": [],
                "mode": "image_only",
            },
            "frontend_hints": {
                "prefer_text_rendering": False,
                "component_family": "region_background",
            },
        },
    }


def _build_large_block_components(
    region_id: str,
    region_record: Dict[str, Any],
    psd_records: Dict[str, Dict[str, Any]],
    used_layer_ids: set[str],
    source_file: str,
    page_name: str,
    region_purpose: str,
) -> List[Dict[str, Any]]:
    region_bbox = region_record.get("bbox")
    region_area = _bbox_area(region_bbox)
    if not region_bbox or region_area <= 0:
        return []
    region_height = max(1, region_bbox[3] - region_bbox[1])

    components: List[Dict[str, Any]] = []
    index = 0
    for child_id in region_record.get("children", []):
        record = psd_records.get(child_id)
        if not record or not record.get("visible", True) or _is_text_record(record):
            continue
        if record.get("kind") not in {"shape", "pixel", "smartobject"}:
            continue
        if child_id in used_layer_ids:
            continue
        bbox = record.get("bbox")
        if not bbox:
            continue

        overlap_ratio = _bbox_overlap_ratio(bbox, region_bbox)
        area_ratio = _bbox_area(bbox) / max(region_area, 1)
        width = max(0, bbox[2] - bbox[0])
        height = max(0, bbox[3] - bbox[1])
        if overlap_ratio < 0.55 or area_ratio < 0.12:
            continue
        if width < 180 or height < 120:
            continue
        if height <= 8 or width <= 8:
            continue
        if bbox[1] <= region_bbox[1] + int(region_height * 0.2) and height < 260:
            continue

        index += 1
        component_name = f"{region_purpose}_block_{index}"
        components.append(
            {
                "id": f"{region_id}__block_{index}",
                "region_id": region_id,
                "name": component_name,
                "type": "content_block",
                "page": page_name,
                "position": (bbox[0], bbox[1]),
                "width": width,
                "height": height,
                "layer_ids": [child_id],
                "source_file": source_file,
                "render_bbox": bbox,
                "layer_data": {
                    "source_file": source_file,
                    "layer_ids": [child_id],
                    "bbox": bbox,
                    "component_name": component_name,
                },
                "custom_fields": {
                    "component_id": f"{region_id}__block_{index}",
                    "component_source": "synthetic_region",
                    "component_type": "content_block",
                    "text_as_metadata": False,
                    "text_entries": [],
                    "layer_roles": {"background": [child_id]},
                    "export_layer_ids": [child_id],
                    "export_decision": {
                        "image_layers": [child_id],
                        "text_layers": [],
                        "mode": "image_only",
                    },
                    "frontend_hints": {
                        "prefer_text_rendering": False,
                        "component_family": "content_block",
                    },
                },
            }
        )
    return components


def _has_selected_ancestor(layer_id: str, selected_ids: set[str], layers_by_id: Dict[str, Dict[str, Any]]) -> bool:
    current = layers_by_id.get(layer_id, {}).get("parent_id")
    while current:
        if current in selected_ids:
            return True
        current = layers_by_id.get(current, {}).get("parent_id")
    return False


def _build_component_candidates(
    layers: List[Dict[str, Any]],
    psd_records: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    layers_by_id = {layer["id"]: layer for layer in layers if layer.get("id")}
    depths = _build_depths(layers_by_id)

    selected_group_ids: set[str] = set()
    components: List[Dict[str, Any]] = []

    group_layers = [
        layer
        for layer in layers
        if layer.get("id") in psd_records and _is_group_layer(layer) and _is_renderable_layer(layer)
    ]
    group_layers.sort(
        key=lambda item: (
            depths.get(item["id"], 0),
            item.get("top", 0),
            item.get("left", 0),
        )
    )

    for layer in group_layers:
        layer_id = layer["id"]
        if _has_selected_ancestor(layer_id, selected_group_ids, layers_by_id):
            continue
        component = _build_group_component(layer, psd_records, layers_by_id)
        if component is None:
            continue
        components.append(component)
        selected_group_ids.add(layer_id)

    for layer in layers:
        layer_id = layer.get("id")
        if not layer_id or _has_selected_ancestor(layer_id, selected_group_ids, layers_by_id):
            continue
        component = _build_leaf_component(layer, psd_records)
        if component is None:
            continue
        components.append(component)

    used_layer_ids: set[str] = set()
    for component in components:
        used_layer_ids.update(component.get("layer_ids", []))
        used_layer_ids.update(_component_export_layers(component))

    root_region_ids = [layer_id for layer_id, record in psd_records.items() if not record.get("parent_id")]
    for region_id in root_region_ids:
        region_record = psd_records.get(region_id)
        layer_context = layers_by_id.get(region_id, {})
        page_name = layer_context.get("page", "Root")
        source_file = layer_context.get("source_file", "")
        region_name = (region_record or {}).get("name", "").lower()
        region_purpose = "region"
        if "10" in region_name:
            region_purpose = "ios_install_guide"
        elif "11" in region_name:
            region_purpose = "android_install_guide"
        elif "9" in region_name:
            region_purpose = "settings_panel"

        if region_record:
            background_component = _build_region_background_component(
                region_id=region_id,
                region_record=region_record,
                psd_records=psd_records,
                used_layer_ids=used_layer_ids,
                source_file=source_file,
                page_name=page_name,
                region_purpose=region_purpose,
            )
            if background_component:
                components.append(background_component)
                used_layer_ids.update(background_component.get("layer_ids", []))
                used_layer_ids.update(_component_export_layers(background_component))

            block_components = _build_large_block_components(
                region_id=region_id,
                region_record=region_record,
                psd_records=psd_records,
                used_layer_ids=used_layer_ids,
                source_file=source_file,
                page_name=page_name,
                region_purpose=region_purpose,
            )
            for component in block_components:
                components.append(component)
                used_layer_ids.update(component.get("layer_ids", []))
                used_layer_ids.update(_component_export_layers(component))

    if components:
        return components

    fallback_components: List[Dict[str, Any]] = []
    for layer in layers:
        if not _is_renderable_layer(layer):
            continue
        fallback_components.append(
            {
                "id": layer.get("id"),
                "name": layer.get("name") or layer.get("id"),
                "type": layer.get("type", layer.get("kind", "unknown")),
                "page": layer.get("page"),
                "position": (layer.get("left", 0), layer.get("top", 0)),
                "width": layer.get("width", 0),
                "height": layer.get("height", 0),
                "layer_ids": [layer.get("id")] if layer.get("id") else [],
                "source_file": layer.get("source_file", ""),
                "render_bbox": (
                    layer.get("left", 0),
                    layer.get("top", 0),
                    layer.get("right", layer.get("left", 0) + layer.get("width", 0)),
                    layer.get("bottom", layer.get("top", 0) + layer.get("height", 0)),
                ),
                "layer_data": {
                    "source_file": layer.get("source_file", ""),
                    "layer_ids": [layer.get("id")] if layer.get("id") else [],
                    "bbox": (
                        layer.get("left", 0),
                        layer.get("top", 0),
                        layer.get("right", layer.get("left", 0) + layer.get("width", 0)),
                        layer.get("bottom", layer.get("top", 0) + layer.get("height", 0)),
                    ),
                    "component_name": layer.get("name") or layer.get("id"),
                },
                "custom_fields": {
                    "component_source": "fallback",
                    "text_entries": [],
                    "layer_roles": {"artwork": [layer.get("id")] if layer.get("id") else []},
                    "export_decision": {"mode": "image_only"},
                    "frontend_hints": {
                        "prefer_text_rendering": False,
                        "component_family": layer.get("type", layer.get("kind", "unknown")),
                    },
                },
            }
        )
    return fallback_components


def _normalize_matching_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def _relative_output_path(output_root: Path, path: Path) -> str:
    try:
        return path.relative_to(output_root).as_posix()
    except ValueError:
        return path.as_posix()


def _collect_descendant_ids(root_id: str, psd_records: Dict[str, Dict[str, Any]]) -> List[str]:
    collected: List[str] = []
    stack = [root_id]
    while stack:
        current = stack.pop()
        collected.append(current)
        children = list(psd_records.get(current, {}).get("children", []))
        stack.extend(reversed(children))
    return collected


def _collect_text_entries(layer_ids: List[str], psd_records: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    for layer_id in layer_ids:
        record = psd_records.get(layer_id)
        if not record or not record.get("visible", True) or not _is_text_record(record):
            continue
        text_value = _normalize_text(record.get("text") or record.get("name") or "")
        if not text_value:
            continue
        entries.append(
            {
                "layer_id": layer_id,
                "name": record.get("name", ""),
                "text": text_value,
                "bbox": list(record["bbox"]) if record.get("bbox") else None,
            }
        )
    return entries


def _find_top_ancestor(layer_id: str, psd_records: Dict[str, Dict[str, Any]]) -> str:
    current = layer_id
    parent_id = psd_records.get(current, {}).get("parent_id")
    while parent_id:
        current = parent_id
        parent_id = psd_records.get(current, {}).get("parent_id")
    return current


def _summarize_backgrounds(
    root_id: str,
    psd_records: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    root_record = psd_records.get(root_id, {})
    root_area = max(_record_area(root_record), 1)
    backgrounds: List[Dict[str, Any]] = []

    for layer_id in _collect_descendant_ids(root_id, psd_records)[1:]:
        record = psd_records.get(layer_id, {})
        if not record.get("visible", True):
            continue
        name = record.get("name", "")
        area_ratio = _record_area(record) / root_area
        if record.get("kind") in {"shape", "pixel", "solidcolorfill"} and (
            name.strip().lower() in {"bg", "top"} or area_ratio >= 0.35
        ):
            backgrounds.append(
                {
                    "layer_id": layer_id,
                    "name": name,
                    "kind": record.get("kind", "unknown"),
                    "bbox": list(record["bbox"]) if record.get("bbox") else None,
                }
            )
    return backgrounds[:6]


def _derive_region_purpose(
    root_record: Dict[str, Any],
    text_entries: List[Dict[str, Any]],
    components: List[Dict[str, Any]],
) -> Tuple[str, str]:
    joined_text = " ".join(entry["text"] for entry in text_entries)
    normalized_text = _normalize_matching_text(joined_text)
    component_types = {component.get("type", "unknown") for component in components}
    component_names = " ".join(component.get("name", "") for component in components).lower()
    name_text = _normalize_matching_text(root_record.get("name", ""))

    if (
        "toggle_row" in component_types
        or "button" in component_types
        or "\u8a2d\u5b9a" in normalized_text
        or "\u8bbe\u7f6e" in normalized_text
        or "\u6309\u94ae" in name_text
    ):
        return (
            "settings_panel",
            "Primary settings area with action buttons and toggle controls.",
        )
    if "tab_control" in component_types:
        if "chrome" in normalized_text:
            return (
                "android_install_guide",
                "Instructional region for adding the web page to the Android home screen.",
            )
        if "safari" in normalized_text:
            return (
                "ios_install_guide",
                "Instructional region for adding the web page to the iOS home screen.",
            )
        if "android" in normalized_text and "ios" not in normalized_text:
            return (
                "android_install_guide",
                "Instructional region for adding the web page to the Android home screen.",
            )
        if "ios" in normalized_text:
            return (
                "ios_install_guide",
                "Instructional region for adding the web page to the iOS home screen.",
            )
        return (
            "tutorial_panel",
            "Instructional region with tab-based guide content.",
        )
    if "banner" in component_types or "banner" in component_names:
        return (
            "promotional_banner",
            "Promotional artwork region intended to stay as a single image asset.",
        )
    return (
        "content_region",
        "General content region that still needs manual strategy refinement.",
    )


def _build_region_summary(
    root_id: str,
    psd_records: Dict[str, Dict[str, Any]],
    components: List[Dict[str, Any]],
) -> Dict[str, Any]:
    root_record = psd_records[root_id]
    descendant_ids = _collect_descendant_ids(root_id, psd_records)
    text_entries = _collect_text_entries(descendant_ids, psd_records)
    purpose, description = _derive_region_purpose(root_record, text_entries, components)

    bbox = root_record.get("bbox") or (0, 0, 0, 0)
    return {
        "region_id": root_id,
        "source_name": root_record.get("name", root_id),
        "purpose": purpose,
        "description": description,
        "bounds": list(bbox),
        "background_layers": _summarize_backgrounds(root_id, psd_records),
        "key_texts": text_entries[:8],
        "components": components,
    }


def _derive_region_display_name(region: Dict[str, Any], index: int) -> str:
    purpose = region["purpose"]
    key_texts = region.get("key_texts", [])
    first_text = key_texts[0]["text"].replace("\n", " / ") if key_texts else ""

    labels = {
        "settings_panel": "Settings Panel",
        "ios_install_guide": "iOS Install Guide",
        "android_install_guide": "Android Install Guide",
        "tutorial_panel": "Tutorial Panel",
        "promotional_banner": "Promotional Banner",
        "content_region": f"Content Region {index + 1}",
    }
    if purpose in labels:
        return labels[purpose]
    if first_text:
        return first_text
    return f"Region {index + 1}"


def _build_page_summary(regions: List[Dict[str, Any]], document, psd_path: str) -> Dict[str, Any]:
    component_counts: Dict[str, int] = {}
    for region in regions:
        for component in region["components"]:
            comp_type = component.get("type", "unknown")
            component_counts[comp_type] = component_counts.get(comp_type, 0) + 1

    region_purposes = {region["purpose"] for region in regions}
    if {"settings_panel", "ios_install_guide", "android_install_guide"} <= region_purposes:
        page_type = "settings_with_install_guides"
        summary = (
            "Detected a settings-focused page that combines a main settings panel "
            "with separate iOS and Android add-to-home-screen guide regions."
        )
    elif "settings_panel" in region_purposes:
        page_type = "settings_page"
        summary = "Detected a settings-oriented page with interactive controls and action buttons."
    else:
        page_type = "component_canvas"
        summary = "Detected a component-oriented design canvas that still needs page-level interpretation."

    ordered_regions = sorted(regions, key=lambda region: (region["bounds"][0], region["bounds"][1]))
    reading_order = [region["display_name"] for region in ordered_regions]
    if len(ordered_regions) >= 3:
        layout_pattern = "horizontal_triptych"
        visual_summary = (
            "The preview reads as a left-to-right strip of three mobile screens: "
            "settings panel, iOS guide, and Android guide."
        )
    elif len(ordered_regions) == 2:
        layout_pattern = "two_panel_layout"
        visual_summary = "The preview reads as a two-panel layout with one primary panel and one supporting panel."
    else:
        layout_pattern = "single_panel"
        visual_summary = "The preview reads as a single primary panel."

    return {
        "page_type": page_type,
        "summary": summary,
        "source_file": psd_path,
        "canvas": {
            "width": document.width,
            "height": document.height,
            "page_count": len(document.pages),
            "total_layers": document.total_layers,
        },
        "component_counts": component_counts,
        "region_count": len(regions),
        "layout_pattern": layout_pattern,
        "reading_order": reading_order,
        "visual_summary": visual_summary,
    }


def _format_bounds(bounds: List[int]) -> str:
    if len(bounds) != 4:
        return "0,0,0,0"
    left, top, right, bottom = bounds
    return f"{left},{top},{right},{bottom}"


def _build_page_tree_markdown(page_summary: Dict[str, Any], regions: List[Dict[str, Any]]) -> str:
    lines = [
        "# Page Tree",
        "",
        f"Page Type: `{page_summary['page_type']}`",
        f"Visual Summary: {page_summary['visual_summary']}",
        f"Reading Order: {' -> '.join(page_summary['reading_order'])}",
        "",
        "```text",
        f"Page: {page_summary['page_type']}",
        f"Summary: {page_summary['summary']}",
    ]

    for index, region in enumerate(regions):
        is_last_region = index == len(regions) - 1
        region_prefix = "`-" if is_last_region else "|-"
        child_prefix = "   " if is_last_region else "| "
        lines.append(
            f"{region_prefix} Region: {region['display_name']} ({region['purpose']}) "
            f"@ {_format_bounds(region['bounds'])}"
        )
        lines.append(f"{child_prefix}Summary: {region['description']}")

        if region["background_layers"]:
            background_names = ", ".join(
                layer.get("name") or layer["layer_id"] for layer in region["background_layers"]
            )
            lines.append(f"{child_prefix}Backgrounds: {background_names}")

        if region["components"]:
            lines.append(f"{child_prefix}Components:")
            for comp_index, component in enumerate(region["components"]):
                comp_prefix = "`-" if comp_index == len(region["components"]) - 1 else "|-"
                lines.append(
                    f"{child_prefix}{comp_prefix} {component['type']}: {component['name']}"
                )

    lines.extend(["```", ""])
    return "\n".join(lines)


def _build_component_entry(component: Dict[str, Any]) -> Dict[str, Any]:
    custom_fields = component.get("custom_fields", {})
    return {
        "component_id": component.get("id"),
        "name": component.get("name"),
        "type": component.get("type"),
        "bounds": list(component.get("render_bbox", (0, 0, 0, 0))),
        "position": list(component.get("position", (0, 0))),
        "dimensions": [component.get("width", 0), component.get("height", 0)],
        "text_entries": custom_fields.get("text_entries", []),
        "layer_roles": custom_fields.get("layer_roles", {}),
        "export_decision": custom_fields.get("export_decision", {}),
        "frontend_hints": custom_fields.get("frontend_hints", {}),
        "subcomponents": custom_fields.get("subcomponents", {}),
        "label_entry": custom_fields.get("label_entry"),
        "state_entry": custom_fields.get("state_entry"),
    }


def _build_component_tree(regions: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "regions": [
            {
                "region_id": region["region_id"],
                "purpose": region["purpose"],
                "source_name": region["source_name"],
                "components": [_build_component_entry(component) for component in region["components"]],
            }
            for region in regions
        ]
    }


def _build_component_tree_markdown(regions: List[Dict[str, Any]]) -> str:
    lines = [
        "# Component Tree",
        "",
        "```text",
    ]

    for region_index, region in enumerate(regions):
        region_prefix = "`-" if region_index == len(regions) - 1 else "|-"
        child_prefix = "   " if region_index == len(regions) - 1 else "| "
        lines.append(f"{region_prefix} Region: {region['display_name']} ({region['purpose']})")
        for comp_index, component in enumerate(region["components"]):
            comp_prefix = "`-" if comp_index == len(region["components"]) - 1 else "|-"
            lines.append(f"{child_prefix}{comp_prefix} {component['type']}: {component['name']}")
            text_entries = component.get("custom_fields", {}).get("text_entries", [])
            export_decision = component.get("custom_fields", {}).get("export_decision", {})
            subcomponents = component.get("custom_fields", {}).get("subcomponents", {})
            text_label = ", ".join(entry["text"].replace("\n", " / ") for entry in text_entries) or "-"
            mode = export_decision.get("mode", "unknown")
            lines.append(f"{child_prefix}   Text: {text_label}")
            lines.append(f"{child_prefix}   ExportMode: {mode}")
            if subcomponents:
                lines.append(f"{child_prefix}   Subparts: {', '.join(subcomponents.keys())}")

    lines.extend(["```", ""])
    return "\n".join(lines)


def _build_page_analysis_markdown(page_summary: Dict[str, Any], regions: List[Dict[str, Any]]) -> str:
    lines = [
        "# Page Analysis",
        "",
        f"- Page type: `{page_summary['page_type']}`",
        f"- Visual summary: {page_summary['visual_summary']}",
        f"- Reading order: {' -> '.join(page_summary['reading_order'])}",
        f"- Canvas: {page_summary['canvas']['width']} x {page_summary['canvas']['height']}",
        "",
        "## Regions",
    ]

    for region in regions:
        lines.append(f"### {region['display_name']}")
        lines.append(f"- Purpose: `{region['purpose']}`")
        lines.append(f"- Bounds: `{_format_bounds(region['bounds'])}`")
        lines.append(f"- Summary: {region['description']}")
        if region["background_layers"]:
            bg_names = ", ".join(layer.get("name") or layer["layer_id"] for layer in region["background_layers"])
            lines.append(f"- Background candidates: {bg_names}")
        if region["key_texts"]:
            key_text = " | ".join(entry["text"].replace("\n", " / ") for entry in region["key_texts"][:4])
            lines.append(f"- Key texts: {key_text}")
        component_names = ", ".join(component["name"] for component in region["components"]) or "None"
        lines.append(f"- Components: {component_names}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def _render_page_preview(psd_path: str, preview_path: Path) -> Optional[Path]:
    if PSDImage is None:
        return None
    try:
        preview_path.parent.mkdir(parents=True, exist_ok=True)
        preview = PSDImage.open(psd_path).composite()
        preview.save(preview_path)
        return preview_path
    except Exception:
        return None


def _write_analysis_outputs(
    output_root: Path,
    document,
    psd_path: str,
    psd_records: Dict[str, Dict[str, Any]],
    components: List[Dict[str, Any]],
) -> Dict[str, str]:
    docs_dir = output_root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    components_by_region: Dict[str, List[Dict[str, Any]]] = {}
    for component in components:
        region_id = component.get("region_id")
        if not region_id:
            component_id = component.get("id")
            if not component_id:
                continue
            region_id = _find_top_ancestor(component_id, psd_records)
        components_by_region.setdefault(region_id, []).append(component)

    root_region_ids = [layer_id for layer_id, record in psd_records.items() if not record.get("parent_id")]
    regions = [
        _build_region_summary(root_id, psd_records, components_by_region.get(root_id, []))
        for root_id in root_region_ids
    ]
    regions = [region for region in regions if region["components"] or region["background_layers"] or region["key_texts"]]
    regions = sorted(regions, key=lambda region: (region["bounds"][0], region["bounds"][1]))
    for index, region in enumerate(regions):
        region["display_name"] = _derive_region_display_name(region, index)

    page_summary = _build_page_summary(regions, document, psd_path)
    component_tree = _build_component_tree(regions)

    preview_path = docs_dir / "page-preview.png"
    preview_file = _render_page_preview(psd_path, preview_path)

    page_analysis = {
        **page_summary,
        "preview_image": _relative_output_path(output_root, preview_file) if preview_file else None,
        "regions": regions,
    }

    page_analysis_path = docs_dir / "page-analysis.json"
    component_tree_path = docs_dir / "component-tree.json"
    page_tree_path = docs_dir / "page-tree.md"
    component_tree_doc_path = docs_dir / "component-tree.md"
    page_analysis_doc_path = docs_dir / "page-analysis.md"

    page_analysis_path.write_text(
        json.dumps(page_analysis, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    component_tree_path.write_text(
        json.dumps(component_tree, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    page_tree_path.write_text(
        _build_page_tree_markdown(page_summary, regions),
        encoding="utf-8-sig",
    )
    component_tree_doc_path.write_text(
        _build_component_tree_markdown(regions),
        encoding="utf-8-sig",
    )
    page_analysis_doc_path.write_text(
        _build_page_analysis_markdown(page_summary, regions),
        encoding="utf-8-sig",
    )

    analysis_paths = {
        "page_analysis": _relative_output_path(output_root, page_analysis_path),
        "page_analysis_doc": _relative_output_path(output_root, page_analysis_doc_path),
        "page_tree": _relative_output_path(output_root, page_tree_path),
        "component_tree": _relative_output_path(output_root, component_tree_path),
        "component_tree_doc": _relative_output_path(output_root, component_tree_doc_path),
    }
    if preview_file:
        analysis_paths["page_preview"] = _relative_output_path(output_root, preview_file)
    return analysis_paths


def _build_recognition_inputs(
    layers: List[Dict[str, Any]],
    classification_by_layer: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    inputs: List[Dict[str, Any]] = []
    for layer in layers:
        layer_id = layer.get("id", "unknown")
        classification = classification_by_layer.get(layer_id, {})
        payload = dict(layer)
        payload["layer_id"] = layer_id
        payload["type"] = classification.get("type", layer.get("type", layer.get("kind", "unknown")))
        inputs.append(payload)
    return inputs


def _merge_layer_context(
    layers: List[Dict[str, Any]],
    classification_results: List[Dict[str, Any]],
    recognition_results: List[Dict[str, Any]],
    psd_path: str,
) -> List[Dict[str, Any]]:
    classification_by_layer = {
        item.get("layer_id"): item for item in classification_results if item.get("layer_id")
    }
    recognition_by_layer = {
        item.get("layer_id"): item for item in recognition_results if item.get("layer_id")
    }

    merged: List[Dict[str, Any]] = []
    for layer in layers:
        layer_id = layer.get("id")
        classification = classification_by_layer.get(layer_id, {})
        recognition = recognition_by_layer.get(layer_id, {})

        merged_layer = dict(layer)
        merged_layer["type"] = classification.get(
            "type", recognition.get("component_type", layer.get("kind", "unknown"))
        )
        merged_layer["name"] = recognition.get("component_name") or layer.get("name") or layer_id
        merged_layer["position"] = (layer.get("left", 0), layer.get("top", 0))
        merged_layer["layer_ids"] = [layer_id] if layer_id else []
        merged_layer["source_file"] = psd_path
        merged_layer["render_bbox"] = (
            layer.get("left", 0),
            layer.get("top", 0),
            layer.get("right", layer.get("left", 0) + layer.get("width", 0)),
            layer.get("bottom", layer.get("top", 0) + layer.get("height", 0)),
        )
        merged_layer["layer_data"] = {
            "source_file": psd_path,
            "layer_ids": merged_layer["layer_ids"],
            "bbox": merged_layer["render_bbox"],
            "component_name": merged_layer["name"],
        }
        merged.append(merged_layer)
    return merged


def _build_export_plan(strategy_plan, components: List[Dict[str, Any]]) -> ExportCutPlan:
    return ExportCutPlan(
        strategy=strategy_plan.strategy_type,
        components=components,
        canvas_width=strategy_plan.canvas_info.width,
        canvas_height=strategy_plan.canvas_info.height,
        metadata=strategy_plan.metadata,
    )


def _prepare_output_root(output_root: Path) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    for child_name in ("assets", "config", "docs", "recognizer"):
        child_path = output_root / child_name
        if child_path.exists():
            shutil.rmtree(child_path)


def run_full_pipeline(
    psd_path: str,
    output_dir: str = "./output",
    strategy: str = "SMART_MERGE",
    formats: Optional[List[str]] = None,
    use_recognizer: bool = True,
    naming_template: str = "{type}/{name}",
    clean_output: bool = True,
) -> PipelineResult:
    """Run the end-to-end PSD Smart Cut workflow."""

    output_root = Path(output_dir)
    if clean_output:
        _prepare_output_root(output_root)
    else:
        output_root.mkdir(parents=True, exist_ok=True)

    document = parse_psd(psd_path)
    layers = _flatten_layers(document)
    renderable_layers = [layer for layer in layers if _is_renderable_layer(layer)]

    classifier = LayerClassifier()
    classification_batch = classifier.classify_batch(renderable_layers, screenshot_dir="")
    classification_results = classification_batch.results
    classification_by_layer = {
        item.get("layer_id"): item for item in classification_results if item.get("layer_id")
    }

    recognition_results: List[Dict[str, Any]] = []
    if use_recognizer:
        recognizer = Recognizer(
            output_dir=str(output_root / "recognizer"),
            use_screenshot=False,
            mock_mode=False,
        )
        recognitions = recognizer.batch_recognize(
            psd_file=psd_path,
            layers_metadata=_build_recognition_inputs(renderable_layers, classification_by_layer),
            capture_screenshots=False,
        )
        recognition_results = [item.to_dict() for item in recognitions]

    merged_layers = _merge_layer_context(
        renderable_layers,
        classification_results,
        recognition_results,
        psd_path,
    )
    psd_records = _build_psd_layer_records(psd_path)
    export_candidates = _build_component_candidates(merged_layers, psd_records)

    strategy_engine = Strategy()
    strategy_plan = strategy_engine.create_plan(
        layers=export_candidates,
        canvas_width=document.width,
        canvas_height=document.height,
        classification_results=classification_results,
        force_strategy=(strategy or "").lower(),
    )

    export_plan = _build_export_plan(strategy_plan, export_candidates)
    export_formats = formats or ["png"]
    export_reports: Dict[str, ExportReport] = {}
    manifest_paths: Dict[str, str] = {}
    analysis_paths = _write_analysis_outputs(
        output_root=output_root,
        document=document,
        psd_path=psd_path,
        psd_records=psd_records,
        components=export_candidates,
    )

    for export_format in export_formats:
        format_output_dir = output_root / "assets" / export_format
        exporter = Exporter(
            output_dir=str(format_output_dir),
            naming_template=naming_template,
            export_format=export_format,
        )
        report = exporter.export(export_plan)
        export_reports[export_format] = report
        manifest_paths[export_format] = report.manifest_path

    return PipelineResult(
        psd_path=str(Path(psd_path)),
        output_dir=str(output_root),
        total_layers=len(layers),
        strategy=strategy_plan.strategy_type,
        export_formats=export_formats,
        classification_results=classification_results,
        recognition_results=recognition_results,
        export_reports=export_reports,
        manifest_paths=manifest_paths,
        analysis_paths=analysis_paths,
    )
