"""Simple integration test for V2 parser

Tests the core V2 parser without complex dependencies.
"""

from power_sdk.protocol.v2.datatypes import Int16, UInt16
from power_sdk.protocol.v2.parser import V2Parser
from power_sdk.protocol.v2.schema import BlockSchema, Field


def test_grid_info_parsing():
    """Test parsing Block 1300 (Grid info)."""

    print("=" * 60)
    print("V2 Parser Integration Test - Block 1300 (Grid Info)")
    print("=" * 60)

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

    print("\n1. Schema created:")
    print(f"   Block ID: {schema.block_id}")
    print(f"   Name: {schema.name}")
    print(f"   Fields: {len(schema.fields)}")

    # Create parser and register schema
    parser = V2Parser()
    parser.register_schema(schema)

    print("\n2. Parser initialized:")
    print(f"   Registered schemas: {parser.list_schemas()}")

    # Create mock data (normalized Modbus payload)
    # Frequency: 500 (50.0 Hz)
    # Voltage: 2300 (230.0 V)
    # Current: -52 (5.2 A)
    data = bytearray(32)
    data[0:2] = bytes([0x01, 0xF4])  # offset 0: frequency = 500
    data[28:30] = bytes([0x08, 0xFC])  # offset 28: voltage = 2300
    data[30:32] = bytes([0xFF, 0xCC])  # offset 30: current = -52

    print("\n3. Mock data created:")
    print(f"   Data length: {len(data)} bytes")
    print(f"   Data (hex): {bytes(data).hex()}")

    # Parse block
    parsed = parser.parse_block(1300, bytes(data))

    print("\n4. Block parsed successfully:")
    print(f"   Block ID: {parsed.block_id}")
    print(f"   Name: {parsed.name}")
    print(f"   Timestamp: {parsed.timestamp}")
    print(f"   Fields parsed: {len(parsed.values)}")

    print("\n5. Parsed values:")
    for field_name, value in parsed.values.items():
        field = schema.get_field(field_name)
        unit = field.unit if field else ""
        print(f"   {field_name}: {value} {unit}")

    # Validate results
    print("\n6. Validation:")
    assert parsed.values["frequency"] == 50.0, "Frequency mismatch"
    print(f"   ✓ Frequency: {parsed.values['frequency']} Hz")

    assert parsed.values["phase_0_voltage"] == 230.0, "Voltage mismatch"
    print(f"   ✓ Voltage: {parsed.values['phase_0_voltage']} V")

    assert parsed.values["phase_0_current"] == 5.2, "Current mismatch"
    print(f"   ✓ Current: {parsed.values['phase_0_current']} A")

    # Test to_dict()
    dict_output = parsed.to_dict()
    print("\n7. Dictionary output:")
    print(f"   {dict_output}")

    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)

    print("\nKey achievements:")
    print("✓ Schema definition works")
    print("✓ Transform pipeline works (scale, abs)")
    print("✓ Parser correctly extracts fields")
    print("✓ Validation passes")
    print("✓ Output formats work (values dict, to_dict())")


if __name__ == "__main__":
    test_grid_info_parsing()

