# Block 1300 (INV_GRID_INFO) - Visual Byte Map

## Priority Block: Grid Voltage & Frequency

This is a visual reference for the most important block - INV_GRID_INFO (1300 / 0x514).

---

## Single Phase Layout (Most Common)

```
Byte Offset:  0    1    2    3    4    5    6    7    8    9   10   11   12   13
             ┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
Content:     │Freq│Freq│TotChgPow│TotChgEng│TotFdBkEn│
             └────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘
             ├─ uint16 ─┤├──── uint32 ───┤├──── uint32 ───┤├──── uint32 ───┤
             ├─ /10.0 ──┤├─────── W ─────┤├──── /10.0 ────┤├──── /10.0 ────┤
             │  Hz       │  Charge Power  │ Charge Energy  │ Feedback Energy│

Byte Offset: 14   15   16   17   18   19   20   21   22   23   24   25
             ┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
Content:     │TotFdBkEn│                 (unused)                    │Phs#│
             └────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘
                                                                      │  1 │

Byte Offset: 26   27   28   29   30   31   32   33   34   35   36   37
             ┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
Content:     │GrdPow │GrdVolt│GrdCur │Apparent │      (unused)        │
             └────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘
Phase 0:     ├─int16─┤├uint16┤├─int16┤├─int16─┤
             ├─abs()─┤├/10.0─┤├abs()─┤├─abs()─┤
             │  W     │  V    │ A/10  │  VA    │
             │        │  ⭐   │       │        │
                        GRID VOLTAGE!
```

---

## Example: Reading Grid Voltage (Single Phase)

### Hex Data Example:
```
Offset 28-29: 0x08 0xFC
```

### Decoding Steps:
1. **Combine bytes** (big-endian): `0x08FC`
2. **Convert to decimal**: 2300
3. **Apply scale** (/10.0): 2300 / 10.0 = **230.0V**

### Python Code:
```python
voltage_raw = int.from_bytes(data[28:30], 'big')  # 2300
voltage = voltage_raw / 10.0                       # 230.0 V
```

---

## Example: Reading Grid Frequency

### Hex Data Example:
```
Offset 0-1: 0x02 0x58
```

### Decoding Steps:
1. **Combine bytes** (big-endian): `0x0258`
2. **Convert to decimal**: 600
3. **Apply scale** (/10.0): 600 / 10.0 = **60.0 Hz**

### Python Code:
```python
frequency_raw = int.from_bytes(data[0:2], 'big')  # 600
frequency = frequency_raw / 10.0                   # 60.0 Hz
```

---

## Three Phase Layout

```
Phase 0 data: Bytes 26-37  (12 bytes)
Phase 1 data: Bytes 38-49  (12 bytes)
Phase 2 data: Bytes 50-61  (12 bytes)

Byte Offset: 26   27   28   29   30   31   32   33   34   35   36   37
             ┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
Phase 0:     │GrdPow │GrdVolt│GrdCur │Apparent │      (unused)        │
             └────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘

Byte Offset: 38   39   40   41   42   43   44   45   46   47   48   49
             ┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
Phase 1:     │GrdPow │GrdVolt│GrdCur │Apparent │      (unused)        │
             └────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘

Byte Offset: 50   51   52   53   54   55   56   57   58   59   60   61
             ┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
Phase 2:     │GrdPow │GrdVolt│GrdCur │Apparent │      (unused)        │
             └────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘
```

---

## Field Details Table

