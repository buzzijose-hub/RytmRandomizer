# Snapshot Essence Hardware Send Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the guarded real-MIDI hardware sender for the Rytm 12-pad snapshot essence send plan.

**Architecture:** Keep the passive CLI read-only. Create a focused active sender module that consumes `SnapshotEssenceSendPlan`, sends through an injected output port with `midi_io.send_cc`, and refuses all unsafe states before touching the port. Wire it from `rytm_randomizer.app` behind `--snapshot-essence-send`, using the existing mock guard for `--dry-run` and the new sender for `--arm`.

**Tech Stack:** Python dataclasses, argparse, existing mido-backed provider, injected fake ports in pytest.

---

## File Structure

- Create `rytm_randomizer/snapshot_essence_hardware_sender.py`: active result dataclass, guard executor, report formatter, error formatter.
- Modify `rytm_randomizer/app.py`: add snapshot essence app flags, validation, dry-run route, armed route, port selection, and confirmation.
- Create `tests/test_snapshot_essence_hardware_sender.py`: sender import-safety, guard, emission, and report tests.
- Modify `tests/test_app_entry.py`: app dry-run and fake-port armed tests.
- Add this spec and plan.

### Task 1: Failing Sender Tests

**Files:**
- Create: `tests/test_snapshot_essence_hardware_sender.py`

- [x] **Step 1: Write import-safety test**

Verify importing `rytm_randomizer.snapshot_essence_hardware_sender` is silent
and does not import `mido`, `rtmidi`, or `librosa`.

- [x] **Step 2: Write refusal tests**

Build a ready snapshot essence send plan from a synthetic Rytm kit fixture.
Assert missing arming returns `missing_arming`, missing confirmation returns
`missing_operator_confirmation`, blocked plans return `plan_not_ready`, and
plans containing an ineligible event return `blocked_by_ineligible_events`.
Every refusal must leave the recording port empty.

- [x] **Step 3: Write acceptance and report tests**

Inject a fake `mido.Message`, execute a ready plan into a recording port, and
assert emitted message count equals `plan.eligible_event_count`, ordering starts
with Pad 1 CC17, and the active report includes `SEND` guard language.

- [x] **Step 4: Run red tests**

Run:

```powershell
pytest tests\test_snapshot_essence_hardware_sender.py -q
```

Expected: fail because the hardware sender module does not exist yet.

### Task 2: Hardware Sender Module

**Files:**
- Create: `rytm_randomizer/snapshot_essence_hardware_sender.py`
- Test: `tests/test_snapshot_essence_hardware_sender.py`

- [x] **Step 1: Implement result and emission dataclasses**

Add `SnapshotEssenceHardwareEmission` and
`SnapshotEssenceHardwareSendResult` with accepted state, reason, source kit
metadata, port name, eligible/blocked counts, emitted messages, and active
metadata.

- [x] **Step 2: Implement executor**

Add `execute_snapshot_essence_hardware_send(plan, out, port_name, armed,
operator_confirmed, sleep)`. Refuse unless armed, confirmed, ready, and free of
ineligible events. Use `send_cc(out, event.control, event.value,
channel=event.wire_channel, sleep=sleep)` for each eligible event.

- [x] **Step 3: Implement report formatters**

Add `format_snapshot_essence_hardware_send_report(result)` and
`format_snapshot_essence_hardware_send_error(message)`. Reports must clearly
state whether real MIDI was emitted and list the active guard policy.

- [x] **Step 4: Run sender tests**

Run:

```powershell
pytest tests\test_snapshot_essence_hardware_sender.py -q
```

Expected: pass.

### Task 3: App Wiring Tests

**Files:**
- Modify: `tests/test_app_entry.py`

- [x] **Step 1: Write dry-run app test**

Run `app.main(["--dry-run", "--snapshot-essence-send", "--snapshot-path",
<fixture>, "--snapshot-slot", "1", "--snapshot-depth", "micro",
"--snapshot-style", "Birmingham dark techno"])`. Assert it prints the guarded
mock report, emits mock messages, opens no port, and returns zero.

- [x] **Step 2: Write armed fake-port app test**

Patch the mido provider to list one fake Rytm port, patch `input()` to return
`0` then `SEND`, inject fake `mido.Message`, run the same command with
`--arm`, and assert the fake port receives the plan's CC messages and closes.

- [x] **Step 3: Write active-mode and conflict tests**

Assert `--snapshot-essence-send` without `--arm` or `--dry-run` returns code 2,
missing required snapshot args are reported, and combining it with
`--dual-machine-snapshot-send` is rejected.

- [x] **Step 4: Run red app tests**

Run:

```powershell
pytest tests\test_app_entry.py::test_app_main_dry_run_snapshot_essence_send_uses_guarded_mock_sender tests\test_app_entry.py::test_app_main_arm_snapshot_essence_send_sends_to_selected_fake_port tests\test_app_entry.py::test_app_main_snapshot_essence_send_requires_active_mode tests\test_app_entry.py::test_app_main_snapshot_essence_send_rejects_dual_machine_conflict -q
```

Expected: fail because the app flag is not wired yet.

### Task 4: App Wiring Implementation

**Files:**
- Modify: `rytm_randomizer/app.py`
- Test: `tests/test_app_entry.py`

- [x] **Step 1: Add argparse flags**

Add `--snapshot-essence-send`, `--snapshot-style`, and
`--snapshot-discovery`. Reuse `--snapshot-path`, `--snapshot-slot`, and
`--snapshot-depth`.

- [x] **Step 2: Add request builder and validation**

Add `_snapshot_essence_send_request_from_args(args)` and validate required
arguments, slot range, active mode, and conflicts with smoke tests or
`--dual-machine-snapshot-send`.

- [x] **Step 3: Add dry-run route**

Build the snapshot essence send plan, run
`build_snapshot_essence_guarded_send_dry_run`, print the guarded dry-run
report, and return success only when accepted.

- [x] **Step 4: Add armed route**

Build the plan first, refuse before provider construction when not ready, list
Rytm outputs, ask for port, ask for exact `SEND`, open the port, execute the
hardware sender, print the active report, and close the port best-effort.

- [x] **Step 5: Run app tests**

Run:

```powershell
pytest tests\test_app_entry.py tests\test_snapshot_essence_hardware_sender.py -q
```

Expected: pass.

### Task 5: Verification, Commit, Push

**Files:**
- All files above.

- [x] **Step 1: Run focused regression**

Run:

```powershell
pytest tests\test_snapshot_essence_hardware_sender.py tests\test_snapshot_essence_guarded_sender.py tests\test_snapshot_essence_send_plan.py tests\test_app_entry.py tests\test_dual_machine_hardware_sender.py tests\architecture\test_no_side_effects.py tests\architecture\test_observability.py -q
```

Expected: pass.

- [x] **Step 2: Run full suite**

Run:

```powershell
pytest -q
```

Expected: pass with existing skips only.

- [x] **Step 3: Run final guards**

Run:

```powershell
git diff --check
git diff --exit-code -- rytm_hybrid_randomizer_v134.py
git status --short
```

- [ ] **Step 4: Stage, commit, and push**

Run:

```powershell
git add docs/superpowers/specs/2026-05-17-snapshot-essence-hardware-send-design.md docs/superpowers/plans/2026-05-17-snapshot-essence-hardware-send.md rytm_randomizer/snapshot_essence_hardware_sender.py rytm_randomizer/app.py tests/test_snapshot_essence_hardware_sender.py tests/test_app_entry.py
git diff --cached --check
git commit -m "Add snapshot essence hardware sender"
git push
```
