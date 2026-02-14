# Architecture Hardening Implementation Plan

**Status**: Ready for Implementation
**Date**: 2026-02-14

## Overview

Three increments implementing Architecture Hardening decisions:
- **A**: AsyncV2Client facade (async API)
- **B**: Instance-scoped registry (no global state)
- **C**: Typed transforms (type-safe DSL)

Each increment is **independent, shippable, and tested**.

---

## Increment A: AsyncV2Client Facade

**Goal**: Provide native async API without breaking sync API

**ADR**: [ADR-001](ADR-001-dual-async-sync-api.md)

### Implementation Steps

#### 1. Create AsyncV2Client class

**File**: `bluetti_sdk/client_async.py`

```python
import asyncio
from typing import List, Optional

from .client import V2Client, ReadGroupResult
from .contracts import TransportProtocol
from .devices.types import DeviceProfile
from .models.types import BlockGroup
from .protocol.v2.types import ParsedBlock


class AsyncV2Client:
    """Async facade for V2Client.

    Wraps synchronous V2Client, delegating to thread pool.
    """

    def __init__(
        self,
        transport: TransportProtocol,
        profile: DeviceProfile,
        device_address: int = 1,
    ):
        # Create sync client (does all the work)
        self._sync_client = V2Client(transport, profile, device_address)

    async def connect(self) -> None:
        """Connect to device (async)."""
        await asyncio.to_thread(self._sync_client.connect)

    async def disconnect(self) -> None:
        """Disconnect from device (async)."""
        await asyncio.to_thread(self._sync_client.disconnect)

    async def read_block(
        self, block_id: int, register_count: Optional[int] = None
    ) -> ParsedBlock:
        """Read and parse block (async)."""
        return await asyncio.to_thread(
            self._sync_client.read_block, block_id, register_count
        )

    async def read_group(
        self, group: BlockGroup, partial_ok: bool = True
    ) -> List[ParsedBlock]:
        """Read block group (async)."""
        return await asyncio.to_thread(
            self._sync_client.read_group, group, partial_ok
        )

    async def read_group_ex(
        self, group: BlockGroup, partial_ok: bool = False
    ) -> ReadGroupResult:
        """Read block group with error details (async)."""
        return await asyncio.to_thread(
            self._sync_client.read_group_ex, group, partial_ok
        )

    async def get_device_state(self) -> dict:
        """Get device state (async)."""
        return await asyncio.to_thread(self._sync_client.get_device_state)

    async def get_group_state(self, group: BlockGroup) -> dict:
        """Get group state (async)."""
        return await asyncio.to_thread(
            self._sync_client.get_group_state, group
        )

    # Async context manager support
    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
        return False
```

**LOC**: ~100

#### 2. Update public API

**File**: `bluetti_sdk/__init__.py`

```python
# Add async client export
from .client_async import AsyncV2Client

__all__ = [
    # ... existing
    "AsyncV2Client",  # NEW
]
```

**LOC**: +2

#### 3. Write comprehensive tests

**File**: `tests/unit/test_client_async.py`

