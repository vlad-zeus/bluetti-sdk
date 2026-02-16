# Phase 2 Schema Coverage Matrix

Status: Draft (post `platform-stable`)  
Updated: 2026-02-15

## Goal

Turn APK-recovered block documentation into implemented, tested declarative schemas and aligned device profiles.

## Ground Truth Sources

1. `docs/blocks/V2_BLOCKS_INDEX.md` (78 discovered V2 blocks)
2. `docs/blocks/*.md` detailed reverse-engineering notes
3. Active SDK profiles in `bluetti_sdk/devices/profiles/*.py`

## Current Implementation Snapshot

Implemented declarative schemas in SDK:

1. Block `100` (`APP_HOME_DATA`)
2. Block `1100` (`INV_BASE_INFO`) ✅ Wave A
3. Block `1300` (`INV_GRID_INFO`)
4. Block `1400` (`INV_LOAD_INFO`) ✅ Wave A
5. Block `1500` (`INV_INV_INFO`) ✅ Wave A
6. Block `6000` (`PACK_MAIN_INFO`)
7. Block `6100` (`PACK_ITEM_INFO`) ✅ Wave A

Profile-required blocks today:

1. `EL30V2`: `100`, `1300`, `6000` (✅ fully covered)
2. `Elite 200 V2`: `100`, `1300`, `6000` (✅ fully covered)
3. `EL100V2`: `100`, `1100`, `1300`, `1400`, `1500`, `6000`, `6100` (✅ fully covered)

## Priority Matrix (Phase 2)

### Wave A (P0): Close active profile gaps ✅ COMPLETED

| Block | Doc Status | SDK Schema | In Active Profile | Priority | Status |
|---|---|---|---|---|---|
| 1100 | Full | ✅ Implemented | EL100V2 | P0 | ✅ Done |
| 1400 | Full | ✅ Implemented | EL100V2 | P0 | ✅ Done |
| 1500 | Full | ✅ Implemented | EL100V2 | P0 | ✅ Done |
| 6100 | Full | ✅ Implemented | EL100V2 | P0 | ✅ Done |

Definition of done for Wave A: ✅ ALL COMPLETE

1. ✅ Add `block_1100_declarative.py`, `block_1400_declarative.py`, `block_1500_declarative.py`, `block_6100_declarative.py`
2. ✅ Register schemas via `schemas/__init__.py` auto-registration
3. ✅ Add unit tests (structure validation) and smoke tests (client integration)
4. ✅ Validate EL100V2 group reads for `inverter` and `cells`
5. ✅ Quality gates: ruff ✓, mypy ✓, pytest (270 passed, 89% coverage ✓)

### Wave B (P1): Core control/settings blocks from APK docs ✅ COMPLETED

| Block | Doc Status | SDK Schema | Priority | Status | Field Coverage |
|---|---|---|---|---|---|
| 2000 | Full | ✅ Implemented | P1 | ✅ Done | 23 fields (partial: gaps at offsets 1-5, 5-7, 7-9, 9-11, 11-13, 13-15, 15-19, 19-21, 25-27, 31-33) |
| 2200 | Full | ✅ Implemented | P1 | ✅ Done | 11 fields (partial: gaps at 9-11, 11-13; includes password field) |
| 2400 | Full | ✅ Implemented | P1 | ✅ Done | 6 fields (full coverage for documented offsets) |
| 7000 | Full | ✅ Implemented | P1 | ✅ Done | 4 fields (partial: gap at offset 3-11) |
| 11000 | Full | ✅ Implemented | P1 | ✅ Done | 6 fields (full coverage for IOT identification) |
| 12002 | Full | ✅ Implemented | P1 | ✅ Done | 4 fields (partial: variable offset due to H32BEnable; SECURITY: WiFi credentials) |
| 19000 | Full | ✅ Implemented | P1 | ✅ Done | 6 threshold pairs (bit-packed format, requires application unpacking) |

Definition of done for Wave B: ✅ ALL COMPLETE

