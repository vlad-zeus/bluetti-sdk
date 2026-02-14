# Platform-Stable Plan

Status: Draft  
Scope: Platform completion first, then schema/device coverage.

## Phase Split

### Phase 1: Platform Completion (current priority)
Goal: finalize SDK platform quality and stability without expanding block/device coverage.

Definition of Done:
1. Architecture locked: instance-scoped schema registry, typed transforms, retry policy, async facade.
2. Transport resilience complete: fail-fast disconnect, clean reconnect retry path, no resource leaks.
3. Quality gates stable: `ruff`, `mypy`, `pytest` green without flaky temp-dir failures.
4. CLI production-ready: secure password flow, argument validation, retry flags wired to policy.
5. Docs complete for platform behavior: contracts, error model, retry/backoff semantics.
6. CI guardrails enforced: required checks + coverage floor (>=85%).

Execution Checklist:
1. Verify platform invariants with focused regression suite.
2. Freeze API contracts for `client`, `client_async`, `transport`, `schemas`, `utils.resilience`.
3. Finalize platform docs (`README.md`, `docs/architecture/*`, `docs/adr/*` consistency).
4. Confirm release hygiene: changelog, packaging metadata, CLI examples, smoke checks.
5. Mark milestone as `platform-stable` (internal milestone, not full feature-complete release).

### Phase 2: Block/Device Coverage (after platform stable)
Goal: expand supported blocks and device profiles on top of stable platform.

Execution Checklist:
1. Build and maintain coverage matrix: `device -> group -> block -> schema status`.
2. Prioritize next supported models and block groups.
3. Implement declarative schemas for missing blocks.
4. Add/extend device profiles and mapping tests.
5. Add integration smoke tests per newly supported device/model.
6. Publish support matrix in docs and release notes.

## Immediate Next Actions (Phase 1)

1. Keep platform-only PR scope; no new block/device additions.
2. Run full quality gate and lock baseline metrics.
3. Update release checklist for platform milestone.
4. Open separate tracking issue/board for Phase 2 coverage work.
