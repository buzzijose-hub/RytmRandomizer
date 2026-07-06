# Operator Package Mock Apply Bundle Implementation Plan

> Status: in-flight

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a mock-safe operator package apply acknowledgement so Cockpit can rehearse accepting an operator package without opening MIDI, sending MIDI, writing files, or mutating snapshots.

**Architecture:** Extend the existing operator-package WebSocket bridge introduced by the apply-preview bundle. The backend reuses the current operator-package header validation, step selection, export-key checks, readiness/recovery helpers, and side-effect assertions; the frontend adds one adjacent Cockpit action and a result panel that remains review-only.

**Tech Stack:** Python 3.11 WebSocket handler TypedDict contracts, pytest, React/TypeScript/Vitest, existing `desktop/web` cockpit components.

---

## Scope

This bundle advances the `preview_operator_package_apply` surface into a second, explicit mock action:

- New command: `mock_apply_operator_package`.
- New ack payload: `operator_package_mock_apply`.
- Same package id, selected step keys, export-key bindings, snapshot id, and `mock_safe: true` validation as the preview command.
- Deterministic evidence rows for every selected operator package step.
- Proof fields showing no MIDI port was opened, no MIDI was sent, no files were written, no snapshot was mutated, no send plan was applied, and no events were emitted.
- Cockpit button and review panel next to the existing sequence rehearsal and apply preview controls.

Out of scope:

- Hardware arm or SEND behavior.
- File writes or persistent journal writes.
- Snapshot mutation.
- V1.34 parity fixture changes.
- New top-level modules or new device-family packages.

## File Map

- Modify: `rytm_randomizer/cockpit/ws/protocol.py`
  - Add command constant, command type, `CommandAck` payload field, `COMMAND_TYPES` membership, and export.
- Modify: `rytm_randomizer/cockpit/ws/handlers.py`
  - Add reusable mock-apply step/result helpers and handler.
  - Register handler in `_CORE_HANDLERS`.
- Modify: `tests/cockpit/test_ws_protocol.py`
  - Pin command constant, command count, TypedDict shape, and ack payload.
- Modify: `tests/cockpit/test_ws_handlers.py`
  - Add mock-apply success, all-steps default, validation, export-key mismatch, and no-side-effect tests.
- Modify: `tests/cockpit/test_integration_protocol_roundtrip.py`
  - Add end-to-end WebSocket roundtrip and update cockpit-native command count.
- Modify: `tests/cockpit/test_ws_wizard_protocol.py`
  - Update folded command count.
- Modify: `desktop/web/src/ws/protocol.ts`
  - Add command and ack payload interfaces.
- Modify: `desktop/web/src/App.tsx`
  - Pass the WebSocket callback into `PerformanceConsole`.
- Modify: `desktop/web/src/cockpit/PerformanceConsole.tsx`
  - Add prop, state, command sender, button, logging, and result panel.
- Modify: `desktop/web/tests/ws-client.test.ts`
  - Round-trip the typed command/ack.
- Modify: `desktop/web/tests/cockpit/PerformanceConsole.test.tsx`
  - Verify disabled state, command body, rendered result, ack-without-payload log, rejection, and transport failure.
- Modify: `README.md`, `docs/CLI_REFERENCE.md`, `docs/STATUS.md`
  - Document the mock-safe Cockpit operator package apply acknowledgement.
- Add: `docs/superpowers/plans/2026-06-22-operator-package-mock-apply-bundle-pr-body.md`
  - PR body with verification checklist.

## Workstream Graph

| Workstream | Owns | Depends on | Parallel with |
|---|---|---|---|
| WS1 Backend protocol tests | Python command/ack contracts | Plan | WS3 |
| WS2 Backend handler implementation | Python handler and helpers | WS1 red tests | WS4 docs after green |
| WS3 Frontend protocol/UI tests | TypeScript command/ack and console behavior | Plan | WS1 |
| WS4 Frontend implementation | WebSocket client wiring and UI panel | WS3 red tests | WS2 after red |
| WS5 Docs/verification/PR | README, CLI reference, status, PR body, full verification | WS2 + WS4 green | None |

All work lands on one branch, `codex/operator-package-mock-apply`, based on `origin/modularize-v1.34`.

## Tasks

### Task 1: Backend Protocol Red Tests

