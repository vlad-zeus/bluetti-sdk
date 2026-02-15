"""Smoke tests for Wave D Batch 2 blocks - schema availability and basic parsing."""

from bluetti_sdk.protocol.v2.parser import V2Parser
from bluetti_sdk.schemas import (
    BLOCK_15750_SCHEMA,
    BLOCK_17000_SCHEMA,
    BLOCK_19365_SCHEMA,
    BLOCK_19425_SCHEMA,
    BLOCK_19485_SCHEMA,
    new_registry_with_builtins,
)


def test_wave_d_batch2_schemas_available():
    """Verify all Wave D Batch 2 schemas are importable and have correct block IDs."""
    assert BLOCK_15750_SCHEMA.block_id == 15750
    assert BLOCK_15750_SCHEMA.name == "DC_HUB_SETTINGS"

    assert BLOCK_17000_SCHEMA.block_id == 17000
    assert BLOCK_17000_SCHEMA.name == "ATS_INFO"

    assert BLOCK_19365_SCHEMA.block_id == 19365
    assert BLOCK_19365_SCHEMA.name == "AT1_TIMER_EVENT_A"

    assert BLOCK_19425_SCHEMA.block_id == 19425
    assert BLOCK_19425_SCHEMA.name == "AT1_TIMER_EVENT_B"

    assert BLOCK_19485_SCHEMA.block_id == 19485
    assert BLOCK_19485_SCHEMA.name == "AT1_TIMER_EVENT_C"


def test_wave_d_batch2_schemas_registered():
    """Verify Wave D Batch 2 schemas are auto-registered in new registries."""
    registry = new_registry_with_builtins()

    # Check all 5 blocks are registered
    assert registry.get(15750) == BLOCK_15750_SCHEMA
    assert registry.get(17000) == BLOCK_17000_SCHEMA
    assert registry.get(19365) == BLOCK_19365_SCHEMA
    assert registry.get(19425) == BLOCK_19425_SCHEMA
    assert registry.get(19485) == BLOCK_19485_SCHEMA

    # Verify total count
    # Wave A/B/C: 20 + Wave D Batches 1-4: 20 = 40
    all_blocks = registry.list_blocks()
    assert len(all_blocks) == 40


def test_wave_d_batch2_minimal_parseability():
    """Verify Wave D Batch 2 blocks can be parsed by V2Parser with minimal payloads."""
    parser = V2Parser()
    for schema in [
        BLOCK_15750_SCHEMA,
        BLOCK_17000_SCHEMA,
        BLOCK_19365_SCHEMA,
        BLOCK_19425_SCHEMA,
        BLOCK_19485_SCHEMA,
    ]:
        parser.register_schema(schema)

    for schema in [
        BLOCK_15750_SCHEMA,
        BLOCK_17000_SCHEMA,
        BLOCK_19365_SCHEMA,
        BLOCK_19425_SCHEMA,
        BLOCK_19485_SCHEMA,
    ]:
        payload = bytes([0] * schema.min_length)
        parsed = parser.parse_block(schema.block_id, payload, validate=True)
        assert parsed.block_id == schema.block_id
        assert parsed.name == schema.name
