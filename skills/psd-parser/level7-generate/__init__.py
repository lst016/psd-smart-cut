"""
Level 7 - Generate Layer
规格生成层 - 生成组件的技术规格文档
"""

from .dimension_generator import (
    DimensionSpec,
    DimensionGenerator,
    UnitConverter,
    generate_dimension,
    generate_dimensions_batch
)

from .position_generator import (
    PositionSpec,
    PositionGenerator,
    LayoutType,
    generate_position,
    generate_positions_batch
)

from .style_generator import (
    StyleSpec,
    StyleGenerator,
    ColorConverter,
    generate_style,
    generate_styles_batch
)

from .spec_validator import (
    ValidationError,
    ValidationResult,
    SpecValidator,
    CSSValidator,
    validate_spec,
    validate_specs_batch
)

from .schema import (
    SCHEMA_VERSION,
    SCHEMA_NAME,
    COMPONENT_SCHEMA,
    COMPONENT_COLLECTION_SCHEMA,
    DIMENSION_SCHEMA,
    POSITION_SCHEMA,
    STYLE_SCHEMA,
    RESPONSIVE_SCHEMA,
    get_schema,
    get_component_schema,
    get_collection_schema,
    validate_against_schema
)

from .generator import (
    SpecResult,
    ComponentSpec,
    GenerationReport,
    SpecGenerator,
    generate_spec,
    generate_specs_batch,
    generate_collection
)

__all__ = [
    # Dimension
    "DimensionSpec",
    "DimensionGenerator",
    "UnitConverter",
    "generate_dimension",
    "generate_dimensions_batch",
    
    # Position
    "PositionSpec",
    "PositionGenerator",
    "LayoutType",
    "generate_position",
    "generate_positions_batch",
    
    # Style
    "StyleSpec",
    "StyleGenerator",
    "ColorConverter",
    "generate_style",
    "generate_styles_batch",
    
    # Validator
    "ValidationError",
    "ValidationResult",
    "SpecValidator",
    "CSSValidator",
    "validate_spec",
    "validate_specs_batch",
    
    # Schema
    "SCHEMA_VERSION",
    "SCHEMA_NAME",
    "COMPONENT_SCHEMA",
    "COMPONENT_COLLECTION_SCHEMA",
    "DIMENSION_SCHEMA",
    "POSITION_SCHEMA",
    "STYLE_SCHEMA",
    "RESPONSIVE_SCHEMA",
    "get_schema",
    "get_component_schema",
    "get_collection_schema",
    "validate_against_schema",
    
    # Generator
    "SpecResult",
    "ComponentSpec",
    "GenerationReport",
    "SpecGenerator",
    "generate_spec",
    "generate_specs_batch",
    "generate_collection"
]
