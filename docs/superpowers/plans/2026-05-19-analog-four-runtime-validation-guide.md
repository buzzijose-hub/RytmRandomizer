# Analog Four Runtime Validation Guide Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive CLI guide that prints the exact A4 runtime validation sequence for the new single-track hardware path.

**Architecture:** Create one small report module under `rytm_randomizer/analog_four/`, then wire it into `cli.py` and `help_text.py`. Keep the report pure text and passive; it must not import `mido`, open ports, send MIDI, or inspect hardware.

**Tech Stack:** Python dataclasses are not needed; this is a deterministic report function with pytest coverage.

---

### Task 1: Report Module

**Files:**
- Create: `rytm_randomizer/analog_four/runtime_validation_guide.py`
- Test: `tests/test_analog_four_runtime_validation_guide.py`

- [ ] **Step 1: Write failing tests**

```python
def test_a4_runtime_validation_guide_report_lists_single_track_sequence():
    from rytm_randomizer.analog_four.runtime_validation_guide import (
        format_analog_four_runtime_validation_guide,
    )

    report = format_analog_four_runtime_validation_guide()

    assert report[0] == "RytmRandomizer passive Analog Four Runtime Validation Guide"
    assert "Single-track validation order:" in report
    assert "rytm-randomizer --dry-run --analog-four-runtime --analog-four-profile peak-time --analog-four-runtime-track 1" in report
    assert "rytm-randomizer --arm --analog-four-runtime --analog-four-profile peak-time --analog-four-runtime-track 4" in report
    assert "Expected single-track messages: 5" in report
    assert "Expected full-profile messages: 20" in report
    assert "- no MIDI sending" in report
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest tests/test_analog_four_runtime_validation_guide.py -q -n 0
```

Expected: fails because the module does not exist.

- [ ] **Step 3: Implement minimal report module**

Add a pure formatter returning static guide lines.

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
python -m pytest tests/test_analog_four_runtime_validation_guide.py -q -n 0
```

Expected: all tests pass.

### Task 2: CLI Wiring

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Test: `tests/test_analog_four_runtime_validation_guide.py`

- [ ] **Step 1: Write failing CLI test**

```python
def test_a4_runtime_validation_guide_cli_prints_report():
    result = run_cli("analog-four-runtime-validation-guide")

    assert result.returncode == 0
    assert "RytmRandomizer passive Analog Four Runtime Validation Guide" in result.stdout
    assert "rytm-randomizer --arm --analog-four-runtime" in result.stdout
    assert "- no port opening" in result.stdout
    assert result.stderr == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest tests/test_analog_four_runtime_validation_guide.py -q -n 0
```

Expected: CLI exits with usage because the command is not registered.

- [ ] **Step 3: Wire CLI and help text**

Add a `cli.py` branch for `analog-four-runtime-validation-guide`, add the
command to the global usage/help text, and include a per-command help entry.

- [ ] **Step 4: Run focused test**

Run:

```powershell
python -m pytest tests/test_analog_four_runtime_validation_guide.py -q -n 0
```

Expected: all tests pass.

### Task 3: Docs And Verification

**Files:**
- Modify: `docs/STATUS.md`
- Modify: `docs/MANUAL_HARDWARE_VALIDATION.md`

- [ ] **Step 1: Update docs**

Add a status bullet and point the manual validation checklist at the new guide
command.

- [ ] **Step 2: Run verification**

Run:

```powershell
python -m pytest tests/test_analog_four_runtime_validation_guide.py -q -n 0
python -m pytest -m fast -q -n 0
python -m pytest -q -n 0
git diff --check
```

Expected: all tests pass and diff check is clean.

- [ ] **Step 3: Commit**

```powershell
git add docs/superpowers/specs/2026-05-19-analog-four-runtime-validation-guide-design.md docs/superpowers/plans/2026-05-19-analog-four-runtime-validation-guide.md rytm_randomizer/analog_four/runtime_validation_guide.py rytm_randomizer/cli.py rytm_randomizer/help_text.py tests/test_analog_four_runtime_validation_guide.py docs/STATUS.md docs/MANUAL_HARDWARE_VALIDATION.md
git commit -m "feat: add a4 runtime validation guide"
```
