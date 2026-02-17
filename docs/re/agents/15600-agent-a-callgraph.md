# Agent A — Call-Graph Hunt: outputCurrentDC1/2
**Date**: 2026-02-17
**Mission**: Exhaustive caller search for `outputCurrentDC1` and `outputCurrentDC2` across the entire Bluetti APK smali corpus

---

## Method Signatures Found (DCDCSettings.smali)

**File**: `smali_classes5/net/poweroak/bluetticloud/ui/connectv2/bean/DCDCSettings.smali`

### Field Declarations
```smali
.field private outputCurrentDC1:I    # line 298 — type: int (I)
.field private outputCurrentDC2:I    # line 300 — type: int (I)
```

### Getter Methods
```smali
.method public final getOutputCurrentDC1()I   # line 3404
    iget v0, p0, ...DCDCSettings;->outputCurrentDC1:I   # line 3408
    return v0
.end method

.method public final getOutputCurrentDC2()I   # line 3413
    iget v0, p0, ...DCDCSettings;->outputCurrentDC2:I   # line 3417
    return v0
.end method
```

### Setter Methods
```smali
.method public final setOutputCurrentDC1(I)V   # line 4338
    iput p1, p0, ...DCDCSettings;->outputCurrentDC1:I   # line 4342
    return-void
.end method

.method public final setOutputCurrentDC2(I)V   # line 4347
    iput p1, p0, ...DCDCSettings;->outputCurrentDC2:I   # line 4351
    return-void
.end method
```

### Constructor Parameter Positions
The main constructor `.method public constructor <init>(IIIILjava/util/List;IIII...)V` (line 496):
- `p7` → `outputCurrentDC1` (7th int param after dcCtrl, silentModeCtrl, factorySet, selfAdaptionEnable, setEvent1(List), voltSetDC1)
  - line 555: `move v1, p7`
  - line 558: `iput v1, v0, ...->outputCurrentDC1:I`
- `p9` → `outputCurrentDC2` (9th param, after voltSetDC2)
  - line 565: `move v1, p9`
  - line 568: `iput v1, v0, ...->outputCurrentDC2:I`

### Kotlin Metadata Strings (annotation block, lines 107–112)
```
"getOutputCurrentDC1"   # line 107
"setOutputCurrentDC1"   # line 108
"getOutputCurrentDC2"   # line 109
"setOutputCurrentDC2"   # line 110
```
These are compile-time string constants in the Kotlin `@Metadata` annotation. They document the property names, not runtime call-sites.

---

## Corpus-Wide grep Results (exhaustive)

### Pattern: `outputCurrentDC1` (all occurrences, all files)

| File | Line | Type | Context |
|------|------|------|---------|
| DCDCSettings.smali | 25 | metadata | `"outputCurrentDC1"` (Kotlin @Metadata d2 annotation) |
| DCDCSettings.smali | 107 | metadata | `"getOutputCurrentDC1"` (Kotlin @Metadata d2 annotation) |
| DCDCSettings.smali | 108 | metadata | `"setOutputCurrentDC1"` (Kotlin @Metadata d2 annotation) |
| DCDCSettings.smali | 298 | field decl | `.field private outputCurrentDC1:I` |
| DCDCSettings.smali | 558 | constructor | `iput v1, v0, ...->outputCurrentDC1:I` (constructor `<init>`, p7) |
| DCDCSettings.smali | 1598 | copy$default | `iget v9, v0, ...->outputCurrentDC1:I` (inside `copy$default`, bit 0x40 branch) |
| DCDCSettings.smali | 2616 | component7() | `iget v0, p0, ...->outputCurrentDC1:I` (method `component7()I`) |
| DCDCSettings.smali | 2858 | equals() | `iget v1, p0, ...->outputCurrentDC1:I` (method `equals()`) |
| DCDCSettings.smali | 2860 | equals() | `iget v3, p1, ...->outputCurrentDC1:I` (method `equals()`, comparing other.outputCurrentDC1) |
| DCDCSettings.smali | 3408 | getter | `iget v0, p0, ...->outputCurrentDC1:I` (method `getOutputCurrentDC1()I`) |
| DCDCSettings.smali | 3752 | hashCode() | `iget v1, p0, ...->outputCurrentDC1:I` (method `hashCode()`) |
| DCDCSettings.smali | 4342 | setter | `iput p1, p0, ...->outputCurrentDC1:I` (method `setOutputCurrentDC1(I)V`) |
| DCDCSettings.smali | 4646 | writeToParcel | `iget v7, v0, ...->outputCurrentDC1:I` (method `writeToParcel`, Parcelable) |
| DCDCSettings.smali | 4858 | toString() | `const-string v1, ", outputCurrentDC1="` (method `toString()`) |

