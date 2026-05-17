# Dual-Machine Armed Snapshot Send Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first guarded real hardware snapshot send path for a single target machine.

**Architecture:** Keep passive CLI read-only. Add a hardware sender module that consumes `DualMachineActiveSendPlan` and sends eligible CCs through an injected output port using `midi_io.send_cc`. Wire it from `rytm_randomizer.app` behind `--arm`; wire the same app modifier to the existing mock guarded sender under `--dry-run`.

**Tech Stack:** Python argparse, existing mido-backed provider, injected fake ports in tests, pytest.

---

## File Structure

- Create `rytm_randomizer/dual_machine_hardware_sender.py`: active sender result, guard checks, send executor, formatter.
- Modify `rytm_randomizer/app.py`: add snapshot-send arguments, validation, dry-run path, armed path, port selection, confirmation.
- Modify `tests/test_app_entry.py`: app-level dry-run and fake-port armed tests.
- Create `tests/test_dual_machine_hardware_sender.py`: import safety and guard behavior tests.
- Add this spec and plan.

### Task 1: Failing Tests

**Files:**
- Create: `tests/test_dual_machine_hardware_sender.py`
- Modify: `tests/test_app_entry.py`

- [x] **Step 1: Write module tests**

Cover import safety, missing arming, missing confirmation, target `both`
refusal, blocked plan refusal, and accepted fake-port sends.

- [x] **Step 2: Write app tests**

Cover dry-run Rytm-only snapshot send, armed fake-port Rytm-only snapshot send,
armed blocked A4 candidate refusal before port opening, and active-mode
validation.

- [x] **Step 3: Run red tests**

Run:

```powershell
pytest tests\test_dual_machine_hardware_sender.py tests\test_app_entry.py::test_app_main_dry_run_dual_machine_snapshot_send_uses_guarded_mock_sender tests\test_app_entry.py::test_app_main_arm_dual_machine_snapshot_send_sends_to_selected_fake_port tests\test_app_entry.py::test_app_main_arm_dual_machine_snapshot_send_refuses_blocked_plan_before_port_open tests\test_app_entry.py::test_app_main_dual_machine_snapshot_send_requires_active_mode -q
```

Expected: fail because the module and app args do not exist yet.

### Task 2: Hardware Sender Module

**Files:**
- Create: `rytm_randomizer/dual_machine_hardware_sender.py`
- Test: `tests/test_dual_machine_hardware_sender.py`

- [x] **Step 1: Implement result dataclass**

Create `DualMachineHardwareSendResult` with target, accepted, reason,
eligible count, blocked count, emitted count, port name, and sent message tuple.

- [x] **Step 2: Implement executor**

Add `execute_dual_machine_hardware_send(plan, out, port_name, armed,
operator_confirmed, sleep)`. Refuse unless armed, confirmed, ready, and single
target. Use `midi_io.send_cc` for eligible events.

- [x] **Step 3: Implement formatter**

Print a deterministic active report with explicit warning that this path sends
real MIDI only when accepted.

- [x] **Step 4: Run module tests**

Run:

```powershell
pytest tests\test_dual_machine_hardware_sender.py -q
```

Expected: pass.

### Task 3: App Wiring

**Files:**
- Modify: `rytm_randomizer/app.py`
- Modify: `tests/test_app_entry.py`

- [x] **Step 1: Add argparse flags**

Add `--dual-machine-snapshot-send`, `--snapshot-path`, `--snapshot-slot`,
`--snapshot-depth`, `--snapshot-target`, `--analog-four-path`, and
`--analog-four-slot`.

- [x] **Step 2: Add validation**

Require active mode and required snapshot args when snapshot-send is present.
Reject missing Analog Four slot/path pairs.

- [x] **Step 3: Add dry-run behavior**

Build the bridge, run `build_dual_machine_guarded_send_dry_run`, print the
guarded dry-run report, and never open ports.

- [x] **Step 4: Add armed behavior**

Build plan first. If refused, print the hardware send report without opening a
port. If accepted, list outputs, choose one port, require `SEND`, open the port,
execute, print report, and close the port.

- [x] **Step 5: Run app tests**

Run:

```powershell
pytest tests\test_app_entry.py tests\test_dual_machine_hardware_sender.py -q
```

Expected: pass.

### Task 4: Verification

**Files:**
- No source changes expected.

- [x] **Step 1: Run real-dump dry-run**

Run:

```powershell
python -m rytm_randomizer.app --dry-run --dual-machine-snapshot-send --snapshot-path "G:\ANALOG RYTM\WHOLE PROJECT DUMP\PROJECTRYTM01.syx" --snapshot-slot 1 --snapshot-depth micro --snapshot-target rytm
```

Expected: accepted true, emitted mock messages 60.

- [x] **Step 2: Run broad regression**

Run:

```powershell
pytest tests\test_app_entry.py tests\test_dual_machine_hardware_sender.py tests\test_dual_machine_guarded_sender.py tests\test_dual_machine_active_send_plan.py tests\test_real_midi_passive_cli_safety.py tests\architecture\test_no_side_effects.py tests\architecture\test_observability.py -q
```

Expected: pass.

- [x] **Step 3: Run full suite**

Run:

```powershell
pytest -q
```

Expected: pass with existing skips only.

### Task 5: Commit and Push

**Files:**
- All files above.

- [x] **Step 1: Run final guards**

Run:

```powershell
git diff --check
git diff --exit-code -- rytm_hybrid_randomizer_v134.py
git status --short
```

- [x] **Step 2: Stage and commit**

Run:

```powershell
git add docs/superpowers/specs/2026-05-17-dual-machine-armed-snapshot-send-design.md docs/superpowers/plans/2026-05-17-dual-machine-armed-snapshot-send.md rytm_randomizer/dual_machine_hardware_sender.py rytm_randomizer/app.py tests/test_dual_machine_hardware_sender.py tests/test_app_entry.py
git diff --cached --check
git commit -m "Add guarded armed snapshot send path"
```

- [x] **Step 3: Push**

Run:

```powershell
git push
```
