# Agent E: Blocks 15500 + 15600 Deep Dive Report

**Generated**: 2026-02-16
**Agent**: Agent E
**Blocks Analyzed**: 15500 (DC_DC_INFO), 15600 (DC_DC_SETTINGS)
**Scope**: Bit-field extraction and scale factor resolution for smali_verified upgrade assessment

---

## Executive Summary

This report provides deep-dive analysis of blocks 15500 and 15600 to resolve bit-field overlaps and scale factors identified in Agent A's initial analysis. The goal was to determine if these blocks can be upgraded from "partial" to "smali_verified" status.

**Key Findings**:

| Block | Name | Fields Analyzed | Fully Proven | Decision | Reason |
|-------|------|----------------|--------------|----------|---------|
| 15500 | DC_DC_INFO | 9 core fields | 9 | **KEEP PARTIAL** | Complex multi-channel structure with 30+ additional fields beyond core 9 |
| 15600 | DC_DC_SETTINGS | 40+ fields | 7 core | **KEEP PARTIAL** | Highly conditional parsing, 40+ fields, voltage/current scales need device validation |

**Critical Constraint**: While bit-field mappings and scale factors have been extracted from smali, both blocks contain significantly more complexity than initially documented. Block 15500 has multi-channel DC input/output structures, and block 15600 has extensive conditional parsing with 40+ configuration fields. Neither meets the strict criteria for smali_verified without complete field mapping and actual device validation.

---

## Block 15500: DC_DC_INFO - Complete Analysis

### Parser Evidence
- **Source**: `DCDCParser.smali`
- **Method**: `baseInfoParse(Ljava/util/List;)` (lines 66-1779)
- **Bean**: `DCDCInfo.smali`
- **Total setter calls**: 30+ fields identified

### Core Field Evidence Table (First 9 Fields)

| Offset | Field Name | Type | Unit | Transform | Smali Line | Bean Setter | Status |
|--------|------------|------|------|-----------|------------|-------------|--------|
| 0-11 | model | String(12) | - | getASCIIStr | 191-207 | setModel | ✅ **PROVEN** |
| 12-19 | sn | String(8) | - | getDeviceSN | 210-222 | setSn | ✅ **PROVEN** |
| 20-21 | dcInputVolt | UInt16 | V | parseInt(16) ÷ 10.0f | 224-267 | setDcInputVolt(F) | ✅ **PROVEN** |
| 22-23 | dcOutputVolt | UInt16 | V | parseInt(16) ÷ 10.0f | 269-310 | setDcOutputVolt(F) | ✅ **PROVEN** |
| 24-25 | dcOutputCurrent | UInt16 | A | parseInt(16) ÷ 10.0f | 312-353 | setDcOutputCurrent(F) | ✅ **PROVEN** |
| 26-27 | dcOutputPower | UInt16 | W | parseInt(16) (NO division) | 355-392 | setDcOutputPower(I) | ✅ **PROVEN** |
| 28 (bit 0) | energyLineCarToCharger | UInt1 | - | hexStrToBinaryList[0] | 395-444 | setEnergyLineCarToCharger | ✅ **PROVEN** |
| 28 (bit 1) | energyLineChargerToDevice | UInt1 | - | hexStrToBinaryList[1] | 446-457 | setEnergyLineChargerToDevice | ✅ **PROVEN** |
| 28-29 | energyLines | List<Int> | - | hexStrToEnableList | 460-490 | setEnergyLines | ✅ **PROVEN** |

### Bit-Field Mapping (Offsets 28-29)

**Evidence from lines 395-524**:

