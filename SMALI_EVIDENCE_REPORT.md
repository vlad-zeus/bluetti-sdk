# Smali Evidence Report: Partial Blocks Analysis

**Generated**: 2026-02-16
**Scope**: 11 blocks currently marked as "partial"
**Objective**: Determine which blocks can be upgraded to smali_verified

---

## Summary Table

| Block | Hex | Switch Route | Parser Method | Bean Class | Status |
|-------|-----|--------------|---------------|------------|--------|
| 14700 | 0x396c | :sswitch_23 @ 6715 | SmartPlugParser.settingsInfoParse | SmartPlugSettingsBean | ⚠️ Parser exists, bean fields TBD |
| 15500 | 0x3c8c | :sswitch_21 @ 6648 | DCDCParser.baseInfoParse | DCDCInfo | ⚠️ Parser exists, bean fields TBD |
| 15600 | 0x3cf0 | :sswitch_20 @ 6605 | DCDCParser.settingsInfoParse | DCDCSettings | ⚠️ Parser exists, bean fields TBD |
| 17100 | 0x42cc | :sswitch_18 @ 6428 | AT1Parser.at1InfoParse | AT1BaseInfo | ⚠️ Parser exists, bean fields TBD |
| 17400 | 0x43f8 | :sswitch_17 @ 6399 | AT1Parser.at1SettingsParse | AT1BaseSettings | ⚠️ Parser exists, bean fields TBD |
| 18000 | 0x4650 | :sswitch_16 @ 6381 | EpadParser.baseInfoParse | EpadBaseInfo | ⚠️ Parser exists, bean fields TBD |
| 18300 | 0x477c | :sswitch_15 @ 6363 | EpadParser.baseSettingsParse | EpadBaseSettings | ⚠️ Parser exists, bean fields TBD |
| 18400 | 0x47e0 | :sswitch_14 @ 6347 | EpadParser.baseLiquidPointParse | List<?> | ⚠️ Shared parser, item type TBD |
| 18500 | 0x4844 | :sswitch_13 @ 6331 | EpadParser.baseLiquidPointParse | List<?> | ⚠️ Shared parser, item type TBD |
| 18600 | 0x48a8 | :sswitch_12 @ 6315 | EpadParser.baseLiquidPointParse | List<?> | ⚠️ Shared parser, item type TBD |
| 26001 | 0x6591 | :sswitch_8 @ 6139 | TouTimeCtrlParser.parseTouTimeExt | List<?> | ⚠️ Parser exists, item type TBD |

---

## Block 14700: SMART_PLUG_SETTINGS

### Switch Route Evidence
- **ConnectManager.smali**: Line 8212 → `0x396c -> :sswitch_23`
- **Handler**: Lines 6715-6729
- **Event name**: `"SMART_PLUG_SETTINGS"`

### Parser Evidence
```smali
# Line 6722-6724
sget-object v2, Lnet/poweroak/bluetticloud/ui/device_smart_plug/tools/SmartPlugParser;->INSTANCE:...
invoke-virtual {v2, v4}, ...;->settingsInfoParse(Ljava/util/List;)Lnet/poweroak/bluetticloud/ui/device_smart_plug/bean/SmartPlugSettingsBean;
```

### Bean Evidence
- **Class**: `SmartPlugSettingsBean.smali`
- **Location**: `smali_classes5/net/poweroak/bluetticloud/ui/device_smart_plug/bean/`
- **Constructor**: TBD (requires bean file analysis)

### Field Mapping Evidence
❌ **NOT YET ANALYZED** - Requires:
1. Read SmartPlugParser.settingsInfoParse method
2. Extract setter call sequence
3. Map byte offsets to bean fields
4. Verify field semantics from setter names

### Recommendation
**Status**: Keep as **PARTIAL**
**Reason**: Parser method confirmed, but field-level mapping not verified from smali

---

## Block 15500: DC_DC_INFO

### Switch Route Evidence
- **ConnectManager.smali**: Line 8214 → `0x3c8c -> :sswitch_21`
- **Handler**: Lines 6648-6694
- **Event name**: None (stores to deviceDataV2.dcdcInfo)

### Parser Evidence
```smali
# Line 6649-6651
sget-object v1, Lnet/poweroak/bluetticloud/ui/connectv2/tools/DCDCParser;->INSTANCE:...
invoke-virtual {v1, v4}, ...;->baseInfoParse(Ljava/util/List;)Lnet/poweroak/bluetticloud/ui/connectv2/bean/DCDCInfo;
```

