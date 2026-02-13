# V2 Parser Specification

**Version:** 1.0.0
**Status:** Design Document (Pre-Implementation)
**Purpose:** Canonical specification for V2 protocol parser architecture

---

## Design Principles

1. **Data, not code** - Block structure is declarative, not procedural
2. **Transform pipeline** - Complex decoding is a sequence of simple operations
3. **Explicit errors** - Strict mode catches protocol changes early
4. **Normalization** - Parser receives clean bytes, protocol layer handles framing
5. **Arrays first-class** - Repeating structures are declarative, not copy-paste
6. **Flexible output** - Dict for flexibility, dataclass for convenience
7. **Device profiles** - Protocol + groups defined per device family

---

## 1. Field Definition

### Basic Field

```python
Field(
    name="soc",               # Field name
    offset=0,                 # Byte offset in block
    type=UInt16,              # Data type
    unit="%",                 # Optional unit
    required=True,            # If False, missing data → None (not error)
    min_protocol_version=2000,  # Optional version gate
    description="Battery state of charge"
)
```

### Field with Transform Pipeline

```python
Field(
    name="grid_current",
    offset=30,
    type=Int16,
    transform=["abs", "scale:0.1"],  # abs() then /10.0
    unit="A",
    required=True
)
```

Available transforms (executed in order):
- `"abs"` - Absolute value
- `"scale:0.1"` - Multiply by constant
- `"minus:40"` - Subtract constant (e.g., temperature)
- `"bitmask:0x3FFF"` - AND with mask
- `"shift:14"` - Bit shift right
- `"enum:ChargingStatus"` - Map to enum
- `"clamp:0:100"` - Clamp to range

### Array Field

```python
ArrayField(
    name="cell_voltages",
    offset=10,
    count=16,                  # Number of items
    stride=2,                  # Bytes between items
    item_type=UInt16,
    transform=["bitmask:0x3FFF", "scale:0.001"],  # Extract 14-bit voltage
    unit="V",
    required=True
)
```

### Packed Struct Field

For cells with voltage + status in one uint16:

```python
PackedField(
    name="cells",
    offset=10,
    count=16,
    stride=2,
    fields=[
        SubField("voltage", bits="0:14", transform=["scale:0.001"], unit="V"),
        SubField("status", bits="14:16", enum=CellStatus)
    ],
    required=True
)
```

---

## 2. Data Types

### Base Types

```python
class DataType(ABC):
    @abstractmethod
    def parse(self, data: bytes, offset: int) -> Any:
        """Parse value from normalized byte buffer."""
        pass

    @abstractmethod
    def size(self) -> int:
        """Size in bytes."""
        pass

    @abstractmethod
    def encode(self, value: Any) -> bytes:
        """Encode value for writing."""
        pass
```

### Standard Types

- `UInt8` - 1 byte unsigned
- `Int8` - 1 byte signed
- `UInt16` - 2 bytes unsigned big-endian
- `Int16` - 2 bytes signed big-endian
- `UInt32` - 4 bytes unsigned big-endian
- `Int32` - 4 bytes signed big-endian
- `String(length)` - Fixed-length ASCII string
- `Bitmap(bits)` - Bit field
- `Enum(mapping)` - Enum type

### Input Format

**Parser always receives normalized bytes:**

```python
def parse_block(self, block_id: int, data: bytes) -> ParsedBlock:
    """
    Args:
        data: Normalized byte buffer (big-endian, no Modbus framing)
    """
```

Protocol layer responsibility:
```python
# modbus.py
def normalize_modbus_response(response: ModbusResponse) -> bytes:
    """
    Convert Modbus response to normalized byte buffer.
    - Remove function code byte
    - Remove byte count
    - Keep only register data
    - Ensure big-endian
    """
    return response.data[2:]  # Skip func + byte_count
```

---

## 3. Block Schema

### Schema Definition

```python
BlockSchema(
    block_id=100,
    name="APP_HOME_DATA",
    description="Main dashboard data",
    min_length=52,             # Minimum valid length
    fields=[...],
    protocol_version=2000,     # Base protocol version
    schema_version="1.0.0",    # Schema version (for evolution)
    strict=True                # Strict validation mode
)
```

