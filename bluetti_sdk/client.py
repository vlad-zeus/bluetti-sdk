"""V2 Client - Layer Orchestration

High-level client that orchestrates all layers:
    transport → protocol → v2_parser → device_model

This is the PUBLIC API for V2 devices.
"""

import logging
import time
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    TypeVar,
)

if TYPE_CHECKING:
    from .protocol.v2.schema import BlockSchema

from . import schemas
from .client_services.group_reader import GroupReader, ReadGroupResult
from .constants import V2_PROTOCOL_VERSION
from .contracts import (
    BluettiClientInterface,
    DeviceModelInterface,
    TransportProtocol,
    V2ParserInterface,
)
from .devices.types import DeviceProfile
from .errors import ParserError, ProtocolError, TransportError
from .models.device import V2Device
from .models.types import BlockGroup
from .protocol.modbus import (
    build_modbus_request,
    normalize_modbus_response,
    parse_modbus_frame,
    validate_crc,
)
from .protocol.v2.parser import V2Parser
from .protocol.v2.types import ParsedBlock
from .schemas.registry import SchemaRegistry
from .utils.resilience import RetryPolicy, iter_delays

logger = logging.getLogger(__name__)

T = TypeVar("T")


class V2Client(BluettiClientInterface):
    """High-level V2 client.

    Orchestrates layers without knowing implementation details:
    - Transport: sends/receives frames
    - Protocol: normalizes Modbus
    - Parser: parses blocks
    - Device: stores state

    Usage:
        client = V2Client(transport, device_profile)
        client.connect()

        # Read single block
        parsed = client.read_block(1300)
        print(f"Grid: {parsed.values['phase_0_voltage']}V")

        # Read block group
        blocks = client.read_group(BlockGroup.GRID)

        # Get device state
        state = client.get_device_state()

    Concurrency:
        A single V2Client instance is intended for serialized access.
        Do not call read/connect/disconnect concurrently from multiple threads.
    """

    def __init__(
        self,
        transport: TransportProtocol,
        profile: DeviceProfile,
        device_address: int = 1,
        parser: Optional[V2ParserInterface] = None,
        device: Optional[DeviceModelInterface] = None,
        schema_registry: Optional[SchemaRegistry] = None,
        retry_policy: Optional[RetryPolicy] = None,
    ):
        """Initialize V2 client with dependency injection.

        Args:
            transport: Transport layer implementation
            profile: Device profile with configuration
            device_address: Modbus device address (default: 1)
            parser: Parser implementation (creates V2Parser if None)
            device: Device model implementation (creates V2Device if None)
            schema_registry: Schema registry (creates instance with built-ins if None)
            retry_policy: Retry policy for transient errors (creates default if None)

        Note:
            Parser and device are injected via constructor for testability.
            If not provided, default implementations are created.
        """
        self.transport = transport
        self.profile = profile
        self.device_address = device_address
        self.retry_policy = retry_policy if retry_policy is not None else RetryPolicy()
        self.schema_registry = (
            schema_registry
            if schema_registry is not None
            else schemas.new_registry_with_builtins()
        )

        # Inject or create V2 parser
        self.parser = parser if parser is not None else V2Parser()

        # Inject or create device model
        self.device = (
            device
            if device is not None
            else V2Device(
                device_id=f"{profile.model}_{device_address}",
                model=profile.model,
                protocol_version=V2_PROTOCOL_VERSION,
            )
        )

        # Auto-register schemas from SchemaRegistry
        self._auto_register_schemas()

        # Initialize group reader service (delegation pattern)
        self._group_reader = GroupReader(self.profile, self.read_block)

    def _auto_register_schemas(self) -> None:
        """Auto-register schemas for all blocks in device profile.

        Collects block IDs from device profile, resolves schemas from global
        SchemaRegistry, and registers them in the parser.

        This eliminates temporal coupling - no need for manual schema registration.
        """
        # Collect all block IDs from profile groups
        block_ids = set()
        for group in self.profile.groups.values():
            block_ids.update(group.blocks)

        if not block_ids:
            logger.warning(
                f"Device profile '{self.profile.model}' has no blocks defined"
            )
            return

        logger.debug(
            f"Auto-registering schemas for {len(block_ids)} blocks: {sorted(block_ids)}"
        )

        # Resolve schemas from client-scoped registry (strict=False for flexibility)
        try:
            resolved_schemas = self.schema_registry.resolve_blocks(
                list(block_ids), strict=False
            )
        except ValueError as e:
            logger.error(f"Failed to resolve schemas: {e}")
            resolved_schemas = {}

        # Register resolved schemas in parser
        for block_id, schema in resolved_schemas.items():
            self.parser.register_schema(schema)
            logger.debug(f"Registered schema: Block {block_id} ({schema.name})")

        # Warn about missing schemas
        missing = block_ids - set(resolved_schemas.keys())
        if missing:
            logger.warning(
                f"Schemas not found for blocks: {sorted(missing)}. "
                f"These blocks cannot be parsed. "
                f"Available schemas: {self.schema_registry.list_blocks()}"
            )

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
        attempt = 1
        last_error: Optional[Exception] = None

        for delay in [0.0, *list(iter_delays(self.retry_policy))]:
            if delay > 0:
                logger.info(
                    f"{operation}: Retry attempt {attempt}/"
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
                attempt += 1
            except (ParserError, ProtocolError):
                # Fail fast on non-transient errors
                raise

        # Exhausted all retries
        logger.error(
            f"{operation}: Failed after {self.retry_policy.max_attempts} attempts"
        )
        raise last_error  # type: ignore

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
        self, block_id: int, register_count: Optional[int] = None
    ) -> ParsedBlock:
        """Read and parse a V2 block.

        This is the core method that orchestrates all layers.

        Flow:
            1. Build Modbus request (protocol layer)
            2. Send via transport
            3. Parse Modbus response (protocol layer)
            4. Normalize to bytes (protocol layer)
            5. Parse block (v2_parser)
            6. Update device model
            7. Return ParsedBlock

        Args:
            block_id: Block ID to read
            register_count: Number of registers (auto-calculated if None)

        Returns:
            ParsedBlock with parsed data

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

        # === Layer 1: Protocol - Build Modbus request ===
        request = build_modbus_request(
            device_address=self.device_address,
            block_address=block_id,
            register_count=register_count,
        )

        logger.debug(f"Modbus request: {request.hex()}")

        # === Layer 2: Transport - Send and receive (with retry) ===
        def _send_frame() -> bytes:
            try:
                return self.transport.send_frame(request, timeout=5.0)
            except Exception as e:
                raise TransportError(f"Transport error: {e}") from e

        response_frame = self._with_retry(_send_frame, f"Read block {block_id}")
        logger.debug(f"Modbus response: {response_frame.hex()}")

        # === Layer 3: Protocol - Parse and normalize ===
        # Validate CRC
        if not validate_crc(response_frame):
            raise ProtocolError("CRC validation failed")

        # Parse Modbus frame
        modbus_response = parse_modbus_frame(response_frame)

        # Normalize to clean bytes
        normalized_data = normalize_modbus_response(modbus_response)

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
                protocol_version=self.device.protocol_version,
            )
        except Exception as e:
            raise ParserError(f"Parse error for block {block_id}: {e}") from e

        # Log validation warnings
        if parsed.validation and parsed.validation.warnings:
            for warning in parsed.validation.warnings:
                logger.warning(f"Block {block_id}: {warning}")

        # === Layer 5: Device Model - Update state ===
        self.device.update_from_block(parsed)

        logger.info(
            f"Block {block_id} ({parsed.name}) parsed successfully: "
            f"{len(parsed.values)} fields"
        )

        return parsed

    def read_group(
        self, group: BlockGroup, partial_ok: bool = True
    ) -> List[ParsedBlock]:
        """Read a block group.

        Args:
            group: BlockGroup to read
            partial_ok: If True (default), return partial results on failures.
                       If False, fail fast on first error.

        Returns:
            List of ParsedBlock (one per block in group)

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
    ) -> Iterator[ParsedBlock]:
        """Stream blocks from a group as they are read.

        Yields blocks as they arrive instead of collecting them in memory.
        Useful for processing large groups or implementing real-time UIs.

        Args:
            group: BlockGroup to stream
            partial_ok: If True (default), skip failed blocks and continue.
                       If False, fail fast on first error.

        Yields:
            ParsedBlock for each successfully read block (in group order)

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

    def register_schema(self, schema: "BlockSchema") -> None:
        """Register a block schema with parser.

        Args:
            schema: BlockSchema to register
        """
        self.schema_registry.register(schema)
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
            Dict mapping block_id → schema_name
        """
        return self.parser.list_schemas()
