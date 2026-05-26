# Multi-Device Dry-Run Cockpit V1 Implementation Plan

> Status: in-flight

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first mock-safe Cockpit slice that visibly supports a 12-pad Analog Rytm view, a staged Analog Four device lane, clearer dry-run safety state, and a working profile export feedback path.

**Architecture:** Keep this work in the existing `rytm_randomizer.cockpit` Python sidecar and `desktop/web/src/cockpit` React UI. The Python sidecar remains deterministic and passive by default, while the web UI renders richer device/session state from existing protocol objects plus local mock-facing presentation data. No real MIDI ports are opened and no hardware sends are introduced.

**Tech Stack:** Python 3.11+, pytest, React, TypeScript, Vitest, Testing Library, existing Cockpit WebSocket protocol.

---

### Task 1: Backend 12-Pad Mock Snapshot

**Files:**
- Modify: `rytm_randomizer/cockpit/__main__.py`
- Modify: `rytm_randomizer/cockpit/data/snapshot.py`
- Test: `tests/cockpit/test_ws_main.py`

- [x] **Step 1: Write the failing test**

Update the existing default snapshot test so it expects all 12 Analog Rytm pad slots:

```python
def test_default_initial_snapshot_has_twelve_rytm_pads_with_known_machines() -> None:
    session = build_session(send_hardware=False)

    assert session.snapshot.device == "analog_rytm_mk2"
    assert [pad.pad_id for pad in session.snapshot.pads] == list(range(1, 13))
    assert [pad.machine for pad in session.snapshot.pads] == [
        "BD Hard",
        "SD Classic",
        "CH Closed",
        "OH Open",
        "BT Rim",
        "LT Low",
        "MT Mid",
        "HT High",
        "CP Clap",
        "RS Riser",
        "SY Raw",
        "BD Acoustic",
    ]
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/cockpit/test_ws_main.py -n 0`
Expected: FAIL because the current initial Cockpit snapshot only includes pads 1-4.

- [x] **Step 3: Implement the 12-pad deterministic snapshot**

Change `_default_initial_snapshot()` to produce pads 1-12 with stable labels and machine names. Keep parameter values deterministic and small enough for existing mock/rendering logic.

- [x] **Step 4: Run backend focused test**

Run: `python -m pytest tests/cockpit/test_ws_main.py -n 0`
Expected: PASS.

### Task 2: Frontend 12-Pad Fixture And Snapshot Rendering

**Files:**
- Modify: `desktop/web/tests/cockpit/_fixtures.ts`
- Modify: `desktop/web/tests/cockpit/SnapshotPanel.test.tsx`
- Modify: `desktop/web/src/cockpit/SnapshotPanel.tsx`
- Modify: `desktop/web/src/cockpit/styles.css`

- [x] **Step 1: Write failing UI test**

Update the shared test fixture to include 12 pads and assert that the snapshot panel renders pad 12 with the expected machine label.

- [x] **Step 2: Run test to verify it fails if rendering/layout still assumes four pads**

Run: `npm run test -- --run src/cockpit/SnapshotPanel.test.tsx tests/cockpit/SnapshotPanel.test.tsx`
Expected: FAIL until the fixture/test path and 12-pad layout are updated correctly.

- [x] **Step 3: Implement responsive 12-pad grid copy and layout**

Render a 12-pad grid using existing `PadCard` components. Keep the compact card format, add snapshot copy that describes dry-run snapshot status, and use CSS grid tracks that handle desktop and narrower windows without text overlap.

- [x] **Step 4: Run snapshot panel tests**

Run: `npm run test -- --run tests/cockpit/SnapshotPanel.test.tsx`
Expected: PASS.

### Task 3: Device And Safety Rails

**Files:**
- Create: `desktop/web/src/cockpit/DeviceRail.tsx`
- Create: `desktop/web/src/cockpit/SafetyRail.tsx`
- Modify: `desktop/web/src/cockpit/Cockpit.tsx`
- Modify: `desktop/web/src/cockpit/HeaderBar.tsx`
- Modify: `desktop/web/src/cockpit/styles.css`
- Test: `desktop/web/tests/cockpit/Cockpit.test.tsx`

- [x] **Step 1: Write failing UI tests**

Assert that the Cockpit shows:

```typescript
expect(screen.getByText('Analog Rytm MKII')).toBeInTheDocument()
expect(screen.getByText('Analog Four MKII')).toBeInTheDocument()
expect(screen.getByText('Mock Safe')).toBeInTheDocument()
expect(screen.getByText('No MIDI Port Open')).toBeInTheDocument()
```

- [x] **Step 2: Run tests to verify they fail**

Run: `npm run test -- --run tests/cockpit/Cockpit.test.tsx`
Expected: FAIL because the current Cockpit does not expose those device/safety rails.

- [x] **Step 3: Implement presentational rails**

Add a left device/session rail and right safety rail. The Analog Four lane is shown as mock-ready/deferred, not as a real hardware connection. Safety status derives from existing `sessionStatus` and `sendPlan` values.

- [x] **Step 4: Run Cockpit tests**

Run: `npm run test -- --run tests/cockpit/Cockpit.test.tsx`
Expected: PASS.

### Task 4: Profile Export Feedback

**Files:**
- Modify: `desktop/web/src/cockpit/ProfileChips.tsx`
- Test: `desktop/web/tests/cockpit/ProfileChips.test.tsx`

- [x] **Step 1: Write failing export test**

Assert that clicking `EXPORT MODEL` sends `export_profile_model`, then displays a success message when the sidecar returns `ok: true` with `model_bytes_b64`.

- [x] **Step 2: Run test to verify it fails**

Run: `npm run test -- --run tests/cockpit/ProfileChips.test.tsx`
Expected: FAIL because the existing button ignores the command acknowledgement.

- [x] **Step 3: Implement visible export result**

Await the command acknowledgement, create a downloadable `.rymp` blob when possible, and always show a clear success or error message. Do not silently swallow errors.

- [x] **Step 4: Run export tests**

Run: `npm run test -- --run tests/cockpit/ProfileChips.test.tsx`
Expected: PASS.

### Task 5: Verification And PR Closeout

**Files:**
- Modify docs/status or README only if the implementation changes user-visible workflow enough to document.

- [x] **Step 1: Run focused Python tests**

Run: `python -m pytest tests/cockpit/test_ws_main.py -n 0`
Expected: PASS.

- [x] **Step 2: Run focused frontend tests**

Run: `npm run test -- --run tests/cockpit`
Expected: PASS.

- [x] **Step 3: Run architecture gate**

Run: `python -m pytest tests/architecture/ -q`
Expected: PASS.

- [x] **Step 4: Run fast suite**

Run: `python -m pytest -m fast`
Expected: PASS or document any unrelated pre-existing failures with evidence.

- [x] **Step 5: Exact stage only intended files**

Run: `git diff --name-only --cached` after staging and confirm no `tests/fixtures/v134_parity/` files are staged.

- [x] **Step 6: Commit, push, and open PR**

Use a single feature commit and open a PR against `modularize-v1.34` with the repository checklist.
