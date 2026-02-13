# PACK Blocks Data Flow Diagram

Visual representation of battery pack data structure and parsing flow.

## Overall System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    BATTERY PACK SYSTEM                       │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Pack 1  │  │  Pack 2  │  │  Pack 3  │  │  Pack 4  │   │
│  │  (BMU 1) │  │  (BMU 2) │  │  (BMU 3) │  │  (BMU 4) │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│       │             │             │             │           │
│       └─────────────┴─────────────┴─────────────┘           │
│                          │                                   │
│                    ┌─────▼──────┐                           │
│                    │   System   │                           │
│                    │   BMS      │                           │
│                    └────────────┘                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ V2 Protocol
                            ▼
                    ┌──────────────┐
                    │  BLE/Serial  │
                    └──────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │ Home Asst.   │
                    │ Integration  │
                    └──────────────┘
```

## Block Hierarchy

```
Block 6000 (PACK_MAIN_INFO) - System Level
│
├─ Total Voltage ────────────┐
├─ Total Current ────────────┤
├─ Total SOC ────────────────┤ → Overall Status
├─ Total SOH ────────────────┤
├─ Pack Count ───────────────┤
├─ Pack Online Status ───────┘
├─ Max Charge Limits
├─ Max Discharge Limits
├─ Time Estimates
└─ Protection Status
    │
    ▼
Block 6100 (PACK_ITEM_INFO) - Pack Level (per pack)
│
├─ Pack ID ──────────────────┐
├─ Pack Type ────────────────┤
├─ Pack Serial ──────────────┤ → Pack Identity
├─ Pack Voltage ─────────────┤
├─ Pack Current ─────────────┤
├─ Pack SOC/SOH ─────────────┘
├─ BMU Count ────────────────┐
├─ Cell Count ───────────────┤ → Structure Info
├─ NTC Count ────────────────┘
├─ Protection Status (multiple layers)
│   ├─ Charge Protection
│   ├─ Discharge Protection
│   ├─ System Errors
│   ├─ High Volt Alarms
│   ├─ DCDC Alarms
│   └─ Protection Status 2
│
└─ Cell/Temperature Arrays ──┐
    │                         │
    ▼                         │
parsePackSubPackInfo()        │ → Detailed Cell Data
│                             │
├─ Cell Voltages[] ──────────┤
│   ├─ Cell 1: 3.333V (status 0)
│   ├─ Cell 2: 3.335V (status 0)
│   ├─ ...
│   └─ Cell N: 3.330V (status 0)
│                             │
└─ Cell Temperatures[] ──────┘
    ├─ Temp 1: 25°C
    ├─ Temp 2: 26°C
    ├─ ...
    └─ Temp M: 25°C
    │
    ▼
Block 6300 (PACK_BMU_READ) - BMU Level (optional)
│
└─ BMU Info[] (per BMU)
    ├─ BMU 1
    │   ├─ Serial Number
    │   ├─ Model: "B300K"
    │   ├─ Cell Count: 16
    │   ├─ NTC Count: 8
    │   ├─ Cell Index Start: 0
    │   ├─ NTC Index Start: 0
    │   └─ Software Version
    │
    ├─ BMU 2
    │   ├─ Serial Number
    │   ├─ Model: "B300K"
    │   ├─ Cell Count: 16
    │   ├─ NTC Count: 8
    │   ├─ Cell Index Start: 16
    │   ├─ NTC Index Start: 8
    │   └─ Software Version
    │
    └─ ...
```

## Data Parsing Flow

```
START
  │
  ▼
┌────────────────────┐
│ Read Block 6000    │ → Get system overview
│ (PACK_MAIN_INFO)   │    - Total voltage/current
└─────────┬──────────┘    - Pack count
          │               - Online status
          ▼
┌────────────────────┐
│ For each pack:     │
│ Read Block 6100    │ → Get pack details
│ (PACK_ITEM_INFO)   │    - Pack voltage/current
└─────────┬──────────┘    - BMU/cell/NTC counts
          │               - Protection status
          │
          ├─────────────┐
          │             │
          ▼             ▼
┌──────────────────┐  ┌──────────────────┐
│ Optional:        │  │ Parse Cell Data  │
│ Read Block 6300  │  │ parsePackSub...  │
│ (BMU READ)       │  │                  │
│                  │  │ - Cell voltages  │
│ - BMU structure  │  │ - Cell temps     │
│ - Model info     │  │ - Status flags   │
│ - Index mapping  │  └──────────────────┘
└──────────────────┘           │
          │                    │
          └────────┬───────────┘
                   │
                   ▼
          ┌────────────────┐
          │ Combine Data   │
          │ - Map cells    │
          │ - Validate     │
          │ - Format       │
          └────────┬───────┘
                   │
                   ▼
          ┌────────────────┐
          │ Output to      │
          │ Home Assistant │
          │ MQTT Topics    │
          └────────────────┘
                   │
                   ▼
                  END