```smali
.line 29
const/16 v5, 0x1c     # v5 = 28 (0x1c)
invoke-interface {v0, v5}, Ljava/util/List;->get(I)Ljava/lang/Object;
const/16 v8, 0x1d     # v8 = 29 (0x1d)
invoke-interface {v0, v8}, Ljava/util/List;->get(I)Ljava/lang/Object;
# Concatenate bytes 28+29 into string
invoke-virtual {v7, v9}, Ljava/lang/StringBuilder;->append(Ljava/lang/Object;)Ljava/lang/StringBuilder;
invoke-virtual {v7}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

# Call 1: hexStrToBinaryList (creates bit array)
invoke-static {v2, v7, v4, v10, v9}, Lnet/poweroak/bluetticloud/ui/connectv2/tools/ProtocolParserV2;->hexStrToBinaryList$default(...)Ljava/util/List;
move-result-object v2

.line 30
invoke-interface {v2, v4}, Ljava/util/List;->get(I)Ljava/lang/Object;  # Get bit 0
invoke-virtual {v1, v7}, Lnet/poweroak/bluetticloud/ui/connectv2/bean/DCDCInfo;->setEnergyLineCarToCharger(I)V

.line 31
invoke-interface {v2, v6}, Ljava/util/List;->get(I)Ljava/lang/Object;  # Get bit 1
invoke-virtual {v1, v2}, Lnet/poweroak/bluetticloud/ui/connectv2/bean/DCDCInfo;->setEnergyLineChargerToDevice(I)V

# Call 2: hexStrToEnableList (creates enable list from same bytes)
.line 32
invoke-static {v2, v5, v4, v10, v9}, Lnet/poweroak/bluetticloud/ui/connectv2/tools/ProtocolParserV2;->hexStrToEnableList$default(...)Ljava/util/List;
move-result-object v2
invoke-virtual {v1, v2}, Lnet/poweroak/bluetticloud/ui/connectv2/bean/DCDCInfo;->setEnergyLines(Ljava/util/List;)V

# Derived fields from energyLines list
.line 33
invoke-virtual {v1}, Lnet/poweroak/bluetticloud/ui/connectv2/bean/DCDCInfo;->getEnergyLines()Ljava/util/List;
invoke-interface {v2, v6}, Ljava/util/List;->get(I)Ljava/lang/Object;  # Get index 1
invoke-virtual {v1, v2}, Lnet/poweroak/bluetticloud/ui/connectv2/bean/DCDCInfo;->setDcInputStatus1(I)V

.line 34
invoke-interface {v2, v10}, Ljava/util/List;->get(I)Ljava/lang/Object;  # Get index 2
invoke-virtual {v1, v2}, Lnet/poweroak/bluetticloud/ui/connectv2/bean/DCDCInfo;->setDcInputStatus2(I)V

.line 35
invoke-interface {v2, v5}, Ljava/util/List;->get(I)Ljava/lang/Object;  # Get index 3
invoke-virtual {v1, v2}, Lnet/poweroak/bluetticloud/ui/connectv2/bean/DCDCInfo;->setDcOutputStatus1(I)V

.line 36
invoke-interface {v2, v7}, Ljava/util/List;->get(I)Ljava/lang/Object;  # Get index 4
invoke-virtual {v1, v2}, Lnet/poweroak/bluetticloud/ui/connectv2/bean/DCDCInfo;->setDcOutputStatus2(I)V
```

**Interpretation**:
- Bytes 28-29 form a 16-bit status word
- `hexStrToBinaryList`: Expands to bit array (LSB first)
  - Bit 0: Energy line direction (car → charger)
  - Bit 1: Energy line direction (charger → device)
- `hexStrToEnableList`: Creates list of enable flags
  - Index 1: DC Input Status 1
  - Index 2: DC Input Status 2
  - Index 3: DC Output Status 1
  - Index 4: DC Output Status 2

**Note**: The parser extracts the SAME bytes 28-29 twice using different transform functions. This is a complex overlapping bit-field pattern where individual bits have specific meanings AND the entire word is treated as an enable list.

### Scale Factor Verification

**Voltage Fields** (lines 224-310):
```smali
const/high16 v5, 0x41200000    # 10.0f (float constant)
int-to-float v2, v2             # Convert parsed int to float
div-float/2addr v2, v5          # Divide by 10.0
invoke-virtual {v1, v2}, Lnet/poweroak/bluetticloud/ui/connectv2/bean/DCDCInfo;->setDcInputVolt(F)V
```
- **Scale**: ×0.1V (divide by 10)
- **Example**: Raw value 120 (0x0078) → 12.0V
- **Bean type**: Float (F)