### Bean Evidence
- **Class**: `DCDCInfo.smali`
- **Location**: `smali_classes5/net/poweroak/bluetticloud/ui/connectv2/bean/`
- **Constructor**: TBD (requires bean file analysis)

### Field Mapping Evidence
❌ **NOT YET ANALYZED** - Requires:
1. Read DCDCParser.baseInfoParse method
2. Extract setter call sequence
3. Map byte offsets to bean fields
4. Verify field semantics from setter names

### Recommendation
**Status**: Keep as **PARTIAL**
**Reason**: Parser method confirmed, but field-level mapping not verified from smali

---

## Block 15600: DC_DC_SETTINGS

### Switch Route Evidence
- **ConnectManager.smali**: Line 8215 → `0x3cf0 -> :sswitch_20`
- **Handler**: Lines 6605-6646
- **Event name**: None (stores to deviceDataV2.dcdcInfo via setter)

### Parser Evidence
```smali
# Line 6606-6608
sget-object v1, Lnet/poweroak/bluetticloud/ui/connectv2/tools/DCDCParser;->INSTANCE:...
invoke-virtual {v1, v4}, ...;->settingsInfoParse(Ljava/util/List;)Lnet/poweroak/bluetticloud/ui/connectv2/bean/DCDCSettings;
```

### Bean Evidence
- **Class**: `DCDCSettings.smali`
- **Location**: `smali_classes5/net/poweroak/bluetticloud/ui/connectv2/bean/`
- **Constructor**: TBD (requires bean file analysis)

### Field Mapping Evidence
❌ **NOT YET ANALYZED** - Requires:
1. Read DCDCParser.settingsInfoParse method
2. Extract setter call sequence
3. Map byte offsets to bean fields
4. Verify field semantics from setter names

### Recommendation
**Status**: Keep as **PARTIAL**
**Reason**: Parser method confirmed, but field-level mapping not verified from smali

---

## Block 17100: AT1_BASE_INFO

### Switch Route Evidence
- **ConnectManager.smali**: Line 8223 → `0x42cc -> :sswitch_18`
- **Handler**: Lines 6428-6454
- **Event name**: `"AT1_INFO"`

### Parser Evidence
```smali
# Line 6431-6433
sget-object v2, Lnet/poweroak/bluetticloud/ui/connectv2/tools/AT1Parser;->INSTANCE:...
invoke-virtual {v2, v4}, ...;->at1InfoParse(Ljava/util/List;)Lnet/poweroak/bluetticloud/ui/connectv2/bean/AT1BaseInfo;
```

### Bean Evidence
- **Class**: `AT1BaseInfo.smali`
- **Location**: `smali_classes5/net/poweroak/bluetticloud/ui/connectv2/bean/`
- **Constructor**: TBD (requires bean file analysis)

### Field Mapping Evidence
❌ **NOT YET ANALYZED** - Requires:
1. Read AT1Parser.at1InfoParse method
2. Extract setter call sequence
3. Map byte offsets to bean fields
4. Verify field semantics from setter names

### Recommendation
**Status**: Keep as **PARTIAL**
**Reason**: Parser method confirmed, but field-level mapping not verified from smali

---

## Block 17400: AT1_SETTINGS

### Switch Route Evidence
- **ConnectManager.smali**: Line 8224 → `0x43f8 -> :sswitch_17`
- **Handler**: Lines 6399-6426
- **Event name**: `"AT1_SETTINGS_PART1"`

### Parser Evidence
```smali
# Line 6402-6404
sget-object v2, Lnet/poweroak/bluetticloud/ui/connectv2/tools/AT1Parser;->INSTANCE:...
invoke-virtual {v2, v4}, ...;->at1SettingsParse(Ljava/util/List;)Lnet/poweroak/bluetticloud/ui/connectv2/bean/AT1BaseSettings;
```

### Bean Evidence
- **Class**: `AT1BaseSettings.smali`
- **Location**: `smali_classes5/net/poweroak/bluetticloud/ui/connectv2/bean/`
- **Constructor**: TBD (requires bean file analysis)

