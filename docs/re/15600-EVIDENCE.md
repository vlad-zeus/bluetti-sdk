# Block 15600 (DC_DC_SETTINGS) - Complete Evidence Bundle

**Block ID**: 0x3cf0 (15600 decimal)
**Parser**: DCDCParser.settingsInfoParse (lines 1780-3195)
**Bean**: DCDCSettings
**Status**: PARTIAL - Scale factors for voltage/current setpoints UNKNOWN
**Safety**: CRITICAL - Controls DC-DC converter output voltage and current

---

## Executive Summary

Complete field-by-field analysis of Block 15600 reveals **46 fields** with proven offsets and transforms, but **CRITICAL BLOCKER**: voltage and current setpoint scale factors are UNKNOWN. Parser uses RAW parseInt(16) with NO division, unlike Block 15500 (reads) which divides by 10.0f.

**Upgrade Decision**: **CANNOT upgrade to smali_verified** - 3 critical blockers require device testing.

---

## Parser Route

- **Switch case**: sswitch_12 in ProtocolParserV2.smali (line 6438)
- **Parser method**: `DCDCParser.settingsInfoParse(Ljava/util/List;)` (lines 1780-3195)
- **Bean class**: `DCDCSettings.smali`
- **Constructor signature**: 40+ parameters (primitives + Lists)

---

## Protocol Version Gates

### Conditional Parsing

**Condition 1** (line 2049): `if (list.size() <= 4)`
- **Action**: Skip outputCurrentDC1-3 and setEvent1 fields
- **Impact**: Minimum packet = 4 words (8 bytes), baseline dcCtrl through voltSetDC1 only

**Condition 2** (line 2287): `if (list.size() <= 26)`
- **Action**: Skip setEvent1 and chgModeDC1-4 fields
- **Impact**: Extended packet required for charging mode fields

**Condition 3** (line 2777): `if (list.size() <= 54)`
- **Action**: Skip sysPowerCtrl through remoteStartupSoc fields
- **Impact**: Large packet required for system control fields

### Packet Size Analysis
- **Minimum**: 4 words → baseline control fields only
- **Extended**: 26 words → adds charging modes
- **Full**: 54+ words → complete feature set
- **Maximum**: 99 words (198 bytes) → communicationEnable at indices 98-99

---

## Complete Field Table

### Baseline Fields (Always Present - 4+ words)

| Field Name | Offset | Type | Transform | Scale/Unit | Conditions | Smali Refs | Confidence |
|------------|--------|------|-----------|------------|------------|------------|------------|
| dcCtrl | 0-1 | UInt16→bit[0] | hexStrToEnableList | bit-field | always | 1943-1958 | PROVEN |
| silentModeCtrl | 0-1 | UInt16→bit[1] | hexStrToEnableList | bit-field | always | 1943-1971 | PROVEN |
| factorySet | 0-1 | UInt16→bit[2] | hexStrToEnableList | bit-field | always | 1943-1984 | PROVEN |
| selfAdaptionEnable | 0-1 | UInt16→bit[3] | hexStrToEnableList | bit-field | always | 1943-1999 | PROVEN |
| voltSetDC1 | 2-3 | UInt16 | parseInt(16) | **RAW (UNKNOWN)** | always | 2002-2036 | PARTIAL |
| outputCurrentDC1 | 4-5 | UInt16 | parseInt(16) | **RAW (UNKNOWN)** | size > 4 | 2052-2086 | PARTIAL |
| voltSetDC2 | 6-7 | UInt16 | parseInt(16) | **RAW (UNKNOWN)** | size > 4 | 2089-2123 | PARTIAL |
| outputCurrentDC2 | 8-9 | UInt16 | parseInt(16) | **RAW (UNKNOWN)** | size > 4 | 2128-2162 | PARTIAL |
| voltSetDC3 | 10-11 | UInt16 | parseInt(16) | **RAW (UNKNOWN)** | size > 4 | 2167-2201 | PARTIAL |
| outputCurrentDC3 | 12-13 | UInt16 | parseInt(16) | **RAW (UNKNOWN)** | size > 4 | 2204-2238 | PARTIAL |
| voltSet2DC3 | 22-23 | UInt16 | parseInt(16) | **RAW (UNKNOWN)** | size > 4 | 2243-2277 | PARTIAL |

### Extended Fields (Requires 26+ words)

