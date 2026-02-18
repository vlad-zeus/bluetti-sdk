"""Bluetti V2 protocol implementations.

Re-exports from sub-modules for convenient access:
    from power_sdk.plugins.bluetti.v2.protocol import V2Parser, BlockSchema, Field
"""

# DataTypes
# ParsedRecord lives in contracts -- re-export for convenience
from power_sdk.contracts.types import ParsedRecord
from .datatypes import (
    Bitmap,
    DataType,
    Enum,
    Int8,
    Int16,
    Int32,
    String,
    UInt8,
    UInt16,
    UInt32,
)

# Parser
from .parser import V2Parser

# Schema
from .schema import (
    ArrayField,
    BlockSchema,
    Field,
    FieldGroup,
    PackedField,
    SubField,
)

# Transforms
from .transforms import (
    TransformChain,
    TransformStep,
    abs_,
    bitmask,
    clamp,
    compile_transform_pipeline,
    minus,
    scale,
    shift,
)

# Protocol layer
from .layer import ModbusProtocolLayer

__all__ = [
    "ArrayField",
    "Bitmap",
    "BlockSchema",
    "DataType",
    "Enum",
    "Field",
    "FieldGroup",
    "Int8",
    "Int16",
    "Int32",
    "ModbusProtocolLayer",
    "PackedField",
    "ParsedRecord",
    "String",
    "SubField",
    "TransformChain",
    "TransformStep",
    "UInt8",
    "UInt16",
    "UInt32",
    "V2Parser",
    "abs_",
    "bitmask",
    "clamp",
    "compile_transform_pipeline",
    "minus",
    "scale",
    "shift",
]
