# V2 Protocol Additional Blocks

This document covers V2 protocol blocks that were not documented by other agents.
Blocks already covered: 100, 1100-1500, 6000-6100.

## Summary Table

Total V2 Blocks Found: **78 blocks**
Already Documented: **8 blocks** (100, 1100, 1200, 1300, 1400, 1500, 6000, 6100)
Additional Blocks: **70 blocks**

| Block Hex | Block Dec | Priority | Method/Handler | Purpose |
|-----------|-----------|----------|----------------|---------|
| 0x0001 | 1 | LOW | parseBaseConfig | Base device configuration (V1 handler) |
| 0x02D0 | 720 | MEDIUM | parseOTAStatus | OTA/Firmware update status |
| 0x06A4 | 1700 | MEDIUM | parseInvMeterInfo | Meter information |
| 0x076C | 1900 | HIGH | parseInvMeterSettings | **Meter settings** |
| 0x07D0 | 2000 | HIGH | parseInvBaseSettings | **Inverter base settings** |
| 0x0898 | 2200 | HIGH | parseInvAdvSettings | **Inverter advanced settings** |
| 0x08E8 | 2280 | MEDIUM | heatPumpEnableParse | Heat pump enable/disable |
| 0x0960 | 2400 | HIGH | parseCertSettings | **Grid certification settings** |
| 0x09C4 | 2500 | HIGH | parseMicroInvAdvSettings | **Micro-inverter advanced settings** |
| 0x0BB8 | 3000 | LOW | UNKNOWN | Fault history page |
| 0x0DAC | 3500 | MEDIUM | parseTotalEnergyInfo | Total energy statistics |
| 0x0E10 | 3600 | MEDIUM | parseCurrYearEnergy | Current year energy |
| 0x1068 | 4200 | MEDIUM | wtInfoParse | WT (Wind Turbine?) information |
| 0x1130 | 4400 | HIGH | wtSettingsParse | **WT settings** |
| 0x1388 | 5000 | MEDIUM | parseTimeCtrlInfo | Time control information |
| 0x189C | 6300 | MEDIUM | parsePackSubPackInfo | Pack sub-pack info (range 6300-7000) |
| 0x1B58 | 7000 | HIGH | parsePackSettingsInfo | **Battery pack settings** |
| 0x1C20 | 7200 | LOW | EVENT | Pack BMU info event |
| 0x2AF8 | 11000 | HIGH | parseIOTInfo | **IOT base information** |
| 0x2B62 | 11106 | MEDIUM | parseWifiInfo | WiFi information |
| 0x2B77 | 11127 | LOW | EVENT | IOT server BLE SN |
| 0x2EE2 | 12002 | HIGH | parseIOTSettingsInfo | **IOT WiFi settings** |
| 0x2F81 | 12161 | HIGH | parseIOTEnableInfo | **IOT enable/control status** |
| 0x2F83 | 12163 | MEDIUM | parseDisasterWarningInfo | Disaster warning data |
| 0x2F8E | 12174 | LOW | EVENT | IOT subnet gateway |
| 0x2FAD | 12205 | HIGH | parseIoTDisplaySettings | **IOT display settings** |
| 0x3320 | 13088 | HIGH | parseIoTMatterInfo | **IOT Matter protocol info** |
| 0x34BC | 13500 | HIGH | parseIOTWiFiMesh | **IOT WiFi mesh info** |
| 0x3523 | 13603 | LOW | EVENT | IOT server key |
| 0x352B | 13611 | MEDIUM | parseMultWifi1 | Multi-WiFi info 1 |
| 0x3538 | 13624 | MEDIUM | parseMultWifi2 | Multi-WiFi info 2 |
| 0x35D0 | 13776 | LOW | EVENT | Client pair BLE SN |
| 0x36B0 | 14000 | MEDIUM | parseHmiInfo | HMI (display) information |
| 0x38A4 | 14500 | MEDIUM | EVENT | Smart plug info |
| 0x396C | 14700 | HIGH | EVENT | **Smart plug settings** |
| 0x3A98 | 15000 | MEDIUM | EVENT | Charging pile info |
| 0x3C8C | 15500 | MEDIUM | EVENT | DC-DC converter info |
| 0x3CF0 | 15600 | HIGH | UNKNOWN | **DC-DC settings** |
| 0x3D54 | 15700 | MEDIUM | dcHubInfoParse | DC Hub information |
| 0x3D86 | 15750 | HIGH | dcHubSettingsParse | **DC Hub settings** |
| 0x3E80 | 16000 | MEDIUM | EVENT | Device panel info |
| 0x3EE4 | 16100 | MEDIUM | EVENT | Panel DC info |
| 0x3F48 | 16200 | MEDIUM | EVENT | Panel AC info |
| 0x4010 | 16400 | HIGH | EVENT | **Panel base settings** |
| 0x4268 | 17000 | MEDIUM | atsInfoParse | ATS (transfer switch) info |
| 0x42CC | 17100 | MEDIUM | EVENT | AT1 info |
| 0x43F8 | 17400 | HIGH | EVENT | **AT1 settings part 1** |
| 0x4650 | 18000 | MEDIUM | EVENT | EPAD base info |
| 0x477C | 18300 | HIGH | EVENT | **EPAD base settings** |
| 0x47E0 | 18400 | LOW | UNKNOWN | Unknown |
| 0x4844 | 18500 | LOW | UNKNOWN | Unknown |
| 0x48A8 | 18600 | LOW | UNKNOWN | Unknown |
| 0x4A38 | 19000 | HIGH | commSOCSettingsParse | **SOC threshold settings** |
| 0x4A9C | 19100 | HIGH | commDelaySettingsParse | **Grid charge delay settings** |
| 0x4B00 | 19200 | MEDIUM | parseScheduledBackup | Scheduled backup settings |
| 0x4B64 | 19300 | HIGH | commTimerSettingsParse | **Timer settings** |
| 0x4B69 | 19305 | HIGH | commTimerTaskListParse | **Timer task list** |
| 0x4BA5 | 19365 | HIGH | EVENT | **AT1 timer slots 1-2** |
| 0x4BE1 | 19425 | HIGH | EVENT | **AT1 timer slots 3-4** |
| 0x4C1D | 19485 | HIGH | EVENT | **AT1 timer slots (additional)** |
| 0x5208 | 21000 | LOW | UNKNOWN | Unknown |
| 0x6591 | 26001 | MEDIUM | EVENT | TOU time info |
| 0x744A | 29770 | LOW | bootUpgradeSupportParse | Boot upgrade support |
| 0x744C | 29772 | LOW | bootSoftwareInfoParse | Boot software info |
| 0x7531 | 30001 | LOW | parseActiveInfo | Device activation info |
| 0x78B5 | 30901 | LOW | testSettingsParse | Test/diagnostic settings |
| 0x9C6C | 40044 | HIGH | parseCertSettingsExt | **Certification settings extended** |
| 0x9CBF | 40127 | HIGH | parseHomeStorageSettings | **Home storage mode settings** |
| 0x9CF5 | 40181 | MEDIUM | parseAntiBackflowCert | Anti-backflow certification |
| 0x9CFB | 40187 | HIGH | parseCertSettingsPart2 | **Certification settings part 2** |

