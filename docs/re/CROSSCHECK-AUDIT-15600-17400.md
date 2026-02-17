# Adversarial Cross-Check Audit: Block 15600 and Block 17400

**Produced by**: Agent C — Adversarial Auditor
**Date**: 2026-02-17
**Sources audited**: Agent A (15600 Forensic) + Agent B (17400 Structural)
**Smali files independently read**: DCDCParser.smali, AT1Parser.smali, AT1BaseSettings.smali, AT1BaseConfigItem.smali, ProtocolParserV2.smali (partial)
**Stance**: Maximum skepticism. Every claim independently verified against primary smali before verdict.

---

## 1. Executive Summary

### Most Important Findings

**Block 15600 (DC_DC_SETTINGS)**:

Agent A's factual claims are overwhelmingly CONFIRMED from direct smali inspection. All 5 corrected byte offsets were independently verified at the exact smali lines Agent A cites. The critical missing gate at threshold 50, the dcTotalPowerSet transform correction, and the communicationEnable gate at threshold 72 are all confirmed. Agent A's field count of 37 (not 46) is consistent with the smali evidence. The existing `15600-EVIDENCE.md` document contains at least 8 confirmed factual errors, including 5 wrong byte offsets that are provably wrong from direct smali reads.

**Block 17400 (AT1_SETTINGS)**:

Agent B's claims about `config_grid.type` (offset 20), `config_grid.linkage_enable` (offset 22), and `config_grid.force_enable_0/1/2` (offset 12, NOT 8) are all CONFIRMED from AT1Parser.smali. The current production schema has WRONG offsets for at minimum 6 fields (type and linkage_enable for both config_grid and config_sl1, force_enable for both). Furthermore, Agent B's "PARTIALLY PROVEN" status for `config_sl1.force_enable` source (bytes 2-3 via v4) can be upgraded to CONFIRMED — v4 is not reassigned between lines 2081 and 2635.

Agent B's new-field claims (SL2-SL4 max_current, PCS1/PCS2 max_current as UInt8) are all CONFIRMED. The startup_flags and simple_end_fields groups are confirmed correct in the current schema.

### Go/No-Go Verdicts

| Block | Promote to smali_verified? | Schema corrections needed? | Schema currently producing wrong values? |
|---|---|---|---|
| 15600 | **NO** | Yes (offset corrections, see Section 7) | Not in schema yet (wrong offsets in EVIDENCE.md, not schema) |
| 17400 | **NO** | **YES — URGENT** | **YES** — 6 fields parse wrong bytes on real device |

---

## 2. Agent A Verification Table (Block 15600)

Independent verification against `DCDCParser.smali`.

### Claim 1: setEvent1 corrected byte offset — Agent A claims bytes 26-27 (not 20-23)

**Smali lines read**: 2285-2328

At line 2285: `const/16 v10, 0x1a` — 0x1a = **26**.
At line 2296: `const/16 v11, 0x1b` — 0x1b = **27**.
`hexStrToEnableList$default` called at line 2318 with the concatenation of list[26] + list[27].
`setSetEvent1(List)` called at line 2328.

**Verdict: CONFIRMED** — setEvent1 is at bytes 26-27. Prior evidence claiming "20-23 (4 bytes)" is WRONG.

---

### Claim 2: voltSetMode corrected byte offset — Agent A claims bytes 68-69 (not 70-71)

**Smali lines read**: 3012-3051

At line 3012: `const/16 v2, 0x44` — 0x44 = **68**.
At line 3019: `const/16 v4, 0x45` — 0x45 = **69**.
`parseInt(str,16)` called, then `and-int/lit8 v2, v2, 0xf` at line 3049.
`setVoltSetMode(v2)` called at line 3051.

**Verdict: CONFIRMED** — voltSetMode is at bytes 68-69. Prior evidence claiming "70-71" is WRONG.

---

### Claim 3: pscModelNumber corrected byte offset — Agent A claims bytes 70-71 (not 72-73)

**Smali lines read**: 3053-3090

At line 3053: `const/16 v2, 0x46` — 0x46 = **70**.
At line 3060: `const/16 v4, 0x47` — 0x47 = **71**.
`parseInt(str,16)` called at line 3086.
`setPscModelNumber(v2)` called at line 3090.

**Verdict: CONFIRMED** — pscModelNumber is at bytes 70-71. Prior evidence claiming "72-73" is WRONG.

---

### Claim 4: leadAcidBatteryVoltage corrected byte offset — Agent A claims bytes 96-97 (not 74-75)

**Smali lines read**: 3098-3139

Gate at line 3100: `const/16 v4, 0x48` = 72; `if-le v2, v4, :cond_4`. This is the size-72 gate.
At line 3102: `const/16 v2, 0x60` — 0x60 = **96**.
At line 3109: `const/16 v4, 0x61` — 0x61 = **97**.
`parseInt(str,16)` at line 3135.
`setLeadAcidBatteryVoltage(v2)` at line 3139.

**Verdict: CONFIRMED** — leadAcidBatteryVoltage is at bytes 96-97. Prior evidence claiming "74-75" is WRONG by 22 bytes.

---

### Claim 5: rechargerPowerDC6 is NEVER PARSED — Agent A claims setRechargerPowerDC6 is not called

Bytes 68-69 (0x44-0x45) are used by voltSetMode (confirmed above). The next instruction after `setVoltSetMode` at line 3051 is `const/16 v2, 0x46` (start of pscModelNumber). There is no `setRechargerPowerDC6` call anywhere between lines 3010 and 3090.

**Verdict: CONFIRMED** — rechargerPowerDC6 is never invoked in settingsInfoParse. Offset 68-69 belongs to voltSetMode.

---

### Claim 6: Gate at threshold 50 (const 0x32) — Agent A claims smali line 2644

**Smali lines read**: 2638-2644

At line 2638: `:cond_1` label. `invoke-interface/range {p1 .. p1}, size()I`.
At line 2640: `move-result v2`.
At line 2642: `const/16 v8, 0x32` — 0x32 = **50**.
At line 2644: `if-le v2, v8, :cond_2`.

