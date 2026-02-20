# Platform API Contracts

Status: active

This document defines the current public API for the runtime-first platform.

## Public API (stable)

### `power_sdk.Client`
- Sync client with dependency injection for parser/protocol/transport.
- Core methods: `connect()`, `disconnect()`, `read_block()`, `read_group()`, `stream_group()`.

### `power_sdk.AsyncClient`
- Async facade over `Client`.
- Read operations are concurrent-safe at async layer; transport serializes I/O.
- Core methods mirror `Client` (`read_block`, `read_group`, `astream_group`).

### `power_sdk.transport.MQTTTransport`
- MQTT transport implementation behind `TransportProtocol`.
- Implements `connect()`, `disconnect()`, `send_frame()`, `is_connected()`.

### `power_sdk.runtime.RuntimeRegistry`
- Runtime-first orchestration entrypoint.
- Builds N device runtimes from YAML:
  - `RuntimeRegistry.from_config(path)`
  - `dry_run()` (no I/O)
  - `poll_all_once()`

### `power_sdk.runtime.Executor`
- Async per-device loop engine for pull/push runtime modes.
- Supports graceful stop, per-device metrics, and sink fan-out.

### `power_sdk.DeviceProfile`
- Stable profile container used by clients and plugin loaders.

### `power_sdk.ParserInterface`
- Stable parser contract used for parser dependency injection.

### `power_sdk.ReadGroupResult`
- Structured result type returned by `read_group_ex()`.

## Runtime-first usage contract

`runtime.yaml` must define:
- `version: 1`
- `pipelines:` mapping
- `devices:` entries with `pipeline` and `profile_id`

CLI contract:
- `power-cli runtime --config runtime.yaml --dry-run`
- `power-cli runtime --config runtime.yaml --once`

## Not public / internal

The following are internal and can change without notice:
- `power_sdk.bootstrap.*` helper functions
- plugin parser internals under `power_sdk.plugins.*.protocol.*`
- historical architecture docs that reference legacy names

## Breaking-change policy

- Patch: bug fixes only, no public API break.
- Minor: additive changes only.
- Major: public API removals/signature breaks allowed.
