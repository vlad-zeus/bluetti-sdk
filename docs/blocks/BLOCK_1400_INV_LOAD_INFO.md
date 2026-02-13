# Block 1400 (0x578) - INV_LOAD_INFO

## Block Information
- **Block ID**: 1400 (0x578)
- **Name**: INV_LOAD_INFO
- **Description**: Load output information - DC and AC load power, current, voltage, and energy
- **Source**: `parseInvLoadInfo()` method in ProtocolParserV2.smali

## Field Mappings

### DC Load Summary

| Offset | Size | Field Name | Data Type | Scale | Unit | Description |
|--------|------|------------|-----------|-------|------|-------------|
| 0 | 4 | dcLoadTotalPower | uint32 | 1 | W | Total DC load power across all outputs |
| 4 | 4 | dcLoadTotalEnergy | uint32 | /10.0 | kWh | Cumulative DC load energy consumption |

### DC 5V Output

| Offset | Size | Field Name | Data Type | Scale | Unit | Description |
|--------|------|------------|-----------|-------|------|-------------|
| 8 | 2 | dc5VPower | uint16 | 1 | W | 5V DC output power |
| 10 | 2 | dc5VCurrent | uint16 | /10.0 | A | 5V DC output current |

**Note**: 5V voltage is fixed at 5V (not reported in data)

### DC 12V Output

| Offset | Size | Field Name | Data Type | Scale | Unit | Description |
|--------|------|------------|-----------|-------|------|-------------|
| 12 | 2 | dc12VPower | uint16 | 1 | W | 12V DC output power |
| 14 | 2 | dc12VCurrent | uint16 | /10.0 | A | 12V DC output current |

**Note**: 12V voltage is set to constant 12V in code (offset 12 value, not scaled)

### DC 24V Output

| Offset | Size | Field Name | Data Type | Scale | Unit | Description |
|--------|------|------------|-----------|-------|------|-------------|
| 16 | 2 | dc24VPower | uint16 | 1 | W | 24V DC output power |
| 18 | 2 | dc24VCurrent | uint16 | /10.0 | A | 24V DC output current |

**Note**: 24V voltage is set to constant 24V in code (value 0x18 = 24)

### DC Output Totals

| Offset | Size | Field Name | Data Type | Scale | Unit | Description |
|--------|------|------------|-----------|-------|------|-------------|
| 24 | 2 | dcVoltTotal | uint16 | /10.0 | V | Total DC voltage (aggregate measurement) |
| 26 | 2 | dcCurrentTotal | uint16 | /10.0 | A | Total DC current (aggregate measurement) |

### AC Load Summary

| Offset | Size | Field Name | Data Type | Scale | Unit | Description |
|--------|------|------------|-----------|-------|------|-------------|
| 40 | 4 | acLoadTotalPower | uint32 | 1 | W | Total AC load power across all phases |
| 44 | 4 | acLoadTotalEnergy | uint32 | /10.0 | kWh | Cumulative AC load energy consumption |
| 59 | 1 | sysPhaseNumber | uint8 | 1 | - | Number of AC phases (1 or 3) |

### Per-Phase AC Load (12 bytes per phase)

**Starting offset**: 60 + (phaseIndex × 12)

For each phase (0 to sysPhaseNumber-1):

| Relative Offset | Size | Field Name | Data Type | Scale | Unit | Description |
|-----------------|------|------------|-----------|-------|------|-------------|
| +0 | 2 | loadPower | uint16 | 1 | W | AC load power for this phase |
| +2 | 2 | loadVoltage | uint16 | /10.0 | V | AC load voltage for this phase |
| +4 | 2 | loadCurrent | uint16 | /10.0 | A | AC load current for this phase |
| +6 | 2 | apparent | uint16 | 1 | VA | Apparent power for this phase |
| +8 | 4 | (unused) | - | - | - | Reserved/padding bytes |

## Phase Examples

### Single Phase System (sysPhaseNumber = 1)
- Phase 0 data: Offset 60-71 (12 bytes)

### Three Phase System (sysPhaseNumber = 3)
- Phase 0 data: Offset 60-71 (12 bytes)
- Phase 1 data: Offset 72-83 (12 bytes)
- Phase 2 data: Offset 84-95 (12 bytes)

## Code Analysis Notes

From line 23916-24755 of ProtocolParserV2.smali:

1. **DC Load Total Power** (offset 0-3):
   ```smali
   const/4 v6, 0x4
   const/4 v7, 0x0
   invoke-interface {v0, v7, v6}, Ljava/util/List;->subList(II)Ljava/util/List;
   invoke-static/range {v26 .. v31}, .../bit32RegByteToNumber$default(...)J
   ```

2. **DC voltage constants**:
   - dc12Volt is set to 12 (0xC) directly in code
   - dc24Volt is set to 24 (0x18) directly in code

3. **AC Load phase loop** (line 24478):
   ```smali
   :goto_1
   if-ge v5, v1, :cond_2    # Loop through phases
   mul-int/lit8 v8, v5, 0xc  # phaseIndex * 12
   add-int/lit8 v11, v8, 0x3c  # + 60 (0x3c) = start offset
   ```