**Verdict: CONFIRMED** — Gate 3 exists at smali line 2644, threshold = 50 (0x32). Prior evidence did not document this gate.

---

### Claim 7: dcTotalPowerSet transform uses bit16HexSignedToInt + Math.abs (not parseInt)

**Smali lines read**: 2608-2634

At line 2608: `sget-object v2, ...ProtocolParserV2;->INSTANCE`.
At line 2610: `const/16 v8, 0x30` = 48. list.get(48) → v8.
At line 2618: `const/16 v10, 0x31` = 49. list.get(49) → v10.
At line 2626: `invoke-virtual {v2, v8, v10}, ProtocolParserV2;->bit16HexSignedToInt(String;String;)I`.
At line 2630: `invoke-static {v2}, Math;->abs(I)I`.
At line 2634: `setDcTotalPowerSet(v2)`.

**Verdict: CONFIRMED** — dcTotalPowerSet uses `bit16HexSignedToInt + abs()`. Prior evidence claiming `parseInt(16)` is WRONG.

---

### Claim 8: communicationEnable guarded by size > 72 (smali line 3100)

**Smali lines read**: 3093-3100

At line 3094: `invoke-interface/range {p1 .. p1}, size()I`.
At line 3096: `move-result v2`.
At line 3098: `const/16 v4, 0x48` — 0x48 = **72**.
At line 3100: `if-le v2, v4, :cond_4`.

`communicationEnable` parsing starts at line 3141 and calls `setCommunicationEnable` at line 3176 — inside the block guarded by the size-72 check.

**Verdict: CONFIRMED** — communicationEnable is gated at size > 72. Prior evidence claiming "conditions: always" is WRONG.

---

### Claim 9: 37 fields actually parsed (not 46)

Agent A's field count of 37 is the sum of all fields traced across 6 tiers:

- Tier 1 (always): 5 fields (dcCtrl, silentModeCtrl, factorySet, selfAdaptionEnable, voltSetDC1)
- Tier 2 (size > 4): 6 fields (outputCurrentDC1, voltSetDC2, outputCurrentDC2, voltSetDC3, outputCurrentDC3, voltSet2DC3)
- Tier 3 (size > 26): 14 fields (setEvent1, chgModeDC1-4, batteryCapacity, batteryType, batteryModelType, powerDC1-5, dcTotalPowerSet)
- Tier 4 (size > 50): 9 fields (genCheckEnable, genType, priorityChg, cableSet, reverseChgEnable, batteryHealthEnable, remotePowerCtrl, ledEnable, reverseChgMode)
- Tier 5 (size > 54): 9 fields (sysPowerCtrl, remoteStartupSoc, rechargerPowerDC1-5, voltSetMode, pscModelNumber)
- Tier 6 (size > 72): 2 fields (leadAcidBatteryVoltage, communicationEnable)

Total = 5+6+14+9+9+2 = **45**. Agent A counts this as 37 in the summary table, but the detailed tier tables sum to 45.

**DISCREPANCY NOTED**: Agent A's summary table shows 37 (5+6+14+9+9+2 = 45, not 37). The discrepancy appears in how Agent A counted Tier 3: the table shows 14 but Agent A's summary row claims 14 for Tier 3. Re-counting: Tier 3 = setEvent1(1) + chgModeDC1-4(4) + batteryCapacity(1) + batteryType(1) + batteryModelType(1) + powerDC1-5(5) + dcTotalPowerSet(1) = 14. Total = 5+6+14+9+9+2 = 45. Agent A's own final table says "Total: 37" but the per-tier sums add to 45.