| Field | Byte Offset | Size | Type | Raw Range | Scale | Final Range | Example |
|-------|-------------|------|------|-----------|-------|-------------|---------|
| **Frequency** | 0-1 | 2 | uint16 | 0-65535 | /10.0 | 0-6553.5 Hz | 600 → 60.0 Hz |
| Total Charge Power | 2-5 | 4 | uint32 | 0-4.2B | 1 | 0-4.2B W | 5000 → 5000 W |
| Total Charge Energy | 6-9 | 4 | uint32 | 0-4.2B | /10.0 | 0-420M kWh | 1234 → 123.4 kWh |
| Total Feedback Energy | 10-13 | 4 | uint32 | 0-4.2B | /10.0 | 0-420M kWh | 567 → 56.7 kWh |
| Phase Number | 25 | 1 | uint8 | 1 or 3 | 1 | 1 or 3 | 1 → single phase |
| **Grid Voltage** (P0) | 28-29 | 2 | uint16 | 0-65535 | /10.0 | 0-6553.5 V | 2300 → 230.0 V |
| Grid Current (P0) | 30-31 | 2 | int16 | -32768 to +32767 | abs()/10.0 | 0-3276.7 A | -52 → 5.2 A |
| Grid Power (P0) | 26-27 | 2 | int16 | -32768 to +32767 | abs() | 0-32767 W | -2500 → 2500 W |
| Apparent (P0) | 32-33 | 2 | int16 | -32768 to +32767 | abs() | 0-32767 VA | 2600 → 2600 VA |

---

## Complete Parser Function

```python
def parse_block_1300_grid_info(data: bytes) -> dict:
    """
    Parse Block 1300 (INV_GRID_INFO) - Grid voltage and frequency

    Args:
        data: Raw byte data from block 1300

    Returns:
        Dictionary with all grid parameters

    Example:
        >>> data = bytes.fromhex('02580000138800000064000000320000...')
        >>> result = parse_block_1300_grid_info(data)
        >>> print(f"Grid: {result['phases'][0]['gridVoltage']}V @ {result['frequency']}Hz")
        Grid: 230.0V @ 60.0Hz
    """
    if len(data) < 26:
        raise ValueError("Insufficient data for block 1300")

    # Parse global fields
    frequency = int.from_bytes(data[0:2], 'big') / 10.0
    total_chg_power = int.from_bytes(data[2:6], 'big')
    total_chg_energy = int.from_bytes(data[6:10], 'big') / 10.0
    total_feedback_energy = int.from_bytes(data[10:14], 'big') / 10.0
    sys_phase_number = data[25]

    result = {
        'frequency': frequency,           # Hz
        'totalChgPower': total_chg_power, # W
        'totalChgEnergy': total_chg_energy, # kWh
        'totalFeedbackEnergy': total_feedback_energy, # kWh
        'sysPhaseNumber': sys_phase_number,
        'phases': []
    }

    # Parse per-phase data
    for phase_idx in range(sys_phase_number):
        base_offset = 26 + (phase_idx * 12)

        # Check if we have enough data for this phase
        if base_offset + 8 > len(data):
            break

        # Parse signed values and take absolute value
        grid_power_raw = int.from_bytes(
            data[base_offset:base_offset+2], 'big', signed=True
        )
        grid_power = abs(grid_power_raw)

        grid_voltage = int.from_bytes(
            data[base_offset+2:base_offset+4], 'big'
        ) / 10.0

        grid_current_raw = int.from_bytes(
            data[base_offset+4:base_offset+6], 'big', signed=True
        )
        grid_current = abs(grid_current_raw) / 10.0

        apparent_raw = int.from_bytes(
            data[base_offset+6:base_offset+8], 'big', signed=True
        )
        apparent = abs(apparent_raw)

        result['phases'].append({
            'gridPower': grid_power,       # W
            'gridVoltage': grid_voltage,   # V  ⭐ THIS IS IT!
            'gridCurrent': grid_current,   # A
            'apparent': apparent,          # VA
            'gridFreq': frequency          # Hz (copied from global)
        })

    return result


# Usage example
if __name__ == '__main__':
    # Example hex data (you would get this from your device)
    hex_data = (
        '0258'  # Frequency: 600 → 60.0 Hz
        '00001388'  # Total charge power: 5000 W
        '000004D2'  # Total charge energy: 1234 → 123.4 kWh
        '00000237'  # Total feedback energy: 567 → 56.7 kWh
        '0000000000000000000000'  # Unused bytes
        '01'  # Phase number: 1 (single phase)
        'F63C'  # Grid power: -2500 → 2500 W (negative, take abs)
        '08FC'  # Grid voltage: 2300 → 230.0 V ⭐
        'FFCC'  # Grid current: -52 → 5.2 A (negative, take abs, /10)
        '0A28'  # Apparent: 2600 VA
        '00000000'  # Unused
    )

    data = bytes.fromhex(hex_data)
    result = parse_block_1300_grid_info(data)

    print(f"Grid Frequency: {result['frequency']} Hz")
    print(f"Grid Voltage (Phase 0): {result['phases'][0]['gridVoltage']} V")
    print(f"Grid Current (Phase 0): {result['phases'][0]['gridCurrent']} A")
    print(f"Grid Power (Phase 0): {result['phases'][0]['gridPower']} W")
    print(f"Total Charge Power: {result['totalChgPower']} W")
    print(f"Total Charge Energy: {result['totalChgEnergy']} kWh")

    # Output:
    # Grid Frequency: 60.0 Hz
    # Grid Voltage (Phase 0): 230.0 V  ⭐⭐⭐
    # Grid Current (Phase 0): 5.2 A
    # Grid Power (Phase 0): 2500 W
    # Total Charge Power: 5000 W
    # Total Charge Energy: 123.4 kWh
```

