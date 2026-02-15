# Native Async Transport Roadmap

Status: Planned (deferred)  
Priority: After current Phase 2 closure

## Decision

Current implementation (`AsyncV2Client` over sync transport) remains the active path
until ongoing schema/reverse-engineering work is completed.

Native async transport is a separate track and will start only after current
block coverage goals are closed.

## Why

Multiple reviews noted that current async model is a facade over sync MQTT.
It is production-usable, but not "native async" end-to-end.

## Scope (future)

1. Add `AsyncTransportProtocol` (native coroutine-based contract).
2. Implement `AsyncMQTTTransport` on an asyncio-native MQTT client.
3. Add `AsyncV2ClientNative` that uses async transport directly.
4. Keep existing sync stack fully supported (no breaking changes).

## Constraints

1. Preserve current public API behavior for existing users.
2. No forced migration from sync stack.
3. Reuse protocol/parser/model layers (no duplication of business logic).
4. Keep request/response safety (single in-flight if protocol requires it).

## Increment Plan

### Increment A: Contracts

1. Define `AsyncTransportProtocol`.
2. Add compatibility adapter tests (sync vs async behavior parity).

### Increment B: Transport

1. Implement async MQTT connect/disconnect/send_frame.
2. Add robust timeout/cancel/disconnect race handling tests.

### Increment C: Client

1. Add native async client path on top of async transport.
2. Verify parity with current `AsyncV2Client` outputs and errors.

## Entry Criteria

1. Current Phase 2 coverage work completed (including active Wave tasks).
2. Quality gates stable.
3. Provisional high-risk schema work not blocked by transport changes.

## Exit Criteria

1. Native async path passes `ruff`, `mypy`, `pytest`.
2. No regressions in existing sync path.
3. Migration guidance documented.