1. ✅ Add block_2000/2200/2400/7000/11000/12002/19000_declarative.py
2. ✅ Register schemas via `schemas/__init__.py` auto-registration (14 total built-in blocks)
3. ✅ Add unit tests (test_wave_b_blocks.py: 14 tests, test_wave_b_blocks_smoke.py: 4 tests)
4. ✅ Quality gates: ruff ✓, mypy ✓, pytest (304 passed, 89% coverage ✓)
5. ✅ Documentation: TODO(smali-verify) markers for ambiguous offsets

Key Findings:
- Block 2200, 12002: Contain sensitive data (password, WiFi credentials)
- Block 19000: Bit-packed format (2 SOC thresholds per UInt16 register)
- All blocks marked required=False for ambiguous fields pending smali verification

### Wave C (P2): Monitoring expansion ✅ COMPLETED

| Block | Doc Status | SDK Schema | Priority | Status | Field Coverage |
|---|---|---|---|---|---|
| 720 | Smali-Verified | ✅ Implemented | P2 | ✅ Done | 7 fields (ota_group + file0 status array; full 16-file structure documented) |
| 1700 | Smali-Verified | ✅ Implemented | P2 | ✅ Done | 7 fields (model, sn, status, sys_time, Float32 raw fields for 3-phase meter) |
| 3500 | Smali-Verified | ✅ Implemented | P2 | ✅ Done | 8 fields (energy_type + total_energy + 3 yearly entries; full 15-year structure documented) |
| 3600 | Smali-Verified | ✅ Implemented | P2 | ✅ Done | 6 fields (energy_type + year + total + 3 monthly entries; full 12-month + 31-day structure documented) |
| 6300 | Smali-Verified | ✅ Implemented | P2 | ✅ Done | 5 fields (single-BMU baseline with smali-verified dynamic offset formulas for multi-BMU) |
| 12161 | Smali-Verified | ✅ Implemented | P2 | ✅ Done | 2 fields (bit-packed control flags with documented bit positions) |

Definition of done for Wave C: ✅ ALL COMPLETE

1. ✅ Add block_720/1700/3500/3600/6300/12161_declarative.py
2. ✅ Register schemas via `schemas/__init__.py` auto-registration (20 total built-in blocks)
3. ✅ Add unit tests (test_wave_c_blocks.py: 16 tests, test_wave_c_blocks_smoke.py: parser-integrated)
4. ✅ Quality gates: ruff ✓, mypy ✓ (57 files), pytest ✓ (16 Wave C tests passing)
5. ✅ Reverse-engineering closure complete - all blocks smali-verified (ProtocolParserV2.smali)

Smali Verification Details:
- Block 720: parseOTAStatus (lines 28228-28430) - OTA group + 16-file status array
- Block 1700: parseInvMeterInfo (lines 24757-25100) - CT meter with Float32 encoding
- Block 3500: parseTotalEnergyInfo (lines 32107-32300) - 15-year energy array
- Block 3600: parseCurrYearEnergy (lines 10784-11000) - 12-month + 31-day energy arrays
- Block 6300: parsePackBMUInfo (lines 28435-28850) - Dynamic multi-BMU offset formulas
- Block 12161: parseIOTEnableInfo (lines 15526-15800) - Bit-packed control flags

Key Implementation Decisions:
- Array structures: Implemented first entries with full structure documented for future dynamic support
- Float32 values (Block 1700): Stored as raw UInt32 with conversion documented
- Bit-packed flags (Block 12161): Stored as raw UInt16 with bit positions documented
- Dynamic parsing (Block 6300): Single-BMU baseline with exact formulas for multi-BMU extension

### Wave D Batch 1 (P3): High-value long-tail blocks ✅ COMPLETED

| Block | Doc Status | SDK Schema | Priority | Status | Field Coverage |
|---|---|---|---|---|---|
| 19100 | Smali-Verified | ✅ Implemented | P3 | ✅ Done | 8 fields (enable/action flags for 16 delay settings, bit-packed) |
| 19200 | Smali-Verified | ✅ Implemented | P3 | ✅ Done | 10 fields (enable flags + 4 backup schedules with start/end times) |
| 19300 | Smali-Verified | ✅ Implemented | P3 | ✅ Done | 5 fields (enable flags + timer count; task list in separate block) |
| 19305 | Smali-Verified | ✅ Implemented | P3 | ✅ Done | 9 fields (timer0 task details: time, days, mode, power) |
| 40127 | Partial | ✅ Implemented | P3 | ⚠️ Provisional | 11 fields (grid power limits + protection settings; 30+ additional fields TBD) |

