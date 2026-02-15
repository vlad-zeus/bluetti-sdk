# Protocol Drift Safeguards Plan

Status: Draft  
Scope: post `platform-stable` hardening against upstream protocol drifts.

## Goal

Reduce breakage risk from small upstream changes (auth/shape/rate behaviors)
without overengineering.

## Scope

1. Fail-soft parsing
2. Diagnostic dump mode

## 1. Fail-soft Parsing

Requirements:

1. If block payload is longer than expected, parse known fields and ignore unknown tail.
2. Unknown block IDs must not crash group reads; log and skip.
3. Parsing errors for one block must not crash whole polling cycle in partial mode.
4. Add explicit warning logs with block ID and reason.

Definition of Done:

1. Unit tests for extended payload and unknown block handling.
2. No regression in strict mode behavior where strict failure is expected.

## 2. Diagnostic Dump Mode

Requirements:

1. Add optional debug flag to capture raw request/response frames.
2. Dumps must redact secrets (passwords/certs/tokens).
3. Support both CLI and library-level logger toggle.
4. Keep disabled by default.

Definition of Done:

1. CLI flag documented and tested.
2. Redaction tested (no secret bytes/strings in output).
3. Minimal overhead when mode is off.
