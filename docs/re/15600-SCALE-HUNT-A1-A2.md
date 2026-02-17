# Block 15600 — Scale Hunt A1+A2

**Date**: 2026-02-17
**Analyst**: Forensic Scale Hunt Agent
**Timebox**: Fast pass — stop at first conclusive evidence or exhaustion

---

## 1. Search Scope

Files searched (in pass order):

| Pass | File | Path |
|---|---|---|
| P1 | DCDCSettings.smali | `smali_classes5/net/poweroak/bluetticloud/ui/connectv2/bean/DCDCSettings.smali` |
| P2 | DCDCCableSettingsActivity.smali | `smali_classes5/net/poweroak/bluetticloud/ui/connectv2/activity/DCDCCableSettingsActivity.smali` |
| P2-inner | DCDCCableSettingsActivity$initView$3$1.smali | same dir |
| P2-inner | DCDCCableSettingsActivity$initView$5$1.smali | same dir |
| P3 | DeviceSettingsSingleRangeActivity$dcdcSettingsInfoHandle$1.smali | `smali_classes4/net/poweroak/bluetticloud/ui/connect/activity/` |
| P3-main | DeviceSettingsSingleRangeActivity.smali | same dir |
| P4 | DCDCParser.smali | `smali_classes5/net/poweroak/bluetticloud/ui/connectv2/tools/DCDCParser.smali` |
| P5-caller | DCDCHomeActivity.smali | `smali_classes5/net/poweroak/bluetticloud/ui/connectv2/activity/` |
| P5-caller | ChargerSettingsVoltageActivityV2.smali | same dir |
| P5-caller | DCDCSettingsAdvActivity.smali | same dir |
| P5-caller | ChargerSettingsVoltageActivityV4.smali | same dir |
| P5-caller | ChargerSettingsPowerActivity.smali | same dir |
| P5-caller | DeviceChargerSettingVoltageFragment.smali | `smali_classes5/net/poweroak/bluetticloud/ui/connectv2/fragment/` |
| P5-caller | DeviceConnSettingsProtocolV2ActivityUI2.smali | `smali_classes5/net/poweroak/bluetticloud/ui/connectv2/activity/` |
| P5-caller | ChargerGenSettingsActivity.smali | same dir |
| P5-caller | ChargerSettingsVoltageActivityV4$showModeSelectDialog$1$3.smali | same dir |

**Search method**: Grep for field names, arithmetic opcodes (`mul-float`, `div-float`, `int-to-float`, `float-to-int`, `div-int/lit8`), and scale constants (`0x41200000` = 10.0f, `0x42C80000` = 100.0f) across all smali directories.

---

## 2. Parser Path Confirmation

DCDCParser.settingsInfoParse (block 15600) stores voltSetDC1 and outputCurrentDC1 as raw integers with no arithmetic:

**voltSetDC1** (bytes 2–3): `Integer.parseInt(str, 16)` → `setVoltSetDC1(I)` — no division after parse.

**outputCurrentDC1** (bytes 4–5, gated by `list.size() > 4`): `Integer.parseInt(str, 16)` → `setOutputCurrentDC1(I)` — no division after parse.

These facts were already known from prior analysis and are NOT contradicted by any finding in this sprint.

---

## 3. Scale Evidence Table

| Field | Evidence Status | Exact Refs | Notes |
|---|---|---|---|
| voltSetDC1 | **PROVEN scale=0.1** | DCDCHomeActivity.smali:1130-1138; ChargerSettingsVoltageActivityV2.smali:553-561, 893-901 | raw → int-to-float → div-float 10.0f (0x41200000) → display V |
| voltSetDC2 | **PROVEN scale=0.1** | ChargerSettingsVoltageActivityV4.smali:1035-1043, 1793-1801; DeviceChargerSettingVoltageFragment.smali:404-412, 1548-1556, 2102-2110; ChargerSettingsPowerActivity.smali:828-836; DeviceConnSettingsProtocolV2ActivityUI2.smali:2457-2465; ChargerSettingsVoltageActivityV4$showModeSelectDialog$1$3.smali:116-124 | same pattern as DC1 |
| voltSetDC3 | **PROVEN scale=0.1** | ChargerGenSettingsActivity.smali:1294-1302; ChargerSettingsVoltageActivityV4.smali (context, see note) | raw → int-to-float → div-float 10.0f → display "V" |
| outputCurrentDC1 | **UNKNOWN — no callers in corpus** | DCDCSettings.smali:3404-3411 only | getOutputCurrentDC1() declared+defined but zero call sites found in all smali files |
| outputCurrentDC2 | **UNKNOWN — no callers in corpus** | DCDCSettings.smali:3413-3420 only | getOutputCurrentDC2() declared+defined but zero call sites found |
| outputCurrentDC3 | **PROVEN scale=0.1** | DCDCSettingsAdvActivity.smali:794-802; DeviceSettingsSingleRangeActivity.smali:570-574 (div-int/lit8 0xa); DeviceSettingsSingleRangeActivity$dcdcSettingsInfoHandle$1.smali:156-184 (getFactor 10.0f write-path) | raw → int-to-float → div-float 10.0f → display "A"; raw/10 = display A confirmed |

