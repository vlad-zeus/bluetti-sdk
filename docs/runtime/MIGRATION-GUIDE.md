# Migration Guide — Runtime DSL

## From legacy `devices.yaml` to pipeline-first `runtime.yaml`

### Overview

The legacy format places vendor, protocol, and transport directly on each
device entry.  The new pipeline-first format extracts these into named
pipeline templates and references them by name — reducing duplication and
enabling stage validation before any connection is attempted.

**Both formats are fully supported and backward-compatible.**

---

## Step 1 — Identify shared configuration

Look for device entries that share the same `vendor`, `protocol`, and
`transport.key`.  These are candidates for a shared pipeline template.

**Before (legacy):**

```yaml
version: 1
defaults:
  transport:
    key: mqtt
    opts:
      broker: "${MQTT_BROKER}"
  poll_interval: 30

devices:
  - id: dev1
    vendor: bluetti
    protocol: v2
    profile_id: EL100V2
    transport:
      opts:
        device_sn: "${SN1}"
        cert_password: "${PW1}"

  - id: dev2
    vendor: bluetti
    protocol: v2
    profile_id: EL100V2
    poll_interval: 60
    transport:
      opts:
        device_sn: "${SN2}"
        cert_password: "${PW2}"
```

---

## Step 2 — Extract a pipeline template

Move `vendor`, `protocol`, `transport.key` (and `mode`) into a named pipeline.

**After (pipeline-first):**

```yaml
version: 1

pipelines:
  bluetti_pull:
    mode: pull
    transport: mqtt
    vendor: bluetti
    protocol: v2

defaults:
  poll_interval: 30
  transport:
    opts:
      broker: "${MQTT_BROKER}"

devices:
  - id: dev1
    pipeline: bluetti_pull
    profile_id: EL100V2
    transport:
      opts:
        device_sn: "${SN1}"
        cert_password: "${PW1}"

  - id: dev2
    pipeline: bluetti_pull
    profile_id: EL100V2
    poll_interval: 60
    transport:
      opts:
        device_sn: "${SN2}"
        cert_password: "${PW2}"
```

---

## Step 3 — Verify with `--dry-run`

```bash
python -m power_sdk runtime --config runtime.yaml --dry-run
```

The Stage Resolution section confirms that plugin stages resolved:

```
Stage Resolution:
  device_id           pipeline        mode  parser        model         write
  ------------------  --------------  ----  ------------  ------------  -----
  dev1                bluetti_pull    pull  bluetti/v2    bluetti/v2    No
  dev2                bluetti_pull    pull  bluetti/v2    bluetti/v2    No
```

---

## Behavior differences

| Aspect | Legacy format | Pipeline-first format |
|---|---|---|
| Stage validation | None — errors surface at connection time | Fail-fast before any I/O |
| `--dry-run` output | Device table only | Device table + Stage Resolution |
| Push mode | Not supported | `mode: push` in pipeline template |
| Plugin key in output | `?` | Resolved `vendor/protocol` key |

---

## Preserving legacy format

No changes required.  Devices without a `pipeline:` field use
`pipeline_name="direct"` and `mode="pull"`.  All existing YAML files
continue to work unchanged.

---

## Push mode migration

For event-driven (push) devices, set `mode: push` in the pipeline template:

```yaml
pipelines:
  bluetti_push:
    mode: push
    transport: mqtt
    vendor: bluetti
    protocol: v2

devices:
  - id: outdoor_station
    pipeline: bluetti_push
    profile_id: EL30V2
    transport:
      opts:
        device_sn: "${SN_OUTDOOR}"
        cert_password: "${PW_OUTDOOR}"
```

The transport plugin must call `adapter.on_data(raw)` when the device
publishes data.  Obtain the adapter via `Executor.push_adapter(device_id)`
after `Executor.run()` has started.
