# Block 1300 (0x514) - INV_GRID_INFO

**Priority: HIGHEST** - Contains critical grid voltage and frequency data!

## Block Information
- **Block ID**: 1300 (0x514)
- **Name**: INV_GRID_INFO
- **Description**: Grid input information - voltage, frequency, power, and energy
- **Source**: `parseInvGridInfo()` method in ProtocolParserV2.smali

## Field Mappings

### Global Fields (Apply to All Phases)

| Offset | Size | Field Name | Data Type | Scale | Unit | Description |
|--------|------|------------|-----------|-------|------|-------------|
| 0 | 2 | frequency | uint16 | /10.0 | Hz | Grid frequency (shared across all phases) |
| 2 | 4 | totalChgPower | uint32 | 1 | W | Total charging power from grid |
| 6 | 4 | totalChgEnergy | uint32 | /10.0 | kWh | Cumulative charging energy from grid |
| 10 | 4 | totalFeedbackEnergy | uint32 | /10.0 | kWh | Cumulative energy fed back to grid |
| 25 | 1 | sysPhaseNumber | uint8 | 1 | - | Number of phases (1 or 3) |

### Per-Phase Fields (12 bytes per phase)

**Starting offset**: 26 + (phaseIndex × 12)

For each phase (0 to sysPhaseNumber-1):

| Relative Offset | Size | Field Name | Data Type | Scale | Unit | Description |
|-----------------|------|------------|-----------|-------|------|-------------|
| +0 | 2 | gridPower | int16 | abs() | W | Grid power for this phase (absolute value) |
| +2 | 2 | gridVoltage | uint16 | /10.0 | V | Grid voltage for this phase |
| +4 | 2 | gridCurrent | int16 | abs()/10.0 | A | Grid current for this phase (absolute value) |
| +6 | 2 | apparent | int16 | abs() | VA | Apparent power (absolute value) |
| +8 | 4 | (unused) | - | - | - | Reserved/padding bytes |

**Note**: The gridFreq field for each phase is copied from the global frequency value (offset 0-1).

## Phase Examples

### Single Phase System (sysPhaseNumber = 1)
- Phase 0 data: Offset 26-37 (12 bytes)

### Three Phase System (sysPhaseNumber = 3)
- Phase 0 data: Offset 26-37 (12 bytes)
- Phase 1 data: Offset 38-49 (12 bytes)
- Phase 2 data: Offset 50-61 (12 bytes)

## Code Analysis Notes

From line 23084-23493 of ProtocolParserV2.smali:

1. **Frequency parsing** (offset 0-1):
   ```smali
   invoke-interface {v0, v5}, Ljava/util/List;->get(I)Ljava/lang/Object;  # get byte 0
   invoke-interface {v0, v7}, Ljava/util/List;->get(I)Ljava/lang/Object;  # get byte 1
   # Concatenate and parse as hex, then divide by 10.0
   ```

2. **Total charge power** (offset 2-5):
   Uses `bit32RegByteToNumber()` helper to parse 4-byte value

3. **Total charge energy** (offset 6-9):
   Parsed as uint32, divided by 10.0 for kWh

4. **Total feedback energy** (offset 10-13):
   Parsed as uint32, divided by 10.0 for kWh

5. **Phase loop** (line 23271):
   ```smali
   mul-int/lit8 v6, v5, 0xc    # phaseIndex * 12
   add-int/lit8 v10, v6, 0x1a  # + 26 (0x1a) = start offset
   add-int/lit8 v6, v6, 0x26   # + 38 (0x26) = end offset
   ```

## Python Decoding Example

```python
def parse_inv_grid_info(data: bytes, phase_num: int = None) -> dict:
    """
    Parse INV_GRID_INFO block (1300 / 0x514)

    Args:
        data: Raw byte data from device
        phase_num: Number of phases (auto-detected if None)

    Returns:
        Dictionary with grid information
    """
    # Global frequency (applies to all phases)
    frequency = int.from_bytes(data[0:2], 'big') / 10.0

    # Total power and energy
    total_chg_power = int.from_bytes(data[2:6], 'big')
    total_chg_energy = int.from_bytes(data[6:10], 'big') / 10.0
    total_feedback_energy = int.from_bytes(data[10:14], 'big') / 10.0

    # Detect or use phase number
    sys_phase_number = phase_num if phase_num else data[25]

    result = {
        'frequency': frequency,
        'totalChgPower': total_chg_power,
        'totalChgEnergy': total_chg_energy,
        'totalFeedbackEnergy': total_feedback_energy,
        'sysPhaseNumber': sys_phase_number,
        'phases': []
    }

    # Parse per-phase data
    for phase_idx in range(sys_phase_number):
        base_offset = 26 + (phase_idx * 12)

        # Parse 2-byte signed integers, take absolute value
        grid_power_raw = int.from_bytes(data[base_offset:base_offset+2], 'big', signed=True)
        grid_power = abs(grid_power_raw)

        grid_voltage = int.from_bytes(data[base_offset+2:base_offset+4], 'big') / 10.0

        grid_current_raw = int.from_bytes(data[base_offset+4:base_offset+6], 'big', signed=True)
        grid_current = abs(grid_current_raw) / 10.0

        apparent_raw = int.from_bytes(data[base_offset+6:base_offset+8], 'big', signed=True)
        apparent = abs(apparent_raw)

        result['phases'].append({
            'gridPower': grid_power,
            'gridVoltage': grid_voltage,
            'gridCurrent': grid_current,
            'apparent': apparent,
            'gridFreq': frequency  # Copy from global
        })

    return result
```

## Usage in Home Assistant

This block is essential for monitoring grid connection status:

- **Grid voltage**: Critical for detecting over/under voltage conditions
- **Grid frequency**: Important for grid stability monitoring
- **Grid power**: Shows how much power is being drawn from or fed to the grid
- **Grid current**: Useful for load balancing calculations

### Example MQTT Topics
```
bluetti/inverter/grid/frequency
bluetti/inverter/grid/total_charge_power
bluetti/inverter/grid/total_charge_energy
bluetti/inverter/grid/total_feedback_energy
bluetti/inverter/grid/phase_0/voltage
bluetti/inverter/grid/phase_0/current
bluetti/inverter/grid/phase_0/power
```

## Verification Notes

- Tested against: ProtocolParserV2.smali lines 23034-23537
- Method: `parseInvGridInfo(Ljava/util/List;I)Lnet/poweroak/bluetticloud/ui/connectv2/bean/InvGridInfo;`
- Bean class: `InvGridInfo` with nested `InvGridPhaseInfo` objects
- All offsets are byte indices (each list element = 1 byte as hex string)