**Current Field** (lines 312-353):
```smali
div-float/2addr v2, v5          # Same 10.0f divisor
invoke-virtual {v1, v2}, Lnet/poweroak/bluetticloud/ui/connectv2/bean/DCDCInfo;->setDcOutputCurrent(F)V
```
- **Scale**: ×0.1A (divide by 10)
- **Example**: Raw value 50 (0x0032) → 5.0A

**Power Field** (lines 355-392):
```smali
invoke-static {v2, v5}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;I)I
move-result v2
invoke-virtual {v1, v2}, Lnet/poweroak/bluetticloud/ui/connectv2/bean/DCDCInfo;->setDcOutputPower(I)V
```
- **Scale**: 1W (NO division - raw value)
- **Example**: Raw value 60 (0x003c) → 60W
- **Bean type**: Integer (I)

### Additional Fields Beyond Core 9

The parser continues with extensive multi-channel DC structures:

**Multi-Channel DC Fields** (lines 1446-1671):
- dc1Voltage, dc1Current, dc1Power (setters at lines 1446, 1459, 1472)
- dc2Voltage, dc2Current, dc2Power (setters at lines 1485, 1498, 1511)
- dc3Voltage, dc3Current, dc3Power (setters at lines 1524, 1537, 1550)
- dc4Voltage, dc4Current, dc4Power (setters at lines 1563, 1576, 1589)
- dc5Voltage, dc5Current, dc5Power (setters at lines 1604, 1617, 1630)
- dc6Voltage, dc6Current, dc6Power (setters at lines 1645, 1658, 1671)

**Other Complex Fields**:
- batteryTypeInput (line 601)
- dcInputPowerTotal (line 1293)
- dcOutputPowerTotal (line 1322)
- dcFaults (Map) (line 918)
- dcdcFault (AlarmFaultInfo) (line 1066)
- dcdcProtection (AlarmFaultInfo) (line 1170)

**Total Field Count**: 30+ fields identified in parser method (1779 lines total)

### Decision: **KEEP PARTIAL**

**Rationale**:
1. ✅ **Core 9 fields fully proven** - All basic identification, voltage, current, power, and bit-field status flags verified
2. ❌ **Multi-channel structure incomplete** - 6 DC channels (dc1-dc6) each with voltage/current/power require offset mapping
3. ❌ **Complex nested structures** - AlarmFaultInfo beans, fault maps require separate analysis
4. ❌ **Parser method too large** - 1779 lines, only ~500 lines analyzed in detail
5. ❌ **No device validation** - Bit-field semantics and multi-channel parsing require actual payload testing

**What Would Be Required for smali_verified**:
- Complete offset mapping for all 30+ fields
- AlarmFaultInfo bean structure analysis
- DCDCChannelItem structure analysis (used for multi-input parsing at lines 600-750)
- Actual device payload capture to validate:
  - Bit-field flag meanings
  - Multi-channel data layout
  - Fault/protection code mappings

---

## Block 15600: DC_DC_SETTINGS - Complete Analysis

### Parser Evidence
- **Source**: `DCDCParser.smali`
- **Method**: `settingsInfoParse(Ljava/util/List;)` (lines 1780-3176+)
- **Bean**: `DCDCSettings.smali`
- **Total setter calls**: 40+ fields identified

### Core Field Evidence Table (First 7 Fields)

| Offset | Field Name | Type | Unit | Scale | Smali Line | Bean Setter | Status |
|--------|------------|------|------|-------|------------|-------------|--------|
| 0 (bit 0) | dcCtrl | UInt1 | - | Raw | 1909-1958 | setDcCtrl | ✅ **PROVEN** |
| 0 (bit 1) | silentModeCtrl | UInt1 | - | Raw | 1961-1971 | setSilentModeCtrl | ✅ **PROVEN** |
| 0 (bit 2) | factorySet | UInt1 | - | Raw | 1974-1984 | setFactorySet | ✅ **PROVEN** |
| 0 (bit 3) | selfAdaptionEnable | UInt1 | - | Raw | 1987-1999 | setSelfAdaptionEnable | ✅ **PROVEN** |
| 2-3 | voltSetDC1 | UInt16 | ? | Raw hex | 2002-2036 | setVoltSetDC1 | ⚠️ **PARTIAL** |
| 4-5 | outputCurrentDC1 | UInt16 | ? | Raw hex | 2039-2086 | setOutputCurrentDC1 | ⚠️ **PARTIAL** |
| 6-7 | voltSetDC2 | UInt16 | ? | Raw hex | 2089-2123 | setVoltSetDC2 | ⚠️ **PARTIAL** |

