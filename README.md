# RytmRandomizer

RytmRandomizer is a Python tool for the Elektron Analog Rytm MK2 hardware drum machine. It randomizes and mutates drum-synthesis parameters over MIDI, organized as a four-pad layout, with a layered "scene" system (Rolling / Deeper / Intense / Wild, each with A/B depth variants) and safety guardrails so you do not accidentally send MIDI to the hardware. You drive it from a small text prompt: pick a scene or command, and it sends the corresponding parameter changes to the Rytm.

As of Wave 4 / WS-O the interactive runtime is owned end-to-end by the modular package (`rytm_randomizer.app` -> `rytm_randomizer.shell`). The original V1.34 monolith (`rytm_hybrid_randomizer_v134.py`) was retired in favor of the package; its reference behavior is captured as JSON goldens under `tests/fixtures/v134_parity/` and asserted by the parity test files.

---

## End-user setup

This path is for someone who just wants to run RytmRandomizer against their Analog Rytm MK2.

### 1. Requirements

- An Analog Rytm MK2 connected over USB MIDI
- One of: a native installer (preferred, see below) **or** Python >= 3.9 + `pip`

### 2. Install — option A: native installer (recommended)

> **Coming soon.** The native installers (Windows `.msi`, macOS `.pkg`, Linux AppImage / `.deb`) are wired up via [BeeWare briefcase](https://briefcase.beeware.org/) but the **first signed release has not shipped yet**. The build matrix lives in `.github/workflows/installers.yml`; release artifacts will be attached to the GitHub Release page once code-signing is provisioned. Until then, use option B.

When available, the install flow is:

1. Visit the [GitHub Releases](https://github.com/misteredr/RytmRandomizer/releases) page.
2. Download the artifact for your OS:
   - Windows: `RytmRandomizer-<version>.msi`
   - macOS: `RytmRandomizer-<version>.pkg`
   - Linux: `RytmRandomizer-<version>.AppImage` or `.deb` / `.rpm`
3. Double-click to install. The installer drops a `rytm-randomizer` CLI binary on your PATH with its own bundled Python — no `pip`, no terminal experience needed.

### 2. Install — option B: `pip` (works today)

```bash
pip install rytm-randomizer
```

Or, from a local clone:

```bash
pip install -e .
```

### 3. Per-OS MIDI notes

- **Windows / macOS** — `python-rtmidi` ships prebuilt wheels, so `pip install` just works. The native installers bundle the wheel directly, so end users do not need a working compiler.
- **Linux** — if no wheel is available for your platform, `python-rtmidi` builds from source and you may need the ALSA development headers first: `sudo apt install libasound2-dev`. The AppImage / `.deb` carry the ALSA runtime so end users do not need the dev headers.

### 4. Launch

```bash
rytm-randomizer
```

The default landing mode is the **passive menu**: a read-only inspection / preview screen that opens no MIDI port and sends no MIDI. From there:

```bash
rytm-randomizer --dry-run   # full interactive logic against an in-memory mock
                            # sender. No hardware, no port opened. Safe to
                            # explore the command surface.

rytm-randomizer --arm       # open a real MIDI output port and drive the
                            # Analog Rytm. The interactive shell prompts you
                            # for a target pad, profile, then a command.
```

`--arm` and `--dry-run` are mutually exclusive: pick one, or neither for the passive menu.

---

## Developer setup

This path is for someone who wants to work on the code, run tests, or contribute.

### 1. Clone and install with dev dependencies

```bash
git clone https://github.com/<owner>/RytmRandomizer.git
cd RytmRandomizer
pip install -e ".[dev]"
```

### 2. Run the test suite

```bash
pytest
```

The full suite is ~1280 tests in roughly five to six minutes (pytest-xdist parallelizes the parity workers). Every commit must keep the suite green. The pytest config in `pyproject.toml` enables:

- `pytest-xdist` (`-n auto`) for parallel execution.
- `pytest-timeout` (default 180s per test) so no test can silently hang the suite.
- `--durations=20` after every run so per-test timings are always visible.
- `pytest-sugar` for a live progress bar; pass `-p no:sugar -v` for plain output.

### 3. Repository map

| Path | What it is |
|------|------------|
| `rytm_randomizer/` | The product package. `app.py` is the entry point; `shell.py` is the interactive command loop; `engines/`, `group_runner.py`, `scene_runner.py` are the orchestration layer; `data/` and `state/` are the canonical data + runtime state. |
| `tests/fixtures/v134_parity/` | Frozen V1.34 reference behavior as JSON goldens, one per parity request. The retired `rytm_hybrid_randomizer_v134.py` monolith used to be the live byte-parity baseline; the goldens are now the authoritative source. |
| `tests/` | The test suite (~50 test files). Includes parity tests that compare the extracted engines' output to the V1.34 JSON goldens. |
| `docs/` | Project documentation, status, and process notes. See `docs/STATUS.md` for the current wave state. |
| `Scripts/` | Helper scripts (e.g. closeout checks, quick status). |
| `tooling/` | Developer utilities (hardware-capture scripts). Not part of the core product. |

### 4. Contributing

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for the workflow (planning, TDD, code review) and the parity rules around the V1.34 reference. A more detailed architecture map will land in `docs/ARCHITECTURE.md` in a follow-up wave.

---

## Scenes and commands

The scene system below is the validated V1.34 layer. These tables are the canonical reference for what commands exist; `rytm_randomizer.shell` dispatches them.

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
- No Pads 5-12 expansion yet.
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
