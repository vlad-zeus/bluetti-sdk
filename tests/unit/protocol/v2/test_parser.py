"""Unit tests for V2 parser."""

import pytest
from power_sdk.plugins.bluetti.v2.protocol.datatypes import Int16, UInt16
from power_sdk.plugins.bluetti.v2.protocol.parser import V2Parser
from power_sdk.plugins.bluetti.v2.protocol.schema import (
    ArrayField,
    BlockSchema,
    Field,
    PackedField,
    SubField,
)


def test_basic_field_parsing():
    """Test parsing a simple field."""
    schema = BlockSchema(
        block_id=100,
        name="TEST_BLOCK",
        description="Test block",
        min_length=4,
        fields=[
            Field("soc", offset=0, type=UInt16(), unit="%"),
            Field(
                "voltage", offset=2, type=UInt16(), transform=["scale:0.1"], unit="V"
            ),
        ],
    )

    parser = V2Parser()
    parser.register_schema(schema)

    # SOC=85, voltage=520 (52.0V)
    data = bytes([0x00, 0x55, 0x02, 0x08])

    parsed = parser.parse_block(100, data)

    assert parsed.block_id == 100
    assert parsed.name == "TEST_BLOCK"
    assert parsed.values["soc"] == 85
    assert parsed.values["voltage"] == pytest.approx(52.0)


def test_array_field_parsing():
    """Test parsing an array field."""
    schema = BlockSchema(
        block_id=101,
        name="ARRAY_TEST",
        description="Array test",
        min_length=8,
        fields=[
            ArrayField(
                name="temperatures",
                offset=0,
                count=4,
                stride=2,
                item_type=UInt16(),
                transform=["minus:40"],
                unit="C",
            )
        ],
    )

    parser = V2Parser()
    parser.register_schema(schema)

    # Temps: 80, 75, 70, 65 (raw) → 40, 35, 30, 25 (C)
    data = bytes(
        [
            0x00,
            80,  # 40C
            0x00,
            75,  # 35C
            0x00,
            70,  # 30C
            0x00,
            65,  # 25C
        ]
    )

    parsed = parser.parse_block(101, data)

    assert parsed.values["temperatures"] == [40, 35, 30, 25]


def test_packed_field_parsing():
    """Test parsing a packed field (cell voltage + status)."""
    schema = BlockSchema(
        block_id=102,
        name="PACKED_TEST",
        description="Packed field test",
        min_length=4,
        fields=[
            PackedField(
                name="cells",
                offset=0,
                count=2,
                stride=2,
                base_type=UInt16(),
                fields=[
                    SubField(
                        "voltage", bits="0:14", transform=["scale:0.001"], unit="V"
                    ),
                    SubField("status", bits="14:16"),
                ],
            )
        ],
    )

    parser = V2Parser()
    parser.register_schema(schema)

    # Cell 0: voltage=3245mV, status=2
    # Cell 1: voltage=3256mV, status=1
    data = bytes(
        [
            0x80 | 0x0C,
            0xAD,  # 0x8CAD = 0b10001100 10101101 → status=2, voltage=3245
            0x40 | 0x0C,
            0xB8,  # 0x4CB8 = 0b01001100 10111000 → status=1, voltage=3256
        ]
    )

    parsed = parser.parse_block(102, data)

    cells = parsed.values["cells"]
    assert len(cells) == 2

    # Cell 0
    assert cells[0]["voltage"] == pytest.approx(3.245)
    assert cells[0]["status"] == 2

    # Cell 1
    assert cells[1]["voltage"] == pytest.approx(3.256)
    assert cells[1]["status"] == 1


def test_validation_strict_mode():
    """Test strict validation mode - should raise exception on validation failure."""
    from power_sdk.errors import ParserError

    schema = BlockSchema(
        block_id=103,
        name="STRICT_TEST",
        description="Strict validation test",
        min_length=4,
        fields=[
            Field("value1", offset=0, type=UInt16(), required=True),
            Field("value2", offset=2, type=UInt16(), required=True),
        ],
        strict=True,
    )

    parser = V2Parser()
    parser.register_schema(schema)

    # Data too short - should raise ParserError in strict mode
    data_short = bytes([0x00, 0x01])

    with pytest.raises(ParserError, match="validation failed"):
        parser.parse_block(103, data_short, validate=True)


def test_validation_optional_fields():
    """Test optional fields in validation."""
    schema = BlockSchema(
        block_id=104,
        name="OPTIONAL_TEST",
        description="Optional fields test",
        min_length=2,
        fields=[
            Field("required_field", offset=0, type=UInt16(), required=True),
            Field("optional_field", offset=2, type=UInt16(), required=False),
        ],
        strict=False,
    )

    parser = V2Parser()
    parser.register_schema(schema)

    # Only required field present
    data = bytes([0x00, 0x42])

    parsed = parser.parse_block(104, data, validate=True)

    assert parsed.values["required_field"] == 66
    assert parsed.values["optional_field"] is None

    # Validation should pass
    assert parsed.validation is not None
    assert parsed.validation.valid
    assert "optional_field" in parsed.validation.missing_fields


