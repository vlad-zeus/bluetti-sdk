"""Client - Layer Orchestration

High-level client that orchestrates all layers:
    transport -> protocol -> parser -> device_model

This is the PUBLIC API for protocol devices.
"""

import logging
import time
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    TypeVar,
)

from .client_services.group_reader import GroupReader, ReadGroupResult
from .contracts import (
    ClientInterface,
    DeviceModelInterface,
    ParsedRecord,
    ParserInterface,
    ProtocolLayerInterface,
    TransportProtocol,
)
from .devices.types import DeviceProfile
from .errors import ParserError, ProtocolError, TransportError
from .models.device import Device
from .models.types import BlockGroup
from .protocol.factory import ProtocolFactory
from .utils.resilience import RetryPolicy, iter_delays

logger = logging.getLogger(__name__)

T = TypeVar("T")


class Client(ClientInterface):
    """High-level client.

    Orchestrates layers without knowing implementation details:
    - Transport: sends/receives frames
    - Protocol: normalizes Modbus
    - Parser: parses blocks
    - Device: stores state

    Usage:
        client = Client(transport, device_profile)
        client.connect()

        # Read single block
        parsed = client.read_block(1300)
        print(f"Grid: {parsed.values['phase_0_voltage']}V")

        # Read block group
        blocks = client.read_group(BlockGroup.GRID)

        # Get device state
        state = client.get_device_state()

    Concurrency:
        A single Client instance is intended for serialized access.
        Do not call read/connect/disconnect concurrently from multiple threads.
    """

    def __init__(
        self,
        transport: TransportProtocol,
        profile: DeviceProfile,
        parser: ParserInterface,
        device_address: int = 1,
        protocol: Optional[ProtocolLayerInterface] = None,
        device: Optional[DeviceModelInterface] = None,
        retry_policy: Optional[RetryPolicy] = None,
    ):
        """Initialize client with dependency injection.

        Args:
            transport: Transport layer implementation
            profile: Device profile with configuration
            parser: Parser implementation (required -- use bootstrap or contrib
                for defaults)
            device_address: Modbus device address (default: 1)
            protocol: Protocol layer implementation (resolved via ProtocolFactory
                if None)
            device: Device model implementation (creates Device if None)
            retry_policy: Retry policy for transient errors (creates default if None)

        Note:
            Runtime-first usage should construct clients via
            RuntimeRegistry.from_config(runtime.yaml).
        """
        self.transport = transport
        self._profile = profile
        self.device_address = device_address
        self.protocol = (
            protocol
            if protocol is not None
            else ProtocolFactory.create(self.profile.protocol)
        )
        self.retry_policy = retry_policy if retry_policy is not None else RetryPolicy()
        self.parser = parser

        # Inject or create device model
        self.device = (
            device
            if device is not None
            else Device(
                device_id=f"{profile.model}_{device_address}",
                model=profile.model,
                protocol_version=self.profile.protocol_version,
            )
        )

        # Initialize group reader service (delegation pattern)
        self._group_reader = GroupReader(self.profile, self.read_block)

    @property
    def profile(self) -> DeviceProfile:
        """Device profile bound to this client."""
        return self._profile

    def _with_retry(self, fn: Callable[[], T], operation: str) -> T:
        """Execute function with retry on TransportError.

        Implements exponential backoff retry logic for transient transport failures.
        Only retries on TransportError - Parser and Protocol errors fail immediately.

        Args:
            fn: Function to execute (must be callable with no args)
            operation: Operation name for logging

        Returns:
            Result of successful function call

        Raises:
            TransportError: After all retry attempts exhausted
            ParserError: Immediately on parser error (no retry)
            ProtocolError: Immediately on protocol error (no retry)
        """
        last_error: Optional[Exception] = None
        delays = [0.0, *list(iter_delays(self.retry_policy))]
        for attempt, delay in enumerate(delays, start=1):
            if delay > 0:
                logger.info(
                    f"{operation}: Retry attempt {attempt - 1}/"
                    f"{self.retry_policy.max_attempts} after {delay:.2f}s delay"
                )
                time.sleep(delay)

            try:
                return fn()
            except TransportError as e:
                last_error = e
                logger.warning(
                    f"{operation}: Transport error on attempt {attempt}: {e}"
                )
            except (ParserError, ProtocolError):
                # Fail fast on non-transient errors
                raise

        # Exhausted all retries
        logger.error(
            f"{operation}: Failed after {self.retry_policy.max_attempts} attempts"
        )
        assert last_error is not None  # Defensive: retry loop always records error
        raise last_error

    def connect(self) -> None:
        """Connect to device with retry on transient errors."""
        logger.info(f"Connecting to {self.profile.model}...")

        def _do_connect() -> None:
            self.transport.connect()
            if not self.transport.is_connected():
                raise TransportError("Failed to connect to device")

        self._with_retry(_do_connect, "Connect")
        logger.info(f"Connected to {self.profile.model}")

    def disconnect(self) -> None:
        """Disconnect from device."""
        logger.info("Disconnecting...")
        self.transport.disconnect()

    def read_block(
        self,
        block_id: int,
        register_count: Optional[int] = None,
        update_state: bool = True,
    ) -> ParsedRecord:
        """Read and parse a block.

        This is the core method that orchestrates all layers.

        Flow:
            1. Build Modbus request (protocol layer)
            2. Send via transport
            3. Parse Modbus response (protocol layer)
            4. Normalize to bytes (protocol layer)
            5. Parse block (parser)
            6. Update device model (if update_state=True)
            7. Return ParsedRecord

        Args:
            block_id: Block ID to read
            register_count: Number of registers (auto-calculated if None)
            update_state: If True (default), update device model state.
                         If False, read without side effects (query-only mode).

        Returns:
            ParsedRecord with parsed data

        Raises:
            TransportError: If transport fails
            ProtocolError: If Modbus error
            ParserError: If parsing fails
        """
        # Auto-calculate register count from schema
        if register_count is None:
            schema = self.parser.get_schema(block_id)
            if schema:
                # min_length is in bytes, registers are 2 bytes each
                register_count = (schema.min_length + 1) // 2
            else:
                raise ParserError(
                    f"No schema registered for block {block_id} "
                    f"and register_count not specified"
                )

        logger.debug(
            f"Reading block {block_id} "
            f"({register_count} registers = {register_count * 2} bytes)"
        )

        # === Layer 1-2: Protocol + Transport ===
        def _read_payload() -> bytes:
            try:
                payload = self.protocol.read_block(
                    transport=self.transport,
                    device_address=self.device_address,
                    block_id=block_id,
                    register_count=register_count,
                )
                return payload.data
            except (ProtocolError, TransportError):
                raise
            except Exception as e:
                raise TransportError(f"Transport error: {e}") from e

        normalized_data = self._with_retry(_read_payload, f"Read block {block_id}")

        logger.debug(
            f"Normalized payload: {normalized_data.hex()} "
            f"({len(normalized_data)} bytes)"
        )

        # === Layer 4: Parser - Parse block ===
        try:
            parsed = self.parser.parse_block(
                block_id=block_id,
                data=normalized_data,
                validate=True,
                protocol_version=self.profile.protocol_version,
            )
        except Exception as e:
            raise ParserError(f"Parse error for block {block_id}: {e}") from e

        # Log validation warnings
        if parsed.validation and parsed.validation.warnings:
            for warning in parsed.validation.warnings:
                logger.warning(f"Block {block_id}: {warning}")

        # === Layer 5: Device Model - Update state ===
        if update_state:
            self.device.update_from_block(parsed)

        logger.info(
            f"Block {block_id} ({parsed.name}) parsed successfully: "
            f"{len(parsed.values)} fields"
        )

        return parsed

    def read_group(
        self, group: BlockGroup, partial_ok: bool = True
    ) -> List[ParsedRecord]:
        """Read a block group.

        Args:
            group: BlockGroup to read
            partial_ok: If True (default), return partial results on failures.
                       If False, fail fast on first error.

        Returns:
            List of ParsedRecord (one per block in group)

        Raises:
            ValueError: If group not supported by this device
            TransportError/ProtocolError: If any block read fails and partial_ok=False
        """
        return self._group_reader.read_group(group, partial_ok)

    def read_group_ex(
        self, group: BlockGroup, partial_ok: bool = False
    ) -> ReadGroupResult:
        """Read a block group with detailed error reporting.

        Args:
            group: BlockGroup to read
            partial_ok: If False (default), fail fast on first error.
                       If True, continue reading remaining blocks and collect errors.

        Returns:
            ReadGroupResult with blocks and errors

        Raises:
            ValueError: If group not supported by this device
            TransportError/ProtocolError: If any block read fails and partial_ok=False
        """
        return self._group_reader.read_group_ex(group, partial_ok)

    def stream_group(
        self, group: BlockGroup, partial_ok: bool = True
    ) -> Iterator[ParsedRecord]:
        """Stream blocks from a group as they are read.

        Yields blocks as they arrive instead of collecting them in memory.
        Useful for processing large groups or implementing real-time UIs.

        Args:
            group: BlockGroup to stream
            partial_ok: If True (default), skip failed blocks and continue.
                       If False, fail fast on first error.

        Yields:
            ParsedRecord for each successfully read block (in group order)

        Raises:
            ValueError: If group not supported by this device
            TransportError/ProtocolError: If any block read fails and partial_ok=False

        Example:
            for block in client.stream_group(BlockGroup.BATTERY):
                print(f"Got {block.name}: {block.values}")
        """
        return self._group_reader.stream_group(group, partial_ok)

    def get_device_state(self) -> Dict[str, Any]:
        """Get current device state.

        Returns:
            Dict with all device attributes
        """
        return self.device.get_state()

    def get_group_state(self, group: BlockGroup) -> Dict[str, Any]:
        """Get state for specific block group.

        Args:
            group: BlockGroup to retrieve

        Returns:
            Dict with group-specific attributes
        """
        return self.device.get_group_state(group)

    def register_schema(self, schema: Any) -> None:
        """Register a block schema with parser.

        Args:
            schema: Schema object implementing the parser's expected schema contract
        """
        self.parser.register_schema(schema)
        logger.debug(f"Registered schema: Block {schema.block_id} ({schema.name})")

    def get_available_groups(self) -> List[str]:
        """Get list of available block groups for this device.

        Returns:
            List of group names
        """
        return list(self.profile.groups.keys())

    def get_registered_schemas(self) -> Dict[int, str]:
        """Get list of registered schemas.

        Returns:
            Dict mapping block_id -> schema_name
        """
        return self.parser.list_schemas()
