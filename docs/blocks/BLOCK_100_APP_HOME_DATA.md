# Block 100 (0x64): APP_HOME_DATA - Main Dashboard Data

**Source**: `ProtocolParserV2.smali` - `parseHomeData()` method (lines 11640-13930)

This is the **PRIMARY** block for Elite V2 devices, containing all main dashboard information including battery status, power flows, energy statistics, and system configuration.

## Field Mapping Table

| Byte Offset | Field Name | Type | Scale | Unit | Notes | Smali Line |
|-------------|------------|------|-------|------|-------|------------|
| 0-1 | packTotalVoltage | UINT16 | 0.1 | V | Battery pack total voltage | 11792-11835 |
| 2-3 | packTotalCurrent | UINT16 | 0.1 | A | Battery pack total current (signed in practice) | 11840-11878 |
| 4-5 | packTotalSoc | UINT16 | 1.0 | % | Battery State of Charge | 11883-11917 |
| 6-7 | packChargingStatus | UINT16 | 1.0 | - | Pack charging status code | 11922-11956 |
| 8-9 | packChgFullTime | UINT16 | 1.0 | min | Time to full charge | 11961-11995 |
| 10-11 | packDsgEmptyTime | UINT16 | 1.0 | min | Time to empty discharge | 12000-12034 |
| 12-13 | packAgingInfo | UINT16 | - | - | Aging info bitfield (see below) | 12039-12122 |
| 15 | packCnts | UINT8 | 1.0 | - | Number of battery packs (max 16) | 12127-12145 |
| 16-17 | packOnline | UINT16 | - | bits | Pack online status bitmap | 12150-12235 |
| 18-19 | canBusFault | UINT16 | - | bits | CAN bus fault bitmap (v2009+) | 12244-12274 |
| 20-31 | deviceModel | ASCII | - | - | Device model string (12 bytes) | 12280-12292 |
| 32-39 | deviceSN | ASCII | - | - | Device serial number (8 bytes) | 12295-12307 |
| 41 | invNumber | UINT8 | 1.0 | - | Number of inverters | 12312-12326 |
| 42-43 | invOnline | UINT16 | - | bits | Inverter online status bitmap | 12331-12361 |
| 45 | invPowerType | UINT8 | 1.0 | - | Inverter power type (1=low, 3=high, etc) | 12423-12437 |
| 46-47 | energyLines | UINT16 | - | bits | Energy flow lines bitmap | 12442-12506 |
| 48-49 | ctrlStatus | UINT16 | - | bits | System control status bitmap | 12510-12540 |
| 51 | gridParallelSoC | UINT8 | 1.0 | % | Grid parallel mode SoC threshold | 12545-12559 |
| 52-59 | alarmInfo | UINT64 | - | bits | Alarm/warning information (8 bytes) | 12625-12713 |
| 66-77 | faultInfo | UINT64 | - | bits | Fault information (12 bytes, v2001+) | 12725-12790 |
| 80-83 | totalDCPower | UINT32 | 1.0 | W | Total DC power | 12797-12815 |
| 84-87 | totalACPower | UINT32 | 1.0 | W | Total AC power | 12820-12838 |
| 88-91 | totalPVPower | UINT32 | 1.0 | W | Total PV (solar) power | 12845-12863 |
| 92-95 | totalGridPower | INT32 | 1.0 | W | Total grid power (signed) | 12870-12878 |
| 96-99 | totalInvPower | UINT32 | 1.0 | W | Total inverter power | 12885-12903 |
| 100-103 | totalDCEnergy | UINT32 | 0.1 | kWh | Total DC energy | 12910-12934 |
| 104-107 | totalACEnergy | UINT32 | 0.1 | kWh | Total AC energy | 12941-12965 |
| 108-111 | totalPVChargingEnergy | UINT32 | 0.1 | kWh | Total PV charging energy | 12972-12996 |
| 112-115 | totalGridChargingEnergy | UINT32 | 0.1 | kWh | Total grid charging energy | 13003-13028 |
| 116-119 | totalFeedbackEnergy | UINT32 | 0.1 | kWh | Total grid feedback energy | 13035-13059 |
| 121 | chargingMode | UINT8 | 1.0 | - | Charging mode setting | 13064-13078 |
| 123 | invWorkingStatus | UINT8 | 1.0 | - | Inverter working status | 13083-13097 |
| 124-127 | pvToAcEnergy | UINT32 | 0.1 | kWh | PV to AC energy (v2001+) | 13113-13137 |
| 129 | selfSufficiencyRate | UINT8 | 1.0 | % | Self-sufficiency rate (v2001+) | 13142-13156 |
| 130-133 | pvToAcPower | UINT32 | 1.0 | W | PV to AC power (v2001+) | 13173-13191 |
| 134-137 | packDsgEnergyTotal | UINT32 | 0.1 | kWh | Pack total discharge energy (v2001+) | 13196-13220 |
| 138-139 | rateVoltage | UINT16 | 1.0 | V | Rated voltage (v2001+) | 13223-13257 |
| 140-141 | rateFrequency | UINT16 | 1.0 | Hz | Rated frequency (v2001+) | 13262-13296 |
| 142-143 | componentOnline | UINT16 | - | bits | Component online status (v2001+) | 13311-13434 |
| 148-149 | iotKeyStatus | UINT16 | - | bits | IoT key status bitmap (v2001+) | 13449-13598 |
| 151 | sceneFlag | UINT8 | 1.0 | - | Scene flag (v2001+) | 13613-13627 |
| 156-159 | sleepStandbyTime | UINT32 | 1.0 | s | Sleep/standby time (v2001+) | 13644-13662 |
| 160-163 | packChgEnergyTotal | UINT32 | 1.0 | Wh | Pack total charging energy (v2001+) | 13669-13687 |
| 164-165 | totalCarPower | UINT16 | 1.0 | W | Total car charging power (v2001+) | 13692-13726 |
| 166-169 | totalEVPower | UINT32 | 1.0 | W | Total EV charging power (v2001+) | 13733-13751 |
| 176-177 | featureStatus | UINT16 | - | bits | Feature status bitmap (v2001+) | 13766-13835 |
| 182-183 | switchRecoveryStatus | UINT16 | - | bits | Switch recovery status (v2001+) | 13850-13907 |

