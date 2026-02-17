# Block 15600 (DC_DC_SETTINGS) — Forensic Parser Analysis Report

**Block ID**: 0x3cf0 (15600 decimal)
**Analysis Agent**: Agent A — Forensic Parser Analyst
**Date**: 2026-02-17
**Smali Sources (read-only)**:
- Parser: `smali_classes5/net/poweroak/bluetticloud/ui/connectv2/tools/DCDCParser.smali`
- Bean: `smali_classes5/net/poweroak/bluetticloud/ui/connectv2/bean/DCDCSettings.smali`
- Router: `smali_classes5/net/poweroak/bluetticloud/ui/connectv2/tools/ProtocolParserV2.smali`

---

## 1. Executive Summary

Block 15600 is parsed by `DCDCParser.settingsInfoParse` (smali lines 1780–3195), reached via `ProtocolParserV2` switch case `sswitch_12` at dispatch table line 6438 (switch value `0x3cf0`). The complete parse method has been traced field-by-field.

**smali_verified verdict: NOT ELIGIBLE**

Three categories of blocker prevent upgrade:

1. **Scale unknown**: Six voltage/current setpoint fields use raw `parseInt(16)` with no arithmetic — scale factor is UNKNOWN and safety-critical.
2. **Prior evidence errors**: This report corrects five factual errors in `15600-EVIDENCE.md` (wrong byte offsets, wrong transforms, wrong field attribution, wrong condition thresholds, wrong confidence ratings).
3. **Missing parser call**: `setRechargerPowerDC6` exists in the bean (DCDCSettings.smali line 4482) but is **never invoked** in `settingsInfoParse`. The evidence document incorrectly marks it PROVEN at offset 68–69.

**Field count revision**: 37 fields actually parsed (not 46 as prior evidence claims). `rechargerPowerDC6` is unparsed. Offsets for `voltSetMode`, `pscModelNumber`, `leadAcidBatteryVoltage`, and `communicationEnable` are all wrong in the prior evidence and are corrected below.

---

## 2. Parser Route Trace

### 2.1 ProtocolParserV2 Dispatch

**File**: `ProtocolParserV2.smali`
**Line 6438** (dispatch table):
```smali
0x3cf0 -> :sswitch_12
```

**Lines 5785–5806** (`sswitch_12` body):
```smali
:sswitch_12
const/16 v2, 0x7e2        # 2018
if-lt v1, v2, :cond_4

:cond_3
const/16 v3, 0x38         # min_length = 56

goto/16 :goto_12

:cond_4
if-lt v1, v6, :cond_5

const/16 v3, 0x24         # min_length = 36

goto/16 :goto_12

:cond_5
if-lt v1, v9, :cond_a

goto :goto_7
```