**Files:**
- Modify: `tests/cockpit/test_ws_protocol.py`
- Modify: `tests/cockpit/test_integration_protocol_roundtrip.py`
- Modify: `tests/cockpit/test_ws_wizard_protocol.py`

- [ ] Add `COMMAND_MOCK_APPLY_OPERATOR_PACKAGE` to the command constant tests.
- [ ] Expect `mock_apply_operator_package` in the wire-string test.
- [ ] Add `MockApplyOperatorPackageCommand` shape test with `operator_package_id`, `step_keys`, `package_export_keys`, `snapshot_id`, and `mock_safe`.
- [ ] Add `CommandAck` shape test for `operator_package_mock_apply`.
- [ ] Update command counts from 14 cockpit / 22 total to 15 cockpit / 23 total.
- [ ] Add integration roundtrip test that sends the new command and asserts `mock_apply_status`, `step_count`, and no-side-effect booleans.
- [ ] Run:

```powershell
python -m pytest tests/cockpit/test_ws_protocol.py tests/cockpit/test_integration_protocol_roundtrip.py tests/cockpit/test_ws_wizard_protocol.py -q -n 0
```

Expected red failure: missing protocol constant/type and stale command counts.

### Task 2: Backend Handler Red Tests

**Files:**
- Modify: `tests/cockpit/test_ws_handlers.py`

- [ ] Add success test for two selected operator-package steps.
- [ ] Assert deterministic `mock_apply_id`.
- [ ] Assert `mock_apply_status == "mock_applied"`.
- [ ] Assert `apply_policy == "mock_apply_only"`.
- [ ] Assert all side-effect booleans are false, including `applied_send_plan`.
- [ ] Assert session snapshot, current candidate, current send plan, `unsaved_sends`, and recorder events are unchanged.
- [ ] Add empty `step_keys` test that selects all operator-package steps.
- [ ] Add validation tests for `mock_safe: false`, unknown package, unknown step, and export-key mismatch.
- [ ] Add monkeypatch test proving `apply`, `apply_send_plan`, and `commit_kit` are not called.
- [ ] Run:

```powershell
python -m pytest tests/cockpit/test_ws_handlers.py -q -n 0
```

Expected red failure: unknown command type.

### Task 3: Backend Implementation

**Files:**
- Modify: `rytm_randomizer/cockpit/ws/protocol.py`
- Modify: `rytm_randomizer/cockpit/ws/handlers.py`

- [ ] Add `COMMAND_MOCK_APPLY_OPERATOR_PACKAGE: Final[Literal["mock_apply_operator_package"]]`.
- [ ] Add command to `COMMAND_TYPES`, `__all__`, and the command-count docstring.
- [ ] Add `operator_package_mock_apply: dict | None` to `CommandAck`.
- [ ] Add `MockApplyOperatorPackageCommand`.
- [ ] Add `_operator_package_mock_apply_step(...)` that mirrors preview step data but uses `mock_apply_status: "accepted_for_mock_apply"` and `blocked_action: "real_apply_blocked"`.
- [ ] Add `_operator_package_mock_apply_summary(step_count=...)` with `apply_policy: "mock_apply_only"` and false side-effect booleans.
- [ ] Add `_handle_mock_apply_operator_package(...)` that reuses current validation/selection/export-key helpers.
- [ ] Register the handler in `_CORE_HANDLERS`.
- [ ] Run backend targeted tests from Tasks 1 and 2 until green.

### Task 4: Frontend Red Tests

**Files:**
- Modify: `desktop/web/tests/ws-client.test.ts`
- Modify: `desktop/web/tests/cockpit/PerformanceConsole.test.tsx`

- [ ] Add WebSocket client roundtrip for `MockApplyOperatorPackageCommand` and `operator_package_mock_apply`.
- [ ] Add disabled-state test for missing `onMockApplyOperatorPackage` and missing package steps.
- [ ] Add success test that clicks `Mock apply operator package`, asserts the exact command body, and renders the result panel.
- [ ] Add ack-without-payload test that logs a mock-safe accepted message without rendering stale data.
- [ ] Add rejection fallback tests for `message`, `error`, `code`, and empty ack.
- [ ] Add transport failure tests for `Error` and non-Error rejection.
- [ ] Run:

