# Agent D — Cross-Module Correlator: 15500 vs 15600 linkage
**Date**: 2026-02-17

---

## 15500 baseInfoParse — Current Field Confirmation

| field | div_float_line | raw_bytes | result_bean_field | scale | refs |
|---|---|---|---|---|---|
| dcInputVolt | lines 263-267 | bytes 20-21 (indices 0x14-0x15) | DCDCInfo.setDcInputVolt(F) | 0.1 V/LSB | DCDCParser.smali:263 |
| dcOutputVolt | lines 308-310 | bytes 22-23 (indices 0x16-0x17) | DCDCInfo.setDcOutputVolt(F) | 0.1 V/LSB | DCDCParser.smali:308 |
| dcOutputCurrent | lines 349-353 | bytes 24-25 (indices 0x18-0x19) | DCDCInfo.setDcOutputCurrent(F) | 0.1 A/LSB | DCDCParser.smali:349-353 |

All three use identical code pattern:
1. Two hex-string nibbles at consecutive byte indices are concatenated
2. `Integer.parseInt(hexStr, 16)` → int
3. `int-to-float` → float
4. `div-float/2addr v2, v5` where `v5 = const/high16 0x41200000` (= 10.0f)
5. Result stored to bean via setter

`dcOutputCurrent` is the **total** DC output current (aggregate), type `F` (float), stored in `DCDCInfo.dcOutputCurrent`.

Important: `dcOutputCurrent` in DCDCInfo is **distinct** from the per-port fields:
- `dc1Current` (type J/long) = per-port DC1 current measurement
- `dc2Current` (type J/long) = per-port DC2 current measurement
- `dc3Current` (type J/long) = per-port DC3 current measurement

No div-float is applied to dc1Current/dc2Current/dc3Current in baseInfoParse (they are populated through a separate iteration loop around lines 754-865).

---

## DCDCInfo Bean Fields

File: `d:\HomeAssistant\_research\reverse_engineering\bluetti_smali\smali_classes5\net\poweroak\bluetticloud\ui\connectv2\bean\DCDCInfo.smali`

All fields with types (from `.field` declarations and d2 metadata):

| Field | Type | Description |
|---|---|---|
| lastUpdateTime | J (long) | timestamp |
| model | Ljava/lang/String | device model string |
| sn | Ljava/lang/String | serial number |
| dcInputVolt | F (float) | DC input voltage (÷10 applied in baseInfoParse) |
| dcOutputVolt | F (float) | DC output voltage (÷10 applied) |
| dcOutputCurrent | F (float) | Total DC output current **(÷10 applied, scale=0.1 A/LSB)** |
| dcOutputPower | I (int) | DC output power (no scale) |
| energyLineCarToCharger | I (int) | energy line status |
| energyLineChargerToDevice | I (int) | energy line status |
| dcInputStatus1 | I (int) | |
| dcInputStatus2 | I (int) | |
| dcOutputStatus1 | I (int) | |
| dcOutputStatus2 | I (int) | |
| energyLines | List\<Integer\> | bit-expanded energy line flags |
| batteryTypeInput | I (int) | |
| dcFaults | Map\<Integer, List\<AlarmFaultInfo\>\> | fault map |
| sumFaults | List\<AlarmFaultInfo\> | |
| dcdcFault | AlarmFaultInfo | |
| chargerFault | List\<AlarmFaultInfo\> | |
| dcdcProtection | AlarmFaultInfo | |
| workingMode | I (int) | |
| dcInputPowerTotal | J (long) | |
| dcOutputPowerTotal | J (long) | |
| dc1Voltage | I (int) | Per-port DC1 voltage |
| **dc1Current** | **J (long)** | **Per-port DC1 current (NOT the same as dcOutputCurrent)** |
| dc1Power | I (int) | |
| dc2Voltage | I (int) | |
| **dc2Current** | **J (long)** | **Per-port DC2 current** |
| dc2Power | I (int) | |
| dc3Voltage | I (int) | |
| **dc3Current** | **J (long)** | **Per-port DC3 current** |
| dc3Power | I (int) | |
| dc4Voltage | I (int) | |
| dc4Current | J (long) | |
| dc4Power | I (int) | |
| dc5Voltage | I (int) | |
| dc5Current | J (long) | |
| dc5Power | I (int) | |
| dc6Voltage | I (int) | |
| dc6Current | J (long) | |
| dc6Power | I (int) | |
| softwareType | I (int) | |
| softwareVer | I (int) | |
| carBatterySOC | I (int) | |
| packVoltType | J (long) | |
| dcCtrl | I (int) | |

