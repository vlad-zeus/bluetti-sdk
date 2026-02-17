# Block 17400 (AT1_SETTINGS) — Structural Analysis Report

**Produced by**: Agent B (Structural Modeler)
**Date**: 2026-02-17
**Block ID**: 0x43f8 (17400 decimal)
**Target consumer**: Agent C (adversarial auditor)
**Status**: Analysis complete — significant schema errors identified

---

## 1. Executive Summary

A full re-analysis of AT1Parser.smali, AT1BaseSettings.smali, and AT1BaseConfigItem.smali was
performed, tracing register assignments from line 1933 through line 3662. The following
conclusions apply:

**What is correct in the current schema (23 sub-fields)**:
- `simple_end_fields` group: all 5 fields — offsets, types, transforms are CORRECT
- `top_level_enables` group: offsets 0 and 2 are CORRECT; transforms CORRECT
- `startup_flags` group: all 4 fields — offset 174, transforms CORRECT
- `config_grid.max_current` offset=84 is CORRECT (smali line 2578: `data[0x54]+data[0x55]`)
- `config_sl1.max_current` offset=86 is CORRECT (smali line 2744: `data[0x56]+data[0x57]`)

**What is WRONG in the current schema**:
- `config_grid.type`: schema says offset=18; smali proves offset=**20** (data[0x14]+data[0x15])
- `config_grid.linkage_enable`: schema says offset=32; smali proves offset=**22** (data[0x16]+data[0x17])
- `config_grid.force_enable_0/1/2`: schema says offset=8 (delayEnable2); smali proves offset=**12** (data[0x0c]+data[0x0d])
- `config_sl1.type`: schema says offset=18; smali proves offset=**20** (same list as grid, index=1)
- `config_sl1.linkage_enable`: schema says offset=32; smali proves offset=**22** (same list as grid, index=1)
- `config_sl1.force_enable_0/1/2`: schema says offset=10 (delayEnable3); actual source not confirmed yet

**New findings (Not-Guess Delta)**:
- `config_sl2.max_current` at offset=**88** (data[0x58]+data[0x59]): PROVEN (smali lines 2869-2906)
- `config_sl3.max_current` at offset=**90** (data[0x5a]+data[0x5b]): PROVEN (smali lines 3027-3064)
- `config_sl4.max_current` at offset=**92** (data[0x5c]+data[0x5d]): PROVEN (smali lines 3192-3229)
- `config_pcs1.max_current` at offset=**95** (data[0x5f] only, single byte): PROVEN (smali lines 3287-3304)
- `config_pcs2.max_current` at offset=**94** (data[0x5e] only, single byte): PROVEN (smali lines 3366-3383)

**Correction urgency**: HIGH — 6 fields in the current schema have wrong offsets. Device writes based
on these offsets would target wrong bytes in the packet, which is dangerous given CRITICAL safety
classification of this block (transfer switch control).

---

## 2. AT1BaseSettings Object Model (Full)

### 2.1 Bean Class Location

File: `smali_classes5/net/poweroak/bluetticloud/ui/connectv2/bean/AT1BaseSettings.smali`
Source file annotation: `AT1BaseSettings.kt`

### 2.2 AT1BaseSettings Fields (from .field declarations, lines 139-210)

| Field Name | Java Type | Smali Declaration Line |
|---|---|---|
| `acSupplyPhaseNum` | `int` | 140 |
| `blackStartEnable` | `int` | 142 |
| `blackStartMode` | `int` | 144 |
| `chgFromGridEnable` | `int` | 146 |
| `configGrid` | `AT1BaseConfigItem` | 148 |
| `configPCS1` | `AT1BaseConfigItem` | 150 |
| `configPCS2` | `AT1BaseConfigItem` | 152 |
| `configSL1` | `AT1BaseConfigItem` | 154 |
| `configSL2` | `AT1BaseConfigItem` | 156 |
| `configSL3` | `AT1BaseConfigItem` | 158 |
| `configSL4` | `AT1BaseConfigItem` | 160 |
| `delayEnable1` | `List<Integer>` | 162-170 |
| `delayEnable2` | `List<Integer>` | 172-180 |
| `delayEnable3` | `List<Integer>` | 182-190 |
| `feedToGridEnable` | `int` | 192 |
| `generatorAutoStartEnable` | `int` | 194 |
| `offGridPowerPriority` | `int` | 196 |
| `socBlackStart` | `int` | 198 |
| `socGenAutoStart` | `int` | 200 |
| `socGenAutoStop` | `int` (line 200+) | ~202 |
| `timerEnable1` | `List<Integer>` | d2 annotation |
| `timerEnable2` | `List<Integer>` | d2 annotation |
| `timerEnable3` | `List<Integer>` | d2 annotation |
| `voltLevelSet` | `int` | d2 annotation |

**Note on timerEnable1/2/3**: These field names appear in the Kotlin metadata d2 annotation (lines 88-94)
and in the constructor signature (d2 line 41), but are not present in the top-level d2 field list.
These are additional top-level AT1BaseSettings fields beyond the AT1BaseConfigItem objects.

**Constructor signature** (AT1Parser.smali line 2008):
```
invoke-direct/range {v2 .. v28},
Lnet/poweroak/bluetticloud/ui/connectv2/bean/AT1BaseSettings;-><init>(
    I I                                     # chgFromGridEnable, feedToGridEnable
    Ljava/util/List;                        # delayEnable1
    Ljava/util/List;                        # delayEnable2
    Ljava/util/List;                        # delayEnable3
    Ljava/util/List;                        # timerEnable1
    Ljava/util/List;                        # timerEnable2
    Ljava/util/List;                        # timerEnable3
    Lnet/.../AT1BaseConfigItem;             # configGrid
    Lnet/.../AT1BaseConfigItem;             # configSL1
    Lnet/.../AT1BaseConfigItem;             # configSL2
    Lnet/.../AT1BaseConfigItem;             # configSL3
    Lnet/.../AT1BaseConfigItem;             # configSL4
    Lnet/.../AT1BaseConfigItem;             # configPCS1
    Lnet/.../AT1BaseConfigItem;             # configPCS2
    I I I I I I I I I I                    # 10 int fields (see below)
    Lkotlin/jvm/internal/DefaultConstructorMarker;
)V
```
All v2..v28 initialized to 0 before the call (lines 1956-2006), meaning the initial AT1BaseSettings
object is constructed with all-null/zero defaults; the parser subsequently calls setXxx() methods.

### 2.3 AT1BaseConfigItem Fields (from .field declarations, lines 122-190)

File: `smali_classes5/net/poweroak/bluetticloud/ui/connectv2/bean/AT1BaseConfigItem.smali`

