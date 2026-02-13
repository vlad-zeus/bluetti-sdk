"""Unit tests for declarative block schema system."""

import pytest
from bluetti_sdk.protocol.v2.datatypes import Int32, String, UInt16, UInt32
from bluetti_sdk.protocol.v2.schema import BlockSchema
from bluetti_sdk.schemas.declarative import block_field, block_schema
from dataclasses import dataclass


def test_block_field_metadata():
    """Test block_field creates proper field metadata."""
    from bluetti_sdk.schemas.declarative import BlockFieldMetadata

    @dataclass
    class TestBlock:
        voltage: float = block_field(
            offset=0,
            type=UInt16(),
            transform=["scale:0.1"],
            unit="V",
            description="Test voltage"
        )

    # Get field metadata
    from dataclasses import fields
    field_def = fields(TestBlock)[0]
    metadata = field_def.metadata.get('block_field')

    assert isinstance(metadata, BlockFieldMetadata)
    assert metadata.offset == 0
    assert isinstance(metadata.type, UInt16)
    assert metadata.transform == ("scale:0.1",)  # Converted to tuple
    assert metadata.unit == "V"
    assert metadata.description == "Test voltage"


def test_block_schema_decorator():
    """Test @block_schema decorator generates BlockSchema."""

    @block_schema(block_id=9001, name="TEST_BLOCK")
    @dataclass
    class TestBlock:
        """Test block description."""

        field1: int = block_field(offset=0, type=UInt16())
        field2: int = block_field(offset=2, type=UInt16())

    # Check schema attached to class
    assert hasattr(TestBlock, '_block_schema')
    assert hasattr(TestBlock, 'to_schema')

    # Get generated schema
    schema = TestBlock.to_schema()

    assert isinstance(schema, BlockSchema)
    assert schema.block_id == 9001
    assert schema.name == "TEST_BLOCK"
    assert schema.description == "Test block description."
    assert len(schema.fields) == 2
    assert schema.fields[0].name == "field1"
    assert schema.fields[1].name == "field2"


def test_auto_min_length_calculation():
    """Test automatic min_length calculation from field offsets."""

    @block_schema(block_id=9002, name="AUTO_LENGTH")
    @dataclass
    class AutoLengthBlock:
        """Auto length test."""

        field1: int = block_field(offset=0, type=UInt16())  # 0-1
        field2: int = block_field(offset=2, type=UInt32())  # 2-5
        field3: str = block_field(offset=10, type=String(length=8))  # 10-17

    schema = AutoLengthBlock.to_schema()

    # min_length should be max(field_end) = 10 + 8 = 18
    assert schema.min_length == 18


def test_explicit_min_length():
    """Test explicit min_length overrides auto-calculation."""

    @block_schema(block_id=9003, name="EXPLICIT_LENGTH", min_length=100)
    @dataclass
    class ExplicitLengthBlock:
        """Explicit length test."""

        field1: int = block_field(offset=0, type=UInt16())

    schema = ExplicitLengthBlock.to_schema()
    assert schema.min_length == 100  # Explicit, not auto-calculated


def test_field_types_and_transforms():
    """Test various field types and transforms are preserved."""

    @block_schema(block_id=9004, name="FIELD_TYPES")
    @dataclass
    class FieldTypesBlock:
        """Field types test."""

        uint16_field: int = block_field(offset=0, type=UInt16())
        uint32_field: int = block_field(offset=2, type=UInt32())
        int32_field: int = block_field(offset=6, type=Int32())
        string_field: str = block_field(offset=10, type=String(length=8))

        scaled_field: float = block_field(
            offset=20,
            type=UInt16(),
            transform=["scale:0.1", "minus:40"],
            unit="°C"
        )

    schema = FieldTypesBlock.to_schema()

    # Check field types
    assert isinstance(schema.fields[0].type, UInt16)
    assert isinstance(schema.fields[1].type, UInt32)
    assert isinstance(schema.fields[2].type, Int32)
    assert isinstance(schema.fields[3].type, String)

    # Check transforms
    scaled = schema.fields[4]
    assert scaled.transform == ("scale:0.1", "minus:40")
    assert scaled.unit == "°C"


def test_optional_and_protocol_version():
    """Test optional fields and protocol version requirements."""

    @block_schema(block_id=9005, name="OPTIONAL_FIELDS")
    @dataclass
    class OptionalFieldsBlock:
        """Optional fields test."""

        required_field: int = block_field(
            offset=0,
            type=UInt16(),
            required=True
        )

        optional_field: int = block_field(
            offset=2,
            type=UInt16(),
            required=False
        )

        v2001_field: int = block_field(
            offset=4,
            type=UInt32(),
            min_protocol_version=2001
        )

    schema = OptionalFieldsBlock.to_schema()

    assert schema.fields[0].required is True
    assert schema.fields[1].required is False
    assert schema.fields[2].min_protocol_version == 2001


def test_schema_immutability():
    """Test that generated schema is immutable (frozen)."""

    @block_schema(block_id=9006, name="IMMUTABLE_TEST")
    @dataclass
    class ImmutableBlock:
        """Immutable test."""

        field1: int = block_field(offset=0, type=UInt16())

    schema = ImmutableBlock.to_schema()

    # Should be frozen
    import dataclasses
    with pytest.raises(dataclasses.FrozenInstanceError):
        schema.name = "HACKED"

    with pytest.raises(dataclasses.FrozenInstanceError):
        schema.fields[0].offset = 999


def test_multiple_blocks_independent():
    """Test multiple declarative blocks are independent."""

    @block_schema(block_id=9007, name="BLOCK_A")
    @dataclass
    class BlockA:
        """Block A."""
        field_a: int = block_field(offset=0, type=UInt16())

    @block_schema(block_id=9008, name="BLOCK_B")
    @dataclass
    class BlockB:
        """Block B."""
        field_b: int = block_field(offset=0, type=UInt32())

    schema_a = BlockA.to_schema()
    schema_b = BlockB.to_schema()

    assert schema_a.block_id == 9007
    assert schema_b.block_id == 9008
    assert schema_a.fields[0].name == "field_a"
    assert schema_b.fields[0].name == "field_b"


def test_non_block_fields_ignored():
    """Test that non-block fields are ignored during schema generation."""

    @block_schema(block_id=9009, name="MIXED_FIELDS")
    @dataclass
    class MixedFieldsBlock:
        """Mixed fields test."""

        # Block field
        block_field1: int = block_field(offset=0, type=UInt16())

        # Regular dataclass field (not a block field)
        runtime_value: int = 0

        # Block field
        block_field2: int = block_field(offset=2, type=UInt16())

    schema = MixedFieldsBlock.to_schema()

    # Should only have 2 fields (block fields), runtime_value ignored
    assert len(schema.fields) == 2
    assert schema.fields[0].name == "block_field1"
    assert schema.fields[1].name == "block_field2"


def test_block_schema_requires_dataclass():
    """Test that @block_schema raises clear error if @dataclass is missing."""

    with pytest.raises(TypeError) as exc_info:
        @block_schema(block_id=9010, name="NOT_DATACLASS")
        class NotDataclassBlock:
            """Missing @dataclass decorator."""
            field1: int = block_field(offset=0, type=UInt16())

    # Check error message is helpful
    error_msg = str(exc_info.value)
    assert "@block_schema can only be applied to dataclasses" in error_msg
    assert "Add @dataclass decorator" in error_msg
    assert "NotDataclassBlock" in error_msg
