# Architecture Decision Records (ADR)

This directory contains Architecture Decision Records documenting significant architectural decisions in the Bluetti SDK project.

## Index

### Architecture Hardening Cycle

| ADR | Title | Status | Priority |
|-----|-------|--------|----------|
| [ADR-001](ADR-001-dual-async-sync-api.md) | Dual Async/Sync Client API | Proposed | **High** |
| [ADR-002](ADR-002-instance-scoped-schema-registry.md) | Instance-Scoped Schema Registry | Proposed | **High** |
| [ADR-003](ADR-003-tls-certificate-lifecycle.md) | TLS Certificate Lifecycle | Proposed | Low (Future) |
| [ADR-004](ADR-004-typed-transforms.md) | Typed Transform System | Proposed | **High** |

## Implementation Plan

### Phase 1: Core Architecture (Current)

**Increment A: AsyncV2Client Facade**
- **Goal**: Native async API without breaking sync
- **Approach**: Facade pattern with asyncio.to_thread()
- **Files**: `client_async.py`, tests
- **Estimate**: 1 PR, ~300 LOC
- **Dependencies**: None
- **ADR**: ADR-001

**Increment B: Instance-Scoped Registry**
- **Goal**: Remove global mutable state
- **Approach**: Move schema ownership to V2Client
- **Files**: `registry.py`, `client.py`, tests
- **Estimate**: 1 PR, ~200 LOC changed
- **Dependencies**: None
- **ADR**: ADR-002

**Increment C: Typed Transforms**
- **Goal**: Type-safe transform composition
- **Approach**: Transform classes + DSL compatibility
- **Files**: `transforms/` package, tests
- **Estimate**: 1 PR, ~500 LOC
- **Dependencies**: None
- **ADR**: ADR-004

### Phase 2: Security Hardening (Future)

**TLS/Certificate Management**
- **Goal**: Secure certificate lifecycle
- **Approach**: CertificateStore, TLSContext
- **Status**: Documented, not scheduled
- **ADR**: ADR-003

## Increment Order

```
┌─────────────────────────────────────────────────────────┐
│ Increment A: AsyncV2Client                              │
│ - Add async facade                                      │
│ - Zero breaking changes                                 │
│ - Users can start using async API                       │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Increment B: Instance Registry                          │
│ - Remove global mutable state                           │
│ - Better test isolation                                 │
│ - Thread-safe by design                                 │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Increment C: Typed Transforms                           │
│ - Type-safe transform API                               │
│ - Backward compatible with DSL                          │
│ - Better DX (autocomplete, validation)                  │
└─────────────────────────────────────────────────────────┘
```

### Why This Order?

1. **AsyncV2Client first**: Unlocks async usage immediately, independent of other changes
2. **Registry second**: Simplifies testing for typed transforms, no global state
3. **Typed Transforms third**: Benefits from clean registry, can use async client in examples

## Acceptance Criteria (All Increments)

- [ ] All tests pass (143+ tests)
- [ ] Coverage ≥ 90%
- [ ] Zero breaking changes to public API
- [ ] Migration guide for each increment
- [ ] Performance benchmarks (no regression)
- [ ] Documentation updated

## ADR Format

Each ADR follows this structure:

```markdown
# ADR-XXX: Title

**Status**: Proposed | Accepted | Implemented | Deprecated
**Date**: YYYY-MM-DD
**Author**: Team

## Context
Problem description, background

## Decision
What we decided to do

## Consequences
Positive, negative, mitigation

## Implementation Plan
Concrete steps, files, API changes

## References
Links, prior art

## Acceptance Criteria
[ ] Checkboxes for done
```

## Status Definitions

- **Proposed**: Under discussion
- **Accepted**: Approved, ready for implementation
- **Implemented**: Code merged, in production
- **Deprecated**: Superseded by newer ADR
- **Rejected**: Decided not to implement

## Contributing

When adding a new ADR:

1. Copy template from existing ADR
2. Number sequentially (ADR-005, ADR-006, etc.)
3. Update this index
4. Link to related ADRs
5. Get team review before marking "Accepted"
