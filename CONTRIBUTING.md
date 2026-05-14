# Contributing To RytmRandomizer

RytmRandomizer is moving from a validated V1.34 hardware script toward a
modular, testable Python package. The current rule is simple: preserve the
musical behavior that V1.34 proved while making the surrounding project easier
to test, review, install, and collaborate on.

## Repository Map

- `rytm_hybrid_randomizer_v134.py` is the hardware-validated V1.34 reference.
  It now imports safely, but it remains the behavior baseline.
- `rytm_randomizer/` is the modular package under active development.
- `tests/` is the regression net and safety gate.
- `Scripts/closeout_check.ps1` is the current local closeout command.
- `Docs/` contains current planning, checkpoints, and safety history.
- `Patches/`, `CaptureTools/`, and `Skills/` are auxiliary project tooling.

## Setup

Use Python 3.11 or newer. The current local development interpreter is recorded
in `.python-version`.

```powershell
python -m pip install -e ".[dev]"
```

The package metadata declares `mido` and `python-rtmidi` because the legacy
hardware script uses MIDI. The modular package must still keep real MIDI usage
behind explicit boundaries and tests.

## Verification

Before committing, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
```

For quick orientation, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\quick_status.ps1
```

## Safety Rules

- Do not open MIDI ports from passive commands.
- Do not send MIDI from passive commands.
- Do not add active CLI behavior without an explicit design and test gate.
- Do not mutate hardware from tests.
- Keep V1.34 behavior changes deliberate, small, and separately verified.
- Use tests before implementation for behavior changes.

## Branching

Use focused branches. The current integration branch is `modularize-v1.34`;
larger execution work should happen on `codex/*` branches or feature branches
and land through review.

## External Review

External review findings are advisory until verified locally. Record broad
review packets in `Docs/`, choose one narrow finding or group, then implement
with targeted tests and full closeout.
