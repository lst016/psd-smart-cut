"""
Level 7 - JSON Schema Definitions
组件规格的 JSON Schema 定义
"""

from typing import Dict, List, Any, Optional

# ============ 版本信息 ============

SCHEMA_VERSION = "1.0.0"
SCHEMA_NAME = "psd-component-spec"

# ============ 尺寸规格 Schema ============

DIMENSION_SCHEMA = {
    "type": "object",
    "properties": {
        "width": {
            "type": "integer",
            "minimum": 0,
            "description": "宽度（像素）"
        },
        "height": {
            "type": "integer",
            "minimum": 0,
            "description": "高度（像素）"
        },
        "unit": {
            "type": "string",
            "enum": ["px", "rem", "dp", "pt", "em", "vh", "vw", "%"],
            "default": "px",
            "description": "尺寸单位"
        },
        "min_width": {
            "type": ["integer", "null"],
            "minimum": 0,
            "description": "最小宽度"
        },
        "max_width": {
            "type": ["integer", "null"],
            "minimum": 0,
            "description": "最大宽度"
        },
        "scale_factors": {
            "type": "array",
            "items": {"type": "number", "minimum": 0},
            "default": [1.0, 2.0, 3.0],
            "description": "缩放因子列表"
        }
    },
    "required": ["width", "height"]
}

# ============ 位置规格 Schema ============

POSITION_SCHEMA = {
    "type": "object",
    "properties": {
        "position_type": {
            "type": "string",
            "enum": ["static", "relative", "absolute", "fixed", "sticky"],
            "default": "relative",
            "description": "CSS position 值"
        },
        "top": {
            "type": ["string", "null"],
            "description": "上偏移"
        },
        "right": {
            "type": ["string", "null"],
            "description": "右偏移"
        },
        "bottom": {
            "type": ["string", "null"],
            "description": "下偏移"
        },
        "left": {
            "type": ["string", "null"],
            "description": "左偏移"
        },
        "margin": {
            "type": "object",
            "properties": {
                "top": {"type": "string"},
                "right": {"type": "string"},
                "bottom": {"type": "string"},
                "left": {"type": "string"}
            },
            "default": {"top": "0", "right": "0", "bottom": "0", "left": "0"},
            "description": "外边距"
        },
        "padding": {
            "type": "object",
            "properties": {
                "top": {"type": "string"},
                "right": {"type": "string"},
                "bottom": {"type": "string"},
                "left": {"type": "string"}
            },
            "default": {"top": "0", "right": "0", "bottom": "0", "left": "0"},
            "description": "内边距"
        },
        "flex_props": {
            "type": ["object", "null"],
            "properties": {
                "display": {"type": "string", "enum": ["flex", "inline-flex"]},
                "flex_direction": {
                    "type": "string",
                    "enum": ["row", "row-reverse", "column", "column-reverse"]
                },
                "justify_content": {
                    "type": "string",
                    "enum": ["flex-start", "flex-end", "center", "space-between", "space-around", "space-evenly"]
                },
                "align_items": {
                    "type": "string",
                    "enum": ["stretch", "flex-start", "flex-end", "center", "baseline"]
                },
                "flex_wrap": {"type": "string", "enum": ["nowrap", "wrap", "wrap-reverse"]},
                "gap": {"type": "string"}
            },
            "description": "Flex 布局属性"
        },
        "grid_props": {
            "type": ["object", "null"],
            "properties": {
                "display": {"type": "string", "enum": ["grid", "inline-grid"]},
                "grid_template_columns": {"type": "string"},
                "grid_template_rows": {"type": "string"},
                "gap": {"type": "string"},
                "grid_area": {"type": "string"}
            },
            "description": "Grid 布局属性"
        }
    }
}

# ============ 样式规格 Schema ============

STYLE_SCHEMA = {
    "type": "object",
    "properties": {
        "css": {
            "type": "object",
            "additionalProperties": {"type": "string"},
            "description": "CSS 属性"
        },
        "tailwind": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Tailwind CSS 类名"
        },
        "ios": {
            "type": "object",
            "additionalProperties": {"type": "string"},
            "description": "iOS 样式 (Swift)"
        },
        "android": {
            "type": "object",
            "additionalProperties": {"type": "string"},
            "description": "Android 样式 (XML)"
        },
        "theme_vars": {
            "type": "object",
            "additionalProperties": {"type": "string"},
            "description": "主题变量"
        }
    }
}

