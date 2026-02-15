# Wave C Reverse-Engineering Backlog

Status: Closed
Scope: finalize Wave C provisional schemas with smali-verified field maps.

All six blocks have been updated with smali-verified field mappings from ProtocolParserV2.smali.

## Why this exists

Wave C blocks are currently implemented as minimal/estimated schemas to keep
coverage moving, but they are not fully reverse-engineered. This backlog is the
"do not forget" checklist before marking Wave C truly complete.

## Priority Order

1. Block `6300` (PACK_BMU_READ) - high complexity, dynamic structure
2. Block `12161` (IOT_ENABLE_INFO) - control/status semantics
3. Block `1700` (METER_INFO) - monitoring correctness
4. Block `3500` (TOTAL_ENERGY_INFO) - long-term energy data correctness
5. Block `3600` (CURR_YEAR_ENERGY) - annual energy data correctness
6. Block `720` (OTA_STATUS) - firmware flow visibility

## Per-block Tasks

### Block 6300 - `parsePackBMUInfo` / `parsePackSubPackInfo` ✅

**Status**: Smali-verified (lines 28435-28850)

1. ✅ Extracted full offset formulas for dynamic multi-BMU parsing
2. ✅ Verified software version gate (protocol >= 0x7DA/2010)
3. ✅ Defined strategy: Single-BMU baseline with documented formulas for multi-BMU extension
4. ✅ Updated required flags (serial_number, fault_data: False→True)
5. ✅ Added comprehensive documentation with example calculations

### Block 12161 - `parseIOTEnableInfo` ✅

**Status**: Smali-verified (lines 15526-15800)

1. ✅ Recovered full IoTCtrlStatus field map using hexStrToEnableList bit extraction
2. ✅ Replaced 3 placeholder fields with 2 bit-packed UInt16 control flags
3. ✅ Documented bit positions (WifiSTA, Enable4G, EthernetEnable, WifiMeshEnable, DefaultMode, BleMatchMode)
4. ✅ Updated tests with correct field names and structure

### Block 1700 - `parseInvMeterInfo` ✅

**Status**: Smali-verified (lines 24757-25100)

1. ✅ Recovered full CT meter structure: model, sn, status, sys_time, 3-phase array, aggregates
2. ✅ Identified Float32 encoding (bit32HexSwap + hexToFloat) for all power/voltage/current values
3. ✅ Stored raw UInt32 values with documented conversion requirement
4. ✅ Updated min_length (4→138) to accommodate full 3-phase + aggregate structure
5. ✅ Updated tests with correct field names (meter_power→model, meter_current→sn)

### Block 3500 - `parseTotalEnergyInfo` ✅

**Status**: Smali-verified (lines 32107-32300)

1. ✅ Recovered exact InvEnergyStatistics structure (energy_type + total + 15-year array)
2. ✅ Confirmed units/scales (UInt32 with scale 0.1 kWh for all energy values)
3. ✅ Implemented first 3 yearly entries (year0-2) with documented full array structure
4. ✅ Updated min_length (16→96) to match 15-year array size
5. ✅ Updated tests with correct field names (total_pv_energy→total_energy)

### Block 3600 - `parseCurrYearEnergy` ✅

**Status**: Smali-verified (lines 10784-11000)

1. ✅ Recovered exact InvCurrentYearEnergy structure (energy_type + year + total + 12 months + 31 days)
2. ✅ Confirmed scale/units (UInt32 with scale 0.1 kWh for monthly, UInt16 for daily)
3. ✅ Implemented first 3 monthly entries (month0-2) with documented full array structure
4. ✅ Updated min_length (16→56) to match 12-month array size
5. ✅ Updated tests with correct field names (year_pv_energy→total_year_energy)

### Block 720 - `parseOTAStatus` ✅

**Status**: Smali-verified (lines 28228-28430)

1. ✅ Recovered OTAStatus structure (ota_group + 16 file entries, each 6 bytes)
2. ✅ Implemented file0 fields: ota_status, progress, result, upgrade_id, file_num, ctrl_flags
3. ✅ Documented full 16-file array structure with 6-byte repeating pattern
4. ✅ Updated min_length (2→8) to match documented file0 structure
5. ✅ Updated tests with correct field names (ota_status→ota_group, ota_progress→file0_progress)

## Exit Criteria (Wave C Re-closure) ✅

1. ✅ All six blocks have smali-verified field maps with documented source line refs
2. ✅ No "estimated" fields remain in Wave C schemas - all replaced with smali-verified structure
3. ✅ TODO(smali-verify) markers removed - all schemas reference specific smali parse methods
4. ✅ Unit tests updated for all blocks (16/16 passing) with correct field structure
5. ✅ `PHASE2-SCHEMA-COVERAGE-MATRIX.md` ready to update from `Provisional` to `Smali-Verified`

**Completion Date**: 2026-02-15
**Quality Gates**: ruff ✅, mypy ✅ (57 files), pytest ✅ (16 Wave C tests)
**Commit**: 46f78e9 (feat(protocol): close Wave C RE backlog with smali-verified schemas)