```powershell
npm.cmd test -- --run tests/ws-client.test.ts tests/cockpit/PerformanceConsole.test.tsx
```

Expected red failure: missing TypeScript types, prop, button, and render panel.

### Task 5: Frontend Implementation

**Files:**
- Modify: `desktop/web/src/ws/protocol.ts`
- Modify: `desktop/web/src/App.tsx`
- Modify: `desktop/web/src/cockpit/PerformanceConsole.tsx`

- [ ] Add `OperatorPackageMockApplyStep`, readiness/recovery aliases or interfaces, summary interface, and `OperatorPackageMockApply`.
- [ ] Add `MockApplyOperatorPackageCommand` to the command union.
- [ ] Add `operator_package_mock_apply?: OperatorPackageMockApply` to `CommandAck`.
- [ ] Add `onMockApplyOperatorPackage` prop to `PerformanceConsoleProps`.
- [ ] Add `operatorPackageMockApply` state.
- [ ] Add `mockApplyOperatorPackage()` command sender with `mock_safe: true`.
- [ ] Add a button next to the preview button.
- [ ] Render `data-testid="performance-console-operator-package-mock-apply"` with status, policy, step count, no-side-effect proof, readiness checks, mock apply steps, recovery requirements, blocked actions, and safety lines.
- [ ] Pass the callback from `App.tsx`.
- [ ] Run frontend targeted tests until green.

### Task 6: Docs and Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/CLI_REFERENCE.md`
- Modify: `docs/STATUS.md`
- Modify: `docs/superpowers/plans/2026-06-22-operator-package-mock-apply-bundle-pr-body.md`

- [ ] Document that Cockpit can now preview and mock-apply operator packages through the WebSocket bridge while still blocking real SEND/hardware/file writes.
- [ ] Add a status entry under the current status section.
- [ ] Fill the PR body test plan with actual verification output.
- [ ] Run:

```powershell
python -m pytest tests/cockpit/test_ws_protocol.py tests/cockpit/test_ws_handlers.py tests/cockpit/test_integration_protocol_roundtrip.py tests/cockpit/test_ws_wizard_protocol.py -q -n 0
npm.cmd test -- --run tests/ws-client.test.ts tests/cockpit/PerformanceConsole.test.tsx
python -m pytest tests/architecture/ -q
python -m pytest
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
```

Expected green result: all commands exit 0 with no fixture regeneration and no hardware access.

### Task 7: Commit, Push, and Open One PR

**Files:**
- Stage only intended files from this plan.

- [ ] Inspect:

```powershell
git status --short
git diff --check
git diff --stat
```

- [ ] Commit:

```powershell
git add docs/superpowers/plans/2026-06-22-operator-package-mock-apply-bundle.md docs/superpowers/plans/2026-06-22-operator-package-mock-apply-bundle-pr-body.md rytm_randomizer/cockpit/ws/protocol.py rytm_randomizer/cockpit/ws/handlers.py tests/cockpit/test_ws_protocol.py tests/cockpit/test_ws_handlers.py tests/cockpit/test_integration_protocol_roundtrip.py tests/cockpit/test_ws_wizard_protocol.py desktop/web/src/ws/protocol.ts desktop/web/src/App.tsx desktop/web/src/cockpit/PerformanceConsole.tsx desktop/web/tests/ws-client.test.ts desktop/web/tests/cockpit/PerformanceConsole.test.tsx README.md docs/CLI_REFERENCE.md docs/STATUS.md
git commit -m "feat: add operator package mock apply"
```

- [ ] Push:

```powershell
git push -u origin codex/operator-package-mock-apply
```

- [ ] Open one PR against `modularize-v1.34` using:

```powershell
python scripts/create_pr.py --title "feat: add operator package mock apply" --body-file docs/superpowers/plans/2026-06-22-operator-package-mock-apply-bundle-pr-body.md
```

## Self-Review

- Spec coverage: the plan covers backend protocol, backend handler, frontend protocol, frontend UI, docs, verification, and PR creation.
- Placeholder scan: no TBD/TODO placeholders remain.
- Type consistency: command name is `mock_apply_operator_package`; ack payload is `operator_package_mock_apply`; backend and frontend use matching names.
- Safety: all new behavior is mock-safe and passive unless a future separately approved hardware path is added.
