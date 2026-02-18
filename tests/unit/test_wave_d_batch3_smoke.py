"""Smoke tests for Wave D Batch 3 blocks - schema availability and basic parsing."""

from power_sdk.plugins.bluetti.v2.protocol.parser import V2Parser
from power_sdk.plugins.bluetti.v2.schemas import (
    BLOCK_14500_SCHEMA,
    BLOCK_14700_SCHEMA,
    BLOCK_15500_SCHEMA,
    BLOCK_15600_SCHEMA,
    BLOCK_17100_SCHEMA,
    new_registry_with_builtins,
)


def test_wave_d_batch3_schemas_available():
    """Verify all Wave D Batch 3 schemas are importable and have correct block IDs."""
    assert BLOCK_14500_SCHEMA.block_id == 14500
    assert BLOCK_14500_SCHEMA.name == "SMART_PLUG_INFO"

    assert BLOCK_14700_SCHEMA.block_id == 14700
    assert BLOCK_14700_SCHEMA.name == "SMART_PLUG_SETTINGS"

    assert BLOCK_15500_SCHEMA.block_id == 15500
    assert BLOCK_15500_SCHEMA.name == "DC_DC_INFO"

    assert BLOCK_15600_SCHEMA.block_id == 15600
    assert BLOCK_15600_SCHEMA.name == "DC_DC_SETTINGS"

    assert BLOCK_17100_SCHEMA.block_id == 17100
    assert BLOCK_17100_SCHEMA.name == "AT1_BASE_INFO"


def test_wave_d_batch3_schemas_registered():
    """Verify Wave D Batch 3 schemas are auto-registered in new registries."""
    registry = new_registry_with_builtins()

    # Check all 5 blocks are registered
    assert registry.get(14500) == BLOCK_14500_SCHEMA
    assert registry.get(14700) == BLOCK_14700_SCHEMA
    assert registry.get(15500) == BLOCK_15500_SCHEMA
    assert registry.get(15600) == BLOCK_15600_SCHEMA
    assert registry.get(17100) == BLOCK_17100_SCHEMA

    # Verify total count
    # Wave A/B/C: 20 + Wave D Batches 1-5: 25 = 45
    all_blocks = registry.list_blocks()
    assert len(all_blocks) == 45


def test_wave_d_batch3_minimal_parseability():
    """Verify Wave D Batch 3 blocks can be parsed by V2Parser with minimal payloads."""
    parser = V2Parser()
    for schema in [
        BLOCK_14500_SCHEMA,
        BLOCK_14700_SCHEMA,
        BLOCK_15500_SCHEMA,
        BLOCK_15600_SCHEMA,
        BLOCK_17100_SCHEMA,
    ]:
        parser.register_schema(schema)

    for schema in [
        BLOCK_14500_SCHEMA,
        BLOCK_14700_SCHEMA,
        BLOCK_15500_SCHEMA,
        BLOCK_15600_SCHEMA,
        BLOCK_17100_SCHEMA,
    ]:
        payload = bytes([0] * schema.min_length)
        parsed = parser.parse_block(schema.block_id, payload, validate=True)
        assert parsed.block_id == schema.block_id
        assert parsed.name == schema.name