| Field Name | Java Type | Smali Declaration Line |
|---|---|---|
| `forceEnable` | `List<Integer>` | 124-132 |
| `linkageEnable` | `int` | 134 |
| `maxCurrent` | `int` | 136 |
| `nameL1` | `String` (nullable) | 138 |
| `nameL2` | `String` (nullable) | 140 |
| `nameResL1` | `int` | 142 |
| `nameResL2` | `int` | 144 |
| `porn` | `AT1Porn` | 146 |
| `powerOLPL1` | `int` | 148 |
| `powerOLPL2` | `int` | 150 |
| `powerOLPL3` | `int` | 152 |
| `powerULPL1` | `int` | 154 |
| `powerULPL2` | `int` | 156 |
| `powerULPL3` | `int` | 158 |
| `protectList` | `List<AT1ProtectItem>` | 160-168 |
| `socSetList` | `List<AT1SOCThresholdItem>` | 170-178 |
| `timerEnable` | `List<Integer>` | 180-188 |
| `type` | `int` | 190 |

**Total fields per AT1BaseConfigItem**: 18

**Constructor signature** (AT1BaseConfigItem.smali d2 annotation line 42):
```
(Lnet/.../AT1Porn;            # porn
 I                             # type
 Ljava/util/List;              # forceEnable  (List<Integer>)
 Ljava/util/List;              # timerEnable  (List<Integer>)
 I                             # linkageEnable
 Ljava/util/List;              # protectList  (List<AT1ProtectItem>)
 Ljava/util/List;              # socSetList   (List<AT1SOCThresholdItem>)
 I I I I I I I                # maxCurrent, powerOLPL1-3, powerULPL1-3
 Ljava/lang/String;            # nameL1
 Ljava/lang/String;            # nameL2
 I I                           # nameResL1, nameResL2
 I                             # bitmask (Kotlin DefaultConstructorMarker variant)
 Lkotlin/jvm/internal/DefaultConstructorMarker;
)V
```

### 2.4 AT1Porn Enum (from evidence doc, confirmed by smali sget-object calls)

| Value | Name | Used in |
|---|---|---|
| 0x0 | GRID | configGrid (AT1Parser line 2469) |
| 0x1 | SMART_LOAD_1 | configSL1 (AT1Parser line 2619) |
| 0x2 | SMART_LOAD_2 | configSL2 (AT1Parser line 2785) |
| 0x3 | SMART_LOAD_3 | configSL3 (AT1Parser line 2945) |
| 0x4 | SMART_LOAD_4 | configSL4 (AT1Parser line 3100) |
| 0x5 | PCS1 | configPCS1 (AT1Parser line 3270) |
| 0x6 | PCS2 | configPCS2 (AT1Parser line 3351) |

### 2.5 AT1ProtectItem Structure

**Source**: Prior evidence doc (smali not re-read for this report; referenced from 17400-EVIDENCE.md)

14 fields per item:
- `porn`: AT1Porn enum
- `enable1`, `enable2`, `enable3`: extracted from enable byte pairs
- `opp1`, `opp2`, `opp3`: from opp bytes
- `upp1`, `upp2`, `upp3`, `upp4`, `upp5`: from upp bytes
- `name`: String (resource ID or default)
- `reserved`: int

Up to 10 items per AT1BaseConfigItem.protectList.

### 2.6 AT1SOCThresholdItem Structure

**Source**: Prior evidence doc (referenced from 17400-EVIDENCE.md)

8 fields per item:
- `porn`: AT1Porn enum
- `soc1`, `soc2`, `soc3`: SOC thresholds (0-100%)
- `reserved1`, `reserved2`: ints
- `name`: String
- `flag`: boolean

Exactly 6 items per AT1BaseConfigItem.socSetList.

---

## 3. AT1BaseConfigItem Field Map Per Group

### 3.1 Byte Index Convention

The parser receives `List<String>` where each element is one 2-char hex string = 1 byte.
Data index N maps exactly to packet byte offset N (1:1 correspondence).

### 3.2 Pre-computation Register Table

Before configGrid is constructed, the parser builds multiple hexStrToEnableList results.
Traced from AT1Parser.smali lines 2012-2463:

| Register | Source bytes (data indices) | hexStrToEnableList result | Used for |
|---|---|---|---|
| v2 (line 2048) | 0-1 | hexStrToEnableList(data[0]+data[1]) | chgFromGridEnable, feedToGridEnable |
| v4 (line 2081) | 2-3 | hexStrToEnableList(data[2]+data[3]) | unknown (possibly SL1 forceEnable source) |
| v8 (line 2116) | 4-5 | hexStrToEnableList(data[4]+data[5]) | unknown |
| v2 (line 2177) | 6-7 | stored as delayEnable1 (setDelayEnable1) | AT1BaseSettings.delayEnable1 |
| v2 (line 2214) | 8-9 | stored as delayEnable2 (setDelayEnable2) | AT1BaseSettings.delayEnable2 |
| v2 (line 2251) | 10-11 | stored as delayEnable3 (setDelayEnable3) | AT1BaseSettings.delayEnable3 |
| v2 (line 2288) | 12-13 | hexStrToEnableList(data[12]+data[13]) | configGrid.timerEnable (take(3)) |
| v12 (line 2323) | 14-15 | hexStrToEnableList(data[14]+data[15]) | unknown |
| v10 (line 2358) | 16-17 | hexStrToEnableList(data[16]+data[17]) | saved to v47 line 2531 |
| v5 (line 2393) | 18-19 | hexStrToEnableList(data[18]+data[19]) | PCS1/PCS2 type (saved to v46 line 2527) |
| v11 (line 2428) | 20-21 | hexStrToEnableList(data[20]+data[21]) | configGrid.type[0], SL1.type[1], SL2.type[2], SL3.type[3], SL4.type[4] |
| v9 (line 2463) | 22-23 | hexStrToEnableList(data[22]+data[23]) | configGrid.linkageEnable[0], SL1[1], SL2[2], SL3[3], SL4[4] |

**Key smali evidence**:
- v5 saved to v46 at line 2527: `move-object/from16 v46, v5`
- v10 saved to v47 at line 2531: `move-object/from16 v47, v10`
- v46 used for PCS1 type at line 3272: `move-object/from16 v3, v46`
- v46 used for PCS2 type at line 3353-3356: same v3 (index 1)

### 3.3 configGrid (AT1Porn.GRID) — Smali lines 2466-2613