### Strict vs Lenient Mode

**Strict mode (default):**
- All `required=True` fields must be parseable
- If `len(data) < field.offset + field.size` → error
- Unknown extra data is logged as warning

**Lenient mode:**
- Missing optional fields → None
- Extra data is ignored
- Use for backward compatibility

```python
schema = BlockSchema(..., strict=False)
```

### Validation

```python
def validate(self, data: bytes) -> ValidationResult:
    """
    Check if data is valid for this schema.

    Returns:
        ValidationResult(
            valid=True/False,
            errors=[...],       # List of validation errors
            warnings=[...],     # List of warnings
            missing_fields=[]   # Optional fields not present
        )
    """
```

---

## 4. Parsed Output

### ParsedBlock Format

```python
@dataclass
class ParsedBlock:
    """Result of parsing a V2 block."""

    # Identity
    block_id: int
    name: str

    # Parsed data
    values: Dict[str, Any]          # Flat dict of field_name → value
    model: Optional[Any] = None     # Optional dataclass instance

    # Metadata
    raw: bytes                      # Original raw bytes (for debug)
    length: int                     # Actual data length
    protocol_version: int           # Device protocol version
    schema_version: str             # Schema version used
    timestamp: float                # Parse timestamp

    # Validation
    validation: Optional[ValidationResult] = None

    def to_dict(self) -> dict:
        """Flat dict for JSON/MQTT."""
        return self.values

    def to_model(self, model_class: Type[T]) -> T:
        """Convert to dataclass."""
        return model_class(**self.values)
```

### Example Usage

```python
# Parse block
parsed = parser.parse_block(100, raw_bytes)

# Access values
soc = parsed.values["soc"]
voltage = parsed.values["pack_voltage"]

# Or use model
home_data = parsed.to_model(HomeData)
print(home_data.soc)

# Export to MQTT
mqtt_payload = json.dumps(parsed.to_dict())

# Debug
if parsed.validation and not parsed.validation.valid:
    logger.warning(f"Parse errors: {parsed.validation.errors}")
```

---

## 5. Transform Pipeline

### Transform Execution

Transforms are applied **in order** after type parsing:

```python
raw_value = type.parse(data, offset)  # uint16 = 65500

# Apply transforms in sequence
for transform in field.transforms:
    raw_value = apply_transform(transform, raw_value)

# Example: ["abs", "scale:0.1"]
# 1. abs: -52 → 52
# 2. scale:0.1: 52 → 5.2
```

### Transform Registry

```python
# v2/transforms.py

TRANSFORMS = {
    "abs": lambda x: abs(x),
    "scale": lambda x, factor: x * float(factor),
    "minus": lambda x, offset: x - float(offset),
    "bitmask": lambda x, mask: x & int(mask, 16),
    "shift": lambda x, bits: x >> int(bits),
    "enum": lambda x, enum_name: ENUMS[enum_name](x),
    "clamp": lambda x, min_val, max_val: max(min_val, min(max_val, x))
}
```

### Complex Example

Cell voltage encoding (14-bit voltage + 2-bit status):

```python
PackedField(
    name="cells",
    offset=10,
    count=16,
    stride=2,
    fields=[
        SubField(
            name="voltage",
            bits="0:14",           # Extract bits 0-13
            transform=["scale:0.001"],  # mV → V
            unit="V"
        ),
        SubField(
            name="status",
            bits="14:16",          # Extract bits 14-15
            enum=CellStatus
        )
    ]
)

# Equivalent manual parsing:
for i in range(16):
    raw = uint16(data, offset + i*2)
    voltage_mv = raw & 0x3FFF         # bits 0-13
    status = (raw & 0xC000) >> 14     # bits 14-15
    cells[i] = {
        "voltage": voltage_mv / 1000.0,
        "status": CellStatus(status)
    }
```

---

## 6. Block Groups

### Group Definition

```python
@dataclass
class BlockGroup:
    """Group of related blocks."""
    name: str
    blocks: List[int]          # Block IDs
    description: str
    poll_interval: int = 5     # Recommended poll interval (seconds)
```

### Standard Groups (V2)