**Note on voltSetDC3 in ChargerGenSettingsActivity**: At line 897, `getVoltSetDC3()I` is read and passed to `String.valueOf(I)` WITHOUT scaling — this appears to be used for a different purpose (a raw string for a UI comparison or debug log). At line 1294-1302, the same field is read for display and IS scaled by /10. The scaled path at 1294-1302 is the authoritative display path.

---

## 4. Bean Layer Analysis

**File**: `d:\HomeAssistant\_research\reverse_engineering\bluetti_smali\smali_classes5\net\poweroak\bluetticloud\ui\connectv2\bean\DCDCSettings.smali`

### Field type declarations (lines 298-362)

```smali
.field private outputCurrentDC1:I      # line 298 — integer
.field private outputCurrentDC2:I      # line 300 — integer
.field private outputCurrentDC3:I      # line 302 — integer
.field private voltSetDC1:I            # line 358 — integer
.field private voltSetDC2:I            # line 360 — integer
.field private voltSetDC3:I            # line 362 — integer
```

All six fields are declared as `I` (32-bit signed integer). No float storage.

### Setter methods (lines 4338-4362, 4584-4606)

```smali
.method public final setOutputCurrentDC1(I)V
    .locals 0
    iput p1, p0, ...->outputCurrentDC1:I    # line 4342 — direct store, NO arithmetic
    return-void
.end method

.method public final setOutputCurrentDC2(I)V
    .locals 0
    iput p1, p0, ...->outputCurrentDC2:I    # line 4351 — direct store, NO arithmetic
    return-void
.end method

.method public final setOutputCurrentDC3(I)V
    .locals 0
    iput p1, p0, ...->outputCurrentDC3:I    # line 4360 — direct store, NO arithmetic
    return-void
.end method

.method public final setVoltSetDC1(I)V
    .locals 0
    iput p1, p0, ...->voltSetDC1:I          # line 4588 — direct store, NO arithmetic
    return-void
.end method

.method public final setVoltSetDC2(I)V
    .locals 0
    iput p1, p0, ...->voltSetDC2:I          # line 4597 — direct store, NO arithmetic
    return-void
.end method

.method public final setVoltSetDC3(I)V
    .locals 0
    iput p1, p0, ...->voltSetDC3:I          # line 4606 — direct store, NO arithmetic
    return-void
.end method
```

**Finding**: All six setters are pure `iput` with zero arithmetic. The bean is a plain data object. No normalization in setters.

### Getter methods (lines 3404-3429, 3646-3671)

```smali
.method public final getOutputCurrentDC1()I
    .locals 1
    iget v0, p0, ...->outputCurrentDC1:I    # line 3408 — direct load, NO arithmetic
    return v0
.end method
```

All six getters are pure `iget` with zero arithmetic. **Conclusion: scale is applied by callers, not by bean.**

---

## 5. UI Layer Analysis

### DCDCCableSettingsActivity.smali

**File**: `d:\HomeAssistant\_research\reverse_engineering\bluetti_smali\smali_classes5\net\poweroak\bluetticloud\ui\connectv2\activity\DCDCCableSettingsActivity.smali`

**Finding**: Complete search for `mul-float`, `div-float`, `int-to-float`, `float-to-int`, `0x41200000`, `0x42C80000`, `setVoltSetDC`, `setOutputCurrentDC` returned **NO MATCHES**. This activity handles DC input source selection (P090a vs Other cable type), NOT voltage/current setpoint editing. It is NOT the user input path for setpoints.