**No separate DC1/DC2/DC3 current fields exist in DCDCInfo that use float type with ÷10 scale.** The per-port currents (dc1Current, dc2Current, dc3Current) are of type long (J) and are NOT the `dcOutputCurrent` (float) field.

---

## DCDCHomeActivity — Dual-Bean Co-access

File: `d:\HomeAssistant\_research\reverse_engineering\bluetti_smali\smali_classes5\net\poweroak\bluetticloud\ui\connectv2\activity\DCDCHomeActivity.smali`

### Evidence of simultaneous access to DCDCInfo + DCDCSettings

**1. initData$lambda$3 — when DCDCSettings update arrives (lines 918-1162)**

Lines 992-1006: After receiving a new DCDCSettings (p1), the code:
- Stores the new settings object: `iput-object p1, p0, ...dcdcSettings` (line 992)
- Immediately checks `dcdcInfo` is non-null (line 995)
- Copies `settings.getDcCtrl()` into `info.setDcCtrl()` (lines 1002-1006)

This is a **field copy** (dcCtrl from settings → info), not a current comparison.

Lines 1130-1162: Displays `voltSetDC1` with ÷10 for voltage:
```
invoke-virtual {p1}, DCDCSettings->getVoltSetDC1()I   # line 1130
int-to-float v5, v5
const/high16 v8, 0x41200000    # 10.0f  (line 1136)
div-float/2addr v5, v8          # line 1138
```
Format string "%sV" confirms this is a voltage display. `outputCurrentDC1` and `outputCurrentDC2` are **never called** in DCDCHomeActivity.

**2. Navigation to ChargerSettingsVoltageActivityV2 (lines 4309-4341)**

Both beans are accessed on same navigation event:
- Line 4309: `iget-object v2, v0, ...->dcdcSettings:DCDCSettings` → passed as Intent extra "chargerSettings"
- Line 4320: `iget-object v2, v0, ...->dcdcInfo:DCDCInfo` → reads `getBatteryTypeInput()` to pass as Intent extra "batteryType"

This is a navigation co-access (passing both to sub-activity), not a direct current comparison.

### Any implied scale relationship from co-display logic

**NONE FOUND.** `getOutputCurrentDC1()` and `getOutputCurrentDC2()` are **never called** in DCDCHomeActivity. There is no side-by-side display of the 15500 read current alongside the 15600 DC1/DC2 setpoints.

---

## ProtocolParserV2 — Write Path for Block 15600

File: `d:\HomeAssistant\_research\reverse_engineering\bluetti_smali\smali_classes5\net\poweroak\bluetticloud\ui\connectv2\tools\ProtocolParserV2.smali`

### Block 0x3CF0 in sparse-switch table (line 6438):
```
0x3cf0 -> :sswitch_12
```

Context: This switch table is in method `getReadTask(ILjava/lang/String;III)` (line 5626). For block address 0x3CF0, the code at `:sswitch_12` (line 5785-5793) returns a **data-length value** (either 0x38=56 bytes or 0x24=36 bytes depending on firmware version check `v1 < 0x7e2`). This is the READ task byte-length calculation, **not a write path**.

### outputCurrentDC1/DC2 in write path: ABSENT