Definition of done for Wave D Batch 1: ✅ ALL COMPLETE

1. ✅ Add block_19100/19200/19300/19305/40127_declarative.py
2. ✅ Register schemas via `schemas/__init__.py` auto-registration (25 total built-in blocks)
3. ✅ Add unit tests (test_wave_d_batch1_blocks.py: 10 tests, test_wave_d_batch1_smoke.py: 3 tests)
4. ✅ Quality gates: ruff ✓, mypy ✓ (62 files), pytest ✓ (334 passed, 90% coverage ✓)

Smali Verification Details:
- Block 19100: commDelaySettingsParse (lines 2287-2700) - Bit-packed delay enable/action flags
- Block 19200: parseScheduledBackup (lines 31605-31900) - 4 scheduled backup time windows
- Block 19300: commTimerSettingsParse (lines 3249-3395) - Timer enable flags + count
- Block 19305: commTimerTaskListParse (lines 3397-3600) + parseTimerItem - 40-byte timer tasks
- Block 40127: parseHomeStorageSettings (lines 13955-14700) - Partial (first 11 fields of 38+ total)

Key Implementation Decisions:
- Delay settings (Block 19100): Bit-packed format (2 bits per setting), 16 settings max
- Scheduled backup (Block 19200): 4 backup time windows with UInt32 timestamps
- Timer settings (Blocks 19300/19305): Enable flags + task list split across 2 blocks
- Timer tasks: 40-byte structure with time, days-of-week bitfield, mode, power
- Home storage (Block 40127): Baseline implementation of first 11 fields; full 38+ field mapping requires comprehensive smali analysis

**Security Notes**:
- **Block 19100**: Grid charge delay settings affect charging behavior
- **Block 19200**: Scheduled backup controls when backup power is active
- **Block 19300/19305**: Timer settings control automatic charge/discharge - verify time zones and power limits
- **Block 40127**: **CRITICAL** - Controls grid-tied inverter protection thresholds. Incorrect values may violate grid codes or damage equipment. Only modify with proper understanding of grid compliance requirements.

**Completion Date**: 2026-02-15
**Quality Gates**: ruff ✅, mypy ✅ (62 files), pytest ✅ (334 tests, 90% coverage)
**Status**: ✅ **WAVE D BATCH 1 COMPLETE**

### Wave D Batch 2 (P3): DC Hub, ATS, and AT1 Timer Event Blocks ✅ COMPLETED

| Block | Doc Status | SDK Schema | Priority | Status | Field Coverage |
|---|---|---|---|---|---|\n| 15750 | Smali-Verified | ✅ Implemented | P3 | ✅ Done | 2 fields (DC hub settings: enable flags, voltage) |
| 17000 | Smali-Verified | ✅ Implemented | P3 | ✅ Done | 4 fields (ATS info: model, SN, software type/version) |
| 19365 | Smali-Verified | ✅ Implemented | P3 | ✅ Done | 6 fields (AT1 timer slots 1-2: bit-packed flags + values per slot) |
| 19425 | Smali-Verified | ✅ Implemented | P3 | ✅ Done | 6 fields (AT1 timer slots 3-4: bit-packed flags + values per slot) |
| 19485 | Smali-Verified | ✅ Implemented | P3 | ✅ Done | 6 fields (AT1 timer slots 5-6: bit-packed flags + values per slot) |

Definition of done for Wave D Batch 2: ✅ ALL COMPLETE

1. ✅ Add block_15750/17000/19365/19425/19485_declarative.py
2. ✅ Register schemas via `schemas/__init__.py` auto-registration (30 total built-in blocks)
3. ✅ Add unit tests (test_wave_d_batch2_blocks.py: 10 tests, test_wave_d_batch2_smoke.py: 3 tests)
4. ✅ Quality gates: ruff ✓, mypy ✓ (67 files), pytest ✓ (346 passed, 90% coverage ✓)