### ChargerSettingsVoltageActivityV2.smali (volt setpoint write path)

**File**: `d:\HomeAssistant\_research\reverse_engineering\bluetti_smali\smali_classes5\net\poweroak\bluetticloud\ui\connectv2\activity\ChargerSettingsVoltageActivityV2.smali`

**Read path** (display to user, lines 553-563):
```smali
invoke-virtual {v0}, DCDCSettings;->getVoltSetDC1()I
move-result v0
int-to-float v0, v0                           # line 557
const/high16 v1, 0x41200000    # 10.0f       # line 559
div-float/2addr v0, v1                        # line 561 — raw / 10 = display volts
invoke-direct {p0, v0}, ...->setValueSet(F)V  # line 563
```

**Write path** (user value → protocol integer, lines 712-724):
```smali
iget v1, v0, ...->valueSet:F                  # line 712 — user-entered float value
const/16 v2, 0xa                              # line 714 — 10 (decimal)
int-to-float v2, v2                           # line 716
mul-float/2addr v1, v2                        # line 718 — user_V * 10 = raw int
float-to-int v1, v1                           # line 720
invoke-virtual {v2}, DCDCSettings;->getVoltSetDC1()I  # line 724 — compare with stored
```

**Conclusion for voltSetDC1**: `raw = user_volts * 10` ↔ `user_volts = raw / 10`. Scale = 0.1 V/LSB.

### DeviceSettingsSingleRangeActivity (outputCurrentDC3 write path)

**File**: `d:\HomeAssistant\_research\reverse_engineering\bluetti_smali\smali_classes4\net\poweroak\bluetticloud\ui\connect\activity\DeviceSettingsSingleRangeActivity.smali`

**Display check** (line 570-574):
```smali
invoke-virtual {p1}, DCDCSettings;->getOutputCurrentDC3()I
move-result v0
div-int/lit8 v0, v0, 0xa                      # line 574 — raw / 10 = display A (integer division)
```

**Factor assignment** (lines 714-748): The "dcdc_max_chg_current" `DeviceRangeSettingBean` is constructed with `getFactor()F` = `0x41200000` = 10.0f at line 736.

**Write path** (DeviceSettingsSingleRangeActivity$dcdcSettingsInfoHandle$1.smali lines 156-196):
```smali
invoke-virtual {p0}, DeviceSettingRangeValueLayout;->getMaxValue()I
move-result p1
int-to-float p1, p1                           # line 160
invoke-virtual {p0}, DeviceSettingRangeValueLayout;->getFactor()F
move-result p0
mul-float/2addr p1, p0                        # line 182 — display_A * 10 = raw int
float-to-int v2, p1                           # line 184
invoke-static/range {v0..v6}, BaseConnActivity;->addSetTask$default(...)V  # line 196
```

**Protocol ID used**: `const/16 v1, 0x3cf6` (line 190) = block 15606 decimal. This writes to the protocol.

**Conclusion for outputCurrentDC3**: `raw = user_amps * 10` ↔ `user_amps = raw / 10`. Scale = 0.1 A/LSB.

---

## 6. Cross-Parser Evidence

**File**: `d:\HomeAssistant\_research\reverse_engineering\bluetti_smali\smali_classes5\net\poweroak\bluetticloud\ui\connectv2\tools\DCDCParser.smali`

**baseInfoParse div-float locations confirmed**:

| Line | Operation | Target setter | Bean |
|---|---|---|---|
| 265 | `div-float/2addr v2, v5` (v5=10.0f) | `setDcInputVolt(F)` | DCDCInfo |
| 308 | `div-float/2addr v2, v5` (v5=10.0f) | `setDcOutputVolt(F)` | DCDCInfo |
| 351 | `div-float/2addr v2, v5` (v5=10.0f) | `setDcOutputCurrent(F)` | DCDCInfo |

**Critical distinction**: All three div-float operations write to `DCDCInfo` (live status bean), NOT to `DCDCSettings` (setpoints bean). These are entirely separate data paths:

- `DCDCInfo.dcOutputVolt` = live measured output voltage, stored as F (float), div by 10 in parser
- `DCDCSettings.voltSetDC1` = configured voltage setpoint, stored as I (int), div by 10 in UI layer

