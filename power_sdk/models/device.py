"""Vendor-neutral device model.

Stores parsed block data and plugin-defined state projections.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime
from threading import RLock
from typing import Any

from ..contracts.device import DeviceModelInterface
from ..contracts.types import ParsedRecord
from .types import BlockGroup

logger = logging.getLogger(__name__)


class Device(DeviceModelInterface):
    """Generic device model for parsed protocol data.

    The core model is vendor-neutral: it stores flat state, per-group state,
    and raw parsed blocks. Vendor plugins register block handlers that project
    parsed records into state via ``merge_state``.
    """

    def __init__(self, device_id: str, model: str, protocol_version: int = 0):
        self.device_id = device_id
        self.model = model
        self.protocol_version = protocol_version

        self._blocks: dict[int, ParsedRecord] = {}
        self._state: dict[str, Any] = {}
        self._group_states: dict[BlockGroup, dict[str, Any]] = {}
        self._block_handlers: dict[int, Callable[[ParsedRecord], None]] = {}

        self.last_update: datetime | None = None
        self._state_lock = RLock()

    def register_handler(
        self,
        block_id: int,
        handler: Callable[[ParsedRecord], None],
    ) -> None:
        """Register a block handler callback."""
        with self._state_lock:
            self._block_handlers[block_id] = handler

    def merge_state(
        self,
        values: dict[str, Any],
        *,
        group: BlockGroup | None = None,
    ) -> None:
        """Merge values into flat state and optional group state."""
        now = datetime.now()
        with self._state_lock:
            self._state.update(values)
            if group is not None:
                group_state = self._group_states.setdefault(group, {})
                group_state.update(values)
                group_state["last_update"] = now.isoformat()

    def update_from_block(self, parsed: ParsedRecord) -> None:
        """Store raw block and dispatch to plugin-registered handler."""
        handler: Callable[[ParsedRecord], None] | None
        with self._state_lock:
            self._blocks[parsed.block_id] = parsed
            self.last_update = datetime.now()
            handler = self._block_handlers.get(parsed.block_id)
        if handler is None:
            logger.warning("Unknown block %s (%s)", parsed.block_id, parsed.name)
            return
        handler(parsed)

    def get_state(self) -> dict[str, Any]:
        """Get complete device state as flat dictionary.

        Returns a copy that is safe to mutate: list values are shallow-copied so
        callers cannot corrupt the internal state by appending to returned lists.
        """
        with self._state_lock:
            state: dict[str, Any] = {
                "device_id": self.device_id,
                "model": self.model,
                "protocol_version": self.protocol_version,
                "last_update": (
                    self.last_update.isoformat() if self.last_update else None
                ),
            }
            for k, v in self._state.items():
                state[k] = list(v) if isinstance(v, list) else v
            return state

    def get_group_state(self, group: BlockGroup) -> dict[str, Any]:
        """Get state snapshot for one group."""
        with self._state_lock:
            group_state = self._group_states.get(group)
            if group_state is None:
                return {}
            return dict(group_state)

    def get_raw_block(self, block_id: int) -> ParsedRecord | None:
        """Get raw ParsedRecord for debugging."""
        with self._state_lock:
            return self._blocks.get(block_id)