## Pack Aging Info Bitfield (Offset 12-13)

The pack aging info at offset 12-13 is converted to binary and parsed as follows:

| Bits | Field | Description |
|------|-------|-------------|
| 12-15 | packAgingStatus | Aging status code |
| 8-11 | packAgingProgress | Aging progress percentage |
| 4-7 | packAgingFault | Aging fault code |
| 0-3 | Reserved | - |

## Component Online Status Bitfield (Offset 142-143)

When size > 0x8E (142), component online status is parsed as 7 bits:

| Bit | Component |
|-----|-----------|
| 0 | Component 0 online |
| 1 | Component 1 online |
| 2 | Component 2 online |
| 3 | Component 3 online |
| 4 | Component 4 online |
| 5 | Component 5 online |
| 6 | Component 6 online |

## IoT Key Status Bitfield (Offset 148-149)

When size > 0x94 (148), IoT key status is parsed as 9 bits:

| Bit | Key Status |
|-----|------------|
| 0 | IoT Key 0 |
| 1 | IoT Key 1 |
| 2 | IoT Key 2 |
| 3 | IoT Key 3 |
| 4 | IoT Key 4 |
| 5 | IoT Key 5 |
| 6 | IoT Key 6 |
| 7 | IoT Key 7 |
| 8 | IoT Key 8 |

## Feature Status Bitfield (Offset 176-177)

When size > 0xB0 (176), feature status is parsed:

| Bit | Feature |
|-----|---------|
| 0 | Feature bit 0 |
| 1 | Feature bit 1 |
| 2 | Feature bit 2 |
| 3 | Feature bit 3 |
| 8 | Feature bit 8 |

## Switch Recovery Status Bitfield (Offset 182-183)

When size > 0xB6 (182), switch recovery status is parsed:

| Bit | Status |
|-----|--------|
| 0 | Switch recovery bit 0 |
| 1 | Switch recovery bit 1 |
| 2 | Switch recovery bit 2 |

## Protocol Version Notes

- **Base fields (v2000)**: Offsets 0-51 available in all versions
- **Extended fields (v2001+)**: Offsets 80+ require protocol version ≥ 2001
- **CAN bus fault (v2009+)**: Offset 18-19 requires protocol version ≥ 2009 (0x7D9)

## Energy Flow Lines (Offset 46-47)

The energy lines bitmap indicates which energy flows are active in the system. This is rendered as a visual diagram in the app using the `getEnergyLine()` method.

## Alarm and Fault Codes

- **Alarm Info** (offset 52-59): 8-byte bitmap mapped to warning names via `ConnConstantsV2` constants
- **Fault Info** (offset 66-77): 12-byte bitmap mapped to fault names via `ConnConstantsV2` constants
- Different mappings exist for:
  - Low power inverters (E series)
  - High power inverters (B series)
  - Micro inverters (C series)

## Data Types

- **UINT8**: 1 byte unsigned integer
- **UINT16**: 2 bytes unsigned integer (hex string parsed, e.g., "00FF" → 255)
- **UINT32**: 4 bytes unsigned integer
- **INT32**: 4 bytes signed integer (used for grid power which can be negative)
- **ASCII**: ASCII string (null-terminated or space-padded)
- **bits**: Bitmap field (individual bits have meaning)

## Method Signature

```java
public final DeviceHomeData parseHomeData(List<String> dataRes, int protocolVersion)
```

- **Input**: List of hex string bytes (e.g., ["00", "0A", "FF", ...])
- **Output**: DeviceHomeData object with all parsed fields
- **Protocol version**: Determines which fields are available

## Total Block Size

- **Minimum**: ~52 bytes (base fields)
- **Extended**: ~184 bytes (all fields with v2001+)
- **Typical**: 184 bytes for Elite V2 devices

## Usage Pattern

This block is typically read at a high frequency (every few seconds) as it contains all real-time dashboard data. It's the most important block for monitoring system status.

## Key Fields for Monitoring

- **Battery**: packTotalVoltage, packTotalCurrent, packTotalSoc
- **Power flows**: totalPVPower, totalGridPower, totalACPower, totalDCPower
- **Energy totals**: totalPVChargingEnergy, totalGridChargingEnergy, totalFeedbackEnergy
- **Status**: packChargingStatus, invWorkingStatus, chargingMode
- **Component health**: alarmInfo, faultInfo, packOnline, invOnline