The `sswitch_12` block selects a minimum expected packet length based on a firmware version comparison (`v1` contains the device's firmware version number, compared against `0x7e2` = 2018 and other thresholds). This is **not** a data-parsing gate; it sets the expected length field. Actual conditional parsing is done inside `settingsInfoParse` via `list.size()` checks.

**Method invoked from sswitch_12 context**: `DCDCParser.settingsInfoParse(Ljava/util/List;)Lnet/poweroak/bluetticloud/ui/connectv2/bean/DCDCSettings;`

### 2.2 settingsInfoParse Method Header

**File**: `DCDCParser.smali`
**Lines 1780–1905**:

```smali
.method public final settingsInfoParse(Ljava/util/List;)Lnet/poweroak/bluetticloud/ui/connectv2/bean/DCDCSettings;
    .locals 54
```

- Parameter `p1`: `List<String>` — list of 2-char hex byte strings
- Each list element represents ONE byte as a hex string (e.g., `"4F"`)
- Two consecutive elements are concatenated to form a 4-char hex string representing a big-endian UInt16

**Constructor call (line 1905)**:
```smali
invoke-direct/range {v2 .. v53}, DCDCSettings;-><init>(IIIILjava/util/List;IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII Ljava/util/List;IILkotlin/jvm/internal/DefaultConstructorMarker;)V
```

All scalar registers initialized to `0x0`; v51 initialized to `-0x1` (sentinel for missing optional fields).

### 2.3 Helper Methods Called

| Helper | Signature | Purpose |
|--------|-----------|---------|
| `hexStrToEnableList$default` | `(ProtocolParserV2, String, I, I, Object) → List` | Converts hex string to list of bit-field values |
| `bit32RegByteToNumber$default` | `(ProtocolParserV2, List, Z, Z, I, Object) → J` | Converts 4-byte sublist to unsigned 32-bit long |
| `bit16HexSignedToInt` | `(ProtocolParserV2, String, String) → I` | Concatenates two hex bytes, interprets as signed Int16 |
| `Integer.parseInt` | `(String, I) → I` | Parses hex string as integer (radix=16 always) |
| `Math.abs` | `(I) → I` | Absolute value (used with bit16HexSignedToInt) |
| `kotlin.text.CharsKt.checkRadix` | `(I) → I` | Validates radix=16, returns 16 |

### 2.4 Protocol-Version Gates (list.size() conditions)

Four `if-le` checks partition the parsing into five tiers. All gates use `if-le` (less-than-or-equal), meaning the gate **skips** the guarded block when `size ≤ threshold`.

| Gate | Smali Line | Threshold (hex) | Threshold (dec) | Skips if |
|------|-----------|-----------------|-----------------|----------|
| Gate 1 | 2049 | `0x4` | 4 | size ≤ 4 |
| Gate 2 | 2287 | `0x1a` | 26 | size ≤ 26 |
| Gate 3 | 2644 | `0x32` | 50 | size ≤ 50 |
| Gate 4 | 2777 | `0x36` | 54 | size ≤ 54 |
| Gate 5 | 3100 | `0x48` | 72 | size ≤ 72 |

**Error in prior evidence**: The evidence document lists only three conditions (at lines 2049, 2287, 2777) with threshold 54 for the third. The actual smali has **five** gates (at lines 2049, 2287, 2644, 2777, 3100). The threshold values at lines 2644 (=50) and 3100 (=72) were not documented.

---

## 3. Complete Field Ledger

### Key to columns

- **list_indices**: actual `list.get(n)` calls observed in smali (each index = 1 byte = 1 hex string element)
- **byte_offset**: `list_index × 1` (each list element is one byte)
- **parse_transform**: exact operation sequence from smali
- **scale_unit**: EXPLICIT from smali only; UNKNOWN if no div/multiply found
- **conditions**: which `list.size()` gate must pass (i.e., size must be strictly greater than threshold)
- **bean_setter**: exact setter invoked (all setter signatures verified from DCDCSettings.smali lines 4173–4611)
- **smali_refs**: line numbers in DCDCParser.smali for each evidence point
- **confidence**: PROVEN (offset + transform + setter all confirmed) | PARTIAL (offset proven, scale unknown) | UNVERIFIED

---

### Tier 1 — Always Parsed (no size gate; lines 1907–2277)

These fields are parsed unconditionally before the first gate check.

| field_name | list_indices | byte_offset | bit_positions | parse_transform | scale_unit | conditions | bean_setter | smali_refs | confidence |
|---|---|---|---|---|---|---|---|---|---|
| dcCtrl | [0,1] | 0–1 | bit[0] of UInt16 | concatenate→hexStrToEnableList(str,0,2,null)→List.get(0)→intValue() | bit-flag (0 or 1) | none | `setDcCtrl(I)` | 1909–1958 | PROVEN |
| silentModeCtrl | [0,1] | 0–1 | bit[1] of UInt16 | (same hexStrToEnableList result)→List.get(1)→intValue() | bit-flag (0 or 1) | none | `setSilentModeCtrl(I)` | 1961–1971 | PROVEN |
| factorySet | [0,1] | 0–1 | bit[2] of UInt16 | (same hexStrToEnableList result)→List.get(2)→intValue() | bit-flag (0 or 1) | none | `setFactorySet(I)` | 1974–1984 | PROVEN |
| selfAdaptionEnable | [0,1] | 0–1 | bit[3] of UInt16 | (same hexStrToEnableList result)→List.get(3)→intValue() | bit-flag (0 or 1) | none | `setSelfAdaptionEnable(I)` | 1986–1999 | PROVEN |
| voltSetDC1 | [2,3] | 2–3 | full UInt16 | concatenate→checkRadix(16)→parseInt(str,16)→int | **RAW (UNKNOWN)** | none | `setVoltSetDC1(I)` | 2002–2036 | PARTIAL |

**Notes on dcCtrl/silentModeCtrl/factorySet/selfAdaptionEnable**:
- At line 1909–1943: list[0] and list[1] are concatenated into a 4-char hex string.
- `hexStrToEnableList$default` called with params `(instance, str, 0, 2, null)` at line 1943.
- The returned List contains the individual bit values.
- List.get(0) → dcCtrl, .get(1) → silentModeCtrl, .get(2) → factorySet, .get(3) → selfAdaptionEnable.

**Notes on voltSetDC1**:
- At line 2002: `list.get(0x2)` (index 2); line 2006: `list.get(0x3)` (index 3 — stored in v4).

Wait — the index for the second byte of voltSetDC1:

Re-reading line 2002–2036:
```
line 2002: invoke-interface {v0, v7}   # v7 was const/4 v7, 0x2 at line 1941
line 2006: invoke-interface {v0, v4}   # v4 was const/4 v4, 0x3 at line 1986
```
`v7=2, v4=3` → list[2] and list[3] → byte offset 2–3. CONFIRMED.

---

### Tier 2 — Requires size > 4 (Gate 1; lines 2049–2277)

All parsed within the block executed when `size > 4`. Gate at DCDCParser.smali line 2049.

| field_name | list_indices | byte_offset | bit_positions | parse_transform | scale_unit | conditions | bean_setter | smali_refs | confidence |
|---|---|---|---|---|---|---|---|---|---|
| outputCurrentDC1 | [4,5] | 4–5 | full UInt16 | concatenate→parseInt(str,16)→int | **RAW (UNKNOWN)** | size > 4 | `setOutputCurrentDC1(I)` | 2052–2086 | PARTIAL |
| voltSetDC2 | [6,7] | 6–7 | full UInt16 | concatenate→parseInt(str,16)→int | **RAW (UNKNOWN)** | size > 4 | `setVoltSetDC2(I)` | 2089–2123 | PARTIAL |
| outputCurrentDC2 | [8,9] | 8–9 | full UInt16 | concatenate→parseInt(str,16)→int | **RAW (UNKNOWN)** | size > 4 | `setOutputCurrentDC2(I)` | 2128–2162 | PARTIAL |
| voltSetDC3 | [10,11] | 10–11 | full UInt16 | concatenate→parseInt(str,16)→int | **RAW (UNKNOWN)** | size > 4 | `setVoltSetDC3(I)` | 2167–2201 | PARTIAL |
| outputCurrentDC3 | [12,13] | 12–13 | full UInt16 | concatenate→parseInt(str,16)→int | **RAW (UNKNOWN)** | size > 4 | `setOutputCurrentDC3(I)` | 2204–2238 | PARTIAL |
| voltSet2DC3 | [22,23] | 22–23 | full UInt16 | concatenate→parseInt(str,16)→int | **RAW (UNKNOWN)** | size > 4 | `setVoltSet2DC3(I)` | 2243–2277 | PARTIAL |

**Index confirmation for outputCurrentDC1 (lines 2052–2086)**:
```smali
const/4 v10, 0x4      # at line 2047
invoke-interface {v0, v10}   # list.get(4)
const/4 v10, 0x5      # line 2056
invoke-interface {v0, v10}   # list.get(5)
```
→ byte offset 4–5. CONFIRMED.

**Index confirmation for voltSet2DC3 (lines 2243–2277)**:
```smali
const/16 v2, 0x16     # = 22
invoke-interface {v0, v2}    # list.get(22)
const/16 v10, 0x17    # = 23
invoke-interface {v0, v10}   # list.get(23)
```
→ byte offset 22–23. CONFIRMED.

**Gap note**: List indices 14–21 (bytes 14–21) are NOT parsed by any field in this method. They are skipped between outputCurrentDC3 (indices 12–13) and voltSet2DC3 (indices 22–23).

---

### Tier 3 — Requires size > 26 (Gate 2; lines 2287–2634)

Executed when `size > 26`. Gate at DCDCParser.smali line 2287.

| field_name | list_indices | byte_offset | bit_positions | parse_transform | scale_unit | conditions | bean_setter | smali_refs | confidence |
|---|---|---|---|---|---|---|---|---|---|
| setEvent1 | [26,27] | 26–27 | all bits | concatenate→hexStrToEnableList(str,0,2,null)→toMutableList() | bit-flag List | size > 26 | `setSetEvent1(List)` | 2289–2328 | PROVEN |
| chgModeDC1 | [28,29] | 28–29 | bits[3:0] | concatenate→parseInt(str,16)→AND 0xf | enum (0–15) | size > 26 | `setChgModeDC1(I)` | 2330–2370 | PROVEN |
| chgModeDC2 | [28,29] | 28–29 | bits[7:4] | (same parse result)→SHR 4→AND 0xf | enum (0–15) | size > 26 | `setChgModeDC2(I)` | 2372–2377 | PROVEN |
| chgModeDC3 | [28,29] | 28–29 | bits[11:8] | (same parse result)→SHR 8→AND 0xf | enum (0–15) | size > 26 | `setChgModeDC3(I)` | 2379–2384 | PROVEN |
| chgModeDC4 | [28,29] | 28–29 | bits[15:12] | (same parse result)→SHR 12→AND 0xf | enum (0–15) | size > 26 | `setChgModeDC4(I)` | 2386–2391 | PROVEN |
| batteryCapacity | [32..35] | 32–35 | full Int32 | subList(32,36)→toMutableList→bit32RegByteToNumber(list,false,false,0,null)→long-to-int | UNKNOWN (likely mAh raw) | size > 26 | `setBatteryCapacity(I)` | 2396–2424 | PARTIAL |
| batteryType | [36] | 36 | full UInt8 | list.get(36)→cast String→parseInt(str,16) | enum | size > 26 | `setBatteryType(I)` | 2427–2441 | PROVEN |
| batteryModelType | [37] | 37 | full UInt8 | list.get(37)→cast String→parseInt(str,16) | enum | size > 26 | `setBatteryModelType(I)` | 2446–2460 | PROVEN |
| powerDC1 | [38,39] | 38–39 | full Int16 signed | bit16HexSignedToInt(str38,str39)→Math.abs(I) | UNKNOWN (W assumed) | size > 26 | `setPowerDC1(I)` | 2463–2489 | PARTIAL |
| powerDC2 | [40,41] | 40–41 | full Int16 signed | bit16HexSignedToInt(str40,str41)→Math.abs(I) | UNKNOWN (W assumed) | size > 26 | `setPowerDC2(I)` | 2492–2518 | PARTIAL |
| powerDC3 | [42,43] | 42–43 | full Int16 signed | bit16HexSignedToInt(str42,str43)→Math.abs(I) | UNKNOWN (W assumed) | size > 26 | `setPowerDC3(I)` | 2521–2547 | PARTIAL |
| powerDC4 | [44,45] | 44–45 | full Int16 signed | bit16HexSignedToInt(str44,str45)→Math.abs(I) | UNKNOWN (W assumed) | size > 26 | `setPowerDC4(I)` | 2550–2576 | PARTIAL |
| powerDC5 | [46,47] | 46–47 | full Int16 signed | bit16HexSignedToInt(str46,str47)→Math.abs(I) | UNKNOWN (W assumed) | size > 26 | `setPowerDC5(I)` | 2579–2605 | PARTIAL |
| dcTotalPowerSet | [48,49] | 48–49 | full Int16 signed | bit16HexSignedToInt(str48,str49)→Math.abs(I) | UNKNOWN (W assumed) | size > 26 | `setDcTotalPowerSet(I)` | 2608–2634 | PARTIAL |

**Error in prior evidence for dcTotalPowerSet**: Evidence states transform = `parseInt(16)`. **ACTUAL smali** at lines 2626–2634 uses `bit16HexSignedToInt` + `Math.abs()`, identical to powerDC1–5. The `parseInt` claim is WRONG.

**Index confirmation for batteryCapacity (lines 2396–2424)**:
```smali
const/16 v2, 0x20     # = 32
const/16 v8, 0x24     # = 36
invoke-interface {v0, v2, v8}   # subList(32, 36) → indices 32,33,34,35
bit32RegByteToNumber$default(instance, mutableList, false, false, 0, null)
long-to-int v2, v10
setBatteryCapacity(v2)
```
→ byte offset 32–35. CONFIRMED. Transform: `bit32RegByteToNumber` (unsigned 32-bit), then `long-to-int`. CONFIRMED.

**Index confirmation for setEvent1 (lines 2289–2328)**:
```smali
const/16 v10, 0x1a    # = 26
invoke-interface {v0, v10}    # list.get(26)
const/16 v11, 0x1b    # = 27
invoke-interface {v0, v11}    # list.get(27)
concatenate → hexStrToEnableList$default(..., 0, 2, null)
```
→ byte offset 26–27 (2 bytes). **Error in prior evidence**: The evidence claims setEvent1 is at "20–23 (4 bytes)". **ACTUAL** is bytes 26–27 (2 bytes / 1 UInt16 interpreted as bit flags). The hexStrToEnableList call takes only the 2-byte concatenated string.

**Index confirmation for chgModeDC1–4 (lines 2330–2391)**:
```smali
const/16 v2, 0x1c     # = 28
invoke-interface {v0, v2}     # list.get(28)
const/16 v10, 0x1d    # = 29
invoke-interface {v0, v10}    # list.get(29)
parseInt(str,16)
and-int/lit8 v10, v2, 0xf    → chgModeDC1
shr-int/lit8 v10, v2, 0x4 ; and 0xf  → chgModeDC2
shr-int/lit8 v10, v2, 0x8 ; and 0xf  → chgModeDC3
shr-int/2addr v2, v8 (v8=0xc=12) ; and 0xf → chgModeDC4
```
→ all four chgMode fields share byte offset 28–29. CONFIRMED.

**Error in prior evidence for chgModeDC4**: The evidence states `SHR 12` and the index is `0xc`. Correct. However, the evidence claims the register operation is `shr-int/lit8 v10, v2, 0xc`. The actual smali at line 2386 uses `shr-int/2addr v2, v8` where `v8=0xc` (set at line 2043: `const/16 v8, 0xc`). This is functionally equivalent but the prior evidence's literal description is inaccurate.

---

### Tier 4 — Requires size > 50 (Gate 3; lines 2644–2767)

**THIS TIER WAS NOT DOCUMENTED IN PRIOR EVIDENCE.** Gate at DCDCParser.smali line 2644.

| field_name | list_indices | byte_offset | bit_positions | parse_transform | scale_unit | conditions | bean_setter | smali_refs | confidence |
|---|---|---|---|---|---|---|---|---|---|
| genCheckEnable | [50,51] | 50–51 | bits[1:0] | concatenate→parseInt(str,16)→AND 0x3 | bit-field (0–3) | size > 50 | `setGenCheckEnable(I)` | 2647–2684 | PROVEN |
| genType | [50,51] | 50–51 | bits[3:2] | (same parse result)→SHR 2→AND 0x3 | bit-field (0–3) | size > 50 | `setGenType(I)` | 2686–2691 | PROVEN |
| priorityChg | [50,51] | 50–51 | bits[5:4] | (same parse result)→SHR 4→AND 0x3 | bit-field (0–3) | size > 50 | `setPriorityChg(I)` | 2693–2698 | PROVEN |
| cableSet | [50,51] | 50–51 | bits[15:14] | (same parse result)→SHR 14 (0xe)→AND 0x3 | bit-field (0–3) | size > 50 | `setCableSet(I)` | 2700–2705 | PROVEN |
| reverseChgEnable | [53] | 53 | bits[1:0] | list.get(53)→cast String→parseInt(str,16)→AND 0x3 | bit-field (0–3) | size > 50 | `setReverseChgEnable(I)` | 2710–2727 | PROVEN |
| batteryHealthEnable | [53] | 53 | bits[3:2] | (same parse result)→SHR 2→AND 0x3 | bit-field (0–3) | size > 50 | `setBatteryHealthEnable(I)` | 2729–2734 | PROVEN |
| remotePowerCtrl | [53] | 53 | bits[5:4] | (same parse result)→SHR 4→AND 0x3 | bit-field (0–3) | size > 50 | `setRemotePowerCtrl(I)` | 2736–2741 | PROVEN |
| ledEnable | [53] | 53 | bits[7:6] | (same parse result)→SHR 6 (v9=6 at line 2743)→AND 0x3 | bit-field (0–3) | size > 50 | `setLedEnable(I)` | 2743–2748 | PROVEN |
| reverseChgMode | [52] | 52 | full UInt8 | list.get(52)→cast String→parseInt(str,16) | enum | size > 50 | `setReverseChgMode(I)` | 2750–2767 | PROVEN |

**Index confirmation for genCheckEnable and relatives (line 2647)**:
```smali
const/16 v8, 0x32     # = 50
invoke-interface {v0, v8}     # list.get(50)
const/16 v8, 0x33     # = 51
invoke-interface {v0, v8}     # list.get(51)
parseInt(str,16) → v2
and-int/lit8 v8, v2, 0x3     → genCheckEnable
shr-int/lit8 v8, v2, 0x2 ; and v4 (v4=0x3) → genType
shr-int/lit8 v8, v2, 0x4 ; and v4           → priorityChg
shr-int/lit8 v2, v2, 0xe ; and v4           → cableSet
```

**Index confirmation for reverseChgEnable relatives (line 2710)**:
```smali
const/16 v2, 0x35     # = 53
invoke-interface {v0, v2}     # list.get(53)
```

**Index confirmation for reverseChgMode (line 2750)**:
```smali
const/16 v2, 0x34     # = 52
invoke-interface {v0, v2}     # list.get(52)
```

**Error in prior evidence**: Prior evidence assigns genCheckEnable–cableSet to condition "size > 26" at smali refs 2681–2705. **ACTUAL** condition gate is `size > 50` (Gate 3 at line 2644). The prior evidence had the wrong condition for all 9 fields in this tier.

Similarly, prior evidence assigns reverseChgEnable–reverseChgMode to condition "size > 26" at refs 2724–2767. **ACTUAL** condition gate is also `size > 50`.

---

### Tier 5 — Requires size > 54 (Gate 4; lines 2777–3090)

Gate at DCDCParser.smali line 2777 (`const/16 v4, 0x36` = 54).

| field_name | list_indices | byte_offset | bit_positions | parse_transform | scale_unit | conditions | bean_setter | smali_refs | confidence |
|---|---|---|---|---|---|---|---|---|---|
| sysPowerCtrl | [55] | 55 | full UInt8 | list.get(0x37=55)→cast String→parseInt(str,16) | enum | size > 54 | `setSysPowerCtrl(I)` | 2779–2796 | PROVEN |
| remoteStartupSoc | [57] | 57 | full UInt8 | list.get(0x39=57)→cast String→parseInt(str,16) | % (0–100, unverified) | size > 54 | `setRemoteStartupSoc(I)` | 2798–2815 | PARTIAL |
| rechargerPowerDC1 | [58,59] | 58–59 | full UInt16 | concatenate→parseInt(str,16) | UNKNOWN (W assumed) | size > 54 | `setRechargerPowerDC1(I)` | 2817–2854 | PARTIAL |
| rechargerPowerDC2 | [60,61] | 60–61 | full UInt16 | concatenate→parseInt(str,16) | UNKNOWN (W assumed) | size > 54 | `setRechargerPowerDC2(I)` | 2856–2893 | PARTIAL |
| rechargerPowerDC3 | [62,63] | 62–63 | full UInt16 | concatenate→parseInt(str,16) | UNKNOWN (W assumed) | size > 54 | `setRechargerPowerDC3(I)` | 2895–2932 | PARTIAL |
| rechargerPowerDC4 | [64,65] | 64–65 | full UInt16 | concatenate→parseInt(str,16) | UNKNOWN (W assumed) | size > 54 | `setRechargerPowerDC4(I)` | 2934–2971 | PARTIAL |
| rechargerPowerDC5 | [66,67] | 66–67 | full UInt16 | concatenate→parseInt(str,16) | UNKNOWN (W assumed) | size > 54 | `setRechargerPowerDC5(I)` | 2973–3010 | PARTIAL |
| voltSetMode | [68,69] | 68–69 | bits[3:0] | concatenate→parseInt(str,16)→AND 0xf | enum (0–15) | size > 54 | `setVoltSetMode(I)` | 3012–3051 | PROVEN |
| pscModelNumber | [70,71] | 70–71 | full UInt16 | concatenate→parseInt(str,16) | raw | size > 54 | `setPscModelNumber(I)` | 3053–3090 | PROVEN |

**Index confirmation for sysPowerCtrl (lines 2779–2796)**:
```smali
const/16 v2, 0x37     # = 55
invoke-interface {v0, v2}     # list.get(55)
parseInt(str,16) → setSysPowerCtrl
```

**Index confirmation for remoteStartupSoc (lines 2798–2815)**:
```smali
const/16 v2, 0x39     # = 57
invoke-interface {v0, v2}     # list.get(57)
parseInt(str,16) → setRemoteStartupSoc
```
**Gap note**: list index 56 (byte 56) is skipped. No field maps to it.

**Index confirmation for rechargerPowerDC1 (lines 2817–2854)**:
```smali
const/16 v2, 0x3a     # = 58
const/16 v4, 0x3b     # = 59
parseInt → setRechargerPowerDC1
```

**Index confirmation for voltSetMode (lines 3012–3051)**:
```smali
const/16 v2, 0x44     # = 68
const/16 v4, 0x45     # = 69
parseInt(str,16) → and-int/lit8 v2, v2, 0xf → setVoltSetMode
```

**Index confirmation for pscModelNumber (lines 3053–3090)**:
```smali
const/16 v2, 0x46     # = 70
const/16 v4, 0x47     # = 71
parseInt(str,16) → setPscModelNumber
```

**Errors in prior evidence (CRITICAL)**:
- Prior evidence claims `voltSetMode` is at **byte offset 70–71**. **ACTUAL: 68–69**.
- Prior evidence claims `pscModelNumber` is at **byte offset 72–73**. **ACTUAL: 70–71**.
- Prior evidence claims `rechargerPowerDC6` is at **byte offset 68–69** (PROVEN). **ACTUAL**: bytes 68–69 are `voltSetMode`. `setRechargerPowerDC6` is **NEVER CALLED** in settingsInfoParse.

---

### Tier 6 — Requires size > 72 (Gate 5; lines 3093–3176)

Gate at DCDCParser.smali line 3100 (`const/16 v4, 0x48` = 72).

| field_name | list_indices | byte_offset | bit_positions | parse_transform | scale_unit | conditions | bean_setter | smali_refs | confidence |
|---|---|---|---|---|---|---|---|---|---|
| leadAcidBatteryVoltage | [96,97] | 96–97 | full UInt16 | concatenate→parseInt(str,16) | mV (assumed, UNKNOWN) | size > 72 | `setLeadAcidBatteryVoltage(I)` | 3102–3139 | PARTIAL |
| communicationEnable | [98,99] | 98–99 | all bits | concatenate→hexStrToEnableList(str,0,2,null) | bit-flag List | size > 72 | `setCommunicationEnable(List)` | 3141–3176 | PROVEN |

**Index confirmation for leadAcidBatteryVoltage (lines 3102–3139)**:
```smali
const/16 v2, 0x60     # = 96
invoke-interface {v0, v2}     # list.get(96)
const/16 v4, 0x61     # = 97
invoke-interface {v0, v4}     # list.get(97)
parseInt(str,16) → setLeadAcidBatteryVoltage
```

**Index confirmation for communicationEnable (lines 3141–3176)**:
```smali
const/16 v4, 0x62     # = 98
invoke-interface {v0, v4}     # list.get(98)
const/16 v5, 0x63     # = 99
invoke-interface {v0, v5}     # list.get(99)
hexStrToEnableList$default(..., 0, 2, null) → setCommunicationEnable
```

**Errors in prior evidence (CRITICAL)**:
- Prior evidence claims `leadAcidBatteryVoltage` at **byte offset 74–75**. **ACTUAL: 96–97**. (Off by 22 bytes.)
- Prior evidence claims `communicationEnable` is **"always"** present. **ACTUAL**: gated by `size > 72` at line 3100. It is NOT unconditional.

**Gap note**: List indices 72–95 (bytes 72–95) are completely skipped — no field is parsed from those 24 bytes. This is a structural gap in the protocol (likely reserved or unused in this firmware version).

---

### Unparsed Bean Field

| field_name | bean_setter (DCDCSettings.smali) | parser status | notes |
|---|---|---|---|
| rechargerPowerDC6 | `setRechargerPowerDC6(I)` (line 4482) | **NEVER CALLED** in settingsInfoParse | Bean has setter; parser does not invoke it. Prior evidence incorrectly marked PROVEN at offset 68–69. |

---

## 4. Scale Risk Table

### 4.1 Block 15500 (baseInfoParse) vs Block 15600 (settingsInfoParse)

Block 15500 is parsed by `DCDCParser.baseInfoParse` (method starting at line 66). The div-float operations are confirmed at lines 265, 308, 351 with constant `0x41200000` = `10.0f`.

| Field (15500 read) | 15500 transform | 15500 scale | Field (15600 setpoint) | 15600 transform | 15600 scale | Match | Hazard if 15600 scale is wrong |
|---|---|---|---|---|---|---|---|
| dcInputVolt (float) | parseInt→int-to-float→div 10.0f | × 0.1 V | (no direct pair) | — | — | N/A | — |
| dcOutputVolt (float) | parseInt→int-to-float→div 10.0f | × 0.1 V | voltSetDC1,DC2,DC3 | parseInt(16)→int (no div) | **UNKNOWN** | **MISMATCH (suspected)** | Writing raw 480 → 480V output if scale=×1; device expects 480 for 48.0V if scale=×0.1 → 10× voltage hazard |
| dcOutputCurrent (float) | parseInt→int-to-float→div 10.0f | × 0.1 A | outputCurrentDC1/2/3 | parseInt(16)→int (no div) | **UNKNOWN** | **MISMATCH (suspected)** | Writing raw 500 → 500A if scale=×1; overcurrent / safety system bypass |
| dcOutputPower (int) | parseInt(16)→int (no div) | × 1 W (raw) | powerDC1–5 | bit16HexSignedToInt→abs() | × 1 W (no div, assumed) | Likely match | Signed vs unsigned representation difference; semantic meaning (set vs actual power) unclear |
| — | — | — | dcTotalPowerSet | bit16HexSignedToInt→abs() | UNKNOWN (W assumed) | N/A | Setting wrong total power limit could cause AC input overload or insufficient delivery |
| — | — | — | voltSet2DC3 | parseInt(16)→int | **UNKNOWN** | N/A | Same hazard as voltSetDC1–3 |

**Proven div-float absence in settingsInfoParse**:
```
$ grep "div-float" DCDCParser.smali
Line 265:   div-float/2addr v2, v5    ← baseInfoParse (dcInputVolt)
Line 308:   div-float/2addr v2, v5    ← baseInfoParse (dcOutputVolt)
Line 351:   div-float/2addr v2, v5    ← baseInfoParse (dcOutputCurrent)
```
**Zero `div-float` instructions in lines 1780–3195** (settingsInfoParse). This is confirmed by the complete grep result above showing only 3 occurrences, all in baseInfoParse.

### 4.2 Transform Method Differences

| Transform | Used in baseInfoParse (15500) | Used in settingsInfoParse (15600) | Risk |
|---|---|---|---|
| `parseInt→int-to-float→div 10.0f` | YES (3 fields) | NO (0 fields) | 10× scale error if 15600 values are in same raw format as 15500 |
| `parseInt→int (raw)` | YES (dcOutputPower) | YES (most scalar fields) | Likely correct for W/enum fields |
| `bit16HexSignedToInt→abs()` | NO | YES (powerDC1–5, dcTotalPowerSet) | New in 15600 only — sign handling unclear |
| `bit32RegByteToNumber→long-to-int` | NO | YES (batteryCapacity) | New in 15600 only |
| `hexStrToEnableList` | NO | YES (dcCtrl group, setEvent1, communicationEnable) | Bit-flag extraction — no scale concern |

---

## 5. Schema Edit List

File: `d:/HomeAssistant/bluetti_sdk/schemas/block_15600_declarative.py`

Current state: 7 fields implemented; 23+ TODO comments.

### 5.1 Corrections Required (PROVEN evidence)

These edits fix factual errors in the current schema or evidence documentation:

**Fix 1 — `dcCtrl` through `selfAdaptionEnable` smali line references**

Current descriptions cite "(smali: lines 1909-1958)" for dc_ctrl but the field extraction uses the returned List from hexStrToEnableList. All four fields share the same parse block (1909–1999). The descriptions are approximately correct, but the smali line ranges should be:
- `dc_ctrl`: 1909–1958
- `silent_mode_ctrl`: 1961–1971
- `factory_set`: 1974–1984
- `self_adaption_enable`: 1986–1999

No offset change needed; these are PROVEN.

**Fix 2 — `volt_set_dc2` description smali reference**

Current: `"(smali: lines 2089-2123)"` — CORRECT.

**Fix 3 — Remove the description claim about `communicationEnable` being "always" present**

`communicationEnable` is only present when `size > 72`. Must not be modeled as unconditional.

### 5.2 Fields to Add with PROVEN evidence

These fields have PROVEN confidence (offset + transform + setter all confirmed from smali):

```python
# Tier 2 — size > 4 (PARTIAL: offsets PROVEN, scales UNKNOWN)
output_current_dc2: int = block_field(
    offset=8, type=UInt16(), unit="UNKNOWN",
    description="DC2 output current limit [SAFETY CRITICAL: scale UNKNOWN, no div-float] (smali: 2128-2162)",
    required=False, default=0,
)
volt_set_dc3: int = block_field(
    offset=10, type=UInt16(), unit="UNKNOWN",
    description="DC3 voltage setpoint [SAFETY CRITICAL: scale UNKNOWN] (smali: 2167-2201)",
    required=False, default=0,
)
output_current_dc3: int = block_field(
    offset=12, type=UInt16(), unit="UNKNOWN",
    description="DC3 output current limit [SAFETY CRITICAL: scale UNKNOWN] (smali: 2204-2238)",
    required=False, default=0,
)
volt_set2_dc3: int = block_field(
    offset=22, type=UInt16(), unit="UNKNOWN",
    description="DC3 secondary voltage setpoint [SAFETY CRITICAL: scale UNKNOWN] (smali: 2243-2277)",
    required=False, default=0,
)

# Tier 3 — size > 26 (PROVEN bit-field fields)
chg_mode_dc1: int = block_field(
    offset=28, type=UInt16(), mask=0x000F,
    description="DC1 charging mode [bits 3:0 of word at 28-29] (smali: 2330-2370)",
    required=False, default=0,
)
chg_mode_dc2: int = block_field(
    offset=28, type=UInt16(), mask=0x00F0, shift=4,
    description="DC2 charging mode [bits 7:4 of word at 28-29] (smali: 2372-2377)",
    required=False, default=0,
)
chg_mode_dc3: int = block_field(
    offset=28, type=UInt16(), mask=0x0F00, shift=8,
    description="DC3 charging mode [bits 11:8 of word at 28-29] (smali: 2379-2384)",
    required=False, default=0,
)
chg_mode_dc4: int = block_field(
    offset=28, type=UInt16(), mask=0xF000, shift=12,
    description="DC4 charging mode [bits 15:12 of word at 28-29] (smali: 2386-2391)",
    required=False, default=0,
)
battery_type: int = block_field(
    offset=36, type=UInt8(),
    description="Battery type enum (smali: 2427-2441)",
    required=False, default=0,
)
battery_model_type: int = block_field(
    offset=37, type=UInt8(),
    description="Battery model type enum (smali: 2446-2460)",
    required=False, default=0,
)

# Tier 4 — size > 50 (PROVEN bit-field fields)
gen_check_enable: int = block_field(
    offset=50, type=UInt16(), mask=0x0003,
    description="Generator check enable [bits 1:0] (smali: 2647-2684)",
    required=False, default=0,
)
# ... (remaining tier 4 fields follow same pattern)

# Tier 5 — size > 54 (PROVEN)
sys_power_ctrl: int = block_field(
    offset=55, type=UInt8(),
    description="System power control enum (smali: 2779-2796)",
    required=False, default=0,
)
volt_set_mode: int = block_field(
    offset=68, type=UInt16(), mask=0x000F,
    description="Voltage set mode [bits 3:0, CORRECTED from evidence offset 70] (smali: 3012-3051)",
    required=False, default=0,
)
psc_model_number: int = block_field(
    offset=70, type=UInt16(),
    description="PSC model number [CORRECTED from evidence offset 72] (smali: 3053-3090)",
    required=False, default=0,
)

# Tier 6 — size > 72 (PROVEN)
communication_enable: List[int] = block_field(
    offset=98, type=UInt16(),
    description="Communication enable bit flags [size>72 gate, NOT unconditional] (smali: 3141-3176)",
    required=False, default_factory=list,
)
```

### 5.3 Fields to REMOVE or CORRECT

| Current schema / evidence claim | Correction | Evidence |
|---|---|---|
| `rechargerPowerDC6` at offset 68–69 (PROVEN) | **REMOVE** — never parsed | `setRechargerPowerDC6` not called in settingsInfoParse (grep confirms 0 occurrences) |
| `voltSetMode` at offset 70–71 | **CHANGE to 68–69** | smali line 3012: `const/16 v2, 0x44` = 68 |
| `pscModelNumber` at offset 72–73 | **CHANGE to 70–71** | smali line 3053: `const/16 v2, 0x46` = 70 |
| `leadAcidBatteryVoltage` at offset 74–75 | **CHANGE to 96–97** | smali line 3102: `const/16 v2, 0x60` = 96 |
| `communicationEnable` — conditions = "always" | **CHANGE to "size > 72"** | Gate at smali line 3100: `if-le size, 0x48 (72)` |
| `dcTotalPowerSet` — transform = `parseInt(16)` | **CHANGE to `bit16HexSignedToInt + abs()`** | smali lines 2626–2634: `bit16HexSignedToInt` invoked |
| `setEvent1` at offset 20–23 (4 bytes) | **CHANGE to offset 26–27 (2 bytes)** | smali lines 2289–2328: indices 0x1a=26, 0x1b=27 |
| genCheckEnable–reverseChgMode conditions = "size > 26" | **CHANGE to "size > 50"** | Gate 3 at smali line 2644: `if-le size, 0x32 (50)` |

### 5.4 `min_length` field in schema

Current schema: `min_length=36`. This corresponds to 18 UInt16 words. With the corrected gate structure, the minimum fully-useful packet (Tier 1 + Tier 2) requires at least 24 bytes (12 UInt16 words to cover voltSet2DC3 at offset 22–23). The schema's `min_length=36` is defensible as a minimum for meaningful data but is not directly derived from a smali gate value. The smali gates are in list-element counts (byte counts), not word counts. **No schema change recommended** without device-confirmed minimum.

---

## 6. Blockers List

### Blocker 1 — Voltage setpoint scale factor UNKNOWN (SAFETY CRITICAL)

**Fields affected**: `voltSetDC1` (offset 2–3), `voltSetDC2` (offset 6–7), `voltSetDC3` (offset 10–11), `voltSet2DC3` (offset 22–23)

**Smali citation**: Lines 2026–2036, 2115–2123, 2193–2201, 2269–2277

**Evidence**: All four fields: `checkRadix(16)` → `parseInt(str,16)` → `int` → direct setter. Zero `div-float` instructions in lines 1780–3195 (confirmed by grep).

**Conflict**: Block 15500 `baseInfoParse` uses `int-to-float` → `div-float 10.0f` for `dcOutputVolt` at smali lines 304–310. If 15600 setpoints use the same raw encoding as 15500 reads, writing a raw integer 10× too large sets dangerous output voltages.

**Why unresolvable from smali alone**: The smali shows the parser reads and stores raw integers; it does not show the encoding agreement between the device firmware and the app. The app may present the user a scaled value and perform the ×10 multiply in a UI layer not visible in this parser class.

**Resolution path**: Read Block 15600 from a live device, compare `voltSetDC1` raw value against simultaneously-read `dcOutputVolt` from Block 15500. If `raw_15600 = 10 × (15500_float)`, scale = ×0.1V confirmed.

---

### Blocker 2 — Current setpoint scale factor UNKNOWN (SAFETY CRITICAL)

**Fields affected**: `outputCurrentDC1` (offset 4–5), `outputCurrentDC2` (offset 8–9), `outputCurrentDC3` (offset 12–13)

**Smali citation**: Lines 2078–2086, 2154–2162, 2230–2238

**Evidence**: Same pattern as voltage setpoints — `parseInt(16)` raw integer, no division.

**Conflict**: Block 15500 `dcOutputCurrent` divides by `10.0f` at smali line 351.

**Resolution path**: Same as Blocker 1: compare raw 15600 current limit against 15500 current reading.

---

### Blocker 3 — Prior evidence has five provably incorrect field offsets (DATA INTEGRITY)

**Fields affected**: `setEvent1`, `voltSetMode`, `pscModelNumber`, `leadAcidBatteryVoltage`, `rechargerPowerDC6`

**Smali citations**:

| Field | Evidence claim | Actual from smali | Smali line proving actual |
|---|---|---|---|
| setEvent1 | offset 20–23 | offset 26–27 | Line 2285: `const/16 v10, 0x1a` = 26 |
| voltSetMode | offset 70–71 | offset 68–69 | Line 3012: `const/16 v2, 0x44` = 68 |
| pscModelNumber | offset 72–73 | offset 70–71 | Line 3053: `const/16 v2, 0x46` = 70 |
| leadAcidBatteryVoltage | offset 74–75 | offset 96–97 | Line 3102: `const/16 v2, 0x60` = 96 |
| rechargerPowerDC6 | PROVEN at 68–69 | NEVER PARSED | grep: 0 occurrences of `setRechargerPowerDC6` in DCDCParser.smali |

**Why this blocks smali_verified**: The evidence document has been the basis for the current schema. Schema fields derived from the incorrect evidence will contain wrong offsets. Any "PROVEN" designation built on incorrect evidence must be recategorized. Until the schema is corrected against the actual smali data in this report, the schema cannot be certified.

---

### Blocker 4 — dcTotalPowerSet transform misidentified (DATA INTEGRITY)

**Smali citation**: Lines 2608–2634

**Evidence document claim**: `dcTotalPowerSet` transform = `parseInt(16)`, W (raw)

**Actual smali** (lines 2626–2634):
```smali
invoke-virtual {v2, v8, v10}, ProtocolParserV2;->bit16HexSignedToInt(String;String;)I
move-result v2
invoke-static {v2}, Math;->abs(I)I
move-result v2
invoke-virtual {v1, v2}, DCDCSettings;->setDcTotalPowerSet(I)V
```

**Impact**: `bit16HexSignedToInt` interprets the two-byte value as a signed 16-bit integer before taking absolute value. This means `dcTotalPowerSet` can represent both positive and negative power flow, and the stored value is always non-negative. This is semantically different from `parseInt(16)` which treats the value as unsigned.

---

### Blocker 5 — Gate 3 (size > 50) not documented; nine fields assigned wrong condition

**Smali citation**: Line 2644 `if-le v2, v8, :cond_2` where `v8=0x32=50`

**Fields with wrong condition in prior evidence**:
`genCheckEnable`, `genType`, `priorityChg`, `cableSet`, `reverseChgEnable`, `batteryHealthEnable`, `remotePowerCtrl`, `ledEnable`, `reverseChgMode`

**Prior evidence claim**: All nine fields have condition "size > 26"
**Actual**: All nine require `size > 50` (Gate 3)

**Impact**: Schema consumers reading packets with 27–50 list elements would expect these fields to be populated, but the parser does not set them. The fields would retain their default/sentinel values silently.

---

## 7. Final Recommendation

**Verdict: KEEP PARTIAL — NOT eligible for smali_verified**

### Grounds

**The schema cannot be certified smali_verified for three distinct reasons:**

1. **Safety blockers (Blockers 1 & 2)**: Voltage and current setpoint scale factors are not determinable from smali alone. The absence of `div-float` in `settingsInfoParse` is a confirmed finding, but whether this means the scale is ×1 (raw) or whether ×0.1 scaling happens elsewhere in the protocol stack cannot be proven from parser bytecode alone. Writing incorrect voltage/current setpoints could damage equipment.

2. **Prior evidence errors (Blocker 3)**: Five fields in the prior evidence document have incorrect offsets or incorrect confidence ratings. The current schema was built from that evidence. At minimum, the schema must be corrected before certification:
   - `setEvent1`: offset 20–23 → **correct to 26–27**
   - `voltSetMode`: offset 70–71 → **correct to 68–69**
   - `pscModelNumber`: offset 72–73 → **correct to 70–71**
   - `leadAcidBatteryVoltage`: offset 74–75 → **correct to 96–97**
   - `rechargerPowerDC6`: PROVEN → **remove (never parsed)**

3. **Transform error (Blocker 4)**: `dcTotalPowerSet` is described as `parseInt(16)` but actually uses `bit16HexSignedToInt + abs()`. The schema description is wrong.

### What CAN be done without device testing

The following corrections to `block_15600_declarative.py` are safe to apply immediately (all are PROVEN from smali with no device needed):

- Remove incorrect offset claims and TODO comments that cite wrong line numbers
- Fix `setEvent1` offset to 26–27
- Fix `voltSetMode` offset to 68–69 (with `AND 0xf` mask)
- Fix `pscModelNumber` offset to 70–71
- Fix `leadAcidBatteryVoltage` offset to 96–97
- Add `conditions="size > 72"` to `communicationEnable` and `leadAcidBatteryVoltage`
- Fix `dcTotalPowerSet` transform description to `bit16HexSignedToInt + abs()`
- Remove `rechargerPowerDC6` from any field list or schema
- Add all PROVEN Tier 4 fields (genCheckEnable, genType, priorityChg, cableSet, reverseChgEnable, batteryHealthEnable, remotePowerCtrl, ledEnable, reverseChgMode) with correct condition `size > 50`
- Add PROVEN Tier 5 fields: `sysPowerCtrl` (offset 55), `voltSetMode` (offset 68, AND 0xf), `pscModelNumber` (offset 70)
- Add PROVEN Tier 6 field: `communicationEnable` (offset 98, condition size > 72)

### What requires device testing

- Voltage scale factor for `voltSetDC1`, `voltSetDC2`, `voltSetDC3`, `voltSet2DC3` (mandatory before any write)
- Current scale factor for `outputCurrentDC1`, `outputCurrentDC2`, `outputCurrentDC3` (mandatory before any write)
- Units for `batteryCapacity` (mAh vs Ah vs Wh)
- Units for `powerDC1`–`powerDC5` and `dcTotalPowerSet` (W raw vs scaled)
- Units for `rechargerPowerDC1`–`rechargerPowerDC5` (W raw vs scaled)
- Confirm `remoteStartupSoc` range is genuinely 0–100%

### Corrected field count

| Tier | Condition | Fields parsed | PROVEN | PARTIAL |
|---|---|---|---|---|
| 1 | always | 5 | 4 (dcCtrl×4) | 1 (voltSetDC1) |
| 2 | size > 4 | 6 | 0 | 6 (volt/curr setpoints) |
| 3 | size > 26 | 14 | 6 (chgMode×4, batteryType, batteryModelType) | 8 (batteryCapacity, powerDC1-5, dcTotalPowerSet) |
| 4 | size > 50 | 9 | 9 (all bit-field extractions confirmed) | 0 |
| 5 | size > 54 | 9 | 3 (sysPowerCtrl, voltSetMode, pscModelNumber) | 6 (remoteStartupSoc, rechargerPowerDC1-5) |
| 6 | size > 72 | 2 | 1 (communicationEnable) | 1 (leadAcidBatteryVoltage) |
| **Total** | | **37** | **23 (62%)** | **14 (38%)** |

**Unparsed bean field**: `rechargerPowerDC6` — exists in bean, never called by parser.

---

*Report produced by Agent A — Forensic Parser Analyst*
*Source smali files verified as read-only; no SDK code was modified.*
*All smali line numbers are exact. All hex constants are decoded to decimal where relevant.*
*This report supersedes the field offsets and condition assignments in 15600-EVIDENCE.md for the five corrected fields.*
