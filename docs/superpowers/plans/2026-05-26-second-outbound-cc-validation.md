# Second Outbound CC Validation Implementation Plan

> Status: proposed
> Requirements reference: This plan follows `docs/PLAN_REQUIREMENTS.md`;
> because it is documentation-only, code, parity, coverage, dependency, and
> active-runtime gates are satisfied by non-applicability plus verification
> that only docs changed.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prepare the next safe hardware validation pass by documenting a repeatability-focused second outbound CC test, without running hardware or adding code.

**Architecture:** This is a documentation-only planning slice. It reuses the already-merged one-CC validation helper from `rytm_randomizer.app`, keeps the passive CLI untouched, and parks any new CC/parameter test behind a separate future candidate approval.

**Tech Stack:** Markdown documentation, existing manual hardware validation runbook, existing `python -m rytm_randomizer.app --arm --validate-one-cc ...` command, existing pytest documentation checks.

---

## Current Evidence

PR #133 merged the first outbound Rytm CC validation milestone:

- Existing helper:
  `python -m rytm_randomizer.app --arm --validate-one-cc --channel N --control 17 --value 64`
- Dry-run proof:
  `python -m rytm_randomizer.app --dry-run --validate-one-cc --channel N --control 17 --value 64`
- Hardware result:
  `docs/hardware-validation/2026-05-26-outbound-12-track-cc-results.md`
- Result: tracks 1 through 12 responded to mido channels 0 through 11,
  respectively, with no cross-pad changes and no weird behavior.

The next safe hardware step is a repeatability pass using the same command
shape, not a new parameter or mutation expansion.

## File Structure

- Create: `docs/superpowers/specs/2026-05-26-second-outbound-cc-validation-design.md`
  - Captures the design decision for a repeatability-first second pass.
- Create: `docs/superpowers/plans/2026-05-26-second-outbound-cc-validation.md`
  - Gives future agents/operators the exact docs-only implementation plan.
- Modify: `docs/MANUAL_HARDWARE_VALIDATION.md`
  - Adds the second outbound CC validation runbook and stop conditions.
- Modify: `docs/STATUS.md`
  - Records the planning checkpoint and confirms no hardware was run.

No package source, tests, fixtures, CI, dependency pins, or active behavior are
modified by this plan.

## Safety Boundaries

- No code changes.
- No test changes.
- No real MIDI during this planning slice.
- No port opening during this planning slice.
- No hardware required during this planning slice.
- No new CLI command.
- No scene execution.
- No group mutation.
- No SysEx.
- No pattern, project, kit-save, transport, or clock behavior.
- No Analog Four behavior.
- No unattended hardware send.
- No V1.34 parity fixture changes.

---

### Task 1: Record The Design Decision

**Files:**
- Create: `docs/superpowers/specs/2026-05-26-second-outbound-cc-validation-design.md`

- [ ] **Step 1: Create the design spec**

Write the design spec with these decisions:

- The second hardware pass is repeatability-first.
- It uses the same existing helper and same CC shape as PR #133.
- It validates tracks 1 through 12 one at a time.
- It does not test a new CC number.
- It does not test mutation commands.
- It does not test scenes, SysEx, transport, clock, kit/project writes, or
  Analog Four.
- Hardware is not run as part of this docs-only slice.

- [ ] **Step 2: Verify the spec says hardware is not run**

Run:

```powershell
rg -n "does not authorize|does not require|without running hardware|planning gate" docs/superpowers/specs/2026-05-26-second-outbound-cc-validation-design.md
```

Expected: the spec clearly marks the slice as planning-only.

---

### Task 2: Add Manual Runbook Section

**Files:**
- Modify: `docs/MANUAL_HARDWARE_VALIDATION.md`

- [ ] **Step 1: Add a second validation runbook**

Add a new section after the first outbound validation result:

```markdown
## Second Outbound 12-Track CC Repeatability Validation

This is the next recommended hardware pass, but it is not run by this planning
slice. The goal is repeatability: prove the first successful all-12 result can
be repeated before testing any new CC number, mutation command, scene, SysEx, or
Analog Four behavior.

Use the same one-CC helper and the same message shape:

`python -m rytm_randomizer.app --arm --validate-one-cc --channel N --control 17 --value 64`

Run tracks one at a time:

| Track | Target mido channel | Control | Value | Expected result |
|---:|---:|---:|---:|---|
| 1 | 0 | 17 | 64 | Only Track 1 changes |
| 2 | 1 | 17 | 64 | Only Track 2 changes |
| 3 | 2 | 17 | 64 | Only Track 3 changes |
| 4 | 3 | 17 | 64 | Only Track 4 changes |
| 5 | 4 | 17 | 64 | Only Track 5 changes |
| 6 | 5 | 17 | 64 | Only Track 6 changes |
| 7 | 6 | 17 | 64 | Only Track 7 changes |
| 8 | 7 | 17 | 64 | Only Track 8 changes |
| 9 | 8 | 17 | 64 | Only Track 9 changes |
| 10 | 9 | 17 | 64 | Only Track 10 changes |
| 11 | 10 | 17 | 64 | Only Track 11 changes |
| 12 | 11 | 17 | 64 | Only Track 12 changes |

Do not test a new CC number in this pass. If a new parameter needs validation,
write a separate candidate note first.
```

- [ ] **Step 2: Verify the manual doc has the second-pass boundary**

Run:

```powershell
rg -n "Second Outbound|repeatability|Do not test a new CC" docs/MANUAL_HARDWARE_VALIDATION.md
```

Expected: the second pass is present and keeps new CC testing parked.

---

### Task 3: Update Project Status

**Files:**
- Modify: `docs/STATUS.md`

- [ ] **Step 1: Add a current status entry**

Add this entry at the top of `## Recent Cleanup`:

```markdown
- 2026-05-26: Second outbound CC validation planning checkpoint created.
  The next recommended hardware pass is repeatability-first: rerun the same
  one-CC all-12-track validation from PR #133 before testing any new CC number
  or mutation behavior. This slice is documentation-only and does not run
  hardware, open ports, send MIDI, or change code.
```

- [ ] **Step 2: Verify status mentions planning-only**

Run:

```powershell
rg -n "Second outbound CC validation|documentation-only|does not run hardware" docs/STATUS.md
```

Expected: the status entry states no hardware was run.

---

### Task 4: Verify Documentation-Only Scope

**Files:**
- No additional file changes.

- [ ] **Step 1: Check changed files**

Run:

```powershell
git diff --name-only
git status --short
git diff --cached --name-only
```

Before staging, `git diff --name-only` should list the modified tracked docs:

- `docs/MANUAL_HARDWARE_VALIDATION.md`
- `docs/STATUS.md`

Before staging, `git status --short` should list only:

- `docs/MANUAL_HARDWARE_VALIDATION.md`
- `docs/STATUS.md`
- `docs/superpowers/specs/2026-05-26-second-outbound-cc-validation-design.md`
- `docs/superpowers/plans/2026-05-26-second-outbound-cc-validation.md`

After staging, the second command should list only:

- `docs/MANUAL_HARDWARE_VALIDATION.md`
- `docs/STATUS.md`
- `docs/superpowers/specs/2026-05-26-second-outbound-cc-validation-design.md`
- `docs/superpowers/plans/2026-05-26-second-outbound-cc-validation.md`

- [ ] **Step 2: Run focused doc checks**

Run:

```powershell
python -m pytest tests/test_manual_hardware_validation_doc.py -n 0
```

Expected: PASS.

- [ ] **Step 3: Run mechanical review gate**

Run:

```powershell
python scripts/code_review_gate.py --mode cli
```

Expected: PASS.

---

## Self-Review

- Spec coverage: the plan creates a repeatability-first design, updates the
  manual runbook, updates project status, and avoids code/hardware changes.
- Placeholder scan: no placeholder or open-ended implementation step remains.
- Type and API consistency: no new Python API is introduced.
- Safety check: no real MIDI, ports, active behavior, SysEx, Analog Four, or
  mutation expansion occurs in this slice.

## Execution Recommendation

Implement only the documentation tasks in this plan. Stop before any hardware
validation. A later explicit studio session can run the second pass from the
manual validation checklist.