def test_protocol_version_gating():
    """Test min_protocol_version field gating."""
    schema = BlockSchema(
        block_id=105,
        name="VERSION_TEST",
        description="Protocol version test",
        min_length=4,
        fields=[
            Field("always_present", offset=0, type=UInt16(), required=True),
            Field(
                "new_field",
                offset=2,
                type=UInt16(),
                required=False,
                min_protocol_version=2003,
            ),
        ],
    )

    parser = V2Parser()
    parser.register_schema(schema)

    data = bytes([0x00, 0x01, 0x00, 0x02])

    # Old protocol version - new_field should be None
    parsed_old = parser.parse_block(105, data, protocol_version=2000)
    assert parsed_old.values["always_present"] == 1
    assert parsed_old.values["new_field"] is None

    # New protocol version - new_field should be parsed
    parsed_new = parser.parse_block(105, data, protocol_version=2003)
    assert parsed_new.values["always_present"] == 1
    assert parsed_new.values["new_field"] == 2


def test_to_dict():
    """Test ParsedRecord.to_dict()."""
    schema = BlockSchema(
        block_id=106,
        name="DICT_TEST",
        description="Dict output test",
        min_length=4,
        fields=[
            Field("soc", offset=0, type=UInt16()),
            Field("voltage", offset=2, type=UInt16(), transform=["scale:0.1"]),
        ],
    )

    parser = V2Parser()
    parser.register_schema(schema)

    data = bytes([0x00, 0x50, 0x02, 0x08])  # SOC=80, voltage=52.0V

    parsed = parser.parse_block(106, data)
    dict_output = parsed.to_dict()

    assert dict_output == {"soc": 80, "voltage": pytest.approx(52.0)}


def test_grid_voltage_frequency_example():
    """Test real-world example: Block 1300 grid voltage/frequency."""
    schema = BlockSchema(
        block_id=1300,
        name="INV_GRID_INFO",
        description="Grid input monitoring",
        min_length=32,
        fields=[
            Field(
                "frequency", offset=0, type=UInt16(), transform=["scale:0.1"], unit="Hz"
            ),
            Field(
                "phase_0_voltage",
                offset=28,
                type=UInt16(),
                transform=["scale:0.1"],
                unit="V",
            ),
            Field(
                "phase_0_current",
                offset=30,
                type=Int16(),
                transform=["abs", "scale:0.1"],
                unit="A",
            ),
        ],
    )

    parser = V2Parser()
    parser.register_schema(schema)

    # Frequency: 500 (50.0 Hz)
    # Voltage: 2300 (230.0V)
    # Current: -52 (5.2A)
    data = bytearray(32)
    data[0:2] = bytes([0x01, 0xF4])  # 500 → 50.0 Hz
    data[28:30] = bytes([0x08, 0xFC])  # 2300 → 230.0V
    data[30:32] = bytes([0xFF, 0xCC])  # -52 → 5.2A

    parsed = parser.parse_block(1300, bytes(data))

    assert parsed.values["frequency"] == pytest.approx(50.0)
    assert parsed.values["phase_0_voltage"] == pytest.approx(230.0)
    assert parsed.values["phase_0_current"] == pytest.approx(5.2)


def test_parser_list_schemas():
    """Test listing registered schemas."""
    parser = V2Parser()

    schema1 = BlockSchema(
        block_id=100, name="BLOCK_A", description="Block A", min_length=10, fields=[]
    )

    schema2 = BlockSchema(
        block_id=200, name="BLOCK_B", description="Block B", min_length=20, fields=[]
    )

    parser.register_schema(schema1)
    parser.register_schema(schema2)

    schemas = parser.list_schemas()

    assert schemas == {100: "BLOCK_A", 200: "BLOCK_B"}


def test_parser_duplicate_registration_conflict_raises():
    """Registering same block_id with a different name raises ValueError."""
    parser = V2Parser()

    schema1 = BlockSchema(
        block_id=100, name="BLOCK_A", description="Block A", min_length=10, fields=[]
    )

    schema2 = BlockSchema(
        block_id=100, name="BLOCK_B", description="Block B", min_length=20, fields=[]
    )

    parser.register_schema(schema1)

    with pytest.raises(ValueError, match="schema conflict"):
        parser.register_schema(schema2)


def test_parser_duplicate_registration_same_name_is_idempotent():
    """Registering same block_id with the same name is a no-op (idempotent)."""
    parser = V2Parser()

    schema = BlockSchema(
        block_id=100, name="BLOCK_A", description="Block A", min_length=10, fields=[]
    )

    parser.register_schema(schema)
    parser.register_schema(schema)  # should not raise

    assert parser.list_schemas() == {100: "BLOCK_A"}


def test_parser_unknown_block():
    """Test parsing unknown block ID raises error."""
    parser = V2Parser()

    with pytest.raises(ValueError, match="No schema registered"):
        parser.parse_block(999, bytes([0x00, 0x01]))
