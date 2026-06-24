## Summary

Adds the next mock-safe Operator Package layer: the Cockpit can build a deterministic passive receipt for the current reviewed operator-package apply preview. The receipt records ordered steps, export-key evidence, recovery requirements, blocked actions, safety lines, a short digest, and explicit proof that no MIDI port opened, no MIDI was sent, no files were written, no snapshot was mutated, no send plan was applied, and no events were emitted.

## What Changed

- Added the typed `build_operator_package_receipt` WebSocket command and `operator_package_receipt` ack payload.
- Reused the existing Operator Package validation seam: package id, selected steps, package export keys, snapshot id, and `mock_safe: true`.
- Added deterministic receipt evidence with `receipt_id`, `receipt_digest`, ordered receipt steps, readiness checks, recovery requirements, blocked actions, safety lines, and audit summary.
- Added desktop TypeScript protocol coverage, Cockpit WebSocket round-trip coverage, and a Performance Console receipt button/panel with accepted/rejected/offline logging.
- Updated README, CLI reference, project status, and plan docs.

## Why

The Operator Package line has safe staging, step rehearsal, sequence rehearsal, and apply-preview evidence. This PR adds the audit/handoff layer before any active apply/send behavior exists, so future Mutation Journal or package-review flows have a stable proof packet without crossing the hardware boundary.

## Safety

This is passive/mock-safe only. It does not open MIDI ports, send MIDI, arm hardware, write package files, mutate snapshots, apply send plans, or emit events.

## Test Plan

- [x] `python -m pytest tests/cockpit/test_ws_protocol.py tests/cockpit/test_ws_handlers.py -q -n 0`
- [x] `cd desktop/web && npm.cmd test -- --run tests/ws-client.test.ts tests/cockpit/PerformanceConsole.test.tsx`
- [x] `python -m pytest`
- [x] `python -m pytest tests/architecture/ -q`
- [x] `python -m ruff check .`
- [x] `python -m black --check --target-version=py311 .`
- [x] `python -m isort --profile black --check-only .`
- [x] `cd desktop/web && npm.cmd test -- --run`
- [x] `cd desktop/web && npm.cmd run typecheck`
- [x] `cd desktop/web && npm.cmd run lint`
- [x] `cd desktop/web && npm.cmd run build`

## Plan Requirements Conformance

- [x] Gate 1 - Coverage: focused tests added for Python protocol/handler and desktop WS/UI receipt paths; full coverage verification pending closeout.
- [x] Gate 2 - Architecture: stays inside Cockpit WebSocket protocol/handler, Performance Console, and passive docs; no new top-level package.
- [x] Gate 3 - Safety: explicit no-port/no-MIDI/no-file/no-snapshot/no-send-plan/no-event booleans in ack and tests.
- [x] Gate 4 - Tests: TDD tests cover success, all-step fallback, validation failures, export-key mismatch, no side effects, UI rendering, and transport failures.
- [x] Gate 5 - Observability: UI logs accepted/rejected/offline outcomes in the existing local operator log; no raw exception text added to backend wire responses.
- [x] Gate 6 - Data ownership: reuses passive Live Kit Operator Package payload and existing export-key bindings.
- [x] Gate 7 - UX: adds one receipt control and one audit panel next to the existing operator-package runtime controls.
- [x] Gate 8 - Docs: README, CLI reference, status, plan, and PR body updated.
- [x] Gate 9 - Backwards compatibility: existing command payloads remain unchanged; legacy console packet fallback still disables unavailable operator-package controls.
- [x] Gate 10 - Security/privacy: receipt digest is a deterministic audit fingerprint only; no secrets, credentials, or file contents are introduced.
- [x] Gate 11 - Fixtures: no parity fixture changes.
- [x] Gate 12 - Dependencies: no dependency or lockfile changes.
- [x] Gate 13 - Performance: receipt construction is small in-memory JSON/digest work over existing package steps.
- [x] Gate 14 - Error handling: reuses categorical validation acks for mock-safe, package id, step, and export-key mismatch failures.
- [x] Gate 15 - Maintainability: naming mirrors the existing operator-package command family and reuses validation helpers.
- [x] Gate 16 - PR shape: one clean-base bundled PR; not stacked on PR #196.
- [x] Gate 17 - Abstraction reuse: uses existing package lookup, step lookup, export-key validation, recovery requirements, and blocked/safety evidence.
- [x] Gate 18 - Release notes/status: status doc and README/CLI references describe the new passive receipt surface.

## Strict Rules Confirmation

- [x] No hardware behavior change.
- [x] No real MIDI port opening or MIDI send path added.
- [x] No top-level `rytm_randomizer/` module added.
- [x] No `mido` / `python-rtmidi` dependency changes.
- [x] No V1.34 parity fixture regeneration.
- [x] No stacked PR base.

Plan: `docs/superpowers/plans/2026-06-23-operator-package-receipt-bundle.md`
