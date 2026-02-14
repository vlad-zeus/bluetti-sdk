"""V2 Client - Layer Orchestration

High-level client that orchestrates all layers:
    transport → protocol → v2_parser → device_model

This is the PUBLIC API for V2 devices.
"""

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from .protocol.v2.schema import BlockSchema

from . import schemas
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

logger = logging.getLogger(__name__)


@dataclass
class ReadGroupResult:
    """Result of read_group operation.

    Attributes:
        blocks: Successfully parsed blocks
        errors: List of (block_id, exception) for failed blocks
    """

    blocks: List["ParsedBlock"]
    errors: List[Tuple[int, Exception]]

    @property
    def success(self) -> bool:
        """Check if all blocks were read successfully."""
        return len(self.errors) == 0

    @property
    def partial(self) -> bool:
        """Check if some (but not all) blocks failed."""
        return len(self.errors) > 0 and len(self.blocks) > 0


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
    ):
        """Initialize V2 client with dependency injection.

        Args:
            transport: Transport layer implementation
            profile: Device profile with configuration
            device_address: Modbus device address (default: 1)
            parser: Parser implementation (creates V2Parser if None)
            device: Device model implementation (creates V2Device if None)
            schema_registry: Schema registry (creates instance with built-ins if None)

        Note:
            Parser and device are injected via constructor for testability.
            If not provided, default implementations are created.
        """
        self.transport = transport
        self.profile = profile
        self.device_address = device_address
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
                protocol_version=2000,  # V2 protocol
            )
        )

        # Auto-register schemas from SchemaRegistry
        self._auto_register_schemas()

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

    def connect(self) -> None:
        """Connect to device."""
        logger.info(f"Connecting to {self.profile.model}...")
        self.transport.connect()

        if not self.transport.is_connected():
            raise TransportError("Failed to connect to device")

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

        # === Layer 2: Transport - Send and receive ===
        try:
            response_frame = self.transport.send_frame(request, timeout=5.0)
        except Exception as e:
            raise TransportError(f"Transport error: {e}") from e

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
        result = self.read_group_ex(group, partial_ok=partial_ok)
        return result.blocks

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
        # Get group definition from device profile
        group_name = group.value
        if group_name not in self.profile.groups:
            raise ValueError(
                f"Group '{group_name}' not supported by {self.profile.model}. "
                f"Available: {list(self.profile.groups.keys())}"
            )

        group_def = self.profile.groups[group_name]

        logger.info(f"Reading group '{group_name}': {len(group_def.blocks)} blocks")

        # Read all blocks in group
        blocks = []
        errors = []

        for block_id in group_def.blocks:
            try:
                parsed = self.read_block(block_id)
                blocks.append(parsed)
            except Exception as e:
                logger.error(f"Failed to read block {block_id}: {e}")
                errors.append((block_id, e))

                # In strict mode (partial_ok=False), fail immediately
                if not partial_ok:
                    raise

        if errors and partial_ok:
            logger.warning(
                f"Group '{group_name}' read completed with {len(errors)} errors: "
                f"{len(blocks)}/{len(group_def.blocks)} blocks successful"
            )
        else:
            logger.info(
                f"Group '{group_name}' read complete: "
                f"{len(blocks)}/{len(group_def.blocks)} blocks successful"
            )

        return ReadGroupResult(blocks=blocks, errors=errors)

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