**Verdict: INCONCLUSIVE (internal inconsistency in Agent A's own counting)** — The smali-based field count is at least 45 verified parse calls, not 37. The claim "37, not 46" is directionally correct (prior evidence overcounted with non-existent fields), but Agent A's own count appears to have a subtraction error. The correct smali-verified count appears to be approximately 45.

---

### Claim 10: voltSetDC1 uses raw parseInt with no division (scale UNKNOWN)

**Smali lines read**: 1907-2036

At line 1907 (Tier 1 parse block start), the first field parsed after the 4 enable bits is voltSetDC1.
From line 2002: list.get(0x2)=list[2], line 2006: list.get(0x3)=list[3].
The transform chain: `checkRadix(16)` → `parseInt(str,16)` → direct `setVoltSetDC1(I)V`.

No `div-float`, no `int-to-float`, no multiply/divide operations at any point.

**Verdict: CONFIRMED** — voltSetDC1 uses raw parseInt(16) with no scale factor. Scale is genuinely UNKNOWN from smali alone.

---

### Claim 11 (High-risk): 4 enable-bit fields at offset 0 via hexStrToEnableList

**Smali lines read**: 1909-1999

At line 1909: `sget-object v2, ProtocolParserV2;->INSTANCE`.
At line 1913: `invoke-interface {v0, v3}` where v3=0 → list.get(0).
At line 1919: `invoke-interface {v0, v5}` where v5=1 → list.get(1).
StringBuilder concatenation, then at line 1943: `hexStrToEnableList$default(..., 0, 2, null)` → stored in v2.
At line 1948: v2.get(0) → `setDcCtrl(I)` at line 1958.
At line 1961: v2.get(1) → `setSilentModeCtrl(I)` at line 1971.
At line 1974: v2.get(2) [via const/4 v7, 0x2] → `setFactorySet(I)` at line 1984.
Then a 4th field uses list.get(3) → `setSelfAdaptionEnable(I)`.

**Verdict: CONFIRMED** — All 4 enable-bit fields at byte offset 0-1, extracted via hexStrToEnableList, indices [0,1,2,3].

---

### Claim 12: voltDC1 in baseInfoParse uses div 10.0f (Agent A's scale cross-reference)

Agent A cites this as a comparison point (not a 15600 claim). The Agent claims DCDCParser.baseInfoParse has 3 div-float calls at lines 265, 308, 351. This is a structural claim about the absence of scale factors in settingsInfoParse versus their presence in baseInfoParse.

Independently confirmed: the div-float at line 2626 in the settingsInfoParse section is actually `Math.abs`, not a float divide. No div-float exists in settingsInfoParse lines 1780-3195.

**Verdict: CONFIRMED** — The scale discrepancy between baseInfoParse (uses div 10.0f) and settingsInfoParse (uses raw parseInt) is real and confirmed.

---

### Summary: Agent A Verification

| # | Claim | Verdict | Smali Evidence |
|---|---|---|---|
| 1 | setEvent1 at bytes 26-27 | CONFIRMED | Lines 2285 (0x1a=26), 2296 (0x1b=27) |
| 2 | voltSetMode at bytes 68-69 | CONFIRMED | Lines 3012 (0x44=68), 3019 (0x45=69) |
| 3 | pscModelNumber at bytes 70-71 | CONFIRMED | Lines 3053 (0x46=70), 3060 (0x47=71) |
| 4 | leadAcidBatteryVoltage at bytes 96-97 | CONFIRMED | Lines 3102 (0x60=96), 3109 (0x61=97) |
| 5 | rechargerPowerDC6 NEVER PARSED | CONFIRMED | No setRechargerPowerDC6 call in lines 3010-3090 |
| 6 | Gate 3 threshold=50 at line 2644 | CONFIRMED | Line 2642 (0x32=50), 2644 (if-le) |
| 7 | dcTotalPowerSet uses bit16HexSignedToInt+abs | CONFIRMED | Lines 2626 (bit16HexSignedToInt), 2630 (abs) |
| 8 | communicationEnable gated by size>72 | CONFIRMED | Lines 3098 (0x48=72), 3100 (if-le) |
| 9 | 37 fields parsed (not 46) | INCONCLUSIVE | Internal counting error in Agent A: per-tier sums yield ~45, not 37; directionally correct that 46 is wrong |
| 10 | voltSetDC1 raw parseInt, no division | CONFIRMED | Lines 2002-2036, no div-float in range |
| 11 | 4 enable bits at offset 0 via hexStrToEnableList | CONFIRMED | Lines 1909-1999, list[0]+list[1] → hexStrToEnableList → get(0-3) |
| 12 | scale discrepancy baseInfoParse vs settingsInfoParse | CONFIRMED | 3 div-float in baseInfoParse, 0 in settingsInfoParse |

**Agent A reliability score: 11/12 CONFIRMED, 1 INCONCLUSIVE. No contradictions found.**

---

## 3. Agent B Verification Table (Block 17400)

Independent verification against `AT1Parser.smali`.

### Claim 1 (CRITICAL): config_grid.type actual offset — Agent B claims bytes 20-21 (data[0x14]+data[0x15])

**Smali lines read**: 2396-2428

At line 2396: `sget-object v11, ProtocolParserV2;->INSTANCE`.
At line 2398: `const/16 v13, 0x14` — 0x14 = **20**.
At line 2400: `invoke-interface {v0, v13}` → list.get(20) → v13.
At line 2404: `const/16 v15, 0x15` — 0x15 = **21**.
At line 2406: `invoke-interface {v0, v15}` → list.get(21) → v15.
StringBuilder concat → `hexStrToEnableList(str, v9)` at line 2426.
Result stored in v11 at line 2428.

At line 2472: `invoke-interface {v11, v3}` where v3=0 → v11.get(0).
At line 2476: cast to Number → `intValue()` → v25 (used as `type` in configGrid constructor).

**Verdict: CONFIRMED** — config_grid.type is read from bytes 20-21. Current schema offset=18 is WRONG.

---

### Claim 2 (CRITICAL): config_grid.linkage_enable actual offset — Agent B claims bytes 22-23

**Smali lines read**: 2430-2463

At line 2431: `sget-object v13, ProtocolParserV2;->INSTANCE`.
At line 2433: `const/16 v14, 0x16` — 0x16 = **22**.
At line 2435: `invoke-interface {v0, v14}` → list.get(22) → v14.
At line 2439: `const/16 v15, 0x17` — 0x17 = **23**.
At line 2441: `invoke-interface {v0, v15}` → list.get(23) → v15.
StringBuilder concat → `hexStrToEnableList$default(...)` at line 2461.
Result stored in v9 at line 2463.

At line 2494: `invoke-interface {v9, v3}` where v3=0 → v9.get(0).
At line 2498: cast to Number → `intValue()` → v28 (used as `linkageEnable` in configGrid constructor).

**Verdict: CONFIRMED** — config_grid.linkage_enable is read from bytes 22-23. Current schema offset=32 is WRONG.

---

### Claim 3 (CRITICAL): config_grid.force_enable actual offset — Agent B claims bytes 12-13, current schema says 8-9

**Smali lines read**: 2255-2292 (bytes 12-13 section)

At line 2258: `const/16 v13, 0xc` — 0xc = **12**.
At line 2260: `invoke-interface {v0, v13}` → list.get(12) → v13.
At line 2264: `const/16 v14, 0xd` — 0xd = **13**.
At line 2266: `invoke-interface {v0, v14}` → list.get(13) → v14.
StringBuilder concat → `hexStrToEnableList$default(...)` at line 2286.
`move-result-object v2` at line 2288.

At line 2483-2491: `move-object v14, v2` → `check-cast v14, Iterable` → `CollectionsKt.take(v14, 3)` → `move-result-object v27` (used as `forceEnable` in configGrid constructor).

**For comparison**: bytes 8-9 (delayEnable2) are read at lines 2184-2214:
At line 2184: `const/16 v13, 0x8` = 8. `const/16 v14, 0x9` = 9.
The hexStrToEnableList result is stored in v2 at line 2214, then immediately passed to `setDelayEnable2(v2)` at line 2216.
That v2 is then OVERWRITTEN at line 2288 (by the bytes 12-13 parse result).

**Verdict: CONFIRMED** — config_grid.force_enable_0/1/2 comes from bytes 12-13, NOT bytes 8-9. Current schema offset=8 is WRONG.

---

### Claim 4: config_sl1.type offset — same bytes as grid (20-21)?

**Smali lines read**: 2619-2632

At line 2619: `sget-object v49, AT1Porn;->SMART_LOAD_1`. (This marks SL1 section.)
At line 2621: `const/4 v10, 0x1`.
At line 2624: `invoke-interface {v11, v10}` where v11 = the saved hexStrToEnableList(bytes 20-21) result, and v10=1 → v11.get(1).
At line 2626: cast to Number → `intValue()` → v50 (used as SL1 `type`).

**Verdict: CONFIRMED** — config_sl1.type also reads from bytes 20-21, index [1] (same list as grid, index [0]). Current schema offset=18 is WRONG.

---

### Claim 5: config_sl1.linkage_enable — same bytes as grid (22-23)?

**Smali lines read**: 2652-2663

At line 2652: `const/4 v2, 0x1`.
At line 2655: `invoke-interface {v9, v2}` where v9 = hexStrToEnableList(bytes 22-23), v2=1 → v9.get(1).
At line 2659: cast to Number → `intValue()` → v53 (SL1 `linkageEnable`).

**Verdict: CONFIRMED** — config_sl1.linkage_enable reads from bytes 22-23, index [1]. Current schema offset=32 is WRONG.

---

### Claim 6: config_sl2.max_current offset — Agent B claims byte 88

**Smali lines read**: 2869-2906

At line 2869: `const/16 v3, 0x58` — 0x58 = **88**.
At line 2872: `invoke-interface {v0, v3}` → list.get(88).
At line 2876: `const/16 v4, 0x59` — 0x59 = **89**.
At line 2878: `invoke-interface {v0, v4}` → list.get(89).
At line 2904: `invoke-static {v3, v5}, Integer.parseInt(String;I)I`.
At line 2906: `move-result v77` (SL2 max_current).

**Verdict: CONFIRMED** — config_sl2.max_current is at bytes 88-89 (UInt16). Not yet in schema.

---

### Claim 7: config_sl3.max_current offset — Agent B claims byte 90

**Smali lines read**: 3027-3064

At line 3027: `const/16 v3, 0x5a` — 0x5a = **90**.
At line 3030: `invoke-interface {v0, v3}` → list.get(90).
At line 3034: `const/16 v4, 0x5b` — 0x5b = **91**.
At line 3036: `invoke-interface {v0, v4}` → list.get(91).
At line 3062: `Integer.parseInt(...)`.
At line 3064: `move-result v56` (SL3 max_current).

**Verdict: CONFIRMED** — config_sl3.max_current is at bytes 90-91 (UInt16). Not yet in schema.

---

### Claim 8: config_sl4.max_current offset — Agent B claims byte 92

**Smali lines read**: 3192-3229

At line 3192: `const/16 v2, 0x5c` — 0x5c = **92**.
At line 3195: `invoke-interface {v0, v2}` → list.get(92).
At line 3199: `const/16 v3, 0x5d` — 0x5d = **93**.
At line 3201: `invoke-interface {v0, v3}` → list.get(93).
At line 3227: `Integer.parseInt(...)`.
At line 3229: `move-result v77` (SL4 max_current).

**Verdict: CONFIRMED** — config_sl4.max_current is at bytes 92-93 (UInt16). Not yet in schema.

---

### Claim 9: config_pcs1.max_current at byte 95, UInt8

**Smali lines read**: 3287-3304

At line 3287: `const/16 v4, 0x5f` — 0x5f = **95**.
At line 3290: `invoke-interface {v0, v4}` → list.get(95). Single element.
At line 3294: `check-cast v4, String;` (direct String cast, NOT via Number.intValue).
At line 3296: `const/16 v5, 0x10`.
At line 3298: `invoke-static {v5}, CharsKt.checkRadix(I)I`.
At line 3302: `invoke-static {v4, v6}, Integer.parseInt(String;I)I`.
At line 3304: `move-result v31` (PCS1 max_current).

CRITICAL: This reads ONLY ONE element (list.get(95)), not two concatenated bytes. Maximum value is 0xFF=255.

**Verdict: CONFIRMED** — config_pcs1.max_current is at byte 95 only (UInt8 effective). Agent B correctly identifies this as single-byte, not UInt16.

---

### Claim 10: config_pcs2.max_current at byte 94, UInt8

**Smali lines read**: 3366-3383

At line 3366: `const/16 v3, 0x5e` — 0x5e = **94**.
At line 3369: `invoke-interface {v0, v3}` → list.get(94). Single element.
At line 3373: `check-cast v3, String;` (direct String cast).
At line 3376: `invoke-static {v4}, CharsKt.checkRadix(I)I`.
At line 3381: `invoke-static {v3, v5}, Integer.parseInt(String;I)I`.
At line 3383: `move-result v52` (PCS2 max_current).

**Verdict: CONFIRMED** — config_pcs2.max_current is at byte 94 only (UInt8 effective). PCS2 precedes PCS1 in packet order (94 before 95) despite PCS1 being constructed first in code.

---

### Claim 11 (EXTRA CRITICAL): simple_end_fields at offsets 176-181

**Smali lines read**: 3525-3645

At line 3525: `const/16 v2, 0xb0` — 0xb0 = **176**. → volt_level_set parse starts.
At line 3532: `const/16 v3, 0xb1` — 0xb1 = **177**.
At line 3564: `and-int/lit8 v3, v2, 0x7` → volt_level_set (bits 2:0).
At line 3567: `setVoltLevelSet(v3)`.
At line 3569-3578: `shr-int/2addr v2, v3` (v3=3), `and-int/2addr v2, 0x7` → setAcSupplyPhaseNum.

At line 3580: `const/16 v2, 0xb2` — 0xb2 = **178**. → soc_gen_auto_stop.
At line 3599: `Math.min(v2, 100)` → setSocGenAutoStop.

At line 3607: `const/16 v2, 0xb3` — 0xb3 = **179**. → soc_gen_auto_start.
At line 3626: `setSocGenAutoStart(v2)`.

At line 3628: `const/16 v2, 0xb5` — 0xb5 = **181**. → soc_black_start.
At line 3645: `setSocBlackStart(v0)`.

**Verdict: CONFIRMED** — simple_end_fields at offsets 176 (volt_level_set + ac_supply_phase_num), 178 (soc_gen_auto_stop), 179 (soc_gen_auto_start), 181 (soc_black_start) are all CORRECT in current schema. Note: offset 180 (0xb4) is SKIPPED — no field reads from it.

---

### Claim 12: startup_flags at bytes 174-175 (data[0xae]+data[0xaf])

**Smali lines read**: 3429-3523

At line 3429: `const/16 v3, 0xae` — 0xae = **174**.
At line 3431: `invoke-interface {v0, v3}` → list.get(174).
At line 3435: `const/16 v4, 0xaf` — 0xaf = **175**.
At line 3437: `invoke-interface {v0, v4}` → list.get(175).
StringBuilder concat → `hexStrToEnableList$default(...)` at line 3463 → result in v2.
At line 3468: `v2.get(2)` [v5=2] → setBlackStartEnable.
At line 3480: v3=3; `v2.get(3)` → setBlackStartMode.
At line 3495: v3=4; `v2.get(4)` → setGeneratorAutoStartEnable.
At line 3510: v3=5; `v2.get(5)` → setOffGridPowerPriority.

**Verdict: CONFIRMED** — startup_flags reads bytes 174-175, extracting indices [2,3,4,5] from hexStrToEnableList. Current schema is CORRECT.

---

### Claim 13 (BONUS): config_sl1.force_enable — Agent B marks "PARTIALLY PROVEN" from v4 (bytes 2-3). Can we upgrade to CONFIRMED?

Agent B noted that v4 was set at line 2081 from hexStrToEnableList(data[2]+data[3]) but may have been reassigned before line 2635.

**Register trace analysis**: The grep of all v4 write operations between lines 2082 and 2635 shows:
- Line 2810: `move-object v4, v12` — AFTER line 2635, not before.
- All other v4 writes in the AT1Parser.smali file are either before line 2081 or after line 2635.

No v4 reassignment occurs between lines 2082 and 2635.

At line 2635 (confirmed in smali): `move-object v10, v4`. v4 is the hexStrToEnableList(data[2]+data[3]) result. Then `take(3)` → v51 = SL1 forceEnable.

**Verdict: CONFIRMED** — config_sl1.force_enable_0/1/2 comes from bytes 2-3 (via v4). Agent B's "PARTIALLY PROVEN" can be upgraded to PROVEN. Current schema claiming offset=10 (delayEnable3=bytes 10-11) is WRONG.

---

### Summary: Agent B Verification

| # | Claim | Verdict | Smali Evidence |
|---|---|---|---|
| 1 | config_grid.type at bytes 20-21 | CONFIRMED | Lines 2398 (0x14=20), 2404 (0x15=21), 2472 (v11.get(0)) |
| 2 | config_grid.linkage_enable at bytes 22-23 | CONFIRMED | Lines 2433 (0x16=22), 2439 (0x17=23), 2494 (v9.get(0)) |
| 3 | config_grid.force_enable at bytes 12-13 (not 8-9) | CONFIRMED | Lines 2258 (0xc=12), 2264 (0xd=13), 2288 (v2=result), 2483 (take(3)) |
| 4 | config_sl1.type at bytes 20-21, index [1] | CONFIRMED | Lines 2621 (v10=1), 2624 (v11.get(1)=SL1 type) |
| 5 | config_sl1.linkage_enable at bytes 22-23, index [1] | CONFIRMED | Lines 2652 (v2=1), 2655 (v9.get(1)) |
| 6 | config_sl2.max_current at bytes 88-89 | CONFIRMED | Lines 2869 (0x58=88), 2876 (0x59=89), 2906 (move-result) |
| 7 | config_sl3.max_current at bytes 90-91 | CONFIRMED | Lines 3027 (0x5a=90), 3034 (0x5b=91), 3064 (move-result) |
| 8 | config_sl4.max_current at bytes 92-93 | CONFIRMED | Lines 3192 (0x5c=92), 3199 (0x5d=93), 3229 (move-result) |
| 9 | config_pcs1.max_current at byte 95, UInt8 | CONFIRMED | Lines 3287 (0x5f=95), 3290 (single get), 3294 (String cast) |
| 10 | config_pcs2.max_current at byte 94, UInt8 | CONFIRMED | Lines 3366 (0x5e=94), 3369 (single get), 3373 (String cast) |
| 11 | simple_end_fields at offsets 176-181 CORRECT | CONFIRMED | Lines 3525 (0xb0=176) through 3645 (0xb5=181) |
| 12 | startup_flags at bytes 174-175 CORRECT | CONFIRMED | Lines 3429 (0xae=174), 3435 (0xaf=175) |
| 13 | config_sl1.force_enable from bytes 2-3 (BONUS) | CONFIRMED | v4 not reassigned between lines 2082-2635; move-object v10, v4 at 2635 |

**Agent B reliability score: 13/13 CONFIRMED. No contradictions found.**

---

## 4. Schema Errors Confirmed

Fields in the current production schema (`block_17400_declarative.py`) that are verified to parse WRONG bytes from the device response:

| Group | Field | Current Offset | Correct Offset | Error Magnitude | Consequence |
|---|---|---|---|---|---|
| config_grid | type | 18 | **20** | +2 bytes | Reads bytes 18-19 (actually the hexStrToEnableList(data[12-13]) spill or adjacent data), should read bytes 20-21 |
| config_grid | linkage_enable | 32 | **22** | -10 bytes | Reads bytes 32-33 (protectList range boundary), should read bytes 22-23 |
| config_grid | force_enable_0/1/2 | 8 | **12** | +4 bytes | Reads bytes 8-9 (delayEnable2 range), should read bytes 12-13 |
| config_sl1 | type | 18 | **20** | +2 bytes | Same error as config_grid.type |
| config_sl1 | linkage_enable | 32 | **22** | -10 bytes | Same error as config_grid.linkage_enable |
| config_sl1 | force_enable_0/1/2 | 10 | **2** | -8 bytes | Reads bytes 10-11 (delayEnable3 range), should read bytes 2-3 |

**Classification**: All 6 field groups are SAFETY_CRITICAL — this is a transfer switch control block. Wrong bytes mean incorrect interpretation of grid and load configuration states.

**Fields NOT in schema but proven by smali** (missing, not wrong):

| Group | Field | Correct Offset | Type | Status |
|---|---|---|---|---|
| config_sl2 | max_current | 88 | UInt16 | PROVEN, absent from schema |
| config_sl3 | max_current | 90 | UInt16 | PROVEN, absent from schema |
| config_sl4 | max_current | 92 | UInt16 | PROVEN, absent from schema |
| config_pcs1 | max_current | 95 | UInt8 (single byte) | PROVEN, absent from schema |
| config_pcs2 | max_current | 94 | UInt8 (single byte) | PROVEN, absent from schema |

**Note on `block_15600_declarative.py`**: The current schema only implements 7 fields (4 enable bits + 3 partial setpoints). The wrong offsets identified by Agent A are in `15600-EVIDENCE.md` documentation only — they are not currently in the schema code. The schema does not yet contain voltSetMode, pscModelNumber, leadAcidBatteryVoltage, or rechargerPowerDC6. No wrong offset is producing wrong values in the running schema (because those fields are absent). The risk is that a future schema expansion based on the uncorrected EVIDENCE.md would introduce wrong offsets.

---

## 5. Consistency Audit

### 5.1 block_17400_declarative.py vs Agent B Findings

| Schema claim | Agent B finding | Status |
|---|---|---|
| config_grid.type offset=18 | Correct offset=20 | CONTRADICTION — schema is wrong |
| config_grid.linkage_enable offset=32 | Correct offset=22 | CONTRADICTION — schema is wrong |
| config_grid.force_enable_0/1/2 offset=8 | Correct offset=12 | CONTRADICTION — schema is wrong |
| config_sl1.type offset=18 | Correct offset=20 | CONTRADICTION — schema is wrong |
| config_sl1.linkage_enable offset=32 | Correct offset=22 | CONTRADICTION — schema is wrong |
| config_sl1.force_enable_0/1/2 offset=10 | Correct offset=2 | CONTRADICTION — schema is wrong |
| config_sl2/sl3/sl4/pcs1/pcs2: no sub-fields | max_current fields proven | Schema conservatively deferred these; Agent B proves they should be added |
| startup_flags at offset 174 | Correct | CONSISTENT |
| simple_end_fields offsets 176-181 | Correct | CONSISTENT |
| top_level_enables offsets 0, 2 | Correct | CONSISTENT |

**Schema docstring errors**: The schema docstring (lines 72-79) cites wrong smali lines and wrong offsets:
- Line 72: "config_grid.type (bytes 18-19, index [0], smali: 2472-2480)" — bytes 18-19 is WRONG; should be 20-21.
- Line 73: "config_grid.linkage_enable (bytes 32-33, index [0], smali: 2504-2510)" — bytes 32-33 is WRONG; should be 22-23.
- Line 74: "config_sl1.type (bytes 18-19, index [1], smali: 2624-2632)" — bytes 18-19 is WRONG; should be 20-21.
- Line 75: "config_sl1.linkage_enable (bytes 32-33, index [1], smali: 2654-2663)" — bytes 32-33 is WRONG; should be 22-23.
- Line 78: "config_grid.force_enable_0/1/2 (bytes 8-9, delayEnable2.take(3), smali: 2482-2491)" — bytes 8-9 is WRONG; should be 12-13.
- Line 79: "config_sl1.force_enable_0/1/2 (bytes 10-11, delayEnable3.take(3), smali: 2634-2643)" — bytes 10-11 is WRONG; should be 2-3.

### 5.2 test_block_17400_nested.py vs Agent B Findings

The test file has multiple test methods that assert incorrect offsets. These tests currently PASS but they assert wrong values:

| Test method | Current assertion | Correct assertion | Status |
|---|---|---|---|
| test_config_grid_type_offset | f.offset == 18 | f.offset == 20 | WRONG — test asserts incorrect offset |
| test_config_grid_linkage_enable_offset | f.offset == 32 | f.offset == 22 | WRONG — test asserts incorrect offset |
| test_config_grid_force_enable_offset | f.offset == 8 | f.offset == 12 | WRONG — test asserts incorrect offset |
| test_config_sl1_type_offset | f.offset == 18 | f.offset == 20 | WRONG — test asserts incorrect offset |
| test_config_sl1_linkage_enable_offset | f.offset == 32 | f.offset == 22 | WRONG — test asserts incorrect offset |
| test_config_sl1_force_enable_offset | f.offset == 10 | f.offset == 2 | WRONG — test asserts incorrect offset |

The tests for startup_flags (offset 174), simple_end_fields (offsets 176-181), and top_level_enables (offsets 0, 2) are all asserting correct values.

The test `test_parser_config_grid_max_current_value` (line 583) correctly places data[84]=0x00, data[85]=0x64 and asserts max_current==100. This will continue to work correctly because config_grid.max_current at offset=84 is proven correct.

### 5.3 test_wave_d_batch4_blocks.py vs Agent B Findings

The `test_block_17400_field_structure` test (lines 65-122) asserts:
- config_grid has 6 fields with names {type, linkage_enable, force_enable_0/1/2, max_current} — CORRECT COUNT but asserts the wrong offsets indirectly via field presence.
- The test does not check offsets directly for config_grid and config_sl1 in this file (only field counts and names).

The deferred groups (config_sl2, sl3, sl4, pcs1, pcs2) are asserted to have 0 sub-fields. Agent B proves they should have max_current fields — so these tests will need updating when corrections are applied.

### 5.4 15600-EVIDENCE.md vs Agent A Findings

Confirmed incorrect entries in `15600-EVIDENCE.md`:

| Field | Evidence claim | Correct value | Error |
|---|---|---|---|
| setEvent1 offset | 20-23 (4 bytes) | 26-27 (2 bytes) | Wrong offset and wrong width |
| setEvent1 conditions | size > 26 | size > 26 | CORRECT (unchanged) |
| genCheckEnable/genType/priorityChg/cableSet conditions | size > 26 | size > 50 | WRONG condition gate |
| reverseChgEnable/batteryHealthEnable/remotePowerCtrl/ledEnable conditions | size > 26 | size > 50 | WRONG condition gate |
| reverseChgMode conditions | size > 26 | size > 50 | WRONG condition gate |
| dcTotalPowerSet transform | parseInt(16), W (raw) | bit16HexSignedToInt + abs() | WRONG transform |
| rechargerPowerDC6 | offset 68-69, PROVEN | NEVER PARSED | Field does not exist in parser |
| voltSetMode | offset 70-71 | offset 68-69 | Wrong offset |
| pscModelNumber | offset 72-73 | offset 70-71 | Wrong offset |
| leadAcidBatteryVoltage | offset 74-75 | offset 96-97 | Wrong offset (22 bytes off) |
| communicationEnable conditions | always | size > 72 | WRONG condition gate |
| Total field count | 46 | ~45 (Agent A counts 37, but sum of tiers is 45) | Overcounted |
| Condition 3 | if (size <= 54) | Two conditions: if (size <= 50) AND if (size <= 54) | Missing Gate 3 |

### 5.5 PHASE2-SCHEMA-COVERAGE-MATRIX.md vs Current State

The PHASE2 matrix for Wave D Batch 4 (Block 17400) states:
- "23 proven sub-fields (7 original + 10 hex_enable_list + 6 force_enable)"
- "force_enable from delayEnable2/3"

This description is INCORRECT: the force_enable fields do NOT come from delayEnable2/3. They come from separate hexStrToEnableList calls on bytes 12-13 (configGrid) and bytes 2-3 (configSL1). The delayEnable2 (bytes 8-9) and delayEnable3 (bytes 10-11) are separate AT1BaseSettings top-level fields that are NOT the source of any config_grid or config_sl1 force_enable sub-fields.

The matrix also states "10 FieldGroups; 23 proven sub-fields." The 23 sub-fields count is correct in terms of total fields modeled, but 6 of those fields have wrong byte offsets and will produce wrong parsed values.

---

## 6. Promotion Safety Verdict

### Block 15600

**Can it be promoted to smali_verified? NO**

Reasons:
1. **Safety blocker** (not resolvable from smali): Voltage setpoint scale factors for voltSetDC1, voltSetDC2, voltSetDC3, voltSet2DC3 are UNKNOWN. The parser uses raw parseInt(16) with no division. Block 15500 (readings) divides by 10.0f. Whether the settings block uses the same raw format or a different encoding cannot be determined from smali alone. Incorrect voltage/current setpoints represent a direct electrical hazard.

2. **Prior evidence errors** (correctable without device): Five wrong byte offsets in 15600-EVIDENCE.md, one nonexistent field (rechargerPowerDC6), one wrong transform (dcTotalPowerSet), one missing gate (Gate 3 at threshold 50), one wrong gate condition (9 fields misassigned from size>26 to size>50). These must be corrected in the evidence doc before any schema expansion.

3. **Schema docstring** claims "no documented parse method" and "46 fields" — both wrong. The parse method is DCDCParser.settingsInfoParse (confirmed). The field count is approximately 45.

**What is the minimum credible status?** The current schema (`partial`) is appropriate. The schema code itself (7 fields) is accurate. The EVIDENCE.md document needs correction. After evidence correction, status can remain `partial` (scale factors still unknown).

**Conditions for smali_verified eligibility**: (1) Correct all 8 errors in 15600-EVIDENCE.md; (2) Resolve voltage/current scale factors via device testing; (3) Confirm batteryCapacity units (mAh vs Ah vs Wh); (4) Update schema to correct field list.

---

### Block 17400

**Can it be promoted to smali_verified? NO**

Reasons:
1. **WRONG OFFSETS IN CURRENT SCHEMA** (urgent, must be corrected before promotion or any write): 6 fields have confirmed wrong byte offsets. The schema currently produces WRONG PARSED VALUES on a real device. This is not a blocker for reads per se (it reads wrong data silently), but any write operation using these offsets would corrupt AT1 transfer switch configuration.

2. **Structural incompleteness**: protectList, socSetList, timerEnable, and delayEnable fields are beyond the current FieldGroup scalar model.

3. **Device validation** (Blocker 3 from Agent B): No AT1 device packet capture has been performed. Given the wrong offsets discovered, device validation before any promotion is mandatory.

**Are there schema corrections needed BEFORE any status change? YES — urgently.**

The 6 wrong-offset fields must be corrected before:
- Any device write test (incorrect offsets sent to AT1 device = dangerous)
- Any status upgrade consideration
- Any further schema expansion

**Is the current schema INCORRECT (will it produce wrong values on a real device)?**

**YES.** On a real device response:
- `config_grid.type` will read bytes 18-19 (should be bytes 20-21) → wrong value
- `config_grid.linkage_enable` will read bytes 32-33 (should be bytes 22-23) → wrong value
- `config_grid.force_enable_0/1/2` will read bytes 8-9 (should be bytes 12-13) → wrong value
- `config_sl1.type` will read bytes 18-19 (should be bytes 20-21) → wrong value
- `config_sl1.linkage_enable` will read bytes 32-33 (should be bytes 22-23) → wrong value
- `config_sl1.force_enable_0/1/2` will read bytes 10-11 (should be bytes 2-3) → wrong value

The startup_flags group (bytes 174-175), simple_end_fields group (bytes 176-181), top_level_enables group (bytes 0-3), and both max_current fields (config_grid at byte 84, config_sl1 at byte 86) are CORRECT and will produce correct values.

---

## 7. Priority Correction List

Ranked by severity (SAFETY_CRITICAL first, then DATA_INTEGRITY, then NON_CRITICAL).

### P0 — SAFETY_CRITICAL (wrong data produced on live device)

These corrections are **mandatory before any device interaction**.

| # | File | Field | Current Offset | Correct Offset | Smali Evidence |
|---|---|---|---|---|---|
| 1 | block_17400_declarative.py | config_grid.type | 18 | **20** | AT1Parser.smali lines 2398 (0x14=20), 2404 (0x15=21) |
| 2 | block_17400_declarative.py | config_grid.linkage_enable | 32 | **22** | AT1Parser.smali lines 2433 (0x16=22), 2439 (0x17=23) |
| 3 | block_17400_declarative.py | config_grid.force_enable_0/1/2 | 8 | **12** | AT1Parser.smali lines 2258 (0xc=12), 2264 (0xd=13), 2288 (move-result) |
| 4 | block_17400_declarative.py | config_sl1.type | 18 | **20** | AT1Parser.smali lines 2621 (v10=1), 2624 (v11.get(1)) |
| 5 | block_17400_declarative.py | config_sl1.linkage_enable | 32 | **22** | AT1Parser.smali lines 2652 (v2=1), 2655 (v9.get(1)) |
| 6 | block_17400_declarative.py | config_sl1.force_enable_0/1/2 | 10 | **2** | AT1Parser.smali line 2081 (v4 from bytes 2-3), 2635 (move-object v10, v4) |

Also update corresponding test assertions in `test_block_17400_nested.py` (6 test methods asserting wrong offsets) and schema docstring comments (lines 72-79 of block_17400_declarative.py).

### P1 — DATA_INTEGRITY (wrong documentation drives future schema errors)

These corrections prevent future introduction of wrong offsets into the schema.

| # | File | Error | Correction |
|---|---|---|---|
| 7 | 15600-EVIDENCE.md | setEvent1 offset "20-23 (4 bytes)" | Change to "26-27 (2 bytes)" |
| 8 | 15600-EVIDENCE.md | dcTotalPowerSet transform "parseInt(16)" | Change to "bit16HexSignedToInt + Math.abs()" |
| 9 | 15600-EVIDENCE.md | rechargerPowerDC6 "PROVEN at 68-69" | Remove: field never called in settingsInfoParse |
| 10 | 15600-EVIDENCE.md | voltSetMode offset "70-71" | Change to "68-69" |
| 11 | 15600-EVIDENCE.md | pscModelNumber offset "72-73" | Change to "70-71" |
| 12 | 15600-EVIDENCE.md | leadAcidBatteryVoltage offset "74-75" | Change to "96-97" |
| 13 | 15600-EVIDENCE.md | communicationEnable conditions "always" | Change to "size > 72" |
| 14 | 15600-EVIDENCE.md | 9 fields with conditions "size > 26" (genCheckEnable, genType, priorityChg, cableSet, reverseChgEnable, batteryHealthEnable, remotePowerCtrl, ledEnable, reverseChgMode) | Change all to "size > 50" |
| 15 | 15600-EVIDENCE.md | Missing gate: only 3 conditions listed | Add Gate 3 (threshold 50, line 2644) and Gate 5 (threshold 72, line 3100) |
| 16 | 15600-EVIDENCE.md | Total field count "46" | Correct to approximately 45 (37 is also wrong per Agent A's internal inconsistency) |
| 17 | PHASE2-SCHEMA-COVERAGE-MATRIX.md | "force_enable from delayEnable2/3" | Correct to "configGrid force_enable from bytes 12-13; configSL1 force_enable from bytes 2-3" |

### P2 — NON_CRITICAL (schema additions, no current wrong data)

These add proven fields to the schema but do not fix incorrect data.

| # | File | Action | Evidence |
|---|---|---|---|
| 18 | block_17400_declarative.py | Add config_sl2.max_current at offset=88 (UInt16) | AT1Parser.smali lines 2869 (0x58=88), 2906 |
| 19 | block_17400_declarative.py | Add config_sl3.max_current at offset=90 (UInt16) | AT1Parser.smali lines 3027 (0x5a=90), 3064 |
| 20 | block_17400_declarative.py | Add config_sl4.max_current at offset=92 (UInt16) | AT1Parser.smali lines 3192 (0x5c=92), 3229 |
| 21 | block_17400_declarative.py | Add config_pcs1.max_current at offset=95 (UInt8, NOT UInt16) | AT1Parser.smali lines 3287 (0x5f=95), 3304 |
| 22 | block_17400_declarative.py | Add config_pcs2.max_current at offset=94 (UInt8, NOT UInt16) | AT1Parser.smali lines 3366 (0x5e=94), 3383 |
| 23 | block_17400_declarative.py | Update evidence_status of config_sl2/sl3/sl4/pcs1/pcs2 groups after additions | All max_current fields PROVEN |
| 24 | block_15600_declarative.py | Fix schema docstring: "no parse method" → "DCDCParser.settingsInfoParse" | DCDCParser.smali line 1780 |
| 25 | block_15600_declarative.py | Fix schema docstring: "46 fields" → "~45 fields (37 in evidence count inconsistent)" | Agent A field analysis |

### P3 — DEFERRED (requires device testing or framework extension)

| # | Item | Reason |
|---|---|---|
| 26 | Block 15600 voltage scale factors | Cannot determine from smali alone; device test required |
| 27 | Block 15600 current scale factors | Cannot determine from smali alone; device test required |
| 28 | Block 17400 protectList/socSetList | Framework limitation: List<NestedObject> not supported |
| 29 | Block 17400 timerEnable per config | Complex sub-parser; beyond FieldGroup scalar model |
| 30 | Block 17400 device validation | Mandatory for smali_verified promotion |

---

## Auditor's Final Notes

1. Agent A's report is high-quality and independently verifiable. The single internal inconsistency (field count 37 vs per-tier sum of 45) does not affect the correctness of the offset corrections or transform corrections — all of which are CONFIRMED.

2. Agent B's report is also high-quality. The "PARTIALLY PROVEN" designation for SL1 force_enable can be upgraded to PROVEN based on the v4 register trace. All other Agent B claims are CONFIRMED.

3. The most urgent action is fixing the 6 wrong offsets in `block_17400_declarative.py`. Until corrected, any read of config_grid or config_sl1 type/linkage_enable/force_enable fields will silently return wrong values. The test suite currently passes but asserts wrong expected values for those 6 fields.

4. The 15600 schema code itself is correct as written (7 fields, all with correct offsets). The evidence document is incorrect and must be updated before schema expansion.

5. No SDK code was modified during this audit. All findings are read-only analysis.

---

*Report produced by Agent C — Adversarial Auditor*
*All claims independently verified against primary smali sources before verdict.*
*No code was modified. Recommendations are for human review and decision.*
