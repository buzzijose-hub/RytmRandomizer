# RytmRandomizer

RytmRandomizer is a Python tool for the Elektron Analog Rytm MK2 hardware drum machine. It randomizes and mutates drum-synthesis parameters over MIDI, organized as a 4-pad layout, with a layered "scene" system (Rolling / Deeper / Intense / Wild, each with A/B depth variants) and safety guardrails so you don't accidentally send MIDI to the hardware. You drive it from a small text prompt: pick a scene or command, and it sends the corresponding parameter changes to the Rytm.

## Repository map

| Path | What it is |
|------|------------|
| `rytm_randomizer/` | The active modular package currently being built. This is where new product code goes. |
| `rytm_hybrid_randomizer_v134.py` | The frozen, hardware-validated reference monolith. Do not change its musical behavior — it is the baseline of truth. |
| `Patches/` | Auxiliary one-off tooling. Not part of the core product. |
| `CaptureTools/` | Auxiliary one-off tooling (capture/diagnostic helpers). Not part of the core product. |
| `Skills/` | Agent tooling — not product code. |
| `tests/` | The test suite (~50 test files). |
| `Docs/` | Project documentation and process notes. |
| `Scripts/` | Helper scripts (e.g. closeout checks). |

## Requirements

- Python >= 3.9
- Dependencies: [`mido`](https://pypi.org/project/mido/) and [`python-rtmidi`](https://pypi.org/project/python-rtmidi/)

Per-OS notes:

- **Windows / macOS** — `python-rtmidi` ships prebuilt wheels, so `pip install` just works.
- **Linux** — if no wheel is available for your platform, `python-rtmidi` builds from source and you may need the ALSA development headers first: `sudo apt install libasound2-dev`.

## Installation

```bash
pip install -e ".[dev]"
```

This installs the package in editable mode along with development dependencies, via `pyproject.toml` (the packaging config is being added by a parallel workstream).

## Running

```bash
rytm-randomizer
```

`rytm-randomizer` is the console entry point for the modular package. To run the current hardware-validated monolith directly:

```bash
python rytm_hybrid_randomizer_v134.py
```

## Testing

```bash
pytest
```

---

## Scenes & commands

The scene system below is the validated V1.34 layer. These tables are the canonical reference for what commands exist.

### Scene system

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

### Four-lane pad layout

```text
Pad 1 = BD Hard / protected kick foundation
Pad 2 = BD Classic / secondary percussion lane
Pad 3 = SY Raw / bass + synth-percussion motion lane
Pad 4 = BD Acoustic / body + accent pressure lane
```

### Safety rules

- No new machine profiles.
- No new MIDI CC mappings.
- No new parameter ranges.
- No Pads 5–12 expansion yet.
- Main-prompt `1`, `2`, and `3` remain guarded and send no MIDI.
- Four-pad scene/global commands auto-load anchors if needed.

### Recommended quick validation flow

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

Keep volume moderate for S3B and S4B.
