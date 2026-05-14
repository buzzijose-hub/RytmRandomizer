# RytmRandomizer

RytmRandomizer is a Python project for controlled, musical randomization of an
Elektron Analog Rytm MKII. The validated V1.34 script already proves the
musical command surface; the package in this repository is the staged,
testable path toward a safer modular application.

The current modular package remains cautious by design. Passive CLI commands
can report, search, inspect, preview, and summarize mock/runtime plans without
opening MIDI ports or sending MIDI. Hardware-facing behavior stays behind
explicit future gates.

## Repository Map

- `rytm_hybrid_randomizer_v134.py` is the hardware-validated V1.34 reference.
  It imports safely and is still the behavior baseline.
- `rytm_randomizer/` is the modular package under active development.
- `tests/` contains the local safety and regression net.
- `Scripts/closeout_check.ps1` runs the current full local verification suite.
- `Docs/` records the current planning, checkpoints, and safety decisions.
- `CaptureTools/`, `Patches/`, and `Skills/` are auxiliary tooling areas.

## Install

Use Python 3.11 or newer.

```powershell
python -m pip install -e ".[dev]"
```

The package metadata declares the MIDI dependencies used by the legacy
hardware script:

- `mido`
- `python-rtmidi`

Declaring those dependencies does not mean passive package commands open ports
or send MIDI. The passive tests still guard those boundaries.

On Linux, `python-rtmidi` may require ALSA development headers if a matching
wheel is unavailable.

## Run

Passive modular CLI:

```powershell
python -m rytm_randomizer.cli --help
python -m rytm_randomizer.cli project-status-report --summary
python -m rytm_randomizer.cli mock-mapper-report
python -m rytm_randomizer.cli runtime-plan-report
```

Installed console entry point:

```powershell
rytm-randomizer
```

Current hardware-validated reference script:

```powershell
python .\rytm_hybrid_randomizer_v134.py
```

Only run the hardware script when the Analog Rytm is intentionally connected
and you are ready for its interactive MIDI behavior.

## Test

Run the current full closeout suite:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
```

Cross-platform closeout for Windows, macOS, and Linux:

```powershell
python .\Scripts\closeout_check.py
```

On macOS/Linux, use the same command with forward slashes:

```bash
python Scripts/closeout_check.py
```

Run all pytest tests directly:

```powershell
python -m pytest
```

## Current Passive CLI Capabilities

```powershell
python -m rytm_randomizer.cli report
python -m rytm_randomizer.cli project-status-report
python -m rytm_randomizer.cli mock-mapper-report
python -m rytm_randomizer.cli runtime-plan-report
python -m rytm_randomizer.cli active-boundary-report
python -m rytm_randomizer.cli mock-runtime-active-bridge-report
python -m rytm_randomizer.cli anchor-profile-report
python -m rytm_randomizer.cli behavior-parity-report
python -m rytm_randomizer.cli list-commands
python -m rytm_randomizer.cli list-scenes
python -m rytm_randomizer.cli list-group-profiles
python -m rytm_randomizer.cli search-commands BD
python -m rytm_randomizer.cli inspect-command J
python -m rytm_randomizer.cli preview-group-profile 2
```

Passive commands remain read-only:

- no MIDI sending
- no MIDI port opening
- no command execution
- no hardware mutation
- no hardware required

## V1.34 Scene Surface

V1.34 locks in the expanded scene layer:

```text
S0  = Home / Clean anchors
S1  = Rolling
S1A = Rolling Light
S1B = Rolling Push
S2  = Deeper
S2A = Deeper Groove
S2B = Deeper Pressure
S3  = Intense
S3A = Intense Motion
S3B = Intense Grit
S4  = Wild
S4A = Wild Controlled
S4B = Wild Maximum
S5  = Back to Clean anchors
```

Current four-lane layout:

```text
Pad 1 = BD Hard / protected kick foundation
Pad 2 = BD Classic / secondary percussion lane
Pad 3 = SY Raw / bass + synth-percussion motion lane
Pad 4 = BD Acoustic / body + accent pressure lane
```

Recommended hardware validation flow for the legacy script:

```text
SCN
GM
S1A
S3A
S3B
S4B
S5
1
Z
Q
```

Keep monitoring volume moderate for `S3B` and `S4B`.
