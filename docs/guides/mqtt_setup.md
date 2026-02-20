## MQTT Setup (Current Runtime Path)

This project no longer uses the old standalone end-to-end script or `bluetti_mqtt_client`.
The supported path is runtime-first configuration via YAML.

### Run

```bash
power-sdk runtime --config examples/runtime.yaml --dry-run
power-sdk runtime --config examples/runtime.yaml --once --connect
```

### Notes

- MQTT transport options come from `examples/runtime.yaml` (or your own config).
- Multi-device operation is configured declaratively in `pipelines` + `devices`.
- For migration details, see `docs/runtime/MIGRATION-GUIDE.md`.
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
└── power-sdk runtime --config examples/runtime.yaml --once        # End-to-end test script
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
**Next:** Run `python power-sdk runtime --config examples/runtime.yaml --once` with real device credentials


