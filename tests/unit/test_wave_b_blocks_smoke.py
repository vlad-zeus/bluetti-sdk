"""Smoke tests for Wave B blocks (2000, 2200, 2400, 7000, 11000, 12002, 19000).

Tests that new schemas are properly registered and accessible.
"""


def test_all_wave_b_blocks_registered():
    """Test that all Wave B blocks are registered in built-in catalog."""
    from bluetti_sdk.schemas import list_blocks, new_registry_with_builtins

    # Force population of built-in catalog
    _ = new_registry_with_builtins()

    blocks = list_blocks()

    # Verify all Wave B blocks are present
    wave_b_blocks = {2000, 2200, 2400, 7000, 11000, 12002, 19000}
    assert wave_b_blocks.issubset(
        blocks
    ), f"Missing Wave B blocks: {wave_b_blocks - set(blocks)}"


def test_wave_b_blocks_accessible_via_get():
    """Test that Wave B blocks are accessible via get()."""
    from bluetti_sdk.schemas import get

    # Block 2000
    schema_2000 = get(2000)
    assert schema_2000 is not None
    assert schema_2000.block_id == 2000
    assert schema_2000.name == "INV_BASE_SETTINGS"

    # Block 2200
    schema_2200 = get(2200)
    assert schema_2200 is not None
    assert schema_2200.block_id == 2200
    assert schema_2200.name == "INV_ADV_SETTINGS"

    # Block 2400
    schema_2400 = get(2400)
    assert schema_2400 is not None
    assert schema_2400.block_id == 2400
    assert schema_2400.name == "CERT_SETTINGS"

    # Block 7000
    schema_7000 = get(7000)
    assert schema_7000 is not None
    assert schema_7000.block_id == 7000
    assert schema_7000.name == "PACK_SETTINGS"

    # Block 11000
    schema_11000 = get(11000)
    assert schema_11000 is not None
    assert schema_11000.block_id == 11000
    assert schema_11000.name == "IOT_INFO"

    # Block 12002
    schema_12002 = get(12002)
    assert schema_12002 is not None
    assert schema_12002.block_id == 12002
    assert schema_12002.name == "IOT_WIFI_SETTINGS"

    # Block 19000
    schema_19000 = get(19000)
    assert schema_19000 is not None
    assert schema_19000.block_id == 19000
    assert schema_19000.name == "SOC_SETTINGS"


def test_wave_b_blocks_in_instance_registry():
    """Test that Wave B blocks are copied to instance registries."""
    from bluetti_sdk.schemas import new_registry_with_builtins

    registry = new_registry_with_builtins()

    # Verify all Wave B blocks are in instance registry
    for block_id in [2000, 2200, 2400, 7000, 11000, 12002, 19000]:
        schema = registry.get(block_id)
        assert schema is not None, f"Block {block_id} missing from instance registry"
        assert schema.block_id == block_id


def test_total_registered_blocks_count():
    """Test expected total number of registered blocks."""
    from bluetti_sdk.schemas import list_blocks

    blocks = list_blocks()

    # Wave A: 100, 1100, 1300, 1400, 1500, 6000, 6100 (7 blocks)
    # Wave B: 2000, 2200, 2400, 7000, 11000, 12002, 19000 (7 blocks)
    # Wave C: 720, 1700, 3500, 3600, 6300, 12161 (6 blocks)
    # Wave D Batch 1: 19100, 19200, 19300, 19305, 40127 (5 blocks)
    # Total: 25 blocks
    assert len(blocks) == 25, f"Expected 25 blocks, got {len(blocks)}: {sorted(blocks)}"
