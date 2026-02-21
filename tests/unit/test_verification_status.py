"""Tests for schema verification status metadata."""

from power_sdk.plugins.bluetti.v2.schemas import new_registry_with_builtins


def test_all_builtin_schemas_have_verification_status():
    """Verify all builtin schemas include verification_status metadata."""
    registry = new_registry_with_builtins()
    all_block_ids = registry.list_blocks()

    missing_status = []

    for block_id in all_block_ids:
        schema = registry.get(block_id)
        if schema and schema.verification_status is None:
            missing_status.append(block_id)

    assert not missing_status, (
        f"Schemas missing verification_status: {missing_status}. "
        "All schemas must specify verification status."
    )


def test_verification_status_values():
    """Verify all verification_status values are valid."""
    registry = new_registry_with_builtins()
    all_block_ids = registry.list_blocks()

    valid_statuses = {"verified_reference", "device_verified", "inferred", "partial"}
    invalid_schemas = []

    for block_id in all_block_ids:
        schema = registry.get(block_id)
        if schema and schema.verification_status not in valid_statuses:
            invalid_schemas.append((block_id, schema.verification_status))

    assert not invalid_schemas, (
        f"Schemas with invalid verification_status: {invalid_schemas}. "
        f"Valid values: {valid_statuses}"
    )


def test_verified_reference_count():
    """verified_reference blocks are exactly all registered blocks minus partial ones.

    Using a set-based assertion means this test remains valid when new
    verified_reference blocks are added — only the partial set needs updating.
    """
    registry = new_registry_with_builtins()
    all_block_ids = set(registry.list_blocks())

    # Blocks whose verification is incomplete; update this set when a block's
    # status changes.  Do NOT add new blocks here unless they are genuinely
    # partial — use verified_reference or device_verified instead.
    # 15700 added: per-port status fields (offsets 36-37, 42-43, 48-49, 54-55, 60-61)
    # were absent and have been added via gap analysis; exact semantics are inferred.
    partial_block_ids = {1700, 2200, 15600, 15700, 15750, 17400}

    verified_reference = {
        block_id
        for block_id in all_block_ids
        if registry.get(block_id).verification_status == "verified_reference"
    }
    non_partial = all_block_ids - partial_block_ids

    assert verified_reference == non_partial, (
        f"verified_reference blocks do not match all_blocks - partial_blocks.\n"
        f"  Unexpected partial (in verified_reference): "
        f"{verified_reference - non_partial}\n"
        f"  Missing from verified_reference: {non_partial - verified_reference}"
    )


def test_inferred_count():
    """Verify expected number of inferred schemas."""
    registry = new_registry_with_builtins()
    all_block_ids = registry.list_blocks()

    inferred = [
        block_id
        for block_id in all_block_ids
        if registry.get(block_id).verification_status == "inferred"
    ]

    # Remaining inferred blocks after partial/reference upgrades
    assert len(inferred) == 0, f"Expected 0 inferred schemas, found {len(inferred)}"


def test_verification_status_distribution():
    """Verify verification status distribution across all schemas.

    The partial set is fixed; everything else must be verified_reference.
    Adding new verified blocks does not require updating this test.
    """
    registry = new_registry_with_builtins()
    all_block_ids = set(registry.list_blocks())

    # 15700 added: per-port status fields inferred from structural gap analysis
    partial_block_ids = {1700, 2200, 15600, 15700, 15750, 17400}

    status_counts: dict[str | None, int] = {}
    for block_id in all_block_ids:
        schema = registry.get(block_id)
        status = schema.verification_status if schema else None
        status_counts[status] = status_counts.get(status, 0) + 1

    # No inferred or device_verified blocks exist yet.
    assert status_counts.get("inferred", 0) == 0
    assert status_counts.get("device_verified", 0) == 0
    # Partial set is exactly the known ambiguous blocks.
    assert status_counts.get("partial", 0) == len(partial_block_ids), (
        f"Expected {len(partial_block_ids)} partial blocks, "
        f"got {status_counts.get('partial', 0)}"
    )
    # All non-partial blocks must be verified_reference.
    expected_verified = len(all_block_ids) - len(partial_block_ids)
    assert status_counts.get("verified_reference", 0) == expected_verified, (
        f"Expected {expected_verified} verified_reference blocks, "
        f"got {status_counts.get('verified_reference', 0)}"
    )


def test_wave_a_blocks_verified_reference():
    """Verify Wave A blocks are marked verified_reference."""
    registry = new_registry_with_builtins()

    # Wave A/B reference blocks — block 1700 and 2200 excluded (partial).
    wave_a_blocks = [100, 720, 1100, 1300, 1400, 1500, 2000, 2400]

    for block_id in wave_a_blocks:
        schema = registry.get(block_id)
        assert schema is not None, f"Block {block_id} not registered"
        assert schema.verification_status == "verified_reference", (
            f"Block {block_id} should be verified_reference, "
            f"got {schema.verification_status}"
        )


def test_wave_d_blocks_inferred():
    """Verify no Wave D blocks remain in inferred status."""
    registry = new_registry_with_builtins()

    inferred_blocks = [
        block_id
        for block_id in registry.list_blocks()
        if registry.get(block_id).verification_status == "inferred"
    ]
    assert not inferred_blocks, (
        f"Inferred blocks should be empty, got {inferred_blocks}"
    )


def test_partial_blocks():
    """Verify blocks upgraded to partial status (Commit 3)."""
    registry = new_registry_with_builtins()

    # Blocks with partial verification:
    # parse method confirmed, semantics/offsets deferred.
    # Note: 18000 upgraded to verified_reference after Agent B verification
    # Note: 18400/18500/18600/26001 are verified_reference after Agent C verification
    # Note: 14700 upgraded to verified_reference after Agent D deep dive
    # Note: 18300 upgraded to verified_reference after Agent G deep dive
    # Note: 15500, 17100 upgraded to verified_reference after Final Closure Sprint
    # Note: 1700 downgraded to partial — Float32 metering fields use raw_bits encoding
    # Note: 2200 downgraded to partial — inv_freq scale ambiguity
    # Note: 15700 downgraded to partial — per-port status fields added via gap analysis
    partial_blocks = [
        1700,
        2200,
        15600,
        15700,
        15750,
        17400,
    ]

    for block_id in partial_blocks:
        schema = registry.get(block_id)
        assert schema is not None, f"Block {block_id} not registered"
        assert schema.verification_status == "partial", (
            f"Block {block_id} should be partial, got {schema.verification_status}"
        )


def test_agent_c_blocks_verified_reference():
    """Verify Agent C blocks (18400/18500/18600/26001) are verified_reference."""
    registry = new_registry_with_builtins()

    # Blocks verified by Agent C (field structure proven from reference)
    agent_c_blocks = [18400, 18500, 18600, 26001]

    for block_id in agent_c_blocks:
        schema = registry.get(block_id)
        assert schema is not None, f"Block {block_id} not registered"
        assert schema.verification_status == "verified_reference", (
            "Block "
            f"{block_id} should be verified_reference, "
            f"got {schema.verification_status}"
        )
