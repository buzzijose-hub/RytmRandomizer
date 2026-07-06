# Live Kit Operator Package Bundle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> Status: in-flight

**Goal:** Bind the passive captured-kit audition packet into an operator package lane that can be staged, reviewed, journal-previewed, and exported locally without hardware behavior.

**Architecture:** Keep the feature inside the existing passive performance-console report and Cockpit console surfaces. The backend will compose a deterministic `live_kit_operator_package` payload from the existing live kit capture workbench and live kit package audition payload. The frontend will render that payload as an operator-facing local package lane, let audition slots become browser-local rehearsal actions, and include the selected operator package context in local rehearsal package export/import. No MIDI ports are opened, no hardware sends are introduced, and installer/runtime behavior remains unchanged.

**Tech Stack:** Python 3.11 typed report payloads, React/TypeScript Cockpit console, Vitest/Testing Library, pytest.

**Maintainability audit:** The backend package stays as one passive report helper under `reports/performance_console/` and composes the existing capture workbench/package audition payloads instead of creating a second cockpit packet family. The frontend keeps enabled behavior browser-local, adds a legacy fallback for console packets produced before `live_kit_operator_package`, and treats imported operator-package slots as compatibility evidence so stale packages become review-required rather than silently compatible. Repeated payload coercion should move into `payload_helpers.py` if another operator package lane needs the same local helpers.

## Task 1: Backend RED Tests

- [x] Add failing tests in `tests/test_live_gui_performance_console_model.py` proving the console model exposes `live_kit_operator_package`.
- [x] Assert the payload is deterministic, JSON-safe, passive-ready, linked to `live_kit_package_audition`, and includes operator steps, slot bindings, recovery requirements, journal preview, local export preview, disabled controls, blocked actions, and safety lines.
- [x] Assert CLI/text output includes a `Live kit operator package:` section.
- [x] Assert type hints expose the new TypedDict payload on `LiveGuiPerformanceConsoleModel` and `LiveGuiPerformanceConsoleModelDict`.

## Task 2: Backend Implementation

- [x] Add `rytm_randomizer/reports/performance_console/live_kit_operator_package.py`.
- [x] Define explicit TypedDict contracts for the operator package manifest, steps, slot bindings, recovery requirements, journal commit preview, local export preview, and final payload.
- [x] Implement `build_live_kit_operator_package(live_kit_capture_workbench, live_kit_package_audition)`.
- [x] Implement `live_kit_operator_package_lines()` with malformed-input tolerance matching nearby passive report helpers.
- [x] Wire the payload into `rytm_randomizer/reports/live_gui_performance_console_model.py`, including model identity, JSON payload, blocked actions, safety lines, and formatted text output.

## Task 3: Frontend RED Tests

- [x] Add failing tests in `desktop/web/tests/cockpit/PerformanceConsole.test.tsx` proving the console renders a `Live Kit Operator Package` panel.
- [x] Assert the panel shows operator steps, slot bindings, recovery requirements, export preview, and journal preview.
- [x] Assert staging an audition slot is browser-local: it adds a local set-plan step/operator log entry and does not enable hardware send controls.
- [x] Assert exported local rehearsal packages include the selected audition source/operator package context.
- [x] Assert imported packages preserve the optional operator package context while retaining compatibility with older package exports.

## Task 4: Frontend Implementation

- [x] Extend `desktop/web/src/types/live_gui_protocol.ts` with the new `live_kit_operator_package` contract.
- [x] Extend `desktop/web/src/cockpit/performanceConsoleDemoModel.ts` with deterministic demo data matching the backend payload.
- [x] Extend `desktop/web/src/cockpit/PerformanceConsole.tsx` with optional package-export fields for audition source and operator package metadata.
- [x] Render a new operator package panel near the existing live kit package audition surface.
- [x] Add local-only stage buttons for operator package steps that update the local set-plan and operator log while preserving mock/passive send guards.
- [x] Keep package import tolerant of older local rehearsal package files that do not include operator package metadata.

## Task 5: Docs And PR Body

- [x] Update `README.md` and `docs/CLI_REFERENCE.md` with the passive operator package lane.
- [x] Update `docs/STATUS.md` with the new bundle entry.
- [x] Draft `docs/superpowers/plans/2026-06-19-live-kit-operator-package-bundle-pr-body.md` with the required 18-gate checklist and test plan.

## Task 6: Verification, Commit, Push, PR

- [x] Run backend focused tests: `python -m pytest tests/test_live_gui_performance_console_model.py -n 0`.
- [x] Run frontend focused tests for the Cockpit console.
- [x] Run architecture tests: `python -m pytest tests/architecture/ -q`.
- [x] Run full test/lint gate or the repo canonical equivalent.
- [x] Commit all intended files only.
- [x] Push `codex/live-kit-operator-package-bundle`.
- [x] Open one large PR against `modularize-v1.34` with Eddie requested for review.