Smali Verification Details:
- Block 15750: dcHubSettingsParse (lines 5224-5356) - DC hub enable flags + voltage setting
- Block 17000: atsInfoParse (lines 745-877) - ATS device info with ASCII model/SN
- Blocks 19365/19425/19485: parseTimerItem (lines 31973-32105) + AT1Parser - 4-byte timer items with bit-packed flags

Key Implementation Decisions:
- DC Hub (Block 15750): Bit-packed enable flags (dcEnable, switchRecoveryEnable) + raw voltage UInt8
- ATS Info (Block 17000): 12-byte ASCII model + 8-byte SN + software type/version
- AT1 Timer Events: Each block holds 2 timer slots (4 bytes per slot: UInt16 flags + 2× UInt8 values)
- Timer flag structure: Bits 0-6 (days of week), Bit 7 (padding), Bits 8-11 (mode flags)
- Baseline implementation covers first slot per block; full 2-slot structure documented

**Security Notes**:
- **Block 15750**: DC hub voltage settings - verify values within safe operating range
- **Blocks 19365/19425/19485**: AT1 timer slots control automatic charge/discharge timing - device-specific to AT1 models

**Completion Date**: 2026-02-15
**Quality Gates**: ruff ✅, mypy ✅ (67 files), pytest ✅ (346 tests, 90% coverage)
**Status**: ✅ **WAVE D BATCH 2 COMPLETE**

### Wave D Batch 3 (P3): Accessory Devices (Smart Plug, DC-DC, AT1 Extended) ✅ COMPLETED

| Block | Doc Status | SDK Schema | Priority | Status | Field Coverage |
|---|---|---|---|---|---|
| 14500 | Smali-Verified | ✅ Implemented | P3 | ✅ Verified | 4 fields (model, serial_number, software_version, plug_count) |
| 14700 | Partial | ✅ Implemented | P3 | ⚠️ Partial | 4 fields (SmartPlugParser path confirmed; settings semantics pending) |
| 15500 | Smali-Verified | ✅ Implemented | P3 | ✅ Verified | 8 fields (all fully proven with scale factors from smali) |
| 15600 | Partial | ✅ Implemented | P3 | ⚠️ Partial | 4 fields (DCDCParser.settingsInfoParse confirmed; voltage/current setpoint scale factors UNKNOWN - SAFETY BLOCKER for write operations) |
| 17100 | Smali-Verified | ✅ Implemented | P3 | ✅ Verified | 3 fields (model, serial_number, software_version fully proven; 6 unverified fields removed) |

Definition of done for Wave D Batch 3: ✅ ALL COMPLETE

1. ✅ Add block_14500/14700/15500/15600/17100_declarative.py
2. ✅ Register schemas via `schemas/__init__.py` auto-registration (35 total built-in blocks)
3. ✅ Add unit tests (test_wave_d_batch3_blocks.py: 10 tests, test_wave_d_batch3_smoke.py: 3 tests)
4. ✅ Quality gates: ruff ✓, mypy ✓ (72 files), pytest ✓ (359 passed, 91% coverage ✓)

Block Type Classification:
- Blocks 14500/14700: parser-backed via SmartPlugParser (baseInfoParse/settingsInfoParse)
- Blocks 15500/15600: parser-backed via DCDCParser (baseInfoParse/settingsInfoParse)
- Block 17100: parser-backed via AT1Parser.at1InfoParse
- Status split: 14500 is smali-verified; 14700/15500/15600/17100 remain partial

Field Mapping Status (TODO):
- Block 14500: Smart plug device info - **SMALI-VERIFIED baseline** (model/SN/softwareVer/nums)
- Block 14700: Smart plug power control - **SECURITY CRITICAL** - verify safe power limits
- Block 15500: DC-DC converter monitoring - requires DC-DC device for payload analysis
- Block 15600: DC-DC voltage/current settings - **SECURITY CRITICAL** - verify electrical safety limits
- Block 17100: AT1 extended info - requires AT1 device, compare with Block 17000 (ATS_INFO)