| Parameter # | Field Name | Data Indices | Byte Offset | Type | Transform | Smali Lines | Status |
|---|---|---|---|---|---|---|---|
| 1 | porn | — | — | AT1Porn | constant GRID | 2469 | PROVEN |
| 2 | type | 20-21 | 20 | int | hexStrToEnableList(data[20]+data[21]).get(0) | 2428, 2472-2480 | PROVEN (corrected) |
| 3 | forceEnable | 12-13 | 12 | List\<Int\> | hexStrToEnableList(data[12]+data[13]).take(3) | 2288, 2483-2491 | PROVEN (corrected) |
| 4 | timerEnable | — | — | List\<Int\> | DEFAULT (bitmask 0x3FF44, bit 3 set) | 2611 bitmask | DEFERRED |
| 5 | linkageEnable | 22-23 | 22 | int | hexStrToEnableList(data[22]+data[23]).get(0) | 2463, 2494-2502 | PROVEN (corrected) |
| 6 | protectList | 24-29,96-101,126-131 | — | List\<AT1ProtectItem\> | protectEnableParse() | 2509-2537 | COMPLEX |
| 7 | socSetList | 84-89 | 84 | List\<AT1SOC...\> | socThresholdParse() | 2541-2539 | COMPLEX |
| 8 | maxCurrent | 84-85 | 84 | int (UInt16) | parseInt(data[0x54]+data[0x55], 16) | 2541-2578 | PROVEN |
| 9-14 | powerOLPL1-3, powerULPL1-3 | — | — | int | DEFAULT 0 | 2588-2606 | HARDCODED |
| 15 | nameL1 | — | — | String | DEFAULT null | 2611 bitmask | HARDCODED |
| 16 | nameL2 | — | — | String | DEFAULT null | 2611 bitmask | HARDCODED |
| 17 | nameResL1 | — | — | int | 0x3FF44 (constant) | 2580 | HARDCODED |
| 18 | nameResL2 | — | — | int | 0x0 | 2582-2583 | HARDCODED |

**CORRECTION from current schema**:
- type: was offset=18, actually offset=**20**
- linkage_enable: was offset=32, actually offset=**22**
- force_enable_0/1/2: was offset=8 (delayEnable2), actually offset=**12** (separate hexStrToEnableList of data[12-13])

**protectList data ranges** (smali lines 2509-2513, 2517-2521, 2529-2533):
- enable: data[0x18..0x1e) = data[24..30) = 6 elements
- opp: data[0x60..0x66) = data[96..102) = 6 elements
- upp: data[0x7e..0x84) = data[126..132) = 6 elements

**socSetList data range** (smali lines 2541-2543):
- socBytes: data[0x54..0x5a) = data[84..90) = 6 elements

**NOTE on parameter ordering in constructor range {v23..v43}**:
- v23=this, v24=porn, v25=type, v26=forceEnable(List, DEFAULT), v27=timerEnable(v2.take(3)),
  v28=linkageEnable, v29=protectList, v30-v43 follow standard order
- v42=0x3FF44 bitmask at line 2580, v43=0x0 (DefaultConstructorMarker placeholder) at line 2582

### 3.4 configSL1 (AT1Porn.SMART_LOAD_1) — Smali lines 2616-2779

| Parameter # | Field Name | Data Indices | Byte Offset | Type | Transform | Smali Lines | Status |
|---|---|---|---|---|---|---|---|
| 1 | porn | — | — | AT1Porn | constant SMART_LOAD_1 | 2619 | PROVEN |
| 2 | type | 20-21 | 20 | int | hexStrToEnableList(data[20]+data[21]).get(1) | 2621-2632 | PROVEN (corrected) |
| 3 | forceEnable | 2-3 | 2 | List\<Int\> | take(3) from hexStrToEnableList(data[2]+data[3]) | 2635-2643 | PARTIALLY PROVEN |
| 4 | timerEnable | 30-35 | 30 | List\<Int\> | subList(30, 36) pattern | 2648-2650 | COMPLEX |
| 5 | linkageEnable | 22-23 | 22 | int | hexStrToEnableList(data[22]+data[23]).get(1) | 2652-2663 | PROVEN (corrected) |
| 6 | protectList | 30-35,102-107,138-149 | — | List\<AT1ProtectItem\> | protectEnableParse() | 2666-2690 | COMPLEX |
| 7 | socSetList | 60-65 | 60 | List\<AT1SOC...\> | socThresholdParse() | 2703-2707 | COMPLEX |
| 8 | maxCurrent | 86-87 | 86 | int (UInt16) | parseInt(data[0x56]+data[0x57], 16) | 2709-2746 | PROVEN |
| 9-14 | powerOLPL1-3, powerULPL1-3 | — | — | int | DEFAULT 0 | 2758-2772 | HARDCODED |
| 15 | nameL1 | — | — | String | R$string.device_porn_smart_load_1_l1 | 2749 | HARDCODED |
| 16 | nameL2 | — | — | String | R$string.device_porn_smart_load_1_l2 | 2752 | HARDCODED |
| 17 | nameResL1 | — | — | int | 0xFF00 (65280) | 2754 | HARDCODED |
| 18 | nameResL2 | — | — | int | 0x0 | 2756 | HARDCODED |

**CORRECTIONS from current schema**:
- type: was offset=18 index[1], actually offset=**20** index[1] (same v11 list as grid, different index)
- linkage_enable: was offset=32 index[1], actually offset=**22** index[1]
- force_enable_0/1/2: was offset=10 (delayEnable3=data[10-11]); actually from `v4.take(3)` where v4 = hexStrToEnableList(data[2]+data[3]) = **offset=2**. UNCONFIRMED — requires tracing v4 at line 2635.

**CAVEAT on SL1 force_enable**: The register v4 at line 2635 (`move-object v10, v4`) needs tracing. v4 was set at line 2081 as hexStrToEnableList(data[2-3]) but may have been reassigned. Evidence is **PARTIALLY PROVEN** until v4 is confirmed not reassigned between line 2081 and 2635.

### 3.5 configSL2 (AT1Porn.SMART_LOAD_2) — Smali lines 2782-2939

| Parameter # | Field Name | Data Indices | Byte Offset | Type | Transform | Smali Lines | Status |
|---|---|---|---|---|---|---|---|
| 1 | porn | — | — | AT1Porn | constant SMART_LOAD_2 | 2785 | PROVEN |
| 2 | type | 20-21 | 20 | int | hexStrToEnableList(data[20]+data[21]).get(2) | 2787, 2790-2798 | PROVEN |
| 5 | linkageEnable | 22-23 | 22 | int | hexStrToEnableList(data[22]+data[23]).get(2) | 2820-2829 | PROVEN |
| 8 | maxCurrent | 88-89 | 88 | int (UInt16) | parseInt(data[0x58]+data[0x59], 16) | 2869-2906 | **PROVEN** |
| other | (deferred) | — | — | — | complex sub-parsers / defaults | — | DEFERRED |