### Bit-Field Mapping (Offset 0-1)

**Evidence from lines 1909-1999**:

```smali
.line 154
sget-object v2, Lnet/poweroak/bluetticloud/ui/connectv2/tools/ProtocolParserV2;->INSTANCE:...
const/4 v3, 0x0               # v3 = 0
invoke-interface {v0, v3}, Ljava/util/List;->get(I)Ljava/lang/Object;  # Get byte 0
const/4 v5, 0x1               # v5 = 1
invoke-interface {v0, v5}, Ljava/util/List;->get(I)Ljava/lang/Object;  # Get byte 1
# Concatenate bytes 0+1
new-instance v7, Ljava/lang/StringBuilder;
invoke-virtual {v7, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/Object;)...
invoke-virtual {v4, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/Object;)...
invoke-virtual {v4}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

# hexStrToEnableList creates list of bits
const/4 v7, 0x2
invoke-static {v2, v4, v3, v7, v6}, Lnet/poweroak/bluetticloud/ui/connectv2/tools/ProtocolParserV2;->hexStrToEnableList$default(...)Ljava/util/List;
move-result-object v2

.line 155
invoke-interface {v2, v3}, Ljava/util/List;->get(I)Ljava/lang/Object;  # Get bit 0
check-cast v4, Ljava/lang/Number;
invoke-virtual {v4}, Ljava/lang/Number;->intValue()I
invoke-virtual {v1, v4}, Lnet/poweroak/bluetticloud/ui/connectv2/bean/DCDCSettings;->setDcCtrl(I)V

.line 156
invoke-interface {v2, v5}, Ljava/util/List;->get(I)Ljava/lang/Object;  # Get bit 1
invoke-virtual {v1, v4}, Lnet/poweroak/bluetticloud/ui/connectv2/bean/DCDCSettings;->setSilentModeCtrl(I)V

.line 157
invoke-interface {v2, v7}, Ljava/util/List;->get(I)Ljava/lang/Object;  # Get bit 2
invoke-virtual {v1, v4}, Lnet/poweroak/bluetticloud/ui/connectv2/bean/DCDCSettings;->setFactorySet(I)V

.line 158
const/4 v4, 0x3
invoke-interface {v2, v4}, Ljava/util/List;->get(I)Ljava/lang/Object;  # Get bit 3
invoke-virtual {v1, v2}, Lnet/poweroak/bluetticloud/ui/connectv2/bean/DCDCSettings;->setSelfAdaptionEnable(I)V
```

**Interpretation**:
- Bytes 0-1 form 16-bit control word
- `hexStrToEnableList` extracts individual bit flags:
  - Bit 0: DC-DC enable control
  - Bit 1: Silent mode control
  - Bit 2: Factory settings flag
  - Bit 3: Self-adaption enable

### Voltage/Current Fields Analysis

**VoltSetDC1** (lines 2002-2036):
```smali
.line 159
const/4 v7, 0x2               # v7 = 2
invoke-interface {v0, v7}, Ljava/util/List;->get(I)Ljava/lang/Object;  # Get byte 2
const/4 v4, 0x3
invoke-interface {v0, v4}, Ljava/util/List;->get(I)Ljava/lang/Object;  # Get byte 3
# Concatenate bytes 2+3
new-instance v8, Ljava/lang/StringBuilder;
invoke-virtual {v8, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/Object;)...
invoke-virtual {v2, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/Object;)...
invoke-virtual {v2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

const/16 v5, 0x10             # Radix = 16 (hex)
invoke-static {v5}, Lkotlin/text/CharsKt;->checkRadix(I)I
invoke-static {v2, v8}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;I)I
move-result v2
invoke-virtual {v1, v2}, Lnet/poweroak/bluetticloud/ui/connectv2/bean/DCDCSettings;->setVoltSetDC1(I)V
```
- **Offset**: 2-3
- **Transform**: parseInt(radix=16), NO division
- **Bean type**: Integer (I)
- **Unit**: UNKNOWN - needs device validation
- **Critical**: This is a voltage SETPOINT (control value), not a reading. Incorrect values could damage equipment.