```

## Cell Voltage Encoding

```
UINT16 Raw Value (16 bits)
┌──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┐
│15│14│13│12│11│10│ 9│ 8│ 7│ 6│ 5│ 4│ 3│ 2│ 1│ 0│
└──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┘
 │  │  └──────────────────────────────────────┘
 │  │                Voltage Value
 │  │              (0-16383 → 0-16.383V)
 │  │                ÷ 1000 = Volts
 │  │
 └──┘
Status
(0-3)

Example: 0x0D05 (3333 decimal)
  Voltage: 3333 & 0x3FFF = 3333 → 3.333V
  Status:  3333 >> 14    = 0    → Normal
```

## Temperature Encoding

```
UINT8 Raw Value (8 bits)
┌──┬──┬──┬──┬──┬──┬──┬──┐
│ 7│ 6│ 5│ 4│ 3│ 2│ 1│ 0│
└──┴──┴──┴──┴──┴──┴──┴──┘
        │
        ▼
   Temperature + 40

Formula: Celsius = raw_value - 40

Range:
  Raw 0x00 (0)    → -40°C
  Raw 0x28 (40)   →   0°C
  Raw 0x3C (60)   →  20°C
  Raw 0x50 (80)   →  40°C
  Raw 0xFF (255)  → 215°C
```

## Memory Layout Example

### Block 6000 Data Stream
```
Offset: 00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F
Byte:   00 30 00 04 00 0F 0A F0 00 1E 00 64 00 64 00 3C
Field:  └─┬─┘    │  └─┬─┘ └─┬─┘ └─┬─┘    │     │  └─┬─┘
         │       │    │     │     │       │     │    │
    VoltType  PkCnt │   TotV   TotI    SOC  SOH  AvgT
                  PkOnln                          (60-40=20°C)
                  (0x0F = 1111b = 4 packs)

TotV: 0x0AF0 = 2800 → 2800/10 = 280.0V
TotI: 0x001E = 30   → 30/10   = 3.0A
SOC:  0x64   = 100  → 100%
SOH:  0x64   = 100  → 100%
```

### Block 6100 Cell Array
```
Cell Count: 16 cells
NTC Count: 8 sensors

Cells (32 bytes = 16 × 2 bytes):
Offset 0-31:
┌──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┐
│ 0D05 │ 0D06 │ 0D04 │ 0D05 │ 0D05 │ 0D06 │ 0D05 │ 0D04 │
│3.333V│3.334V│3.332V│3.333V│3.333V│3.334V│3.333V│3.332V│
└──────┴──────┴──────┴──────┴──────┴──────┴──────┴──────┘
┌──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┐
│ 0D05 │ 0D05 │ 0D06 │ 0D05 │ 0D04 │ 0D05 │ 0D05 │ 0D06 │
│3.333V│3.333V│3.334V│3.333V│3.332V│3.333V│3.333V│3.334V│
└──────┴──────┴──────┴──────┴──────┴──────┴──────┴──────┘

Temps (8 bytes = 4 × 2 bytes, 8 temps):
Offset 32-39:
┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│ 3D  │ 3C  │ 3D  │ 3C  │ 3E  │ 3C  │ 3D  │ 3C  │
│ 21°C│ 20°C│ 21°C│ 20°C│ 22°C│ 20°C│ 21°C│ 20°C│
└─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘

Note: Temps stored as pairs in 2-byte words:
  Word 1: [byte1=3C, byte0=3D] → temps [3D, 3C]
  Word 2: [byte1=3C, byte0=3D] → temps [3D, 3C]
  ...
```

## BMU Index Mapping

```
System with 2 BMUs:

BMU 0:
  Cell Count: 16
  NTC Count: 8
  Cell Index: 0 to 15
  NTC Index: 0 to 7
  └─► Cells [0-15] in array
      Temps [0-7] in array

BMU 1:
  Cell Count: 16
  NTC Count: 8
  Cell Index: 16 to 31  (starts at 0 + 16)
  NTC Index: 8 to 15    (starts at 0 + 8)
  └─► Cells [16-31] in array
      Temps [8-15] in array

