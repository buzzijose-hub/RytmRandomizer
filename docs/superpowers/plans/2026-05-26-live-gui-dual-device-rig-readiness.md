# Live GUI Dual Device Rig Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
> Status: in-flight (PR #135)

**Goal:** Make the cockpit's mock-safe live GUI path explicitly show the full 12-pad Analog Rytm surface plus a staged 4-track Analog Four device, and add one passive rig-readiness packet for future desktop wiring.

**Architecture:** Keep runtime GUI work inside `desktop/web/src/cockpit` and passive report work inside `rytm_randomizer/reports`. Reuse the existing 12-pad surface, device inventory, hardware rail, and snapshot compatibility models instead of creating a new device boundary.

**Tech Stack:** Python 3.11 report dataclasses and pytest; React 18, TypeScript, Vitest, and Testing Library for the desktop web surface.

---

### Task 1: Device Rail 12+4 Visual Contract

**Files:**
- Create: `desktop/web/tests/cockpit/DeviceRail.test.tsx`
- Modify: `desktop/web/src/cockpit/DeviceRail.tsx`
- Modify: `desktop/web/src/cockpit/styles.css`

- [x] **Step 1: Write the failing test**

Create `DeviceRail.test.tsx` asserting that the rail renders an Analog Rytm card with 12 pad chips from the current snapshot and an Analog Four card with four staged track chips.

- [x] **Step 2: Run the test to verify RED**

Run: `npm run test:run -- DeviceRail.test.tsx`

Expected: FAIL because the current rail only renders summary cards and no chip grids.

- [x] **Step 3: Implement the minimal DeviceRail rendering**

Map `snapshot.pads` into Rytm pad chips and render a constant four-track Analog Four staged plan. Keep controls declarative and do not add WebSocket commands.

- [x] **Step 4: Run focused frontend tests**

Run: `npm run test:run -- DeviceRail.test.tsx Cockpit.test.tsx SnapshotPanel.test.tsx LiveReadinessPanel.test.tsx`

Expected: PASS.

### Task 2: Passive Dual Device Rig Readiness Packet

**Files:**
- Create: `tests/test_live_gui_dual_device_rig_readiness_model.py`
- Create: `rytm_randomizer/reports/live_gui_dual_device_rig_readiness_model.py`
- Modify: `desktop/web/src/types/live_gui_protocol.ts`
- Modify: `tests/architecture/test_live_gui_protocol_ts_matches_python_typeddicts.py`

- [x] **Step 1: Write the failing Python report test**

Assert that the model composes existing Rytm 12-pad surface, device inventory, hardware rail, and snapshot compatibility metadata into one JSON-safe packet with two devices, 16 total tracks, no open ports, disabled hardware controls, and replay commands.

- [x] **Step 2: Run the test to verify RED**

Run: `python -m pytest tests/test_live_gui_dual_device_rig_readiness_model.py -n 0`

Expected: FAIL because the module does not exist.

- [x] **Step 3: Implement the passive model**

Create focused frozen dataclasses with sibling `TypedDict` contracts. Build from existing report functions only; do not import real MIDI modules.

- [x] **Step 4: Mirror TypeScript protocol fields**

Add the new `TypedDict` mirrors to `desktop/web/src/types/live_gui_protocol.ts` and include the Python module in the architecture mirror test.

- [x] **Step 5: Run focused Python tests**

Run: `python -m pytest tests/test_live_gui_dual_device_rig_readiness_model.py tests/architecture/test_live_gui_protocol_ts_matches_python_typeddicts.py -n 0`

Expected: PASS.

### Task 3: Documentation and Verification

**Files:**
- Modify: `docs/STATUS.md`
- Optionally modify: `README.md` or `docs/CLI_REFERENCE.md` only if a CLI command is added.

- [x] **Step 1: Update status docs**

Add a concise hand-authored entry describing the mock-safe 12+4 GUI/device readiness bundle.

- [x] **Step 2: Run verification**

Run focused frontend tests, focused Python tests, architecture tests, fast tests, frontend typecheck/build if dependencies are available, lint, and the repo review gate.

- [x] **Step 3: Exact-stage and publish**

Stage only files changed for this bundle, commit, push the `codex/live-gui-12-pad-a4-readiness` branch, and open one PR against `modularize-v1.34`.
