"""Declarative Block Schema Definition

Provides decorator-based declarative API for defining block schemas.
Automatically generates BlockSchema from class definitions.

Example:
    @block_schema(block_id=100, name="APP_HOME_DATA")
    class AppHomeDataBlock:
        '''Main dashboard data.'''

        pack_voltage: float = block_field(
            offset=0,
            type=UInt16(),
            transform=["scale:0.1"],
            unit="V",
            description="Total pack voltage"
        )

        soc: int = block_field(
            offset=4,
            type=UInt16(),
            unit="%",
            description="State of charge"
        )

Usage:
    # Auto-generate BlockSchema
    schema = AppHomeDataBlock.to_schema()

    # Type-safe access to parsed data
    data = parser.parse_block(100, raw_bytes)
    voltage = data.values['pack_voltage']  # IDE autocomplete works!
"""

from dataclasses import dataclass, fields, is_dataclass
from dataclasses import field as dataclass_field
from typing import Any, Callable, List, Optional, Sequence, Type, TypeVar, Union

from ..protocol.v2.datatypes import DataType
from ..protocol.v2.schema import BlockSchema, Field
from ..protocol.v2.transforms import TransformStep

T = TypeVar("T")

# Transform specification: supports both typed transforms and legacy string DSL
TransformSpec = Union[str, TransformStep]


@dataclass(frozen=True)
class BlockFieldMetadata:
    """Metadata for a declarative block field.

    This is stored in dataclass field metadata and used to generate
    BlockSchema Field definitions.
    """

    offset: int
    type: DataType
    unit: Optional[str] = None
    required: bool = True
    transform: Optional[Sequence[TransformSpec]] = None
    min_protocol_version: Optional[int] = None
    description: Optional[str] = None


def block_field(
    offset: int,
    type: DataType,
    unit: Optional[str] = None,
    required: bool = True,
    transform: Optional[Sequence[TransformSpec]] = None,
    min_protocol_version: Optional[int] = None,
    description: Optional[str] = None,
    default: Any = None,
) -> Any:
    """Define a block field with metadata.

    Args:
        offset: Byte offset in block
        type: DataType for parsing
        unit: Physical unit (e.g., "V", "A", "%")
        required: Whether field is required
        transform: Transform pipeline (typed transforms or legacy strings)
                  Examples: [scale(0.1)] or ["scale:0.1"]
        min_protocol_version: Minimum protocol version
        description: Field description
        default: Default value if field missing

    Returns:
        dataclass field with BlockFieldMetadata
    """
    metadata = BlockFieldMetadata(
        offset=offset,
        type=type,
        unit=unit,
        required=required,
        transform=tuple(transform) if transform else None,
        min_protocol_version=min_protocol_version,
        description=description,
    )

    return dataclass_field(default=default, metadata={"block_field": metadata})


def block_schema(
    block_id: int,
    name: str,
    description: Optional[str] = None,
    min_length: Optional[int] = None,
    protocol_version: int = 2000,
    schema_version: str = "1.0.0",
    strict: bool = True,
) -> Callable[[Type[T]], Type[T]]:
    """Decorator to mark a class as a declarative block schema.

    Automatically generates BlockSchema from class fields.

    Args:
        block_id: Unique block identifier
        name: Block name (e.g., "APP_HOME_DATA")
        description: Block description
        min_length: Minimum data length in bytes (auto-calculated if None)
        protocol_version: Protocol version
        schema_version: Schema version
        strict: Strict validation mode

    Returns:
        Decorator function

    Example:
        @block_schema(block_id=100, name="APP_HOME_DATA")
        class AppHomeData:
            voltage: float = block_field(offset=0, type=UInt16())
    """

    def decorator(cls: Type[T]) -> Type[T]:
        # Generate BlockSchema from class fields
        schema = _generate_schema(
            cls,
            block_id=block_id,
            name=name,
            description=description or cls.__doc__ or "",
            min_length=min_length,
            protocol_version=protocol_version,
            schema_version=schema_version,
            strict=strict,
        )

        # Attach schema to class
        cls._block_schema = schema  # type: ignore
        cls.to_schema = classmethod(lambda _: schema)  # type: ignore

        return cls

    return decorator


def _generate_schema(
    cls: Type[Any],
    block_id: int,
    name: str,
    description: str,
    min_length: Optional[int],
    protocol_version: int,
    schema_version: str,
    strict: bool,
) -> BlockSchema:
    """Generate BlockSchema from declarative class.

    Args:
        cls: Dataclass with block_field definitions
        block_id: Block ID
        name: Block name
        description: Block description
        min_length: Minimum data length
        protocol_version: Protocol version
        schema_version: Schema version
        strict: Strict mode

    Returns:
        Generated BlockSchema

    Raises:
        TypeError: If cls is not a dataclass
    """
    # Validate that cls is a dataclass
    if not is_dataclass(cls):
        raise TypeError(
            f"@block_schema can only be applied to dataclasses. "
            f"Add @dataclass decorator to {cls.__name__}. "
            f"Example:\n"
            f"  @block_schema(block_id={block_id}, name='{name}')\n"
            f"  @dataclass\n"
            f"  class {cls.__name__}:\n"
            f"      ..."
        )

    # Extract field definitions from dataclass
    schema_fields: List[Field] = []
    max_offset = 0

    for field_def in fields(cls):
        # Get block field metadata
        metadata = field_def.metadata.get("block_field")
        if not metadata:
            # Skip non-block fields
            continue

        # Create Field from metadata
        schema_field = Field(
            name=field_def.name,
            offset=metadata.offset,
            type=metadata.type,
            unit=metadata.unit,
            required=metadata.required,
            transform=metadata.transform,
            min_protocol_version=metadata.min_protocol_version,
            description=metadata.description,
        )

        schema_fields.append(schema_field)

        # Track max offset for auto min_length
        field_end = metadata.offset + metadata.type.size()
        max_offset = max(max_offset, field_end)

    # Auto-calculate min_length if not provided
    if min_length is None:
        min_length = max_offset

    # Generate BlockSchema
    return BlockSchema(
        block_id=block_id,
        name=name,
        description=description.strip(),
        min_length=min_length,
        protocol_version=protocol_version,
        schema_version=schema_version,
        strict=strict,
        fields=schema_fields,
    )
