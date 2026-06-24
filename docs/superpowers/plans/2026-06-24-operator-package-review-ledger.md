# Operator Package Review Ledger Implementation Plan

> Status: in-flight

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one mock-safe operator package review ledger that connects package intent, selected steps, apply preview, mock apply, receipt evidence, and blocked hardware actions in the passive Cockpit console.

**Architecture:** The ledger is a new passive report module under `rytm_randomizer/reports/performance_console/`, then is composed into `live_gui_performance_console_model` and mirrored in `desktop/web/src/types/live_gui_protocol.ts`. The React Performance Console renders the ledger from the existing console packet; it does not add WebSocket commands, MIDI send authority, file writes, hardware arm state, or snapshot mutation.

**Tech Stack:** Python 3.11 TypedDict/dataclass report contracts, existing passive CLI/report composition, React + TypeScript/Vitest frontend tests, pytest fast tests, existing architecture gates.

---

## File Structure

- Create `rytm_randomizer/reports/performance_console/live_kit_operator_review_ledger.py`
  - Owns the passive ledger TypedDicts, builder, and text report lines.
  - Consumes the existing `LiveKitOperatorPackagePayload`; does not import WebSocket handlers or runtime session state.
- Modify `rytm_randomizer/reports/live_gui_performance_console_model.py`
  - Adds `operator_package_review_ledger` to the dataclass, TypedDict, payload, console id digest, blocked actions, safety lines, and report text.
- Modify `desktop/web/src/types/live_gui_protocol.ts`
  - Adds interfaces for the nested ledger contract and the new console model field.
- Modify `desktop/web/src/cockpit/performanceConsoleDemoModel.ts`
  - Adds deterministic demo ledger data matching the Python shape.
- Modify `desktop/web/src/cockpit/PerformanceConsole.tsx`
  - Renders the ledger as a review surface near the existing operator package preview/mock-apply/receipt panels.
- Modify tests:
  - `tests/test_live_gui_operator_package_review_ledger.py`
  - `tests/test_live_gui_performance_console_model.py`
  - `tests/architecture/test_live_gui_protocol_ts_matches_python_typeddicts.py`
  - `desktop/web/tests/cockpit/PerformanceConsole.test.tsx`
- Modify docs:
  - `docs/STATUS.md`
  - `README.md`
  - `docs/CLI_REFERENCE.md` only if the visible report text changes enough to need the command description updated.

## Task 1: Passive Ledger Model

**Files:**
- Create: `tests/test_live_gui_operator_package_review_ledger.py`
- Create: `rytm_randomizer/reports/performance_console/live_kit_operator_review_ledger.py`

- [x] **Step 1: Write the failing test**

Add tests that assert a deterministic review ledger has three stages (`apply-preview`, `mock-apply`, `receipt-audit`), one row per operator package step, all hardware side effects false, package blocked actions preserved, and deterministic operator-readable lines.

- [x] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_live_gui_operator_package_review_ledger.py -n 0`

Expected: FAIL with `ModuleNotFoundError: No module named 'rytm_randomizer.reports.performance_console.live_kit_operator_review_ledger'`.

- [x] **Step 3: Implement the minimal ledger module**

Create TypedDicts for `LiveKitOperatorReviewLedgerStage`, `LiveKitOperatorReviewLedgerStep`, `LiveKitOperatorReviewLedgerReadinessSummary`, and `LiveKitOperatorReviewLedgerPayload`. Implement `build_live_kit_operator_review_ledger(operator_package)` and `live_kit_operator_review_ledger_lines(ledger)`.

- [x] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_live_gui_operator_package_review_ledger.py -n 0`

Expected: PASS.

## Task 2: Console Packet Composition

**Files:**
- Modify: `tests/test_live_gui_performance_console_model.py`
- Modify: `rytm_randomizer/reports/live_gui_performance_console_model.py`

- [x] **Step 1: Write the failing test**

Add assertions that `LiveGuiPerformanceConsoleModel.operator_package_review_ledger` exists, has version `performance-console-operator-package-review-ledger-v1`, status `passive-ready`, three stages, five step rows, the operator package blocked actions, and appears in report lines.