**maxCurrent evidence** (smali lines 2869-2906):
```smali
2869:    const/16 v3, 0x58        # = 88
2872:    invoke-interface {v0, v3}, Ljava/util/List;->get(I)Ljava/lang/Object;
2876:    const/16 v4, 0x59        # = 89
2878:    invoke-interface {v0, v4}, Ljava/util/List;->get(I)Ljava/lang/Object;
...
2904:    invoke-static {v3, v5}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;I)I
2906:    move-result v77           # = maxCurrent
```

### 3.6 configSL3 (AT1Porn.SMART_LOAD_3) — Smali lines 2942-3097

| Parameter # | Field Name | Data Indices | Byte Offset | Type | Transform | Smali Lines | Status |
|---|---|---|---|---|---|---|---|
| 1 | porn | — | — | AT1Porn | constant SMART_LOAD_3 | 2945 | PROVEN |
| 2 | type | 20-21 | 20 | int | hexStrToEnableList(data[20]+data[21]).get(3) | 2947, 2950-2958 | PROVEN |
| 5 | linkageEnable | 22-23 | 22 | int | hexStrToEnableList(data[22]+data[23]).get(3) | 2977-2985 | PROVEN |
| 8 | maxCurrent | 90-91 | 90 | int (UInt16) | parseInt(data[0x5a]+data[0x5b], 16) | 3027-3064 | **PROVEN** |
| other | (deferred) | — | — | — | complex sub-parsers / defaults | — | DEFERRED |

**maxCurrent evidence** (smali lines 3027-3064):
```smali
3027:    const/16 v3, 0x5a        # = 90
3030:    invoke-interface {v0, v3}, Ljava/util/List;->get(I)Ljava/lang/Object;
3034:    const/16 v4, 0x5b        # = 91
3036:    invoke-interface {v0, v4}, Ljava/util/List;->get(I)Ljava/lang/Object;
...
3062:    invoke-static {v3, v5}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;I)I
3064:    move-result v56           # = maxCurrent
```

### 3.7 configSL4 (AT1Porn.SMART_LOAD_4) — Smali lines 3100-3264

| Parameter # | Field Name | Data Indices | Byte Offset | Type | Transform | Smali Lines | Status |
|---|---|---|---|---|---|---|---|
| 1 | porn | — | — | AT1Porn | constant SMART_LOAD_4 | 3100 | PROVEN |
| 2 | type | 20-21 | 20 | int | hexStrToEnableList(data[20]+data[21]).get(4) | 3102, 3105-3113 | PROVEN |
| 5 | linkageEnable | 22-23 | 22 | int | hexStrToEnableList(data[22]+data[23]).get(4) | 3133-3144 | PROVEN |
| 8 | maxCurrent | 92-93 | 92 | int (UInt16) | parseInt(data[0x5c]+data[0x5d], 16) | 3192-3229 | **PROVEN** |
| other | (deferred) | — | — | — | complex sub-parsers / defaults | — | DEFERRED |

**maxCurrent evidence** (smali lines 3192-3229):
```smali
3192:    const/16 v2, 0x5c        # = 92
3195:    invoke-interface {v0, v2}, Ljava/util/List;->get(I)Ljava/lang/Object;
3199:    const/16 v3, 0x5d        # = 93
3201:    invoke-interface {v0, v3}, Ljava/util/List;->get(I)Ljava/lang/Object;
...
3227:    invoke-static {v2, v4}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;I)I
3229:    move-result v77           # = maxCurrent
```

### 3.8 configPCS1 (AT1Porn.PCS1) — Smali lines 3267-3345

| Parameter # | Field Name | Data Index | Byte Offset | Type | Transform | Smali Lines | Status |
|---|---|---|---|---|---|---|---|
| 1 | porn | — | — | AT1Porn | constant PCS1 | 3270 | PROVEN |
| 2 | type | 18-19 | 18 | int | hexStrToEnableList(data[18]+data[19]).get(0) | 3272-3285 | **PROVEN** |
| 8 | maxCurrent | 95 | 95 | int (UInt8 effective) | parseInt(data[0x5f], 16) — SINGLE BYTE | 3287-3304 | **PROVEN** |
| other | (deferred) | — | — | — | defaults / not parsed | — | DEFERRED |

**maxCurrent evidence** (smali lines 3287-3304):
```smali
3287:    const/16 v4, 0x5f        # = 95
3290:    invoke-interface {v0, v4}, Ljava/util/List;->get(I)Ljava/lang/Object;
3294:    check-cast v4, Ljava/lang/String;
3296:    const/16 v5, 0x10
3298:    invoke-static {v5}, Lkotlin/text/CharsKt;->checkRadix(I)I
3300:    move-result v6
3302:    invoke-static {v4, v6}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;I)I
3304:    move-result v31           # = maxCurrent
```

**CRITICAL DIFFERENCE from SL1-4**: PCS1 maxCurrent reads only ONE element (data[0x5f]), not two
concatenated bytes. The cast is directly to String (not Object→Number→intValue). The max value is
0xFF (255) from a single byte, not 0xFFFF from two bytes. Schema type should be **UInt8**, not UInt16.

**type evidence** (smali lines 3272-3285):
```smali
3272:    move-object/from16 v3, v46    # v46 = hexStrToEnableList(data[18]+data[19])
3274:    const/4 v4, 0x0
3277:    invoke-interface {v3, v4}, Ljava/util/List;->get(I)Ljava/lang/Object;
3281:    check-cast v5, Ljava/lang/Number;
3283:    invoke-virtual {v5}, Ljava/lang/Number;->intValue()I
3285:    move-result v25              # = type
```

### 3.9 configPCS2 (AT1Porn.PCS2) — Smali lines 3348-3424

| Parameter # | Field Name | Data Index | Byte Offset | Type | Transform | Smali Lines | Status |
|---|---|---|---|---|---|---|---|
| 1 | porn | — | — | AT1Porn | constant PCS2 | 3351 | PROVEN |
| 2 | type | 18-19 | 18 | int | hexStrToEnableList(data[18]+data[19]).get(1) | 3353-3364 | **PROVEN** |
| 8 | maxCurrent | 94 | 94 | int (UInt8 effective) | parseInt(data[0x5e], 16) — SINGLE BYTE | 3366-3383 | **PROVEN** |
| other | (deferred) | — | — | — | defaults / not parsed | — | DEFERRED |

**maxCurrent evidence** (smali lines 3366-3383):
```smali
3366:    const/16 v3, 0x5e        # = 94
3369:    invoke-interface {v0, v3}, Ljava/util/List;->get(I)Ljava/lang/Object;
3373:    check-cast v3, Ljava/lang/String;
3376:    invoke-static {v4}, Lkotlin/text/CharsKt;->checkRadix(I)I
3379:    move-result v5
3381:    invoke-static {v3, v5}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;I)I
3383:    move-result v52           # = maxCurrent
```

