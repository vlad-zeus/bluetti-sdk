"""V2 Device Model

Device state management for V2 protocol devices.
Maps ParsedBlock → device attributes without knowing about bytes/offsets.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from ..contracts.device import DeviceModelInterface
from ..protocol.v2.types import ParsedBlock
from .types import BlockGroup

logger = logging.getLogger(__name__)


@dataclass
class GridInfo:
    """Grid input information (Block 1300)."""

    frequency: Optional[float] = None  # Hz
    phase_0_voltage: Optional[float] = None  # V
    phase_0_current: Optional[float] = None  # A
    phase_0_power: Optional[int] = None  # W

    # Optional: 3-phase systems
    phase_1_voltage: Optional[float] = None
    phase_2_voltage: Optional[float] = None

    # Energy counters
    total_charge_energy: Optional[int] = None  # Wh
    total_feedback_energy: Optional[int] = None  # Wh

    # Metadata
    last_update: Optional[datetime] = None


@dataclass
class HomeData:
    """Main dashboard data (Block 100)."""

    # Battery
    soc: Optional[int] = None  # %
    pack_voltage: Optional[float] = None  # V
    pack_current: Optional[float] = None  # A
    pack_power: Optional[int] = None  # W
    soh: Optional[int] = None  # %

    # Temperatures
    pack_temp_avg: Optional[int] = None  # °C
    pack_temp_max: Optional[int] = None  # °C
    pack_temp_min: Optional[int] = None  # °C

    # Power flows
    dc_input_power: Optional[int] = None  # W
    ac_input_power: Optional[int] = None  # W
    ac_output_power: Optional[int] = None  # W

    # PV
    pv_power: Optional[int] = None  # W
    pv1_voltage: Optional[float] = None  # V
    pv1_current: Optional[float] = None  # A
    pv2_voltage: Optional[float] = None  # V
    pv2_current: Optional[float] = None  # A

    # Grid
    grid_power: Optional[int] = None  # W (negative = export)

    # Load
    load_power: Optional[int] = None  # W

    # Energy totals
    total_energy_charge: Optional[int] = None  # Wh
    total_energy_discharge: Optional[int] = None  # Wh

    # Metadata
    last_update: Optional[datetime] = None


@dataclass
class BatteryPackInfo:
    """Battery pack information (Block 6000)."""

    soc: Optional[int] = None  # %
    voltage: Optional[float] = None  # V
    current: Optional[float] = None  # A
    power: Optional[int] = None  # W

    temp_max: Optional[int] = None  # °C
    temp_min: Optional[int] = None  # °C
    temp_avg: Optional[int] = None  # °C

    cycles: Optional[int] = None
    soh: Optional[int] = None  # %

    cell_count: Optional[int] = None

    # Status
    charging: Optional[bool] = None
    discharging: Optional[bool] = None

    # Metadata
    last_update: Optional[datetime] = None


class BlockUpdateRegistry:
    """Registry for block_id → update handler mapping.

    Replaces if/elif dispatch with strategy table pattern.
    Supports extensibility via register_handler().
    """

    def __init__(self, device: "V2Device"):
        """Initialize registry with device reference.

        Args:
            device: V2Device instance to update
        """
        self.device = device
        self._handlers: Dict[int, Callable[[ParsedBlock], None]] = {
            100: self.device._update_home_data,
            1300: self.device._update_grid_info,
            6000: self.device._update_battery_pack,
        }

    def update(self, parsed: ParsedBlock) -> None:
        """Dispatch to handler based on block_id.

        Args:
            parsed: ParsedBlock to process
        """
        handler = self._handlers.get(parsed.block_id)
        if handler:
            handler(parsed)
        else:
            logger.warning(f"Unknown block {parsed.block_id} ({parsed.name})")

    def register_handler(
        self,
        block_id: int,
        handler: Callable[[ParsedBlock], None],
    ) -> None:
        """Register custom handler for block_id (extensibility).

        Args:
            block_id: Block ID to handle
            handler: Handler function
        """
        self._handlers[block_id] = handler


class GroupStateRegistry:
    """Registry for group → state getter mapping.

    Replaces if/elif dispatch with strategy table pattern.
    """

    def __init__(self, device: "V2Device"):
        """Initialize registry with device reference.

        Args:
            device: V2Device instance to query
        """
        self.device = device
        self._getters: Dict[BlockGroup, Callable[[], Dict[str, Any]]] = {
            BlockGroup.GRID: self.device._get_grid_state,
            BlockGroup.CORE: self.device._get_core_state,
            BlockGroup.BATTERY: self.device._get_battery_state,
        }

    def get_state(self, group: BlockGroup) -> Dict[str, Any]:
        """Get state for group via registry lookup.

        Args:
            group: BlockGroup to query

        Returns:
            Dict with group-specific attributes
        """
        getter = self._getters.get(group)
        if getter:
            return getter()
        else:
            logger.warning(f"Unknown group: {group}")
            return {}


class V2Device(DeviceModelInterface):
    """V2 protocol device model.

    Stores parsed data from V2 blocks and provides high-level API.
    Does NOT know about byte offsets, transforms, or Modbus.
    """

    def __init__(self, device_id: str, model: str, protocol_version: int = 2000):
        """Initialize V2 device.

        Args:
            device_id: Device serial number or identifier
            model: Device model (e.g., "EL100V2")
            protocol_version: Protocol version (default: 2000)
        """
        self.device_id = device_id
        self.model = model
        self.protocol_version = protocol_version

        # State containers (one per block group)
        self.grid_info = GridInfo()
        self.home_data = HomeData()
        self.battery_pack = BatteryPackInfo()

        # Raw block storage (for debugging)
        self._blocks: Dict[int, ParsedBlock] = {}

        # Last update timestamp
        self.last_update: Optional[datetime] = None

        # Dispatch registries (strategy table pattern)
        self._block_registry = BlockUpdateRegistry(self)
        self._group_registry = GroupStateRegistry(self)

    def update_from_block(self, parsed: ParsedBlock) -> None:
        """Update device state from parsed block.

        Maps ParsedBlock.values → device attributes based on block_id.
        Uses registry dispatch pattern instead of if/elif chains.

        Args:
            parsed: ParsedBlock from V2 parser
        """
        # Store raw block
        self._blocks[parsed.block_id] = parsed
        self.last_update = datetime.now()

        # Dispatch to handler via registry
        self._block_registry.update(parsed)

    def _update_home_data(self, parsed: ParsedBlock) -> None:
        """Update home data from Block 100."""
        values = parsed.values

        # Battery
        self.home_data.soc = values.get("soc")
        self.home_data.pack_voltage = values.get("pack_voltage")
        self.home_data.pack_current = values.get("pack_current")
        self.home_data.pack_power = values.get("pack_power")
        self.home_data.soh = values.get("soh")

        # Temperatures
        self.home_data.pack_temp_avg = values.get("pack_temp_avg")
        self.home_data.pack_temp_max = values.get("pack_temp_max")
        self.home_data.pack_temp_min = values.get("pack_temp_min")

        # Power flows
        self.home_data.dc_input_power = values.get("dc_input_power")
        self.home_data.ac_input_power = values.get("ac_input_power")
        self.home_data.ac_output_power = values.get("ac_output_power")

        # PV
        self.home_data.pv_power = values.get("pv_power")
        self.home_data.pv1_voltage = values.get("pv1_voltage")
        self.home_data.pv1_current = values.get("pv1_current")
        self.home_data.pv2_voltage = values.get("pv2_voltage")
        self.home_data.pv2_current = values.get("pv2_current")

        # Grid
        self.home_data.grid_power = values.get("grid_power")

        # Load
        self.home_data.load_power = values.get("load_power")

        # Energy totals
        self.home_data.total_energy_charge = values.get("total_energy_charge")
        self.home_data.total_energy_discharge = values.get("total_energy_discharge")

        self.home_data.last_update = datetime.now()

        logger.debug(f"Updated home_data: SOC={self.home_data.soc}%")

    def _update_grid_info(self, parsed: ParsedBlock) -> None:
        """Update grid info from Block 1300."""
        values = parsed.values

        self.grid_info.frequency = values.get("frequency")
        self.grid_info.phase_0_voltage = values.get("phase_0_voltage")
        self.grid_info.phase_0_current = values.get("phase_0_current")
        self.grid_info.phase_0_power = values.get("phase_0_power")

        # Optional 3-phase
        self.grid_info.phase_1_voltage = values.get("phase_1_voltage")
        self.grid_info.phase_2_voltage = values.get("phase_2_voltage")

        # Energy counters
        self.grid_info.total_charge_energy = values.get("total_charge_energy")
        self.grid_info.total_feedback_energy = values.get("total_feedback_energy")

        self.grid_info.last_update = datetime.now()

        logger.debug(
            f"Updated grid_info: {self.grid_info.phase_0_voltage}V @ "
            f"{self.grid_info.frequency}Hz"
        )

    def _update_battery_pack(self, parsed: ParsedBlock) -> None:
        """Update battery pack from Block 6000."""
        values = parsed.values

        self.battery_pack.soc = values.get("soc")
        self.battery_pack.voltage = values.get("voltage")
        self.battery_pack.current = values.get("current")
        self.battery_pack.power = values.get("power")

        self.battery_pack.temp_max = values.get("temp_max")
        self.battery_pack.temp_min = values.get("temp_min")
        self.battery_pack.temp_avg = values.get("temp_avg")

        self.battery_pack.cycles = values.get("cycles")
        self.battery_pack.soh = values.get("soh")
        self.battery_pack.cell_count = values.get("cell_count")

        # Status flags
        self.battery_pack.charging = values.get("charging")
        self.battery_pack.discharging = values.get("discharging")

        self.battery_pack.last_update = datetime.now()

        logger.debug(f"Updated battery_pack: SOC={self.battery_pack.soc}%")

    def get_state(self) -> Dict[str, Any]:
        """Get complete device state as flat dict.

        Returns:
            Dict with all device attributes (for MQTT/JSON)
        """
        state = {
            "device_id": self.device_id,
            "model": self.model,
            "protocol_version": self.protocol_version,
            "last_update": self.last_update.isoformat() if self.last_update else None,
        }

        # Grid info
        if self.grid_info.last_update:
            state.update(
                {
                    "grid_frequency": self.grid_info.frequency,
                    "grid_voltage": self.grid_info.phase_0_voltage,
                    "grid_current": self.grid_info.phase_0_current,
                    "grid_power": self.grid_info.phase_0_power,
                }
            )

        # Home data
        if self.home_data.last_update:
            state.update(
                {
                    "soc": self.home_data.soc,
                    "pack_voltage": self.home_data.pack_voltage,
                    "pack_current": self.home_data.pack_current,
                    "pack_power": self.home_data.pack_power,
                    "soh": self.home_data.soh,
                    "pack_temp_avg": self.home_data.pack_temp_avg,
                    "dc_input_power": self.home_data.dc_input_power,
                    "ac_input_power": self.home_data.ac_input_power,
                    "ac_output_power": self.home_data.ac_output_power,
                    "pv_power": self.home_data.pv_power,
                    "grid_power": self.home_data.grid_power,
                    "load_power": self.home_data.load_power,
                }
            )

        # Battery pack
        if self.battery_pack.last_update:
            state.update(
                {
                    "battery_soc": self.battery_pack.soc,
                    "battery_voltage": self.battery_pack.voltage,
                    "battery_current": self.battery_pack.current,
                    "battery_cycles": self.battery_pack.cycles,
                }
            )

        return state

    def get_group_state(self, group: BlockGroup) -> Dict[str, Any]:
        """Get state for specific block group.

        Uses registry dispatch pattern instead of if/elif chains.

        Args:
            group: BlockGroup to retrieve

        Returns:
            Dict with group-specific attributes
        """
        return self._group_registry.get_state(group)

    def _get_grid_state(self) -> Dict[str, Any]:
        """Get grid state (extracted from get_group_state)."""
        return {
            "frequency": self.grid_info.frequency,
            "voltage": self.grid_info.phase_0_voltage,
            "current": self.grid_info.phase_0_current,
            "power": self.grid_info.phase_0_power,
            "last_update": self.grid_info.last_update.isoformat()
            if self.grid_info.last_update
            else None,
        }

    def _get_core_state(self) -> Dict[str, Any]:
        """Get core state (extracted from get_group_state)."""
        return {
            "soc": self.home_data.soc,
            "pack_voltage": self.home_data.pack_voltage,
            "pack_current": self.home_data.pack_current,
            "pack_power": self.home_data.pack_power,
            "last_update": self.home_data.last_update.isoformat()
            if self.home_data.last_update
            else None,
        }

    def _get_battery_state(self) -> Dict[str, Any]:
        """Get battery state (extracted from get_group_state)."""
        return {
            "soc": self.battery_pack.soc,
            "voltage": self.battery_pack.voltage,
            "current": self.battery_pack.current,
            "cycles": self.battery_pack.cycles,
            "soh": self.battery_pack.soh,
            "last_update": self.battery_pack.last_update.isoformat()
            if self.battery_pack.last_update
            else None,
        }

    def get_raw_block(self, block_id: int) -> Optional[ParsedBlock]:
        """Get raw ParsedBlock for debugging.

        Args:
            block_id: Block ID

        Returns:
            ParsedBlock or None if not available
        """
        return self._blocks.get(block_id)
