# Block 6100 (0x17D4) - PACK_ITEM_INFO

Individual battery pack detailed information including cell voltages and temperatures.

## Fields

| Offset | Field Name | Type | Scale | Unit | Description |
|--------|-----------|------|-------|------|-------------|
| 1 | pack_id | UINT8 | 1 | - | Pack ID number |
| 2-13 | pack_type | ASCII | - | - | Pack type string (12 bytes) |
| 14-21 | pack_sn | ASCII | - | - | Pack serial number (8 bytes) |
| 22-23 | voltage | UINT16 | 0.01 | V | Pack voltage |
| 24-25 | current | UINT16 | 0.1 | A | Pack current |
| 27 | pack_soc | UINT8 | 1 | % | Pack state of charge |
| 29 | pack_soh | UINT8 | 1 | % | Pack state of health |
| 30-31 | average_temp | UINT16 | 1 | C | Average temperature (raw - 40) |
| 49 | running_status | UINT8 | 1 | - | Running status |
| 51 | charging_status | UINT8 | 1 | - | Charging status |
| 59 | pack_cap_online | UINT8 | 1 | - | Pack capacity online |
| 88-89 | pack_protect | BYTES | - | - | Pack charge protection (2 bytes) |
| 90-91 | pack_protect | BYTES | - | - | Pack discharge protection (2 bytes) |
| 92-99 | pack_sys_err | BYTES | - | - | Pack system error (6 bytes) |
| 100-101 | pack_high_volt_alarm | BYTES | - | - | Pack high voltage alarm (2 bytes) |
| 105 | total_cell_cnt | UINT8 | 1 | - | Total cell count |
| 107 | ntc_cell_cnt | UINT8 | 1 | - | NTC temperature sensor count |
| 109 | bmu_cnt | UINT8 | 1 | - | BMU (Battery Management Unit) count |
| 110-111 | bmu_fault_bit | UINT16 | 1 | - | BMU fault bits (bitmap) |
| 143 | bmu_type | UINT8 | 1 | - | BMU type |
| 128-131 | pack_protect2 | BYTES | - | - | Pack protection status 2 (4 bytes) |
| 134-135 | pack_dcdc_alarm | BYTES | - | - | Pack DC-DC converter alarm (2 bytes) |
| 138-139 | dcdc_protect | UINT16 | 1 | - | DC-DC converter protection status |
| 156 | fm_ver_diff | UINT8 | 1 | - | Firmware version difference |
| 157 | mcu_status | UINT8 | 1 | - | MCU status |
| 158 | pack_type_diff | UINT8 | 1 | - | Pack type difference |
| 159 | software_number | UINT8 | 1 | - | Software number/count |
| 160+ | software_list | BYTES | - | - | Software version list (variable) |
| VAR | fm_list | BYTES | - | - | Firmware list (variable, offset depends on software_number) |

## Sub-Structures

### Cell Voltage Array (via PackSubPackInfo)

Cell voltages are parsed using `parsePackSubPackInfo()` method:

| Field | Type | Scale | Unit | Description |
|-------|------|-------|------|-------------|
| cell_number | UINT8 | 1 | - | Number of cells (from offset 1 or param) |
| ntc_number | UINT8 | 1 | - | Number of NTC sensors (from offset 3 or param) |
| cell_voltages[] | UINT16[] | 0.001 | V | Array of cell voltages |
| cell_temps[] | UINT8[] | 1 | C | Array of cell temperatures (raw - 40) |

**Cell Voltage Parsing** (loop starting at offset 4 or 0):
```
For each cell (i = 0 to cell_number-1):
  offset = i * 2 + base_offset
  raw_value = UINT16 at offset
  voltage = (raw_value & 0x3FFF) / 1000.0  // Mask 14 bits, divide by 1000
  status = (raw_value & 0xC000) >> 14      // Top 2 bits = status
```

**Cell Temperature Parsing** (loop after cell voltages):
```
For each pair of NTC sensors:
  base_offset = cell_number * 2 + base_offset
  offset = pair_index * 2 + base_offset

  If temp count not reached:
    temp1 = UINT8 at (offset + 1) - 40  // Second byte first
    Add temp1 to list

  If temp count still not reached:
    temp2 = UINT8 at offset - 40        // First byte second
    Add temp2 to list
```

### BMU (Battery Management Unit) Info

Parsed via `parsePackBMUInfo(bmuCnt, dataBytes, protocolVersion)`:

Each BMU item contains:
- BMU index
- Device serial number (8 bytes)
- Model string (derived from type: B700, B300K, B300S, B300, or empty)
- Cell count
- NTC count
- Cell index (cumulative)
- NTC index (cumulative)
- Software version (if protocol >= 2010)
- Fault information (4 bytes, parsed as warnings)

## Protection/Alarm Parsing Details

### Pack Charge Protection (offset 88-89)
- Mode: 3
- Map: PackChgProtectStatusNames
- Prefix: "P"
- Code: 0x11

### Pack Discharge Protection (offset 90-91)
- Mode: 3
- Map: PackDsgProtectStatusNames
- Prefix: "P"
- Code: 0x21

### Pack System Error (offset 92-99)
- Mode: 2
- Map: PackHighVoltErrorNames
- Prefix: "P"
- Code: 0x31

### Pack High Voltage Alarm (offset 100-101)
- Mode: 1
- Map: PackHighVoltAlarmNames
- Prefix: "P"
- Code: 0x01

### Pack Protection 2 (offset 128-131)
- Mode: 3
- Map: PackProtectNames
- Prefix: "E"
- Code: 0x51

### Pack DC-DC Alarm (offset 134-135)
- Mode: 1
- Map: PackDCDCAlarmNames
- Prefix: "P"
- Code: 0xA1

### DC-DC Protection (offset 138-139)
- Parsed as UINT16
- Map: PackDCDCProtectNames
- Used as lookup key for protection name

## Notes

- **Temperature Conversion**: All temperatures stored as (raw - 40) to get Celsius
- **Voltage Scale**: Pack voltage uses 0.01 scale, cell voltages use 0.001 scale
- **ASCII Fields**: pack_type and pack_sn are parsed using ASCII conversion
- **Variable Length**: The packet contains variable-length arrays based on counts
- Method: `parsePackItemInfo(List<String> dataBytes)`
- Bean: `PackItemInfo`

## Cell Voltage Bit Structure

Each cell voltage UINT16 is encoded as:
```
Bits 0-13:  Voltage value (multiply by 0.001 for volts)
Bits 14-15: Cell status code
```

Mask operations:
- `raw_value & 0x3FFF` = Extract voltage (14 bits)
- `raw_value & 0xC000` = Extract status (2 bits)
- `status >> 14` = Shift status to bits 0-1

## Example Data Flow

```
Byte 1      -> PackID
Bytes 2-13  -> Convert ASCII to PackType string
Bytes 14-21 -> Convert to device SN
Bytes 22-23 -> Parse as UINT16, divide by 100 = Voltage (V)
Bytes 24-25 -> Parse as UINT16, divide by 10 = Current (A)
Byte 27     -> PackSoc (%)
Byte 29     -> PackSoh (%)
Bytes 30-31 -> Parse as UINT16, subtract 40 = AverageTemp (C)
```

## Related Methods

- `parsePackSubPackInfo(dataBytes, cellNumber, ntcNumber)` - Parses cell voltages and temperatures
- `parsePackBMUInfo(bmuCnt, dataBytes, protocolVersion)` - Parses BMU information
