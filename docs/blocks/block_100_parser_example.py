"""
Block 100 (APP_HOME_DATA) Parser - Reference Implementation

This is a reference implementation showing how to parse Block 100 data
based on the reverse-engineered smali code from ProtocolParserV2.smali

Source: parseHomeData() method, lines 11640-13930
"""

from dataclasses import dataclass
from enum import IntEnum
from typing import List, Optional


class InvPowerType(IntEnum):
    """Inverter power type from offset 45"""

    LOW_POWER = 1  # E series
    HIGH_POWER = 3  # B series
    MICRO_INV = 99  # C series (detected from device model)


@dataclass
class DeviceHomeData:
    """Block 100 data structure matching Java DeviceHomeData class"""

    # Battery Status (offsets 0-11)
    pack_total_voltage: float  # V (offset 0-1, scale 0.1)
    pack_total_current: float  # A (offset 2-3, scale 0.1, signed)
    pack_total_soc: int  # % (offset 4-5)
    pack_charging_status: int  # Status code (offset 6-7)
    pack_chg_full_time: int  # minutes (offset 8-9)
    pack_dsg_empty_time: int  # minutes (offset 10-11)

    # Pack Aging Info (offset 12-13)
    pack_aging_status: int  # From bits 12-15
    pack_aging_progress: int  # From bits 8-11
    pack_aging_fault: int  # From bits 4-7

    # System Info (offsets 15-51)
    pack_cnts: int  # offset 15
    pack_online: List[int]  # offset 16-17 (bitmap)
    can_bus_fault: Optional[List[int]]  # offset 18-19 (v2009+)
    device_model: str  # offset 20-31
    device_sn: str  # offset 32-39
    inv_number: int  # offset 41
    inv_online: List[int]  # offset 42-43 (bitmap)
    inv_power_type: int  # offset 45
    energy_lines: int  # offset 46-47 (bitmap)
    ctrl_status: int  # offset 48-49 (bitmap)
    grid_parallel_soc: int  # offset 51 (%)

    # Alarm/Fault (offsets 52-77, v2001+)
    alarm_info: Optional[int]  # offset 52-59 (64-bit)
    fault_info: Optional[int]  # offset 66-77 (96-bit)

    # Power (offsets 80-99, v2001+)
    total_dc_power: Optional[int]  # W, offset 80-83
    total_ac_power: Optional[int]  # W, offset 84-87
    total_pv_power: Optional[int]  # W, offset 88-91
    total_grid_power: Optional[int]  # W, offset 92-95 (SIGNED!)
    total_inv_power: Optional[int]  # W, offset 96-99

    # Energy (offsets 100-119, v2001+)
    total_dc_energy: Optional[float]  # kWh, offset 100-103, scale 0.1
    total_ac_energy: Optional[float]  # kWh, offset 104-107, scale 0.1
    total_pv_charging_energy: Optional[float]  # kWh, offset 108-111, scale 0.1
    total_grid_charging_energy: Optional[float]  # kWh, offset 112-115, scale 0.1
    total_feedback_energy: Optional[float]  # kWh, offset 116-119, scale 0.1

    # Settings (offsets 121-141, v2001+)
    charging_mode: Optional[int]  # offset 121
    inv_working_status: Optional[int]  # offset 123
    pv_to_ac_energy: Optional[float]  # kWh, offset 124-127, scale 0.1
    self_sufficiency_rate: Optional[int]  # %, offset 129
    pv_to_ac_power: Optional[int]  # W, offset 130-133
    pack_dsg_energy_total: Optional[float]  # kWh, offset 134-137, scale 0.1
    rate_voltage: Optional[int]  # V, offset 138-139
    rate_frequency: Optional[int]  # Hz, offset 140-141

    # Component Status (offsets 142-183, v2001+)
    component_online: Optional[List[int]]  # 7 bits, offset 142-143
    iot_key_status: Optional[List[int]]  # 9 bits, offset 148-149
    scene_flag: Optional[int]  # offset 151
    sleep_standby_time: Optional[int]  # seconds, offset 156-159
    pack_chg_energy_total: Optional[int]  # Wh, offset 160-163
    total_car_power: Optional[int]  # W, offset 164-165
    total_ev_power: Optional[int]  # W, offset 166-169
    feature_status: Optional[List[int]]  # 5 bits, offset 176-177
    switch_recovery_status: Optional[List[int]]  # 3 bits, offset 182-183


def parse_uint16(data: List[str], offset: int) -> int:
    """Parse 2-byte UINT16 from hex string list"""
    high = data[offset]
    low = data[offset + 1]
    hex_str = high + low
    return int(hex_str, 16)


def parse_uint32(data: List[str], offset: int) -> int:
    """Parse 4-byte UINT32 from hex string list"""
    b0 = data[offset]
    b1 = data[offset + 1]
    b2 = data[offset + 2]
    b3 = data[offset + 3]
    hex_str = b0 + b1 + b2 + b3
    return int(hex_str, 16)