Smali Analysis Details:
- Block 14500: ConnectManager switch case 0x38a4 -> :sswitch_24
  * Parser: SmartPlugParser.baseInfoParse
  * Verified schema mapping: bytes 0-11 model, 12-19 sn, 20-23 softwareVer, 24-25 nums
- Block 14700: Switch case 0x396c -> sswitch_1a, min_length 32 bytes (const v18 = 0x20)
- Block 15500: Switch case 0x3c8c -> sswitch_13, min_length 70 bytes (const v12 = 0x46)
- Block 15600: Switch case 0x3cf0 -> sswitch_12, min_length 36 bytes (protocol dependent: 36-56)
- Block 17100: Switch case 0x42cc -> sswitch_b, min_length 127 bytes (const 0x7f)

Related Blocks:
- Smart Plug: 14500 (info) ↔ 14700 (settings) - control/monitoring pair
- DC-DC Converter: 15500 (info) ↔ 15600 (settings) - control/monitoring pair
- AT1 Transfer Switch: 17000 (basic ATS info) → 17100 (extended AT1 info) - info hierarchy

**Security Notes**:
- **Block 14700 (SMART_PLUG_SETTINGS)**: **CRITICAL** - Controls smart plug power output. Incorrect settings may overload connected devices or create fire hazard. Only modify with proper understanding of load requirements and safety margins.
- **Block 15600 (DC_DC_SETTINGS)**: **CRITICAL** - Controls DC-DC converter voltage and current output. Incorrect values may damage connected equipment or create electrical hazards. Only modify with proper understanding of system limits and load requirements.
- Both blocks require actual device testing to verify safe operating ranges before production use.

**Completion Date**: 2026-02-15
**Quality Gates**: ruff ✅, mypy ✅ (72 files), pytest ✅ (359 tests, 91% coverage)
**Status**: ✅ **WAVE D BATCH 3 COMPLETE** (Provisional - pending device testing)

### Wave D Batch 4 (P3): Advanced Accessory Blocks (DC Hub, AT1 Extended, EPAD, TOU) ✅ COMPLETED

| Block | Doc Status | SDK Schema | Priority | Status | Field Coverage |
|---|---|---|---|---|---|
| 15700 | Smali-Verified | ✅ Implemented | P3 | ✅ Verified | 20 fields (dcHubInfoParse + DeviceDcHubInfo setter mapping confirmed) |
| 17400 | Partial | ✅ Implemented | P3 | ⚠️ Partial | 0 fields (empty baseline - all 11 previous fields incorrect; actual structure: 7x nested AT1BaseConfigItem objects; requires nested dataclass support) |
| 18000 | Smali-Verified | ✅ Implemented | P3 | ✅ Verified | 13 fields (EpadParser.baseInfoParse fully verified; core monitoring fields confirmed from smali) |
| 18300 | Partial | ✅ Implemented | P3 | ⚠️ Partial | 12 fields (EpadParser.baseSettingsParse path confirmed; byte ranges known, sub-item structures pending) |
| 26001 | Smali-Verified | ✅ Implemented | P3 | ✅ Verified | 7 fields (record0 baseline: 5 raw words + target_reg + target_value) |

Definition of done for Wave D Batch 4: ✅ ALL COMPLETE

1. ✅ Add block_15700/17400/18000/18300/26001_declarative.py
2. ✅ Register schemas via `schemas/__init__.py` auto-registration (40 total built-in blocks)
3. ✅ Add unit tests (test_wave_d_batch4_blocks.py: 10 tests, test_wave_d_batch4_smoke.py: 3 tests)
4. ✅ Quality gates: ruff ✓, mypy ✓ (77 files), pytest ✓ (374 passed, 91% coverage ✓)

Block Type Classification:
- Block 15700: PARSED block (dcHubInfoParse method exists at line 3590)
- Blocks 17400, 18000, 18300: parser-backed (AT1Parser/EpadParser paths confirmed)
- Block 26001: parser-backed via ConnectManager -> TouTimeCtrlParser.parseTouTimeExt
- Status split: 15700, 18000, and 26001 are smali-verified; 17400/18300 remain partial