**No other file in the entire corpus contains `outputCurrentDC1`.**

### Pattern: `outputCurrentDC2` (all occurrences, all files)

| File | Line | Type | Context |
|------|------|------|---------|
| DCDCSettings.smali | 27 | metadata | `"outputCurrentDC2"` (Kotlin @Metadata d2 annotation) |
| DCDCSettings.smali | 109 | metadata | `"getOutputCurrentDC2"` (Kotlin @Metadata d2 annotation) |
| DCDCSettings.smali | 110 | metadata | `"setOutputCurrentDC2"` (Kotlin @Metadata d2 annotation) |
| DCDCSettings.smali | 300 | field decl | `.field private outputCurrentDC2:I` |
| DCDCSettings.smali | 568 | constructor | `iput v1, v0, ...->outputCurrentDC2:I` (constructor `<init>`, p9) |
| DCDCSettings.smali | 1622 | copy$default | `iget v11, v0, ...->outputCurrentDC2:I` (inside `copy$default`, bit 0x100 branch) |
| DCDCSettings.smali | 2632 | component9() | `iget v0, p0, ...->outputCurrentDC2:I` (method `component9()I`) |
| DCDCSettings.smali | 2876 | equals() | `iget v1, p0, ...->outputCurrentDC2:I` (method `equals()`) |
| DCDCSettings.smali | 2878 | equals() | `iget v3, p1, ...->outputCurrentDC2:I` (method `equals()`, comparing other.outputCurrentDC2) |
| DCDCSettings.smali | 3417 | getter | `iget v0, p0, ...->outputCurrentDC2:I` (method `getOutputCurrentDC2()I`) |
| DCDCSettings.smali | 3772 | hashCode() | `iget v1, p0, ...->outputCurrentDC2:I` (method `hashCode()`) |
| DCDCSettings.smali | 4351 | setter | `iput p1, p0, ...->outputCurrentDC2:I` (method `setOutputCurrentDC2(I)V`) |
| DCDCSettings.smali | 4650 | writeToParcel | `iget v9, v0, ...->outputCurrentDC2:I` (method `writeToParcel`, Parcelable) |
| DCDCSettings.smali | 4878 | toString() | `const-string v1, ", outputCurrentDC2="` (method `toString()`) |

**No other file in the entire corpus contains `outputCurrentDC2`.**

### Pattern: `setOutputCurrentDC1/2` (cross-file search)

| File | Line | Call | Enclosing Method |
|------|------|------|-----------------|
| DCDCParser.smali | 2086 | `invoke-virtual {v1, v2}, ...DCDCSettings;->setOutputCurrentDC1(I)V` | `settingsInfoParse(Ljava/util/List;)Lnet/poweroak/.../DCDCSettings;` (method starts line 1780) |
| DCDCParser.smali | 2162 | `invoke-virtual {v1, v2}, ...DCDCSettings;->setOutputCurrentDC2(I)V` | `settingsInfoParse(Ljava/util/List;)Lnet/poweroak/.../DCDCSettings;` (method starts line 1780) |
| DCDCSettings.smali | 4338 | `.method public final setOutputCurrentDC1(I)V` | (definition) |
| DCDCSettings.smali | 4347 | `.method public final setOutputCurrentDC2(I)V` | (definition) |

### Pattern: `getOutputCurrentDC` (all DC variants, cross-file search)