```python
import pytest
from unittest.mock import Mock
from bluetti_sdk.client_async import AsyncV2Client
from bluetti_sdk.devices.profiles import get_device_profile


@pytest.fixture
def mock_transport():
    transport = Mock()
    transport.connect = Mock()
    transport.disconnect = Mock()
    transport.is_connected = Mock(return_value=True)
    return transport


@pytest.fixture
def device_profile():
    return get_device_profile("EL100V2")


@pytest.mark.asyncio
async def test_async_client_creation(mock_transport, device_profile):
    """Test AsyncV2Client creation."""
    client = AsyncV2Client(mock_transport, device_profile)
    assert client._sync_client is not None


@pytest.mark.asyncio
async def test_async_connect(mock_transport, device_profile):
    """Test async connect."""
    client = AsyncV2Client(mock_transport, device_profile)
    await client.connect()
    mock_transport.connect.assert_called_once()


@pytest.mark.asyncio
async def test_async_disconnect(mock_transport, device_profile):
    """Test async disconnect."""
    client = AsyncV2Client(mock_transport, device_profile)
    await client.disconnect()
    mock_transport.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_async_context_manager(mock_transport, device_profile):
    """Test async context manager."""
    async with AsyncV2Client(mock_transport, device_profile) as client:
        assert client is not None

    mock_transport.connect.assert_called_once()
    mock_transport.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_async_read_block(mock_transport, device_profile):
    """Test async read_block delegates to sync client."""
    from bluetti_sdk.protocol.v2.types import ParsedBlock

    client = AsyncV2Client(mock_transport, device_profile)

    # Mock sync client's read_block
    mock_parsed = ParsedBlock(
        block_id=100,
        name="TEST",
        values={},
        raw=b"",
        length=0,
        protocol_version=2000,
        schema_version="1.0.0",
        timestamp=0.0
    )
    client._sync_client.read_block = Mock(return_value=mock_parsed)

    result = await client.read_block(100)

    assert result == mock_parsed
    client._sync_client.read_block.assert_called_once_with(100, None)
```

**LOC**: ~200

#### 4. Documentation

**File**: `docs/examples/async_usage.py`

```python
"""Example: Using AsyncV2Client for async applications."""

import asyncio
from pathlib import Path
from bluetti_sdk import AsyncV2Client, MQTTConfig, MQTTTransport
from bluetti_sdk.devices.profiles import get_device_profile


async def main():
    # Configure MQTT
    config = MQTTConfig(
        device_sn="2345EB200xxxxxxx",
        pfx_cert=Path("cert.pfx").read_bytes(),
        cert_password="password"
    )

    # Create transport and profile
    transport = MQTTTransport(config)
    profile = get_device_profile("EL100V2")

    # Use async client with context manager
    async with AsyncV2Client(transport, profile) as client:
        # Read single block
        home_data = await client.read_block(100)
        print(f"SOC: {home_data.values['soc']}%")

        # Read multiple blocks concurrently
        grid_task = client.read_block(1300)
        battery_task = client.read_block(6000)

        grid, battery = await asyncio.gather(grid_task, battery_task)

        print(f"Grid: {grid.values['phase_0_voltage']}V")
        print(f"Battery: {battery.values['pack_voltage']}V")


if __name__ == "__main__":
    asyncio.run(main())
```

**LOC**: ~40

### Deliverables

- [ ] `bluetti_sdk/client_async.py` - AsyncV2Client implementation
- [ ] `tests/unit/test_client_async.py` - Comprehensive tests
- [ ] `docs/examples/async_usage.py` - Usage example
- [ ] Updated `bluetti_sdk/__init__.py` - Export AsyncV2Client
- [ ] Migration notes in `docs/migration/async-api.md`

### Acceptance Criteria

- [ ] All async methods delegate to sync via asyncio.to_thread()
- [ ] Async context manager works (__aenter__, __aexit__)
- [ ] 100% test coverage for AsyncV2Client
- [ ] All existing tests pass unchanged
- [ ] Performance: thread pool overhead < 1ms per call
- [ ] Documentation with examples

**Estimated LOC**: ~350 total
**Estimated Effort**: 1 PR, 4-6 hours

---

## Increment B: Instance-Scoped Schema Registry

**Goal**: Remove global mutable state, improve test isolation

**ADR**: [ADR-002](ADR-002-instance-scoped-schema-registry.md)

### Implementation Steps

#### 1. Make SchemaRegistry immutable

**File**: `bluetti_sdk/schemas/registry.py`

Current (mutable):
```python
class SchemaRegistry:
    _schemas: Dict[int, BlockSchema] = {}

    @classmethod
    def register(cls, schema: BlockSchema):
        cls._schemas[schema.block_id] = schema  # MUTABLE!
```