---

## Quick Reference: Get Grid Voltage NOW

### Minimal Code (Just Voltage & Frequency):

```python
def get_grid_essentials(data: bytes) -> tuple:
    """
    Get just the critical values: voltage and frequency

    Returns:
        (frequency_hz, voltage_v)
    """
    frequency = int.from_bytes(data[0:2], 'big') / 10.0
    voltage = int.from_bytes(data[28:30], 'big') / 10.0
    return frequency, voltage

# Usage:
freq, volt = get_grid_essentials(data)
print(f"Grid: {volt}V @ {freq}Hz")
```

---

## Verification Against Smali

**Source**: `ProtocolParserV2.smali`, line 23084-23392

### Frequency (lines 23084-23127):
```smali
invoke-interface {v0, v5}, Ljava/util/List;->get(I)Ljava/lang/Object;  # v5=0
invoke-interface {v0, v7}, Ljava/util/List;->get(I)Ljava/lang/Object;  # v7=1
# Concatenate bytes 0 and 1
const/16 v8, 0x10  # Base 16 (hex)
invoke-static {v6, v9}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;I)I
int-to-float v6, v6
const/high16 v9, 0x41200000    # 10.0f
div-float/2addr v6, v9
invoke-virtual {v4, v6}, .../InvGridInfo;->setFrequency(F)V
```
✅ Confirmed: Offset 0-1, uint16, /10.0

### Grid Voltage (lines 23352-23391):
```smali
# Within phase loop
const/4 v14, 0x3  # Byte 3 of phase data
invoke-interface {v6, v14}, Ljava/util/List;->get(I)Ljava/lang/Object;
# Parse as uint16
int-to-float v12, v12
div-float/2addr v12, v9  # Divide by 10.0
invoke-virtual {v10, v12}, .../InvGridPhaseInfo;->setGridVoltage(F)V
```
✅ Confirmed: Phase offset +2-3, uint16, /10.0

### Phase Base Calculation (line 23275):
```smali
mul-int/lit8 v6, v5, 0xc     # phaseIndex * 12
add-int/lit8 v10, v6, 0x1a   # + 26 (0x1a)
add-int/lit8 v6, v6, 0x26    # + 38 (0x26) = end
```
✅ Confirmed: Base offset 26, 12 bytes per phase

---

## Success! 🎉

**You now have everything needed to read grid voltage and frequency from Block 1300!**

The most critical offsets:
- **Byte 0-1**: Grid frequency (Hz)
- **Byte 28-29**: Grid voltage for phase 0 (V)

Both with `/10.0` scaling factor.

---

**File**: BLOCK_1300_VISUAL_MAP.md
**Created**: 2026-02-13
**Status**: Complete and Verified