---

## High Priority Blocks - Detailed Mappings

### Block 0x07D0 (2000) - Inverter Base Settings

**Purpose:** Core inverter control settings including working mode, charging, and eco mode.

**Method:** `parseInvBaseSettings`
**Bean:** `InvBaseSettings`

| Offset | Field Name | Description |
|--------|------------|-------------|
| 0 | InvAddress | Inverter modbus address |
| 1 | WorkingMode | Operating mode selector |
| 5 | CtrlLed | LED control enable |
| 7 | CtrlGridChg | Grid charging enable |
| 9 | CtrlPV | PV input enable |
| 11 | CtrlInverter | Inverter enable |
| 13 | CtrlAC | AC output enable |
| 15 | CtrlDC | DC output enable |
| 19 | DcECOCtrl | DC ECO mode enable |
| 21 | DcECOOffTime | DC ECO off delay (minutes) |
| 23 | DcECOPower | DC ECO power threshold (W) |
| 25 | AcECOCtrl | AC ECO mode enable |
| 27 | AcECOOffTime | AC ECO off delay (minutes) |
| 29 | AcECOPower | AC ECO power threshold (W) |
| 31 | ChargingMode | Charging mode selector |
| 33 | PowerLiftingMode | Power lifting mode |

**Notes:** This is a critical block for controlling basic inverter functions. All offsets are byte positions in the modbus response.

---

### Block 0x0898 (2200) - Inverter Advanced Settings

**Purpose:** Advanced inverter configuration including grid parameters and limits.

**Method:** `parseInvAdvSettings`
**Bean:** `InvAdvancedSettings`

