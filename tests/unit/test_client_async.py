"""Unit tests for AsyncV2Client facade."""

from unittest.mock import Mock

import pytest
from bluetti_sdk.client_async import AsyncV2Client
from bluetti_sdk.devices.profiles import get_device_profile
from bluetti_sdk.errors import TransportError
from bluetti_sdk.models.types import BlockGroup
from bluetti_sdk.protocol.v2.types import ParsedBlock


@pytest.fixture
def mock_transport():
    transport = Mock()
    transport.connect = Mock()
    transport.disconnect = Mock()
    transport.is_connected = Mock(return_value=True)
    return transport


@pytest.fixture
def device_profile():
    return get_device_profile("EL100V2")


def _make_parsed_block(block_id: int) -> ParsedBlock:
    return ParsedBlock(
        block_id=block_id,
        name=f"BLOCK_{block_id}",
        values={"ok": True},
        raw=b"",
        length=0,
        protocol_version=2000,
        schema_version="1.0.0",
        timestamp=0.0,
    )


@pytest.mark.asyncio
async def test_async_connect_disconnect(mock_transport, device_profile):
    client = AsyncV2Client(mock_transport, device_profile)
    await client.connect()
    await client.disconnect()
    mock_transport.connect.assert_called_once()
    mock_transport.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_async_context_manager(mock_transport, device_profile):
    async with AsyncV2Client(mock_transport, device_profile) as client:
        assert client is not None

    mock_transport.connect.assert_called_once()
    mock_transport.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_async_read_block_delegates(mock_transport, device_profile):
    client = AsyncV2Client(mock_transport, device_profile)
    parsed = _make_parsed_block(100)
    client._sync_client.read_block = Mock(return_value=parsed)

    result = await client.read_block(100)
    assert result == parsed
    client._sync_client.read_block.assert_called_once_with(100, None)


@pytest.mark.asyncio
async def test_async_read_group_ex_delegates(mock_transport, device_profile):
    client = AsyncV2Client(mock_transport, device_profile)
    client._sync_client.read_group_ex = Mock(return_value=Mock(success=True))
    result = await client.read_group_ex(BlockGroup.CORE, partial_ok=True)
    assert result.success is True
    client._sync_client.read_group_ex.assert_called_once_with(BlockGroup.CORE, True)


@pytest.mark.asyncio
async def test_async_propagates_exceptions(mock_transport, device_profile):
    client = AsyncV2Client(mock_transport, device_profile)
    client._sync_client.read_block = Mock(side_effect=TransportError("boom"))

    with pytest.raises(TransportError, match="boom"):
        await client.read_block(100)
