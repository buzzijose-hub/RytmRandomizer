# Live Kit Capture Cockpit Bundle Implementation Plan

> Status: in-flight

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Surface RytmRandomizer's live SysEx kit-capture advantage in the passive Cockpit performance console.

**Architecture:** Reuse the existing `rytm_live_macro_hardware_rehearsal` launch command and the existing performance-console packet. Add one passive `live_kit_capture_panel` object to the Python report, mirror it in the TypeScript protocol/demo model, render it in `PerformanceConsole`, and update docs/status. No hardware path changes.

**Tech Stack:** Python dataclasses/TypedDict report model, pytest, TypeScript React, Vitest, static demo model, Markdown docs.

---

### Task 1: Python Packet Contract

**Files:**
- Modify: `tests/test_live_gui_performance_console_model.py`
- Modify: `rytm_randomizer/reports/live_gui_performance_console_model.py`

- [x] **Step 1: Write failing tests**

Add assertions that the model and JSON payload expose `live_kit_capture_panel`
with version `performance-console-live-kit-capture-panel-v1`, tagline
`Mutate the kit you are actually playing.`, six workflow steps, five
differentiators, recovery commands including `Z` then `send`, blocked actions,
safety lines, and text-report lines.

- [x] **Step 2: Verify RED**

Run:

```powershell
python -m pytest tests/test_live_gui_performance_console_model.py -n 0 -q
```

Expected: failure because `LiveGuiPerformanceConsoleModel` has no
`live_kit_capture_panel` attribute or payload key.

- [x] **Step 3: Implement the model**

Add constants, `_build_live_kit_capture_panel()`, dataclass/TypedDict fields,
console id input, blocked-action/safety aggregation, payload serialization, and
report formatting. Keep every active action blocked and keep safety lines
passive/read-only.

- [x] **Step 4: Verify GREEN**

Run the same pytest command. Expected: pass.

### Task 2: TypeScript Protocol and Demo Fixture

**Files:**
- Modify: `desktop/web/src/types/live_gui_protocol.ts`
- Modify: `desktop/web/src/cockpit/performanceConsoleDemoModel.ts`

- [x] **Step 1: Add protocol interfaces**

Mirror the Python field names and object order with TypeScript interfaces for
workflow steps, differentiators, and the panel object.

- [x] **Step 2: Add fixture data**

Insert the deterministic `live_kit_capture_panel` object into
`DEFAULT_PERFORMANCE_CONSOLE_MODEL` with the same text as the Python packet.

- [x] **Step 3: Typecheck**

Run:

```powershell
npm.cmd run typecheck
```

Expected: pass after the fixture satisfies the protocol.

### Task 3: React Surface

**Files:**
- Modify: `desktop/web/tests/cockpit/PerformanceConsole.test.tsx`
- Modify: `desktop/web/src/cockpit/PerformanceConsole.tsx`

- [x] **Step 1: Write failing UI assertions**

Assert that the Performance Console renders `Live Kit Capture`, the tagline,
`receive-kit-sysex`, `mutate-captured-kit`, `captured-anchor recovery`, and
disabled Receive Kit / Mutate Captured Kit / Send Captured Plan buttons.

- [x] **Step 2: Verify RED**

Run:

```powershell
npm.cmd run test:run -- PerformanceConsole.test.tsx
```

Expected: failure because the UI does not render the panel yet.

- [x] **Step 3: Render the panel**

Add a passive section with workflow and differentiator cards, blocked chips,
safety chips, and disabled controls. Do not attach handlers that dispatch
hardware or WebSocket commands.

- [x] **Step 4: Verify GREEN**

Run the same Vitest command. Expected: pass.

### Task 4: Docs, Status, and Bundle Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/CLI_REFERENCE.md`
- Modify: `docs/STATUS.md`

- [x] **Step 1: Update docs**

Mention that the performance-console report now includes a passive
`live_kit_capture_panel` explaining the live SysEx kit-capture workflow and
why it differs from fixed controller mapping.

- [x] **Step 2: Run focused checks**

Run:

```powershell
python -m pytest tests/test_live_gui_performance_console_model.py -n 0 -q
npm.cmd run test:run -- PerformanceConsole.test.tsx
npm.cmd run typecheck
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
```

- [x] **Step 3: Run full gates**

Run:

```powershell
python -m pytest tests/architecture/ -q
python -m pytest
npm.cmd run lint
npm.cmd run build
python scripts/code_review_gate.py --mode cli
```

Expected: all pass. The known Gate 17 short-name warning may remain warn-only.