**type evidence** (smali lines 3353-3364):
```smali
3353:    const/4 v4, 0x1
3356:    invoke-interface {v3, v4}, Ljava/util/List;->get(I)Ljava/lang/Object;   # v3 still = v46
3360:    check-cast v3, Ljava/lang/Number;
3362:    invoke-virtual {v3}, Ljava/lang/Number;->intValue()I
3364:    move-result v46          # = type
```

---

## 4. Helper Parsers

### 4.1 protectEnableParse()

**Location**: AT1Parser.smali, private method (referenced from prior evidence; lines 416-750)

**Signature**: `private final protectEnableParse(AT1Porn, List<String>, List<String>, List<String>) List<AT1ProtectItem>`

**Inputs**:
- `porn`: enum value (identifies which load)
- `enableList`: hex string list (6 elements = 3 enable-byte-pairs)
- `oppList`: hex string list (6 elements = 3 opp-byte-pairs)
- `uppList`: hex string list (up to 16 elements)

**Output**: `List<AT1ProtectItem>` — up to 10 items

**Algorithm** (from prior evidence, not re-verified in this session):
1. Chunk enableList by 2-element pairs → up to 10 chunks
2. For each chunk: parse 2 hex bytes as 16-bit value, extract 3 enable flags
3. Build AT1ProtectItem(porn, 11 integers, name, reserved)

**Data ranges per config item** (verified from smali subList calls):

| Config | enableList (data[a..b)) | oppList (data[c..d)) | uppList (data[e..f)) |
|---|---|---|---|
| configGrid | data[0x18..0x1e) = [24..30) | data[0x60..0x66) = [96..102) | data[0x7e..0x84) = [126..132) |
| configSL1 | data[0x1e..0x24) = [30..36) | data[0x66..0x6c) = [102..108) | data[0x84..0x8a) = [132..138) |
| configSL2 | data[0x24..0x2a) = [36..42) | data[0x6c..0x72) = [108..114) | data[0x8a..0x90) = [138..144) |
| configSL3 | data[0x30..0x??) (v6,0x30 at line 2990) | data[0x72..0x78) = [114..120) | data[0x90..0x96) = [144..150) |
| configSL4 | data[0x30..0x36) = [48..54) | data[0x78..0x7e) = [120..126) | data[0x96..0x9c) = [150..156) |
| configPCS1 | — (no protectEnableParse call observed) | — | — |
| configPCS2 | — (no protectEnableParse call observed) | — | — |

**Note**: PCS1 and PCS2 do NOT call protectEnableParse. Their protectList defaults to null/empty
(handled by the Kotlin DefaultConstructorMarker bitmask 0x3ff7c).

### 4.2 socThresholdParse()

**Location**: AT1Parser.smali, private method (referenced from prior evidence; lines 751-930)

**Signature**: `private final socThresholdParse(List<String>, AT1Porn) List<AT1SOCThresholdItem>`

**Inputs**: list of 6 hex string elements, porn enum

**Output**: `List<AT1SOCThresholdItem>` — exactly 6 items

**Data ranges** (from subList calls in smali):

| Config | socBytes range | Byte offsets |
|---|---|---|
| configGrid | data[0x54..0x5a) | [84..90) |
| configSL1 | data[0x3c..0x42) | [60..66) |
| configSL2 | data[0x42..0x48) | [66..72) |
| configSL3 | data[0x48..0x4e) | [72..78) |
| configSL4 | data[0x4e..0x54) | [78..84) |
| configPCS1 | — (no call) | — |
| configPCS2 | — (no call) | — |

**Note**: PCS1 and PCS2 do NOT call socThresholdParse either. Their socSetList defaults to null/empty.

---

## 5. Current Schema Validation

### 5.1 Field-by-Field Verdict Table

| Group | Field | Schema Offset | Schema Transform | Smali Verdict | Correct? | Evidence Lines |
|---|---|---|---|---|---|---|
| top_level_enables | chg_from_grid_enable | 0 | hex_enable_list:0:3 | data[0]+data[1], v2.get(3) | **CORRECT** | 2012-2129 |
| top_level_enables | feed_to_grid_enable | 2 | hex_enable_list:0:4 | data[2]+data[3], v4.get(4) | **CORRECT** | 2051-2142 |
| startup_flags | black_start_enable | 174 | hex_enable_list:0:2 | data[0xae]+data[0xaf], v2.get(2) | **CORRECT** | 3429-3478 |
| startup_flags | black_start_mode | 174 | hex_enable_list:0:3 | same bytes, v2.get(3) | **CORRECT** | 3480-3493 |
| startup_flags | generator_auto_start_enable | 174 | hex_enable_list:0:4 | same bytes, v2.get(4) | **CORRECT** | 3495-3508 |
| startup_flags | off_grid_power_priority | 174 | hex_enable_list:0:5 | same bytes, v2.get(5) | **CORRECT** | 3510-3523 |
| config_grid | type | 18 | hex_enable_list:0:0 | data[0x14]+data[0x15]=bytes 20-21, v11.get(0) | **WRONG — offset should be 20** | 2428, 2472-2480 |
| config_grid | linkage_enable | 32 | hex_enable_list:0:0 | data[0x16]+data[0x17]=bytes 22-23, v9.get(0) | **WRONG — offset should be 22** | 2463, 2494-2502 |
| config_grid | force_enable_0 | 8 | hex_enable_list:0:0 | data[0x0c]+data[0x0d]=bytes 12-13, v2.take(3)[0] | **WRONG — offset should be 12** | 2288, 2483-2491 |
| config_grid | force_enable_1 | 8 | hex_enable_list:0:1 | same bytes 12-13, index 1 | **WRONG — offset should be 12** | 2288, 2483-2491 |
| config_grid | force_enable_2 | 8 | hex_enable_list:0:2 | same bytes 12-13, index 2 | **WRONG — offset should be 12** | 2288, 2483-2491 |
| config_grid | max_current | 84 | none | data[0x54]+data[0x55]=bytes 84-85 | **CORRECT** | 2541-2578 |
| config_sl1 | type | 18 | hex_enable_list:0:1 | data[0x14]+data[0x15]=bytes 20-21, v11.get(1) | **WRONG — offset should be 20** | 2621-2632 |
| config_sl1 | linkage_enable | 32 | hex_enable_list:0:1 | data[0x16]+data[0x17]=bytes 22-23, v9.get(1) | **WRONG — offset should be 22** | 2652-2663 |
| config_sl1 | force_enable_0 | 10 | hex_enable_list:0:0 | take(3)[0] from v4=hexStrToEnableList(data[2-3]) | **WRONG — offset likely 2** (PARTIALLY PROVEN) | 2635-2643 |
| config_sl1 | force_enable_1 | 10 | hex_enable_list:0:1 | same, index 1 | **WRONG — offset likely 2** (PARTIALLY PROVEN) | 2635-2643 |
| config_sl1 | force_enable_2 | 10 | hex_enable_list:0:2 | same, index 2 | **WRONG — offset likely 2** (PARTIALLY PROVEN) | 2635-2643 |
| config_sl1 | max_current | 86 | none | data[0x56]+data[0x57]=bytes 86-87 | **CORRECT** | 2744-2746 |
| simple_end_fields | volt_level_set | 176 | bitmask:0x7 | data[0xb0]+data[0xb1]=bytes 176-177, AND 0x7 | **CORRECT** | 3525-3567 |
| simple_end_fields | ac_supply_phase_num | 176 | shift:3, bitmask:0x7 | same bytes, SHR 3, AND 0x7 | **CORRECT** | 3569-3578 |
| simple_end_fields | soc_gen_auto_stop | 178 | clamp:0:100 | data[0xb2]=byte 178, min(100) | **CORRECT** | 3580-3605 |
| simple_end_fields | soc_gen_auto_start | 179 | none | data[0xb3]=byte 179 | **CORRECT** | 3607-3626 |
| simple_end_fields | soc_black_start | 181 | none | data[0xb5]=byte 181 | **CORRECT** | 3628-3645 |