New (immutable after init):
```python
class SchemaRegistry:
    _schemas: Dict[int, BlockSchema] = {}
    _initialized: bool = False

    @classmethod
    def _register_builtin(cls, schemas: List[BlockSchema]):
        """Register built-in schemas (called once at module init)."""
        if cls._initialized:
            raise RuntimeError("Registry already initialized")

        for schema in schemas:
            cls._schemas[schema.block_id] = schema

        cls._initialized = True

    @classmethod
    def discover(cls, block_ids: List[int]) -> Dict[int, BlockSchema]:
        """Discover schemas (read-only)."""
        return {
            bid: cls._schemas[bid]
            for bid in block_ids
            if bid in cls._schemas
        }

    @classmethod
    def get(cls, block_id: int) -> Optional[BlockSchema]:
        """Get schema (read-only)."""
        return cls._schemas.get(block_id)
```

**LOC**: ~50 changed

#### 2. Initialize registry at module load

**File**: `bluetti_sdk/schemas/__init__.py`

```python
# Register built-in schemas once at module import
from .registry import SchemaRegistry

SchemaRegistry._register_builtin([
    BLOCK_100_SCHEMA,
    BLOCK_1300_SCHEMA,
    BLOCK_6000_SCHEMA,
])
```

**LOC**: ~10

#### 3. Remove global mutation methods

**File**: `bluetti_sdk/schemas/registry.py`

Remove from public API:
- `register()` - ❌ Removed
- `register_many()` - ❌ Removed
- `_clear_for_testing()` - ❌ Removed

Keep:
- `discover()` - ✅ Read-only
- `get()` - ✅ Read-only
- `list_blocks()` - ✅ Read-only
- `resolve_blocks()` - ✅ Read-only

**LOC**: ~30 removed

#### 4. Update tests

**File**: `tests/unit/test_schema_registry.py`

Remove global state tests:
```python
# REMOVE: No longer valid
def test_register_schema():
    schemas.register(schema)  # No longer public

# KEEP: Test discovery
def test_discover_schemas():
    result = SchemaRegistry.discover([100, 1300])
    assert 100 in result
    assert 1300 in result
```

**LOC**: ~50 changed

#### 5. Update V2Client (already done)

V2Client already has `register_schema()` instance method:
```python
def register_schema(self, schema: BlockSchema):
    """Register custom schema with this client."""
    self.parser.register_schema(schema)
```

No changes needed!

### Deliverables

- [ ] `bluetti_sdk/schemas/registry.py` - Immutable registry
- [ ] `bluetti_sdk/schemas/__init__.py` - Initialize built-ins
- [ ] `tests/unit/test_schema_registry.py` - Updated tests
- [ ] Migration notes in `docs/migration/instance-registry.md`

### Acceptance Criteria

- [ ] SchemaRegistry is immutable after module import
- [ ] No global mutation methods in public API
- [ ] Tests don't use global state cleanup
- [ ] All tests pass
- [ ] Client.register_schema() is documented pattern

**Estimated LOC**: ~150 changed
**Estimated Effort**: 1 PR, 3-4 hours

---

## Increment C: Typed Transforms

**Goal**: Type-safe transform composition with IDE support

**ADR**: [ADR-004](ADR-004-typed-transforms.md)

### Implementation Steps

#### 1. Create transform base classes

**File**: `bluetti_sdk/transforms/base.py`

```python
from abc import ABC, abstractmethod
from typing import Any, Callable, List


class Transform(ABC):
    """Base transform class."""

    @abstractmethod
    def compile(self) -> Callable[[Any], Any]:
        """Compile to runtime function."""

    def __or__(self, other: "Transform") -> "Pipeline":
        """Compose transforms using | operator."""
        return Pipeline([self, other])


class Pipeline(Transform):
    """Compose multiple transforms."""

    def __init__(self, transforms: List[Transform]):
        self.transforms = transforms

    def compile(self) -> Callable[[Any], Any]:
        """Compile to composed function."""
        fns = [t.compile() for t in self.transforms]

        def composed(x):
            for fn in fns:
                x = fn(x)
            return x

        return composed

    def __or__(self, other: Transform) -> "Pipeline":
        return Pipeline([*self.transforms, other])
```