| Offset | Field Name | Description |
|--------|------------|-------------|
| 0-7 | AdvLoginPassword | Advanced settings password (8 bytes) |
| 8 | FactoryReset | Factory reset flag |
| 9 | CtrlGrid | Grid connection control |
| 11 | CtrlFeedback | Grid feedback enable |
| 13 | InvVoltage | Inverter output voltage (V) |
| 15 | InvFreq | Inverter output frequency (Hz) |
| 17 | ChgMaxVoltage | Max charging voltage (V) |
| 19 | PvChgMaxCurrent | PV max charging current (A) |
| 21 | GridMaxPower | Grid max power (W) |
| 23 | GridMaxCurrent | Grid max current (A) |
| 25 | FeedbackMaxPower | Max feedback power (W) |

**Security:** Contains password protection for advanced settings.

---

### Block 0x0960 (2400) - Certification Settings

**Purpose:** Grid compliance and certification parameters.

**Method:** `parseCertSettings`
**Bean:** `DeviceCertSettings`

| Offset | Field Name | Description |
|--------|------------|-------------|
| 0 | AdvEnable | Advanced cert enable |
| 1 | GridUV2Value | Grid undervoltage 2 threshold |
| 3 | GridUV2Time | Grid undervoltage 2 time |
| 5 | PowerFactor | Power factor setting |
| 7 | GridCertDivision | Grid cert division/region |
| 9 | VvarAndVoltWattRespMode | Reactive power response mode |

**Notes:** Used for different grid standards (Europe, North America, etc.).

---

### Block 0x1B58 (7000) - Pack Settings

**Purpose:** Battery pack configuration.

**Method:** `parsePackSettingsInfo`
**Bean:** `PackSettingsInfo`

| Offset | Field Name | Description |
|--------|------------|-------------|
| 0 | PackId | Battery pack ID |
| 1 | PackParallelNumber | Number of packs in parallel |
| 3 | StartHeatingEnable | Battery heating enable |
| 11 | BmsCommInterfaceType | BMS communication type |

---

### Block 0x2AF8 (11000) - IOT Base Information

**Purpose:** IOT module identification and version information.

**Method:** `parseIOTInfo`
**Bean:** `DeviceIotInfo`

| Offset | Field Name | Description |
|--------|------------|-------------|
| 0-11 | IotModel | IOT model string (ASCII, 12 bytes) |
| 12-19 | IotSn | IOT serial number (8 bytes) |
| 20-27 | SafetyCode | Safety code (8 bytes as number) |
| 28-31 | IotSoftwareVer | IOT firmware version (32-bit) |
| 32-35 | RfVer | RF module version (32-bit) |
| 36-37 | CtrlStatus | IOT control status (bit field) |

**Format Notes:**
- Model is ASCII string, may need null trimming
- SafetyCode is 4-register (8-byte) number converted to string
- Versions are 32-bit integers

---

### Block 0x2EE2 (12002) - IOT Settings

**Purpose:** WiFi configuration for IOT module.

**Method:** `parseIOTSettingsInfo`
**Bean:** `IOTSettingsInfo`

| Offset | Field Name | Type | Description |
|--------|------------|------|-------------|
| 0-63 or 0-95 | WifiSSID | String | WiFi SSID (64 or 96 bytes based on password type) |
| 64-95 or 96+ | WifiPassword | String | WiFi password |
| 96 | WifiNoPasswordEnable | Bool | Open WiFi (no password) enable |
| 97 | WifiPasswordH32BEnable | Bool | Use 32-byte hex password encoding |

**Format Notes:**
- SSID/Password length depends on `WifiPasswordH32BEnable` flag
- If H32B enabled, uses 96-byte encoding
- If not enabled, uses 64-byte encoding
- Password stored as hex-encoded bytes

**WARNING:** Contains WiFi credentials - handle securely!

---

### Block 0x4A38 (19000) - SOC Threshold Settings

**Purpose:** Battery state-of-charge thresholds for grid charge and UPS modes.

**Method:** `commSOCSettingsParse`
**Bean:** `List<DeviceSOCThresholdItem>`

**Format:** Each 2 bytes (1 register) encodes 2 SOC threshold items (on/off pair).

**Byte Layout per Register:**
```
Byte 1: [bit7: off_enable][bits6-0: off_soc]
Byte 2: [bit7: on_enable][bits6-0: on_soc]
```

**Calculation:**
```
word = (high_byte << 8) | low_byte
off_soc = word & 0x7F
off_enable = (word >> 7) & 0x01
on_soc = (word >> 8) & 0x7F
on_enable = (word >> 15) & 0x01
```

**Register Addresses:**
- Each threshold pair has a base address starting at 0x4A38
- Index 0: offset 0 (address 0x4A38)
- Index 1: offset 2 (address 0x4A3A)
- Index 2: offset 4 (address 0x4A3C)
- etc.

