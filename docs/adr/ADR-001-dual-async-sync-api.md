# ADR-001: Dual Async/Sync Client API

**Status**: Proposed
**Date**: 2026-02-14
**Author**: Zeus Fabric Team

## Context

Current V2Client is purely synchronous, blocking on I/O operations:
- `client.read_block()` blocks on MQTT transport
- Not suitable for async applications (FastAPI, asyncio apps)
- Forces async apps to use `run_in_executor()` workarounds

### Problem

Users building async applications need native async support without:
- Breaking existing synchronous API
- Duplicating all client logic
- Maintaining two separate codebases

### Requirements

1. Native async API for modern Python apps
2. Zero breaking changes to existing sync API
3. Shared business logic (no duplication)
4. Clear migration path for users

## Decision

Implement **dual API pattern** with `AsyncV2Client` facade:

### Architecture

```
AsyncV2Client (facade, async methods)
    ↓ delegates via asyncio.to_thread()
V2Client (existing, sync implementation)
    ↓ contains all business logic
[Transport, Parser, Device layers]
```

### Public API

```python
# NEW: Async facade
async with AsyncV2Client(transport, profile) as client:
    await client.connect()
    block = await client.read_block(100)
    state = await client.get_device_state()

# EXISTING: Sync API unchanged
with V2Client(transport, profile) as client:
    client.connect()
    block = client.read_block(100)
    state = client.get_device_state()
```

### Implementation Strategy

**Phase 1**: AsyncV2Client facade using `asyncio.to_thread()`
- Wraps existing V2Client
- Each async method delegates to sync via thread pool
- Zero changes to V2Client internals
- Works with existing sync transports

**Phase 2** (future): Native async transport
- Create AsyncMQTTTransport using aiomqtt
- AsyncV2Client detects async transport, calls directly
- Still supports sync transport via to_thread()

## Consequences

### Positive

✅ Users get async API immediately
✅ Zero breaking changes to sync API
✅ Single source of truth (V2Client business logic)
✅ Natural migration path (sync → async)
✅ Thread pool overhead only when needed

### Negative

⚠️ Thread pool overhead with sync transport
⚠️ Not "true" async until Phase 2 (async transport)
⚠️ Need to maintain both APIs long-term

### Mitigation

- Thread pool overhead negligible for I/O-bound operations
- Document performance characteristics clearly
- Provide async transport in Phase 2
- Sync API remains for simple scripts/tools

## Implementation Plan

### Increment A

1. Create `AsyncV2Client` in `power_sdk/client_async.py`
2. Implement async methods wrapping V2Client via `to_thread()`
3. Add async context manager support
4. Write comprehensive async tests
5. Update documentation with async examples

### Files to Create

- `power_sdk/client_async.py` - AsyncV2Client facade
- `tests/unit/test_client_async.py` - Async client tests
- `docs/examples/async_usage.py` - Usage examples

### Public API Changes

```python
# New export in power_sdk/__init__.py
from .client_async import AsyncV2Client

__all__ = [
    "BluettiClient",      # Existing sync
    "AsyncV2Client",      # NEW async facade
    # ... rest unchanged
]
```

## References

- [asyncio.to_thread() documentation](https://docs.python.org/3/library/asyncio-task.html#asyncio.to_thread)
- [Facade pattern](https://refactoring.guru/design-patterns/facade)
- Similar approach: `aiohttp.ClientSession` (sync → async migration)

## Acceptance Criteria

- [ ] AsyncV2Client implements all V2Client public methods
- [ ] 100% test coverage for async facade
- [ ] No changes to existing V2Client code
- [ ] All existing tests pass unchanged
- [ ] Documentation updated with async examples
- [ ] Performance benchmarks (thread pool overhead < 1ms)

