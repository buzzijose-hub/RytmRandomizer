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

For non-Windows collaborators, run the cross-platform closeout:

```powershell
python .\Scripts\closeout_check.py
```

On macOS/Linux, use:

```bash
python Scripts/closeout_check.py
```

GitHub Actions are currently manual-only gates to avoid automatic hosted-runner
minute usage during execution-plan work. Use local closeout as the daily
feedback loop. Workflow actions use current major versions prepared for
GitHub's Node 24 runner transition.

The manual `tests` workflow runs a lean Windows/macOS/Ubuntu Python 3.13
matrix and the package coverage gate:

```powershell
python -m pytest --cov=rytm_randomizer --cov-branch --cov-fail-under=84
```

The current ratchet floor is 84% branch coverage for `rytm_randomizer/`. Raise
the floor when coverage improves; do not lower it.

Before final PR readiness or a major merge decision, manually run the `tests`
workflow and, when the extra confidence is worth the Actions minutes, the
`tests-full-matrix` workflow to exercise Windows/macOS/Ubuntu across Python
3.11, 3.12, and 3.13.

For quick orientation, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\quick_status.ps1
```

Optional local hygiene tools are configured with `pre-commit`. Install them
when you want the same formatting/lint checks available before pushing:

```powershell
python -m pip install pre-commit
pre-commit install
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

For PR #2 review, start with:

- `Docs/COLLABORATOR_PR_REVIEW_CHECKLIST.md`

That checklist records the safe review order, local verification commands,
finding format, and boundaries that remain blocked until separate approval.
