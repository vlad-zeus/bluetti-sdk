# Block 1500 (0x5DC) - INV_INV_INFO

## Block Information
- **Block ID**: 1500 (0x5DC)
- **Name**: INV_INV_INFO
- **Description**: Inverter output information - inverter voltage, current, power, frequency, and energy
- **Source**: `parseInvInvInfo()` method in ProtocolParserV2.smali

## Field Mappings

### Global Fields (Apply to All Phases)

| Offset | Size | Field Name | Data Type | Scale | Unit | Description |
|--------|------|------------|-----------|-------|------|-------------|
| 0 | 2 | frequency | uint16 | /10.0 | Hz | Inverter output frequency (shared across all phases) |
| 2 | 4 | totalEnergy | uint32 | /10.0 | kWh | Cumulative energy produced by inverter |
| 17 | 1 | sysPhaseNumber | uint8 | 1 | - | Number of phases (1 or 3) |

### Per-Phase Fields (12 bytes per phase)

**Starting offset**: 18 + (phaseIndex × 12)

For each phase (0 to sysPhaseNumber-1):

| Relative Offset | Size | Field Name | Data Type | Scale | Unit | Description |
|-----------------|------|------------|-----------|-------|------|-------------|
| +0 | 1 | (unused) | - | - | - | Reserved byte |
| +1 | 1 | workStatus | uint8 | 1 | - | Work status code for this phase |
| +2 | 2 | invPower | uint16 | 1 | W | Inverter output power for this phase |
| +4 | 2 | invVoltage | uint16 | /10.0 | V | Inverter output voltage for this phase |
| +6 | 2 | invCurrent | uint16 | /10.0 | A | Inverter output current for this phase |
| +8 | 4 | (unused) | - | - | - | Reserved/padding bytes |

**Note**: The invFreq field for each phase is copied from the global frequency value (offset 0-1).

## Phase Examples

### Single Phase System (sysPhaseNumber = 1)
- Phase 0 data: Offset 18-29 (12 bytes)

### Three Phase System (sysPhaseNumber = 3)
- Phase 0 data: Offset 18-29 (12 bytes)
- Phase 1 data: Offset 30-41 (12 bytes)
- Phase 2 data: Offset 42-53 (12 bytes)

## Work Status Codes

The `workStatus` field indicates the operational state of each phase:

| Code | Status | Description |
|------|--------|-------------|
| 0 | Standby | Inverter phase is idle/off |
| 1 | Running | Inverter phase is actively producing power |
| 2 | Fault | Inverter phase has encountered an error |
| 3 | Bypass | Inverter phase is in bypass mode |

**Note**: Exact status codes may vary by device model. Refer to device documentation for specific meanings.

## Code Analysis Notes

From line 23537-23914 of ProtocolParserV2.smali:

1. **Frequency parsing** (offset 0-1):
   ```smali
   invoke-interface {v0, v4}, Ljava/util/List;->get(I)Ljava/lang/Object;  # get byte 0
   const/4 v6, 0x1
   invoke-interface {v0, v6}, Ljava/util/List;->get(I)Ljava/lang/Object;  # get byte 1
   # Concatenate, parse as hex, divide by 10.0
   int-to-float v5, v5
   const/high16 v8, 0x41200000    # 10.0f
   div-float/2addr v5, v8
   ```

2. **Total energy** (offset 2-5):
   ```smali
   const/4 v5, 0x6
   const/4 v15, 0x2
   invoke-interface {v0, v15, v5}, Ljava/util/List;->subList(II)Ljava/util/List;
   invoke-static/range {v9 .. v14}, .../bit32RegByteToNumber$default(...)J
   long-to-float v9, v9
   div-float/2addr v9, v8  # Divide by 10.0
   ```

3. **System phase number** (offset 17):
   ```smali
   const/16 v9, 0x11  # 17 decimal
   invoke-interface {v0, v9}, Ljava/util/List;->get(I)Ljava/lang/Object;
   invoke-static {v9, v10}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;I)I
   ```

4. **Phase loop** (line 23679):
   ```smali
   :goto_0
   if-ge v4, v9, :cond_0    # Loop through phases
   mul-int/lit8 v10, v4, 0xc  # phaseIndex * 12
   add-int/lit8 v11, v10, 0x12  # + 18 (0x12) = start offset
   add-int/lit8 v10, v10, 0x1e  # + 30 (0x1e) = end offset
   ```

