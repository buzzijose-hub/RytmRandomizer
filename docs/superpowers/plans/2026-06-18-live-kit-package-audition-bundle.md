# Live Kit Package Audition Implementation Plan

> Status: in-flight

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive Live Kit Package Audition section to the Performance Console so captured-kit variation slots, queue, checks, journal preview, and disabled controls are GUI-ready.

**Architecture:** Implement a focused Python helper under `rytm_randomizer/reports/performance_console/`, compose it into `live_gui_performance_console_model`, mirror the contract in TypeScript, render it in `PerformanceConsole`, and document it in README/CLI/status. The bundle remains passive and report-only.

**Tech Stack:** Python 3.11, pytest, TypeScript, React, Vitest, existing passive report/Performance Console architecture.

---

### Task 1: Python Contract

**Files:**
- Create: `rytm_randomizer/reports/performance_console/live_kit_package_audition.py`
- Modify: `rytm_randomizer/reports/live_gui_performance_console_model.py`
- Test: `tests/test_live_gui_performance_console_model.py`

- [x] Write failing tests that assert `live_gui_performance_console_model_payload()` includes `live_kit_package_audition` with five audition slots, a review-only queue, package checks, a journal preview, disabled controls, blocked actions, safety lines, and replay commands.
- [x] Run `python -m pytest tests/test_live_gui_performance_console_model.py -n 0 -q` and verify the new assertions fail because the field is missing.
- [x] Implement `build_live_kit_package_audition(workbench)` and `live_kit_package_audition_lines(audition)` in the new helper module.
- [x] Compose the helper into `LiveGuiPerformanceConsoleModel`, `LiveGuiPerformanceConsoleModelDict`, JSON payloads, blocked/safety aggregation, and formatted text output.
- [x] Run the focused pytest command again and verify the Python tests pass.

### Task 2: Frontend Contract and Rendering

**Files:**
- Modify: `desktop/web/src/types/live_gui_protocol.ts`
- Modify: `desktop/web/src/cockpit/performanceConsoleDemoModel.ts`
- Modify: `desktop/web/src/cockpit/PerformanceConsole.tsx`
- Test: `desktop/web/tests/cockpit/PerformanceConsole.test.tsx`

- [x] Write failing Vitest expectations for a `performance-console-live-kit-package-audition` section that renders audition slots, queue rows, package checks, journal preview, blocked actions, safety lines, and disabled controls.
- [x] Run `npm.cmd run test:run -- PerformanceConsole.test.tsx` from `desktop/web` and verify the new expectations fail because the section is missing.
- [x] Add TypeScript interfaces for the audition payload.
- [x] Add demo data that mirrors the Python payload.
- [x] Render the section in `PerformanceConsole.tsx` with all active-looking controls disabled.
- [x] Confirm no alternate fixture branch is needed for this straight-through render surface.
- [x] Run the focused Vitest command again and verify it passes.

### Task 3: Docs and Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/CLI_REFERENCE.md`
- Modify: `docs/STATUS.md`

- [x] Update docs to describe the passive Live Kit Package Audition surface and its safety boundaries.
- [x] Run focused Python coverage on the touched report modules.
- [x] Run `python -m pytest -q`.
- [x] Run `python -m pytest tests/architecture/ -q`.
- [x] Run `python -m ruff check .`, `python -m black --check --target-version=py311 .`, and `python -m isort --profile black --check-only .`.
- [x] Run `npm.cmd run lint`, `npm.cmd run typecheck`, `npm.cmd run test:coverage`, and `npm.cmd run build` in `desktop/web`.
- [x] Run `python scripts/code_review_gate.py --mode cli`.
- [ ] Commit, push, and open one PR against `modularize-v1.34`.

## Self-Review

- Spec coverage: The tasks cover the passive Python payload, text/JSON report,
  frontend contract, rendering, docs, and safety boundaries.
- Placeholder scan: No TODO/TBD placeholders are present.
- Type consistency: The payload name is `live_kit_package_audition` across
  Python JSON, TypeScript, demo data, and React rendering.