| File | Line | Call | Notes |
|------|------|------|-------|
| DCDCSettings.smali | 3404 | `.method public final getOutputCurrentDC1()I` | definition |
| DCDCSettings.smali | 3413 | `.method public final getOutputCurrentDC2()I` | definition |
| DCDCSettings.smali | 3422 | `.method public final getOutputCurrentDC3()I` | definition |
| DCDCSettingsAdvActivity.smali | 794 | `invoke-virtual {v4}, ...->getOutputCurrentDC3()I` | DC3 ONLY |
| DCDCSettingsAdvActivity.smali | 2026 | `invoke-virtual {v1}, ...->getOutputCurrentDC3()I` | DC3 ONLY |
| DeviceSettingsSingleRangeActivity.smali | 570 | `invoke-virtual {p1}, ...->getOutputCurrentDC3()I` | DC3 ONLY, followed by `div-int/lit8 v0, v0, 0xa` (scale=0.1) |
| DeviceSettingsSingleRangeActivity.smali | 608 | `invoke-virtual {p1}, ...->getOutputCurrentDC3()I` | DC3 ONLY |

**getOutputCurrentDC1 and getOutputCurrentDC2 are NEVER called outside DCDCSettings.smali.**

---

## Full Activity Search Log

| Activity File | Lines | Searched For | DC1 Found? | DC2 Found? | DC3 Found? | Notes |
|---|---|---|---|---|---|---|
| DCDCSettingsAdvActivity.smali | 2374 | `getOutput`, `setOutput`, `outputCurrent` | NO | NO | YES (lines 794, 2026) | Calls `getOutputCurrentDC3()` with `div-int/lit8 0xa` (scale=0.1) |
| DCDCHomeActivity.smali | 4706 | `getOutput`, `setOutput`, `outputCurrent`, DCDCSettings methods | NO | NO | NO | Calls: getSysPowerCtrl, getDcCtrl, getSilentModeCtrl, getVoltSetDC1, getChgModeDC3, getSelfAdaptionEnable only |
| DCDCSettingsVoltageActivity.smali | 1145 | `getOutput`, `setOutput`, `outputCurrent` | NO | NO | NO | Only calls getVoltSetDC1() |
| DCDCCableSettingsActivity.smali | 587 | `getOutput`, `setOutput`, `outputCurrent` | NO | NO | NO | No matches |
| DCDCInputDetailsActivity.smali | full | `getOutput`, `setOutput`, `outputCurrent` | NO | NO | NO | No matches |
| DCDCParallelCommunicationActivity.smali | full | `getOutput`, `setOutput`, `outputCurrent` | NO | NO | NO | No matches |
| DCDCChgModeActivity.smali | full | `getOutput`, `setOutput`, `outputCurrent` | NO | NO | NO | No matches |
| DCDCChgModeSelectActivity.smali | full | `getOutput`, `setOutput`, `outputCurrent` | NO | NO | NO | No matches |
| DeviceSettingsSingleRangeActivity.smali (classes4) | full | `getOutput` | NO | NO | YES (lines 570, 608) | DC3 ONLY, `div-int/lit8 0xa` confirms scale=0.1 for DC3 |

### Lambda/Inner-Class files searched (all DCDC-related)
The following inner-class and synthetic lambda files were enumerated via glob but contain no `outputCurrentDC1/2` references (confirmed by corpus-wide grep):
- `DCDCCableSettingsActivity$$ExternalSyntheticLambda0/1/2/3.smali`
- `DCDCCableSettingsActivity$initView$5$1.smali`, `$initView$3$1.smali`, `$onAttachedToWindow$1$1.smali`
- `DCDCChgModeActivity$$ExternalSyntheticLambda0/1/2.smali`, `$onClick$1$1-5.smali`
- `DCDCHomeActivity$$ExternalSyntheticLambda0-6.smali`, `$onClick$1.smali`, `$setViewClickListener$*.smali`, etc.
- `DCDCSettingsAdvActivity$$ExternalSyntheticLambda0/1/2.smali`, `$initView$1$1/2/3.smali`, `$onClick$1.smali`, `$onClick$1$1.smali`
- `DCDCSettingsVoltageActivity$$ExternalSyntheticLambda0/1/2.smali`, `$initView$2$1.smali`, `$initView$3$1.smali`, `$setup$1.smali`
- All confirmed clean by exhaustive corpus grep.

---

## ViewModel/Fragment Search