Total Array Sizes:
  Cell Voltage Array: 32 cells × 2 bytes = 64 bytes
  Temperature Array: 16 sensors × 1 byte = 16 bytes
```

## Protection Status Bitmap

```
Pack Protection Status (4 bytes at offset 58-61 in Block 6000):

Byte 1:    Byte 2:    Byte 3:    Byte 4:
┌────────┐┌────────┐┌────────┐┌────────┐
│76543210││76543210││76543210││76543210│
└────────┘└────────┘└────────┘└────────┘
    │         │         │         │
    └─────────┴─────────┴─────────┘
                 │
                 ▼
    Convert to 32-bit binary
                 │
                 ▼
    Lookup each set bit in map
    (PackProtectNames, code 0x51)
                 │
                 ▼
    Generate alarm list

Example:
  Raw: 0x00000040
  Binary: ...0000 0000 0100 0000
  Bit 6 is set → Lookup bit 6 in map
  Result: "Low SOC Protection" (example)
```

## Data Type Size Reference

```
┌──────────┬───────┬─────────────┬───────────────────┐
│   Type   │ Bytes │    Range    │      Example      │
├──────────┼───────┼─────────────┼───────────────────┤
│  UINT8   │   1   │   0-255     │  0x3C = 60        │
│  UINT16  │   2   │   0-65535   │  0x0AF0 = 2800    │
│  UINT32  │   4   │   0-4.29B   │  0x000007D2 = 2010│
│  ASCII   │   N   │  Printable  │  "B300K"          │
│  BITMAP  │   N   │  Bit flags  │  0x0F = 0b1111    │
└──────────┴───────┴─────────────┴───────────────────┘
```

## Parsing State Machine

```
┌─────────┐
│  IDLE   │
└────┬────┘
     │ Request Block 6000
     ▼
┌─────────────┐
│ READING_SYS │
└─────┬───────┘
      │ Receive data
      ▼
┌──────────────┐     Parse Error
│ PARSING_SYS  ├───────────┐
└─────┬────────┘           │
      │ Success            │
      ▼                    │
┌─────────────┐            │
│ READING_PK  │◄───┐       │
└─────┬───────┘    │       │
      │            │       │
      ├─ For each │       │
      │  pack     │       │
      │           │       │
      ▼           │       │
┌──────────────┐  │       │
│ PARSING_PK   ├──┘       │
└─────┬────────┘          │
      │ All parsed        │
      ▼                   │
┌─────────────┐           │
│ READING_BMU │◄──────────┤
└─────┬───────┘ (optional)│
      │                   │
      ▼                   │
┌──────────────┐          │
│ PARSING_BMU  │          │
└─────┬────────┘          │
      │                   │
      ▼                   │
┌─────────────┐           │
│  COMPLETE   │◄──────────┘
└─────┬───────┘
      │
      ▼
┌─────────────┐
│   OUTPUT    │
└─────────────┘
```

## Integration Architecture

```
┌──────────────────────────────────────────────────┐
│                  Bluetti Device                   │
│                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Block    │  │ Block    │  │ Block    │       │
│  │ 6000     │  │ 6100     │  │ 6300     │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       │             │             │              │
└───────┼─────────────┼─────────────┼──────────────┘
        │             │             │
        └─────────────┴─────────────┘
                      │
              ┌───────▼────────┐
              │  BLE/Serial    │
              │  Connection    │
              └───────┬────────┘
                      │
        ┌─────────────▼─────────────┐
        │   Bluetti MQTT Bridge     │
        │                           │
        │  ┌─────────────────────┐  │
        │  │  Protocol Parser    │  │
        │  │  - Block 6000       │  │
        │  │  - Block 6100       │  │
        │  │  - Block 6300       │  │
        │  └─────────────────────┘  │
        │           │               │
        │  ┌────────▼────────┐      │
        │  │ Data Formatter  │      │
        │  │ - Voltages      │      │
        │  │ - Temperatures  │      │
        │  │ - Status        │      │
        │  └────────┬────────┘      │
        └───────────┼───────────────┘
                    │
            ┌───────▼────────┐
            │  MQTT Broker   │
            └───────┬────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
    ┌───▼──────┐         ┌──────▼─────┐
    │   HA     │         │  Grafana   │
    │  Sensors │         │ Dashboard  │
    └──────────┘         └────────────┘
```

## Summary

This diagram shows the complete data flow from battery pack hardware through protocol blocks to Home Assistant integration. Use in conjunction with the detailed documentation files for implementation.