```python
BLOCK_GROUPS_V2 = {
    "core": BlockGroup(
        name="core",
        blocks=[100],
        description="Main dashboard (SOC, power flows, energy)",
        poll_interval=5
    ),

    "grid": BlockGroup(
        name="grid",
        blocks=[1300],
        description="Grid voltage, frequency, power",
        poll_interval=5
    ),

    "battery": BlockGroup(
        name="battery",
        blocks=[6000],
        description="Battery pack status",
        poll_interval=10
    ),

    "cells": BlockGroup(
        name="cells",
        blocks=[6100],
        description="Individual cell voltages/temps (expensive!)",
        poll_interval=60  # Poll rarely
    ),

    "inverter": BlockGroup(
        name="inverter",
        blocks=[1100, 1400, 1500],
        description="Inverter details",
        poll_interval=10
    )
}
```

### Device Profile

```python
@dataclass
class DeviceProfile:
    """Device-specific configuration."""
    model: str
    type_id: int
    protocol: str              # "v1" or "v2"
    voltage: str               # "25V" or "56V"
    groups: Dict[str, BlockGroup]  # Available groups for this model

# Example
ELITE_100_V2_PROFILE = DeviceProfile(
    model="EL100V2",
    type_id=31,
    protocol="v2",
    voltage="56V",
    groups={
        "core": BLOCK_GROUPS_V2["core"],
        "grid": BLOCK_GROUPS_V2["grid"],
        "battery": BLOCK_GROUPS_V2["battery"],
        "cells": BLOCK_GROUPS_V2["cells"],
        "inverter": BLOCK_GROUPS_V2["inverter"]
    }
)
```

### Usage in Client

```python
# client.py

def read_group(self, device: BluettiDevice, group_name: str):
    """Read a logical group (V1 or V2)."""

    group = device.profile.groups.get(group_name)
    if not group:
        raise ValueError(f"Unknown group: {group_name}")

    if device.profile.protocol == "v2":
        # V2: read multiple blocks
        results = []
        for block_id in group.blocks:
            parsed = self.read_v2_block(device, block_id)
            results.append(parsed)
        return results
    else:
        # V1: existing logic
        return self._read_v1_group(device, group_name)
```

**No if-elif chains in application code!**

---

## 7. Schema Generation from Markdown

### Build-Time Generation

```bash
# tools/generate_schemas.py

python tools/generate_schemas.py \
    --input v2_blocks/BLOCK_100_APP_HOME_DATA.md \
    --output bluetti_mqtt/v2/schemas_generated/block_100.py
```

### Generated Schema Format

```python
# bluetti_mqtt/v2/schemas_generated/block_100.py
# AUTO-GENERATED from BLOCK_100_APP_HOME_DATA.md
# DO NOT EDIT MANUALLY

from ..schema import Field, BlockSchema
from ..datatypes import UInt16, Int16, UInt32

BLOCK_100_SCHEMA = BlockSchema(
    block_id=100,
    name="APP_HOME_DATA",
    min_length=52,
    fields=[
        Field(name="soc", offset=0, type=UInt16(), unit="%"),
        Field(name="pack_voltage", offset=2, type=UInt16(),
              transform=["scale:0.1"], unit="V"),
        # ... auto-generated from markdown table
    ],
    schema_version="1.0.0"
)
```

### Source of Truth

- **Markdown files** in `v2_blocks/` - Human-editable, source of truth
- **Generated Python** in `v2/schemas_generated/` - Committed to repo, used at runtime
- **CI check** - Ensure generated files are up-to-date

---

## 8. Parser Implementation Checklist

### Core Components

- [ ] `v2/datatypes.py` - Base types (UInt16, Int16, etc)
- [ ] `v2/transforms.py` - Transform functions
- [ ] `v2/schema.py` - Field, ArrayField, PackedField, BlockSchema
- [ ] `v2/parser.py` - V2Parser engine
- [ ] `v2/registry.py` - Schema + group registration
- [ ] `v2/models/` - Optional dataclasses

### Block Schemas (Priority Order)