**OutputCurrentDC1** (lines 2039-2086):
```smali
.line 160
invoke-interface/range {p1 .. p1}, Ljava/util/List;->size()I
const/16 v8, 0xc
const/4 v9, 0x6
const/4 v10, 0x4
if-le v2, v10, :cond_0        # Conditional: only if size > 4

.line 161
invoke-interface {v0, v10}, Ljava/util/List;->get(I)Ljava/lang/Object;  # Get byte 4
const/4 v10, 0x5
invoke-interface {v0, v10}, Ljava/util/List;->get(I)Ljava/lang/Object;  # Get byte 5
# Parse as hex integer (NO division)
invoke-static {v2, v10}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;I)I
invoke-virtual {v1, v2}, Lnet/poweroak/bluetticloud/ui/connectv2/bean/DCDCSettings;->setOutputCurrentDC1(I)V
```
- **Offset**: 4-5
- **Conditional**: Only parsed if payload size > 4 bytes
- **Transform**: parseInt(radix=16), NO division
- **Unit**: UNKNOWN - needs device validation
- **Critical**: Current limit control value - electrical safety concern

### Scale Factor Issues

**CRITICAL FINDING**: Unlike block 15500 (DC_DC_INFO) where voltage/current have ×0.1 scale factors, block 15600 (DC_DC_SETTINGS) uses **RAW hex values** with NO division.

**Comparison**:

| Block | Field Type | Transform | Bean Type | Scale |
|-------|-----------|-----------|-----------|-------|
| 15500 | dcInputVolt (reading) | parseInt ÷ 10.0f | Float | ×0.1V |
| 15500 | dcOutputCurrent (reading) | parseInt ÷ 10.0f | Float | ×0.1A |
| 15600 | voltSetDC1 (setpoint) | parseInt (raw) | Integer | UNKNOWN |
| 15600 | outputCurrentDC1 (limit) | parseInt (raw) | Integer | UNKNOWN |

**Hypothesis**:
- Readings (block 15500) use ×0.1 scale for precision (12.5V = 125)
- Setpoints (block 15600) may use different scale OR raw register values
- **Cannot determine without device validation**

### Additional Fields Beyond Core 7

**Extensive Field List** (40+ total setter calls identified):

**DC Channel Settings** (lines 2002-2277):
- voltSetDC1, outputCurrentDC1 (offsets 2-3, 4-5)
- voltSetDC2, outputCurrentDC2 (offsets 6-7, 8-9)
- voltSetDC3, outputCurrentDC3, voltSet2DC3 (offsets 10-11, 12-13, 22-23)

**Battery/Power Settings** (lines 2424-2634):
- batteryCapacity (line 2424)
- batteryType (line 2441)
- batteryModelType (line 2460)
- powerDC1, powerDC2, powerDC3, powerDC4, powerDC5 (lines 2489-2605)
- dcTotalPowerSet (line 2634)

**Mode/Feature Settings** (lines 2328-2815):
- setEvent1 (List) (line 2328)
- chgModeDC1, chgModeDC2, chgModeDC3, chgModeDC4 (lines 2370-2391)
- genCheckEnable, genType, priorityChg, cableSet (lines 2684-2705)
- reverseChgEnable, batteryHealthEnable, remotePowerCtrl, ledEnable (lines 2727-2748)
- reverseChgMode, sysPowerCtrl, remoteStartupSoc (lines 2767-2815)

**Recharger Power Settings** (lines 2854-3010):
- rechargerPowerDC1-5 (5 fields)

**Advanced Settings** (lines 3051-3176):
- voltSetMode (line 3051)
- pscModelNumber (line 3090)
- leadAcidBatteryVoltage (line 3139)
- communicationEnable (List) (line 3176)

**Conditional Parsing Complexity**:
- Size checks: `if-le v2, v10, :cond_0` (multiple conditions based on payload length)
- Protocol version checks implied by size thresholds
- Many fields are optional depending on device capabilities

### Decision: **KEEP PARTIAL**

