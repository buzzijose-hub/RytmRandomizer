# Operator Package Apply Preview Bundle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive, mock-safe Operator Package Apply Preview command and Cockpit surface that previews the whole package apply plan without touching hardware or files.

**Architecture:** Build on PR #193's Operator Package runtime-control merge and keep the new surface inside the existing Cockpit WebSocket protocol, handler registry, Performance Console route, and passive Live Kit Operator Package payload. The sidecar validates the current package id, step order, export-key bindings, readiness gates, and recovery requirements, then returns a deterministic ack-only apply-preview evidence payload. The implementation must not open MIDI ports, send MIDI, write package files, mutate snapshots, apply send plans, or arm hardware.

**Tech Stack:** Python 3.11 Cockpit WebSocket sidecar, typed Python/TypeScript protocol contracts, React Performance Console, Vitest, pytest, existing passive report data.

---

Status: in-flight

Local verification: complete; awaiting PR review and CI.

**Date:** 2026-06-22

**Base:** `modularize-v1.34`

**Branch/worktree:** `codex/operator-package-apply-preview` in `.worktrees/operator-package-apply-preview`

**PR shape:** one large bundled PR after implementation, not stacked. Intermediate workstreams may use disjoint worktrees/branches, but only the bundle opens for review.

## Why

PR #193 made the runtime-control bridge capable of rehearsing a whole Operator Package sequence. The next safe increment is not real apply/send. It is an apply preview: a deterministic proof packet that answers "what would the package apply plan require, in what order, and what active actions are still blocked?"

This gives the future active path a reviewed contract without crossing the hardware boundary early.

## Owned Scope For This Plan

Documentation packaging owns these files:

- `docs/superpowers/plans/2026-06-22-operator-package-apply-preview-bundle.md`
- `docs/superpowers/plans/2026-06-22-operator-package-apply-preview-bundle-pr-body.md`
- `docs/STATUS.md`
- `README.md`
- `docs/CLI_REFERENCE.md`

Implementation workers should keep their write scopes disjoint and should not split the work into stacked PRs.

## Expected Implementation Files

Likely source/test paths for the implementation bundle:

- Modify: `rytm_randomizer/cockpit/ws/protocol.py`
- Modify: `rytm_randomizer/cockpit/ws/handlers.py`
- Modify: `desktop/web/src/ws/protocol.ts`
- Modify: `desktop/web/src/App.tsx`
- Modify: `desktop/web/src/cockpit/PerformanceConsole.tsx`
- Test: `tests/cockpit/test_ws_protocol.py`
- Test: `tests/cockpit/test_ws_handlers.py`
- Test: `tests/cockpit/test_integration_protocol_roundtrip.py`
- Test: `desktop/web/tests/ws-client.test.ts`
- Test: `desktop/web/tests/cockpit/PerformanceConsole.test.tsx`
- Docs: `README.md`, `docs/STATUS.md`, `docs/CLI_REFERENCE.md`

Do not add a new top-level package or a new sidecar service. Do not edit parity fixtures.

## Wire Contract

Name the command and ack consistently with the existing runtime-control family:

- Command: `preview_operator_package_apply`
- Ack payload: `operator_package_apply_preview`
- Required command fields:
  - `operator_package_id: str`
  - `step_keys: list[str]`
  - `package_export_keys: dict[str, str]`
  - `snapshot_id: str`
  - `mock_safe: true`
- Required ack evidence:
  - `preview_id`
  - `operator_package_id`
  - `snapshot_id`
  - `preview_status`
  - `apply_policy`
  - `apply_steps` with deterministic order and per-step `package_export_key`
  - `readiness_checks`
  - `recovery_requirements`
  - `blocked_actions`
  - `safety_lines`
  - `dry_run_summary`
  - `opened_midi_port: false`
  - `sent_midi: false`
  - `writes_files: false`

If implementation finds an existing naming pattern that is stricter than this name, keep the existing pattern and update this plan plus the draft PR body in the same commit.

## Architecture Shape

The backend should reuse the validation helpers introduced for Operator Package step and sequence rehearsal:

- Package lookup uses the current passive `live_kit_operator_package` payload on the session.
- Step lookup validates all requested `step_keys`; an empty list may fall back to all package steps only if that matches PR #193 sequence behavior.
- Export-key validation compares every requested step against the current slot binding's `package_export_key`, rejects mismatches categorically, and echoes the validated key on each apply-preview step.
- Readiness checks are computed from existing package metadata and sidecar state only.
- Recovery requirements are copied from passive package evidence; no recovery command is executed.
- Blocked real-send actions are explicit strings or safety lines covering package apply, package write/export, snapshot mutation, send-plan apply, hardware arm, port open, and MIDI send.
- Dry-run summary is a count/ordering preview only; it does not build or dispatch a real send plan.

The frontend should render one package-level Apply Preview control near the existing Operator Package runtime controls. Clicking it sends the typed command only when a sidecar client is present and logs either the ack or categorical rejection in the local operator log.

## Maintainability Audit

