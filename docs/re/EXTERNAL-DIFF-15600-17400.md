# External Differential Analysis: Blocks 15600 and 17400

**Date:** 2026-02-17
**Purpose:** Assess whether the three external repositories resolve, partially resolve, or fail to
resolve the specific open blockers for SDK blocks 15600 (DC_DC_SETTINGS) and 17400 (ATS_EVENT_EXT).

---

## 1. Block 15600 (DC_DC_SETTINGS) Differential Analysis

### 1.1 Background

Block 15600 (decimal) = 0x3CF0 (hex). Current SDK status: partial. Seven fields implemented; three
critical blockers remain open due to unknown scale factors for voltage and current setpoint fields.
A fourth semantic blocker exists for `voltSet2DC3`.

Working hypothesis from smali analysis: block 15500 (DC_DC_INFO reads) uses `/10.0f` for
`dcOutputVolt` and `dcOutputCurrent`. If setpoints follow the same convention, scale=1 (/10) applies.

---

### Blocker 1: voltSetDC1 / voltSetDC2 / voltSetDC3 — Scale Unknown

**Question:** Do external sources confirm whether DC voltage setpoint registers use scale=1 (/10),
scale=2 (/100), or raw integer?

| Repository | Evidence Found | Evidence Type | Verdict |
|---|---|---|---|
| warhammerkid/bluetti_mqtt | None | — | Not resolved |
| mariolukas/Bluetti_ESP32_Bridge | None | — | Not resolved |
| bluetti-official/bluetti-home-assistant | None | — | Not resolved |

**Direct evidence:** Absent from all three repositories. No DC-DC voltage setpoint register is
defined, named, or referenced in any external codebase examined.

**Indirect evidence (labeled as such):** Both Repo 1 and Repo 2 confirm that every DC voltage
read register uses scale=1 (/10 → Volts):
- `internal_dc_input_voltage` (reg 86 / offset 0x56): scale=1, confirmed on AC300, EP500P, EB3A,
  AC200M across both repos independently.
- `pack_voltage` (reg 98 / offset 0x5C): scale=1 or scale=2 depending on device (see table in
  EXTERNAL-EVIDENCE-TOP3.md).

Combined with the smali finding that block 15500 DC read fields use `/10.0f`, indirect support
for `scale=1` on block 15600 voltage setpoints is moderate but not conclusive.

**Verdict:** UNRESOLVED. External evidence does not confirm or deny the scale factor. The scale=1
(/10) hypothesis remains the best-supported working assumption, backed by indirect cross-repo
consistency. Cannot be closed without direct device observation or additional smali/APK evidence.

---

### Blocker 2: outputCurrentDC1 / outputCurrentDC2 / outputCurrentDC3 — Scale Unknown

**Question:** Do external sources confirm whether DC current setpoint registers use scale=1 (/10),
scale=2 (/100), or raw integer?

| Repository | Evidence Found | Evidence Type | Verdict |
|---|---|---|---|
| warhammerkid/bluetti_mqtt | None | — | Not resolved |
| mariolukas/Bluetti_ESP32_Bridge | None | — | Not resolved |
| bluetti-official/bluetti-home-assistant | None | — | Not resolved |

**Direct evidence:** Absent from all three repositories. No DC-DC current setpoint register appears.

**Indirect evidence (labeled as such):**
- Repo 1 (`bluetti_mqtt/core/devices/ac300.py` and others): `internal_dc_input_current` (reg 88)
  uses scale=1 (/10 → A) on AC300, EP500, EP500P. Scale=2 (/100 → A) on AC200M only.
- Repo 2 (`DEVICE_EP500P.h`, `Device_AC300.h`): `INTERNAL_DC_INPUT_CURRENT` (offset 0x58):
  scale=1 confirmed independently on AC300 and EP500P.
- Pattern: current read fields on mainstream devices (AC300, EP500P) use scale=1. AC200M is the
  outlier at scale=2.

If setpoint registers follow the same device-specific pattern, AC300/EP500P-family devices should
use scale=1 for current setpoints. However, setpoint registers may use different precision than
read registers — this cannot be assumed without evidence.

