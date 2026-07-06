# Operator Package Runtime Control Bundle

Status: in-flight

**Date:** 2026-06-21

**Goal:** Extend the mock-safe Operator Package runtime bridge from one staged
operator step to a package-level rehearsal command. The Performance Console
should validate the current operator package sequence as one unit before any
future apply/send work exists, while preserving the mock-first safety contract.

**Architecture:** Keep the feature inside the existing Cockpit WebSocket
protocol, handler registry, and Performance Console route. The backend reads
the passive `live_kit_operator_package` payload, validates package id,
selected step keys, package export-key bindings, and `mock_safe: true`, then
returns an ack-only `operator_package_sequence_rehearsal` payload. The
sequence command reuses the same deterministic step evidence as
`rehearse_operator_package_step`. The existing step command also rejects stale
`package_export_key` values so UI/package drift is visible before active work
exists. No send-plan apply, kit commit, MIDI adapter, package writer, Tauri
invoke, hardware arm path, or snapshot mutation is called.

**Maintainability audit:** The bundle deliberately stays in the same WebSocket
and Performance Console seams introduced by the step bridge. It does not add a
new top-level module, sidecar service, package-file writer, or hardware state
machine. Reusable helper functions in `handlers.py` now own package step
lookup, binding lookup, export-key validation, and rehearsal payload assembly
so the step and sequence commands cannot drift. If a later PR promotes package
apply/dry-run/send, it should reuse the same validation helpers rather than
forking the package contract.

## Build Checklist

- [x] Add backend protocol tests for
  `COMMAND_REHEARSE_OPERATOR_PACKAGE_SEQUENCE`, command shape, and sequence
  ack payload shape.
- [x] Add backend handler tests for package-sequence happy path,
  all-steps fallback, `mock_safe` rejection, unknown package, unknown step,
  export-key mismatch, and no device/session side effects.
- [x] Add stale `package_export_key` rejection coverage for the existing
  `rehearse_operator_package_step` command.
- [x] Add WebSocket round-trip coverage for the new command and update
  aggregate command-count invariants.
- [x] Add TypeScript protocol coverage for the sequence command and ack.
- [x] Wire `PerformanceConsole` to render a mock-safe package-sequence
  rehearsal control and log ack/rejection evidence.
- [x] Pass the `client.send` callback from the performance-console route in
  `App`.
- [x] Update project status and README notes.

## Safety Boundary

- [x] No MIDI port is opened.
- [x] No MIDI is sent.
- [x] No package file is written.
- [x] No snapshot is mutated.
- [x] No send plan is applied.
- [x] No hardware arm behavior is changed.
- [x] The command requires `mock_safe: true` and returns categorical
  validation errors otherwise.
- [x] The sequence command only returns deterministic ack evidence; it emits no
  side-effect events.

## Verification

- [x] `python -m pytest tests/cockpit/test_ws_protocol.py tests/cockpit/test_ws_handlers.py tests/cockpit/test_integration_protocol_roundtrip.py -q -n 0`
- [x] `npm.cmd test -- --run tests/ws-client.test.ts tests/cockpit/PerformanceConsole.test.tsx`
- [x] `python -m pytest tests/architecture/ -q`
- [x] `python -m pytest`
- [x] `python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing`
- [x] `python -m ruff check .`
- [x] `python -m black --check --target-version=py311 .`
- [x] `python -m isort --profile black --check-only .`
- [x] `npm.cmd run build`
- [x] `npm.cmd test -- --run`
- [x] `npm.cmd run test:coverage`
- [x] `git diff --check`