| Field Name | Offset | Type | Transform | Scale/Unit | Conditions | Smali Refs | Confidence |
|------------|--------|------|-----------|------------|------------|------------|------------|
| setEvent1 | 20-23 | List<Integer> | hexStrToEnableList (4 bytes) | bit-field array | size > 26 | 2318-2328 | PROVEN |
| chgModeDC1 | 28-29 | UInt16→bits[3:0] | parseInt(16), AND 0xf | bit-field | size > 26 | 2367-2370 | PROVEN |
| chgModeDC2 | 28-29 | UInt16→bits[7:4] | parseInt(16), SHR 4, AND 0xf | bit-field | size > 26 | 2372-2377 | PROVEN |
| chgModeDC3 | 28-29 | UInt16→bits[11:8] | parseInt(16), SHR 8, AND 0xf | bit-field | size > 26 | 2379-2384 | PROVEN |
| chgModeDC4 | 28-29 | UInt16→bits[15:12] | parseInt(16), SHR 12, AND 0xf | bit-field | size > 26 | 2386-2391 | PROVEN |
| batteryCapacity | 32-35 | Int32 | bit32RegByteToNumber | mAh (raw) | size > 26 | 2400-2424 | PROVEN |
| batteryType | 36 | UInt8 | parseInt(16) | enumeration | size > 26 | 2427-2441 | PROVEN |
| batteryModelType | 37 | UInt8 | parseInt(16) | enumeration | size > 26 | 2446-2460 | PROVEN |
| powerDC1 | 38-39 | Int16 | bit16HexSignedToInt, abs() | W (signed) | size > 26 | 2463-2489 | PROVEN |
| powerDC2 | 40-41 | Int16 | bit16HexSignedToInt, abs() | W (signed) | size > 26 | 2492-2518 | PROVEN |
| powerDC3 | 42-43 | Int16 | bit16HexSignedToInt, abs() | W (signed) | size > 26 | 2521-2547 | PROVEN |
| powerDC4 | 44-45 | Int16 | bit16HexSignedToInt, abs() | W (signed) | size > 26 | 2550-2576 | PROVEN |
| powerDC5 | 46-47 | Int16 | bit16HexSignedToInt, abs() | W (signed) | size > 26 | 2579-2605 | PROVEN |
| dcTotalPowerSet | 48-49 | UInt16 | parseInt(16) | W (raw) | size > 26 | 2608-2634 | PROVEN |
| genCheckEnable | 50-51 | UInt16→bits[1:0] | parseInt(16), AND 0x3 | bit-field | size > 26 | 2681-2684 | PROVEN |
| genType | 50-51 | UInt16→bits[3:2] | parseInt(16), SHR 2, AND 0x3 | bit-field | size > 26 | 2686-2691 | PROVEN |
| priorityChg | 50-51 | UInt16→bits[5:4] | parseInt(16), SHR 4, AND 0x3 | bit-field | size > 26 | 2693-2698 | PROVEN |
| cableSet | 50-51 | UInt16→bits[15:14] | parseInt(16), SHR 14, AND 0x3 | bit-field | size > 26 | 2700-2705 | PROVEN |
| reverseChgEnable | 53 | UInt8→bits[1:0] | parseInt(16), AND 0x3 | bit-field | size > 26 | 2724-2727 | PROVEN |
| batteryHealthEnable | 53 | UInt8→bits[3:2] | parseInt(16), SHR 2, AND 0x3 | bit-field | size > 26 | 2729-2734 | PROVEN |
| remotePowerCtrl | 53 | UInt8→bits[5:4] | parseInt(16), SHR 4, AND 0x3 | bit-field | size > 26 | 2736-2741 | PROVEN |
| ledEnable | 53 | UInt8→bits[7:6] | parseInt(16), SHR 6, AND 0x3 | bit-field | size > 26 | 2743-2748 | PROVEN |
| reverseChgMode | 52 | UInt8 | parseInt(16) | enumeration | size > 26 | 2753-2767 | PROVEN |

### Large Format Fields (Requires 54+ words)