**Verdict:** UNRESOLVED. Same status as Blocker 1. Scale=1 is the best indirect inference for
mainstream devices; AC200M may differ. Requires direct device test or APK analysis.

---

### Blocker 3: voltSet2DC3 — Semantics Unknown

**Question:** Do external sources clarify what `voltSet2DC3` means (second voltage threshold for
DC channel 3? hysteresis value? reconnect voltage?)

| Repository | Evidence Found | Evidence Type | Verdict |
|---|---|---|---|
| warhammerkid/bluetti_mqtt | None | — | Not resolved |
| mariolukas/Bluetti_ESP32_Bridge | None | — | Not resolved |
| bluetti-official/bluetti-home-assistant | None | — | Not resolved |

**Direct evidence:** Absent. No equivalent field or documentation exists in any external repository.

**Indirect evidence:** None. This field's semantics cannot be inferred from external sources.
The naming pattern suggests a secondary voltage setpoint (e.g., reconnect threshold vs. disconnect
threshold) for DC channel 3, but this is speculative.

**Verdict:** UNRESOLVED. No external evidence available. Requires either device testing with
live value manipulation, or further smali/APK decompilation to find UI labels or validation ranges.

---

### 1.2 Block 15600 Structural Context

Block address 15600 decimal = 0x3CF0 hex. This address is architecturally unreachable in the
{page, offset} BLE protocol used by Repo 2 (max addressable = 0xFF, 0xFF = 255, 255). This
confirms that block 15600 exists in a separate protocol layer — likely a higher-level application
protocol above the raw BLE service. This explains why no open-source BLE implementation has
encountered these registers and why device testing is the only viable path to direct confirmation.

---

## 2. Block 17400 (ATS_EVENT_EXT) Differential Analysis

### 2.1 Background

Block 17400 (decimal) = 0x43F8 (hex). Current SDK status: partial. 30 sub-fields proven after
forensic audit. Six proven fields remain absent from the SDK implementation. These are AT1
(Automatic Transfer Switch) configuration fields related to transfer switch type selection,
inter-device linkage, and forced enable controls.

---

### Field Group A: SL2 / SL3 / SL4 type fields — AT1 Transfer Switch Type Enumerations

**Question:** Do external sources define or reference the transfer switch type enum values for
secondary slots (SL2, SL3, SL4)?

| Repository | Evidence Found | Notes |
|---|---|---|
| warhammerkid/bluetti_mqtt | None | No ATS/transfer switch fields anywhere in codebase |
| mariolukas/Bluetti_ESP32_Bridge | None | No ATS fields in any device header |
| bluetti-official/bluetti-home-assistant | Not supported | GitHub issue #52 explicitly confirms AT1 not supported |