- [x] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_live_gui_performance_console_model.py -k "performance_console_model" -n 0`

Expected: FAIL with `AttributeError: 'LiveGuiPerformanceConsoleModel' object has no attribute 'operator_package_review_ledger'`.

- [x] **Step 3: Compose the ledger into the model**

Import the new builder and lines helper, add the dataclass/TypedDict field, build it after `live_kit_operator_package`, include it in `blocked_actions`, `safety_lines`, `_console_id`, payload JSON, and `_format_console_body`.

- [x] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_live_gui_operator_package_review_ledger.py tests/test_live_gui_performance_console_model.py -n 0`

Expected: PASS.

## Task 3: TypeScript Contract And UI Rendering

**Files:**
- Modify: `tests/architecture/test_live_gui_protocol_ts_matches_python_typeddicts.py`
- Modify: `desktop/web/src/types/live_gui_protocol.ts`
- Modify: `desktop/web/src/cockpit/performanceConsoleDemoModel.ts`
- Modify: `desktop/web/src/cockpit/PerformanceConsole.tsx`
- Modify: `desktop/web/tests/cockpit/PerformanceConsole.test.tsx`

- [x] **Step 1: Write the failing tests**

Extend the architecture mirror map with the four new Python TypedDict names. Add frontend assertions for `performance-console-operator-package-review-ledger`, the three review stages, one package export key, one safety line, and a disabled "Apply Operator Package Ledger" button.

- [x] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/architecture/test_live_gui_protocol_ts_matches_python_typeddicts.py -n 0`

Expected: FAIL because the TS interfaces do not exist.

Run: `cd desktop/web; npm test -- --run tests/cockpit/PerformanceConsole.test.tsx`

Expected: FAIL because `performance-console-operator-package-review-ledger` is not rendered.

- [x] **Step 3: Add TS interfaces, demo data, and rendering**

Add interfaces mirroring the Python TypedDict field order. Add `operator_package_review_ledger` to `LiveGuiPerformanceConsoleModelDict`. Add demo ledger data to `performanceConsoleDemoModel.ts`. Render a disabled, passive-only ledger section in `PerformanceConsole.tsx`.

- [x] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/architecture/test_live_gui_protocol_ts_matches_python_typeddicts.py -n 0`

Run: `cd desktop/web; npm test -- --run tests/cockpit/PerformanceConsole.test.tsx`

Expected: both PASS.

## Task 4: Docs And Final Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/STATUS.md`
- Modify: `docs/CLI_REFERENCE.md` if wording needs refresh.

- [x] **Step 1: Update docs**

Add a top `docs/STATUS.md` entry dated 2026-06-24 describing the operator package review ledger bundle. Refresh the README/CLI wording for `live-gui-performance-console-report` if the user-facing list of console sections omits the ledger.

- [ ] **Step 2: Run focused verification**

Run:

```powershell
python -m pytest tests/test_live_gui_operator_package_review_ledger.py tests/test_live_gui_performance_console_model.py tests/architecture/test_live_gui_protocol_ts_matches_python_typeddicts.py -n 0
cd desktop/web
npm test -- --run tests/cockpit/PerformanceConsole.test.tsx
```

Expected: all focused tests PASS.

- [ ] **Step 3: Run broader safety verification**

Run:

```powershell
python -m pytest -m fast
python -m pytest tests/architecture/ -q
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
cd desktop/web
npm test -- --run
npm run build
```

Expected: all commands exit 0.

- [ ] **Step 4: Commit and open one PR**

Stage only intended files, commit with `git commit -m "feat: add operator package review ledger"`, push `codex/operator-package-review-ledger`, and open one PR against `modularize-v1.34` with the 18-gate checklist.

## Safety Boundaries

- The ledger is passive metadata only.
- No tests or reports open MIDI ports.
- No WebSocket command sends MIDI.
- No new hardware arm path is introduced.
- No snapshot, send plan, or local storage is mutated by the Python report.
- The UI control for applying the ledger remains disabled.

## Self-Review

- Spec coverage: covers backend passive model, console composition, TS contract, UI rendering, docs, and verification.
- Placeholder scan: no TODO/TBD placeholders.
- Type consistency: Python and TypeScript names use `LiveKitOperatorReviewLedger*`; console field is `operator_package_review_ledger`.
- Scope check: one logical bundle continuing the operator package workflow after mock apply and receipt; no stacked PRs.
