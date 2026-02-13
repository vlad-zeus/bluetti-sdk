# PACK Blocks Quick Reference

Fast lookup table for battery pack block field offsets.

## Block 6000 (0x1770) - PACK_MAIN_INFO

| Byte Offset | Bytes | Field | Type | Scale | Unit | Formula/Notes |
|-------------|-------|-------|------|-------|------|---------------|
| 0-1 | 2 | pack_volt_type | UINT16 | 1 | - | Hex parse |
| 3 | 1 | pack_cnts | UINT8 | 1 | - | Hex parse |
| 4-5 | 2 | pack_online | UINT16 | - | bitmap | Convert to binary, find last '1' |
| 6-7 | 2 | total_voltage | UINT16 | 0.1 | V | Parse hex, divide by 10 |
| 8-9 | 2 | total_current | UINT16 | 0.1 | A | Parse hex, divide by 10 |
| 11 | 1 | total_soc | UINT8 | 1 | % | Hex parse |
| 13 | 1 | total_soh | UINT8 | 1 | % | Hex parse |
| 14-15 | 2 | average_temp | UINT16 | 1 | °C | Parse hex, subtract 40 |
| 17 | 1 | running_status | UINT8 | 1 | - | Hex parse |
| 19 | 1 | charging_status | UINT8 | 1 | - | Hex parse |
| 20-21 | 2 | max_chg_voltage | UINT16 | 0.1 | V | Parse hex, divide by 10 |
| 22-23 | 2 | max_chg_current | UINT16 | 0.1 | A | Parse hex, divide by 10 |
| 24-25 | 2 | max_dsg_current | UINT16 | 0.1 | A | Parse hex, divide by 10 |
| 34-35 | 2 | pack_chg_full_time | UINT16 | 1 | min | Hex parse |
| 36-37 | 2 | pack_dsg_empty_time | UINT16 | 1 | min | Hex parse |
| 32-33 | 2 | pack_mos | UINT16 | - | bitmap | Convert to binary |
| 58-61 | 4 | protect_status | BYTES | - | - | Bitmap parse, code 0x51 |
| 62-63 | 2 | pack_fault_bit | UINT16 | - | bitmap | Only if size >= 64 bytes |

**Total Size**: Minimum 62 bytes, 64+ bytes if fault_bit present

## Block 6100 (0x17D4) - PACK_ITEM_INFO

### Fixed Fields

| Byte Offset | Bytes | Field | Type | Scale | Unit | Formula/Notes |
|-------------|-------|-------|------|-------|------|---------------|
| 1 | 1 | pack_id | UINT8 | 1 | - | Hex parse |
| 2-13 | 12 | pack_type | ASCII | - | - | Convert to ASCII string, trim |
| 14-21 | 8 | pack_sn | ASCII | - | - | Device serial number |
| 22-23 | 2 | voltage | UINT16 | 0.01 | V | Parse hex, divide by 100 |
| 24-25 | 2 | current | UINT16 | 0.1 | A | Parse hex, divide by 10 |
| 27 | 1 | pack_soc | UINT8 | 1 | % | Hex parse |
| 29 | 1 | pack_soh | UINT8 | 1 | % | Hex parse |
| 30-31 | 2 | average_temp | UINT16 | 1 | °C | Parse hex, subtract 40 |
| 49 | 1 | running_status | UINT8 | 1 | - | Hex parse |
| 51 | 1 | charging_status | UINT8 | 1 | - | Hex parse |
| 59 | 1 | pack_cap_online | UINT8 | 1 | - | Hex parse |

### Protection/Alarm Fields

| Byte Offset | Bytes | Field | Parse Mode | Map Name | Prefix | Code |
|-------------|-------|-------|------------|----------|--------|------|
| 88-89 | 2 | pack_chg_protect | 3 | PackChgProtectStatusNames | P | 0x11 |
| 90-91 | 2 | pack_dsg_protect | 3 | PackDsgProtectStatusNames | P | 0x21 |
| 92-99 | 6 | pack_sys_err | 2 | PackHighVoltErrorNames | P | 0x31 |
| 100-101 | 2 | pack_high_volt_alarm | 1 | PackHighVoltAlarmNames | P | 0x01 |
| 128-131 | 4 | pack_protect2 | 3 | PackProtectNames | E | 0x51 |
| 134-135 | 2 | pack_dcdc_alarm | 1 | PackDCDCAlarmNames | P | 0xA1 |

### BMU and Structure Fields

| Byte Offset | Bytes | Field | Type | Scale | Unit | Notes |
|-------------|-------|-------|------|-------|------|-------|
| 105 | 1 | total_cell_cnt | UINT8 | 1 | - | Total cells in pack |
| 107 | 1 | ntc_cell_cnt | UINT8 | 1 | - | Total NTC sensors |
| 109 | 1 | bmu_cnt | UINT8 | 1 | - | Number of BMUs |
| 110-111 | 2 | bmu_fault_bit | UINT16 | - | bitmap | BMU fault bitmap |
| 143 | 1 | bmu_type | UINT8 | 1 | - | BMU type code |
| 138-139 | 2 | dcdc_protect | UINT16 | - | - | DCDC protection status |
| 156 | 1 | fm_ver_diff | UINT8 | 1 | - | Firmware version difference |
| 157 | 1 | mcu_status | UINT8 | 1 | - | MCU status |
| 158 | 1 | pack_type_diff | UINT8 | 1 | - | Pack type difference |
| 159 | 1 | software_number | UINT8 | 1 | - | Software count |