**Verdict:** UNRESOLVED. The cloud integration's explicit confirmation that AT1 is unsupported
(issue #52) is the only external statement about these fields — and it is a negative statement.
No enum values, no field names, no type codes available from any external source.

---

### Field Group B: linkage_enable — Inter-Device Linkage Control

**Question:** Do external sources define or reference `linkage_enable` or equivalent field?

| Repository | Evidence Found | Notes |
|---|---|---|
| warhammerkid/bluetti_mqtt | None | — |
| mariolukas/Bluetti_ESP32_Bridge | None | — |
| bluetti-official/bluetti-home-assistant | None | DC hub controls confirmed missing (issue #32) |

**Verdict:** UNRESOLVED. GitHub issue #32 in Repo 3 confirms DC hub controls are missing from
the cloud integration, which may encompass linkage control. No positive evidence exists anywhere.

---

### Field Group C: force_enable — Forced AT1 Activation

**Question:** Do external sources define or reference `force_enable` or equivalent field?

| Repository | Evidence Found | Notes |
|---|---|---|
| warhammerkid/bluetti_mqtt | None | — |
| mariolukas/Bluetti_ESP32_Bridge | None | — |
| bluetti-official/bluetti-home-assistant | None | — |

**Verdict:** UNRESOLVED. No external evidence whatsoever.

---

### Field Group D: max_current — UInt8 vs UInt16 Type Question

**Question:** Do external sources indicate whether `max_current` in ATS context is 8-bit or 16-bit?

| Repository | Evidence Found | Notes |
|---|---|---|
| warhammerkid/bluetti_mqtt | Partial analog | All current fields are UInt16 (16-bit) in flat register space |
| mariolukas/Bluetti_ESP32_Bridge | Partial analog | All parsed current fields use 16-bit reads |
| bluetti-official/bluetti-home-assistant | None | — |

**Indirect evidence (labeled as such):** Both BLE repos use 16-bit (uint16) reads for all
confirmed current fields. No 8-bit current field appears in either codebase. This provides
weak indirect support for UInt16 for `max_current`, but ATS configuration registers may differ
from measurement registers.

**Verdict:** UNRESOLVED DIRECTLY. Indirect support for UInt16 (16-bit) based on universal 16-bit
usage in confirmed current fields. Cannot be confirmed without direct block 17400 field analysis.

---

### 2.2 Block 17400 Structural Context

Block address 17400 decimal = 0x43F8 hex. Same structural constraint as block 15600: this address
exceeds the 8-bit offset limit of the {page, offset} BLE protocol in Repo 2 (max 0xFF = 255).
Block 17400 is architecturally unreachable from the open-source BLE layer. The official Bluetti
cloud API (Repo 3) does not expose AT1 functionality. This means the ATS configuration registers
are accessible only through the official Bluetti app's proprietary protocol — the same higher-level
layer where block 15600 resides.

---

## 3. Prioritized Backlog

Items are grouped by whether they can be resolved without a physical device and the specific
action recommended.

---

### Group A: Can Close Without Device (APK/Smali Analysis Sufficient)

These items have clear paths to resolution through further static analysis of the Bluetti APK.

**A1 — Confirm scale=1 for voltSetDC registers (HIGHEST PRIORITY)**
- What to do: Search smali for block 15600 write handlers. Look for division operations adjacent
  to voltSetDC field writes. The pattern `div-float/2addr v0, v1` with literal `10.0f` would
  confirm scale=1.
- Why: Scale=1 is the strong indirect inference from all external repos. A single smali hit
  would close Blocker 1 definitively.
- External support: Indirect — all confirmed DC voltage reads use /10 (Repo 1, Repo 2, Repo 3).

**A2 — Confirm scale=1 for outputCurrentDC registers**
- What to do: Same APK search as A1 but for current setpoint write handlers. Also check if
  any UI validation (min/max value hints) reveals expected range (e.g., max=100 would suggest
  raw integer amps; max=1000 would suggest /10 → A).
- Why: Resolves Blocker 2. Same indirect support as A1.
- External support: Indirect — DC input current reads use scale=1 on AC300/EP500P (Repo 1 + Repo 2).

**A3 — Resolve voltSet2DC3 semantics via UI label search**
- What to do: Search smali/resource strings for labels associated with the DC channel 3 voltage
  settings screen. Look for strings like "reconnect voltage", "hysteresis", or "second threshold".
- Why: Resolves Blocker 3. UI label is the fastest non-device path to semantic clarity.
- External support: None.

**A4 — Enumerate SL2/SL3/SL4 type values from APK resources**
- What to do: Search smali for spinner/dropdown arrays associated with AT1 slot configuration.
  Enum values are often stored as string arrays in resources.
- Why: Would close Field Group A for block 17400 without device.
- External support: None — only available path is APK analysis.

**A5 — Confirm linkage_enable field presence in block 17400 via smali write handler**
- What to do: Search smali for writes to block 17400 with field offsets beyond the 30 already
  confirmed. Compare against SDK's "6 absent fields" list.
- Why: Confirms whether fields exist before implementing them.
- External support: None direct; issue #32 in Repo 3 confirms linkage is a known missing feature.

**A6 — Resolve max_current UInt8 vs UInt16 via smali type analysis**
- What to do: Find smali read handler for max_current field in block 17400. Check whether a
  byte read (int-to-byte) or short read (int-to-short) is used.
- Why: Type mismatch would cause silent data corruption. Low effort to confirm.
- External support: Indirect — both BLE repos use 16-bit uniformly for current fields.

---

### Group B: Requires Device Test (Live Hardware Needed)

These items cannot be reliably resolved through static analysis alone and require a live device
for validation.

**B1 — Validate voltSetDC scale factor with live write-then-read cycle (CRITICAL)**
- What to do: Write a known voltage setpoint (e.g., 48.0 V) to voltSetDC1. Read back via
  block 15500 dcOutputVolt. If read-back shows 480 (raw), confirm scale=1. If 4800, confirm scale=2.
- Why: Direct confirmation closes Blocker 1 with certainty. No indirect inference required.
- Device needed: Any AC300, EP500, or EP500P with DC port configured.

**B2 — Validate outputCurrentDC scale factor with live write-then-read cycle**
- What to do: Same procedure as B1 for current setpoints. Write known current value; verify
  block 15500 dcOutputCurrent read-back matches at expected scale.
- Why: Direct confirmation closes Blocker 2.
- Device needed: Same as B1.

**B3 — Clarify voltSet2DC3 via UI observation**
- What to do: Navigate Bluetti app to DC channel 3 settings. Record all displayed voltage
  fields and their labels. Map displayed labels to register offsets in block 15600.
- Why: Resolves Blocker 3 semantic ambiguity without needing to write to device.
- Device needed: Any device with 3 DC output channels (AC300 or equivalent).

**B4 — Validate AT1 force_enable behavior via toggle observation**
- What to do: If AT1 accessory is available, toggle force_enable via block 17400 write and
  observe physical transfer switch behavior.
- Why: Confirms field semantics and that the field is not a no-op.
- Device needed: AC300 or EP500 with AT1 transfer switch accessory attached.

**B5 — Validate linkage_enable behavior via multi-device test**
- What to do: Configure two devices with linkage_enable set vs. unset. Observe whether AC
  output behavior changes when primary device load changes.
- Why: Semantics are purely behavioral — cannot be inferred from static analysis.
- Device needed: Two AC300 or EP500 units.

**B6 — Confirm SL2/SL3/SL4 type enum values via AT1 multi-slot configuration**
- What to do: Configure each AT1 slot to a known type (Generator, Grid, Solar). Read back
  raw register values from block 17400 at the SL2/SL3/SL4 type offsets. Map raw values to
  configured types.
- Why: Enum mapping requires hardware to generate known ground-truth states.
- Device needed: AC300 or EP500 with AT1 accessory; multiple input sources.

**B7 — Confirm max_current effective range via current-limited load test**
- What to do: Set max_current to progressively higher values while monitoring actual output
  current. Identify the unit (A vs 0.1A) from the value that corresponds to observed current limit.
- Why: Validates the UInt8/UInt16 decision and confirms field is functional.
- Device needed: AC300 or EP500 with controllable load.

---

### Summary Priority Matrix

| Priority | Item | Group | Effort | Blocker Resolved |
|---|---|---|---|---|
| 1 | A1 — voltSetDC scale via smali | A (no device) | Low | Blocker 1 |
| 2 | A2 — outputCurrentDC scale via smali | A (no device) | Low | Blocker 2 |
| 3 | B1 — voltSetDC scale via device | B (device) | Medium | Blocker 1 (definitive) |
| 4 | B2 — outputCurrentDC scale via device | B (device) | Medium | Blocker 2 (definitive) |
| 5 | A3 — voltSet2DC3 semantics via string search | A (no device) | Low | Blocker 3 |
| 6 | A4 — SL2/SL3/SL4 enum via APK resources | A (no device) | Medium | Block 17400 Field Group A |
| 7 | A5 — linkage_enable presence confirmation | A (no device) | Low | Block 17400 Field Group B |
| 8 | A6 — max_current type via smali | A (no device) | Low | Block 17400 Field Group D |
| 9 | B3 — voltSet2DC3 via UI observation | B (device) | Low | Blocker 3 (definitive) |
| 10 | B4 — force_enable AT1 behavior | B (device) | High | Block 17400 Field Group C |
| 11 | B6 — SL2/SL3/SL4 enum via device | B (device) | High | Block 17400 Field Group A (definitive) |
| 12 | B5 — linkage_enable via multi-device | B (device) | Very High | Block 17400 Field Group B |
| 13 | B7 — max_current range via load test | B (device) | High | Block 17400 Field Group D |
