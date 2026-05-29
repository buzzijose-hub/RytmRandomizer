# Rytm OXI-Style Randomizer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an OXI-inspired per-pad randomizer contract layer to the Analog Rytm live snapshot shell.

**Architecture:** Extend `analog_rytm_snapshot_shell.py` with pad randomizer contracts stored in session guardrails. `randomize` uses the existing anchor-relative mutation path, then adds density-based event selection and bias-directed movement before clamping to existing live-safety limits.

**Tech Stack:** Python 3.13, pytest, dataclasses, existing snapshot shell tests, existing `MockMidiSender`.

---

### Task 1: Add Contract Behavior Tests

**Files:**
- Modify: `tests/test_analog_rytm_snapshot_shell.py`

- [ ] **Step 1: Write failing tests**

Add tests covering default inferred contracts, density off/low/full, brighter/tighter bias, amount width, status output, and invalid commands.

```python
def test_snapshot_shell_status_reports_default_randomizer_contracts(capsys) -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    shell = AnalogRytmSnapshotShell(build_snapshot_shell_anchor(_snapshot()), MockMidiSender())

    assert shell.dispatch("status") is True

    captured = capsys.readouterr()
    assert "randomizer pads:" in captured.out
    assert "1=kick/micro/low/tighter" in captured.out
    assert "3=synth/normal/medium/neutral" in captured.out
    assert "9=hat/normal/high/brighter" in captured.out
```

- [ ] **Step 2: Verify red**

Run:

```powershell
& "C:\Users\Jose Buzzi\AppData\Local\Programs\Python\Python313\python.exe" -m pytest tests\test_analog_rytm_snapshot_shell.py -n 0
```

Expected: tests fail because `randomize`, randomizer contracts, and status output do not exist yet.

### Task 2: Add Pad Contract Types and Defaults

**Files:**
- Modify: `rytm_randomizer/engines/analog_rytm_snapshot_shell.py`

- [ ] **Step 1: Add types and defaults**

Add literals for role, amount, density, and bias; add `SnapshotPadRandomizerContract`; add default contract inference from `classify_rytm_pad_role`.

```python
SnapshotRandomizerRole: TypeAlias = Literal["kick", "snare", "tom", "hat", "cymbal", "synth", "noise", "perc"]
SnapshotRandomizerAmount: TypeAlias = Literal["micro", "normal", "wide"]
SnapshotRandomizerDensity: TypeAlias = Literal["off", "low", "medium", "high", "full"]
SnapshotRandomizerBias: TypeAlias = Literal["neutral", "darker", "brighter", "tighter", "looser", "grittier"]

@dataclass(frozen=True)
class SnapshotPadRandomizerContract:
    role: SnapshotRandomizerRole
    amount: SnapshotRandomizerAmount
    density: SnapshotRandomizerDensity
    bias: SnapshotRandomizerBias
```

- [ ] **Step 2: Run focused tests**

Run the focused snapshot shell test command. Expected: remaining failures identify missing command behavior.

### Task 3: Add Pad Contract Commands and Status

**Files:**
- Modify: `rytm_randomizer/engines/analog_rytm_snapshot_shell.py`

- [ ] **Step 1: Store per-pad contract overrides**

Add `randomizer_overrides` to `SnapshotSessionGuardrails`. Preserve it through mode/depth/lock/preset changes unless `guards reset` is used.

- [ ] **Step 2: Extend `pad` command**

Support:

```text
pad N role kick|snare|tom|hat|cymbal|synth|noise|perc|auto
pad N amount micro|normal|wide
pad N density off|low|medium|high|full
pad N bias neutral|darker|brighter|tighter|looser|grittier
```

- [ ] **Step 3: Extend status output**

Add compact output:

```text
randomizer pads: 1=kick/micro/low/tighter, ...
```

### Task 4: Add Randomize Mutation Path

**Files:**
- Modify: `rytm_randomizer/engines/analog_rytm_snapshot_shell.py`

- [ ] **Step 1: Add command**

Add `randomize` to `SNAPSHOT_SHELL_COMMANDS` as a staged full-kit command. Optional aliases: `rand`, `r`.

- [ ] **Step 2: Density filter**

Before mutating an event in randomizer mode, decide whether the event is eligible for this generation:

```python
threshold = {"off": 0, "low": 25, "medium": 50, "high": 75, "full": 100}[density]
```

Use deterministic hashing from command, generation, pad, section, parameter, and anchor value.

- [ ] **Step 3: Amount mapping**

Map:

```python
micro -> gentle
normal -> normal
wide -> strong
```

Use this as the effective pad depth for randomizer mode while preserving live pad caps and locks.

- [ ] **Step 4: Bias movement**

Apply musical sign preferences:

- `brighter`: filter frequency tends up
- `darker`: filter frequency tends down
- `tighter`: decay/hold/release and space tend down
- `looser`: decay/hold/release and space tend up
- `grittier`: drive/resonance/transient/noise-adjacent rows tend up

All movements still clamp to existing anchor-relative windows and value metadata.

### Task 5: Verify and Hardware Script

**Files:**
- Modify: `tests/test_analog_rytm_snapshot_shell.py`
- Modify: `rytm_randomizer/engines/analog_rytm_snapshot_shell.py`

- [ ] **Step 1: Run focused tests**

```powershell
& "C:\Users\Jose Buzzi\AppData\Local\Programs\Python\Python313\python.exe" -m pytest tests\test_analog_rytm_snapshot_shell.py -n 0
```

- [ ] **Step 2: Run fast and architecture suites**

```powershell
& "C:\Users\Jose Buzzi\AppData\Local\Programs\Python\Python313\python.exe" -m pytest -m fast
& "C:\Users\Jose Buzzi\AppData\Local\Programs\Python\Python313\python.exe" -m pytest tests\architecture\ -q
```

- [ ] **Step 3: Run style checks**

```powershell
& "C:\Users\Jose Buzzi\AppData\Local\Programs\Python\Python313\python.exe" -m ruff check rytm_randomizer\engines\analog_rytm_snapshot_shell.py tests\test_analog_rytm_snapshot_shell.py
& "C:\Users\Jose Buzzi\AppData\Local\Programs\Python\Python313\python.exe" -m black --check --target-version=py311 rytm_randomizer\engines\analog_rytm_snapshot_shell.py tests\test_analog_rytm_snapshot_shell.py
& "C:\Users\Jose Buzzi\AppData\Local\Programs\Python\Python313\python.exe" -m isort --profile black --check-only rytm_randomizer\engines\analog_rytm_snapshot_shell.py tests\test_analog_rytm_snapshot_shell.py
```

- [ ] **Step 4: Provide hardware script**

Give the operator a conservative PowerShell startup command and shell commands:

```text
status
pad 1 density low
pad 1 bias tighter
pad 2 density medium
pad 2 bias darker
pad 9 density high
pad 9 bias brighter
tune micro
randomize
changes
send
```
