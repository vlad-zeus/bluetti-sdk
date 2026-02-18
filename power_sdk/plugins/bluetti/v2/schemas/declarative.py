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

from power_sdk.constants import V2_PROTOCOL_VERSION
from ..protocol.datatypes import DataType
from ..protocol.schema import BlockSchema, Field, FieldGroup
from ..protocol.transforms import TransformStep

T = TypeVar("T")

# Transform specification: supports both typed transforms and legacy string DSL
TransformSpec = Union[str, TransformStep]


@dataclass(frozen=True)
class NestedGroupSpec:
    """Class-level attribute specifying a nested field group.

    NOT a dataclass field - define as a plain class attribute (no type
    annotation, no block_field() wrapper):

    Example::

        @block_schema(block_id=17400, name="AT1_SETTINGS")
        @dataclass
        class ATSEventExtBlock:
            volt_level_set: int = block_field(offset=176, type=UInt16())

            # Nested group - plain class attribute, no type annotation
            config_grid = nested_group(
                "config_grid",
                sub_fields=[Field("max_current", 84, UInt16())],
                evidence_status="partial",
            )

    The group is collected by _generate_schema() and becomes a FieldGroup
    in the BlockSchema. Parser output: values["config_grid"] = {"max_current": ...}
    """

    name: str
    sub_fields: tuple[Field, ...]  # tuple of Field objects
    required: bool = False
    description: Optional[str] = None
    evidence_status: Optional[str] = None


def nested_group(
    name: str,
    *,
    sub_fields: Sequence[Field],
    required: bool = False,
    description: Optional[str] = None,
    evidence_status: Optional[str] = None,
) -> NestedGroupSpec:
    """Define a nested field group for a declarative schema.

    Unlike block_field(), nested_group() creates a class-level attribute
    (not a dataclass field). The group is detected by _generate_schema()
    and added as a FieldGroup to the BlockSchema.

    Each field in sub_fields uses its absolute byte offset within the
    block data (not relative to any base offset).

    Parser output::

        values["group_name"] = {"field_name": value, ...}

    Args:
        name: Group name (key in parsed values dict)
        sub_fields: Field objects with absolute byte offsets
        required: Whether group is required (default False)
        description: Group description / evidence notes
        evidence_status: Evidence status (e.g. "partial", "smali_verified")

    Returns:
        NestedGroupSpec instance (to be used as class attribute)

    Example::

        @block_schema(block_id=17400, name="AT1_SETTINGS")
        @dataclass
        class ATSEventExtBlock:
            volt_level_set: int = block_field(
                offset=176, type=UInt16(),
                transform=["bitmask:0x7"],
                required=False,
            )

            # NOT a dataclass field - no type annotation
            config_grid = nested_group(
                "config_grid",
                sub_fields=[
                    Field(
                        name="max_current",
                        offset=84,
                        type=UInt16(),
                        required=False,
                        description="Max current limit (smali: line 2578)",
                    ),
                ],
                description="AT1 grid config item",
                evidence_status="partial",
            )
    """
    return NestedGroupSpec(
        name=name,
        sub_fields=tuple(sub_fields),
        required=required,
        description=description,
        evidence_status=evidence_status,
    )


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
    protocol_version: int = V2_PROTOCOL_VERSION,
    schema_version: str = "1.0.0",
    strict: bool = True,
    verification_status: Optional[str] = None,
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
        verification_status: Verification status ("smali_verified",
            "device_verified", "inferred", "partial")

    Returns:
        Decorator function

    Example:
        @block_schema(
            block_id=100,
            name="APP_HOME_DATA",
            verification_status="smali_verified"
        )
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
            verification_status=verification_status,
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
    verification_status: Optional[str],
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
        verification_status: Verification status metadata

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
    schema_fields: List[Any] = []
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

    # Collect nested group specs from class-level attributes (not dataclass fields)
    # These are NestedGroupSpec instances defined as plain class attributes
    for attr_val in vars(cls).values():
        if not isinstance(attr_val, NestedGroupSpec):
            continue
        group = FieldGroup(
            name=attr_val.name,
            fields=attr_val.sub_fields,
            required=attr_val.required,
            description=attr_val.description,
            evidence_status=attr_val.evidence_status,
        )
        schema_fields.append(group)

        # Track max offset for auto min_length
        if group.fields:
            group_end = max(f.offset + f.size() for f in group.fields)
            max_offset = max(max_offset, group_end)

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
        verification_status=verification_status,
        fields=schema_fields,
    )