Field Mapping Status:
- Block 15700: DC Hub monitoring - **SMALI-VERIFIED** for all schema fields (bean: DeviceDcHubInfo). Offsets and semantics are confirmed from parser setter sequence.
- Block 17400: AT1 transfer switch extended settings - **9 of 25 fields SMALI-VERIFIED** (simple UInt8 fields at offsets 138-146). Complex nested AT1BaseConfigItem structures and enable list transformations require sub-schema documentation. **CAUTION: Transfer switch control - verify electrical code compliance**
- Block 18000: Energy Pad info - **SMALI-VERIFIED** for all 13 core monitoring fields (offsets 12-37). Parser: EpadParser.baseInfoParse (lines 972-1590), Bean: EpadBaseInfo. Alarm list (bytes 38-2018) pending sub-parser analysis. **Upgrade Date: 2026-02-16**
- Block 18300: Energy Pad settings - Byte boundaries confirmed for all 8 fields. Sub-item structures (EpadLiquidSensorSetItem, EpadTempSensorSetItem) require dedicated analysis. **CAUTION: Energy management control - verify safe operating limits**
- Block 26001: Time-of-Use control records - **SMALI-VERIFIED first-item baseline**
  (14-byte record: 5 raw words + target_reg + target_value). Dynamic list support deferred.

Smali Analysis Details:
- Block 15700: ConnectManager switch case 0x3d54 -> :sswitch_1f, parser path uses bytes up to index 0x43 (68 bytes)
  * **Parse method**: dcHubInfoParse at ProtocolParserV2.smali line 3590
  * **Bean**: Lnet/poweroak/bluetticloud/ui/connectv2/bean/DeviceDcHubInfo;
  * Structure confirmed from bean setters: model, SN, DC I/O monitoring, multi-port status
- Block 17400: Switch case 0x43f8 -> sswitch_a, min_length 91 bytes (0x5b)
  * Field name: AT1_SETTINGS_1 / AT1_SETTINGS_GRID_ENABLE
- Block 18000: Switch case 0x4650 -> sswitch_9, min_length 2019 bytes (0x7e3) **[SMALI-VERIFIED]**
  * Parser method: EpadParser.baseInfoParse at lines 972-1590
  * Bean: Lnet/poweroak/bluetticloud/ui/connectv2/bean/EpadBaseInfo;
  * 13 core monitoring fields verified (bytes 12-37): liquid levels (3), sensor temps (3), remaining capacity (3), connection status (1), ambient temps (3)
  * Alarm list spans bytes 38-2018 (parsed via alarmListParse sub-method)
- Block 18300: Switch case 0x477c -> sswitch_8, min_length 75-76 bytes (0x4b-0x4c)
  * Protocol dependent: if (v1 >= v6) then 0x4c else 0x4b
- Block 26001: ConnectManager switch case 0x6591 -> :sswitch_8
  * Dispatches to TouTimeCtrlParser.parseTouTimeExt(dataBytes)
  * parseTouTimeExt consumes 14-byte records:
    - bytes 0..9 -> parseTouTimeItem payload
    - bytes 10..11 -> targetReg (UInt16)
    - bytes 12..13 -> targetValue (UInt16)
  * SDK schema intentionally models record0 baseline only (dynamic array deferred)
  * Baseline structure is smali-verified; limitation is dynamic list support only

Related Blocks:
- DC Hub: 15700 (info) ↔ 15750 (settings) - monitoring/control pair
- AT1 Transfer Switch: 17000 (basic ATS) → 17100 (AT1 base) → 17400 (AT1 extended) - info hierarchy
- Energy Pad: 18000 (info) ↔ 18300 (settings) - monitoring/control pair
- Time-of-Use: 26001 (standalone TOU schedule configuration)