**Typical Threshold Types:**
1. Grid charge start/stop
2. UPS mode start/stop
3. Battery protect start/stop
(Multiple sets for different modes)

---

### Block 0x4A9C (19100) - Delay Settings

**Purpose:** Grid charge time delays.

**Method:** `commDelaySettingsParse`
**Bean:** `List<DeviceDelayItem>`

**Notes:** Parses charging delay configuration. Details TBD - uses different parsing logic than simple offsets.

---

### Block 0x4B64 (19300) - Timer Settings

**Purpose:** Scheduled charge/discharge timers.

**Method:** `commTimerSettingsParse`
**Bean:** `DeviceCommTimerSettings`

**Related Blocks:**
- 0x4B69 (19305): Timer task list
- 0x4BA5 (19365): AT1 timer slots 1-2
- 0x4BE1 (19425): AT1 timer slots 3-4

**Notes:** Timer settings are complex with multiple related blocks. Each timer has:
- Enable flag
- Start time (hour, minute)
- End time (hour, minute)
- Days of week
- Power settings
- Mode (charge/discharge)

Full extraction requires analyzing `commTimerTaskListParse` method.

---

### Block 0x9CBF (40127) - Home Storage Settings

**Purpose:** Home storage mode configuration for residential energy storage.

**Method:** `parseHomeStorageSettings`
**Bean:** `HomeStorageSettingsBean`

**Notes:** This is for grid-tied home battery systems. Controls:
- Self-consumption mode
- Time-of-use optimization
- Backup reserve levels
- Grid sell-back settings

Full offset mapping TBD.

---

## Medium Priority Blocks

### Block 0x02D0 (720) - OTA Status

**Purpose:** Firmware update status.
**Method:** `parseOTAStatus`
**Use Case:** Monitor firmware update progress.

### Block 0x06A4 (1700) - Inverter Meter Info

**Purpose:** CT meter readings.
**Method:** `parseInvMeterInfo`
**Use Case:** Monitor grid import/export via CT clamps.

### Block 0x076C (1900) - Inverter Meter Settings

**Purpose:** CT meter configuration.
**Method:** `parseInvMeterSettings`
**Use Case:** Configure CT clamp settings.

### Block 0x0DAC (3500) - Total Energy Statistics

**Purpose:** Lifetime energy totals.
**Method:** `parseTotalEnergyInfo`
**Use Case:** Historical energy tracking.

### Block 0x0E10 (3600) - Current Year Energy

**Purpose:** Year-to-date energy statistics.
**Method:** `parseCurrYearEnergy`
**Use Case:** Annual energy reports.

### Block 0x1388 (5000) - Time Control Info

**Purpose:** Time-based control settings.
**Method:** `parseTimeCtrlInfo`
**Use Case:** Schedule management.

### Block 0x2B62 (11106) - WiFi Info

**Purpose:** Current WiFi connection status.
**Method:** `parseWifiInfo`
**Use Case:** Monitor WiFi signal, IP address.

### Block 0x2F81 (12161) - IOT Enable Info

**Purpose:** IOT module enable/control status.
**Method:** `parseIOTEnableInfo`
**Bean:** `IoTCtrlStatus`
**Use Case:** Check IOT module operational status.

### Block 0x2F83 (12163) - Disaster Warning Info

**Purpose:** Disaster/emergency warning data.
**Method:** `parseDisasterWarningInfo`
**Use Case:** Emergency alerts integration.

### Block 0x36B0 (14000) - HMI Info

**Purpose:** Display/HMI status.
**Method:** `parseHmiInfo`
**Use Case:** Monitor display settings.

### Block 0x3D54 (15700) - DC Hub Info

**Purpose:** DC expansion hub information.
**Method:** `dcHubInfoParse`
**Use Case:** Monitor DC hub status.

### Block 0x3D86 (15750) - DC Hub Settings

**Purpose:** DC hub configuration.
**Method:** `dcHubSettingsParse`
**Contains:** DC voltage setpoint.

### Block 0x4268 (17000) - ATS Info

**Purpose:** Automatic transfer switch information.
**Method:** `atsInfoParse`
**Use Case:** Monitor ATS status for backup systems.

### Block 0x4B00 (19200) - Scheduled Backup

**Purpose:** Scheduled backup power settings.
**Method:** `parseScheduledBackup`
**Use Case:** Configure backup power schedules.

---

## Low Priority / Diagnostic Blocks

