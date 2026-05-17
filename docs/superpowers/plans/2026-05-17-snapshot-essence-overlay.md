# Snapshot Essence Overlay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a passive report that compares a captured Rytm kit snapshot against a style-driven 12-pad machine plan.

**Architecture:** Add a read-only overlay module that composes the existing snapshot mutation planner with the existing style-intent/machine-catalog planner. Wire it into the passive CLI as a report only; no active sender or MIDI port access in this slice.

**Tech Stack:** Python dataclasses, existing snapshot/style modules, passive CLI dispatch, pytest.

---

## File Structure

- Create `rytm_randomizer/snapshot_essence_overlay.py`: overlay dataclasses, builder, formatter, error formatter.
- Modify `rytm_randomizer/cli.py`: add `snapshot-essence-overlay-report` argument parsing and dispatch.
- Modify `rytm_randomizer/help_text.py`: add usage/help entry for the new passive report.
- Create `tests/test_snapshot_essence_overlay.py`: module behavior, CLI behavior, import safety.
- Add this spec and plan.

### Task 1: Failing Tests

**Files:**
- Create: `tests/test_snapshot_essence_overlay.py`

- [x] **Step 1: Write import-safety test**

Verify importing `rytm_randomizer.snapshot_essence_overlay` is silent and does
not import `mido`, `rtmidi`, or `librosa`.

- [x] **Step 2: Write overlay behavior test**

Use a synthetic Rytm kit fixture where Pad 1 already matches `BD Hard`, Pad 3
already matches `BD FM`, and other pads use disabled/generic engines. Assert
that the overlay covers all 12 pads, separates same-engine ready pads from
engine-switch-ready pads, and records mapped machine values.

- [x] **Step 3: Write CLI test**

Run:

```powershell
python -m rytm_randomizer.cli snapshot-essence-overlay-report <fixture> --slot 1 --depth micro --style "Birmingham dark techno"
```

Expected: report header, style prompt, all 12 pad rows, engine switch count,
passive safety lines, and no stderr.

- [x] **Step 4: Run red tests**

Run:

```powershell
pytest tests\test_snapshot_essence_overlay.py -q
```

Expected: fail because the module and CLI command do not exist yet.

### Task 2: Passive Overlay Module

**Files:**
- Create: `rytm_randomizer/snapshot_essence_overlay.py`

- [x] **Step 1: Implement dataclasses**

Create `SnapshotEssenceOverlayPad` and `SnapshotEssenceOverlayPlan` with style
prompt, matched profiles, tags, discovery, kit metadata, pad rows, status
counts, and blocked state.

- [x] **Step 2: Implement builder**

Add `build_snapshot_essence_overlay_plan_from_file(path, slot, depth, style,
discovery=None)`. Decode via `build_snapshot_mutation_plan_from_file`; resolve
style via `build_style_intent_request`; rank roles via `build_essence_role_plan`.

- [x] **Step 3: Implement formatter**

Print deterministic lines showing captured machine, selected mapped machine,
whether a machine switch is required, captured mutation change count, and safety
lines.

- [x] **Step 4: Run module tests**

Run:

```powershell
pytest tests\test_snapshot_essence_overlay.py -q
```

Expected: behavior tests pass except CLI wiring until Task 3.

### Task 3: CLI Wiring

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`

- [x] **Step 1: Add CLI dispatch**

Accept:

```text
snapshot-essence-overlay-report <path> --slot <slot> --depth <depth> --style <style> [--discovery <0..1>]
```

Return formatted errors on file, slot, depth, and discovery problems.

- [x] **Step 2: Add help text**

Add the command to `USAGE`, `--help`, command list, and its dedicated help entry.

- [x] **Step 3: Run CLI tests**

Run:

```powershell
pytest tests\test_snapshot_essence_overlay.py -q
```

Expected: pass.

### Task 4: Verification

**Files:**
- No source changes expected.

- [x] **Step 1: Run real project overlay**

Run:

```powershell
python -m rytm_randomizer.cli snapshot-essence-overlay-report "G:\ANALOG RYTM\WHOLE PROJECT DUMP\PROJECTRYTM01.syx" --slot 1 --depth micro --style "Birmingham dark techno"
```

Expected: report reads the real dump and prints 12 pad overlay rows.

- [x] **Step 2: Run focused regression**

Run:

```powershell
pytest tests\test_snapshot_essence_overlay.py tests\test_style_intent_profiles.py tests\test_twelve_pad_mock_runtime.py tests\test_snapshot_mutation_planner.py tests\test_real_midi_passive_cli_safety.py tests\architecture\test_no_side_effects.py -q
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

- [ ] **Step 1: Run final guards**

Run:

```powershell
git diff --check
git diff --exit-code -- rytm_hybrid_randomizer_v134.py
git status --short
```

- [ ] **Step 2: Stage and commit**

Run:

```powershell
git add docs/superpowers/specs/2026-05-17-snapshot-essence-overlay-design.md docs/superpowers/plans/2026-05-17-snapshot-essence-overlay.md rytm_randomizer/snapshot_essence_overlay.py rytm_randomizer/cli.py rytm_randomizer/help_text.py tests/test_snapshot_essence_overlay.py tests/test_cli.py tests/fixtures/cli_help_expected.txt
git diff --cached --check
git commit -m "Add snapshot essence overlay report"
```

- [ ] **Step 3: Push**

Run:

```powershell
git push
```
