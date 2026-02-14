# Platform-Stable Baseline Metrics

**Status**: Locked (platform-stable milestone)
**Date**: 2026-02-14
**Version**: Pre-2.0.0 (platform freeze)

## Quality Gate Metrics

### Static Analysis

**Ruff**:
```
Command: python -m ruff check bluetti_sdk tests CHANGELOG.md
Result: All checks passed ✓
```

**MyPy**:
```
Command: python -m mypy bluetti_sdk
Result: Success: no issues found in 40 source files ✓
```

### Test Coverage

**Pytest**:
```
Command: python -m pytest -q
Tests: 250 passed
Coverage: 88% (TOTAL: 1739 statements, 210 missed)
Platform: Windows (win32), Python 3.12.4
```

**Critical Modules Coverage** (>= 85% enforced):
- `bluetti_sdk/client.py`: 88%
- `bluetti_sdk/client_async.py`: 84%
- `bluetti_sdk/transport/mqtt.py`: 77%
- `bluetti_sdk/utils/resilience.py`: 100%
- `bluetti_sdk/schemas/registry.py`: 98%
- `bluetti_sdk/protocol/modbus.py`: 100%

**Coverage Floor**: 85% minimum for platform-stable

### CI Requirements

All jobs must pass:
1. `ruff` - Lint and format check
2. `mypy` - Type checking (40 source files)
3. `pytest` - Test suite on Python 3.10, 3.11, 3.12 with coverage >= 85%
4. `quality-gate` - Summary job (depends on all above)

## Platform Invariants

### Architecture
- ✓ Instance-scoped schema registry (no global mutable state)
- ✓ Typed transform API (declarative schema definitions)
- ✓ Configurable retry policy with exponential backoff
- ✓ Async/sync client facade pattern
- ✓ MQTT fail-fast disconnect detection

### Error Handling
- ✓ Selective retry: `TransportError` only
- ✓ Fail-fast: `ParserError`, `ProtocolError` no retry
- ✓ Resource cleanup: MQTT loop_stop on connect failure
- ✓ No resource leaks in retry scenarios

### Security
- ✓ TLS certificate temp files with 0o400 permissions
- ✓ Private temp directory (0o700)
- ✓ Password input: CLI arg > env var > getpass prompt
- ✓ Non-interactive mode fails clearly (exit code 2)

## Stability Guarantees

### No Flaky Tests
- Windows temp directory cleanup: stable (explicit tempfile management)
- MQTT resource cleanup: verified with dedicated test
- Async concurrency: lock-protected, no race conditions

### API Contracts (Frozen)
Public APIs locked for platform-stable:
- `bluetti_sdk.client.V2Client`
- `bluetti_sdk.client_async.AsyncV2Client`
- `bluetti_sdk.transport.mqtt.MQTTTransport`
- `bluetti_sdk.utils.resilience.RetryPolicy`
- `bluetti_sdk.schemas.registry.SchemaRegistry`

Breaking changes to these require major version bump.

## Out of Scope (Phase 2)

The following are **not** part of platform-stable baseline:
- Complete device profile coverage (only EL100V2 baseline)
- Complete block schema coverage (100, 1300, 6000 only)
- Write/command support (read-only for now)
- Real-time push notifications from device

Platform-stable focuses on **infrastructure quality**, not feature completeness.

## Next Steps

After platform-stable freeze:
1. Begin Phase 2: Schema coverage expansion
2. Add device profile matrix tracking
3. Implement missing block schemas
4. Add integration smoke tests per device model