**LOC**: ~50

#### 2. Implement numeric transforms

**File**: `bluetti_sdk/transforms/numeric.py`

```python
from typing import Callable, Any
from .base import Transform


class Scale(Transform):
    """Scale by factor."""

    def __init__(self, factor: float):
        if factor == 0:
            raise ValueError("Scale factor cannot be zero")
        self.factor = factor

    def compile(self) -> Callable[[Any], Any]:
        return lambda x: x * self.factor


class Minus(Transform):
    """Subtract offset."""

    def __init__(self, offset: float):
        self.offset = offset

    def compile(self) -> Callable[[Any], Any]:
        return lambda x: x - self.offset


class Abs(Transform):
    """Absolute value."""

    def compile(self) -> Callable[[Any], Any]:
        return abs


class Clamp(Transform):
    """Clamp value to range."""

    def __init__(self, min_val: float, max_val: float):
        if min_val >= max_val:
            raise ValueError("min must be less than max")
        self.min = min_val
        self.max = max_val

    def compile(self) -> Callable[[Any], Any]:
        return lambda x: max(self.min, min(self.max, x))
```

**LOC**: ~60

#### 3. Implement bitwise transforms

**File**: `bluetti_sdk/transforms/bitwise.py`

```python
from typing import Callable, Any
from .base import Transform


class Bitmask(Transform):
    """Apply bitmask."""

    def __init__(self, mask: int):
        if mask < 0:
            raise ValueError("Bitmask must be non-negative")
        self.mask = mask

    def compile(self) -> Callable[[Any], Any]:
        return lambda x: x & self.mask


class Shift(Transform):
    """Bit shift (left if positive, right if negative)."""

    def __init__(self, bits: int):
        self.bits = bits

    def compile(self) -> Callable[[Any], Any]:
        if self.bits >= 0:
            return lambda x: x << self.bits
        else:
            return lambda x: x >> abs(self.bits)
```

**LOC**: ~40

#### 4. Update Field to accept typed transforms

**File**: `bluetti_sdk/protocol/v2/schema.py`

```python
from typing import Union, List, Optional, Callable
from bluetti_sdk.transforms import Transform

@dataclass(frozen=True)
class Field:
    name: str
    offset: int
    type: "DataType"
    unit: Optional[str] = None
    required: bool = True
    transform: Optional[Union[Transform, List[str]]] = None  # NEW: Accept typed
    min_protocol_version: Optional[int] = None
    description: Optional[str] = None
    _compiled_transform: Optional[Callable] = dataclass_field(
        default=None, init=False, repr=False
    )

    def __post_init__(self):
        # Compile transform at schema definition time
        if self.transform is None:
            object.__setattr__(self, "_compiled_transform", None)
        elif isinstance(self.transform, Transform):
            # NEW: Compile typed transform
            object.__setattr__(
                self, "_compiled_transform", self.transform.compile()
            )
        elif isinstance(self.transform, list):
            # Existing: Parse string DSL
            from ..transforms import parse_transform_pipeline
            object.__setattr__(
                self, "_compiled_transform", parse_transform_pipeline(self.transform)
            )
        else:
            raise TypeError(
                f"transform must be Transform or List[str], got {type(self.transform)}"
            )
```

**LOC**: ~30 changed

#### 5. Write comprehensive tests

**File**: `tests/unit/transforms/test_typed_transforms.py`

