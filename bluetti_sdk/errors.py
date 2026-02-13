"""Layer Contracts and Interfaces

Defines strict contracts between architectural layers:
    transport → protocol → v2_parser → device_model

Each layer has clear responsibilities and does NOT leak into others.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol
from dataclasses import dataclass
from enum import Enum


# ============================================================================
# Transport Layer → Protocol Layer
# ============================================================================

class TransportProtocol(ABC):
    """Transport layer interface.

    Responsibilities:
    - Send/receive raw frames over wire (MQTT, BLE, Serial)
    - Connection management
    - Retries and timeouts

    Does NOT know about:
    - Modbus framing
    - Block schemas
    - Device models
    """

    @abstractmethod
    def send_frame(self, frame: bytes, timeout: float = 5.0) -> bytes:
        """Send frame and wait for response.

        Args:
            frame: Raw frame to send (complete with framing/CRC)
            timeout: Timeout in seconds

        Returns:
            Raw response frame

        Raises:
            TimeoutError: If no response within timeout
            ConnectionError: If connection lost
        """
        pass

    @abstractmethod
    def connect(self):
        """Establish connection to device."""
        pass

    @abstractmethod
    def disconnect(self):
        """Close connection to device."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected."""
        pass


# ============================================================================
# Protocol Layer → V2 Parser Layer
# ============================================================================

@dataclass
class NormalizedPayload:
    """Normalized payload ready for parsing.

    This is the CONTRACT between protocol layer and parser.
    """
    block_id: int
    data: bytes  # Big-endian, no framing
    device_address: int
    protocol_version: int = 2000


class ProtocolLayerInterface(ABC):
    """Protocol layer interface.

    Responsibilities:
    - Modbus framing/unframing
    - CRC validation
    - Byte normalization (big-endian)

    Does NOT know about:
    - Block schemas
    - Field parsing
    - Device models
    """

    @abstractmethod
    def read_block(
        self,
        transport: TransportProtocol,
        device_address: int,
        block_id: int,
        register_count: int
    ) -> NormalizedPayload:
        """Read a V2 block via Modbus.

        Args:
            transport: Transport layer to use
            device_address: Modbus device address
            block_id: V2 block address
            register_count: Number of registers to read

        Returns:
            NormalizedPayload with clean bytes

        Raises:
            ProtocolError: If Modbus error or CRC mismatch
        """
        pass


# ============================================================================
# V2 Parser Layer → Device Model Layer
# ============================================================================

@dataclass
class ParsedBlock:
    """Parsed block result.

    This is the CONTRACT between parser and device model.

    Parser outputs this, device model consumes it.
    """
    # Identity
    block_id: int
    name: str

    # Parsed data (flat dict)
    values: Dict[str, Any]

    # Metadata
    raw: bytes
    length: int
    protocol_version: int
    schema_version: str
    timestamp: float

    # Validation result
    validation: Optional[Any] = None  # ValidationResult

    def to_dict(self) -> dict:
        """Export for JSON/MQTT."""
        return self.values.copy()


class V2ParserInterface(ABC):
    """V2 Parser interface.

    Responsibilities:
    - Parse normalized bytes using schemas
    - Apply transform pipelines
    - Validate against schema

    Does NOT know about:
    - Modbus
    - Transport
    - Device state management
    """

    @abstractmethod
    def parse_block(
        self,
        block_id: int,
        data: bytes,
        validate: bool = True,
        protocol_version: int = 2000
    ) -> ParsedBlock:
        """Parse a V2 block.

        Args:
            block_id: Block ID
            data: Normalized byte buffer (big-endian, no framing)
            validate: Whether to validate against schema
            protocol_version: Device protocol version

        Returns:
            ParsedBlock with parsed values

        Raises:
            ValueError: If block_id not registered or parsing fails
        """
        pass

    @abstractmethod
    def register_schema(self, schema: Any):
        """Register a block schema."""
        pass


# ============================================================================
# Device Model Layer
# ============================================================================

class BlockGroup(Enum):
    """V2 block groups."""
    CORE = "core"           # Block 100 - Dashboard
    GRID = "grid"           # Block 1300 - Grid input
    BATTERY = "battery"     # Block 6000 - Battery pack
    CELLS = "cells"         # Block 6100 - Cell details
    INVERTER = "inverter"   # Blocks 1100, 1400, 1500


@dataclass
class BlockGroupDefinition:
    """Definition of a block group."""
    name: str
    blocks: List[int]  # Block IDs in this group
    description: str
    poll_interval: int = 5  # Recommended poll interval (seconds)


class DeviceModelInterface(ABC):
    """Device model interface.

    Responsibilities:
    - Store device state
    - Map ParsedBlock → device attributes
    - Provide high-level API

    Does NOT know about:
    - Byte offsets
    - Transforms
    - Modbus framing
    """

    @abstractmethod
    def update_from_block(self, parsed: ParsedBlock):
        """Update device state from parsed block.

        Args:
            parsed: ParsedBlock from V2 parser

        This method knows how to map block data to device attributes.
        """
        pass

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """Get complete device state as dict."""
        pass

    @abstractmethod
    def get_group_state(self, group: BlockGroup) -> Dict[str, Any]:
        """Get state for specific block group."""
        pass


# ============================================================================
# Client Layer - Orchestration
# ============================================================================

class BluettiClientInterface(ABC):
    """High-level client interface.

    Responsibilities:
    - Orchestrate layers: transport → protocol → parser → device
    - Device discovery
    - Polling loops
    - Error handling

    This is the PUBLIC API for applications.
    """

    @abstractmethod
    def connect(self):
        """Connect to device."""
        pass

    @abstractmethod
    def read_block(self, block_id: int) -> ParsedBlock:
        """Read and parse a V2 block.

        Args:
            block_id: Block ID to read

        Returns:
            ParsedBlock with parsed data

        Flow:
            1. Build Modbus request (protocol layer)
            2. Send via transport
            3. Normalize response (protocol layer)
            4. Parse (v2_parser)
            5. Update device model
            6. Return ParsedBlock
        """
        pass

    @abstractmethod
    def read_group(self, group: BlockGroup) -> List[ParsedBlock]:
        """Read a block group.

        Args:
            group: BlockGroup to read

        Returns:
            List of ParsedBlock (one per block in group)
        """
        pass

    @abstractmethod
    def get_device_state(self) -> Dict[str, Any]:
        """Get current device state."""
        pass


# ============================================================================
# Device Profile - Configuration
# ============================================================================

@dataclass
class DeviceProfile:
    """Device-specific configuration.

    This is configuration data, not code.
    """
    model: str
    type_id: str
    protocol: str  # "v1" or "v2"
    groups: Dict[str, BlockGroupDefinition]  # Available groups
    description: str


# ============================================================================
# Error Hierarchy
# ============================================================================

class BluettiError(Exception):
    """Base error for all Bluetti errors."""
    pass


class TransportError(BluettiError):
    """Transport layer error (connection, timeout)."""
    pass


class ProtocolError(BluettiError):
    """Protocol layer error (CRC, framing, invalid response)."""
    pass


class ParserError(BluettiError):
    """Parser layer error (unknown block, validation failure)."""
    pass


class DeviceError(BluettiError):
    """Device layer error (invalid state, unsupported operation)."""
    pass