**Relevance to settingsInfoParse**: The parser for block 15600 uses only `Integer.parseInt(hex, 16)` with direct `iput` to `DCDCSettings` fields. The scale is deferred to UI read/write callers, consistent with the evidence found in Pass 5.

---

## 7. Verdict

**voltSetDC1 scale**: **PROVEN** — scale = 0.1 V/LSB (raw value / 10 = volts)
- Direct smali proof: ChargerSettingsVoltageActivityV2.smali lines 553-561 (display), 712-720 (write)
- Corroborating: DCDCHomeActivity.smali lines 1130-1138

**voltSetDC2 scale**: **PROVEN** — scale = 0.1 V/LSB (raw / 10 = volts)
- Direct smali proof: ChargerSettingsVoltageActivityV4.smali lines 1035-1043, DeviceChargerSettingVoltageFragment.smali lines 404-412, multiple corroborating files

**voltSetDC3 scale**: **PROVEN** — scale = 0.1 V/LSB (raw / 10 = volts)
- Direct smali proof: ChargerGenSettingsActivity.smali lines 1294-1302

**outputCurrentDC1 scale**: **UNKNOWN** — no callers in corpus
- Zero call sites found for `getOutputCurrentDC1()` outside DCDCSettings.smali itself
- By strong analogy with DC2/DC3 pattern (all use 0.1 A/LSB), scale is likely 0.1 A/LSB
- BUT: no direct smali proof — absence of caller in decompiled corpus

**outputCurrentDC2 scale**: **UNKNOWN** — no callers in corpus
- Zero call sites found for `getOutputCurrentDC2()` outside DCDCSettings.smali
- Same situation as DC1

**outputCurrentDC3 scale**: **PROVEN** — scale = 0.1 A/LSB (raw / 10 = amperes)
- Direct smali proof: DCDCSettingsAdvActivity.smali lines 794-802 (display), DeviceSettingsSingleRangeActivity.smali line 574 (display check), dcdcSettingsInfoHandle$1.smali lines 160-184 (write-path multiply)

**Evidence quality**: direct smali proof for voltSetDC1/2/3 and outputCurrentDC3; absence of evidence for outputCurrentDC1/2

---

## 8. Decision

### voltSetDC1/2/3: PROVEN — device validation NOT required for scale factor
- All three voltage setpoint fields proven scale = 0.1 V/LSB
- Direct read and write path both confirmed

### outputCurrentDC3: PROVEN — device validation NOT required for scale factor
- Display path and write path both confirm scale = 0.1 A/LSB

### outputCurrentDC1/2: UNKNOWN — reasoning by analogy only
- B1/B2 device validation **RECOMMENDED** (but not strictly mandatory for safety reasoning):
  - Reason 1: The field is architecturally parallel to DC3 (same bean, same parser, same storage type `I`)
  - Reason 2: DC3 is proven 0.1 A/LSB; DC1 and DC2 likely have identical scale
  - Reason 3: No caller was found — field may be unused in the current firmware
  - If writing DC1/DC2 current fields: treat as scale = 0.1 A/LSB (consistent with DC3) until device test can confirm
  - Risk if assumption is wrong: only if DC1/DC2 are actually writable and used by firmware

---

## 9. Raw Evidence Snippets

### A. voltSetDC1 Display Path
**File**: `d:\HomeAssistant\_research\reverse_engineering\bluetti_smali\smali_classes5\net\poweroak\bluetticloud\ui\connectv2\activity\ChargerSettingsVoltageActivityV2.smali`
```smali
;; Lines 551-563
iget-object v0, p0, ChargerSettingsVoltageActivityV2;->chargerSettings:DCDCSettings;
invoke-virtual {v0}, DCDCSettings;->getVoltSetDC1()I    # line 553
move-result v0
int-to-float v0, v0                                      # line 557 — raw int to float
const/high16 v1, 0x41200000    # 10.0f                  # line 559
div-float/2addr v0, v1                                   # line 561 — raw / 10 = display volts
invoke-direct {p0, v0}, ChargerSettingsVoltageActivityV2;->setValueSet(F)V  # line 563
```

