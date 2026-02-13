# V2 Protocol Reverse Engineering Summary

Documentation of Bluetti V2 protocol blocks extracted from APK smali code.

## Project Overview

**Goal**: Reverse engineer battery pack protocol blocks (6000-6500) from Bluetti Android APK
**Source**: `bluetti_smali/smali_classes5/net/poweroak/bluetticloud/ui/connectv2/tools/ProtocolParserV2.smali`
**Method**: Static analysis of decompiled smali bytecode
**Date**: February 13, 2026

## Completed Work

### PACK Blocks Documented (6000-6500 range)

#### Block 6000 (0x1770) - PACK_MAIN_INFO
**Status**: ✅ Complete
**File**: `BLOCK_6000_PACK_MAIN_INFO.md`

Extracted field mappings for main battery pack information:
- Pack voltage type and count (offsets 0-3)
- Pack online status bitmap (offsets 4-5)
- Total voltage, current, SOC, SOH (offsets 6-15)
- Average temperature (offsets 14-15, formula: raw - 40)
- Running and charging status (offsets 17, 19)
- Max charge/discharge limits (offsets 20-25)
- Time to full/empty (offsets 34-37)
- MOS status (offsets 32-33)
- Protection status (offsets 58-61)
- Fault bits (offsets 62-63, conditional)

**Key Findings**:
- Temperature offset formula: `raw_value - 40 = Celsius`
- Voltage scale: 0.1V (divide by 10)
- Current scale: 0.1A (divide by 10)
- Protection parsing uses map lookup with code 0x51

#### Block 6100 (0x17D4) - PACK_ITEM_INFO
**Status**: ✅ Complete
**File**: `BLOCK_6100_PACK_ITEM_INFO.md`

Extracted comprehensive individual pack data structure:
- Pack ID, type, serial number (offsets 1-21)
- Pack voltage (0.01V scale) and current (0.1A scale) (offsets 22-25)
- Pack SOC/SOH (offsets 27, 29)
- Average temperature (offsets 30-31)
- Running/charging status (offsets 49, 51)
- Multiple protection layers (offsets 88-135)
- BMU configuration (offsets 105-143)
- Variable-length arrays for cell voltages and temperatures

**Key Findings**:
- Cell voltage encoding: 14-bit value + 2-bit status in UINT16
  - Voltage: `(raw & 0x3FFF) / 1000.0` Volts
  - Status: `(raw & 0xC000) >> 14`
- Cell temperature: `raw_byte - 40` Celsius
- Multiple protection maps with different parse modes
- Complex BMU structure with cumulative indices

**Sub-Structures Documented**:
- `PackSubPackInfo`: Cell voltage/temperature array parsing
  - Cell voltages: UINT16 array, 0.001V scale
  - Cell temps: UINT8 array, alternating byte pairs
  - Variable offsets based on cell/NTC counts
- `PackBMUInfo`: BMU information container
- `PackBMUItem`: Individual BMU details

#### Block 6300 (0x189C) - PACK_BMU_READ
**Status**: ✅ Complete
**File**: `BLOCK_6300_PACK_BMU_READ.md`

Documented BMU read command structure:
- Read length: 25 bytes (0x19)
- BMU data layout per unit
- Device serial number extraction (8 bytes)
- Cell/NTC count parsing with offset calculations
- Model type identification (B700, B300K, B300S, B300)
- Software version extraction (protocol >= 2010)
- Cumulative index mapping

**Key Findings**:
- BMU index calculation uses alternating even/odd logic
- Cell indices are cumulative across BMUs
- Model type byte: 1=B700, 2=B300K, 3=B300S, 4=B300
- Software version parsing requires protocol check

### Additional Documentation

#### Summary Documents
1. **README_PACK_BLOCKS.md** - Complete PACK blocks overview
   - Block summary table
   - Data flow diagrams
   - Cell voltage/temperature encoding
   - Protection status parsing details
   - Source code references

2. **PACK_BLOCKS_QUICK_REFERENCE.md** - Fast lookup tables
   - Byte offset tables for all fields
   - Common formulas
   - Data type reference
   - Parsing order guide
   - Validation checks

## Technical Discoveries

### Cell Voltage Bit Structure
Discovered 16-bit cell voltage encoding:
```
Bits 0-13:  Voltage value (0-16383 → 0-16.383V)
Bits 14-15: Cell status code (0-3)
```

This allows single UINT16 to carry both voltage and status information.

### Temperature Encoding
Universal temperature formula across all blocks:
```
Celsius = raw_byte - 40
```
Valid range: -40°C to 215°C (stored as 0-255)

### Protection Status Parsing
Multiple protection fields use bitmap parsing with different modes:
- **Mode 1**: Simple bit-to-alarm mapping
- **Mode 2**: Multi-byte error codes
- **Mode 3**: Complex bit pattern matching

Each uses different constant maps for alarm name lookup.

### BMU Index Mapping
BMU data uses cumulative index scheme:
```
BMU 0: cells 0 to N₀-1
BMU 1: cells N₀ to N₀+N₁-1
BMU 2: cells N₀+N₁ to N₀+N₁+N₂-1
```
Same pattern for NTC temperature sensors.

## Parsing Methods Identified

### Main Methods
- `parsePackMainInfo(List<String>)` → PackMainInfo
- `parsePackItemInfo(List<String>)` → PackItemInfo
- `parsePackBMUInfo(int, List<String>, int)` → PackBMUInfo
- `parsePackSubPackInfo(List<String>, int, int)` → PackSubPackInfo

### Helper Methods
- `hexStrToBinaryList()` - Convert hex string to binary list
- `getASCIIStr()` - Extract ASCII string from hex bytes
- `getDeviceSN()` - Parse device serial number
- `getLogInfo()` - Parse protection/alarm bitmaps
- `bit32RegByteToNumber()` - Parse 32-bit integers

