# MQTT Setup

Runtime mode is the only supported path.

## 1. Configure `runtime.yaml`

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
      broker: "${MQTT_BROKER:-iot.bluettipower.com}"
      port: 18760

devices:
  - id: living_room_battery
    pipeline: bluetti_pull
    profile_id: EL100V2
    transport:
      opts:
        device_sn: "${LIVING_ROOM_SN}"
        cert_password: "${LIVING_ROOM_CERT_PASSWORD}"
```

## 2. Validate without I/O

```bash
power-cli runtime --config runtime.yaml --dry-run
```

## 3. Run one cycle

```bash
power-cli runtime --config runtime.yaml --once --connect
```

For migration details see `docs/runtime/MIGRATION-GUIDE.md`.
