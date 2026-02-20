# Layer Contracts and Interfaces

> Archive note (legacy naming): this document describes the pre-runtime phase
> and contains old identifiers (`V2Client`, legacy device model, `ParsedBlock`). Use
> `docs/platform/API-CONTRACTS.md` for current public API.

**Status:** Architecture fixed, implementation in progress

This document defines **strict contracts** between architectural layers. These interfaces are **non-negotiable** and prevent layer leakage.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│         Application / Home Assistant            │
│         (uses client.read_group())              │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│          CLIENT LAYER (v2_client.py)            │
│   Orchestrates: transport → protocol → parser   │
│                                                  │
│  Public API:                                     │
│  - read_block(block_id) → ParsedBlock          │
│  - read_group(BlockGroup) → List[ParsedBlock]  │
│  - get_device_state() → Dict                    │
└─────┬──────────┬──────────┬──────────┬─────────┘
      │          │          │          │
      │          │          │          │
┌─────▼────┐ ┌──▼─────┐ ┌──▼──────┐ ┌▼─────────┐
│TRANSPORT │ │PROTOCOL│ │V2 PARSER│ │  DEVICE  │
│  LAYER   │ │ LAYER  │ │  LAYER  │ │  MODEL   │
└──────────┘ └────────┘ └─────────┘ └──────────┘
```

---

## Layer Responsibilities

### Transport Layer
**File:** `mqtt_transport.py`, `ble_transport.py`

**Knows:**
- How to send/receive raw frames
- Connection management
- Timeouts and retries

**Does NOT know:**
- Modbus framing
- Block schemas
- Field parsing

**Interface:**
```python
class TransportProtocol(ABC):
    def send_frame(self, frame: bytes, timeout: float) -> bytes
    def connect(self)
    def disconnect(self)
    def is_connected(self) -> bool
```

---

### Protocol Layer
**File:** `protocol.py`

**Knows:**
- Modbus RTU framing
- CRC16-Modbus calculation
- Byte normalization (big-endian)

**Does NOT know:**
- Block schemas
- Field offsets
- Transform pipelines

**Interface:**
```python
def build_modbus_request(device_addr: int, block_addr: int, count: int) -> bytes
def parse_modbus_frame(frame: bytes) -> ModbusResponse
def normalize_modbus_response(response: ModbusResponse) -> bytes
def validate_crc(frame: bytes) -> bool
```

**Contract:**
```python
# Input: Raw Modbus frame
frame = b'\x01\x03\x06\x00\x55\x02\x08\x0C\xAD\xCR\xCC'

# Output: Normalized bytes (no framing, big-endian)
normalized = b'\x00\x55\x02\x08\x0C\xAD'
```

---

### V2 Parser Layer
**File:** `v2/parser.py`, `v2/schema.py`

**Knows:**
- Block schemas (fields, offsets, types)
- Transform pipelines
- Validation rules

**Does NOT know:**
- Modbus
- Transport
- Device state management

**Interface:**
```python
class V2ParserInterface(ABC):
    def parse_block(
        self,
        block_id: int,
        data: bytes,  # Normalized, no framing
        validate: bool = True,
        protocol_version: int = 2000
    ) -> ParsedBlock

    def register_schema(self, schema: BlockSchema)
```

**Contract:**
```python
# Input: Normalized bytes
data = b'\x00\x55\x02\x08\x0C\xAD'

# Output: ParsedBlock
ParsedBlock(
    block_id=100,
    name="APP_HOME_DATA",
    values={
        "soc": 85,
        "pack_voltage": 52.0,
        "pack_current": 31.41
    },
    raw=data,
    validation=ValidationResult(valid=True)
)
```

---

### Device Model Layer
**File:** `v2_device.py`

**Knows:**
- Device state structure
- Block ID → attribute mapping
- High-level API

**Does NOT know:**
- Byte offsets
- Transforms
- Modbus

**Interface:**
```python
class DeviceModelInterface(ABC):
    def update_from_block(self, parsed: ParsedBlock)
    def get_state(self) -> Dict[str, Any]
    def get_group_state(self, group: BlockGroup) -> Dict[str, Any]
```

**Contract:**
```python
# Input: ParsedBlock
parsed = ParsedBlock(block_id=1300, values={"frequency": 50.0, ...})

# Action: Update device state
device.update_from_block(parsed)

# Output: High-level attributes
device.grid_info.frequency  # 50.0 Hz
device.grid_info.phase_0_voltage  # 230.0 V
```

---

## Data Flow Example

### Reading Block 1300 (Grid Info)

```python
# === Application Code ===
client = V2Client(transport, profile)
parsed = client.read_block(1300)

print(f"Grid: {parsed.values['phase_0_voltage']}V")
```

**Internal flow:**

```
1. CLIENT: Build Modbus request
   └─> protocol.build_modbus_request(1, 1300, 16)
   └─> returns: b'\x01\x03\x05\x14\x00\x10\xCR\xCC'

2. CLIENT: Send via transport
   └─> transport.send_frame(request, timeout=5.0)
   └─> returns: b'\x01\x03\x20...\xCR\xCC'

3. CLIENT: Parse Modbus response
   └─> protocol.parse_modbus_frame(response)
   └─> returns: ModbusResponse(data=b'\x01\xF4\x08\xFC...')

4. CLIENT: Normalize bytes
   └─> protocol.normalize_modbus_response(response)
   └─> returns: b'\x01\xF4\x08\xFC...' (32 bytes, big-endian)

