# V2 Protocol PACK Blocks (6000-6500)

Documentation for Bluetti V2 protocol battery pack blocks reverse-engineered from APK smali code.

## Overview

The PACK blocks provide comprehensive battery pack information including main status, individual pack details, cell voltages, cell temperatures, and BMU (Battery Management Unit) data.

## Block Summary

| Block | Hex | Name | Type | Description |
|-------|-----|------|------|-------------|
| 6000 | 0x1770 | PACK_MAIN_INFO | Data | Overall battery pack system status |
| 6100 | 0x17D4 | PACK_ITEM_INFO | Data | Individual pack details and arrays |
| 6300 | 0x189C | PACK_BMU_READ | Command | Read request for BMU information |

## Block Details

### Block 6000 - PACK_MAIN_INFO
**File:** `BLOCK_6000_PACK_MAIN_INFO.md`

Main battery pack system information:
- Pack voltage type and count
- Total voltage, current, SOC, SOH
- Average temperature
- Running and charging status
- Max charge/discharge limits
- Time to full/empty
- Protection and fault status

**Key Fields:**
- Total Voltage (0.1V scale)
- Total Current (0.1A scale)
- Total SOC/SOH (%)
- Pack count and online status
- MOS status bitmap
- Protection status (4 bytes)

### Block 6100 - PACK_ITEM_INFO
**File:** `BLOCK_6100_PACK_ITEM_INFO.md`

Detailed individual pack information:
- Pack ID, type, serial number
- Pack voltage and current
- Pack SOC and SOH
- Running and charging status
- Cell voltage arrays (via PackSubPackInfo)
- Cell temperature arrays (via PackSubPackInfo)
- BMU information
- Protection and alarm data

**Key Features:**
- **Cell Voltages**: UINT16 array, 0.001V scale, 14-bit value + 2-bit status
- **Cell Temps**: UINT8 array, raw - 40 = Celsius
- **Multiple Protection Layers**: Charge, discharge, system error, DCDC
- **Variable Length**: Depends on cell/NTC/BMU counts

**Related Sub-Structures:**
- `PackSubPackInfo`: Cell voltage and temperature parsing
- `PackBMUInfo`: BMU-level information
- `PackBMUItem`: Individual BMU details

### Block 6300 - PACK_BMU_READ
**File:** `BLOCK_6300_PACK_BMU_READ.md`

Read command for BMU data:
- Request 25 bytes of BMU information
- Returns BMU list with device info
- Provides cell/NTC index mapping
- Includes model identification

**BMU Item Details:**
- Device serial number
- Cell and NTC counts per BMU
- Model type (B700, B300K, B300S, B300)
- Software version (protocol >= 2010)
- Fault/warning information

## Data Flow

### Reading Pack Information

1. **Read Block 6000** (PACK_MAIN_INFO)
   - Get overall pack count
   - Get total voltage, current, SOC
   - Check online status of packs

2. **Read Block 6100** (PACK_ITEM_INFO)
   - Get individual pack details
   - Extract BMU count from offset 109
   - Note cell and NTC counts

3. **Read Block 6300** (PACK_BMU_READ) if needed
   - Get detailed BMU structure
   - Map cell indices to BMUs
   - Identify pack models

4. **Parse Cell Data** (from Block 6100)
   - Use `parsePackSubPackInfo()` method
   - Extract cell voltages with status
   - Extract cell temperatures
   - Map to BMU indices

## Cell Voltage Encoding

Cell voltages in block 6100 use a special 16-bit encoding:

```
UINT16 raw_value:
  Bits 0-13:  Voltage (raw & 0x3FFF) / 1000.0 = Volts
  Bits 14-15: Cell status (raw & 0xC000) >> 14
```

Example:
```
Raw: 0x0D05 = 3333 decimal
Voltage: 3333 & 0x3FFF = 3333 / 1000.0 = 3.333V
Status: (3333 & 0xC000) >> 14 = 0
```

## Temperature Encoding

All temperatures use the same encoding:
```
Celsius = raw_byte - 40
```

Example:
```
Raw: 0x3C (60 decimal)
Temperature: 60 - 40 = 20°C
```

## Protection Status Parsing

Multiple protection/alarm fields use bitmap parsing:

| Field | Offset | Bytes | Mode | Map Name | Prefix | Code |
|-------|--------|-------|------|----------|--------|------|
| Pack Charge Protect | 88-89 | 2 | 3 | PackChgProtectStatusNames | P | 0x11 |
| Pack Discharge Protect | 90-91 | 2 | 3 | PackDsgProtectStatusNames | P | 0x21 |
| Pack System Error | 92-99 | 6 | 2 | PackHighVoltErrorNames | P | 0x31 |
| Pack High Volt Alarm | 100-101 | 2 | 1 | PackHighVoltAlarmNames | P | 0x01 |
| Pack Protect 2 | 128-131 | 4 | 3 | PackProtectNames | E | 0x51 |
| Pack DCDC Alarm | 134-135 | 2 | 1 | PackDCDCAlarmNames | P | 0xA1 |

Parse modes are defined in the `getLogInfo()` method from ProtocolParse.

## Source Code References

### Main Parsing Methods
- `parsePackMainInfo(List<String> dataBytes)` - Block 6000
- `parsePackItemInfo(List<String> dataBytes)` - Block 6100
- `parsePackBMUInfo(int bmuCnt, List<String> dataBytes, int protocolVersion)` - Block 6300 data
- `parsePackSubPackInfo(List<String> dataBytes, int cellNumber, int ntcNumber)` - Cell arrays

### Bean Classes
- `PackMainInfo` - Main pack information bean
- `PackItemInfo` - Individual pack information bean
- `PackBMUInfo` - BMU information container
- `PackBMUItem` - Individual BMU details
- `PackSubPackInfo` - Cell voltage/temperature arrays
- `PackCellsInfo` - Individual cell voltage with status

### Constants Maps
- `PackChgProtectStatusNames` - Charge protection status names
- `PackDsgProtectStatusNames` - Discharge protection status names
- `PackHighVoltErrorNames` - High voltage error names
- `PackHighVoltAlarmNames` - High voltage alarm names
- `PackProtectNames` - General protection names
- `PackDCDCAlarmNames` - DC-DC converter alarm names
- `PackDCDCProtectNames` - DC-DC converter protection names
- `BmuWarnNames` - BMU warning names

## Implementation Notes

### Array Parsing
When parsing cell voltages and temperatures:
1. Cell voltages: Loop through cell count, read UINT16 at offset (i*2 + base)
2. Apply bit mask (0x3FFF) and divide by 1000 for voltage
3. Extract status from top 2 bits
4. Cell temps: Loop through NTC count in pairs, read alternating bytes
5. Subtract 40 from each temperature byte

### BMU Mapping
BMU indices are cumulative:
- BMU 0 starts at cell index 0
- BMU 1 starts at cell index (BMU0 cell count)
- BMU 2 starts at cell index (BMU0 + BMU1 cell counts)
- Same pattern for NTC indices

### Protocol Version
Some features depend on protocol version:
- BMU software version requires protocol >= 2010 (0x7DA)
- Check protocol version before parsing certain fields

## Example Use Cases

### Get Total Pack Status
1. Read block 6000
2. Parse total voltage, current, SOC
3. Check charging/running status
4. Monitor protection alarms

### Get Individual Cell Voltages
1. Read block 6100
2. Parse cell count from data
3. Use parsePackSubPackInfo to extract voltages
4. Monitor cell balance and min/max voltages

### Identify Battery Configuration
1. Read block 6300 for BMU info
2. Check model type for each BMU
3. Map cell indices to physical packs
4. Determine total system configuration

## Files in This Directory

- `BLOCK_6000_PACK_MAIN_INFO.md` - Block 6000 documentation
- `BLOCK_6100_PACK_ITEM_INFO.md` - Block 6100 documentation
- `BLOCK_6300_PACK_BMU_READ.md` - Block 6300 documentation
- `README_PACK_BLOCKS.md` - This summary file

## Reverse Engineering Source

All information extracted from:
- **File**: `bluetti_smali/smali_classes5/net/poweroak/bluetticloud/ui/connectv2/tools/ProtocolParserV2.smali`
- **APK**: Bluetti Android application
- **Method**: Static analysis of smali bytecode

## Related Documentation

See also:
- Main V2 protocol documentation (if available)
- Device-specific field mappings
- BLE communication protocol
- Error code definitions
