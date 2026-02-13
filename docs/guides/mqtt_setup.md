
# Day 4: MQTT Transport + Block 1300 End-to-End Test

**Status:** Ready for testing
**Goal:** Read grid voltage/frequency from live EL100V2 device

---

## What Was Built

### 1. MQTT Transport Layer (`mqtt_transport.py`)

Minimal MQTT implementation that:
- ✅ Connects to `iot.bluettipower.com:18760` with mTLS
- ✅ Handles PFX certificates
- ✅ Correct topics: Subscribe `PUB/{sn}`, Publish `SUB/{sn}`
- ✅ Synchronous `send_frame()` with 5s timeout
- ✅ Implements `TransportProtocol` interface

### 2. End-to-End Test (`test_mqtt_block_1300.py`)

Complete stack test:
```
MQTT Transport → Protocol Layer → V2 Parser → Device Model
```

Flow:
1. Authenticate with Bluetti API
2. Download PFX certificate
3. Connect to MQTT broker
4. Read Block 1300 (32 bytes = 16 registers)
5. Parse grid voltage/frequency/current/power
6. Validate values
7. Display results

### 3. Quality Control (`MQTT_TRANSPORT_CHECKLIST.md`)

Comprehensive checklist preventing:
- Topic confusion (PUB vs SUB)
- Register count errors
- Payload parsing mistakes
- CRC validation issues
- Endianness bugs
- Timeout problems

---

## Prerequisites

### 1. Install Dependencies

```bash
pip install paho-mqtt requests cryptography
```

### 2. Device Requirements

- ✅ Bluetti Elite 100 V2 or Elite 30 V2
- ✅ Device connected to internet (MQTT accessible)
- ✅ Bluetti account credentials
- ✅ Device serial number

---

## Running the Test

### Step 1: Navigate to Project Directory

```bash
cd d:\HomeAssistant
```

### Step 2: Run End-to-End Test

```bash
python test_mqtt_block_1300.py
```

### Step 3: Enter Credentials

```
Email: your_email@example.com
Password: ********
Device SN: 2345EB200xxxxxxx
Device model (EL100V2/EL30V2): EL100V2
```

### Step 4: Observe Output

Expected output:

```
============================================================
V2 End-to-End Test - Block 1300 (Grid Info)
============================================================

[Step 1] Authentication
------------------------------------------------------------
✓ Login successful, userId: 12345
✓ Certificate downloaded (1234 bytes)

[Step 2] Creating MQTT transport...
------------------------------------------------------------
✓ SSL certificates loaded successfully

[Step 3] Connecting to device...
------------------------------------------------------------
✓ Connected to MQTT broker
✓ Subscribed to PUB/2345EB200xxxxxxx

[Step 4] Reading Block 1300 (Grid Info)...
------------------------------------------------------------
✓ Block read successfully
  Block ID: 1300
  Name: INV_GRID_INFO
  Fields parsed: 4
  Data length: 32 bytes

[Step 5] Parsed Values
------------------------------------------------------------

📊 Grid Status:
  Frequency:     50.0 Hz
  Voltage:       230.4 V
  Current:       5.2 A
  Power:         1196 W

[Step 6] Validation
------------------------------------------------------------
✓ All values in expected ranges

============================================================
✅ End-to-End Test COMPLETE
============================================================
```

---

## Troubleshooting

### Issue: Connection Timeout

**Symptom:**
```
❌ Connection failed: Connection timeout
```

**Possible causes:**
1. Device is offline
2. Wrong device serial number
3. Certificate expired

**Solution:**
- Verify device is online in Bluetti app
- Double-check serial number
- Try re-downloading certificate

---

### Issue: Topic Not Found

**Symptom:**
```
No response received
```

**Possible causes:**
1. Wrong topic names
2. Device not subscribed

**Solution:**
- Check logs for topic names
- Verify: Subscribe to `PUB/{sn}`, Publish to `SUB/{sn}`

---

### Issue: CRC Mismatch

**Symptom:**
```
ProtocolError: CRC validation failed
```

**Possible causes:**
1. Corrupted data
2. Wrong endianness

**Solution:**
- Check CRC is little-endian (`<H`)
- Verify data integrity

---

### Issue: Values Out of Range

**Symptom:**
```
⚠️  Frequency out of range: 0.0 Hz
```

**Possible causes:**
1. Wrong schema offsets
2. Parsing error
3. Device returning zeros

**Solution:**
- Check schema offsets match APK
- Enable DEBUG logging
- Verify device is actually connected to grid

---

## Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This shows:
- MQTT messages (hex dumps)
- Modbus frames
- Parsed values
- Response times