5. CLIENT: Parse block
   └─> parser.parse_block(1300, normalized, validate=True)
   └─> returns: ParsedBlock(values={"frequency": 50.0, ...})

6. CLIENT: Update device model
   └─> device.update_from_block(parsed)
   └─> device.grid_info.frequency = 50.0

7. CLIENT: Return ParsedBlock
   └─> Application gets ParsedBlock
```

---

## Non-Negotiable Rules

### ✅ Rule 1: No Layer Leakage

**BAD:**
```python
# Device model knows about byte offsets
device.pack_voltage = int.from_bytes(data[2:4], 'big') / 10.0
```

**GOOD:**
```python
# Device model only knows ParsedBlock
device.update_from_block(parsed)
device.pack_voltage = parsed.values["pack_voltage"]
```

---

### ✅ Rule 2: No If-Chains for Protocol Detection

**BAD:**
```python
if device.model == "EL100V2":
    blocks = [100, 1300, 6000]
elif device.model == "EL30V2":
    blocks = [100, 1300]
```

**GOOD:**
```python
# Device profile defines blocks (data, not code)
profile = get_device_profile("EL100V2")
blocks = profile.groups["core"].blocks
```

---

### ✅ Rule 3: Parser Receives Normalized Bytes

**BAD:**
```python
# Parser strips Modbus framing
parser.parse_block(modbus_response)
```

**GOOD:**
```python
# Protocol layer normalizes, parser parses clean bytes
normalized = normalize_modbus_response(modbus_response)
parsed = parser.parse_block(block_id, normalized)
```

---

### ✅ Rule 4: Transform Pipelines Are Declarative

**BAD:**
```python
# Hardcoded transform in parser
voltage = (raw_value & 0x3FFF) / 1000.0
```

**GOOD:**
```python
# Declarative transform in schema
Field(
    name="voltage",
    offset=10,
    type=UInt16(),
    transform=["bitmask:0x3FFF", "scale:0.001"]
)
```

---

### ✅ Rule 5: Device State Is High-Level

**BAD:**
```python
# Application accesses raw bytes
voltage = device.raw_data[28:30]
```

**GOOD:**
```python
# Application accesses typed attributes
voltage = device.grid_info.phase_0_voltage
```

---

## Error Handling

### Error Hierarchy

```
BluettiError (base)
├── TransportError (connection, timeout)
├── ProtocolError (CRC, framing, Modbus error)
├── ParserError (unknown block, validation failure)
└── DeviceError (invalid state, unsupported operation)
```

### Error Flow

```python
try:
    parsed = client.read_block(1300)
except TransportError:
    # Retry connection
    pass
except ProtocolError:
    # Log invalid response
    pass
except ParserError:
    # Schema mismatch - update schema
    pass
```

---

## Testing Strategy

### Unit Tests (per layer)

```python
# Transport layer test
def test_transport_send_frame():
    transport = MockTransport()
    response = transport.send_frame(b'\x01\x03...')
    assert len(response) > 0

# Protocol layer test
def test_normalize_modbus():
    response = ModbusResponse(data=b'\x00\x55\x02\x08')
    normalized = normalize_modbus_response(response)
    assert normalized == b'\x00\x55\x02\x08'

# Parser layer test
def test_parse_block():
    parser = V2Parser()
    parser.register_schema(schema_1300)
    parsed = parser.parse_block(1300, normalized_bytes)
    assert parsed.values["frequency"] == 50.0

# Device model test
def test_device_update():
    device = LegacyDeviceModel("test", "EL100V2")
    device.update_from_block(parsed)
    assert device.grid_info.frequency == 50.0
```

### Integration Test (full stack)

```python
def test_full_stack():
    transport = MockTransport()
    client = V2Client(transport, profile)
    client.register_schema(schema_1300)

    parsed = client.read_block(1300)

    assert parsed.values["frequency"] == 50.0
    assert client.device.grid_info.frequency == 50.0
```

---

## Implementation Checklist

### ✅ Completed

- [x] Protocol layer (`protocol.py`)
- [x] Contracts (`contracts.py`)
- [x] V2 Parser (`v2/parser.py`, `v2/schema.py`, `v2/datatypes.py`, `v2/transforms.py`)
- [x] Device model (`v2_device.py`)
- [x] Client (`v2_client.py`)
- [x] Device profiles (`device_profiles.py`)
- [x] Example usage (`examples/v2_usage_example.py`)

### 🔲 Pending

- [ ] Block schemas (1300, 100, 6000)
- [ ] MQTT transport implementation
- [ ] BLE transport implementation
- [ ] CLI tool
- [ ] Live device testing

---

## Next Steps

### Day 3 (Today): Integration Testing

1. Run example: `python examples/v2_usage_example.py`
2. Verify all layers work together
3. Test with mock transport

### Day 4: Block 1300 Schema

1. Create `v2/schemas_generated/block_1300.py`
2. Test with live device (if available)
3. Verify grid voltage/frequency reading

### Day 5: Block 100 + 6000 Schemas

1. Implement larger schemas
2. Test array fields
3. Test packed fields

### Day 6: CLI Tool

```bash
python tools/v2_debug_cli.py --device EL100V2 --block 1300
```

---

**Status:** Architecture complete, ready for block schema implementation
**Last updated:** 2026-02-13
**Design approved:** Yes
