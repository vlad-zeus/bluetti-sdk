# Runtime DSL Specification (v1)

> **Status:** Stable — `power_sdk.runtime` Phase 4+5
> **Schema version:** `version: 1`

The runtime DSL is a YAML-based declarative description of one or more device
polling/push pipelines.  It is the single source of truth for:

- Which vendor/protocol plugin handles a device
- How data is transported (MQTT, …)
- Whether the device is polled periodically (pull) or event-driven (push)
- Where snapshots are written (memory ring-buffer, JSONL, composite)

---

## Top-level structure

```yaml
version: 1              # required; only 1 is supported

pipelines:              # optional; named pipeline templates
  <name>:
    mode: pull | push   # default: pull
    transport: mqtt     # registered TransportFactory key
    vendor: <str>       # PluginRegistry vendor
    protocol: <str>     # PluginRegistry protocol

sinks:                  # optional; named output sinks
  <name>:
    type: memory | jsonl | composite
    # type-specific fields (see below)

defaults:               # optional; fallback values for all devices
  poll_interval: 30     # seconds (> 0)
  sink: <sink_name>
  transport:
    key: mqtt
    opts:
      broker: "..."

devices:                # required; list of device entries
  - id: <device_id>     # unique string
    profile_id: <str>   # resolved via plugin's profile_loader
    pipeline: <name>    # optional; references pipelines section
    poll_interval: <n>  # per-device override (> 0)
    sink: <name>        # per-device sink override
    transport:
      key: <str>        # per-device transport key override
      opts:
        <key>: <value>  # transport-specific options
    options:
      device_address: 1
```

---

## Pipeline templates (`pipelines:`)

A pipeline template declares the *type* of connection a group of devices uses.
It overrides `defaults.transport.key`, `defaults.vendor`, and `defaults.protocol`
for any device that references it.

```yaml
pipelines:
  bluetti_mqtt_pull:
    mode: pull
    transport: mqtt
    vendor: bluetti
    protocol: v2
```

**Stage validation** (`StageResolver`) runs at `RuntimeRegistry.from_config()` time:

| Stage | Validated against |
|---|---|
| `transport` | `TransportFactory.list_transports()` |
| `vendor` + `protocol` | `PluginRegistry.get(vendor, protocol)` |
| Plugin factories | `parser_factory`, `protocol_layer_factory`, `profile_loader` all non-None |

If any stage fails, a `ValueError` is raised before any connection is attempted.

---

## Modes

| Mode | Description |
|---|---|
| `pull` | `DeviceRuntime.poll_once()` called every `poll_interval` seconds |
| `push` | Transport delivers data via callback; `PushCallbackAdapter.on_data()` |

---

## Sinks (`sinks:`)

### `memory`

In-memory ring-buffer per device. Thread-safe for read queries.

```yaml
sinks:
  my_memory:
    type: memory
    maxlen: 200   # default: 100
```

### `jsonl`

Appends one JSON line per snapshot. No external dependencies.

```yaml
sinks:
  my_log:
    type: jsonl
    path: /var/log/power_sdk/runtime.jsonl
```

### `composite`

Fan-out to multiple named sinks.

```yaml
sinks:
  combined:
    type: composite
    sinks:
      - my_memory
      - my_log
```

Cycle detection is enforced at validation time.

---

## Write gate

Write operations are gated by `PluginCapabilities`:

```python
manifest.can_write()              # respects requires_device_validation_for_write
manifest.can_write(force=True)    # bypasses validation requirement; not supports_write
```

The `--dry-run` Stage Resolution table shows a `write` column per device.

---

## Precedence rules

For any resolved field, the lookup order is:
1. Per-device entry (`devices[*]`)
2. Pipeline template (`pipelines.<name>`)
3. Global defaults (`defaults`)
4. Built-in defaults (e.g. `poll_interval=30`)

---

## Example

```yaml
version: 1

pipelines:
  bluetti_pull:
    mode: pull
    transport: mqtt
    vendor: bluetti
    protocol: v2

sinks:
  mem:
    type: memory
    maxlen: 100
  log:
    type: jsonl
    path: /tmp/runtime.jsonl
  all:
    type: composite
    sinks: [mem, log]

defaults:
  poll_interval: 30
  sink: all
  transport:
    opts:
      broker: "${MQTT_BROKER}"

devices:
  - id: living_room
    pipeline: bluetti_pull
    profile_id: EL100V2
    transport:
      opts:
        device_sn: "${SN_LIVING_ROOM}"
        cert_password: "${PW_LIVING_ROOM}"
```