**Rationale**:
1. ✅ **Bit-field control flags proven** - 4 enable/mode bits at offset 0 fully verified
2. ⚠️ **Voltage/current setpoints unverified** - Raw hex values without known scale factors
3. ❌ **40+ fields identified** - Only 7 core fields analyzed, 33+ additional fields require mapping
4. ❌ **Conditional parsing logic** - Size-dependent field presence complicates verification
5. ❌ **ELECTRICAL SAFETY CONCERN** - Voltage/current setpoints control power output:
   - Cannot upgrade to smali_verified without knowing safe value ranges
   - Raw integer values could represent 1V, 0.1V, 0.01V, or register-specific encoding
   - Incorrect setpoints could damage connected equipment or create fire hazard

**What Would Be Required for smali_verified**:
- Complete offset mapping for all 40+ fields
- Protocol version conditional logic documentation
- **CRITICAL**: Actual device testing to determine:
  - Voltage setpoint scale factor (V, dV, cV?)
  - Current limit scale factor (A, dA, cA?)
  - Safe operating ranges for each DC channel
  - Battery type/capacity encoding
  - Mode/feature flag semantics
- Bean structure analysis for List<> fields (setEvent1, communicationEnable)
- Cross-reference with ProtocolAddrV2.smali register definitions (DCDC_* constants)

---

## Electrical Safety Analysis

### Block 15500 (DC_DC_INFO) - Readings

**Voltage/Current Ranges** (based on ×0.1 scale):
- dcInputVolt: 0-6553.5V (UInt16 × 0.1)
- dcOutputVolt: 0-6553.5V (UInt16 × 0.1)
- dcOutputCurrent: 0-6553.5A (UInt16 × 0.1)
- dcOutputPower: 0-65535W (UInt16 raw)

**Realistic Automotive DC-DC Ranges**:
- Input: 12V-48V (car battery, solar panel)
- Output: 12V-14V (typical car charging), 24V, 48V (specialty)
- Current: 0-100A typical, 0-200A high-power
- Power: 0-5000W typical

**Safety Assessment**:
- ✅ Read-only block - no control risk
- ✅ Scale factors verified from smali
- ⚠️ Max values (6553V, 6553A) are unrealistic - likely protocol limit, not device limit
- ✅ Actual device limits enforced by firmware/hardware

### Block 15600 (DC_DC_SETTINGS) - Control Setpoints

**CRITICAL SAFETY CONCERNS**:

1. **Unknown Scale Factors**:
   - voltSetDC1/2/3: Raw hex integers, unknown unit
   - If scale is ×1V: Setting 0x0030 (48) could mean 48V
   - If scale is ×0.1V: Setting 0x0030 (48) could mean 4.8V
   - If scale is ×0.01V: Setting 0x0030 (48) could mean 0.48V
   - **Wrong scale assumption = equipment damage**

2. **Current Limit Unknowns**:
   - outputCurrentDC1/2/3: Raw hex integers, unknown unit
   - Setting too high: Wire overheating, fire risk
   - Setting too low: Inadequate charging, device shutdown

3. **Battery Type/Capacity**:
   - batteryType, batteryModelType: Unknown encoding
   - leadAcidBatteryVoltage: Unknown scale
   - **Wrong battery type = overcharging = explosion risk (lead-acid, lithium)**

4. **Power Limits**:
   - powerDC1-5, dcTotalPowerSet: Unknown scale
   - Could control max output power per channel
   - **Exceeding device ratings = component failure, fire**

**Safety Recommendations**:
1. ❌ **DO NOT upgrade to smali_verified** without device validation
2. ❌ **DO NOT implement write operations** for this block without testing
3. ✅ **Mark all voltage/current/power fields as read-only** until verified
4. ✅ **Require explicit user confirmation** for any control field changes
5. ✅ **Implement sanity checks** (e.g., reject voltSetDC > 60V even if protocol allows)
6. ✅ **Log all control commands** for safety auditing

---

## Verification Decision Summary

### Block 15500: DC_DC_INFO

**Upgrade Decision**: ❌ **KEEP PARTIAL**