```python
import pytest
from bluetti_sdk.transforms import Scale, Minus, Abs, Clamp, Bitmask, Shift


def test_scale_transform():
    """Test Scale transform."""
    transform = Scale(0.1)
    fn = transform.compile()
    assert fn(100) == 10.0


def test_scale_zero_raises():
    """Test Scale with zero factor raises."""
    with pytest.raises(ValueError, match="cannot be zero"):
        Scale(0)


def test_minus_transform():
    """Test Minus transform."""
    transform = Minus(40)
    fn = transform.compile()
    assert fn(60) == 20


def test_abs_transform():
    """Test Abs transform."""
    transform = Abs()
    fn = transform.compile()
    assert fn(-5) == 5


def test_clamp_transform():
    """Test Clamp transform."""
    transform = Clamp(0, 100)
    fn = transform.compile()
    assert fn(-10) == 0
    assert fn(50) == 50
    assert fn(150) == 100


def test_pipeline_composition():
    """Test transform composition with | operator."""
    pipeline = Minus(40) | Scale(0.1) | Clamp(0, 100)
    fn = pipeline.compile()

    # (60 - 40) * 0.1 = 2.0
    assert fn(60) == 2.0


def test_field_accepts_typed_transform():
    """Test Field accepts typed transform."""
    from bluetti_sdk.protocol.v2.schema import Field
    from bluetti_sdk.protocol.v2.datatypes import UInt16

    field = Field(
        name="voltage",
        offset=0,
        type=UInt16(),
        transform=Scale(0.1)
    )

    assert field._compiled_transform is not None
    assert field._compiled_transform(100) == 10.0


def test_field_backward_compatible_string_dsl():
    """Test Field still accepts string DSL."""
    from bluetti_sdk.protocol.v2.schema import Field
    from bluetti_sdk.protocol.v2.datatypes import UInt16

    field = Field(
        name="voltage",
        offset=0,
        type=UInt16(),
        transform=["scale:0.1"]  # Old string DSL
    )

    assert field._compiled_transform is not None
```

**LOC**: ~150

#### 6. Migrate Block 100 declarative (example)

**File**: `bluetti_sdk/schemas/block_100_declarative.py`

```python
# Before (string DSL)
pack_voltage: float = block_field(
    offset=0,
    type=UInt16(),
    transform=["scale:0.1"],  # String DSL
    unit="V",
)

# After (typed transforms)
from bluetti_sdk.transforms import Scale

pack_voltage: float = block_field(
    offset=0,
    type=UInt16(),
    transform=Scale(0.1),  # Type-safe!
    unit="V",
)
```

**LOC**: ~50 changed (example migration)

### Deliverables

- [ ] `bluetti_sdk/transforms/base.py` - Transform base class
- [ ] `bluetti_sdk/transforms/numeric.py` - Numeric transforms
- [ ] `bluetti_sdk/transforms/bitwise.py` - Bitwise transforms
- [ ] `bluetti_sdk/transforms/__init__.py` - Public API
- [ ] `bluetti_sdk/protocol/v2/schema.py` - Field accepts typed transforms
- [ ] `tests/unit/transforms/test_typed_transforms.py` - Comprehensive tests
- [ ] `bluetti_sdk/schemas/block_100_declarative.py` - Migration example
- [ ] `docs/migration/typed-transforms.md` - Migration guide

### Acceptance Criteria

- [ ] All transform classes implemented
- [ ] Pipeline composition with | operator
- [ ] Field accepts Union[Transform, List[str]]
- [ ] Backward compatible with string DSL
- [ ] 100% test coverage for transforms
- [ ] Block 100 migrated as example
- [ ] Documentation and migration guide

**Estimated LOC**: ~500 total
**Estimated Effort**: 1 PR, 6-8 hours

---

## Summary

| Increment | ADR | Files | LOC | Effort | Dependencies |
|-----------|-----|-------|-----|--------|--------------|
| A: AsyncV2Client | ADR-001 | 4 new | ~350 | 4-6h | None |
| B: Instance Registry | ADR-002 | 3 modified | ~150 | 3-4h | None |
| C: Typed Transforms | ADR-004 | 8 new/modified | ~500 | 6-8h | None |

**Total**: ~1000 LOC, 13-18 hours

All increments are **independent** and can be implemented in parallel or sequentially.

## Next Steps

1. Review ADR documents
2. Get approval for implementation order
3. Start Increment A (AsyncV2Client)
4. Test, document, merge
5. Repeat for B and C

Ready to start? 🚀