A global search across all smali in `smali_classes5` confirms: `getOutputCurrentDC1()` and `setOutputCurrentDC1()` are only referenced in:
- `DCDCParser.smali` (the parse/settingsInfoParse methods)
- `DCDCSettings.smali` (the bean's own getter/setter/Parcelable/equals methods)

**No write command construction using outputCurrentDC1 or outputCurrentDC2 exists anywhere in the APK.**

---

## Shared Helpers

| Helper method | Used in baseInfoParse? | Used in settingsInfoParse? | Notes |
|---|---|---|---|
| `ProtocolParserV2.hexStrToBinaryList$default` | YES (line 429) | YES (line 1943) | Parses hex-string pairs into enable-bit lists |
| `ProtocolParserV2.hexStrToEnableList$default` | YES (line 486) | YES (line 1943, 2318) | Parses hex-string into list of enable bits |
| `ProtocolParse.getASCIIStr` | YES (line 203) | NO | Only for model string in baseInfoParse |
| `ProtocolParserV2.bit32RegByteToNumber$default` | NO (in baseInfoParse region) | YES (line 2418) | Used in settingsInfoParse for battery capacity |
| `Kotlin Integer.parseInt(hexStr, 16)` (radix=16) | YES (many) | YES (many) | Identical hex parse pattern used in both methods |
| `div-float/2addr v, 10.0f` | YES (lines 265, 308, 351) | NO — not present | **CRITICAL: ÷10 scale is ONLY in baseInfoParse, NOT in settingsInfoParse** |

No helper method is shared that performs unit conversion in both directions (raw→float for reads, float→raw for writes). The two parse methods do not share any scale-transformation helper.

---

## DCDCSettings Bean — outputCurrentDC1/2/3 Write Path Summary

File: `d:\HomeAssistant\_research\reverse_engineering\bluetti_smali\smali_classes5\net\poweroak\bluetticloud\ui\connectv2\bean\DCDCSettings.smali`

Fields:
- `outputCurrentDC1:I` (integer, line 298)
- `outputCurrentDC2:I` (integer, line 300)
- `outputCurrentDC3:I` (integer, line 302)

### outputCurrentDC3 write path — PROVEN scale via UI (strongest evidence)

File: `d:\HomeAssistant\_research\reverse_engineering\bluetti_smali\smali_classes4\net\poweroak\bluetticloud\ui\connect\activity\DeviceSettingsSingleRangeActivity.smali`

**Display of outputCurrentDC3** (DCDCSettingsAdvActivity.smali lines 794-822):
```smali
invoke-virtual {v4}, DCDCSettings->getOutputCurrentDC3()I  # line 794
int-to-float v4, v4
const/high16 v6, 0x41200000    # 10.0f  (line 800)
div-float/2addr v4, v6          # line 802
# appended with "A" string → displays as X.Y A
```
Widget: `kvvMaxOutputCurrent` binding (line 790).
**Confirmed: outputCurrentDC3 raw integer ÷ 10 = amps displayed.**

**Write of outputCurrentDC3** (DeviceSettingsSingleRangeActivity.smali, key "dcdc_max_chg_current"):

The `DeviceRangeSettingBean` is created at lines 716-748:
```smali
const/high16 v10, 0x41200000    # factor = 10.0f  (line 736)
const-string v9, "A"            # unit = "A"       (line 734)
const/16 v8, 0x37               # maxValue = 55    (line 732)
const/16 v12, 0x3cf6            # writeAddress = 0x3CF6 = 15606  (line 740)
```

The write callback at lines 2200-2238:
```smali
# get slider max value (float)
invoke-virtual {v3}, DeviceSettingRangeValueLayout->getFactor()F
move-result v3
mul-float/2addr v0, v3          # multiply by factor (10.0f)  (line 2224)
float-to-int v6, v0
const/16 v5, 0x3cf6             # target register = 0x3CF6 = 15606  (line 2232)
invoke-static addSetTask(activity, 0x3CF6, value*10, ...)  (line 2238)
```

**Conclusion: user enters value in amps; the APK multiplies by 10 before writing to wire. Wire value = A × 10. Scale = 0.1 A/LSB.**

Register address 0x3CF6 = block 15600 word-offset +6 = `outputCurrentDC3` position in the 15600 block layout.

### outputCurrentDC1 and outputCurrentDC2 write path — ABSENT

No `addSetTask`, `commonSetTask`, or write command construction for addresses 0x3CF2 or 0x3CF4 (the expected word offsets for DC1 and DC2 current) was found anywhere in the APK. A search across all smali files for `0x3cf2`, `0x3cf3`, `0x3cf4`, `0x3cf5` returned zero DCDC-related matches.

**`getOutputCurrentDC1()` and `getOutputCurrentDC2()` are called only in `DCDCParser.smali` (parse) and `DCDCSettings.smali` (bean internals). They are not called in any display or write UI.**

---

## Explicit Linkage Table

| Candidate linkage | Hard proof (file:line)? | Verdict |
|---|---|---|
| `dcOutputCurrent` (15500 read) and `outputCurrentDC1` (15600 setpoint) compared side by side | NO — `getOutputCurrentDC1()` never called in DCDCHomeActivity | NO LINKAGE |
| `dcOutputCurrent` (15500 read) and `outputCurrentDC3` (15600 setpoint) compared side by side | NO — not co-accessed in any display method | NO LINKAGE |
| `outputCurrentDC3` write-path scale × 10 (DeviceSettingsSingleRangeActivity:2224) confirms same scale as read-path ÷10 | YES — direct scale symmetry: read ÷10, write ×10 | CONFIRMED for DC3 |
| `voltSetDC1` display in DCDCHomeActivity uses ÷10 (line 1138) → implies voltSetDC1 raw = V×10 | YES — DCDCHomeActivity.smali:1136-1138 | CONFIRMED for voltSetDC1 scale |
| `voltSetDC1` write address = 0x3CF1 (word offset +1 from 0x3CF0) confirming block layout | YES — DCDCSettingsVoltageActivity$setup$1.smali:110 | CONFIRMED |
| `outputCurrentDC3` write address = 0x3CF6 (word offset +6 from 0x3CF0) confirming block layout | YES — DeviceSettingsSingleRangeActivity.smali:740,2232 | CONFIRMED |
| `outputCurrentDC1` or `outputCurrentDC2` display with ÷10 scale anywhere in APK | NO — not found | ABSENT |
| `outputCurrentDC1` or `outputCurrentDC2` write path with ×10 scale anywhere in APK | NO — not found | ABSENT |

---

## Block 15600 (0x3CF0) Word Layout Reconstruction

From parse order in `settingsInfoParse` and confirmed write addresses:

| Word offset | Register addr | Field name | Confirmed write addr? | Scale evidence |
|---|---|---|---|---|
| 0 | 0x3CF0 | dc ctrl / silentMode / factorySet / selfAdaption bits | YES (line 678, DCDCSettingsAdvActivity) | bit fields, no float scale |
| 1 | 0x3CF1 | voltSetDC1 | YES (DCDCSettingsVoltageActivity$setup$1:110) | ÷10 for display (DCDCHomeActivity:1138) |
| 2 | 0x3CF2 | outputCurrentDC1 | NO write path found | UNKNOWN — inferred 0.1 A/LSB by analogy |
| 3 | 0x3CF3 | voltSetDC2 | Confirmed as result-addr in DeviceChargerSettingVoltSelFragment:811 | inferred ÷10 by analogy with voltSetDC1 |
| 4 | 0x3CF4 | outputCurrentDC2 | NO write path found | UNKNOWN — inferred 0.1 A/LSB by analogy |
| 5 | 0x3CF5 | voltSetDC3 | NO write path found | inferred ÷10 by analogy |
| 6 | 0x3CF6 | outputCurrentDC3 | YES (DeviceSettingsSingleRangeActivity:740,2232) | CONFIRMED 0.1 A/LSB (×10 on write) |

---

## Verdict

- **Explicit 15500↔15600 scale linkage found**: **NO**
  - There is no code that directly compares or co-displays `dcOutputCurrent` (the 15500 read value) with `outputCurrentDC1` or `outputCurrentDC2` (15600 setpoints). No method simultaneously accesses both with a scale relationship.

- **Protocol write path scale found for outputCurrentDC3**: **YES**
  - `DeviceSettingsSingleRangeActivity.smali:736` (factor = 10.0f, unit = "A") and `:2224` (mul-float × 10.0f before `addSetTask` at address 0x3CF6)
  - `DCDCSettingsAdvActivity.smali:794-802` (getOutputCurrentDC3() ÷ 10.0f displayed as "A")
  - **Confirmed scale for outputCurrentDC3 = 0.1 A/LSB**

- **Protocol write path scale found for outputCurrentDC1/2**: **NO**
  - No write path, no display code with scaling, no `DeviceRangeSettingBean` for addresses 0x3CF2 or 0x3CF4 found anywhere in the APK.

- **Strongest cross-module evidence**:
  The strongest evidence is an **inductive chain** rather than a direct link:
  1. `outputCurrentDC3` (word offset +6 in block 15600) is confirmed scale = 0.1 A/LSB via both read display (÷10) and write path (×10).
  2. `dcOutputCurrent` in block 15500 (baseInfoParse) uses the identical ÷10 scale for the total DC output current.
  3. `voltSetDC1` (word offset +1) and presumably voltSetDC2/3 use ÷10 for voltage in the same block, showing the block consistently uses ×10 integer encoding.
  4. By structural analogy — all "current" fields in DCDC blocks use 0.1 A/LSB — it is **strongly inferred** that `outputCurrentDC1` (0x3CF2) and `outputCurrentDC2` (0x3CF4) use the **same scale = 0.1 A/LSB**.
  5. However, no explicit code was found that **proves** this for DC1/DC2. The fields exist in the bean, are populated by settingsInfoParse with no scale applied (raw integer stored), and are never displayed or written through any identified UI path. Their scale remains **inferred, not proven**.

---

## File References Summary

| File | Key evidence |
|---|---|
| `smali_classes5/.../tools/DCDCParser.smali` | baseInfoParse ÷10 at lines 265, 308, 351; settingsInfoParse raw-int assignment at lines 2086, 2162, 2238 |
| `smali_classes5/.../bean/DCDCInfo.smali` | Fields: dcOutputCurrent:F at line 341; dc1Current:J at line 282; dc2Current:J at line 288 |
| `smali_classes5/.../bean/DCDCSettings.smali` | Fields: outputCurrentDC1:I at line 298; outputCurrentDC2:I at line 300; outputCurrentDC3:I at line 302 |
| `smali_classes5/.../activity/DCDCHomeActivity.smali` | voltSetDC1 ÷10 display at lines 1130-1138; dual-bean navigation at lines 4309-4341 |
| `smali_classes5/.../activity/DCDCSettingsAdvActivity.smali` | outputCurrentDC3 ÷10 display at lines 794-822; block 0x3CF0 write at line 678 |
| `smali_classes5/.../activity/DCDCSettingsVoltageActivity$setup$1.smali` | voltSetDC1 write at address 0x3CF1 at line 110 |
| `smali_classes4/.../activity/DeviceSettingsSingleRangeActivity.smali` | "dcdc_max_chg_current" → factor=10.0f + addr=0x3CF6 at lines 716-748; ×10 write at lines 2224-2238 |
| `smali_classes5/.../tools/ProtocolParserV2.smali` | 0x3cf0 in getReadTask sparse-switch at line 6438; returns data-length only |
