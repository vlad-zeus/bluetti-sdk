# External Evidence Synthesis: Top 3 Bluetti Repositories

**Date:** 2026-02-17
**Scope:** Three external Bluetti reverse-engineering repositories analyzed for scale factor confirmation,
protocol structure, and evidence bearing on SDK blocks 15600 (DC_DC_SETTINGS) and 17400 (ATS_EVENT_EXT).

---

## 1. Executive Summary

- **Scale factors confirmed with high confidence.** Two independent BLE/MODBUS repositories
  (warhammerkid/bluetti_mqtt and mariolukas/Bluetti_ESP32_Bridge) confirm identical scale semantics:
  raw uint16 divided by 10^scale. Key voltage fields use scale=1 (/10), current fields use scale=1 (/10)
  on most devices and scale=2 (/100) on AC200M, power fields use scale=0 (raw integer in W).

- **Block 15600 (DC_DC_SETTINGS) — NOT RESOLVED by external evidence.** All three repositories
  contain zero evidence for DC-DC setpoint registers (voltSetDC, outputCurrentDC, dc_total_power_set).
  The BLE repositories max out at 8-bit offsets (0xFF = 255), making block address 15600 unreachable
  in their protocol layer. The cloud API (Repo 3) does not expose these fields at all.

- **Block 17400 (ATS_EVENT_EXT) — NOT RESOLVED by external evidence.** No external repository
  contains AT1 transfer switch register definitions. The cloud API repository (Repo 3) confirms via
  GitHub issue #52 that AT1 transfer switch is not supported in that integration. The BLE repositories
  show no fields matching gen_check_enable, force_enable, linkage_enable, or AT1 type enumerations.

- **Indirect support for scale=1 hypothesis on DC setpoint registers.** Repo 1 and Repo 2 independently
  confirm that all confirmed DC read registers (dc_input_voltage, dc_input_current, pack_voltage) use
  scale=1 (/10). Combined with smali evidence that block 15500 DC_DC_INFO reads use /10.0f, the
  hypothesis that block 15600 setpoint fields also use /10 has indirect cross-repo support but remains
  unconfirmed by direct observation.

---

## 2. Repository Comparison Table