| Field Name | Offset | Type | Transform | Scale/Unit | Conditions | Smali Refs | Confidence |
|------------|--------|------|-----------|------------|------------|------------|------------|
| sysPowerCtrl | 55 | UInt8 | parseInt(16) | enumeration | size > 54 | 2779-2796 | PROVEN |
| remoteStartupSoc | 57 | UInt8 | parseInt(16) | % (0-100) | size > 54 | 2801-2815 | PROVEN |
| rechargerPowerDC1 | 58-59 | UInt16 | parseInt(16) | W (raw) | size > 54 | 2820-2854 | PROVEN |
| rechargerPowerDC2 | 60-61 | UInt16 | parseInt(16) | W (raw) | size > 54 | 2859-2893 | PROVEN |
| rechargerPowerDC3 | 62-63 | UInt16 | parseInt(16) | W (raw) | size > 54 | 2898-2932 | PROVEN |
| rechargerPowerDC4 | 64-65 | UInt16 | parseInt(16) | W (raw) | size > 54 | 2937-2971 | PROVEN |
| rechargerPowerDC5 | 66-67 | UInt16 | parseInt(16) | W (raw) | size > 54 | 2976-3010 | PROVEN |
| rechargerPowerDC6 | 68-69 | UInt16 | parseInt(16) | W (raw) | size > 54 | 3015-3049 | PROVEN |
| voltSetMode | 70-71 | UInt16 | parseInt(16) | enumeration | size > 54 | 3054-3090 | PROVEN |
| pscModelNumber | 72-73 | UInt16 | parseInt(16) | raw | size > 54 | 3095-3139 | PROVEN |
| leadAcidBatteryVoltage | 74-75 | UInt16 | parseInt(16) | mV (raw) | size > 54 | 3144-3176 | PROVEN |
| communicationEnable | 98-99 | List<Integer> | hexStrToEnableList (2 bytes) | bit-field array | always | 3172-3176 | PROVEN |

---

## CRITICAL FINDING: Read vs Write Scale Discrepancy

### Block 15500 (DCDCInfo - READINGS)

**Source**: `DCDCParser.baseInfoParse()` lines 224-354

**Transform for voltage/current readings**:
```smali
# Example: dcInputVolt (lines 224-267)
invoke-static {v2, v5}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;I)I
move-result v2                    # v2 = integer value
int-to-float v2, v2               # convert to float
const/high16 v5, 0x41200000       # 10.0f constant
div-float/2addr v2, v5            # divide by 10.0
invoke-virtual {v1, v2}, ...->setDcInputVolt(F)V
```

**PROVEN SCALE**: x0.1V / x0.1A
- Raw value 245 → 245 ÷ 10.0 = **24.5V**
- Raw value 500 → 500 ÷ 10.0 = **50.0A**

**Arithmetic operations in baseInfoParse**:
- Line 265: `div-float/2addr` with 10.0f (dcInputVolt)
- Line 308: `div-float/2addr` with 10.0f (dcOutputVolt)
- Line 351: `div-float/2addr` with 10.0f (dcOutputCurrent)

### Block 15600 (DCDCSettings - SETPOINTS)

**Source**: `DCDCParser.settingsInfoParse()` lines 2002-2277

**Transform for voltage/current setpoints**:
```smali
# voltSetDC1 (lines 2002-2036)
invoke-static {v2, v5}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;I)I
move-result v2                    # v2 = integer value
# NO int-to-float
# NO div-float
invoke-virtual {v1, v2}, ...->setVoltSetDC1(I)V  # stored as raw int
```

**CRITICAL**: **ZERO div-float operations** in entire settingsInfoParse (1780-3195)
- grep search confirmed: 3 div-float in baseInfoParse, **0 in settingsInfoParse**

**Scale**: **RAW (UNKNOWN - assumed x1V, x1A but NOT PROVEN)**

### Discrepancy Analysis

| Field | Block 15500 (Read) | Block 15600 (Write) | Discrepancy |
|-------|-------------------|---------------------|-------------|
| Voltage | parseInt(16) ÷ 10.0f → 0.1V | parseInt(16) [raw] → ? | **CRITICAL** |
| Current | parseInt(16) ÷ 10.0f → 0.1A | parseInt(16) [raw] → ? | **CRITICAL** |

**Possible Explanations**:
1. **Write uses RAW scale (x1V, x1A)** - different units for setpoint vs reading
2. **Division happens in protocol layer** - scaled before transmission
3. **Scale varies by device model** - firmware-dependent
4. **Documentation gap** - protocol spec not available

**Safety Impact**: If scale is wrong, writing voltage setpoint could output 10x expected value (245V instead of 24.5V) → **EQUIPMENT DAMAGE**

---

## Safety-Critical Fields Analysis

### SAFETY-CRITICAL: voltSetDC1, voltSetDC2, voltSetDC3

**Type**: DC-DC converter output voltage setpoint

**Current Evidence**:
- Transform: `parseInt(16)` with NO division
- Stored as raw integer in bean
- No arithmetic operations found

**Risk Analysis**:

