# Block 15600 (DC_DC_SETTINGS) — Device Validation Gate

**Added**: Sprint 2026-02-17
**Status**: BLOCKED — Awaiting device testing
**Evidence source**: `docs/re/15600-EVIDENCE.md`
**Schema**: `bluetti_sdk/schemas/block_15600_declarative.py`
**Verification status**: `partial` (must not be upgraded without completing this gate)

---

## Why This Gate Exists

Block 15600 controls DC-DC converter voltage and current output. The smali
analysis (15600-EVIDENCE.md) proved offsets and parser routes for 46 fields
but could **not** determine scale factors for any voltage or current setpoint.

The parser uses raw `parseInt(16)` with no division. Block 15500 (the
companion read block) divides by `10.0f`. Whether 15600 write values use
the same scale is **not proven from smali alone** — the scale must be
confirmed by reading back a known-good device setting.

**Safety consequence**: Writing a raw integer that is 10× too large could
configure a dangerous output voltage or overcurrent limit. This block must
not be considered production-ready until the scale factors are confirmed.

---

## Critical Blockers (3)

### Blocker 1: voltSetDC1/2/3 scale factor

| Property | Value |
|----------|-------|
| Offsets | bytes 2-3 (DC1), 6-7 (DC2), 10-11 (DC3) |
| Parser | `parseInt(16)` — no division |
| Smali refs | 2002-2036 (DC1), 2089-2123 (DC2), 2167-2201 (DC3) |
| Current schema | `UInt16`, no transform, description says "UNKNOWN unit" |
| Evidence | Block 15500 uses `/ 10.0f` for voltDC1-3 reads |
| Hypothesis | Scale = 0.1 V (raw 480 = 48.0 V) — **NOT PROVEN** |

**Test required**: Read volt_dc1 from Block 15500 while device is running.
Read voltSetDC1 from Block 15600. Verify raw value × scale = measured voltage.

### Blocker 2: outputCurrentDC1/2/3 scale factor

| Property | Value |
|----------|-------|
| Offsets | bytes 4-5 (DC1), 8-9 (DC2), 12-13 (DC3) |
| Parser | `parseInt(16)` — no division |
| Smali refs | 2052-2086 (DC1), 2128-2162 (DC2), 2204-2238 (DC3) |
| Current schema | `UInt16`, no transform, description says "UNKNOWN unit" |
| Evidence | Block 15500 uses `/ 10.0f` for outputCurrentDC1-3 reads |
| Hypothesis | Scale = 0.1 A — **NOT PROVEN** |

**Test required**: Same approach as voltage: compare 15500 read with 15600
setpoint. If scale matches, document.

### Blocker 3: voltSet2DC3 scale factor

| Property | Value |
|----------|-------|
| Offset | bytes 22-23 |
| Parser | `parseInt(16)` — no division |
| Smali refs | 2243-2277 |
| Current schema | Not yet implemented in schema |
| Note | Second voltage setpoint for DC3 port only |

**Test required**: Confirm semantics and scale via device read-back.

---

## Current Schema State (2026-02-17)

**7 fields implemented** in `block_15600_declarative.py`:

| Field | Offset | Transform | Status |
|-------|--------|-----------|--------|
| `dc_ctrl` | 0 | `hex_enable_list:0:0` | PROVEN (smali 1943-1958) |
| `silent_mode_ctrl` | 0 | `hex_enable_list:0:1` | PROVEN (smali 1943-1971) |
| `factory_set` | 0 | `hex_enable_list:0:2` | PROVEN (smali 1943-1984) |
| `self_adaption_enable` | 0 | `hex_enable_list:0:3` | PROVEN (smali 1943-1999) |
| `volt_set_dc1` | 2 | none | PARTIAL (offset proven, scale unknown) |
| `output_current_dc1` | 4 | none | PARTIAL (offset proven, scale unknown) |
| `volt_set_dc2` | 6 | none | PARTIAL (offset proven, scale unknown) |

**23 TODO comments** for fields requiring extended packet (size > 4, > 26, > 54
words) or proven scale factors. These are documented in the schema file.

---

## Validation Protocol

### Prerequisites

