"""Client layer contract."""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client_services.group_reader import ReadGroupResult
    from ..devices.types import DeviceProfile
    from ..models.types import BlockGroup
    from .types import ParsedRecord


class ClientInterface(ABC):
    """High-level client interface.

    Responsibilities:
    - Orchestrate layers: transport → protocol → parser → device
    - Device discovery
    - Polling loops
    - Error handling

    This is the PUBLIC API for applications.
    """

    @abstractmethod
    def connect(self) -> None:
        """Connect to device."""

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from device."""

    @abstractmethod
    def connect_once(self) -> None:
        """Attempt one connection without internal retry."""

    @property
    @abstractmethod
    def profile(self) -> "DeviceProfile":
        """Device profile bound to this client."""

    @abstractmethod
    def read_block(
        self,
        block_id: int,
        register_count: int | None = None,
        update_state: bool = True,
    ) -> "ParsedRecord":
        """Read and parse a block.

        Args:
            block_id: Block ID to read
            register_count: Optional register count override
            update_state: If True, update device model state

        Returns:
            ParsedRecord with parsed data

        Flow:
            1. Build request (protocol layer)
            2. Send via transport
            3. Normalize response (protocol layer)
            4. Parse (parser)
            5. Update device model
            6. Return ParsedRecord
        """

    @abstractmethod
    def read_group(
        self, group: "BlockGroup", partial_ok: bool = True
    ) -> list["ParsedRecord"]:
        """Read a block group.

        Args:
            group: BlockGroup to read
            partial_ok: If True (default), return partial results on failures.
                       If False, fail fast on first error.

        Returns:
            List of ParsedRecord (one per block in group)
        """

    @abstractmethod
    def read_group_ex(
        self, group: "BlockGroup", partial_ok: bool = False
    ) -> "ReadGroupResult":
        """Read group with per-block error details."""

    @abstractmethod
    def stream_group(
        self, group: "BlockGroup", partial_ok: bool = True
    ) -> Iterator["ParsedRecord"]:
        """Stream group blocks lazily in group order."""

    @abstractmethod
    def get_device_state(self) -> dict[str, Any]:
        """Get current device state."""

    @abstractmethod
    def get_group_state(self, group: "BlockGroup") -> dict[str, Any]:
        """Get state for specific block group.

        Args:
            group: BlockGroup to retrieve

        Returns:
            Dict with group-specific attributes
        """

    @abstractmethod
    def get_available_groups(self) -> list[str]:
        """Get list of available block groups for this device.

        Returns:
            List of group names
        """

    @abstractmethod
    def get_registered_schemas(self) -> dict[int, str]:
        """Get list of registered schemas.

        Returns:
            Dict mapping block_id -> schema_name
        """