### Field Mapping Evidence
❌ **NOT YET ANALYZED** - Requires:
1. Read AT1Parser.at1SettingsParse method
2. Extract setter call sequence
3. Map byte offsets to bean fields
4. Verify field semantics from setter names

### Recommendation
**Status**: Keep as **PARTIAL**
**Reason**: Parser method confirmed, but field-level mapping not verified from smali

---

## Block 18000: EPAD_INFO

### Switch Route Evidence
- **ConnectManager.smali**: Line 8225 → `0x4650 -> :sswitch_16`
- **Handler**: Lines 6381-6397
- **Event name**: `"EPAD_BASE_INFO"`

### Parser Evidence
```smali
# Line 6388-6390
sget-object v2, Lnet/poweroak/bluetticloud/ui/connectv2/tools/EpadParser;->INSTANCE:...
invoke-virtual {v2, v4}, ...;->baseInfoParse(Ljava/util/List;)Lnet/poweroak/bluetticloud/ui/connectv2/bean/EpadBaseInfo;
```

### Bean Evidence
- **Class**: `EpadBaseInfo.smali`
- **Location**: `smali_classes5/net/poweroak/bluetticloud/ui/connectv2/bean/`
- **Constructor**: TBD (requires bean file analysis)

### Field Mapping Evidence
❌ **NOT YET ANALYZED** - Requires:
1. Read EpadParser.baseInfoParse method
2. Extract setter call sequence
3. Map byte offsets to bean fields
4. Verify field semantics from setter names

### Known Issue
- **Min length**: 2019 bytes (0x7e3) - exceptionally large payload
- **Implication**: Likely contains historical data or multi-channel monitoring
- **Risk**: Full field mapping extremely time-consuming without device testing

### Recommendation
**Status**: Keep as **PARTIAL**
**Reason**: Parser method confirmed, but 2KB payload structure not fully understood

---

## Block 18300: EPAD_SETTINGS

### Switch Route Evidence
- **ConnectManager.smali**: Line 8226 → `0x477c -> :sswitch_15`
- **Handler**: Lines 6363-6379
- **Event name**: `"EPAD_BASE_SETTINGS"`

### Parser Evidence
```smali
# Line 6370-6372
sget-object v2, Lnet/poweroak/bluetticloud/ui/connectv2/tools/EpadParser;->INSTANCE:...
invoke-virtual {v2, v4}, ...;->baseSettingsParse(Ljava/util/List;)Lnet/poweroak/bluetticloud/ui/connectv2/bean/EpadBaseSettings;
```

### Bean Evidence
- **Class**: `EpadBaseSettings.smali`
- **Location**: `smali_classes5/net/poweroak/bluetticloud/ui/connectv2/bean/`
- **Constructor**: TBD (requires bean file analysis)

### Field Mapping Evidence
❌ **NOT YET ANALYZED** - Requires:
1. Read EpadParser.baseSettingsParse method
2. Extract setter call sequence
3. Map byte offsets to bean fields
4. Verify field semantics from setter names

### Recommendation
**Status**: Keep as **PARTIAL**
**Reason**: Parser method confirmed, but field-level mapping not verified from smali

---

## Blocks 18400/18500/18600: EPAD_LIQUID_POINT_1/2/3

### Shared Parser Evidence
**ALL THREE BLOCKS** use the same parser method:

```smali
sget-object v2, Lnet/poweroak/bluetticloud/ui/connectv2/tools/EpadParser;->INSTANCE:...
invoke-virtual {v2, v4}, ...;->baseLiquidPointParse(Ljava/util/List;)Ljava/util/List;
```

### Switch Route Evidence
- **Block 18400** (0x47e0): Line 8227 → `:sswitch_14` @ 6347-6361
- **Block 18500** (0x4844): Line 8228 → `:sswitch_13` @ 6331-6345
- **Block 18600** (0x48a8): Line 8229 → `:sswitch_12` @ 6315-6329

### Event Name Issue
All three handlers use variable `v7` for event name instead of string constant:
```smali
invoke-static {v7}, Lcom/jeremyliao/liveeventbus/LiveEventBus;->get(Ljava/lang/String;)...
```

**Requires trace-back** to find where `v7` is initialized (likely to "EPAD_BASE_LIQUID_POINT1/2/3")

### Bean Evidence
- **Return type**: `List<?>` - item type unknown from handler
- **Requires**: Analysis of EpadParser.baseLiquidPointParse to find item bean class

