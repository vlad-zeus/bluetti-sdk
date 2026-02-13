# Block 6300 (0x189C) - PACK_BMU_READ

Read request for Battery Management Unit (BMU) information.

## Purpose

This block is a read command that requests BMU (Battery Management Unit) data from battery packs. It works in conjunction with blocks 6000 and 6100 to retrieve detailed battery pack information.

## Command Details

| Parameter | Value | Description |
|-----------|-------|-------------|
| Block ID | 6300 (0x189C) | Command identifier |
| Read Length | 25 (0x19) | Number of bytes to read |
| Type | Read Command | Request for data |

## Related Parsing

The data returned by this command is parsed using:
- `parsePackBMUInfo(bmuCnt, dataBytes, protocolVersion)` method
- Returns `PackBMUInfo` bean containing:
  - List of `PackBMUItem` objects
  - List of BMU fault information

## PackBMUInfo Structure

Contains two main lists:

### 1. BMU List (List<PackBMUItem>)

Each BMU item includes:
- **bmuIndex**: Index of the BMU (0-based)
- **deviceSN**: Device serial number (8 bytes, parsed from data)
- **model**: Pack model string derived from type:
  - Type 1: "B700"
  - Type 2: "B300K"
  - Type 3: "B300S"
  - Type 4: "B300"
  - Other: "" (empty)
- **cellCnt**: Number of cells managed by this BMU
- **ntcCnt**: Number of NTC temperature sensors
- **cellIndex**: Starting index of cells for this BMU (cumulative)
- **ntcIndex**: Starting index of NTC sensors for this BMU (cumulative)
- **softwareVersion**: Firmware version (if protocol >= 2010/0x7DA)
- **fault**: List of fault/warning information

### 2. BMU Fault List

List of alarm/fault information objects for the BMU system.

## Data Layout (Per BMU)

Each BMU in the data stream occupies:

### Base Information
- **Bytes 0-7**: Device Serial Number (8 bytes, ASCII)

### Fault/Warning Data
- **Offset**: `bmuCnt * 8 + bmuIndex * 4`
- **Length**: 4 bytes
- **Parsing**: Mode 1, Map: BmuWarnNames, Prefix: "P", Code: 0x71

### Cell and NTC Counts
- **Cell Count Offset**: `bmuCnt * 12 + bmuIndex * 2 + 1`
- **NTC Count Offset**: `bmuCnt * 12 + bmuIndex * 2`

### Model Type
- **Offset**: `bmuCnt * 14 + adjustedIndex`
- **Encoding**:
  - Alternates between even/odd BMU indices
  - If bmuIndex is even: use (bmuIndex + 1)
  - If bmuIndex is odd: use (bmuIndex - 1)

### Software Version (if protocol >= 2010)
- **Offset**: Calculated based on BMU count and index
- **Length**: 4 bytes
- **Type**: UINT32 (bit32RegByteToNumber)

## Usage Flow

1. Send read request to block 6300 (0x189C)
2. Receive response with BMU data
3. Parse using `parsePackBMUInfo()`:
   - Loop through each BMU (0 to bmuCnt-1)
   - Extract serial number, counts, model, fault data
   - Build list of BMUItem objects
   - Accumulate cell and NTC indices
4. Use BMU information to understand battery pack structure
5. Reference cell/NTC indices when parsing block 6100 cell data

## Integration with Other Blocks

- **Block 6000** (PACK_MAIN_INFO): Provides overall pack count and status
- **Block 6100** (PACK_ITEM_INFO): Uses BMU cell/NTC indices for detailed voltage/temperature data
- **Block 6300** (PACK_BMU_READ): Provides BMU-level information and structure

## Example BMU Parsing

```
BMU Count = 2

BMU 0:
  Serial Number: Bytes 0-7
  Cell Count: Read from offset 12*2 + 0*2 + 1 = 25
  NTC Count: Read from offset 12*2 + 0*2 = 24
  Model Type: Read from offset 14*2 + 1 = 29 (use odd index)
  Cell Index Start: 0
  NTC Index Start: 0

BMU 1:
  Serial Number: Bytes 8-15
  Cell Count: Read from offset 12*2 + 1*2 + 1 = 27
  NTC Count: Read from offset 12*2 + 1*2 = 26
  Model Type: Read from offset 14*2 + 0 = 28 (use even index)
  Cell Index Start: 0 + BMU0_cellCount
  NTC Index Start: 0 + BMU0_ntcCount
```

## Notes

- BMU count is typically obtained from block 6100's `bmu_cnt` field (offset 109)
- Cell and NTC indices are cumulative across BMUs
- Model type byte determines battery pack model string
- Software version parsing requires protocol version check
- Method: `parsePackBMUInfo(I bmuCnt, List<String> dataBytes, I protocolVersion)`
- Bean: `PackBMUInfo` with lists of `PackBMUItem` and `AlarmFaultInfo`