5. **Work status** (line 23715):
   ```smali
   invoke-interface {v10, v6}, Ljava/util/List;->get(I)Ljava/lang/Object;  # v6=1 (byte 1 of phase data)
   invoke-static {v12, v13}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;I)I
   invoke-virtual {v11, v12}, .../InvPhaseInfo;->setWorkStatus(I)V
   ```

6. **Frequency copy** (line 23852):
   ```smali
   invoke-virtual {v3}, .../InvInvInfo;->getFrequency()F
   invoke-virtual {v11, v10}, .../InvPhaseInfo;->setInvFreq(F)V
   ```

## Python Decoding Example

```python
def parse_inv_inv_info(data: bytes) -> dict:
    """
    Parse INV_INV_INFO block (1500 / 0x5DC)

    Args:
        data: Raw byte data from device

    Returns:
        Dictionary with inverter output information
    """
    # Global frequency (applies to all phases)
    frequency = int.from_bytes(data[0:2], 'big') / 10.0

    # Total energy produced
    total_energy = int.from_bytes(data[2:6], 'big') / 10.0

    # System phase number
    sys_phase_number = data[17]

    result = {
        'frequency': frequency,
        'totalEnergy': total_energy,
        'sysPhaseNumber': sys_phase_number,
        'phases': []
    }

    # Parse per-phase data
    for phase_idx in range(sys_phase_number):
        base_offset = 18 + (phase_idx * 12)

        # Check if we have enough data
        if base_offset + 8 > len(data):
            break

        work_status = data[base_offset + 1]
        inv_power = int.from_bytes(data[base_offset+2:base_offset+4], 'big')
        inv_voltage = int.from_bytes(data[base_offset+4:base_offset+6], 'big') / 10.0
        inv_current = int.from_bytes(data[base_offset+6:base_offset+8], 'big') / 10.0

        result['phases'].append({
            'workStatus': work_status,
            'invPower': inv_power,
            'invVoltage': inv_voltage,
            'invCurrent': inv_current,
            'invFreq': frequency  # Copy from global
        })

    return result
```

## Usage in Home Assistant

This block is essential for monitoring inverter output performance:

- **Inverter frequency**: Ensure output frequency matches grid requirements (50Hz or 60Hz)
- **Inverter voltage**: Monitor output voltage stability
- **Inverter power**: Track actual power being inverted from DC to AC
- **Work status**: Detect operational issues or phase-specific faults
- **Total energy**: Cumulative energy production tracking

### Example MQTT Topics
```
bluetti/inverter/output/frequency
bluetti/inverter/output/total_energy
bluetti/inverter/output/phase_count
bluetti/inverter/output/phase_0/status
bluetti/inverter/output/phase_0/power
bluetti/inverter/output/phase_0/voltage
bluetti/inverter/output/phase_0/current
```

### Work Status Monitoring

Create automations based on work status:

```yaml
# Example Home Assistant automation
automation:
  - alias: "Inverter Phase Fault Alert"
    trigger:
      - platform: state
        entity_id: sensor.inverter_phase_0_status
        to: "2"  # Fault status
    action:
      - service: notify.notify
        data:
          title: "Inverter Alert"
          message: "Inverter Phase 0 has encountered a fault!"
```

## Power Calculation

For each phase:
- **Expected Power** = invVoltage × invCurrent
- **Reported Power** = invPower

These should approximately match (within 5-10% due to power factor and rounding).

If there's a large discrepancy:
1. Check work status - may indicate a fault
2. Verify voltage and current readings are valid
3. Consider reactive power component (not reported separately)

## Frequency Monitoring

Typical frequency values:
- **North America / Japan**: ~60 Hz (59.5-60.5 Hz range)
- **Europe / Asia / Australia**: ~50 Hz (49.5-50.5 Hz range)

Alert conditions:
- **Warning**: Frequency outside ±0.5 Hz of nominal
- **Critical**: Frequency outside ±1.0 Hz of nominal

## Verification Notes

- Tested against: ProtocolParserV2.smali lines 23537-23914
- Method: `parseInvInvInfo(Ljava/util/List;)Lnet/poweroak/bluetticloud/ui/connectv2/bean/InvInvInfo;`
- Bean class: `InvInvInfo` with nested `InvPhaseInfo` objects
- All offsets are byte indices (each list element = 1 byte as hex string)
- Global frequency is copied to each phase's invFreq field
