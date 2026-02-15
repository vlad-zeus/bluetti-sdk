"""Tests for GroupReader service."""

from unittest.mock import Mock

import pytest
from bluetti_sdk.client_services.group_reader import GroupReader, ReadGroupResult
from bluetti_sdk.devices.profiles import get_device_profile
from bluetti_sdk.models.types import BlockGroup
from bluetti_sdk.protocol.v2.types import ParsedBlock


@pytest.fixture
def test_profile():
    """Get test device profile."""
    return get_device_profile("EL100V2")


@pytest.fixture
def mock_read_block():
    """Create mock read_block function."""
    return Mock(
        return_value=ParsedBlock(
            block_id=100,
            name="TEST_BLOCK",
            values={"field1": 100},
            raw=b"\x00\x64",
            length=2,
        )
    )


@pytest.fixture
def group_reader(test_profile, mock_read_block):
    """Create GroupReader instance."""
    return GroupReader(test_profile, mock_read_block)


def test_group_reader_creation(test_profile, mock_read_block):
    """Verify GroupReader initialization."""
    reader = GroupReader(test_profile, mock_read_block)

    assert reader.profile == test_profile
    assert reader.read_block == mock_read_block


def test_read_group_success(group_reader, mock_read_block):
    """Verify read_group returns list of parsed blocks."""
    # EL100V2 CORE group has block 100
    result = group_reader.read_group(BlockGroup.CORE, partial_ok=True)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].block_id == 100
    mock_read_block.assert_called_once_with(100)


def test_read_group_with_partial_failures(group_reader, mock_read_block):
    """Verify read_group handles partial failures when partial_ok=True."""
    # Mock read_block to fail on some blocks
    def mock_read(block_id):
        if block_id == 1100:
            raise ValueError("Test error")
        return ParsedBlock(
            block_id=block_id, name=f"BLOCK_{block_id}", values={}, raw=b"", length=0
        )

    group_reader.read_block = mock_read

    # INVERTER group has multiple blocks
    result = group_reader.read_group(BlockGroup.INVERTER, partial_ok=True)

    # Should return partial results (skipping failed block)
    assert isinstance(result, list)
    assert len(result) >= 1  # At least some blocks succeeded


def test_read_group_ex_success(group_reader, mock_read_block):
    """Verify read_group_ex returns ReadGroupResult."""
    result = group_reader.read_group_ex(BlockGroup.CORE, partial_ok=False)

    assert isinstance(result, ReadGroupResult)
    assert len(result.blocks) == 1
    assert len(result.errors) == 0
    assert result.success is True
    assert result.partial is False


def test_read_group_ex_strict_mode_fails_fast(group_reader):
    """Verify read_group_ex fails fast when partial_ok=False."""
    # Mock read_block to always fail
    group_reader.read_block = Mock(side_effect=ValueError("Test error"))

    with pytest.raises(ValueError, match="Test error"):
        group_reader.read_group_ex(BlockGroup.CORE, partial_ok=False)


def test_read_group_ex_partial_mode_collects_errors(group_reader):
    """Verify read_group_ex collects errors when partial_ok=True."""
    call_count = 0

    def mock_read(block_id):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call succeeds
            return ParsedBlock(
                block_id=block_id,
                name=f"BLOCK_{block_id}",
                values={},
                raw=b"",
                length=0,
            )
        # Subsequent calls fail
        raise ValueError(f"Error on block {block_id}")

    group_reader.read_block = mock_read

    result = group_reader.read_group_ex(BlockGroup.INVERTER, partial_ok=True)

    assert result.success is False  # Had errors
    assert result.partial is True  # But some succeeded
    assert len(result.blocks) >= 1  # At least one succeeded
    assert len(result.errors) >= 1  # At least one failed


def test_stream_group_yields_in_order(group_reader):
    """Verify stream_group yields blocks in group order."""
    call_count = 0

    def mock_read(block_id):
        nonlocal call_count
        call_count += 1
        return ParsedBlock(
            block_id=block_id,
            name=f"BLOCK_{block_id}",
            values={"order": call_count},
            raw=b"",
            length=0,
        )

    group_reader.read_block = mock_read

    # Collect streamed blocks
    streamed_blocks = list(group_reader.stream_group(BlockGroup.CORE, partial_ok=True))

    assert len(streamed_blocks) >= 1
    # Verify blocks are yielded in order (first block has order=1)
    assert streamed_blocks[0].values["order"] == 1


def test_stream_group_partial_mode_continues_on_error(group_reader):
    """Verify stream_group continues after errors when partial_ok=True."""
    call_count = 0

    def mock_read(block_id):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            # Second call fails
            raise ValueError("Test error")
        return ParsedBlock(
            block_id=block_id, name=f"BLOCK_{block_id}", values={}, raw=b"", length=0
        )

    group_reader.read_block = mock_read

    # Should yield blocks despite error
    streamed_blocks = list(
        group_reader.stream_group(BlockGroup.INVERTER, partial_ok=True)
    )

    # At least first block should be yielded
    assert len(streamed_blocks) >= 1


def test_validate_group_raises_on_unknown(group_reader):
    """Verify _validate_group raises ValueError for unknown group."""
    # Create a fake group enum
    class FakeGroup:
        value = "UNKNOWN_GROUP"

    with pytest.raises(ValueError, match="not supported"):
        group_reader._validate_group(FakeGroup())  # type: ignore[arg-type]


def test_group_reader_uses_injected_read_block(test_profile):
    """Verify GroupReader uses injected read_block function."""
    mock_fn = Mock(
        return_value=ParsedBlock(
            block_id=100, name="TEST", values={}, raw=b"", length=0
        )
    )
    reader = GroupReader(test_profile, mock_fn)

    reader.read_group(BlockGroup.CORE, partial_ok=True)

    # Verify injected function was called
    assert mock_fn.called
    mock_fn.assert_called_with(100)