def parse_int32(data: List[str], offset: int) -> int:
    """Parse 4-byte INT32 (signed) from hex string list"""
    value = parse_uint32(data, offset)
    # Convert to signed if MSB is set
    if value & 0x80000000:
        value = value - 0x100000000
    return value


def parse_ascii(data: List[str], start: int, end: int) -> str:
    """Parse ASCII string from hex bytes"""
    chars = []
    for i in range(start, end):
        byte_val = int(data[i], 16)
        if byte_val > 0 and byte_val < 127:
            chars.append(chr(byte_val))
    return "".join(chars).strip()


def hex_to_binary_list(hex_str: str) -> List[int]:
    """Convert hex string to list of binary bits (0 or 1)"""
    value = int(hex_str, 16)
    bits = []
    for i in range(16):  # 16 bits for UINT16
        bits.append((value >> i) & 1)
    return bits


def parse_block_100(data: List[str], protocol_version: int = 2001) -> DeviceHomeData:
    """
    Parse Block 100 (APP_HOME_DATA) from hex string list

    Args:
        data: List of hex strings (e.g., ["00", "0A", "FF", ...])
        protocol_version: Protocol version (e.g., 2001, 2009)

    Returns:
        DeviceHomeData object with all parsed fields
    """

    # Basic battery info (always present)
    pack_voltage = parse_uint16(data, 0) / 10.0  # Scale 0.1V
    pack_current = parse_uint16(data, 2) / 10.0  # Scale 0.1A
    pack_soc = parse_uint16(data, 4)
    pack_charging_status = parse_uint16(data, 6)
    pack_chg_full_time = parse_uint16(data, 8)
    pack_dsg_empty_time = parse_uint16(data, 10)

    # Pack aging info (bitfield)
    aging_info = parse_uint16(data, 12)
    # Convert to binary string and extract fields
    aging_binary = bin(aging_info)[2:].zfill(16)
    pack_aging_status = int(aging_binary[0:4], 2)  # bits 12-15
    pack_aging_progress = int(aging_binary[4:8], 2)  # bits 8-11
    pack_aging_fault = int(aging_binary[8:12], 2)  # bits 4-7

    # System info
    pack_cnts = int(data[15], 16)
    pack_cnts = min(pack_cnts, 16)  # Max 16 packs

    pack_online_bits = hex_to_binary_list(data[16] + data[17])
    pack_online = [i for i, bit in enumerate(pack_online_bits[:pack_cnts]) if bit == 1]

    # CAN bus fault (v2009+)
    can_bus_fault = None
    if protocol_version >= 0x7D9:  # 2009
        can_bus_fault = hex_to_binary_list(data[18] + data[19])

    device_model = parse_ascii(data, 20, 32)
    device_sn = parse_ascii(data, 32, 40)
    inv_number = int(data[41], 16)

    inv_online_bits = hex_to_binary_list(data[42] + data[43])
    inv_online = [i for i, bit in enumerate(inv_online_bits) if bit == 1]

    inv_power_type = int(data[45], 16)
    energy_lines = parse_uint16(data, 46)
    ctrl_status = parse_uint16(data, 48)
    grid_parallel_soc = int(data[51], 16)

    # Extended fields (v2001+)
    alarm_info = None
    fault_info = None
    total_dc_power = None
    total_ac_power = None
    total_pv_power = None
    total_grid_power = None
    total_inv_power = None
    total_dc_energy = None
    total_ac_energy = None
    total_pv_charging_energy = None
    total_grid_charging_energy = None
    total_feedback_energy = None
    charging_mode = None
    inv_working_status = None
    pv_to_ac_energy = None
    self_sufficiency_rate = None
    pv_to_ac_power = None
    pack_dsg_energy_total = None
    rate_voltage = None
    rate_frequency = None
    component_online = None
    iot_key_status = None
    scene_flag = None
    sleep_standby_time = None
    pack_chg_energy_total = None
    total_car_power = None
    total_ev_power = None
    feature_status = None
    switch_recovery_status = None

    if protocol_version >= 2001 and len(data) > 80:
        # Alarm/Fault info
        alarm_info = parse_uint32(data, 52)  # Actually 64-bit, simplified here
        fault_info = parse_uint32(data, 66)  # Actually 96-bit, simplified here

        # Power values
        total_dc_power = parse_uint32(data, 80)
        total_ac_power = parse_uint32(data, 84)
        total_pv_power = parse_uint32(data, 88)
        total_grid_power = parse_int32(data, 92)  # SIGNED!
        total_inv_power = parse_uint32(data, 96)

        # Energy values
        total_dc_energy = parse_uint32(data, 100) / 10.0
        total_ac_energy = parse_uint32(data, 104) / 10.0
        total_pv_charging_energy = parse_uint32(data, 108) / 10.0
        total_grid_charging_energy = parse_uint32(data, 112) / 10.0
        total_feedback_energy = parse_uint32(data, 116) / 10.0

        # Settings
        charging_mode = int(data[121], 16)
        inv_working_status = int(data[123], 16)

        if len(data) > 129:
            pv_to_ac_energy = parse_uint32(data, 124) / 10.0
            self_sufficiency_rate = int(data[129], 16)

        if len(data) > 141:
            pv_to_ac_power = parse_uint32(data, 130)
            pack_dsg_energy_total = parse_uint32(data, 134) / 10.0
            rate_voltage = parse_uint16(data, 138)
            rate_frequency = parse_uint16(data, 140)

        # Component status
        if len(data) > 142:
            comp_bits = hex_to_binary_list(data[142] + data[143])
            component_online = comp_bits[:7]

        if len(data) > 148:
            iot_bits = hex_to_binary_list(data[148] + data[149])
            iot_key_status = iot_bits[:9]

        if len(data) > 151:
            scene_flag = int(data[151], 16)

        if len(data) > 169:
            sleep_standby_time = parse_uint32(data, 156)
            pack_chg_energy_total = parse_uint32(data, 160)  # Already in Wh
            total_car_power = parse_uint16(data, 164)
            total_ev_power = parse_uint32(data, 166)

        if len(data) > 177:
            feat_value = parse_uint16(data, 176)
            feature_status = [
                feat_value & 0x1,
                (feat_value >> 1) & 0x1,
                (feat_value >> 2) & 0x1,
                (feat_value >> 3) & 0x1,
                (feat_value >> 8) & 0x1,
            ]

        if len(data) > 183:
            switch_value = parse_uint16(data, 182)
            switch_recovery_status = [
                switch_value & 0x1,
                (switch_value >> 1) & 0x1,
                (switch_value >> 2) & 0x1,
            ]

    return DeviceHomeData(
        pack_total_voltage=pack_voltage,
        pack_total_current=pack_current,
        pack_total_soc=pack_soc,
        pack_charging_status=pack_charging_status,
        pack_chg_full_time=pack_chg_full_time,
        pack_dsg_empty_time=pack_dsg_empty_time,
        pack_aging_status=pack_aging_status,
        pack_aging_progress=pack_aging_progress,
        pack_aging_fault=pack_aging_fault,
        pack_cnts=pack_cnts,
        pack_online=pack_online,
        can_bus_fault=can_bus_fault,
        device_model=device_model,
        device_sn=device_sn,
        inv_number=inv_number,
        inv_online=inv_online,
        inv_power_type=inv_power_type,
        energy_lines=energy_lines,
        ctrl_status=ctrl_status,
        grid_parallel_soc=grid_parallel_soc,
        alarm_info=alarm_info,
        fault_info=fault_info,
        total_dc_power=total_dc_power,
        total_ac_power=total_ac_power,
        total_pv_power=total_pv_power,
        total_grid_power=total_grid_power,
        total_inv_power=total_inv_power,
        total_dc_energy=total_dc_energy,
        total_ac_energy=total_ac_energy,
        total_pv_charging_energy=total_pv_charging_energy,
        total_grid_charging_energy=total_grid_charging_energy,
        total_feedback_energy=total_feedback_energy,
        charging_mode=charging_mode,
        inv_working_status=inv_working_status,
        pv_to_ac_energy=pv_to_ac_energy,
        self_sufficiency_rate=self_sufficiency_rate,
        pv_to_ac_power=pv_to_ac_power,
        pack_dsg_energy_total=pack_dsg_energy_total,
        rate_voltage=rate_voltage,
        rate_frequency=rate_frequency,
        component_online=component_online,
        iot_key_status=iot_key_status,
        scene_flag=scene_flag,
        sleep_standby_time=sleep_standby_time,
        pack_chg_energy_total=pack_chg_energy_total,
        total_car_power=total_car_power,
        total_ev_power=total_ev_power,
        feature_status=feature_status,
        switch_recovery_status=switch_recovery_status,
    )


# Example usage
if __name__ == "__main__":
    # Example data (hex string list)
    # This would come from the device via Bluetooth
    example_data = [
        "00",
        "F0",  # offset 0-1: voltage = 0x00F0 = 240 → 24.0V
        "00",
        "64",  # offset 2-3: current = 0x0064 = 100 → 10.0A
        "00",
        "5A",  # offset 4-5: SoC = 0x005A = 90%
        "00",
        "01",  # offset 6-7: charging status = 1
        "00",
        "3C",  # offset 8-9: time to full = 60 min
        "00",
        "78",  # offset 10-11: time to empty = 120 min
        "00",
        "00",  # offset 12-13: aging info
        "00",  # offset 14: reserved
        "02",  # offset 15: pack count = 2
        "00",
        "03",  # offset 16-17: pack online = 0x0003 (packs 0,1 online)
        # ... more data ...
    ]

    # Note: This is just an example. Real data would be 184 bytes for full block
    # parsed = parse_block_100(example_data, protocol_version=2001)
    # print(f"Battery SoC: {parsed.pack_total_soc}%")
    # print(f"Voltage: {parsed.pack_total_voltage}V")
    # print(f"Current: {parsed.pack_total_current}A")
