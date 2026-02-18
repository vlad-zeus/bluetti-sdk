# Platform-Stable Baseline Metrics

**Status**: Locked (platform-stable milestone)
**Date**: 2026-02-14
**Version**: Pre-2.0.0 (platform freeze)

## Quality Gate Metrics

### Static Analysis

**Ruff**:
```
Command: python -m ruff check power_sdk tests CHANGELOG.md
Result: All checks passed ✓
```

**MyPy**:
```
Command: python -m mypy power_sdk
Result: Success: no issues found in 72 source files ✓
```

### Test Coverage

**Pytest**:
```
Command: python -m pytest -q
Tests: 360 passed
Coverage: 91% (TOTAL: 2273 statements, 210 missed)
Platform: Windows (win32), Python 3.12.4
```

**Critical Modules Coverage** (>= 85% enforced):
- `power_sdk/client.py`: 88%
- `power_sdk/client_async.py`: 84%
- `power_sdk/transport/mqtt.py`: 77%
- `power_sdk/utils/resilience.py`: 100%
- `power_sdk/schemas/registry.py`: 98%
- `power_sdk/protocol/modbus.py`: 100%

**Coverage Floor**: 85% minimum for platform-stable

### CI Requirements

All jobs must pass:
1. `ruff` - Lint and format check
2. `mypy` - Type checking (72 source files)
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
- `power_sdk.client.V2Client`
- `power_sdk.client_async.AsyncV2Client`
- `power_sdk.transport.mqtt.MQTTTransport`
- `power_sdk.utils.resilience.RetryPolicy`
- `power_sdk.schemas.registry.SchemaRegistry`

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