---

## What to Verify

### ✅ Checklist

After successful test:

- [ ] Frequency is 45-55 Hz (50 Hz ±5)
- [ ] Voltage is 200-250 V (230V ±30)
- [ ] Current is reasonable (0-20A typical)
- [ ] Power matches V × I (within 10%)
- [ ] Device state updates correctly
- [ ] No timeout errors
- [ ] CRC validation passes
- [ ] All 4 fields parsed

---

## Next Steps After Success

### Day 5: Block 100 (Dashboard)

**Schema:** 50+ fields
- SOC, pack voltage/current
- Power flows (DC input, AC input/output, PV, Grid)
- Energy totals
- Temperatures
- Alarm/fault bitmaps

**Implementation:**
```python
# v2/schemas_generated/block_100.py
BLOCK_100_SCHEMA = BlockSchema(
    block_id=100,
    name="APP_HOME_DATA",
    min_length=52,
    fields=[
        Field("soc", offset=0, type=UInt16(), unit="%"),
        Field("pack_voltage", offset=2, type=UInt16(),
              transform=["scale:0.1"], unit="V"),
        # ... 50 more fields
    ]
)
```

---

### Day 6: Block 6000 (Battery Pack)

**Schema:** Battery pack status
- Voltage, current, power
- Temperatures (max/min/avg)
- Cycles, SOH
- Cell count
- Status flags

---

### Day 7: CLI Tool

```bash
python tools/v2_debug_cli.py --device EL100V2 --block 1300

# Output:
Block 1300 (INV_GRID_INFO):
  frequency: 50.0 Hz
  phase_0_voltage: 230.4 V
  phase_0_current: 5.2 A
  phase_0_power: 1196 W
  last_update: 2026-02-13 14:30:00
```

---

### Future: Home Assistant Integration

After all blocks are working:

```yaml
# configuration.yaml
sensor:
  - platform: bluetti_mqtt
    device: EL100V2_serial
    scan_interval: 5
    monitored_conditions:
      - grid_voltage
      - grid_frequency
      - soc
      - pack_power
```

---

## Architecture Validation

This test validates:

### ✅ Layer Separation

```
Application (test script)
    ↓
V2Client (orchestration)
    ↓
┌──────────┬──────────┬──────────┬──────────┐
│  MQTT    │ PROTOCOL │V2 PARSER │  DEVICE  │
│TRANSPORT │  LAYER   │  LAYER   │  MODEL   │
└──────────┴──────────┴──────────┴──────────┘
```

Each layer knows ONLY its responsibility:
- ❌ Transport doesn't know block schemas
- ❌ Protocol doesn't know field offsets
- ❌ Parser doesn't know MQTT topics
- ❌ Device model doesn't know byte manipulation

### ✅ Interface Contracts

All layers communicate through interfaces:
- `TransportProtocol.send_frame()` → bytes
- `normalize_modbus_response()` → clean bytes
- `V2Parser.parse_block()` → ParsedBlock
- `Device.update_from_block()` → state update

### ✅ No If-Chains

Device configuration is data, not code:
```python
profile = get_device_profile("EL100V2")
blocks = profile.groups["grid"].blocks  # [1300]
```

### ✅ Declarative Schemas

Field parsing is declarative:
```python
Field(
    name="frequency",
    offset=0,
    type=UInt16(),
    transform=["scale:0.1"],
    unit="Hz"
)
```

---

## Performance Expectations

For Day 4 minimal implementation:

| Operation | Target | Measured |
|-----------|--------|----------|
| Connect to MQTT | < 2s | ? |
| Read Block 1300 | < 1s | ? |
| Parse + validate | < 10ms | ? |
| Total end-to-end | < 3s | ? |

Fill in "Measured" column after first successful run.

---

## Files Created Today

```
bluetti_mqtt/
├── mqtt_transport.py              # MQTT transport layer
├── MQTT_TRANSPORT_CHECKLIST.md    # Quality control checklist
└── (existing files updated)

d:\HomeAssistant/
└── test_mqtt_block_1300.py        # End-to-end test script
```

---

## Success Criteria

End-to-end test is successful if:

1. ✅ Connection established
2. ✅ Block 1300 read without errors
3. ✅ Frequency in range 45-55 Hz
4. ✅ Voltage in range 200-250 V
5. ✅ All 4 fields parsed
6. ✅ Device state updated
7. ✅ No CRC errors
8. ✅ No timeout errors

If all checks pass → **Ready for Day 5** (Block 100 implementation)

---

**Status:** Ready for live device testing
**Next:** Run `python test_mqtt_block_1300.py` with real device credentials