1. [ ] Block 100 (APP_HOME_DATA) - Core dashboard
2. [ ] Block 1300 (INV_GRID_INFO) - Grid voltage/frequency
3. [ ] Block 6000 (PACK_MAIN_INFO) - Battery status
4. [ ] Block 6100 (PACK_ITEM_INFO) - Cell voltages
5. [ ] Block 1100 (INV_BASE_INFO) - Inverter details
6. [ ] Block 1400 (INV_LOAD_INFO) - Load outputs
7. [ ] Block 1500 (INV_INV_INFO) - Inverter output

### Integration

- [ ] Update `client.py` - Add `read_v2_block()`
- [ ] Update `device.py` - Add V2 state storage
- [ ] Add `protocol.py` - Modbus payload normalization
- [ ] Add device profiles - EL30V2, EL100V2

### Testing

- [ ] Unit tests - Schema validation
- [ ] Unit tests - Transform pipeline
- [ ] Unit tests - Array parsing
- [ ] Integration tests - Live device parsing
- [ ] Validation tests - Strict mode error handling

---

## 9. Example: Complete Block 1300 Schema

```python
# v2/schemas_generated/block_1300.py

BLOCK_1300_SCHEMA = BlockSchema(
    block_id=1300,
    name="INV_GRID_INFO",
    description="Grid input monitoring",
    min_length=38,
    strict=True,
    fields=[
        # Frequency
        Field(
            name="frequency",
            offset=0,
            type=UInt16(),
            transform=["scale:0.1"],
            unit="Hz",
            required=True
        ),

        # Phase 0
        Field(
            name="phase_0_power",
            offset=26,
            type=Int16(),
            transform=["abs"],
            unit="W",
            required=True
        ),
        Field(
            name="phase_0_voltage",
            offset=28,
            type=UInt16(),
            transform=["scale:0.1"],
            unit="V",
            required=True
        ),
        Field(
            name="phase_0_current",
            offset=30,
            type=Int16(),
            transform=["abs", "scale:0.1"],
            unit="A",
            required=True
        ),

        # Optional: Phase 1 & 2 (for 3-phase systems)
        Field(
            name="phase_1_voltage",
            offset=40,
            type=UInt16(),
            transform=["scale:0.1"],
            unit="V",
            required=False
        ),
        # ... etc
    ],
    schema_version="1.0.0"
)
```

---

## 10. Non-Negotiables

**Fixed architectural decisions:**

1. ✅ Parser receives **normalized bytes** (protocol layer handles Modbus framing)
2. ✅ Schema supports **required/optional** fields and strict validation mode
3. ✅ Transforms are **declarative** (pipeline of named operations)
4. ✅ Arrays/Repeat are **first-class** schema elements (no manual field copy-paste)
5. ✅ Parser output is **ParsedBlock** (dict + optional dataclass)
6. ✅ Block groups are **defined per device profile** (no protocol if-chains)
7. ✅ Schema generation is **build-time** (markdown is source, generated Python is committed)

---

## 11. Version Evolution Strategy

### Schema Versioning

Each BlockSchema has:
- `protocol_version` - Minimum device protocol version
- `schema_version` - Parser schema version (semantic versioning)

### Adding New Fields

```python
# Original schema (v1.0.0)
Field("soc", offset=0, type=UInt16())

# New field added in device firmware v2003
Field("extended_soh", offset=100, type=UInt16(),
      min_protocol_version=2003, required=False)
```

### Backward Compatibility

- Old devices (protocol < 2003): `extended_soh` = None
- New devices (protocol >= 2003): `extended_soh` = parsed value
- Parser gracefully handles both

---

## 12. Performance Considerations

### Parsing Speed

- Target: <5ms per block on typical hardware
- Optimize hot paths: type parsing, transform application
- Cache compiled transform pipelines

### Memory

- Avoid unnecessary copies of raw bytes
- Reuse ParsedBlock objects where possible
- Limit number of blocks polled simultaneously

### Polling Strategy

- Use `BlockGroup.poll_interval` as guidance
- Expensive blocks (cells) → poll rarely
- Critical blocks (dashboard) → poll frequently

---

**Status:** Design approved, ready for implementation
**Next Step:** Implement `v2/datatypes.py`, `v2/schema.py`, `v2/parser.py`
**Timeline:** 5-7 days (Days 1-3: core, Days 4-5: blocks, Days 6-7: integration)