- **Onboarding curve:** A new contributor should be able to follow the existing PR #193 step/sequence rehearsal tests and add the apply-preview command without discovering a new subsystem.
- **Naming hygiene:** Use `operator_package_apply_preview` consistently for the ack and avoid vague names like `apply_dry_run` that could imply a real apply path.
- **Coupling / boundaries:** Keep backend logic in the existing WebSocket handler module and frontend logic in the existing Performance Console surface. No new cross-process service.
- **Magic strings:** New command literals should live next to the existing Operator Package command constants in Python and TypeScript protocol files.
- **Configuration:** No new env vars. `mock_safe: true` is an explicit command contract, not configuration.
- **Test maintainability:** Extend the existing protocol, handler, round-trip, ws-client, and Performance Console tests rather than creating parallel fixtures.
- **Build friction:** Focused tests should run with `-n 0` for single cockpit test files, while full pytest should keep default xdist.
- **Error messages:** Rejections should be categorical and useful: missing package, unknown step, export-key mismatch, `mock_safe` required, apply preview unavailable.
- **Versioning / release:** No version bump and no dependency change.
- **Future-proofing:** The future active apply/send path can reuse the same validation and evidence fields, then add an explicit armed/action boundary in a separate PR.

## Build Checklist

- [x] Add Python protocol constants and typed command/ack fields for `preview_operator_package_apply` and `operator_package_apply_preview`.
- [x] Add TypeScript protocol types and client tests for the new command and ack payload.
- [x] Add handler tests for the happy path, all-step ordering, `mock_safe` rejection, unknown package, unknown step, export-key mismatch, missing sidecar/package state, and no side effects.
- [x] Add WebSocket round-trip coverage proving the ack carries deterministic apply-preview evidence.
- [x] Reuse package/step/export-key validation helpers from PR #193; refactor only if it reduces duplication between step, sequence, and apply-preview commands.
- [x] Render the Apply Preview control in `PerformanceConsole.tsx` and log ack/rejection evidence without changing local package staging semantics.
- [x] Add Performance Console tests for command payload, disabled/unavailable states, ack log text, rejection log text, and no accidental send/apply UI enablement.
- [x] Update `README.md`, `docs/CLI_REFERENCE.md`, and `docs/STATUS.md` alongside the implementation.
- [x] Keep the branch as one bundle against `modularize-v1.34`; do not open stacked PRs.

## Safety Boundary

- [x] No MIDI port is opened.
- [x] No MIDI is sent.
- [x] No package file is written.
- [x] No snapshot is mutated.
- [x] No send plan is applied.
- [x] No hardware arm behavior is changed.
- [x] No Tauri invoke path is added for active apply/send.
- [x] No parity fixture is regenerated.
- [x] The command requires `mock_safe: true`.
- [x] The ack includes explicit no-port/no-MIDI/no-file proof plus blocked-action or safety-line proof for snapshot mutation, send-plan apply, and hardware arm.

## Verification Checklist

Use these checkboxes as implementation closeout placeholders. Do not mark them complete without local output.

- [x] `python -m pytest tests/cockpit/test_ws_protocol.py tests/cockpit/test_ws_handlers.py tests/cockpit/test_integration_protocol_roundtrip.py -q -n 0` (`151 passed` with wizard protocol guard included)
- [x] `npm.cmd test -- --run tests/ws-client.test.ts tests/cockpit/PerformanceConsole.test.tsx` (`113 passed`)
- [x] `python -m pytest tests/architecture/ -q` (`622 passed`)
- [x] `python -m pytest` (`5765 passed, 3 skipped`)
- [x] `python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing` (`98.77%` total)
- [x] `python -m ruff check .`
- [x] `python -m black --check --target-version=py311 .`
- [x] `python -m isort --profile black --check-only .`
- [x] `npm.cmd run build`
- [x] `npm.cmd test -- --run` (`442 passed`; coverage run includes the later defensive tests)
- [x] `npm.cmd run test:coverage` (`447 passed`, `100%` frontend coverage)
- [x] `git diff --check`

## Plan-Requirements Conformance

Per `docs/PLAN_REQUIREMENTS.md`, this bundle is expected to satisfy all 18 gates before PR open:

- [x] Gate 1 -- 100% branch coverage on touched production files.
- [x] Gate 2 -- V1.34 parity byte-identical; no fixture regeneration.
- [x] Gate 3 -- lint/format/type clean.
- [x] Gate 4 -- no new dead code.
- [x] Gate 5 -- docs updated in the same PR.
- [x] Gate 6 -- no `Any` escape hatches; typed protocol fields only.
- [x] Gate 7 -- no new hot-path send/guardrail behavior; validation rejections stay observable through existing handler patterns.
- [x] Gate 8 -- tests extend existing cockpit/web fixtures and intent naming.
- [x] Gate 9 -- no new top-level modules.
- [x] Gate 10 -- no mode/intensity/page string dispatch.
- [x] Gate 11 -- shared fixtures reused.
- [x] Gate 12 -- new constants annotated with `Final` where applicable.
- [x] Gate 13 -- no new env vars.
- [x] Gate 14 -- maintainability audit captured above.
- [x] Gate 15 -- no new learned skill needed.
- [x] Gate 16 -- one bundled PR against `modularize-v1.34`; no stacked PR.
- [x] Gate 17 -- reuse existing Cockpit WS protocol, handler registry, passive package payload, and Performance Console seams.
- [x] Gate 18 -- architecture docs/diagrams unchanged because this does not add a new architecture boundary beyond the existing WS command family.

## Risks And Follow-Ups

- The ack name and command name must be kept identical across Python, TypeScript, tests, README, and CLI reference text.
- The apply preview must not be marketed as a dry-run send; it is evidence for a future active path, not the active path.
- A later active apply/send PR will need a new plan with explicit hardware arming, operator confirmation, manual validation, and a separate safety review.