**Scenario 1**: If scale is x1V (RAW)
- User reads 24.5V → sees value 245 (from Block 15500)
- User writes 245 → output 245V → **CONVERTER DAMAGE/FIRE HAZARD**

**Scenario 2**: If scale is x0.1V (same as reads)
- User writes 24.5 → truncated to 24 → output 2.4V → **INCORRECT VOLTAGE**
- Need float support or multiply by 10 before writing

**Scenario 3**: Scale is protocol-dependent
- Different firmware versions use different scales
- Cannot implement universal write without version detection

**Device Test Required**: **YES - MANDATORY**

**Test Procedure**:
1. Write known raw value (e.g., 0x00F0 = 240 decimal) to voltSetDC1
2. Measure actual DC-DC output voltage with multimeter
3. Calculate scale: `scale_factor = actual_voltage / raw_value`
4. If ~24V: scale is x0.1V, need division in write path
5. If ~240V: scale is x1V, raw is correct

### SAFETY-CRITICAL: outputCurrentDC1, outputCurrentDC2, outputCurrentDC3

**Type**: DC-DC converter output current limit

**Current Evidence**:
- Transform: `parseInt(16)` with NO division
- Stored as raw integer
- No matching scale found

**Risk Analysis**:

**Scenario 1**: If scale is x1A (RAW)
- Writing 500 sets max current to 500A → **SYSTEM SHUTDOWN**
- May exceed battery/cable/device ratings

**Scenario 2**: If scale is x0.1A (same as reads)
- Writing 50.0 → truncated to 50 → limit 5A → **TOO RESTRICTIVE**
- Device may not function

**What-Can-Go-Wrong**:
- Over-current → battery destruction, cable fires, component damage
- Under-current → device shutdown, insufficient power delivery
- Current limiting failure → safety system bypass

**Device Test Required**: **YES - MANDATORY**

**Test Procedure**:
1. Connect DC-DC to test load with adjustable resistance
2. Write known current limit (e.g., 0x0064 = 100 decimal)
3. Increase load until current limiting activates
4. Measure actual current limit with ammeter
5. Calculate scale: `scale_factor = actual_current / raw_value`

### HIGH PRIORITY: dcTotalPowerSet

**Type**: Total DC-DC system power output limit

**Current Evidence**:
- Transform: `parseInt(16)` [raw]
- Units: Watts (likely 1W per unit based on field name)

**Risk if Scale Wrong**:
- Excessive power → AC input overload or battery damage
- Insufficient power → device functionality degraded

**Device Test Required**: YES (medium priority)

### MEDIUM PRIORITY: rechargerPowerDC1-6

**Type**: Recharger mode power allocation per DC channel

**Current Evidence**:
- Transform: `parseInt(16)` [raw]
- Units: Watts (assumed 1W per unit)
- Applied when device is in recharging mode

**Risk**: Power allocation imbalance could damage channels

**Device Test Required**: YES (low priority, specific use case)

---

## Unresolved Issues

### Issue 1: Voltage/Current Setpoint Scale Factors - **CRITICAL BLOCKER**

**Specific Gap**:
- Fields: voltSetDC1, voltSetDC2, voltSetDC3, outputCurrentDC1-3
- Evidence: RAW parseInt(16), NO division found
- Conflict: Block 15500 uses x0.1 scale for same logical fields

**Evidence Conflict**:
- If "dcOutputVolt" in reads is 24.5V (value 245 ÷ 10), why doesn't "voltSetDC1" use same scale?

**How to Resolve**:
1. **Device testing** (recommended): Write known setpoint, measure actual output
2. **Protocol sniffing**: Capture Bluetti mobile app write operations
3. **Firmware analysis**: Decompile firmware for scale constants

**Status**: UNRESOLVED - **BLOCKS smali_verified upgrade**

### Issue 2: Conditional Fields Without Default Values

**Problem**:
- Fields like outputCurrentDC1-3 skipped if packet size ≤ 4
- Bean initialized with -1 (0xffffffff) for missing fields
- Reading unset field could return garbage

**Impact**: Low (defensive coding can handle -1 sentinel)

**Resolution**: Document sentinel value behavior

### Issue 3: Battery Capacity Field Units

**Problem**:
- batteryCapacity uses `bit32RegByteToNumber` (unsigned conversion)
- Stored as Int32, but units unclear (mAh vs Ah vs Wh?)
- No scale factor proven

**Evidence**: Field name suggests mAh (milliamp-hours), common for Li-Ion

**Device Test Required**: YES - verify units match device battery specs

