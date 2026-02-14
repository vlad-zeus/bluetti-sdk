"""Async facade for V2Client.

Provides async/await-friendly API while reusing sync V2Client logic.
"""

from __future__ import annotations

import asyncio
from typing import Dict, List, Optional

from .client import ReadGroupResult, V2Client
from .contracts import DeviceModelInterface, V2ParserInterface
from .contracts.transport import TransportProtocol
from .devices.types import DeviceProfile
from .models.types import BlockGroup
from .protocol.v2.types import ParsedBlock
from .schemas.registry import SchemaRegistry


class AsyncV2Client:
    """Async facade over sync V2Client using thread delegation."""

    def __init__(
        self,
        transport: TransportProtocol,
        profile: DeviceProfile,
        device_address: int = 1,
        parser: Optional[V2ParserInterface] = None,
        device: Optional[DeviceModelInterface] = None,
        schema_registry: Optional[SchemaRegistry] = None,
    ) -> None:
        self._sync_client = V2Client(
            transport=transport,
            profile=profile,
            device_address=device_address,
            parser=parser,
            device=device,
            schema_registry=schema_registry,
        )

    async def connect(self) -> None:
        await asyncio.to_thread(self._sync_client.connect)

    async def disconnect(self) -> None:
        await asyncio.to_thread(self._sync_client.disconnect)

    async def read_block(
        self,
        block_id: int,
        register_count: Optional[int] = None,
    ) -> ParsedBlock:
        return await asyncio.to_thread(
            self._sync_client.read_block, block_id, register_count
        )

    async def read_group(
        self, group: BlockGroup, partial_ok: bool = True
    ) -> List[ParsedBlock]:
        return await asyncio.to_thread(self._sync_client.read_group, group, partial_ok)

    async def read_group_ex(
        self, group: BlockGroup, partial_ok: bool = False
    ) -> ReadGroupResult:
        return await asyncio.to_thread(
            self._sync_client.read_group_ex, group, partial_ok
        )

    async def get_device_state(self) -> Dict:
        return await asyncio.to_thread(self._sync_client.get_device_state)

    async def get_group_state(self, group: BlockGroup) -> Dict:
        return await asyncio.to_thread(self._sync_client.get_group_state, group)

    async def register_schema(self, schema) -> None:
        await asyncio.to_thread(self._sync_client.register_schema, schema)

    async def get_available_groups(self) -> List[str]:
        return await asyncio.to_thread(self._sync_client.get_available_groups)

    async def get_registered_schemas(self) -> Dict[int, str]:
        return await asyncio.to_thread(self._sync_client.get_registered_schemas)

    async def __aenter__(self) -> "AsyncV2Client":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        await self.disconnect()
        return False
