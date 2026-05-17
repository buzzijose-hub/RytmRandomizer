# Dual-Machine Both-Target Hardware Send Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow a ready dual-machine active send plan to send mapped CCs to both Analog Rytm and Analog Four ports in one guarded armed command.

**Architecture:** Extend the active hardware sender with a dual-port executor that routes events by device name through injected output ports. Update `rytm_randomizer.app` so `--arm --dual-machine-snapshot-send --snapshot-target both` builds and validates the plan first, prompts for two ports, requires exact `SEND`, opens both ports, executes, reports, and closes ports.

**Tech Stack:** Python dataclasses, existing mido-backed provider, existing `DualMachineActiveSendPlan`, fake ports in pytest.

---

## File Structure

- Modify `rytm_randomizer/dual_machine_hardware_sender.py`: add dual-port executor, both-target guard metadata, and report wording.
- Modify `rytm_randomizer/app.py`: route both-target active snapshot sends through two output selections and one confirmation prompt.
- Modify `tests/test_dual_machine_hardware_sender.py`: add dual-port acceptance/refusal tests.
- Modify `tests/test_app_entry.py`: add app-level armed both-target fake-port and blocked-candidate tests.
- Add this spec and plan.

### Task 1: Failing Hardware Sender Tests

**Files:**
- Modify: `tests/test_dual_machine_hardware_sender.py`

- [x] **Step 1: Write dual-port acceptance test**

Build a ready `target="both"` plan using the existing synthetic Rytm fixture and
the Analog Four safe-starter plan. Inject fake `mido.Message`. Assert
`execute_dual_machine_dual_port_hardware_send(...)` accepts, sends six Rytm
messages to the Rytm fake port, sends eight A4 messages to the A4 fake port, and
reports `accepted_hardware_send`.

- [x] **Step 2: Write blocked-candidate refusal test**

Build a `target="both"` plan with an A4 saved snapshot path so A4 events are
`saved_offset_candidate`. Assert the dual-port executor returns
`blocked_by_unverified_candidates` and sends no messages to either port.

- [x] **Step 3: Run red hardware tests**

Run:

```powershell
pytest tests\test_dual_machine_hardware_sender.py::test_dual_port_hardware_send_accepts_ready_both_target_plan tests\test_dual_machine_hardware_sender.py::test_dual_port_hardware_send_refuses_blocked_candidates_before_sending -q
```

Expected: fail because the dual-port executor does not exist yet.

### Task 2: Hardware Sender Implementation

**Files:**
- Modify: `rytm_randomizer/dual_machine_hardware_sender.py`

- [x] **Step 1: Add device constants**

Define device keys for `"Analog Rytm MKII"` and `"Analog Four MKII"` inside the
module.

- [x] **Step 2: Add dual-port executor**

Add `execute_dual_machine_dual_port_hardware_send(plan, outputs_by_device,
port_names_by_device, armed, operator_confirmed, sleep)`. Refuse unless armed,
confirmed, `target == "both"`, plan ready, and all events eligible. Route each
eligible CC event to the matching output by `event.device`.

- [x] **Step 3: Update report wording**

Keep existing report compatibility, but make guard policy mention single-target
or validated dual-port both-target sends.

- [x] **Step 4: Run hardware sender tests**

Run:

```powershell
pytest tests\test_dual_machine_hardware_sender.py -q
```

Expected: pass.

### Task 3: Failing App Tests

**Files:**
- Modify: `tests/test_app_entry.py`

- [x] **Step 1: Write armed both-target fake-port test**

Patch the mido provider to list `("Fake Rytm", "Fake A4")`; patch `input()` to
return `0`, `1`, and `SEND`; run the app with `--arm
--dual-machine-snapshot-send --snapshot-target both`. Assert one provider list
call, both ports opened and closed, Rytm fake port receives six messages, A4
fake port receives eight messages, and the report is accepted.

- [x] **Step 2: Write blocked-candidate app test**

Run `--arm --dual-machine-snapshot-send --snapshot-target both` with
`--analog-four-path` and `--analog-four-slot`. Assert refusal happens before
provider list/open and report reason is `blocked_by_unverified_candidates`.

- [x] **Step 3: Run red app tests**

Run:

```powershell
pytest tests\test_app_entry.py::test_app_main_arm_dual_machine_snapshot_send_both_target_sends_to_two_fake_ports tests\test_app_entry.py::test_app_main_arm_dual_machine_snapshot_send_both_target_refuses_blocked_candidates_before_port_open -q
```

Expected: fail because the app still refuses `target=both`.

### Task 4: App Implementation

**Files:**
- Modify: `rytm_randomizer/app.py`

- [x] **Step 1: Change validation order**

In `_run_arm_dual_machine_snapshot_send`, refuse not-ready plans before any
provider construction. Do not refuse `target=both` when the plan is ready.

- [x] **Step 2: Add both-target route**

Add `_run_arm_dual_machine_snapshot_send_both(plan)` or an equivalent helper
that lists outputs once, asks for the Analog Rytm port, asks for the Analog Four
port, rejects duplicate port names, requires exact `SEND`, opens both ports, and
calls the dual-port executor.

- [x] **Step 3: Preserve single-target behavior**

Keep existing Rytm-only and A4-only flow unchanged for `target="rytm"` and
`target="analog-four"`.

- [x] **Step 4: Run app tests**

Run:

```powershell
pytest tests\test_app_entry.py tests\test_dual_machine_hardware_sender.py -q
```

Expected: pass.

### Task 5: Verification, Commit, Push

**Files:**
- All files above.

- [x] **Step 1: Run focused regression**

Run:

```powershell
pytest tests\test_dual_machine_hardware_sender.py tests\test_app_entry.py tests\test_dual_machine_active_send_plan.py tests\test_dual_machine_guarded_sender.py tests\test_snapshot_essence_hardware_sender.py tests\architecture\test_no_side_effects.py tests\architecture\test_observability.py -q
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
git add docs/superpowers/specs/2026-05-17-dual-machine-both-target-hardware-send-design.md docs/superpowers/plans/2026-05-17-dual-machine-both-target-hardware-send.md rytm_randomizer/dual_machine_hardware_sender.py rytm_randomizer/app.py tests/test_dual_machine_hardware_sender.py tests/test_app_entry.py
git diff --cached --check
git commit -m "Add dual-machine both-target hardware send"
git push
```
