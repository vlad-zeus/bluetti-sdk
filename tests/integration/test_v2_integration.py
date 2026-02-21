"""Simple integration test for V2 parser

Tests the core V2 parser without complex dependencies.
"""

from power_sdk.plugins.bluetti.v2.protocol.datatypes import Int16, UInt16
from power_sdk.plugins.bluetti.v2.protocol.parser import V2Parser
from power_sdk.plugins.bluetti.v2.protocol.schema import BlockSchema, Field


def test_grid_info_parsing():
    """Test parsing Block 1300 (Grid info)."""

    # Create schema for Block 1300
    schema = BlockSchema(
        block_id=1300,
        name="INV_GRID_INFO",
        description="Grid input monitoring",
        min_length=32,
        fields=[
            Field(
                name="frequency",
                offset=0,
                type=UInt16(),
                transform=["scale:0.1"],
                unit="Hz",
                required=True,
                description="Grid frequency",
            ),
            Field(
                name="phase_0_voltage",
                offset=28,
                type=UInt16(),
                transform=["scale:0.1"],
                unit="V",
                required=True,
                description="Phase 0 voltage",
            ),
            Field(
                name="phase_0_current",
                offset=30,
                type=Int16(),
                transform=["abs", "scale:0.1"],
                unit="A",
                required=True,
                description="Phase 0 current",
            ),
        ],
        strict=True,
        schema_version="1.0.0",
    )

    # Create parser and register schema
    parser = V2Parser()
    parser.register_schema(schema)

    # Create mock data (normalized Modbus payload)
    # Frequency: 500 (50.0 Hz)
    # Voltage: 2300 (230.0 V)
    # Current: -52 (5.2 A)
    data = bytearray(32)
    data[0:2] = bytes([0x01, 0xF4])  # offset 0: frequency = 500
    data[28:30] = bytes([0x08, 0xFC])  # offset 28: voltage = 2300
    data[30:32] = bytes([0xFF, 0xCC])  # offset 30: current = -52

    # Parse block
    parsed = parser.parse_block(1300, bytes(data))

    # Validate results
    assert parsed.values["frequency"] == 50.0, "Frequency mismatch"
    assert parsed.values["phase_0_voltage"] == 230.0, "Voltage mismatch"
    assert parsed.values["phase_0_current"] == 5.2, "Current mismatch"

    # Test to_dict()
    dict_output = parsed.to_dict()
    assert isinstance(dict_output, dict)
