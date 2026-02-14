"""Async facade for V2Client.

Provides async/await-friendly API while reusing sync V2Client logic.
"""

from __future__ import annotations

import asyncio
import contextlib
from types import TracebackType
from typing import Any

from .client import ReadGroupResult, V2Client
from .contracts import DeviceModelInterface, V2ParserInterface
from .contracts.transport import TransportProtocol
from .devices.types import DeviceProfile
from .models.types import BlockGroup
from .protocol.v2.schema import BlockSchema
from .protocol.v2.types import ParsedBlock
from .schemas.registry import SchemaRegistry
from .utils.resilience import RetryPolicy


class AsyncV2Client:
    """Async facade over sync V2Client using thread delegation.

    Thread Safety:
        This client is SAFE for concurrent async operations on the same instance.
        All operations are serialized using an internal asyncio.Lock.

        Multiple coroutines can call methods concurrently - they will be queued
        and executed sequentially, preventing race conditions.

    Usage:
        # Safe: concurrent calls are automatically serialized
        async with AsyncV2Client(transport, profile) as client:
            results = await asyncio.gather(
                client.read_block(100),
                client.read_block(1300),
                client.read_group(BlockGroup.BATTERY),
            )
    """

    def __init__(
        self,
        transport: TransportProtocol,
        profile: DeviceProfile,
        device_address: int = 1,
        parser: V2ParserInterface | None = None,
        device: DeviceModelInterface | None = None,
        schema_registry: SchemaRegistry | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self._sync_client = V2Client(
            transport=transport,
            profile=profile,
            device_address=device_address,
            parser=parser,
            device=device,
            schema_registry=schema_registry,
            retry_policy=retry_policy,
        )
        # Operation lock: serializes all async operations to prevent races
        self._op_lock = asyncio.Lock()

    async def connect(self) -> None:
        """Connect to device.

        Raises:
            TransportError: If connection fails
        """
        async with self._op_lock:
            await asyncio.to_thread(self._sync_client.connect)

    async def disconnect(self) -> None:
        """Disconnect from device.

        This is idempotent - safe to call multiple times.
        """
        async with self._op_lock:
            await asyncio.to_thread(self._sync_client.disconnect)

    async def read_block(
        self,
        block_id: int,
        register_count: int | None = None,
    ) -> ParsedBlock:
        """Read and parse a single block.

        Args:
            block_id: Block ID to read
            register_count: Optional Modbus register count override

        Returns:
            Parsed block with values

        Raises:
            TransportError: If communication fails
            ProtocolError: If Modbus response is invalid
            ParserError: If block schema is unknown or parsing fails
        """
        async with self._op_lock:
            return await asyncio.to_thread(
                self._sync_client.read_block, block_id, register_count
            )

    async def read_group(
        self, group: BlockGroup, partial_ok: bool = True
    ) -> list[ParsedBlock]:
        """Read all blocks in a group.

        Args:
            group: Block group to read
            partial_ok: If True, return partial results on error

        Returns:
            List of successfully parsed blocks

        Raises:
            Exception: If partial_ok=False and any block fails
        """
        async with self._op_lock:
            return await asyncio.to_thread(
                self._sync_client.read_group, group, partial_ok
            )

    async def read_group_ex(
        self, group: BlockGroup, partial_ok: bool = False
    ) -> ReadGroupResult:
        """Read block group with detailed error reporting.

        Args:
            group: Block group to read
            partial_ok: If True, collect errors instead of raising

        Returns:
            ReadGroupResult with blocks and errors

        Raises:
            Exception: If partial_ok=False and any block fails
        """
        async with self._op_lock:
            return await asyncio.to_thread(
                self._sync_client.read_group_ex, group, partial_ok
            )

    async def get_device_state(self) -> dict[str, Any]:
        """Get current device state as flat dictionary.

        Returns:
            Dictionary mapping field names to values
        """
        async with self._op_lock:
            return await asyncio.to_thread(self._sync_client.get_device_state)

    async def get_group_state(self, group: BlockGroup) -> dict[str, Any]:
        """Get state for a specific block group.

        Args:
            group: Block group to query

        Returns:
            Dictionary mapping field names to values for this group
        """
        async with self._op_lock:
            return await asyncio.to_thread(self._sync_client.get_group_state, group)

    async def register_schema(self, schema: BlockSchema) -> None:
        """Register a new block schema dynamically.

        Args:
            schema: Block schema to register

        Raises:
            ValueError: If schema conflicts with existing registration
        """
        async with self._op_lock:
            await asyncio.to_thread(self._sync_client.register_schema, schema)

    async def get_available_groups(self) -> list[str]:
        """Get list of available block groups.

        Returns:
            List of group names
        """
        async with self._op_lock:
            return await asyncio.to_thread(self._sync_client.get_available_groups)

    async def get_registered_schemas(self) -> dict[int, str]:
        """Get mapping of registered block schemas.

        Returns:
            Dictionary mapping block IDs to schema names
        """
        async with self._op_lock:
            return await asyncio.to_thread(self._sync_client.get_registered_schemas)

    async def __aenter__(self) -> AsyncV2Client:
        """Enter async context manager.

        Connects to device. If connection fails, ensures proper cleanup
        before propagating the exception.

        Returns:
            Self for use in async with statement

        Raises:
            TransportError: If connection fails
        """
        try:
            await self.connect()
        except Exception:
            # If connect fails, attempt cleanup before re-raising
            # This handles partial connection states
            with contextlib.suppress(Exception):
                # Ignore disconnect errors during error recovery
                await self.disconnect()
            raise
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        """Exit async context manager.

        Ensures disconnect is called even if exception occurred in context.
        If disconnect fails during exception handling, the original exception
        from the context takes precedence to preserve diagnostics.

        Args:
            exc_type: Exception type if raised in context
            exc_val: Exception value if raised in context
            exc_tb: Exception traceback if raised in context

        Returns:
            False to propagate any exceptions from context
        """
        try:
            await self.disconnect()
        except Exception:
            # If there's already an exception from the context, don't mask it
            if exc_val is None:
                # No original exception - re-raise disconnect error
                raise
            # Otherwise suppress disconnect error to preserve original exception
            # (Could add logging here if needed)
        return False
