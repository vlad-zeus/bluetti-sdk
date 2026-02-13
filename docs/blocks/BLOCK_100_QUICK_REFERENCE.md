# Block 100 Quick Reference Card

## Essential Information

- **Block ID**: 100 (0x64 hex)
- **Name**: APP_HOME_DATA
- **Purpose**: Primary dashboard data for Elite V2 devices
- **Size**: 52-184 bytes (depends on protocol version)
- **Update Frequency**: High (every few seconds)

## Most Important Fields

```
Offset | Field                    | Type    | Scale | Unit
-------|--------------------------|---------|-------|------
0-1    | packTotalVoltage         | UINT16  | 0.1   | V
2-3    | packTotalCurrent         | UINT16  | 0.1   | A
4-5    | packTotalSoc             | UINT16  | 1.0   | %
80-83  | totalDCPower             | UINT32  | 1.0   | W
84-87  | totalACPower             | UINT32  | 1.0   | W
88-91  | totalPVPower             | UINT32  | 1.0   | W
92-95  | totalGridPower (SIGNED!) | INT32   | 1.0   | W
100-103| totalDCEnergy            | UINT32  | 0.1   | kWh
108-111| totalPVChargingEnergy    | UINT32  | 0.1   | kWh
116-119| totalFeedbackEnergy      | UINT32  | 0.1   | kWh
```

## Parsing Examples

### Read UINT16 (2 bytes)
```python
def parse_uint16(data, offset):
    hex_str = data[offset] + data[offset+1]
    return int(hex_str, 16)

voltage_raw = parse_uint16(data, 0)  # bytes 0-1
voltage = voltage_raw / 10.0  # Apply 0.1 scale → Volts
```

### Read UINT32 (4 bytes)
```python
def parse_uint32(data, offset):
    hex_str = data[offset] + data[offset+1] + data[offset+2] + data[offset+3]
    return int(hex_str, 16)

power = parse_uint32(data, 80)  # bytes 80-83 → Watts
energy_raw = parse_uint32(data, 100)  # bytes 100-103
energy = energy_raw / 10.0  # Apply 0.1 scale → kWh
```

### Read INT32 (signed, 4 bytes)
```python
def parse_int32(data, offset):
    value = parse_uint32(data, offset)
    if value & 0x80000000:  # Check sign bit
        value = value - 0x100000000
    return value

grid_power = parse_int32(data, 92)  # Can be negative!
```

### Read ASCII String
```python
def parse_ascii(data, start, end):
    chars = []
    for i in range(start, end):
        byte_val = int(data[i], 16)
        if 0 < byte_val < 127:
            chars.append(chr(byte_val))
    return ''.join(chars).strip()

model = parse_ascii(data, 20, 32)  # 12-byte model string
serial = parse_ascii(data, 32, 40)  # 8-byte serial number
```

## Data Format Notes

1. **Input Format**: Data arrives as `List[String]` of hex bytes
   - Example: `["00", "F0", "00", "64", "00", "5A", ...]`

2. **Byte Combining**: Two consecutive hex strings are concatenated
   - `data[0] + data[1]` → `"00" + "F0"` → `"00F0"` → `int("00F0", 16)` → `240`

3. **Signed Values**: Only `totalGridPower` (offset 92-95) is signed
   - Negative = exporting to grid
   - Positive = importing from grid

4. **Scaling**: Don't forget to divide!
   - Voltage/Current: ÷10 (0.1 scale)
   - Energy (kWh): ÷10 (0.1 scale)
   - Power (W): No division (1.0 scale)
   - Exception: `packChgEnergyTotal` at offset 160 is already in Wh (no division)

## Protocol Version Checks

```python
if protocol_version >= 2001:
    # Can read offsets 80+ (power, energy, extended fields)
    total_pv_power = parse_uint32(data, 88)

if protocol_version >= 0x7D9:  # 2009
    # Can read CAN bus fault at offset 18-19
    can_fault = parse_uint16(data, 18)

if len(data) > 142:
    # Extended fields available
    component_online = parse_uint16(data, 142)
```

## Common Pitfalls

1. **Forgetting to scale**: Always divide by 10 for voltage/current/energy fields!
2. **Unsigned grid power**: `totalGridPower` must be read as INT32 (signed)
3. **Protocol version**: Fields at offset 80+ require v2001+
4. **Byte order**: Bluetti uses big-endian (high byte first)
5. **String parsing**: Device model may contain null bytes or spaces

## Bitmap Fields

Several fields are bitmaps (each bit has meaning):

```python
# Pack online bitmap (offset 16-17)
pack_online_value = parse_uint16(data, 16)
pack_0_online = (pack_online_value >> 0) & 1  # bit 0
pack_1_online = (pack_online_value >> 1) & 1  # bit 1
# ... up to pack 15

# Inverter online bitmap (offset 42-43)
inv_online_value = parse_uint16(data, 42)
inv_0_online = (inv_online_value >> 0) & 1
inv_1_online = (inv_online_value >> 1) & 1
```

## Home Assistant Integration

```yaml
sensor:
  - platform: mqtt
    name: "Bluetti Battery SoC"
    state_topic: "bluetti/state/DEVICE_SN"
    value_template: "{{ value_json.pack_total_soc }}"
    unit_of_measurement: "%"
    device_class: battery

  - platform: mqtt
    name: "Bluetti PV Power"
    state_topic: "bluetti/state/DEVICE_SN"
    value_template: "{{ value_json.total_pv_power }}"
    unit_of_measurement: "W"
    device_class: power

  - platform: mqtt
    name: "Bluetti Grid Power"
    state_topic: "bluetti/state/DEVICE_SN"
    value_template: "{{ value_json.total_grid_power }}"
    unit_of_measurement: "W"
    device_class: power
    # Note: Negative = exporting, Positive = importing
```

## Testing

```python
# Test data: 90% SoC, 24.0V, 10.0A
test_data = [
    "00", "F0",  # 240 → 24.0V
    "00", "64",  # 100 → 10.0A
    "00", "5A",  # 90%
    # ... rest of data
]

parsed = parse_block_100(test_data)
assert parsed.pack_total_voltage == 24.0
assert parsed.pack_total_current == 10.0
assert parsed.pack_total_soc == 90
```

## Performance Tips

1. **Cache parsed values**: Don't re-parse the same data
2. **Skip unused fields**: Only parse fields you need
3. **Use struct module**: For better performance in Python:
   ```python
   import struct
   voltage = struct.unpack('>H', bytes.fromhex(data[0] + data[1]))[0] / 10.0
   ```
4. **Batch MQTT updates**: Send all fields in one JSON message

## Additional Resources

- Full documentation: `BLOCK_100_APP_HOME_DATA.md`
- Detailed summary: `BLOCK_100_SUMMARY.txt`
- Python example: `block_100_parser_example.py`
- Source smali: `ProtocolParserV2.smali` lines 11640-13930