### Constant Maps
- PackChgProtectStatusNames
- PackDsgProtectStatusNames
- PackHighVoltErrorNames
- PackHighVoltAlarmNames
- PackProtectNames
- PackDCDCAlarmNames
- PackDCDCProtectNames
- BmuWarnNames

## Block Relationships

```
Block 6000 (PACK_MAIN_INFO)
    ↓ provides pack_cnts
    ↓
Block 6100 (PACK_ITEM_INFO) [for each pack]
    ↓ provides bmu_cnt, cell_cnt, ntc_cnt
    ↓
Block 6300 (PACK_BMU_READ) [optional]
    ↓ provides BMU structure
    ↓
parsePackSubPackInfo()
    ↓ parses cell voltages & temps
    ↓
Final Data: Cell-level voltage and temperature arrays
```

## Implementation Notes

### For Python Implementation
```python
# Temperature conversion
def parse_temp(raw_byte):
    return int(raw_byte, 16) - 40

# Cell voltage from UINT16
def parse_cell_voltage(raw_uint16):
    value = int(raw_uint16, 16)
    voltage = (value & 0x3FFF) / 1000.0
    status = (value & 0xC000) >> 14
    return voltage, status

# Pack voltage
def parse_pack_voltage(byte1, byte2):
    raw = int(byte1 + byte2, 16)
    return raw / 10.0
```

### For Data Validation
- Voltage range: 2.5-4.2V per cell (LiFePO4: 2.5-3.65V)
- Temperature range: -20°C to 60°C (normal operation)
- SOC range: 0-100%
- Cell count: Typically 12-16 per pack
- NTC count: Typically 4-8 per pack

## Files Created

### Block Documentation
1. `BLOCK_6000_PACK_MAIN_INFO.md` (2.5 KB)
2. `BLOCK_6100_PACK_ITEM_INFO.md` (5.9 KB)
3. `BLOCK_6300_PACK_BMU_READ.md` (4.0 KB)

### Summary Files
4. `README_PACK_BLOCKS.md` (7.3 KB)
5. `PACK_BLOCKS_QUICK_REFERENCE.md` (7.4 KB)
6. `REVERSE_ENGINEERING_SUMMARY.md` (this file)

**Total**: 6 markdown files, ~35 KB of documentation

## Source Code Analysis Stats

**File Analyzed**: ProtocolParserV2.smali
- Total size: 913.6 KB
- Total lines: ~32,000
- Methods analyzed: 4 main parsing methods
- Bean classes referenced: 6
- Constant maps identified: 8

**Key Sections**:
- Lines 28898-30167: parsePackItemInfo method
- Lines 30167-31000: parsePackMainInfo method
- Lines 28435-28900: parsePackBMUInfo method
- Lines 31272-31603: parsePackSubPackInfo method

## Methodology

1. **Pattern Recognition**
   - Searched for hex block IDs (0x1770, 0x17D4, 0x189C)
   - Located corresponding switch cases
   - Traced method calls from switch handlers

2. **Method Analysis**
   - Read smali bytecode for parsing methods
   - Identified field setters and offsets
   - Tracked data type conversions (parseInt, divide operations)
   - Mapped local variables to data positions

3. **Bean Structure**
   - Examined bean class constructors
   - Listed setter methods and parameter types
   - Correlated with parsing code

4. **Formula Extraction**
   - Identified arithmetic operations (div-float, add-int)
   - Found constant multipliers (0.1, 0.01, 0.001)
   - Noted offset adjustments (subtract 40 for temperature)

5. **Bitmap Parsing**
   - Located hexStrToBinaryList calls
   - Found getLogInfo method invocations
   - Identified constant map references
   - Documented parse modes and codes

## Challenges Overcome

1. **Large File Size** (913 KB smali file)
   - Solution: Used targeted grep searches and offset-based reading

2. **Complex Control Flow** (goto statements, switch tables)
   - Solution: Traced switch case values to method calls

3. **Variable-Length Arrays**
   - Solution: Identified loop patterns and count-based parsing

4. **Bitmap Encoding**
   - Solution: Found helper methods and constant map references

5. **Cumulative Indices**
   - Solution: Traced cell/NTC index calculations across BMU loops

## Future Work

### Additional Blocks to Investigate
- Other blocks in 6000-6500 range (if any)
- Related command blocks for pack control
- Write commands for pack configuration

### Validation Needed
- Test with real device data
- Verify field mappings with actual values
- Confirm protection status parsing
- Validate BMU index calculations

### Implementation Tasks
- Python parser class for PACK blocks
- MQTT topic mapping for Home Assistant
- Real-time monitoring dashboard
- Cell balance analysis tools

## References

### Source Files
- **Main Parser**: `bluetti_smali/smali_classes5/net/poweroak/bluetticloud/ui/connectv2/tools/ProtocolParserV2.smali`
- **Bean Classes**: `bluetti_smali/smali_classes5/net/poweroak/bluetticloud/ui/connectv2/bean/`
- **Constants**: `bluetti_smali/smali_classes5/net/poweroak/bluetticloud/ui/connectv2/tools/ConnConstantsV2.smali`

### Related Documentation
- V2 protocol overview (if available)
- BLE communication protocol
- Device-specific quirks and variations

## Conclusion

Successfully reverse-engineered three battery pack protocol blocks (6000, 6100, 6300) with comprehensive field mappings, formulas, and parsing details. Documented cell voltage encoding, temperature conversion, protection status parsing, and BMU structure mapping. Created quick reference guides for implementation in Home Assistant integration.

**Status**: PACK blocks (6000-6500) - ✅ Complete