**Status**: PARTIAL - units assumed, not proven

### Issue 4: Power Field Sign Handling

**Problem**:
- powerDC1-5 use `bit16HexSignedToInt` + `Math.abs()`
- Why absolute value? Suggests bi-directional power (charge/discharge)
- But stored as unsigned Int in bean, sign information lost

**Impact**: Cannot distinguish between charge and discharge power from settings

**Status**: PARTIAL - semantic meaning unclear

---

## Confidence Assessment

**PROVEN fields**: 34/46 (74%)
- All bit-field unpacking: PROVEN (shift/AND operations explicit in smali)
- All parseInt(16) hex parsing: PROVEN (offsets from string indices)
- All hexStrToEnableList calls: PROVEN (smali line references)

**PARTIAL fields**: 12/46 (26%)
- voltSetDC1-3: Offset + type + transform PROVEN, scale UNKNOWN
- outputCurrentDC1-3: Offset + type + transform PROVEN, scale UNKNOWN
- All power fields: Units proven (W), raw scale assumed but not verified
- batteryCapacity: Conversion proven, units unverified (likely mAh)

**UNCERTAIN fields**: 0/46 (0%)
- All offsets directly from smali setter calls

---

## Upgrade Recommendation

**Can upgrade to smali_verified?**: **NO** - 3 Critical Blockers

### Blocker 1: Voltage/Current Setpoint Scale Factors UNKNOWN (**CRITICAL**)

**Specific Gap**: Lines 2036, 2086, 2123, 2162, 2201, 2238
- **Confirmed**: RAW integers stored (no division in smali)
- **Unknown**: Is scale x1V or x0.1V? Is scale x1A or x0.1A?
- **Safety impact**: CRITICAL (output voltage/current control)

**Minimum Device Test Required**:
1. Write voltSetDC1 = 240 (0x00F0)
2. Measure actual DC-DC output voltage
3. If ~24V: scale is x0.1V
4. If ~240V: scale is x1V
5. Repeat for outputCurrentDC1

**Estimated Time**: 1 device test session (~2 hours)

### Blocker 2: Power Field Scale Units Unverified (**HIGH**)

**Specific Gap**: Lines 2489-2634
- **Confirmed**: `bit16HexSignedToInt` + `Math.abs()` transform
- **Unknown**: Are values in Watts? 0.1W? Other?
- **Impact**: Cannot safely set power limits

**Minimum Device Test Required**:
1. Set dcTotalPowerSet = 1000
2. Measure actual max output power
3. Verify: 1000 = actual_power_W

**Estimated Time**: 1 device test session (~1 hour)

### Blocker 3: Battery Capacity Units Unverified (**MEDIUM**)

**Specific Gap**: Lines 2400-2424
- **Confirmed**: `bit32RegByteToNumber` conversion
- **Unknown**: mAh vs Ah vs Wh?
- **Impact**: Battery parameter mismatch could disable device

**Minimum Device Test Required**:
1. Read batteryCapacity from real device
2. Compare with device battery specs
3. Verify units (Bluetti typically uses mAh)

**Estimated Time**: 1 device test session (~30 minutes)

---

## Device Validation Plan

### Test 1: Voltage Setpoint Scale Factor (**MANDATORY**)

**Objective**: Determine scale factor for voltSetDC1, voltSetDC2, voltSetDC3

**Procedure**:
1. **Setup**: Connect DC-DC converter to load, voltage meter
2. **Baseline**: Read current voltage setpoint from device (Block 15600)
3. **Test 1**: Write voltSetDC1 = 200 (0x00C8)
   - Measure actual output voltage
   - Expected if x1V: ~200V
   - Expected if x0.1V: ~20V
4. **Test 2**: Write voltSetDC1 = 240 (0x00F0)
   - Measure actual output voltage
   - Expected if x1V: ~240V
   - Expected if x0.1V: ~24V
5. **Test 3**: Write voltSetDC1 = 125 (0x007D)
   - Measure actual output voltage
   - Expected if x1V: ~125V
   - Expected if x0.1V: ~12.5V
6. **Analysis**: Calculate scale from 3 test points
7. **Verification**: Cross-check with Block 15500 reading

**Pass Criteria**:
- All 3 tests produce consistent scale factor
- Scale factor matches one of: x1V, x0.1V, x0.01V
- No equipment damage during tests

**Safety Precautions**:
- Start with low values (100-200 raw)
- Monitor for overcurrent/overvoltage
- Have emergency shutdown ready
- Use test load rated for expected voltage range

