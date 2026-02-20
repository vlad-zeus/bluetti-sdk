"""DeviceRuntime — poll-cycle lifecycle wrapper over Client."""

from __future__ import annotations

import contextlib
import time
from dataclasses import dataclass, field
from typing import Any

from ..client import Client
from ..models.types import BlockGroup


@dataclass
class DeviceSnapshot:
    """Immutable result of a single poll cycle."""

    device_id: str
    model: str
    timestamp: float
    state: dict[str, Any]
    blocks_read: int
    duration_ms: float = 0.0
    error: Exception | None = field(default=None, compare=False)

    @property
    def ok(self) -> bool:
        return self.error is None


class DeviceRuntime:
    """Wraps Client with poll-cycle lifecycle and snapshot capture.

    vendor, protocol, profile_id, transport_key are stored from YAML
    runtime context — DeviceProfile is NOT modified.
    """

    def __init__(
        self,
        device_id: str,
        client: Client,
        *,
        vendor: str,
        protocol: str,
        profile_id: str,
        transport_key: str,
        poll_interval: float = 30.0,
        sink_name: str = "memory",
        pipeline_name: str = "direct",
        mode: str = "pull",
    ) -> None:
        self.device_id = device_id
        self.client = client
        self.vendor = vendor
        self.protocol = protocol
        self.profile_id = profile_id
        self.transport_key = transport_key
        self.poll_interval = poll_interval
        self.sink_name = sink_name
        self.pipeline_name = pipeline_name
        self.mode = mode
        self._last_snapshot: DeviceSnapshot | None = None

    def poll_once(
        self,
        connect: bool = False,
        disconnect: bool = False,
    ) -> DeviceSnapshot:
        """Read device state once, return snapshot.

        Args:
            connect: Call client.connect() before reading.
            disconnect: Call client.disconnect() after reading (even on error).
        """
        t = time.time()
        t0 = time.monotonic()
        try:
            if connect:
                self.client.connect()
            # Read CORE group; partial_ok so one block failure doesn't abort all
            blocks = self.client.read_group(BlockGroup.CORE, partial_ok=True)
            state = self.client.get_device_state()
            snapshot = DeviceSnapshot(
                device_id=self.device_id,
                model=self.client.profile.model,
                timestamp=t,
                state=state,
                blocks_read=len(blocks),
                duration_ms=(time.monotonic() - t0) * 1000.0,
            )
        except Exception as exc:
            snapshot = DeviceSnapshot(
                device_id=self.device_id,
                model=self.client.profile.model,
                timestamp=t,
                state={},
                blocks_read=0,
                duration_ms=(time.monotonic() - t0) * 1000.0,
                error=exc,
            )
        finally:
            if disconnect:
                with contextlib.suppress(Exception):
                    self.client.disconnect()

        self._last_snapshot = snapshot
        return snapshot

    @property
    def last_snapshot(self) -> DeviceSnapshot | None:
        return self._last_snapshot