# ============ 响应式规格 Schema ============

RESPONSIVE_SCHEMA = {
    "type": "object",
    "properties": {
        "mobile": DIMENSION_SCHEMA,
        "tablet": DIMENSION_SCHEMA,
        "desktop": DIMENSION_SCHEMA,
        "wide": DIMENSION_SCHEMA
    },
    "additionalProperties": DIMENSION_SCHEMA
}

# ============ 组件规格 Schema ============

COMPONENT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": f"https://psd-smart-cut.dev/schemas/{SCHEMA_VERSION}/component.json",
    "title": "PSD Component Specification",
    "description": "PSD 智能切图组件规格定义",
    "version": SCHEMA_VERSION,
    "type": "object",
    "properties": {
        "id": {
            "type": "string",
            "description": "组件唯一标识"
        },
        "name": {
            "type": "string",
            "description": "组件名称"
        },
        "type": {
            "type": "string",
            "enum": ["button", "icon", "image", "text", "background", "group", "decorator", "unknown"],
            "description": "组件类型"
        },
        "layer_id": {
            "type": "string",
            "description": "对应 PSD 图层 ID"
        },
        "dimensions": DIMENSION_SCHEMA,
        "position": POSITION_SCHEMA,
        "style": STYLE_SCHEMA,
        "responsive": RESPONSIVE_SCHEMA,
        "children": {
            "type": "array",
            "items": {"$ref": "#"},
            "description": "子组件"
        },
        "metadata": {
            "type": "object",
            "properties": {
                "source_file": {"type": "string"},
                "page_index": {"type": "integer"},
                "layer_index": {"type": "integer"},
                "created_at": {"type": "string", "format": "date-time"},
                "updated_at": {"type": "string", "format": "date-time"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "notes": {"type": "string"}
            }
        }
    },
    "required": ["id", "name"]
}

# ============ 组件集合 Schema ============

COMPONENT_COLLECTION_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": f"https://psd-smart-cut.dev/schemas/{SCHEMA_VERSION}/collection.json",
    "title": "PSD Component Collection",
    "description": "PSD 组件集合定义",
    "version": SCHEMA_VERSION,
    "type": "object",
    "properties": {
        "schema_version": {
            "type": "string",
            "const": SCHEMA_VERSION
        },
        "source_file": {
            "type": "string",
            "description": "源 PSD 文件"
        },
        "canvas": {
            "type": "object",
            "properties": {
                "width": {"type": "integer"},
                "height": {"type": "integer"}
            },
            "required": ["width", "height"]
        },
        "components": {
            "type": "array",
            "items": COMPONENT_SCHEMA
        },
        "metadata": {
            "type": "object",
            "properties": {
                "generated_at": {"type": "string", "format": "date-time"},
                "generator": {"type": "string"},
                "generator_version": {"type": "string"}
            }
        }
    },
    "required": ["schema_version", "components"]
}

# ============ 导出所有 Schema ============

SCHEMAS = {
    "component": COMPONENT_SCHEMA,
    "collection": COMPONENT_COLLECTION_SCHEMA,
    "dimension": DIMENSION_SCHEMA,
    "position": POSITION_SCHEMA,
    "style": STYLE_SCHEMA,
    "responsive": RESPONSIVE_SCHEMA
}


def get_schema(name: str) -> Optional[Dict]:
    """获取指定名称的 Schema"""
    return SCHEMAS.get(name)


def get_component_schema() -> Dict:
    """获取组件 Schema"""
    return COMPONENT_SCHEMA


def get_collection_schema() -> Dict:
    """获取集合 Schema"""
    return COMPONENT_COLLECTION_SCHEMA


def validate_against_schema(data: Dict, schema_name: str) -> bool:
    """
    验证数据是否符合 Schema
    
    Args:
        data: 要验证的数据
        schema_name: Schema 名称
        
    Returns:
        bool: 是否符合
    """
    schema = get_schema(schema_name)
    if schema is None:
        return False
    
    # 简单的必需字段检查
    required = schema.get("required", [])
    for field in required:
        if field not in data:
            return False
    
    # 尺寸检查
    if schema_name in ["component", "dimension"]:
        if "dimensions" in data:
            dims = data["dimensions"]
            if "width" not in dims or "height" not in dims:
                return False
    
    return True