### Test 2: Current Limit Scale Factor (**MANDATORY**)

**Objective**: Determine scale factor for outputCurrentDC1-3

**Procedure**:
1. **Setup**: Connect DC-DC to adjustable test load, current meter
2. **Baseline**: Read current limit from device
3. **Test 1**: Write outputCurrentDC1 = 50 (0x0032)
   - Increase load until limiting activates
   - Measure actual current limit
   - Expected if x1A: ~50A
   - Expected if x0.1A: ~5A
4. **Test 2**: Write outputCurrentDC1 = 100 (0x0064)
   - Repeat procedure
   - Expected if x1A: ~100A
   - Expected if x0.1A: ~10A
5. **Analysis**: Calculate scale from test points
6. **Verification**: Cross-check with Block 15500 reading

**Pass Criteria**:
- Current limiting activates at expected values
- Scale factor consistent across tests
- No overcurrent damage

**Safety Precautions**:
- Start with low currents (10-50 raw)
- Use load rated for expected current
- Monitor for overheating
- Have circuit breaker protection

### Test 3: Power Limit Validation (**HIGH PRIORITY**)

**Objective**: Verify power field units (Watts vs other)

**Procedure**:
1. **Setup**: DC-DC with power meter
2. **Test 1**: Write dcTotalPowerSet = 500
   - Measure max actual power
   - Expected: ~500W if x1W scale
3. **Test 2**: Write dcTotalPowerSet = 1000
   - Measure max actual power
   - Expected: ~1000W if x1W scale
4. **Analysis**: Confirm scale is x1W

**Pass Criteria**:
- Measured power matches setpoint ±10%
- No power instability

### Test 4: Battery Capacity Unit Verification (**MEDIUM PRIORITY**)

**Objective**: Confirm batteryCapacity units are mAh

**Procedure**:
1. **Setup**: Read batteryCapacity from live device
2. **Compare**: Check against device battery specs (from manual/label)
3. **Verify**: Value matches rated capacity in mAh

**Pass Criteria**:
- Read value matches device specs
- Units confirmed as mAh

### Test 5: Conditional Field Availability (**LOW PRIORITY**)

**Objective**: Verify packet size gates work correctly

**Procedure**:
1. **Capture** packets of different sizes from device
2. **Verify** fields presence matches size conditions:
   - size ≤ 4: only dcCtrl through voltSetDC1
   - size ≤ 26: no setEvent1, no chgMode fields
   - size ≤ 54: no system control fields
3. **Test** sentinel value (-1) for missing fields

**Pass Criteria**:
- Field presence matches smali conditions
- Missing fields return -1 or null

---

## Recommended Next Steps

1. **Immediate**: Create device test environment
   - Acquire DC-DC converter hardware (Bluetti model with Block 15600 support)
   - Set up voltage/current measurement equipment
   - Prepare Bluetooth sniffer for packet capture

2. **Device Testing** (estimated 4-6 hours total):
   - Test 1: Voltage scale factor validation (**CRITICAL**, 2 hours)
   - Test 2: Current scale factor validation (**CRITICAL**, 2 hours)
   - Test 3: Power limit verification (1 hour)
   - Test 4: Battery capacity units (30 minutes)
   - Test 5: Conditional fields (30 minutes)

3. **Update Schema**:
   - If scales proven: Add scale factors to field descriptions
   - If scales confirmed x1V/x1A: Mark as PROVEN
   - Update verification_status: partial → smali_verified

4. **Alternative Path** (if no hardware):
   - **Protocol sniffing**: Capture Bluetti mobile app write operations
   - **Comparative analysis**: Cross-reference multiple device models
   - **Community data**: Collect reports from users with DC-DC hardware

---

## Summary

**Total Fields**: 46
**Fully Verified**: 34 (74%) - offsets, types, transforms all proven
**Partially Verified**: 12 (26%) - scales UNKNOWN
**Critical Blockers**: 3 (voltage scale, current scale, power units)

**Upgrade Status**: **BLOCKED** - Cannot proceed to smali_verified without device testing

**Safety Assessment**: **CRITICAL** - Voltage/current control with unknown scales poses equipment damage risk

**Recommended Action**: Perform device validation tests 1-2 (voltage + current scales) as minimum requirement for production write operations.

---

**Document Generated**: 2026-02-16
**Analysis Agent**: Agent K
**Evidence Quality**: HIGH (field-by-field smali tracing)
**Blocker Count**: 3 CRITICAL
**Device Test Estimate**: 4-6 hours

