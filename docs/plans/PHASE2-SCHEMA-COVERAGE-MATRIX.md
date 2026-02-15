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