### B. voltSetDC1 Write Path (user value → protocol)
**File**: `d:\HomeAssistant\_research\reverse_engineering\bluetti_smali\smali_classes5\net\poweroak\bluetticloud\ui\connectv2\activity\ChargerSettingsVoltageActivityV2.smali`
```smali
;; Lines 712-720
iget v1, v0, ChargerSettingsVoltageActivityV2;->valueSet:F    # line 712 — user float
const/16 v2, 0xa                                               # line 714 — literal 10
int-to-float v2, v2                                            # line 716
mul-float/2addr v1, v2                                         # line 718 — user_V * 10 = raw
float-to-int v1, v1                                            # line 720 — truncate to int
;; v1 now contains raw protocol integer (e.g. user 12.5V → raw 125)
```

### C. voltSetDC1 Display Path (DCDCHomeActivity)
**File**: `d:\HomeAssistant\_research\reverse_engineering\bluetti_smali\smali_classes5\net\poweroak\bluetticloud\ui\connectv2\activity\DCDCHomeActivity.smali`
```smali
;; Lines 1130-1138
invoke-virtual {p1}, DCDCSettings;->getVoltSetDC1()I           # line 1130
move-result v5
int-to-float v5, v5                                             # line 1134
const/high16 v8, 0x41200000    # 10.0f                         # line 1136
div-float/2addr v5, v8                                          # line 1138 — /10 for display
```

### D. voltSetDC2 Display Path
**File**: `d:\HomeAssistant\_research\reverse_engineering\bluetti_smali\smali_classes5\net\poweroak\bluetticloud\ui\connectv2\activity\ChargerSettingsVoltageActivityV4.smali`
```smali
;; Lines 1035-1043
invoke-virtual {v1}, DCDCSettings;->getVoltSetDC2()I           # line 1035
move-result v1
int-to-float v1, v1                                             # line 1039
const/high16 v2, 0x41200000    # 10.0f                         # line 1041
div-float/2addr v1, v2                                          # line 1043
```

### E. voltSetDC3 Display Path
**File**: `d:\HomeAssistant\_research\reverse_engineering\bluetti_smali\smali_classes5\net\poweroak\bluetticloud\ui\connectv2\activity\ChargerGenSettingsActivity.smali`
```smali
;; Lines 1294-1302
invoke-virtual {v1}, DCDCSettings;->getVoltSetDC3()I           # line 1294
move-result v1
int-to-float v1, v1                                             # line 1298
const/high16 v4, 0x41200000    # 10.0f                         # line 1300
div-float/2addr v1, v4                                          # line 1302
;; followed by StringBuilder.append(F) + "V" → display "12.5V" etc.
```

### F. outputCurrentDC3 Display Path
**File**: `d:\HomeAssistant\_research\reverse_engineering\bluetti_smali\smali_classes5\net\poweroak\bluetticloud\ui\connectv2\activity\DCDCSettingsAdvActivity.smali`
```smali
;; Lines 794-802
iget-object v0, v0, ...->kvvMaxOutputCurrent:KeyValueVerticalView;
iget-object v4, p0, DCDCSettingsAdvActivity;->dcdcSettings:DCDCSettings;
invoke-virtual {v4}, DCDCSettings;->getOutputCurrentDC3()I     # line 794
move-result v4
int-to-float v4, v4                                             # line 798
const/high16 v6, 0x41200000    # 10.0f                         # line 800
div-float/2addr v4, v6                                          # line 802 — /10 → amps
;; followed by StringBuilder.append(F) + "A" → display "5.5A" etc.
```

### G. outputCurrentDC3 Display Check (integer division)
**File**: `d:\HomeAssistant\_research\reverse_engineering\bluetti_smali\smali_classes4\net\poweroak\bluetticloud\ui\connect\activity\DeviceSettingsSingleRangeActivity.smali`
```smali
;; Lines 570-574
invoke-virtual {p1}, DCDCSettings;->getOutputCurrentDC3()I     # line 570
move-result v0
div-int/lit8 v0, v0, 0xa                                       # line 574 — raw / 10 (integer) = A
```

### H. outputCurrentDC3 Write Path
**File**: `d:\HomeAssistant\_research\reverse_engineering\bluetti_smali\smali_classes4\net\poweroak\bluetticloud\ui\connect\activity\DeviceSettingsSingleRangeActivity$dcdcSettingsInfoHandle$1.smali`
```smali
;; Lines 156-196 — "normal mode" confirm button handler
invoke-virtual {p0}, DeviceSettingRangeValueLayout;->getMaxValue()I
move-result p1
int-to-float p1, p1                                             # line 160
invoke-virtual {p0}, DeviceSettingRangeValueLayout;->getFactor()F  # line 178 — factor=10.0f
move-result p0
mul-float/2addr p1, p0                                          # line 182 — display_A * 10 = raw
float-to-int v2, p1                                             # line 184 — truncate to int
const/16 v1, 0x3cf6                                            # line 190 — protocol ID 0x3CF6 = 15606
invoke-static/range {v0..v6}, BaseConnActivity;->addSetTask$default(...)V  # line 196
```