### Variable Length Arrays

These require additional parsing via `parsePackSubPackInfo()`:

**Cell Voltages** (starting offset varies, typically after fixed fields):
- Each cell: 2 bytes (UINT16)
- Formula: `(raw & 0x3FFF) / 1000.0` = Voltage in V
- Status: `(raw & 0xC000) >> 14` = Cell status (0-3)
- Count: From `total_cell_cnt` field

**Cell Temperatures** (after cell voltages):
- Each temp: 1 byte (UINT8)
- Formula: `raw - 40` = Temperature in °C
- Stored in pairs per 2-byte word
- Count: From `ntc_cell_cnt` field

**Total Size**: Variable, depends on cell/NTC/BMU counts and software list

## Block 6300 (0x189C) - PACK_BMU_READ

This is a read command, not a data block. Response data layout:

### Per-BMU Structure (variable count)

**Device Serial** (first in sequence):
- Offset: `bmuIndex * 8`
- Length: 8 bytes
- Type: ASCII

**Fault Data** (after all serial numbers):
- Offset: `bmuCnt * 8 + bmuIndex * 4`
- Length: 4 bytes
- Parse: Mode 1, BmuWarnNames, Prefix "P", Code 0x71

**Cell/NTC Counts**:
- NTC Count Offset: `bmuCnt * 12 + bmuIndex * 2`
- Cell Count Offset: `bmuCnt * 12 + bmuIndex * 2 + 1`
- Type: UINT8

**Model Type**:
- Offset: `bmuCnt * 14 + adjustedIndex`
- Adjusted Index: If even use odd, if odd use even
- Mapping: 1=B700, 2=B300K, 3=B300S, 4=B300

**Software Version** (if protocol >= 2010):
- Offset: Complex calculation based on BMU count
- Length: 4 bytes
- Type: UINT32

## Common Formulas

### Temperature Conversion
```
Celsius = raw_byte - 40
Fahrenheit = Celsius * 9/5 + 32
```

### Voltage (Cell - 0.001V scale)
```
raw_value = parse_uint16(bytes)
voltage_mv = raw_value & 0x3FFF    # Mask lower 14 bits
voltage_v = voltage_mv / 1000.0
status = (raw_value >> 14) & 0x03   # Top 2 bits
```

### Voltage (Pack - 0.1V scale)
```
raw_value = parse_uint16(bytes)
voltage_v = raw_value / 10.0
```

### Current (0.1A scale)
```
raw_value = parse_uint16(bytes)
current_a = raw_value / 10.0
```

### Bitmap to Binary List
```
hex_string = "1A2B"
binary = bin(int(hex_string, 16))[2:]  # "0001101000101011"
positions = [i for i, bit in enumerate(reversed(binary)) if bit == '1']
```

## Data Type Reference

| Type | Size | Range | Parse Method |
|------|------|-------|--------------|
| UINT8 | 1 byte | 0-255 | `parseInt(hex, 16)` |
| UINT16 | 2 bytes | 0-65535 | `parseInt(byte1+byte2, 16)` |
| UINT32 | 4 bytes | 0-4294967295 | `bit32RegByteToNumber()` |
| ASCII | Variable | Printable | Convert hex to ASCII |
| BITMAP | Variable | Bit flags | Convert to binary string |

## Parsing Order for Complete Pack Data

1. **Read Block 6000** → Get pack count, total status
2. **Read Block 6100** → Get pack details, BMU count, cell/NTC counts
3. **Optional: Read Block 6300** → Get detailed BMU structure
4. **Parse Cell Arrays** → From Block 6100 using parsePackSubPackInfo
5. **Map Data** → Use BMU indices to map cells to physical packs

## Quick Validation Checks

### Block 6000
- Pack count should be 1-8 (typical)
- Total voltage should match nominal system voltage
- SOC should be 0-100%
- Temperatures should be -40 to 100°C

### Block 6100
- Cell count typically 12-16 per pack
- NTC count typically 4-8 per pack
- Cell voltages typically 2.5-4.2V (LiFePO4: 2.5-3.65V)
- BMU count should match pack count

### Data Consistency
- Sum of individual pack voltages ≈ total voltage (Block 6000)
- Cell count should equal BMU count × cells per BMU
- NTC count should equal BMU count × sensors per BMU

## Error Handling

- **Missing bytes**: Check data length before parsing
- **Invalid values**: Validate ranges (voltage, temp, SOC)
- **Bitmap overflow**: Check bitmap size matches expected bits
- **Array bounds**: Verify cell/NTC counts before parsing arrays