### Field Mapping Evidence
❌ **NOT YET ANALYZED** - Requires:
1. Find event string constant for each block (trace v7 initialization)
2. Read EpadParser.baseLiquidPointParse method
3. Identify list item bean class
4. Extract item structure (byte offsets, fields)
5. Map semantics from setter names

### Recommendation
**Status**: Keep as **PARTIAL**
**Reason**: Shared parser complicates analysis; event name not explicit in handlers

---

## Block 26001: TOU_TIME_INFO

### Switch Route Evidence
- **ConnectManager.smali**: Line 8239 → `0x6591 -> :sswitch_8`
- **Handler**: Lines 6139-6155
- **Event name**: `"TOU_TIME_INFO"`

### Parser Evidence
```smali
# Line 6146-6148
sget-object v2, Lnet/poweroak/bluetticloud/ui/connectv2/tools/TouTimeCtrlParser;->INSTANCE:...
invoke-virtual {v2, v4}, ...;->parseTouTimeExt(Ljava/util/List;)Ljava/util/List;
```

### Bean Evidence
- **Return type**: `List<?>` - item type unknown from handler
- **Requires**: Analysis of TouTimeCtrlParser.parseTouTimeExt to find item bean class

### Field Mapping Evidence
❌ **NOT YET ANALYZED** - Requires:
1. Read TouTimeCtrlParser.parseTouTimeExt method
2. Identify list item bean class
3. Extract item structure (byte offsets, fields)
4. Map semantics from setter names

### Recommendation
**Status**: Keep as **PARTIAL**
**Reason**: Parser method confirmed, but list item structure not verified from smali

---

## Overall Analysis Summary

### Confirmed Evidence (All 11 Blocks)
✅ **Switch routes**: All confirmed with line references
✅ **Parser methods**: All confirmed with class + method names
✅ **Bean classes**: Files located for 7 blocks (14700, 15500, 15600, 17100, 17400, 18000, 18300)
❌ **Bean constructors**: NOT analyzed (requires reading each bean file)
❌ **Field mappings**: NOT analyzed (requires reading each parser method)
❌ **Field semantics**: NOT analyzed (requires setter name interpretation)

### Next Steps to Achieve smali_verified

For **ANY** block to be upgraded to `smali_verified`, the following evidence is required:

1. ✅ Switch route (already have)
2. ✅ Parser method signature (already have)
3. ❌ **Bean constructor signature** - requires reading bean .smali file
4. ❌ **Complete field table** with:
   - Field name (from bean setter calls)
   - Byte offset (from parser logic)
   - Data type (from parser datatype calls)
   - Transform/unit (from parser transform functions)
   - Smali line references (from parser method)

### Effort Estimate

**Per block analysis** (parser method + bean constructor):
- **Simple block** (4-6 fields): 30-45 minutes
- **Medium block** (7-12 fields): 45-90 minutes
- **Complex block** (13+ fields or List return): 90-180 minutes

**Total for 11 blocks**: Estimated 10-15 hours of smali disassembly work

### Recommendation

**Priority approach**:
1. Start with **simplest candidates**: Blocks with fewest fields and single bean (not List)
2. **Defer List-based blocks** (18400/18500/18600, 26001) until SDK supports dynamic arrays
3. **Defer EPAD_INFO** (18000) due to 2KB payload complexity

**Suggested order**:
1. **14700** (SmartPlugSettings) - likely 4-6 fields
2. **15600** (DCDCSettings) - likely 4-6 fields
3. **15500** (DCDCInfo) - likely 8-10 fields
4. **17100** (AT1BaseInfo) - likely 8-10 fields
5. **17400** (AT1BaseSettings) - likely 10-12 fields
6. **18300** (EpadSettings) - likely 10-12 fields
7. **18000** (EpadInfo) - DEFERRED (2KB payload)
8. **18400/18500/18600** - DEFERRED (shared parser, List return)
9. **26001** - DEFERRED (List return, complex time-of-use structure)

---

## Conclusion

**Current state**: All 11 blocks have **parser methods confirmed** but **NO field-level verification** from smali.

**Upgrade path**: Each block requires individual deep-dive analysis (30-180 min each) to extract complete field mappings.

**Recommendation**: Keep all blocks as **PARTIAL** until systematic parser analysis is completed for each block individually.