1. DC-DC converter device connected and powered
2. Block 15500 (DC_DC_INFO) readable from device
3. Block 15600 readable from device
4. Safe operating environment — do **not** change setpoints on live loads
   without confirming scale factors first

### Step 1: Read-Back Scale Factor Test (READ-ONLY)

Objective: Confirm volt/current scale without writing.

```
1. Read Block 15500 (DC_DC_INFO) — parse volt_dc1 using existing scale (0.1)
2. Read Block 15600 (DC_DC_SETTINGS) — record raw voltSetDC1 value
3. Compare: if 15600_raw × 0.1 ≈ 15500_volt_dc1 → scale confirmed
4. Repeat for outputCurrentDC1 vs. 15500 current read
5. Document raw values and computed results
```

**Expected result if hypothesis correct**: 15600 raw value = 10 × (15500 read value).

### Step 2: Known-Setting Verification (OPTIONAL, low-risk)

Only if read-back test is inconclusive and the device is in a safe test state:

```
1. Note current voltSetDC1 setting (from Step 1)
2. Write a small adjustment (±1 raw unit) and re-read Block 15500
3. Measure actual output voltage if multimeter available
4. Record: raw_write → measured_voltage
5. Restore original value immediately
```

### Step 3: Extended Packet Verification

Objective: Confirm protocol version gates (list.size() conditions).

```
1. Capture raw Block 15600 packet bytes
2. Count 16-bit words (bytes / 2)
3. Record which condition gates apply:
   - ≤ 4 words: baseline only (dc_ctrl + voltSetDC1)
   - > 4 words: + outputCurrentDC1/2/3, voltSetDC2/3
   - > 26 words: + chgModeDC1-4, batteryCapacity, etc.
   - > 54 words: + sysPowerCtrl, remoteStartupSoc, etc.
4. Update schema min_length if current value (36) is wrong for device
```

---

## Upgrade Criteria

### To `partial` → `smali_verified`

All of the following must be satisfied:

- [ ] voltSetDC1 scale factor confirmed (0.1 V or other)
- [ ] outputCurrentDC1 scale factor confirmed (0.1 A or other)
- [ ] voltSet2DC3 semantics confirmed
- [ ] Schema transforms updated with confirmed scale values
- [ ] At least 1 extended-packet field confirmed (chgModeDC1 or batteryCapacity)
- [ ] `verification_status` and descriptions updated in schema
- [ ] Tests updated (new field counts, scale factor assertions)

### Intermediate `partial` upgrade (safe to do now)

The "4 fields" count in PHASE2 matrix is stale. The schema already has **7 fields**
(4 enable bits + 3 PARTIAL voltage/current setpoints). This can be updated
without device testing since it's a documentation correction only.

---

## Files to Update After Validation

1. `bluetti_sdk/schemas/block_15600_declarative.py`
   - Add `transform=("scale:0.1",)` (or confirmed factor) to volt/current fields
   - Add 23+ deferred fields from the evidence table
   - Change `verification_status` from `"partial"` to `"smali_verified"`

2. `docs/plans/PHASE2-SCHEMA-COVERAGE-MATRIX.md`
   - Update "4 fields" → "7 fields" (fix stale count)
   - Remove "3 CRITICAL blockers" note once resolved
   - Change status from `⚠️ Partial` to `✅ Verified`

3. `tests/unit/test_wave_d_batch3_blocks.py`
   - Update field count assertions to match new schema

4. This file: update status from BLOCKED → COMPLETE

---

## Evidence References

| Artifact | Location | Notes |
|----------|----------|-------|
| Complete field table (46 fields) | `docs/re/15600-EVIDENCE.md` | All offsets/transforms |
| Smali parser source | `DCDCParser.settingsInfoParse` lines 1780-3195 | Block 15500 for comparison |
| Scale comparison target | `DCDCParser.baseInfoParse` lines ~100-800 | Uses `/ 10.0f` |
| Current schema | `bluetti_sdk/schemas/block_15600_declarative.py` | 7 fields, partial |
| PHASE2 matrix entry | `docs/plans/PHASE2-SCHEMA-COVERAGE-MATRIX.md` line 195 | Needs "4→7" fix |