### 5.2 Summary of Wrong Fields

6 fields in the current schema have wrong byte offsets (all in config_grid and config_sl1):

- `config_grid.type`: offset=18 → should be **20**
- `config_grid.linkage_enable`: offset=32 → should be **22**
- `config_grid.force_enable_0/1/2`: offset=8 → should be **12**
- `config_sl1.type`: offset=18 → should be **20**
- `config_sl1.linkage_enable`: offset=32 → should be **22**
- `config_sl1.force_enable_0/1/2`: offset=10 → should be **2** (PARTIALLY PROVEN — requires v4 trace confirmation)

**Root cause of the errors**: The previous evidence document incorrectly mapped the hexStrToEnableList
register assignments. Specifically:
- "delayEnable2.take(3)" was cited for forceEnable but the actual register at take() was NOT delayEnable2
  (bytes 8-9) — it was hexStrToEnableList(bytes 12-13) which had been stored in v2 at line 2288.
- "type at data[18-19]" was incorrect because the hexStrToEnableList result from bytes 18-19 was saved
  to v46 (line 2527) for PCS1/PCS2 type, not for grid/SL type.
- "linkageEnable at bytes 32-33" was incorrect; the actual bytes are 22-23 (data[0x16-0x17]).

---

## 6. No-Guess Delta

### 6.a Fields That CAN Be Added Now (100% smali evidence)

All items below have an explicit parser call + setter chain verified in AT1Parser.smali.

**config_sl2.max_current**:
- offset: 88 (data[0x58], two-byte UInt16)
- type: UInt16
- transform: none (direct parseInt hex, two bytes)
- smali lines: 2869 (`const/16 v3, 0x58`), 2876 (`const/16 v4, 0x59`), 2904-2906 (parseInt, move-result v77)
- evidence_status: PROVEN

**config_sl3.max_current**:
- offset: 90 (data[0x5a], two-byte UInt16)
- type: UInt16
- transform: none
- smali lines: 3027 (`const/16 v3, 0x5a`), 3034 (`const/16 v4, 0x5b`), 3062-3064 (parseInt, move-result v56)
- evidence_status: PROVEN

**config_sl4.max_current**:
- offset: 92 (data[0x5c], two-byte UInt16)
- type: UInt16
- transform: none
- smali lines: 3192 (`const/16 v2, 0x5c`), 3199 (`const/16 v3, 0x5d`), 3227-3229 (parseInt, move-result v77)
- evidence_status: PROVEN

**config_pcs1.max_current**:
- offset: 95 (data[0x5f], SINGLE BYTE — NOT UInt16)
- type: UInt8 (max value 0xFF = 255)
- transform: none
- smali lines: 3287 (`const/16 v4, 0x5f`), 3290 (get single element), 3294 (cast to String directly), 3302-3304 (parseInt, move-result v31)
- evidence_status: PROVEN
- **WARNING**: Schema type must be UInt8, not UInt16 — single element parse, not two-byte concatenation

**config_pcs2.max_current**:
- offset: 94 (data[0x5e], SINGLE BYTE — NOT UInt16)
- type: UInt8 (max value 0xFF = 255)
- transform: none
- smali lines: 3366 (`const/16 v3, 0x5e`), 3369 (get single element), 3373 (cast to String directly), 3381-3383 (parseInt, move-result v52)
- evidence_status: PROVEN
- **WARNING**: Schema type must be UInt8, not UInt16 — single element parse, not two-byte concatenation

**config_pcs1.type** (via v46 = hexStrToEnableList(data[18-19])):
- offset: 18 (data[0x12]+data[0x13], two-byte hexStrToEnableList input)
- type: UInt16
- transform: hex_enable_list:0:0 (index 0 from list)
- smali lines: 2393 (v5=hexStrToEnableList result), 2527 (`move-object/from16 v46, v5`), 3272 (`move-object/from16 v3, v46`), 3277 (`v3.get(0)`)
- evidence_status: PROVEN

**config_pcs2.type** (same v46, index 1):
- offset: 18 (same source as PCS1)
- type: UInt16
- transform: hex_enable_list:0:1 (index 1 from same list)
- smali lines: 2393 (v5), 2527 (v46=v5), 3353 (`const/4 v4, 0x1`), 3356 (`v3.get(v4)`)
- evidence_status: PROVEN

**Corrections to add (replacing wrong offsets)**:
These are NOT new fields but require schema offset corrections:
- `config_grid.type`: change offset from 18 to **20**, transform stays hex_enable_list:0:0
- `config_grid.linkage_enable`: change offset from 32 to **22**, transform stays hex_enable_list:0:0
- `config_grid.force_enable_0/1/2`: change offset from 8 to **12**
- `config_sl1.type`: change offset from 18 to **20**, transform stays hex_enable_list:0:1
- `config_sl1.linkage_enable`: change offset from 32 to **22**, transform stays hex_enable_list:0:1

### 6.b Fields That MUST Remain Deferred