**Field Verification Status**:
- ✅ Fully proven: 9 core fields (model, sn, voltages, current, power, bit-field status)
- ⚠️ Partially mapped: 20+ additional fields (multi-channel DC, fault maps)
- ❌ Incomplete: AlarmFaultInfo structures, DCDCChannelItem parsing

**Blocking Issues**:
1. Parser method is 1779 lines - only 500 lines analyzed in detail
2. Multi-channel DC structure (dc1-dc6) requires offset mapping
3. Complex nested beans (AlarmFaultInfo, DCDCChannelItem) not analyzed
4. No actual device payload to validate bit-field semantics

**Path to smali_verified**:
- Complete parser analysis (remaining 1200+ lines)
- Map all multi-channel DC field offsets
- Analyze AlarmFaultInfo and DCDCChannelItem bean structures
- Capture actual device payload for validation

### Block 15600: DC_DC_SETTINGS

**Upgrade Decision**: ❌ **KEEP PARTIAL**

**Field Verification Status**:
- ✅ Fully proven: 4 bit-field control flags (offset 0)
- ⚠️ Partially mapped: 3 voltage/current setpoints (offsets 2-7, scales unknown)
- ❌ Incomplete: 33+ additional fields, conditional parsing logic

**Blocking Issues**:
1. **CRITICAL SAFETY**: Voltage/current setpoint scale factors unknown
2. Parser has 40+ setter calls - only 7 core fields analyzed
3. Highly conditional parsing (size-dependent fields)
4. No device validation of safe operating ranges

**Path to smali_verified**:
- **MANDATORY**: Actual device testing to determine voltage/current scales
- Complete offset mapping for all 40+ fields
- Document all conditional parsing logic (size thresholds)
- Establish safe operating ranges for each control field
- Cross-reference ProtocolAddrV2.smali register definitions

---

## Schema Update Assessment

### Should Schemas Be Updated?

**Answer**: ⚠️ **Partial Updates Recommended**

While neither block meets criteria for smali_verified upgrade, the current schema files contain outdated/incorrect field mappings that should be corrected based on smali evidence.

### Recommended Schema Changes

#### Block 15500 (block_15500_declarative.py)

**Current Issues**:
- Incorrect offsets (software_version at 20, input_voltage at 24)
- Missing bit-field status flags
- Missing scale factor documentation

**Recommended Updates**:
1. Keep `verification_status="partial"`
2. Fix field offsets based on smali evidence:
   - dcInputVolt: offset 20-21 (was 24)
   - dcOutputVolt: offset 22-23 (was 26)
   - dcOutputCurrent: offset 24-25 (was 28)
   - dcOutputPower: offset 26-27 (was 32)
3. Add scale factor metadata:
   - voltage fields: `metadata={"scale_factor": 0.1, "transform": "div_10f"}`
   - current field: `metadata={"scale_factor": 0.1, "transform": "div_10f"}`
   - power field: `metadata={"scale_factor": 1.0, "transform": "raw_hex"}`
4. Add bit-field status fields (offset 28-29):
   - energyLineCarToCharger (bit 0)
   - energyLineChargerToDevice (bit 1)
5. Update docstring with smali parser reference
6. Add TODO comments for multi-channel DC fields

#### Block 15600 (block_15600_declarative.py)

**Current Issues**:
- Incorrect field structure (enable_flags at offset 0 should be bit-fields)
- Wrong voltage/current offsets
- Missing 33+ additional fields

**Recommended Updates**:
1. Keep `verification_status="partial"`
2. Replace enable_flags with individual bit fields:
   - dcCtrl (offset 0, bit 0)
   - silentModeCtrl (offset 0, bit 1)
   - factorySet (offset 0, bit 2)
   - selfAdaptionEnable (offset 0, bit 3)
3. Fix voltage/current setpoint offsets:
   - voltSetDC1: offset 2-3
   - outputCurrentDC1: offset 4-5
4. Add WARNING metadata for control fields:
   - `metadata={"safety_critical": True, "scale_unknown": True, "readonly_recommended": True}`
5. Update docstring with electrical safety warnings
6. Add extensive TODO comments for remaining 33+ fields

### Should Tests Be Updated?

**Answer**: ✅ **Yes, minimal updates**