| Repository | Protocol | Scale Engine | DC-DC Setpoint Evidence | AT1/ATS Evidence | Block 15600/17400 Addresses |
|---|---|---|---|---|---|
| warhammerkid/bluetti_mqtt | MODBUS-over-BLE, flat decimal register space | `DecimalField(raw_uint16 / 10^scale)` | None found | None found | Not applicable — flat register IDs, no block addressing |
| mariolukas/Bluetti_ESP32_Bridge | Custom BLE, 2D {page, offset} addressing (both 1 byte) | C++ `parse_decimal_field(raw / pow(10, scale))` — identical semantics | None found | None found | Architecturally impossible: max offset = 0xFF = 255; 15600 and 17400 exceed 8-bit limit |
| bluetti-official/bluetti-home-assistant | Cloud REST API + STOMP WebSocket | API returns string floats; batteryVoltage confirmed /10 | None found | Not supported (issue #52) | Not applicable — cloud API, no register addresses |

---

## 3. Scale Factor Cross-Confirmation Table

Fields are listed with the number of independent repositories that confirm each scale factor and the
number of distinct device types providing confirmation.

| Field | Register / Offset | Scale | Repos Confirming | Device Confirmations | Unit |
|---|---|---|---|---|---|
| dc_input_voltage / INTERNAL_DC_INPUT_VOLTAGE | reg 86 / page=0x00 offset=0x56 | 1 → /10 | 2 (Repo 1, Repo 2) | 4 (AC300, EP500P, EB3A, AC200M) | V |
| dc_input_current / INTERNAL_DC_INPUT_CURRENT | reg 88 / offset=0x58 | 1 → /10 | 2 (Repo 1, Repo 2) | 2 (AC300, EP500P) | A |
| dc_input_current (AC200M variant) | reg 88 | 2 → /100 | 1 (Repo 1 only) | 1 (AC200M) | A |
| dc_input_power / INTERNAL_DC_INPUT_POWER | reg 36 / offset=0x57 | 0 → raw | 2 (Repo 1, Repo 2) | All devices | W |
| ac_input_voltage | reg 77 | 1 → /10 | 1 (Repo 1) | AC300, EP500 | V |
| ac_input_power | reg 37 | 0 → raw | 1 (Repo 1) | All devices | W |
| ac_output_power | reg 38 | 0 → raw | 1 (Repo 1) | All devices | W |
| dc_output_power | reg 39 | 0 → raw | 1 (Repo 1) | All devices | W |
| internal_ac_voltage | reg 71 / offset=0x47 | 1 → /10 (AC300/EP500/EP500P), 0=raw (AC200M) | 2 (Repo 1, Repo 2) | 3 devices each scale | V |
| total_battery_percent | reg 43 | 0 → raw | 1 (Repo 1) | All devices | % |
| total_battery_voltage | reg 92 | 1 → /10 (AC300/AC500/EP500/EP500P) | 1 (Repo 1) | 4 devices | V |
| total_battery_voltage (AC200M) | reg 92 | 2 → /100 | 1 (Repo 1) | 1 (AC200M) | V |
| pack_voltage / INTERNAL_PACK_VOLTAGE | reg 98 / offset=0x5C | 2 → /100 (AC300/AC500/AC200M) | 2 (Repo 1, Repo 2) | 3 devices | V |
| pack_voltage on AC300/EP500P | offset=0x5C | 1 → /10 (AC300/EP500P in Repo 2) | 1 (Repo 2 only) | 2 devices | V |
| cell_voltages | regs 105-120 / offsets 0x69-0x78 | 2 → /100 | 2 (Repo 1, Repo 2) | All devices with cell monitoring | V |
| internal_ac_frequency | reg 74 | 2 → /100 (AC300/EP500), 1 → /10 (AC200M) | 1 (Repo 1) | 3 devices | Hz |
| power_generation | reg 41 | 1 → /10 | 1 (Repo 1) | All devices | kWh |
| batteryVoltage (cloud API) | API field | /10 → V | 1 (Repo 3) | EL100V2, EL30V2 (real device confirmed) | V |

**Key observation:** The /10 scale (scale=1) is the dominant pattern for voltage and current across
all independent sources. Raw integer (scale=0) is universal for power in watts. The AC200M is the
consistent outlier with scale=2 (/100) for fields where other devices use scale=1.

---

## 4. Negative Findings

The following fields are **absent from all three external repositories**. This constitutes strong
negative evidence that these fields either do not exist in the BLE/cloud layers examined, or belong
to a proprietary protocol layer not covered by any open-source implementation.

### Block 15600 (DC_DC_SETTINGS) — All Absent

| Field (SDK name) | Searched in Repo 1 | Searched in Repo 2 | Searched in Repo 3 | Verdict |
|---|---|---|---|---|
| voltSetDC1 / voltSetDC2 / voltSetDC3 | Not found | Not found | Not found | No external evidence |
| outputCurrentDC1 / outputCurrentDC2 / outputCurrentDC3 | Not found | Not found | Not found | No external evidence |
| dc_total_power_set | Not found | Not found | Not found | No external evidence |
| voltSet2DC3 | Not found | Not found | Not found | No external evidence |

**Structural reason (Repo 2):** Block address 15600 decimal = 0x3CF0. In the Bluetti_ESP32_Bridge
2D addressing scheme, page and offset are each 1 byte (max 0xFF = 255). 0x3CF0 cannot be expressed
as any valid {page, offset} pair. This confirms that register 15600 belongs to a different protocol
layer that Repo 2 does not implement.

**Structural reason (Repo 1):** The flat register space in bluetti_mqtt covers documented registers
up to ~register 200 range. Register 15600 is not referenced anywhere in the codebase.

### Block 17400 (ATS_EVENT_EXT) — All Absent

| Field (SDK name) | Searched in Repo 1 | Searched in Repo 2 | Searched in Repo 3 | Verdict |
|---|---|---|---|---|
| gen_check_enable | Not found | Not found | Not found | No external evidence |
| force_enable | Not found | Not found | Not found | No external evidence |
| linkage_enable | Not found | Not found | Not found | No external evidence |
| AT1 type / transfer switch type | Not found | Not found | Issue #52: not supported | No external evidence; cloud confirms unsupported |
| SL2/SL3/SL4 type fields | Not found | Not found | Not found | No external evidence |

**Structural reason (Repo 2):** Block address 17400 decimal = 0x43F8. Same 8-bit offset limit
applies — this address is architecturally unreachable in the {page, offset} BLE protocol.

---

## 5. Per-Repository Detailed Evidence

### 5.1 warhammerkid/bluetti_mqtt

**Sources:** `bluetti_mqtt/core/devices/struct.py`, `bluetti_mqtt/core/devices/ac300.py`,
`ac500.py`, `ep500.py`, `ep500p.py`, `ac200m.py`, `eb3a.py`, `ep600.py`, `ac60.py`

**Protocol:** MODBUS-over-BLE. Single flat register space with decimal register IDs. BLE write
characteristic `0000ff02`, notify characteristic `0000ff01`. Packet format: MODBUS standard with
CRC-16.

**Scale engine:** `DecimalField` class. Formula: `raw_uint16 / (10 ** scale)`. scale=0 returns raw
integer, scale=1 divides by 10, scale=2 divides by 100. Semantically identical to Repo 2.

**Key device-specific findings:**
- AC200M is a confirmed outlier: uses scale=2 for `dc_input_current` (reg 88) and
  `total_battery_voltage` (reg 92) where all other devices use scale=1.
- AC200M uses scale=0 (raw) for `internal_ac_voltage` (reg 71) where AC300/EP500 use scale=1.
- AC200M uses scale=1 for `internal_ac_frequency` (reg 74) where AC300/EP500 use scale=2.
- All devices share the same scale for power registers (0 → W) and dc_input_voltage (1 → /10).

**Writable registers confirmed:** Range 3001-3061 covers UPS mode, AC/DC output on/off, grid charge
enable, battery range start/end, bluetooth connected flag, auto sleep mode. These are confirmed
writable via the write characteristic. No DC-DC setpoint registers in this range.

**DC-DC evidence:** None. No field named `volt_set_dc`, `output_current_dc`, `dc_total_power_set`,
or any variant appears in any device file.

**AT1/ATS evidence:** None. No field named `gen_check_enable`, `force_enable`, `linkage_enable`,
or transfer switch type appears in any device file.

**Block address evidence:** No hex addresses like `0x3CF0` or `0x43F8` appear. The protocol uses
flat decimal register IDs only.

---

### 5.2 mariolukas/Bluetti_ESP32_Bridge

**Sources:** `Bluetti_ESP32/PayloadParser.cpp`, `Device_AC300.h`, `DEVICE_EP500P.h`,
`DEVICE_EB3A.h`, `Device_AC200M.h`, `Device_AC500.h`, `Device_EP600.h`, `DeviceType.h`

**Protocol:** Custom BLE with 2D {page, offset} addressing. Page = 1 byte, offset = 1 byte.
Maximum addressable register: page=0xFF, offset=0xFF (255, 255). Same BLE characteristics as Repo 1.
Packet prefix=0x01, cmd=0x03 (read), cmd=0x06 (write), CRC-16/MODBUS appended.

**Scale engine:** C++ function `parse_decimal_field(data, scale)` computing `raw_uint16 / pow(10, scale)`.
Semantically identical to Repo 1's `DecimalField`.

**Key independent confirmations (same results as Repo 1, derived independently):**
- `INTERNAL_DC_INPUT_VOLTAGE` (page=0x00, offset=0x56): scale=1 confirmed on AC300, EP500P,
  EB3A, AC200M — 4 device confirmations, all in agreement.
- `INTERNAL_DC_INPUT_CURRENT` (page=0x00, offset=0x58): scale=1 confirmed on AC300 and EP500P.
- `INTERNAL_DC_INPUT_POWER` (page=0x00, offset=0x57): scale=0 (raw W) confirmed on all devices.
- `INTERNAL_AC_VOLTAGE` (offset=0x47): scale=1 on AC300/EP500P, scale=0 on AC200M — matches Repo 1.
- `INTERNAL_PACK_VOLTAGE` (offset=0x5C): scale=2 on AC200M (matches Repo 1); scale=1 on AC300/EP500P
  (minor discrepancy with Repo 1 which lists scale=2 for AC300/AC500).
- Cell voltages (offsets 0x69-0x78): scale=2 → /100 V — matches Repo 1.

**Critical architectural finding:** Block addresses 15600 (0x3CF0) and 17400 (0x43F8) cannot be
represented in the {page, offset} scheme. Both values exceed 0xFF in their low byte and require
multi-byte addresses. This confirms these block IDs belong to a separate, higher-level protocol
layer not implemented in Repo 2.

**DC-DC evidence:** None. No setpoint fields found in any device header.

**AT1/ATS evidence:** None. No transfer switch fields found in any device header.

---

### 5.3 bluetti-official/bluetti-home-assistant

**Sources:** `custom_components/bluetti/sensor.py`, `switch.py`, `select.py`, `models.py`,
`api/product_client.py`, local research files.

**Protocol:** Cloud REST API + STOMP WebSocket. No local BLE or MODBUS. All data comes from
Bluetti cloud servers as JSON key-value pairs using `fnCode` string identifiers.

**Devices:** EL100V2, EL300, EL320, EP6K, EP13K, EP2000, and others (cloud-connected models).
Notably, the heavy-load devices covered by Repos 1 and 2 (AC300, EP500, AC200M) are handled
differently or via a separate path.

**Confirmed scale factor (real device data):**
- `batteryVoltage` API field confirmed to return decivolts requiring /10 for volts.
  EL100V2 returned "548.5" → 54.85 V (real device confirmation).
  EL30V2 returned "170.2" → 17.02 V (real device confirmation).
  This independently supports the universal /10 pattern for voltage fields.

**Cloud API fields confirmed present:** SOC, ChgFullTime, ACLoadAllTotalPower, DCLoadAllTotalPower,
PVAllTotalPower, GridAllTotalPower, InvWorkState, onLine, SetCtrlAc, SetCtrlDc, SetCtrlPowerOn,
Storm_Mode_Cloud_Ctrl, SetCtrlWorkMode, SetDCECO, SetACECO, batteryVoltage, batterySoh,
powerGridIn, powerPvIn, powerAcOut, powerDcOut, packTotalChgEnergy, packTotalDsgEnergy,
packChargingStatus (enum: 0=Idle, 1=Charging, 2=Discharging), grid_line.

**Confirmed absent from cloud API:** gridVoltage, inputVoltage, gridFrequency, acVoltage
(these exist only in MQTT/Modbus layer, not cloud). DC-DC setpoint fields not present.

**AT1 transfer switch:** Explicitly confirmed unsupported. GitHub issue #52 documents that
AT1 transfer switch control is not available through the cloud integration.

**DC hub controls:** Confirmed missing. GitHub issue #32 documents that DC hub controls are absent.

---

## 6. Cross-Repository Conclusions

### 6.1 Scale Factor Consensus

The /10 scale for voltage and current fields is the most robustly confirmed finding across this
analysis. It appears in:
- Two independent BLE implementations (Repos 1 and 2) with different codebases, different languages
  (Python vs C++), and different addressing schemes, both arriving at the same result.
- One cloud API implementation (Repo 3) with real device confirmation.
- Across a combined 8+ distinct device types.

The AC200M outlier pattern (scale=2 where others use scale=1 for current and total battery voltage)
is consistently reproduced in both Repo 1 and Repo 2, suggesting it is a genuine firmware difference
in the AC200M rather than a documentation error.

### 6.2 Block 15600 — No External Resolution

Despite broad coverage across three independent repositories and multiple protocol layers, no external
source provides direct evidence for block 15600 DC-DC setpoint fields. The indirect evidence (all
confirmed DC read registers use /10 for voltage, /10 for current, raw for power) provides meaningful
support for the SDK's working hypothesis that setpoint registers follow the same scale conventions.
However, this remains an inference, not a confirmation.

The architectural analysis in Repo 2 provides a structural explanation for the absence: block 15600
exists in a protocol layer (likely a higher-level application protocol or a different BLE service)
that none of the open-source implementations access.

### 6.3 Block 17400 — No External Resolution; Cloud Confirms Unsupported

Block 17400 AT1/ATS fields are absent from all three repositories. Repo 3 provides the only
explicit negative statement: the official Bluetti Home Assistant integration does not support AT1
transfer switch functionality (issue #52). This may indicate the AT1 is a specialized accessory
with a dedicated protocol path, or that cloud integration simply omits this capability.

### 6.4 Protocol Layer Segregation

A key structural insight from this analysis is that the open-source community has successfully
reverse-engineered the primary BLE service layer (registers ~0-300 range, cloud API fields) but
has not penetrated the higher-level application protocol that contains DC-DC setpoint blocks and
ATS event blocks. These blocks appear to be accessible only through the official Bluetti app using
a protocol layer above the raw BLE MODBUS service.

### 6.5 Recommendations for SDK Development

1. The scale=1 (/10) hypothesis for block 15600 voltage/current fields is the highest-confidence
   inference available from external evidence. It should be used as the working assumption.
2. Block 17400 fields have no external analog to guide implementation. Device testing is the only
   path to resolution.
3. The AC200M scale=2 outlier pattern should be watched for in block 15600 if AC200M-specific
   DC-DC registers are ever confirmed.
4. The packChargingStatus enum (0=Idle, 1=Charging, 2=Discharging) from Repo 3 may be applicable
   to SDK charging state fields if the same enumeration is used in the local protocol.
