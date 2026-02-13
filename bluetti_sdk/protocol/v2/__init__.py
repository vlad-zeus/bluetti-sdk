"""V2 Protocol - Schema-based parser for Elite V2 devices.

This module implements a declarative, data-driven parser for V2 protocol blocks.

Architecture:
    - DataTypes: Type system (UInt8/16/32, Int8/16/32, String, Bitmap, Enum)
    - Transforms: Transform pipeline (abs, scale, minus, bitmask, shift, clamp)
    - Schema: Field definitions (Field, ArrayField, PackedField, BlockSchema)
    - Parser: V2Parser engine

Example:
    >>> from bluetti_sdk.protocol.v2 import V2Parser, BlockSchema, Field, UInt16
    >>>
    >>> schema = BlockSchema(
    ...     block_id=1300,
    ...     name="GRID_INFO",
    ...     min_length=32,
    ...     fields=[
    ...         Field("frequency", offset=0, type=UInt16(),
    ...               transform=["scale:0.1"], unit="Hz"),
    ...         Field("voltage", offset=28, type=UInt16(),
    ...               transform=["scale:0.1"], unit="V"),
    ...     ]
    ... )
    >>>
    >>> parser = V2Parser()
    >>> parser.register_schema(schema)
    >>> parsed = parser.parse_block(1300, data_bytes)
    >>> print(parsed.values['frequency'])  # 50.0
"""

# DataTypes
from .datatypes import (
    DataType,
    UInt8,
    UInt16,
    UInt32,
    Int8,
    Int16,
    Int32,
    String,
    Bitmap,
    Enum,
)

# Transforms
from .transforms import compile_transform_pipeline

# Schema
from .schema import (
    Field,
    ArrayField,
    PackedField,
    SubField,
    BlockSchema,
)

# Parser
from .parser import V2Parser, ParsedBlock

__all__ = [
    # DataTypes
    "DataType",
    "UInt8",
    "UInt16",
    "UInt32",
    "Int8",
    "Int16",
    "Int32",
    "String",
    "Bitmap",
    "Enum",

    # Transforms
    "compile_transform_pipeline",

    # Schema
    "Field",
    "ArrayField",
    "PackedField",
    "SubField",
    "BlockSchema",

    # Parser
    "V2Parser",
    "ParsedBlock",
]