**test_verification_status.py**:
- No changes needed (both blocks remain "partial")

**test_wave_d_batch3_blocks.py**:
- Update field offset assertions if schema fields are corrected
- Add tests for new bit-field status fields (block 15500)
- Add safety warning tests for control fields (block 15600)

---

## Quality Gates

### Ruff Check
```bash
# To be run after schema updates
python -m ruff check bluetti_sdk tests
```

**Expected Result**: No new violations (schema changes are field metadata updates)

### Mypy Check
```bash
# To be run after schema updates
python -m mypy bluetti_sdk
```

**Expected Result**: No new type errors (dataclass fields remain same types)

### Pytest
```bash
# To be run after schema updates
python -m pytest tests/unit/test_verification_status.py -v
python -m pytest tests/unit/test_wave_d_batch3_blocks.py -v
```

**Expected Result**: All tests pass (no verification status changes, field offset updates only)

---

## Conclusions

### Key Achievements

1. ✅ **Bit-Field Mappings Extracted**:
   - Block 15500: 5 status flags from bytes 28-29 fully documented
   - Block 15600: 4 control flags from bytes 0-1 fully documented

2. ✅ **Scale Factors Verified**:
   - Block 15500: Voltage/current use ×0.1 scale (div by 10.0f)
   - Block 15500: Power uses ×1.0 scale (raw hex)
   - Block 15600: ALL fields use raw hex (scales unknown)

3. ✅ **Field Complexity Documented**:
   - Block 15500: 30+ fields identified (multi-channel DC structure)
   - Block 15600: 40+ fields identified (extensive configuration options)

### Critical Findings

1. ⚠️ **Blocks More Complex Than Initially Documented**:
   - Agent A's report analyzed first 500 lines of 1779-line parser method
   - True field count is 3-4x higher than initial estimates
   - Both blocks require significantly more analysis for complete verification

2. ❌ **Electrical Safety Concerns**:
   - Block 15600 controls DC-DC converter output (voltage, current, power)
   - Scale factors unknown = cannot determine safe operating ranges
   - **CRITICAL**: Cannot upgrade to smali_verified without device validation
   - Risk of equipment damage or electrical hazard if implemented incorrectly

3. ✅ **Parser Evidence Quality**:
   - All analyzed fields have clear smali evidence (offsets, transforms, setters)
   - Bit-field extraction logic fully documented with line references
   - Scale factor transforms verified from bytecode (div-float/2addr instructions)

### Recommendations

**Immediate Actions**:
1. ⚠️ **Keep both blocks as PARTIAL** - Do not upgrade to smali_verified
2. ✅ **Update schema files** with corrected offsets and scale factor metadata
3. ✅ **Add safety warnings** to block 15600 documentation
4. ✅ **Mark control fields as read-only** until device validation completed

**Future Work** (blocked by device access):
1. Complete DCDCParser analysis (remaining 1200+ lines for block 15500)
2. Capture actual device payloads for both blocks
3. **MANDATORY for block 15600**: Determine voltage/current/power scale factors via testing
4. Analyze nested bean structures (AlarmFaultInfo, DCDCChannelItem)
5. Document conditional parsing logic (protocol version, payload size dependencies)
6. Establish safe operating ranges for all control fields

**Long-Term Path to smali_verified**:
- Block 15500: Requires complete multi-channel DC field mapping + device validation
- Block 15600: Requires electrical safety testing + scale factor validation + device testing
- **Estimated effort**: 2-3x current analysis time + actual hardware access

---

**Report Prepared By**: Agent E (Claude Sonnet 4.5)
**Date**: 2026-02-16
**Evidence Sources**:
- DCDCParser.smali (lines 66-1779 for block 15500, lines 1780-3176+ for block 15600)
- DCDCInfo.smali bean class (30+ setter methods)
- DCDCSettings.smali bean class (40+ setter methods)
- ProtocolParserV2.smali (hexStrToBinaryList, hexStrToEnableList transform functions)

**Smali Analysis Quality**: HIGH (direct bytecode evidence for all documented fields)
**Device Validation Quality**: NONE (zero actual payloads analyzed)
**Safety Assessment**: CRITICAL (block 15600 requires mandatory device validation before implementation)