### I. Bean Setter — No Arithmetic (representative)
**File**: `d:\HomeAssistant\_research\reverse_engineering\bluetti_smali\smali_classes5\net\poweroak\bluetticloud\ui\connectv2\bean\DCDCSettings.smali`
```smali
;; Lines 4584-4590 — setVoltSetDC1
.method public final setVoltSetDC1(I)V
    .locals 0
    .line 135
    iput p1, p0, DCDCSettings;->voltSetDC1:I    # line 4588 — direct store, NO arithmetic
    return-void
.end method

;; Lines 3646-3653 — getVoltSetDC1
.method public final getVoltSetDC1()I
    .locals 1
    .line 135
    iget v0, p0, DCDCSettings;->voltSetDC1:I    # line 3650 — direct load, NO arithmetic
    return v0
.end method
```

### J. baseInfoParse div-float (DCDCInfo, NOT DCDCSettings)
**File**: `d:\HomeAssistant\_research\reverse_engineering\bluetti_smali\smali_classes5\net\poweroak\bluetticloud\ui\connectv2\tools\DCDCParser.smali`
```smali
;; Line 263-267 — dcInputVolt (DCDCInfo, NOT DCDCSettings)
const/high16 v5, 0x41200000    # 10.0f    # line 263
div-float/2addr v2, v5                    # line 265
invoke-virtual {v1, v2}, DCDCInfo;->setDcInputVolt(F)V    # line 267

;; Line 306-310 — dcOutputVolt (DCDCInfo, NOT DCDCSettings)
int-to-float v2, v2                       # line 306
div-float/2addr v2, v5                    # line 308
invoke-virtual {v1, v2}, DCDCInfo;->setDcOutputVolt(F)V   # line 310

;; Line 349-353 — dcOutputCurrent (DCDCInfo, NOT DCDCSettings)
int-to-float v2, v2                       # line 349
div-float/2addr v2, v5                    # line 351
invoke-virtual {v1, v2}, DCDCInfo;->setDcOutputCurrent(F)V  # line 353
```

**These are live-status fields in DCDCInfo, completely separate from the settingsInfoParse (block 15600) DCDCSettings bean.**

---

## 10. Field Declaration Proof

**File**: `d:\HomeAssistant\_research\reverse_engineering\bluetti_smali\smali_classes5\net\poweroak\bluetticloud\ui\connectv2\bean\DCDCSettings.smali`

```smali
.field private voltSetDC1:I       # line 358
.field private voltSetDC2:I       # line 360
.field private voltSetDC3:I       # line 362
.field private outputCurrentDC1:I # line 298
.field private outputCurrentDC2:I # line 300
.field private outputCurrentDC3:I # line 302
```

All six are `I` (int). Scale is applied externally by each caller.

---

## Summary Table

| Field | Raw type | Scale | Raw → Display | Evidence files |
|---|---|---|---|---|
| voltSetDC1 | `I` (int) | 0.1 V/LSB | raw / 10 = V | ChargerSettingsVoltageActivityV2.smali:553-561, DCDCHomeActivity.smali:1130-1138 |
| voltSetDC2 | `I` (int) | 0.1 V/LSB | raw / 10 = V | ChargerSettingsVoltageActivityV4.smali:1035-1043, DeviceChargerSettingVoltageFragment.smali:404-412 |
| voltSetDC3 | `I` (int) | 0.1 V/LSB | raw / 10 = V | ChargerGenSettingsActivity.smali:1294-1302 |
| outputCurrentDC1 | `I` (int) | **UNKNOWN** | no callers | None (field unused in UI corpus) |
| outputCurrentDC2 | `I` (int) | **UNKNOWN** | no callers | None (field unused in UI corpus) |
| outputCurrentDC3 | `I` (int) | 0.1 A/LSB | raw / 10 = A | DCDCSettingsAdvActivity.smali:794-802, DeviceSettingsSingleRangeActivity.smali:574 |