### Fragment Search
- `DeviceEnergyViewDCDC.smali` — searched for `getOutput`, `setOutput`, `outputCurrent` → **No matches**
- No fragment file named `DeviceChargerSettingVoltageFragment` exists at the searched path
- `DeviceMicroInvBindToDcdcFragment*.smali` — unrelated to DC current display
- `DeviceWifiSettingStatusFragment*` (classes4) — unrelated

### ViewModel Search
No ViewModel files with DCDC-related names (`*DCDC*ViewModel*`, `*DcDc*ViewModel*`) were found in the smali corpus via glob pattern search.

---

## DCDCParser settingsInfoParse — DC1/DC2 Parse Context

**File**: `smali_classes5/net/poweroak/bluetticloud/ui/connectv2/tools/DCDCParser.smali`
**Method**: `settingsInfoParse(Ljava/util/List;)Lnet/poweroak/bluetticloud/ui/connectv2/bean/DCDCSettings;` (line 1780)

DC1 parse (lines 2001–2086):
- `.line 159`: `List.get(v7)` and `List.get(v4)` → concatenate bytes → `Integer.parseInt(str, radix=16)` → `setOutputCurrentDC1(I)V`
- No scale factor (`div-int/lit8`) applied before set

DC2 parse (lines ~2120–2162):
- `.line 162`/`.line 163`: same pattern → `Integer.parseInt(str, radix=16)` → `setOutputCurrentDC2(I)V`
- No scale factor applied before set

DC3 parse (same method, ~line 2238):
- `setOutputCurrentDC3(I)V` called (line 2238)
- DC3 getter in `DeviceSettingsSingleRangeActivity` applies `div-int/lit8 v0, v0, 0xa` (÷10, scale=0.1) at display time

**Implication**: DC1 and DC2 values are stored raw (no ÷10 in parser, no ÷10 at any display site because there ARE no display sites). The scale factor for DC1/DC2, if any, cannot be determined from the UI call graph — the values are written to the Parcelable bean but never read by any activity or fragment.

---

## Call Graph

```
DCDCParser.settingsInfoParse()
  ├─ Integer.parseInt(bytes[6..7], 16) → DCDCSettings.setOutputCurrentDC1(I)V   [DCDCParser:2086]
  │     └─ iput p1 → DCDCSettings.outputCurrentDC1:I                            [DCDCSettings:4342]
  │           ├─ (INTERNAL ONLY) getOutputCurrentDC1()I                          [DCDCSettings:3404–3410]
  │           │     → ZERO external callers
  │           ├─ (INTERNAL) component7()I                                         [DCDCSettings:2613–2618]
  │           ├─ (INTERNAL) equals()                                              [DCDCSettings:2858,2860]
  │           ├─ (INTERNAL) hashCode()                                            [DCDCSettings:3752]
  │           ├─ (INTERNAL) copy$default()                                        [DCDCSettings:1598]
  │           ├─ (INTERNAL) writeToParcel()                                       [DCDCSettings:4646]
  │           └─ (INTERNAL) toString()                                            [DCDCSettings:4858]
  │
  └─ Integer.parseInt(bytes[8..9], 16) → DCDCSettings.setOutputCurrentDC2(I)V   [DCDCParser:2162]
        └─ iput p1 → DCDCSettings.outputCurrentDC2:I                            [DCDCSettings:4351]
              ├─ (INTERNAL ONLY) getOutputCurrentDC2()I                          [DCDCSettings:3413–3419]
              │     → ZERO external callers
              ├─ (INTERNAL) component9()I                                         [DCDCSettings:2629–2634]
              ├─ (INTERNAL) equals()                                              [DCDCSettings:2876,2878]
              ├─ (INTERNAL) hashCode()                                            [DCDCSettings:3772]
              ├─ (INTERNAL) copy$default()                                        [DCDCSettings:1622]
              ├─ (INTERNAL) writeToParcel()                                       [DCDCSettings:4650]
              └─ (INTERNAL) toString()                                            [DCDCSettings:4858→4878]

CONTRAST — DC3 (has external callers with scale evidence):
  DCDCParser.settingsInfoParse() → setOutputCurrentDC3()            [DCDCParser:2238]
  DCDCSettingsAdvActivity.update() → getOutputCurrentDC3()          [DCDCSettingsAdvActivity:794, 2026]
      div-int/lit8 v0, v0, 0xa (÷10) → display                     [DCDCSettingsAdvActivity (context)]
  DeviceSettingsSingleRangeActivity.dcdcSettingsInfoHandle() → getOutputCurrentDC3() [SingleRange:570,608]
      div-int/lit8 v0, v0, 0xa (÷10) → display                     [SingleRange:574]
```

