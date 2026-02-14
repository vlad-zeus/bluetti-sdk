# Platform API Contracts

**Status**: Frozen (platform-stable)
**Semver Policy**: Breaking changes require major version bump

## Stability Guarantee

These APIs are **public and stable**. Any breaking changes will follow semantic versioning:
- Patch (x.y.Z): Bug fixes, no API changes
- Minor (x.Y.0): New features, backward compatible
- Major (X.0.0): Breaking changes allowed

## Public API Surface

### 1. `bluetti_sdk.client.V2Client`

**Synchronous client for V2 protocol devices.**

```python
class V2Client:
    def __init__(
        self,
        transport: TransportProtocol,
        profile: DeviceProfile,
        device_address: int = 1,
        parser: Optional[V2ParserInterface] = None,
        device: Optional[DeviceModelInterface] = None,
        schema_registry: Optional[SchemaRegistry] = None,
        retry_policy: Optional[RetryPolicy] = None,
    ) -> None: ...

    def connect(self) -> None: ...
    def disconnect(self) -> None: ...
    def is_connected(self) -> bool: ...

    def read_block(
        self, block_id: int, register_count: Optional[int] = None
    ) -> ParsedBlock: ...

    def read_group(
        self, group: BlockGroup, partial_ok: bool = True
    ) -> list[ParsedBlock]: ...

    def read_group_ex(
        self, group: BlockGroup, partial_ok: bool = True
    ) -> GroupReadResult: ...
```

**Contract Guarantees**:
- `connect()` retries on `TransportError` according to `retry_policy`
- `read_block()` retries transient errors, fails fast on parsing/protocol errors
- `read_group()` returns partial results if `partial_ok=True`
- All methods raise documented exceptions: `TransportError`, `ParserError`, `ProtocolError`

---

### 2. `bluetti_sdk.client_async.AsyncV2Client`

**Async facade over V2Client with concurrency safety.**

```python
class AsyncV2Client:
    def __init__(
        self,
        transport: TransportProtocol,
        profile: DeviceProfile,
        device_address: int = 1,
        parser: V2ParserInterface | None = None,
        device: DeviceModelInterface | None = None,
        schema_registry: SchemaRegistry | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None: ...

    async def connect(self) -> None: ...
    async def disconnect(self) -> None: ...

    async def read_block(
        self, block_id: int, register_count: int | None = None
    ) -> ParsedBlock: ...

    async def read_group(
        self, group: BlockGroup, partial_ok: bool = True
    ) -> list[ParsedBlock]: ...

    async def read_group_ex(
        self, group: BlockGroup, partial_ok: bool = True
    ) -> GroupReadResult: ...

    # Context manager support
    async def __aenter__(self) -> AsyncV2Client: ...
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool: ...
```

**Contract Guarantees**:
- All operations serialized via internal `asyncio.Lock`
- Safe for concurrent `asyncio.gather()` calls
- Context manager handles cleanup even on connect failure
- Delegates retry logic to underlying sync client

---

### 3. `bluetti_sdk.transport.mqtt.MQTTTransport`

**MQTT transport implementation for V2 devices.**

```python
@dataclass
class MQTTConfig:
    broker: str = "iot.bluettipower.com"
    port: int = 18760
    device_sn: str = ""
    pfx_cert: Optional[bytes] = None
    pfx_password: Optional[str] = None
    keepalive: int = 60

class MQTTTransport(TransportProtocol):
    def __init__(self, config: MQTTConfig) -> None: ...

    def connect(self) -> None: ...
    def disconnect(self) -> None: ...
    def is_connected(self) -> bool: ...

    def send_frame(self, frame: bytes, timeout: float = 5.0) -> bytes: ...
```

**Contract Guarantees**:
- `connect()` performs safe cleanup on failure (no resource leaks)
- `send_frame()` fails fast on disconnect (no full timeout wait)
- TLS certificates written to private temp dir (0o700) with 0o400 file permissions
- Cleanup happens in `disconnect()` and on exceptions

---

### 4. `bluetti_sdk.utils.resilience.RetryPolicy`

**Configurable retry behavior with exponential backoff.**

```python
@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    initial_delay: float = 0.5
    backoff_factor: float = 2.0
    max_delay: float = 5.0

    def __post_init__(self) -> None: ...  # Validates parameters

def iter_delays(policy: RetryPolicy) -> Iterator[float]: ...
```

**Contract Guarantees**:
- Immutable (frozen dataclass)
- Validates parameters in `__post_init__`
- Exponential backoff: delay = min(initial_delay * backoff_factor^attempt, max_delay)
- `iter_delays()` yields `max_attempts - 1` delay values

---

### 5. `bluetti_sdk.schemas.registry.SchemaRegistry`

**Instance-scoped schema registry (no global mutable state).**

```python
class SchemaRegistry:
    def __init__(self) -> None: ...

    def get_schema(self, block_id: int) -> Optional[BlockSchema]: ...
    def has_schema(self, block_id: int) -> bool: ...
    def list_block_ids(self) -> list[int]: ...

    @staticmethod
    def new_registry_with_builtins() -> SchemaRegistry: ...

def register_builtin_schemas(registry: SchemaRegistry) -> None: ...
```

**Contract Guarantees**:
- Each client gets isolated instance via `new_registry_with_builtins()`
- No global mutable state
- Built-in schemas immutable after registration
- Custom schemas can be added to instance without affecting others

---

## Internal/Private APIs

The following are **not stable** and may change without major version bump:

### Parser Internals
- `bluetti_sdk.protocol.v2.parser.V2Parser` (internal)
- `bluetti_sdk.protocol.modbus.*` (internal protocol layer)

### Device Model
- `bluetti_sdk.models.device.V2Device` (internal state tracking)

### Schema Internals
- `bluetti_sdk.schemas.declarative._declare_field()` (private)
- `bluetti_sdk.schemas.registry._register_builtin()` (private init-only)

### Transform Internals
- `bluetti_sdk.protocol.v2.transforms.*` implementation details

## Deprecation Policy

When deprecating public APIs:
1. Mark with `@deprecated` decorator
2. Add `DeprecationWarning` in runtime
3. Document removal version in docstring
4. Keep deprecated API for at least one minor version
5. Remove only in major version bump

## Example Usage Contracts

### Safe Retry Usage
```python
from bluetti_sdk.utils.resilience import RetryPolicy

# Custom retry policy
policy = RetryPolicy(
    max_attempts=5,
    initial_delay=1.0,
    max_delay=10.0,
)

client = V2Client(transport, profile, retry_policy=policy)
# connect() will retry up to 5 times on TransportError
client.connect()
```

### Async Concurrency
```python
async with AsyncV2Client(transport, profile) as client:
    # Safe concurrent reads
    results = await asyncio.gather(
        client.read_block(100),
        client.read_block(1300),
        client.read_block(6000),
    )
```

### Schema Registry Isolation
```python
# Each client gets independent registry
client1 = V2Client(transport, profile1)  # Own registry
client2 = V2Client(transport, profile2)  # Different registry
# No interference between clients
```

## Breaking Change Examples

**Allowed in Patch** (x.y.Z):
- Fix bug in retry logic
- Fix resource leak
- Improve error messages

**Allowed in Minor** (x.Y.0):
- Add new optional parameter with default
- Add new method to client
- Add new built-in schema

**Requires Major** (X.0.0):
- Remove public method
- Change method signature (required params)
- Change exception hierarchy
- Remove support for Python version
