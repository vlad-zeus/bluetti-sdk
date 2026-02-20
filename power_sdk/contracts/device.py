"""Device model layer contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable

from .types import ParsedRecord

if TYPE_CHECKING:
    from ..models.types import BlockGroup


class DeviceModelInterface(ABC):
    """Device model interface.

    Responsibilities:
    - Store device state
    - Map ParsedRecord → device attributes
    - Provide high-level API

    Does NOT know about:
    - Byte offsets
    - Transforms
    - Protocol framing
    """

    @abstractmethod
    def update_from_block(self, parsed: ParsedRecord) -> None:
        """Update device state from parsed record."""

    @abstractmethod
    def register_handler(
        self,
        block_id: int,
        handler: Callable[[ParsedRecord], None],
    ) -> None:
        """Register a block handler callback."""

    @abstractmethod
    def get_state(self) -> dict[str, Any]:
        """Get complete device state as dict."""

    @abstractmethod
    def get_group_state(self, group: BlockGroup) -> dict[str, Any]:
        """Get state for specific block group."""
