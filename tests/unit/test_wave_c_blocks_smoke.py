"""Smoke tests for Wave C (P2 monitoring) block schemas.

Tests verify:
- Schema registration in built-in catalog
- Schema import accessibility
- Basic parseability of minimal payloads
- Total registered block count
"""


from power_sdk.plugins.bluetti.v2.protocol.parser import V2Parser
from power_sdk.plugins.bluetti.v2.schemas import (
    BLOCK_720_SCHEMA,
    BLOCK_1700_SCHEMA,
    BLOCK_3500_SCHEMA,
    BLOCK_3600_SCHEMA,
    BLOCK_6300_SCHEMA,
    BLOCK_12161_SCHEMA,
    list_blocks,
    new_registry_with_builtins,
)


def test_all_wave_c_blocks_registered():
    """Verify all Wave C blocks are registered in built-in catalog."""
    # Force population of built-in catalog
    _ = new_registry_with_builtins()

    blocks = list_blocks()
    wave_c_blocks = {720, 1700, 3500, 3600, 6300, 12161}
    assert wave_c_blocks.issubset(
        blocks
    ), f"Missing Wave C blocks: {wave_c_blocks - blocks}"


def test_wave_c_blocks_accessible_via_import():
    """Verify all Wave C blocks can be imported directly."""
    # All imports should succeed without errors
    assert BLOCK_720_SCHEMA.block_id == 720
    assert BLOCK_1700_SCHEMA.block_id == 1700
    assert BLOCK_3500_SCHEMA.block_id == 3500
    assert BLOCK_3600_SCHEMA.block_id == 3600
    assert BLOCK_6300_SCHEMA.block_id == 6300
    assert BLOCK_12161_SCHEMA.block_id == 12161


def test_wave_c_blocks_minimal_parseability():
    """Verify Wave C blocks can be parsed by V2Parser with minimal payloads."""
    parser = V2Parser()
    for schema in [
        BLOCK_720_SCHEMA,
        BLOCK_1700_SCHEMA,
        BLOCK_3500_SCHEMA,
        BLOCK_3600_SCHEMA,
        BLOCK_6300_SCHEMA,
        BLOCK_12161_SCHEMA,
    ]:
        parser.register_schema(schema)

    for schema in [
        BLOCK_720_SCHEMA,
        BLOCK_1700_SCHEMA,
        BLOCK_3500_SCHEMA,
        BLOCK_3600_SCHEMA,
        BLOCK_6300_SCHEMA,
        BLOCK_12161_SCHEMA,
    ]:
        payload = bytes([0] * schema.min_length)
        parsed = parser.parse_block(schema.block_id, payload, validate=True)
        assert parsed.block_id == schema.block_id
        assert parsed.name == schema.name


def test_total_registered_blocks_count():
    """Verify total number of registered blocks after Wave C."""
    _ = new_registry_with_builtins()
    blocks = list_blocks()

    # Wave A: 100, 1100, 1300, 1400, 1500, 6000, 6100 (7 blocks)
    # Wave B: 2000, 2200, 2400, 7000, 11000, 12002, 19000 (7 blocks)
    # Wave C: 720, 1700, 3500, 3600, 6300, 12161 (6 blocks)
    # Wave D Batch 1: 19100, 19200, 19300, 19305, 40127 (5 blocks)
    # Wave D Batch 2: 15750, 17000, 19365, 19425, 19485 (5 blocks)
    # Wave D Batch 3: 14500, 14700, 15500, 15600, 17100 (5 blocks)
    # Wave D Batch 4: 15700, 17400, 18000, 18300, 26001 (5 blocks)
    # Wave D Batch 5: 18400, 18500, 18600, 29770, 29772 (5 blocks)
    # Total: 45 blocks
    assert len(blocks) == 45, f"Expected 45 blocks, got {len(blocks)}: {sorted(blocks)}"