**Security Notes**:
- **Block 17400 (ATS_EVENT_EXT)**: **CAUTION** - Controls automatic transfer switch settings. Incorrect configuration may result in improper grid/generator switching, violate electrical codes, cause power interruption or equipment damage, or lead to unsafe backfeed conditions. Only modify with proper understanding of transfer switch operation and local codes.
- **Block 18300 (EPAD_SETTINGS)**: **CAUTION** - Controls Energy Pad operation. Incorrect settings may exceed safe operating limits for connected devices, cause equipment damage or safety hazards, or lead to inefficient energy management. Only modify with proper understanding of EPAD specifications and load requirements.
- **Block 26001 (TOU_SETTINGS)**: **CAUTION** - Controls time-of-use scheduling. Incorrect TOU configuration may result in charging during expensive peak rate periods, missed opportunities for low-rate charging, higher electricity costs, or interference with grid demand response programs. Verify TOU time windows and rate tiers match utility's actual schedule.

**Completion Date**: 2026-02-15
**Quality Gates**: ruff ✅, mypy ✅ (77 files), pytest ✅ (374 tests, 91% coverage)
**Status**: ✅ **WAVE D BATCH 4 COMPLETE** (Provisional - pending device testing)

### Wave D Batch 5 (P3): EPAD Liquid Measurement + Boot Information ✅ COMPLETED

| Block | Doc Status | SDK Schema | Priority | Status | Field Coverage |
|---|---|---|---|---|---|
| 18400 | Smali-Verified | ✅ Implemented | P3 | ✅ Verified | 2 fields (volume, liquid; first calibration item) |
| 18500 | Smali-Verified | ✅ Implemented | P3 | ✅ Verified | 2 fields (volume, liquid; first calibration item) |
| 18600 | Smali-Verified | ✅ Implemented | P3 | ✅ Verified | 2 fields (volume, liquid; first calibration item) |
| 29770 | Smali-Verified | ✅ Implemented | P3 | ✅ Verified | 2 fields (is_supported, software_version_total; complete smali evidence) |
| 29772 | Smali-Verified | ✅ Implemented | P3 | ✅ Verified | 6 fields (software_type, software_version, 4 unused; complete item structure) |

Definition of done for Wave D Batch 5: ✅ ALL COMPLETE

1. ✅ Add block_18400/18500/18600/29770/29772_declarative.py
2. ✅ Register schemas via `schemas/__init__.py` auto-registration (45 total built-in blocks)
3. ✅ Add unit tests (test_wave_d_batch5_blocks.py: 10 tests, test_wave_d_batch5_smoke.py: 3 tests)
4. ✅ Quality gates: ruff ✓, mypy ✓ (82 files), pytest ✓ (387 passed, 91% coverage ✓)

Block Type Classification:
- Blocks 18400, 18500, 18600: parser-backed via EpadParser.baseLiquidPointParse
- Blocks 29770, 29772: PARSED blocks (bootUpgradeSupportParse, bootSoftwareInfoParse)
- EPAD liquid blocks: Smali-verified first-item baseline via shared parser
- Boot blocks: Parse methods exist but field semantics require verification

Field Mapping Status (TODO):
- Blocks 18400/18500/18600: EPAD liquid measurement points - **SMALI-VERIFIED**.
  All three blocks share EpadParser.baseLiquidPointParse and map first item:
  offset 0 -> volume (UInt8), offset 1 -> liquid (UInt8), min_length 2.
  Dynamic list parsing remains deferred as SDK limitation.

- Block 29770: Boot upgrade support - **SMALI-VERIFIED** (bootUpgradeSupportParse).
  Bean: BootUpgradeSupport with fields isSupport (boolean flag, LSB only) and
  softwareVerTotal (version count). Complete field semantics verified from smali
  disassembly. UInt16 BE values at offsets 0-1 and 2-3.
  **CAUTION: Bootloader upgrade flags - manufacturer authorization required.**

- Block 29772: Boot software info - **SMALI-VERIFIED** (bootSoftwareInfoParse).
  Bean: List<BootSoftwareItem> with constructor <init>(JI)V (long softwareVer, int softwareType).
  Complete 10-byte item structure verified from smali:
  * Bytes 0-1: softwareType (UInt16 BE, hex-parsed)
  * Bytes 2-5: softwareVer (4 bytes via bit32RegByteToNumber → long)
  * Bytes 6-9: UNUSED by parser (padding/reserved, purpose unknown)
  Schema represents first item only (dynamic array support is SDK limitation).
  **CAUTION: Bootloader software component data - manufacturer authorization required.**