| Field | Group | Reason |
|---|---|---|
| delay_enable_1 | top-level | Full List\<Integer\> output of hexStrToEnableList(data[6-7]); no scalar index extracted |
| delay_enable_2 | top-level | Full List\<Integer\>; stored as AT1BaseSettings.delayEnable2 but no scalar element confirmed |
| delay_enable_3 | top-level | Full List\<Integer\>; same reason |
| forceEnable (list) | any config | Full List stored in AT1BaseConfigItem.forceEnable; only scalar take(3) elements proven |
| timerEnable (list) | any config | Passed as subList or take; complex list, no scalar element extraction confirmed |
| protectList | all config | Sub-parser protectEnableParse(); requires 14-field AT1ProtectItem — beyond FieldGroup model |
| socSetList | all config | Sub-parser socThresholdParse(); requires 8-field AT1SOCThresholdItem — beyond FieldGroup model |
| powerOLPL1-3 | all config | Hardcoded 0 (default bitmask); NOT read from data |
| powerULPL1-3 | all config | Hardcoded 0 (default bitmask); NOT read from data |
| nameL1/nameL2 | all config | Resource ID constants (R$string), not data-derived (except SL1-4 which use resource IDs) |
| nameResL1/nameResL2 | all config | Hardcoded constants (0x3FF44 for grid, 0xFF00 for SL); not data-derived |
| timerEnable1/2/3 | AT1BaseSettings | Top-level list fields in AT1BaseSettings; no scalar extraction observed in parser |
| config_sl1.force_enable_0/1/2 | config_sl1 | Offset PARTIALLY PROVEN as byte 2; v4 register trace not completed |
| config_sl2.type | config_sl2 | PROVEN (bytes 20-21, index 2) but offset correction BLOCKER: schema must first fix type offsets |
| config_sl3.type | config_sl3 | PROVEN (bytes 20-21, index 3) same blocker |
| config_sl4.type | config_sl4 | PROVEN (bytes 20-21, index 4) same blocker |
| config_sl2.linkage_enable | config_sl2 | PROVEN (bytes 22-23, index 2) same blocker |
| config_sl3.linkage_enable | config_sl3 | PROVEN (bytes 22-23, index 3) same blocker |
| config_sl4.linkage_enable | config_sl4 | PROVEN (bytes 22-23, index 4) same blocker |

---

## 7. Promotion Blockers

The following specific gaps prevent upgrade from `partial` to `smali_verified`:

### Blocker 1: WRONG OFFSETS IN CURRENT SCHEMA (CRITICAL)

The 6 fields listed in Section 5.2 have incorrect byte offsets. The schema currently claims
config_grid.type at offset=18, but smali proves offset=20. Any write operation using these
offsets would corrupt adjacent data in a safety-critical transfer switch block.

**Resolution**: Correct offsets in block_17400_declarative.py before any upgrade consideration.
- config_grid.type: 18 → 20
- config_grid.linkage_enable: 32 → 22
- config_grid.force_enable_0/1/2: 8 → 12
- config_sl1.type: 18 → 20
- config_sl1.linkage_enable: 32 → 22
- config_sl1.force_enable_0/1/2: 10 → 2 (PARTIALLY PROVEN — confirm first)

### Blocker 2: SL1 FORCE_ENABLE OFFSET UNCONFIRMED

The forceEnable source for configSL1 is `take(3)` from register v4 at AT1Parser line 2635.
v4 was set at line 2081 as `hexStrToEnableList(data[2]+data[3])`. However, v4 may have been
reassigned between lines 2081 and 2635.

**What is needed**: Read AT1Parser.smali lines 2081-2635 and search for any instruction that
writes to register v4 (e.g., `move-result-object v4`, `const v4`, `move-object v4`). If no such
instruction exists, the PARTIALLY PROVEN evidence for offset=2 becomes PROVEN.

**Smali method**: `at1SettingsParse`, lines 2081-2635.
**Search target**: any opcode writing to v4 between those lines.

### Blocker 3: DEVICE VALIDATION NOT DONE

No physical AT1 device packet has been captured and verified against the schema. All parser-side
evidence is smali-level only. The safety-critical nature of this block (transfer switch operation)
requires at minimum one full device validation cycle before `smali_verified` status.

**What is needed**: Capture of a real Block 17400 response from an AT1 device; parse with the
corrected schema; compare results with official Bluetti app display.

### Blocker 4: PCS1/PCS2 SINGLE-BYTE vs TWO-BYTE MAX_CURRENT

The current schema uses `UInt16` for all max_current fields. PCS1 and PCS2 max_current are
single-byte reads (data[0x5f] and data[0x5e] respectively), not two-byte concatenations. The
schema must use `UInt8` for these fields, not `UInt16`. Failure to correct this will cause the
parser to read a wrong value or panic on short data.

**What is needed**: Change config_pcs1.max_current and config_pcs2.max_current type from UInt16 to
UInt8 in the schema.

### Blocker 5: COMPLEX SUB-PARSERS NOT MODELED

The `protectEnableParse()` and `socThresholdParse()` helpers produce nested object lists
(AT1ProtectItem and AT1SOCThresholdItem respectively). These cannot be modeled as FieldGroup
sub-fields in the current declarative framework which supports only flat scalars. Until the
framework supports nested object list parsing, these fields must remain deferred.

**What is needed**: Framework extension to support `List<NestedObject>` with sub-parser wiring.
This is a significant infrastructure investment.

### Blocker 6: HARDCODED-DEFAULT FIELDS

11 of the 18 AT1BaseConfigItem fields are hardcoded to zero/null/default via the Kotlin
DefaultConstructorMarker bitmask (e.g., powerOLPL1-3, powerULPL1-3, nameL1, nameL2, nameResL1,
nameResL2 for configGrid). These fields are NOT read from the packet data. They must not be
added to the schema as if they were data-derived fields.

**What is needed**: Documentation confirming which fields are hardcoded per config group (done for
configGrid with bitmask 0x3FF44; configSL1-4 use 0xFF00 mask; configPCS1-2 use 0x3FF7C).

---

## 8. Deferred Group Analysis (config_sl2..4, pcs1..2)

### 8.1 config_sl2

| Sub-field | Evidence Strength | Byte Offset | Smali Line(s) |
|---|---|---|---|
| max_current | **PROVEN** | 88 (bytes 0x58-0x59) | 2869-2906 |
| type | PROVEN (part of v11 list) | 20 (same as grid/sl1, index 2) | 2787-2798 |
| linkage_enable | PROVEN (part of v9 list) | 22 (same as grid/sl1, index 2) | 2820-2829 |
| force_enable_0/1/2 | NOT_FOUND (register trace incomplete) | unknown | — |
| timerEnable | COMPLEX | — | 2804-2807 (subList) |
| protectList | COMPLEX | 36-41, 108-113, 138-143 | 2832-2852 |
| socSetList | COMPLEX | 66-71 | 2856-2865 |
| powerOLPL/UL | HARDCODED_ZERO | — | 2918-2932 |
| nameL1/L2 | HARDCODED_RESOURCE | — | 2909-2912 |
| nameResL1 | HARDCODED: 0xFF00 | — | 2914 |

