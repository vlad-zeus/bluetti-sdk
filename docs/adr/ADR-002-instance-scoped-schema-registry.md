# ADR-002: Instance-Scoped Schema Registry

**Status**: Proposed
**Date**: 2026-02-14
**Author**: Zeus Fabric Team

## Context

Current architecture has **global mutable state** in schema registry:

```python
# Global mutable registry (current)
from power_sdk import schemas

schemas.register(my_schema)  # Mutates global state
schemas.get(100)             # Reads global state
```

### Problems

1. **Test isolation**: Tests can't run in parallel, share registry state
2. **Runtime coupling**: All clients share same schemas globally
3. **Multi-tenant risk**: Different devices might need different schema versions
4. **Thread safety**: Global mutable state requires locking

### Current Workarounds

```python
# In tests - manual cleanup
def teardown():
    schemas._clear_for_testing()  # Fragile, breaks isolation
```

## Decision

Migrate to **instance-scoped registry** within V2Client:

### Architecture

```
V2Client
  ├── parser: V2Parser
  │     └── _schemas: Dict[int, BlockSchema]  # Instance state
  └── profile: DeviceProfile
        └── groups: BlockGroup definitions

# Registry becomes discovery helper only
SchemaRegistry (immutable)
  └── discover(block_ids) -> Dict[int, BlockSchema]
```

### Key Principles

1. **Each V2Client instance owns its schema state**
2. **Global registry becomes immutable discovery catalog**
3. **Auto-registration at client initialization**
4. **No runtime global mutations**

## Design

### Phase 1: V2Client owns schemas

```python
class V2Client:
    def __init__(self, transport, profile, parser=None):
        self.parser = parser or V2Parser()

        # Auto-register schemas for this client
        self._register_schemas_from_profile()

    def _register_schemas_from_profile(self):
        """Register schemas needed by this device profile."""
        block_ids = self._collect_block_ids()
        schemas = SchemaRegistry.discover(block_ids)

        for schema in schemas.values():
            self.parser.register_schema(schema)
```

### Phase 2: Immutable global registry

```python
# Global registry becomes immutable discovery catalog
class SchemaRegistry:
    _schemas: Dict[int, BlockSchema] = {}  # Module-level, immutable after init

    @classmethod
    def discover(cls, block_ids: List[int]) -> Dict[int, BlockSchema]:
        """Discover schemas (immutable read-only operation)."""
        return {bid: cls._schemas[bid] for bid in block_ids if bid in cls._schemas}

    @classmethod
    def register_builtin(cls, schemas: List[BlockSchema]):
        """Register built-in schemas at module initialization (once)."""
        # Only called once during module import
        for schema in schemas:
            cls._schemas[schema.block_id] = schema
```

## Consequences

### Positive

✅ **Test isolation**: Each test creates independent client
✅ **Thread safety**: No shared mutable state
✅ **Multi-tenant safe**: Different clients = different schemas
✅ **Cleaner API**: Schema registration happens at client init
✅ **Easier reasoning**: State lives where it's used

### Negative

⚠️ **Migration effort**: Tests need minor updates
⚠️ **Memory**: Each client has schema dict (negligible - schemas are shared references)

### Migration

**Before** (global):
```python
from power_sdk import schemas
schemas.register(custom_schema)
client = V2Client(transport, profile)
```

**After** (instance):
```python
client = V2Client(transport, profile)
client.register_schema(custom_schema)  # Instance method
```

## Implementation Plan

### Increment B

1. **Keep global registry for discovery only**
   - Make SchemaRegistry.discover() read-only
   - Remove runtime mutations

2. **Move registration to V2Client**
   - `V2Client.register_schema()` → delegates to parser
   - Auto-register from profile at init
   - Remove `schemas.register()` from public API

3. **Update tests**
   - Remove global registry cleanup
   - Use client.register_schema() for custom schemas

4. **Deprecate global mutations**
   - Document new pattern
   - Add migration guide

### Files to Modify

- `power_sdk/schemas/registry.py` - Make immutable
- `power_sdk/client.py` - Already has `register_schema()`
- `tests/unit/test_schema_registry.py` - Test immutable discovery
- `tests/unit/test_client.py` - Test instance registration

### API Changes

```python
# REMOVE from public API
schemas.register()       # ❌ Global mutation
schemas.register_many()  # ❌ Global mutation

# KEEP for discovery
schemas.discover()       # ✅ Read-only discovery
schemas.get()           # ✅ Read-only lookup

# NEW in V2Client
client.register_schema(schema)  # ✅ Instance registration
```

## References

- Dependency Injection pattern (already in V2Client)
- Immutable registries in Django, FastAPI (app startup only)
- Test isolation best practices

## Acceptance Criteria

- [ ] SchemaRegistry is immutable after module import
- [ ] V2Client owns all schema registration
- [ ] Tests run in parallel without isolation issues
- [ ] No global mutable state in runtime
- [ ] Migration guide documented
- [ ] All tests pass with new pattern

