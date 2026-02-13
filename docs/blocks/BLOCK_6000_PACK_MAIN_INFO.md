# Block 6000 (0x1770) - PACK_MAIN_INFO

Battery pack main information and status.

## Fields

| Offset | Field Name | Type | Scale | Unit | Description |
|--------|-----------|------|-------|------|-------------|
| 0-1 | pack_volt_type | UINT16 | 1 | - | Pack voltage type |
| 3 | pack_cnts | UINT8 | 1 | - | Number of battery packs |
| 4-5 | pack_online | UINT16 | 1 | - | Pack online status (bitmap) |
| 6-7 | total_voltage | UINT16 | 0.1 | V | Total pack voltage |
| 8-9 | total_current | UINT16 | 0.1 | A | Total pack current |
| 11 | total_soc | UINT8 | 1 | % | Total state of charge |
| 13 | total_soh | UINT8 | 1 | % | Total state of health |
| 14-15 | average_temp | UINT16 | 1 | C | Average temperature (raw - 40) |
| 17 | running_status | UINT8 | 1 | - | Running status |
| 19 | charging_status | UINT8 | 1 | - | Charging status |
| 20-21 | max_chg_voltage | UINT16 | 0.1 | V | Maximum charge voltage |
| 22-23 | max_chg_current | UINT16 | 0.1 | A | Maximum charge current |
| 24-25 | max_dsg_current | UINT16 | 0.1 | A | Maximum discharge current |
| 34-35 | pack_chg_full_time | UINT16 | 1 | min | Time to full charge |
| 36-37 | pack_dsg_empty_time | UINT16 | 1 | min | Time to empty discharge |
| 32-33 | pack_mos | UINT16 | 1 | - | Pack MOS status (bitmap) |
| 58-61 | protect_status | BYTES | - | - | Protection status (4 bytes, parsed as bitmap) |
| 62-63 | pack_fault_bit | UINT16 | 1 | - | Pack fault bits (bitmap, if size >= 64) |

## Notes

- **Temperature Conversion**: Raw value - 40 = Celsius
- **pack_online**: Binary bitmap where each bit represents one pack's online status
- **pack_mos**: Binary bitmap for MOS (Metal-Oxide-Semiconductor) status
- **protect_status**: Parsed using ConnConstantsV2.getPackProtectNames() map, prefix "E", code 0x51
- **pack_fault_bit**: Only present if data size >= 64 bytes
- Method: `parsePackMainInfo(List<String> dataBytes)`
- Bean: `PackMainInfo`

## Protection Status Parsing

The protection status at offset 58-61 (0x3A-0x3E) is parsed as 4 bytes and decoded using:
- Parse mode: 3 (check bit patterns)
- Status map: PackProtectNames
- Code prefix: "E" (Error)
- Status code: 0x51

## Example Data Flow

```
Bytes 0-1   -> PackVoltType
Byte 3      -> PackCnts
Bytes 4-5   -> Convert to binary bitmap, find last "1", use as pack count
Bytes 6-7   -> Parse as UINT16, divide by 10 = TotalVoltage (V)
Bytes 8-9   -> Parse as UINT16, divide by 10 = TotalCurrent (A)
Byte 11     -> TotalSOC (%)
Byte 13     -> TotalSOH (%)
Bytes 14-15 -> Parse as UINT16, subtract 40 = AverageTemp (C)
```