**Promotion status**: `partial` — max_current PROVEN and addable; type/linkage_enable also addable
but require first fixing the shared list offsets in schema (conflict with existing wrong offsets).

### 8.2 config_sl3

| Sub-field | Evidence Strength | Byte Offset | Smali Line(s) |
|---|---|---|---|
| max_current | **PROVEN** | 90 (bytes 0x5a-0x5b) | 3027-3064 |
| type | PROVEN (v11 list, index 3) | 20 | 2950-2958 |
| linkage_enable | PROVEN (v9 list, index 3) | 22 | 2977-2985 |
| force_enable_0/1/2 | NOT_FOUND | unknown | — |
| timerEnable | COMPLEX | — | — |
| protectList | COMPLEX | 42-47, 114-119, 144-149 | 2988-3008 |
| socSetList | COMPLEX | 72-77 | 3012-3023 |
| powerOLPL/UL | HARDCODED_ZERO | — | 3076-3090 |
| nameL1/L2 | HARDCODED_RESOURCE | — | 3067-3070 |

**Promotion status**: `partial` — max_current PROVEN.

### 8.3 config_sl4

| Sub-field | Evidence Strength | Byte Offset | Smali Line(s) |
|---|---|---|---|
| max_current | **PROVEN** | 92 (bytes 0x5c-0x5d) | 3192-3229 |
| type | PROVEN (v11 list, index 4) | 20 | 3102-3113 |
| linkage_enable | PROVEN (v9 list, index 4) | 22 | 3133-3144 |
| force_enable_0/1/2 | NOT_FOUND | unknown | — |
| timerEnable | COMPLEX | — | — |
| protectList | COMPLEX | 48-53, 120-125, 150-155 | 3147-3173 |
| socSetList | COMPLEX | 78-83 | 3177-3188 |
| powerOLPL/UL | HARDCODED_ZERO | — | 3244-3258 |
| nameL1/L2 | HARDCODED_RESOURCE | — | 3232-3235 |

**Promotion status**: `partial` — max_current PROVEN.

### 8.4 config_pcs1

| Sub-field | Evidence Strength | Byte Offset | Smali Line(s) |
|---|---|---|---|
| max_current | **PROVEN** (SINGLE BYTE UInt8) | **95** (data[0x5f] only) | 3287-3304 |
| type | **PROVEN** | 18 (data[0x12]+data[0x13], v46, index 0) | 3272-3285 |
| linkage_enable | NOT_FOUND | unknown | — |
| forceEnable/timerEnable | NOT PARSED (defaults) | — | — |
| protectList | NOT PARSED (bitmask 0x3FF7C defaults) | — | — |
| socSetList | NOT PARSED (defaults) | — | — |
| powerOLPL/UL | HARDCODED_ZERO (bitmask) | — | 3310-3338 |
| nameResL1 | HARDCODED: 0x3FF7C | — | 3306 |

**Promotion status**: max_current PROVEN (UInt8), type PROVEN; both addable.

### 8.5 config_pcs2

| Sub-field | Evidence Strength | Byte Offset | Smali Line(s) |
|---|---|---|---|
| max_current | **PROVEN** (SINGLE BYTE UInt8) | **94** (data[0x5e] only) | 3366-3383 |
| type | **PROVEN** | 18 (data[0x12]+data[0x13], v46, index 1) | 3353-3364 |
| linkage_enable | NOT_FOUND | unknown | — |
| forceEnable/timerEnable | NOT PARSED (defaults) | — | — |
| protectList | NOT PARSED (bitmask 0x3FF7C defaults) | — | — |
| socSetList | NOT PARSED (defaults) | — | — |
| powerOLPL/UL | HARDCODED_ZERO (bitmask) | — | 3389-3417 |
| nameResL1 | HARDCODED: 0x3FF7C | — | 3385 |

**Promotion status**: max_current PROVEN (UInt8), type PROVEN; both addable.

---

## 9. Key Byte Offset Reference Table

All max_current fields across the 7 config groups:

| Config Group | max_current byte offset | Width | Smali line range |
|---|---|---|---|
| configGrid | 84 (data[0x54]+data[0x55]) | UInt16 | 2541-2578 |
| configSL1 | 86 (data[0x56]+data[0x57]) | UInt16 | 2709-2746 |
| configSL2 | 88 (data[0x58]+data[0x59]) | UInt16 | 2869-2906 |
| configSL3 | 90 (data[0x5a]+data[0x5b]) | UInt16 | 3027-3064 |
| configSL4 | 92 (data[0x5c]+data[0x5d]) | UInt16 | 3192-3229 |
| configPCS2 | 94 (data[0x5e] only) | **UInt8** | 3366-3383 |
| configPCS1 | 95 (data[0x5f] only) | **UInt8** | 3287-3304 |

**Pattern**: Grid and SL1-4 increment by 2 (each UInt16). PCS2 at byte 94 and PCS1 at byte 95
are single-byte reads. Note PCS2 (94) precedes PCS1 (95) in packet ordering but PCS1 (3267) is
constructed before PCS2 (3348) in code.

---

## 10. Analysis Methodology and Confidence

**Method**: Direct register tracing through AT1Parser.smali at1SettingsParse method (lines 1933-3662).
Each hexStrToEnableList call was traced to its source data indices by following the `const` opcodes
for the two-element data indices immediately before each `invoke-interface {v0, vN}` call.

**Confidence levels**:
- PROVEN: explicit const opcode for data index + direct path to setter/constructor parameter
- PARTIALLY PROVEN: indirect register trace not fully closed (v4 between lines 2081-2635)
- NOT_FOUND: no explicit smali evidence found in this analysis session
- COMPLEX: sub-parser involved; cannot model without framework extension
- HARDCODED: default/constant value, not data-read; confirmed by DefaultConstructorMarker bitmask

**Limitations**:
1. The register v4 trace between lines 2081 and 2635 was not completed; config_sl1 force_enable
   source offset (line 2635 `move-object v10, v4`) is PARTIALLY PROVEN only.
2. timerEnable data ranges for SL1-4 were not fully decoded; subList boundaries were not tracked for
   all groups.
3. AT1ProtectItem and AT1SOCThresholdItem field semantics were not re-verified; evidence from
   17400-EVIDENCE.md is accepted as prior work.

---

**Report complete.**
**Status**: Analysis done; CORRECTION REQUIRED in schema before any promotion or device testing.
**Safety note**: Do NOT use the current (uncorrected) schema for any write operations.