4. **Phase data parsing** (lines 24531-24690):
   Each phase parses 8 fields (0-7) within its 12-byte range

## Python Decoding Example

```python
def parse_inv_load_info(data: bytes, phase_num: int = None) -> dict:
    """
    Parse INV_LOAD_INFO block (1400 / 0x578)

    Args:
        data: Raw byte data from device
        phase_num: Number of phases (auto-detected if None)

    Returns:
        Dictionary with load information
    """
    # DC Load totals
    dc_load_total_power = int.from_bytes(data[0:4], 'big')
    dc_load_total_energy = int.from_bytes(data[4:8], 'big') / 10.0

    # DC 5V output
    dc_5v_power = int.from_bytes(data[8:10], 'big')
    dc_5v_current = int.from_bytes(data[10:12], 'big') / 10.0

    # DC 12V output
    dc_12v_power = int.from_bytes(data[12:14], 'big')
    dc_12v_current = int.from_bytes(data[14:16], 'big') / 10.0

    # DC 24V output
    dc_24v_power = int.from_bytes(data[16:18], 'big')
    dc_24v_current = int.from_bytes(data[18:20], 'big') / 10.0

    # DC totals
    dc_volt_total = int.from_bytes(data[24:26], 'big') / 10.0
    dc_current_total = int.from_bytes(data[26:28], 'big') / 10.0

    # AC Load totals
    ac_load_total_power = int.from_bytes(data[40:44], 'big')
    ac_load_total_energy = int.from_bytes(data[44:48], 'big') / 10.0

    # Detect or use phase number
    sys_phase_number = phase_num if phase_num else data[59]

    result = {
        'dcLoadTotalPower': dc_load_total_power,
        'dcLoadTotalEnergy': dc_load_total_energy,
        'dc5VPower': dc_5v_power,
        'dc5VCurrent': dc_5v_current,
        'dc5Volt': 5,  # Fixed value
        'dc12VPower': dc_12v_power,
        'dc12VCurrent': dc_12v_current,
        'dc12Volt': 12,  # Fixed value
        'dc24VPower': dc_24v_power,
        'dc24VCurrent': dc_24v_current,
        'dc24Volt': 24,  # Fixed value
        'dcVoltTotal': dc_volt_total,
        'dcCurrentTotal': dc_current_total,
        'acLoadTotalPower': ac_load_total_power,
        'acLoadTotalEnergy': ac_load_total_energy,
        'sysPhaseNumber': sys_phase_number,
        'phases': []
    }

    # Parse per-phase AC load data
    for phase_idx in range(sys_phase_number):
        base_offset = 60 + (phase_idx * 12)

        # Check if we have enough data
        if base_offset + 8 > len(data):
            break

        load_power = int.from_bytes(data[base_offset:base_offset+2], 'big')
        load_voltage = int.from_bytes(data[base_offset+2:base_offset+4], 'big') / 10.0
        load_current = int.from_bytes(data[base_offset+4:base_offset+6], 'big') / 10.0
        apparent = int.from_bytes(data[base_offset+6:base_offset+8], 'big')

        result['phases'].append({
            'loadPower': load_power,
            'loadVoltage': load_voltage,
            'loadCurrent': load_current,
            'apparent': apparent
        })

    return result
```

## Usage in Home Assistant

This block is essential for monitoring power consumption:

- **DC outputs**: Monitor USB (5V), car port (12V), and other DC loads (24V)
- **AC outputs**: Track household appliance power consumption
- **Energy tracking**: Cumulative energy use for billing/monitoring
- **Load balancing**: Distribute loads across phases in 3-phase systems

### Example MQTT Topics
```
bluetti/inverter/load/dc/total_power
bluetti/inverter/load/dc/total_energy
bluetti/inverter/load/dc/5v/power
bluetti/inverter/load/dc/5v/current
bluetti/inverter/load/dc/12v/power
bluetti/inverter/load/dc/12v/current
bluetti/inverter/load/dc/24v/power
bluetti/inverter/load/dc/24v/current
bluetti/inverter/load/ac/total_power
bluetti/inverter/load/ac/total_energy
bluetti/inverter/load/ac/phase_0/power
bluetti/inverter/load/ac/phase_0/voltage
bluetti/inverter/load/ac/phase_0/current
bluetti/inverter/load/ac/phase_0/apparent
```

## Power Calculation Relationships

For AC loads:
- **Real Power (W)** = loadPower
- **Apparent Power (VA)** = apparent
- **Power Factor** = loadPower / apparent (if apparent > 0)
- **Voltage × Current** ≈ apparent (may not equal exactly due to rounding)

For DC loads:
- **Power (W)** = Voltage × Current
- Example: dc12VPower should approximately equal 12V × dc12VCurrent

## Verification Notes

- Tested against: ProtocolParserV2.smali lines 23916-24755
- Method: `parseInvLoadInfo(Ljava/util/List;I)Lnet/poweroak/bluetticloud/ui/connectv2/bean/InvLoadInfo;`
- Bean class: `InvLoadInfo` with nested `InvACPhaseInfo` objects
- All offsets are byte indices (each list element = 1 byte as hex string)
- DC voltage constants are hardcoded in the parsing logic
