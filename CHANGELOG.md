# Changelog

All notable changes to `power_sdk` are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.1.0] - 2026-02-20

### Added

- Runtime-first execution path via `power-cli runtime --config <file>`.
- Required `pipelines` + per-device `pipeline` validation in runtime config.
- Async runtime executor with per-device loop, backpressure queue, and metrics.
- Runtime sinks (`MemorySink`, `JsonlSink`, `CompositeSink`) and sink factory wiring.
- Stage resolver validation and extended dry-run output.
- CI runtime smoke checks and legacy API surface guard.

### Changed

- Public surface is runtime-first; plugin discovery is entry-point based.
- Dry-run metadata now reports parser/model from resolved manifest key.
- TLS key/cert temp file handling hardened.

### Removed (Breaking)

- Legacy public bootstrap exports from `power_sdk.__init__`.
- `V2Device` alias from `power_sdk.models`.
- Legacy CLI flags/commands (`--sn`, `--cert`, vendor-specific command paths).

## [2.0.0] - 2026-02-13

### Added

- Initial `power_sdk` platform split (core + plugin architecture).
- Protocol/parsing/runtime foundations and quality gates.
