"""V2 Protocol Schema Definitions

Field definitions and block schemas for V2 protocol parsing.
"""

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from typing import Any, cast

from .datatypes import DataType
from .transforms import compile_transform_pipeline

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of schema validation."""

    valid: bool
    errors: list[str] = dataclass_field(default_factory=list)
    warnings: list[str] = dataclass_field(default_factory=list)
    missing_fields: list[str] = dataclass_field(default_factory=list)


@dataclass(frozen=True)
class Field:
    """Basic field definition.

    Represents a single value at a specific offset in a V2 block.

    Example:
        Field(
            name="soc",
            offset=0,
            type=UInt16(),
            unit="%",
            required=True
        )
    """

    name: str
    offset: int
    type: DataType
    unit: str | None = None
    required: bool = True
    transform: Sequence[str] | None = None
    min_protocol_version: int | None = None
    description: str | None = None
    # Computed in __post_init__
    _compiled_transform: Any | None = dataclass_field(init=False)

    def __post_init__(self) -> None:
        """Compile transform pipeline for performance."""
        # Convert to immutable tuple if list provided
        if self.transform is not None and isinstance(self.transform, list):
            object.__setattr__(self, "transform", tuple(self.transform))

        # Compile transform pipeline (frozen-safe: use object.__setattr__)
        if self.transform:
            compiled = compile_transform_pipeline(self.transform)
            object.__setattr__(self, "_compiled_transform", compiled)
        else:
            object.__setattr__(self, "_compiled_transform", None)

    def parse(self, data: bytes) -> Any:
        """Parse field value from data.

        Args:
            data: Normalized byte buffer

        Returns:
            Parsed and transformed value

        Raises:
            IndexError: If offset + size exceeds data length
            ValueError: If parsing fails
        """
        # Parse raw value
        raw_value = self.type.parse(data, self.offset)

        # Apply transforms
        if self._compiled_transform:
            return self._compiled_transform(raw_value)

        return raw_value

    def size(self) -> int:
        """Field size in bytes."""
        return cast(int, self.type.size())


@dataclass(frozen=True)
class ArrayField:
    """Array field definition.

    Represents multiple values of the same type at regular intervals.

    Example:
        ArrayField(
            name="cell_voltages",
            offset=10,
            count=16,
            stride=2,
            item_type=UInt16(),
            transform=["bitmask:0x3FFF", "scale:0.001"],
            unit="V"
        )
    """

    name: str
    offset: int
    count: int
    stride: int
    item_type: DataType
    unit: str | None = None
    required: bool = True
    transform: Sequence[str] | None = None
    min_protocol_version: int | None = None
    description: str | None = None
    # Computed in __post_init__
    _compiled_transform: Any | None = dataclass_field(init=False)

    def __post_init__(self) -> None:
        """Compile transform pipeline for performance."""
        # Validate count and stride before any other processing
        if self.count < 1:
            raise ValueError(
                f"ArrayField '{self.name}': count must be >= 1, got {self.count}"
            )
        if self.stride < 1:
            raise ValueError(
                f"ArrayField '{self.name}': stride must be >= 1, got {self.stride}"
            )

        # Convert to immutable tuple if list provided
        if self.transform is not None and isinstance(self.transform, list):
            object.__setattr__(self, "transform", tuple(self.transform))

        # Compile transform pipeline (frozen-safe: use object.__setattr__)
        if self.transform:
            compiled = compile_transform_pipeline(self.transform)
            object.__setattr__(self, "_compiled_transform", compiled)
        else:
            object.__setattr__(self, "_compiled_transform", None)

    def parse(self, data: bytes) -> list[Any]:
        """Parse array values from data.

        Args:
            data: Normalized byte buffer

        Returns:
            List of parsed and transformed values

        Raises:
            IndexError: If any item exceeds data length
            ValueError: If parsing fails
        """
        values = []

        for i in range(self.count):
            item_offset = self.offset + (i * self.stride)

            # Parse raw value
            raw_value = self.item_type.parse(data, item_offset)

            # Apply transforms
            if self._compiled_transform:
                value = self._compiled_transform(raw_value)
            else:
                value = raw_value

            values.append(value)

        return values

    def size(self) -> int:
        """Total array size in bytes."""
        return self.count * self.stride


@dataclass(frozen=True)
class SubField:
    """Sub-field within a packed field.

    Represents a portion of bits extracted from a packed value.

    Example:
        SubField(
            name="voltage",
            bits="0:14",
            transform=["scale:0.001"],
            unit="V"
        )
    """

    name: str
    bits: str  # "start:end" (e.g., "0:14" for bits 0-13)
    transform: Sequence[str] | None = None
    unit: str | None = None
    enum: Mapping[int, str] | None = None
    # Computed attributes (set in __post_init__)
    bit_start: int = dataclass_field(init=False)
    bit_end: int = dataclass_field(init=False)
    mask: int = dataclass_field(init=False)
    shift: int = dataclass_field(init=False)
    _compiled_transform: Any | None = dataclass_field(init=False)

    def __post_init__(self) -> None:
        """Parse bit range and compile transform."""
        # Convert to immutable tuple if list provided
        if self.transform is not None and isinstance(self.transform, list):
            object.__setattr__(self, "transform", tuple(self.transform))

        # Parse bits "start:end" (frozen-safe: use object.__setattr__)
        parts = self.bits.split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid bits spec: {self.bits} (expected 'start:end')")

        bit_start = int(parts[0])
        bit_end = int(parts[1])

        if bit_start >= bit_end:
            raise ValueError(f"Invalid bit range: {self.bits} (start >= end)")

        # Calculate mask and shift
        bit_count = bit_end - bit_start
        mask = (1 << bit_count) - 1
        shift = bit_start

        # Set computed attributes (frozen-safe)
        object.__setattr__(self, "bit_start", bit_start)
        object.__setattr__(self, "bit_end", bit_end)
        object.__setattr__(self, "mask", mask)
        object.__setattr__(self, "shift", shift)

        # Compile transform
        if self.transform:
            compiled = compile_transform_pipeline(self.transform)
            object.__setattr__(self, "_compiled_transform", compiled)
        else:
            object.__setattr__(self, "_compiled_transform", None)

    def extract(self, packed_value: int) -> Any:
        """Extract sub-field value from packed integer.

        Args:
            packed_value: Packed integer value

        Returns:
            Extracted and transformed value
        """
        # Extract bits
        raw_value = (packed_value >> self.shift) & self.mask

        # Apply enum mapping if present
        value: Any = raw_value
        if self.enum:
            value = self.enum.get(raw_value, f"UNKNOWN_{raw_value}")

        # Apply transforms
        if self._compiled_transform:
            return self._compiled_transform(value)

        return value


@dataclass(frozen=True)
class PackedField:
    """Packed field definition.

    Represents multiple sub-fields packed into a single integer value.
    Common for cell voltages with status bits.

    Example:
        PackedField(
            name="cells",
            offset=10,
            count=16,
            stride=2,
            fields=[
                SubField("voltage", bits="0:14", transform=["scale:0.001"], unit="V"),
                SubField("status", bits="14:16", enum={0: "OK", 1: "LOW", 2: "HIGH"})
            ]
        )
    """

    name: str
    offset: int
    count: int
    stride: int
    base_type: DataType
    fields: Sequence[SubField]
    required: bool = True
    min_protocol_version: int | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        """Convert fields to immutable tuple and validate SubField bit ranges."""
        # Convert to immutable tuple if list provided
        if self.fields is not None and isinstance(self.fields, list):
            object.__setattr__(self, "fields", tuple(self.fields))

        # Validate that each SubField's bit_end does not exceed the base_type width
        base_bits = self.base_type.size() * 8
        for subfield in self.fields:
            if subfield.bit_end > base_bits:
                raise ValueError(
                    f"PackedField '{self.name}': SubField '{subfield.name}' "
                    f"bit_end={subfield.bit_end} exceeds base_type width "
                    f"of {base_bits} bits"
                )

    def parse(self, data: bytes) -> list[dict[str, Any]]:
        """Parse packed field array.

        Args:
            data: Normalized byte buffer

        Returns:
            List of dicts, one per packed item, with sub-field names as keys

        Example output:
            [
                {"voltage": 3.245, "status": "OK"},
                {"voltage": 3.256, "status": "OK"},
                ...
            ]
        """
        items = []

        for i in range(self.count):
            item_offset = self.offset + (i * self.stride)

            # Parse packed value using configured base_type
            packed_value = self.base_type.parse(data, item_offset)

            # Extract all sub-fields
            item = {}
            for subfield in self.fields:
                item[subfield.name] = subfield.extract(packed_value)

            items.append(item)

        return items

    def size(self) -> int:
        """Total packed field size in bytes."""
        return self.count * self.stride


@dataclass(frozen=True)
class FieldGroup:
    """Named group of fields for namespace organization.

    Groups related fields under a common namespace in the parsed values dict.
    Use for complex blocks where logical sub-structures span multiple offsets.
    Each field in the group uses its absolute byte offset within the block
    data (not relative to any base). This matches evidence-based modeling
    where nested structures reference scattered absolute data positions.

    Parser output::

        values["group_name"] = {
            "field1": value1,
            "field2": value2,
        }

    Use for:
    - Evidence-accurate modeling of nested protocol structures
    - Logical grouping of related fields under a namespace
    - Complex blocks where flat field listing loses semantic structure

    Example::

        FieldGroup(
            name="config_grid",
            fields=[
                Field("max_current", offset=84, type=UInt16()),
                Field("type", offset=18, type=UInt16()),
            ],
            required=False,
            evidence_status="partial",
        )
    """

    name: str
    fields: Sequence[Field]
    required: bool = False
    description: str | None = None
    evidence_status: str | None = None

    def __post_init__(self) -> None:
        """Convert fields to immutable tuple."""
        if self.fields is not None and isinstance(self.fields, list):
            object.__setattr__(self, "fields", tuple(self.fields))

    @property
    def offset(self) -> int:
        """Minimum byte offset of any field in this group (0 if empty)."""
        if not self.fields:
            return 0
        return min(f.offset for f in self.fields)

    def size(self) -> int:
        """Byte span from min field start to max field end (0 if empty)."""
        if not self.fields:
            return 0
        return max(f.offset + f.size() for f in self.fields) - self.offset

    def parse(self, data: bytes) -> dict[str, Any]:
        """Parse all sub-fields in this group.

        Args:
            data: Normalized byte buffer

        Returns:
            Dict mapping field_name to parsed value (None if unavailable)
        """
        result: dict[str, Any] = {}
        for field_def in self.fields:
            field_end = field_def.offset + field_def.size()
            if field_end > len(data):
                result[field_def.name] = None
            else:
                try:
                    result[field_def.name] = field_def.parse(data)
                except Exception as exc:
                    logger.debug(
                        "FieldGroup parse failed for %s.%s: %s",
                        self.name,
                        field_def.name,
                        exc,
                    )
                    result[field_def.name] = None
        return result


@dataclass(frozen=True)
class BlockSchema:
    """Schema definition for a V2 block.

    Defines the structure and validation rules for a specific block ID.

    Verification Status:
        - "verified_reference": Fields confirmed from reference implementation
        - "device_verified": Fields validated against real device data
        - "inferred": Fields inferred without verification (provisional)
        - "partial": Mix of verified and inferred fields

    Example:
        BlockSchema(
            block_id=100,
            name="APP_HOME_DATA",
            description="Main dashboard data",
            min_length=52,
            fields=[
                Field("soc", 0, UInt16(), unit="%"),
                Field("pack_voltage", 2, UInt16(), transform=["scale:0.1"], unit="V"),
                ArrayField("cell_voltages", 10, count=16, stride=2, item_type=UInt16())
            ],
            strict=True,
            verification_status="verified_reference"
        )
    """

    block_id: int
    name: str
    description: str
    min_length: int
    fields: Sequence[Any]  # Sequence[Field | ArrayField | PackedField]
    protocol_version: int = 2000
    schema_version: str = "1.0.0"
    strict: bool = True
    verification_status: str | None = None

    def __post_init__(self) -> None:
        """Convert fields to immutable tuple."""
        # Convert to immutable tuple if list provided
        if self.fields is not None and isinstance(self.fields, list):
            object.__setattr__(self, "fields", tuple(self.fields))

    @property
    def max_field_end(self) -> int:
        """Maximum end offset across all fields in bytes."""
        max_end = 0
        for field_def in self.fields:
            if isinstance(field_def, FieldGroup):
                for subfield in field_def.fields:
                    max_end = max(max_end, subfield.offset + subfield.size())
            else:
                max_end = max(max_end, field_def.offset + field_def.size())
        return max_end

    def validate(self, data: bytes) -> ValidationResult:
        """Validate data against this schema.

        Args:
            data: Normalized byte buffer

        Returns:
            ValidationResult with errors, warnings, and missing fields
        """
        result = ValidationResult(valid=True)

        # Check minimum length
        if len(data) < self.min_length:
            result.valid = False
            result.errors.append(f"Data length {len(data)} < minimum {self.min_length}")

        # Check each field
        for field_def in self.fields:
            if isinstance(field_def, FieldGroup):
                # Recurse into subfields so required sub-fields are checked
                # individually; the group-level required flag is advisory only.
                for sub in field_def.fields:
                    sub_end = sub.offset + sub.size()
                    if sub_end > len(data):
                        if sub.required:
                            result.valid = False
                            result.errors.append(
                                f"Required field '{field_def.name}.{sub.name}' "
                                f"at offset {sub.offset} exceeds data length "
                                f"{len(data)}"
                            )
                        else:
                            result.missing_fields.append(
                                f"{field_def.name}.{sub.name}"
                            )
                continue

            field_name = field_def.name

            try:
                # Check if field fits in data
                field_end = field_def.offset + field_def.size()

                if field_end > len(data):
                    if field_def.required:
                        result.valid = False
                        result.errors.append(
                            f"Required field '{field_name}' at offset "
                            f"{field_def.offset} exceeds data length {len(data)}"
                        )
                    else:
                        result.missing_fields.append(field_name)

            except Exception as e:
                if field_def.required:
                    result.valid = False
                    result.errors.append(f"Field '{field_name}' validation error: {e}")

        # Warn about extra data in strict mode
        if self.strict:
            max_offset = self.max_field_end

            if len(data) > max_offset:
                result.warnings.append(
                    f"Extra data beyond defined fields: {len(data) - max_offset} bytes"
                )

        return result

    def get_field(self, name: str) -> Any | None:
        """Get field definition by name.

        Searches top-level fields first, then recurses one level into any
        FieldGroup to locate nested sub-fields by name.

        Args:
            name: Field name (top-level or nested within a FieldGroup)

        Returns:
            Field definition or None if not found
        """
        for field_def in self.fields:
            if field_def.name == name:
                return field_def
            # Recurse one level into FieldGroup containers
            if isinstance(field_def, FieldGroup):
                for sub in field_def.fields:
                    if sub.name == name:
                        return sub
        return None