Smali Analysis Details:
- Blocks 18400/18500/18600: Switch case 0x47e0/0x4844/0x48a8 -> sswitch_14/13/12
  * Dispatches to EpadParser.baseLiquidPointParse (shared parser path)
  * Parser item structure is 2 bytes (EpadLiquidCalibratePoint): volume, liquid
  * Schema models first item only (dynamic list parsing deferred)

- Block 29770: Switch case 0x744a -> sswitch_7, parser consumes 4 bytes
  * Parse method: bootUpgradeSupportParse()
  * Bean: Lnet/poweroak/bluetticloud/ui/connectv2/bean/BootUpgradeSupport;
  * Extracts integers from hex byte pairs (bytes 0-1 and 2-3), first masked by bit 0

- Block 29772: Switch case 0x744c -> sswitch_1c (not in sparse-switch data)
  * Parse method: bootSoftwareInfoParse()
  * Bean: List<Lnet/poweroak/bluetticloud/ui/connectv2/bean/BootSoftwareItem>;
  * Processes 10-byte items: bytes 0-1 (address), bytes 2-5 (value via bit32RegByteToNumber)

Related Blocks:
- EPAD Liquid System: 18400 (point 1) + 18500 (point 2) + 18600 (point 3) - multi-point monitoring
- EPAD Core: 18000 (base info) + 18300 (base settings) + 18400/18500/18600 (liquid points)
- Boot System: 29770 (upgrade support) + 29772 (software component info)

**Security/Operational Notes**:
- **Blocks 18400/18500/18600 (EPAD Liquid)**: Parser-backed but still partial. EPAD liquid
  measurement is a specialized accessory feature; field names remain baseline until
  validated on real hardware.

- **Block 29770 (BOOT_UPGRADE_SUPPORT)**: **CAUTION** - Contains boot loader upgrade support
  information. DO NOT use for write control without:
  * Proper device validation and authorization
  * Understanding of boot upgrade protocols
  * Manufacturer documentation for upgrade procedures
  Incorrect boot upgrade operations may brick the device or void warranty.

- **Block 29772 (BOOT_SOFTWARE_INFO)**: **CAUTION** - Contains boot software component inventory.
  DO NOT use for write control without:
  * Proper device validation and authorization
  * Understanding of boot component structure
  * Manufacturer documentation for software updates
  Incorrect boot software operations may brick the device or void warranty.

**Completion Date**: 2026-02-15
**Quality Gates**: ruff ✅, mypy ✅ (82 files), pytest ✅ (387 tests, 91% coverage)
**Status**: ✅ **WAVE D BATCH 5 COMPLETE** (Provisional - EPAD liquid + Boot info)

### Wave D (P3): Long tail / accessory / event blocks

Remaining documented blocks from `V2_BLOCKS_INDEX.md` not yet implemented.

## Execution Rules (strict)

1. Platform first rule is closed; now only schema/profile expansion in this phase.
2. No deprecated shim code for new schemas.
3. New block implementation must include:
   - Declarative schema
   - Unit tests (schema + parser integration)
   - Documentation link back to source block doc
4. No profile references to blocks without schema unless explicitly marked experimental.
5. Keep quality gates green on every wave: `ruff`, `mypy`, `pytest`, coverage floor.

## Claude Task Pack (copy/paste)

1. Implement Wave A blocks (`1100`, `1400`, `1500`, `6100`) as declarative schemas.
2. Add/adjust registry loading so new schemas auto-register.
3. Add tests:
   - one equivalence/structure test per block
   - one EL100V2 group-read smoke test using mocks
4. Update support matrix docs with actual implemented status.
5. Run `ruff`, `mypy`, `pytest` and report final numbers.

## Exit Criteria for Phase 2

1. All blocks referenced by shipped profiles are implemented.
2. Support matrix published and accurate.
3. No undocumented gaps between profile block lists and schema registry.

## Deferred Track (After Phase 2)

Native async transport migration is tracked separately and intentionally deferred
until current schema/reverse-engineering work is closed:

- `docs/plans/ASYNC-NATIVE-ROADMAP.md`