---

## Verdict

- **outputCurrentDC1 external callers**: **ZERO**
  - `getOutputCurrentDC1()` is never called outside DCDCSettings.smali
  - `setOutputCurrentDC1()` is called only from DCDCParser.smali:2086 (the parser, not a UI consumer)
  - All internal usages (equals, hashCode, copy$default, writeToParcel, toString, component7) are within DCDCSettings.smali itself

- **outputCurrentDC2 external callers**: **ZERO**
  - `getOutputCurrentDC2()` is never called outside DCDCSettings.smali
  - `setOutputCurrentDC2()` is called only from DCDCParser.smali:2162 (the parser)
  - All internal usages (equals, hashCode, copy$default, writeToParcel, toString, component9) are within DCDCSettings.smali itself

- **Confidence in "zero external callers"**: **HIGH (EXHAUSTIVE)**
  - Search method: `grep -r outputCurrentDC1` and `grep -r outputCurrentDC2` across entire smali corpus
  - Both searches returned ONLY hits in DCDCSettings.smali
  - `grep -r getOutputCurrentDC` shows DC1/DC2 getters defined but never invoked outside the bean
  - `grep -r setOutputCurrentDC` shows DC1/DC2 setters called ONLY from DCDCParser.settingsInfoParse
  - Every DCDC-related activity file (8 activities) and fragment/view file individually verified

### Files Confirmed Searched (with negative results for DC1/DC2)

| File | Path |
|------|------|
| DCDCSettingsAdvActivity.smali | smali_classes5/.../activity/DCDCSettingsAdvActivity.smali |
| DCDCHomeActivity.smali | smali_classes5/.../activity/DCDCHomeActivity.smali |
| DCDCSettingsVoltageActivity.smali | smali_classes5/.../activity/DCDCSettingsVoltageActivity.smali |
| DCDCCableSettingsActivity.smali | smali_classes5/.../activity/DCDCCableSettingsActivity.smali |
| DCDCInputDetailsActivity.smali | smali_classes5/.../activity/DCDCInputDetailsActivity.smali |
| DCDCParallelCommunicationActivity.smali | smali_classes5/.../activity/DCDCParallelCommunicationActivity.smali |
| DCDCChgModeActivity.smali | smali_classes5/.../activity/DCDCChgModeActivity.smali |
| DCDCChgModeSelectActivity.smali | smali_classes5/.../activity/DCDCChgModeSelectActivity.smali |
| DeviceSettingsSingleRangeActivity.smali | smali_classes4/.../activity/DeviceSettingsSingleRangeActivity.smali |
| DeviceEnergyViewDCDC.smali | smali_classes5/.../view/DeviceEnergyViewDCDC.smali |
| DCDCSettings.smali (bean) | smali_classes5/.../bean/DCDCSettings.smali |
| DCDCParser.smali | smali_classes5/.../tools/DCDCParser.smali |
| (entire smali corpus) | all smali_classes* via exhaustive grep |

### Scale Implication

Since `outputCurrentDC1` and `outputCurrentDC2` have zero display consumers in the UI code:
- There is **no direct evidence of a scale factor** for DC1/DC2 from the UI layer
- DC3's scale is proven as **÷10 (scale=0.1)** by `div-int/lit8 0xa` at call-sites in DCDCSettingsAdvActivity and DeviceSettingsSingleRangeActivity
- DC1/DC2 are parsed identically to DC3 in DCDCParser.settingsInfoParse (same `parseInt(hex, 16)` pattern, no parser-side scaling)
- By analogy with DC3's confirmed scale=0.1, DC1/DC2 are **likely** scale=0.1 — but this cannot be proven from the call graph because there are no call sites to inspect