- **0x0001 (1)**: Base config - uses V1 parser
- **0x0BB8 (3000)**: Fault history - diagnostic only
- **0x1C20 (7200)**: Pack BMU raw data
- **0x2B77 (11127)**: IOT server BLE SN - internal use
- **0x2F8E (12174)**: IOT subnet gateway - network config
- **0x3523 (13603)**: IOT server key - authentication
- **0x35D0 (13776)**: Client pair BLE SN - pairing process
- **0x47E0-0x48A8**: Unknown blocks - need investigation
- **0x5208 (21000)**: Unknown - need investigation
- **0x744A (29770)**: Boot upgrade support - firmware related
- **0x744C (29772)**: Boot software info - firmware related
- **0x7531 (30001)**: Activation info - factory/setup
- **0x78B5 (30901)**: Test settings - factory diagnostic

---

## Blocks Requiring Further Analysis

The following blocks have event handlers but no documented parse methods:

1. **Smart Plug Blocks (14500, 14700)**
   - 0x38A4: Smart plug info
   - 0x396C: Smart plug settings
   - Use case: Control smart plugs connected to Bluetti systems

2. **Charging Pile Blocks (15000)**
   - 0x3A98: Charging pile info
   - Use case: EV charger integration

3. **DC-DC Converter Blocks (15500-15600)**
   - 0x3C8C: DC-DC info
   - 0x3CF0: DC-DC settings
   - Use case: DC voltage conversion settings

4. **Panel Blocks (16000-16400)**
   - 0x3E80: Device panel info
   - 0x3EE4: Panel DC info
   - 0x3F48: Panel AC info
   - 0x4010: Panel base settings
   - Use case: Solar panel monitoring/configuration

5. **AT1 Blocks (17100-17400)**
   - 0x42CC: AT1 info
   - 0x43F8: AT1 settings part 1
   - Use case: AT1 transfer switch settings

6. **EPAD Blocks (18000-18300)**
   - 0x4650: EPAD base info
   - 0x477C: EPAD base settings
   - Use case: EPAD device (expansion accessory?)

7. **TOU Block (26001)**
   - 0x6591: Time-of-use tariff info
   - Use case: Electricity rate schedules

---

## Implementation Priority

### Immediate (Essential for Home Assistant):
1. ✅ Block 0x07D0 (2000) - Inverter base settings
2. ✅ Block 0x2AF8 (11000) - IOT info
3. ✅ Block 0x2EE2 (12002) - IOT WiFi settings
4. ✅ Block 0x4A38 (19000) - SOC thresholds
5. Block 0x4B64 (19300) - Timer settings (complex)

### High Priority (Power users):
1. Block 0x0898 (2200) - Advanced inverter settings
2. Block 0x0960 (2400) - Certification settings
3. Block 0x1B58 (7000) - Pack settings
4. Block 0x9CBF (40127) - Home storage settings
5. Block 0x4A9C (19100) - Delay settings

### Medium Priority (Nice to have):
1. Block 0x06A4 (1700) - Meter info
2. Block 0x076C (1900) - Meter settings
3. Block 0x0DAC (3500) - Energy statistics
4. Block 0x2F81 (12161) - IOT enable status

### Low Priority (Future):
- Diagnostic blocks (OTA, boot, test)
- Unknown blocks requiring device testing
- Specialized accessories (smart plug, EV charger, etc.)

---

## Notes for Implementation

1. **Security Considerations:**
   - Block 0x2EE2 contains WiFi credentials - encrypt in transit
   - Block 0x0898 contains advanced settings password
   - Be careful with factory reset flags

2. **Complex Parsing:**
   - SOC settings (0x4A38) use bit-packed format
   - Timer blocks (0x4B64+) use multi-block structure
   - Some blocks return arrays/lists, not single objects

3. **Device Compatibility:**
   - Not all blocks exist on all models
   - Check device capabilities before querying
   - Some blocks may require specific firmware versions

4. **Testing Requirements:**
   - Settings blocks should be tested on non-production systems
   - Write operations require careful validation
   - Some settings may require device restart to take effect

---

## Next Steps

1. Extract detailed mappings for timer blocks (0x4B64, 0x4B69, 0x4BA5, 0x4BE1)
2. Reverse engineer home storage settings block (0x9CBF)
3. Document smart plug and panel blocks if devices available
4. Create write/control methods for high-priority settings blocks
5. Add Home Assistant entities for new blocks

---

## References

- Source file: `ConnectManager.smali` (lines 8168-8249, 5916-8100)
- Parser file: `ProtocolParserV2.smali`
- Bean definitions: `bluetti_smali/smali_classes5/net/poweroak/bluetticloud/ui/connectv2/bean/`
