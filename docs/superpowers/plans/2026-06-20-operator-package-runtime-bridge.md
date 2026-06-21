# Operator Package Runtime Bridge

Status: in-flight

**Date:** 2026-06-20

**Goal:** Promote the Live Kit Operator Package lane from browser-local staging only to a typed, mock-safe Cockpit runtime rehearsal command. The Performance Console should still stage operator package steps locally, but when connected to the Python sidecar it should also ask the WebSocket layer to rehearse the same operator package step and return deterministic safety evidence.

**Architecture:** Keep the command under the existing Cockpit WebSocket protocol and handler registry. The handler reads the already-passive Live Kit Operator Package packet, validates the package id, step key, slot key, and `mock_safe: true`, then returns an ack-only `operator_package_rehearsal` payload. It must not call send-plan apply, kit commit, MIDI adapters, package writers, Tauri invokes, hardware arm paths, or snapshot mutation. The React Performance Console receives an optional callback from `App`, preserving local-only behavior for injected/demo tests while using `client.send(...)` on the live route.

## Build Checklist

- [x] Add backend protocol tests for `COMMAND_REHEARSE_OPERATOR_PACKAGE_STEP`, command shape, and ack payload shape.
- [x] Add backend handler tests for happy-path rehearsal, `mock_safe` rejection, unknown package, unknown step, slot mismatch, and no device/session side effects.
- [x] Add WebSocket round-trip coverage for the new command and update aggregate command-count invariants.
- [x] Add TypeScript protocol coverage for the command and ack payload.
- [x] Wire `PerformanceConsole` to preserve local staging while optionally sending the sidecar rehearsal command.
- [x] Pass the `client.send` callback from the performance-console route in `App`.
- [x] Log sidecar acknowledgement or rejection in the local operator log without rolling back local staging.
- [x] Update project status and README notes.

## Safety Boundary

- [x] No MIDI port is opened.
- [x] No MIDI is sent.
- [x] No package file is written.
- [x] No snapshot is mutated.
- [x] No send plan is applied.
- [x] No hardware arm behavior is changed.
- [x] The command requires `mock_safe: true` and returns categorical validation errors otherwise.

## Verification

- [x] `python -m pytest tests/cockpit/test_ws_protocol.py tests/cockpit/test_ws_handlers.py tests/cockpit/test_integration_protocol_roundtrip.py tests/cockpit/test_ws_wizard_protocol.py -q -n 0`
- [x] `npm.cmd test -- --run tests/cockpit/PerformanceConsole.test.tsx tests/ws-client.test.ts`
- [x] `python -m pytest`
- [x] `python -m pytest tests/architecture/ -q`
- [x] `python -m ruff check .`
- [x] `python -m black --check --target-version=py311 .`
- [x] `python -m isort --profile black --check-only .`
- [x] `npm.cmd run build`
- [x] `npm.cmd test -- --run`
