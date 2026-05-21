# RytmRandomizer

RytmRandomizer is a Python tool for Elektron hardware: the Analog Rytm MK2 drum machine and the Analog Four MK2 synthesizer. The Analog Rytm path is the mature live-performance randomizer, with MIDI parameter mutation, a four-pad scene system (Rolling / Deeper / Intense / Wild, each with A/B depth variants), and safety guardrails so you do not accidentally send MIDI to hardware. The Analog Four path is now registered behind the same cross-machine `Device` Protocol, with candidate/manifest-gated planning while saved-kit offsets are promoted.

Each machine is exposed as a registered `Device`; see `docs/ARCHITECTURE.md` section 6.1. You can inspect the dual-machine target surface with `rytm`, `a4`, or `both`. The interactive runtime is owned end-to-end by the modular package (`rytm_randomizer.app` -> `rytm_randomizer.shell`). The original V1.34 monolith (`rytm_hybrid_randomizer_v134.py`) was retired in favor of the package; its reference behavior is captured as JSON goldens under `tests/fixtures/v134_parity/` and asserted by the parity test files.

---

## End-user setup

This path is for someone who just wants to run RytmRandomizer against their Analog Rytm MK2, or inspect the safe dual-machine target surface that now includes Analog Four MK2.

### 1. Requirements

- An Analog Rytm MK2 connected over USB MIDI for the current interactive runtime
- Optional: an Analog Four MK2 for the candidate dual-machine path
- One of: a native installer (preferred, see below) **or** Python >= 3.9 + `pip` (Python 3.11 is the tested contributor/runtime matrix)

### 2. Install — option A: native installer (recommended)

> **Coming soon.** The native installers (Windows `.msi`, macOS `.pkg`, Linux AppImage / `.deb`) are wired up via [BeeWare briefcase](https://briefcase.beeware.org/) but the **first signed release has not shipped yet**. The build matrix lives in `.github/workflows/installers.yml`; release artifacts will be attached to the GitHub Release page once code-signing is provisioned. Until then, use option B.

When available, the install flow is:

1. Visit the [GitHub Releases](https://github.com/buzzijose-hub/RytmRandomizer/releases) page.
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
git clone https://github.com/buzzijose-hub/RytmRandomizer.git
cd RytmRandomizer
pip install -e ".[dev]"
```

### 2. Run the test suite

```bash
pytest
```

The full suite is roughly 2,400 tests and usually runs in about 30 seconds on a multi-core machine. `pyproject.toml` sets `-n auto`, so `pytest-xdist` parallelizes across CPU cores. Do not pass `-o addopts=''` for normal runs; it disables xdist and makes the suite much slower. Every commit must keep the suite green. The pytest config in `pyproject.toml` enables:

- `pytest-xdist` (`-n auto`) for parallel execution.
- `pytest-timeout` (default 180s per test) so no test can silently hang the suite.
- `--durations=20` after every run so per-test timings are always visible.
- `pytest-sugar` for a live progress bar; pass `-p no:sugar -v` for plain output.

Common loops if `just` is installed: `just test` for the full suite, `just fast` for the fast subset, `just lint` for ruff/black/isort, and `just check` for the pre-PR gate.

### 3. Repository map

| Path | What it is |
|------|------------|
| `rytm_randomizer/` | The product package. `app.py` is the entry point; `cli.py` is the passive CLI; `shell.py` is the interactive command loop. |
| `rytm_randomizer/devices/` | Cross-machine `Device` Protocol + registry. `analog_rytm.py` and `analog_four.py` are the registered devices; `strategies/` holds each device's snapshot decoder, mutation planner, and message renderer. |
| `rytm_randomizer/senders/` | Generic guarded and hardware send paths that consume any registered `Device`. |
| `rytm_randomizer/dual_machine/` | Dual-machine target reporting and alias resolution for `rytm`, `a4`, and `both`; it fans out through `devices.all_devices()`. |
| `rytm_randomizer/engines/`, `group_runner.py`, `scene_runner.py` | The V1.34 Analog Rytm orchestration layer. |
| `rytm_randomizer/data/`, `state/` | Canonical fact tables and runtime state. |
| `rytm_randomizer/guardrails/`, `observability/`, `snapshot/`, `reports/`, `behavior/`, `style_analysis/` | Safety/policy, logging/metrics, SysEx envelope helpers, passive reports, behavior evaluators, and style-analysis support. |
| `tests/fixtures/v134_parity/` | Frozen V1.34 reference behavior as JSON goldens, one per parity request. The retired `rytm_hybrid_randomizer_v134.py` monolith used to be the live byte-parity baseline; the goldens are now the authoritative source. |
| `tests/` | Roughly 2,400 tests across 108 test files, including `tests/architecture/` mechanical guardrails and parity tests against the V1.34 JSON goldens. |
| `docs/` | Project documentation, status, process notes, `ARCHITECTURE.md`, `ARCHITECTURE_DIAGRAMS.md`, and `PLAN_REQUIREMENTS.md`. |
| `scripts/` | Cross-platform Python tooling such as closeout and coverage checks. `Scripts/` is the legacy PowerShell equivalent. |
| `tooling/` | Developer utilities (hardware-capture scripts). Not part of the core product. |

### 4. Contributing

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for the workflow (planning, TDD, code review) and the parity rules around the V1.34 reference. The architecture standard is `docs/ARCHITECTURE.md`; `docs/ARCHITECTURE_DIAGRAMS.md` has the visual map. Agentic contributors should also read `AGENTS.md`, and Codex work should read `docs/CODEX_CONTRIBUTING.md`.

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
- Pads 5-12 have a passive machine matrix report; armed 12-pad runtime mutation remains gated until the follow-up runtime slice.
- Main-prompt `1`, `2`, and `3` remain guarded and send no MIDI.
- Four-pad scene/global commands auto-load anchors if needed.
- Analog Four sends are candidate/manifest-gated and require an explicit `--arm` path plus a ready plan; the passive default touches no hardware.

### Dual-machine target commands

The passive CLI exposes the current machine target surface, passive 12-pad machine matrix, and local Rytm snapshot intelligence without opening a MIDI port:

```bash
python -m rytm_randomizer.cli dual-machine-target-report rytm   # Analog Rytm only
python -m rytm_randomizer.cli dual-machine-target-report a4     # Analog Four only
python -m rytm_randomizer.cli dual-machine-target-report both   # both registered devices
python -m rytm_randomizer.cli rytm-12-pad-machine-matrix-report   # passive Rytm 12-pad machine compatibility matrix
python -m rytm_randomizer.cli rytm-snapshot-pad-compatibility-report   # passive snapshot readiness per Rytm pad
python -m rytm_randomizer.cli rytm-snapshot-intelligence-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --list   # list supported Rytm kit snapshots in a SysEx dump
python -m rytm_randomizer.cli rytm-snapshot-intelligence-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --slot 7   # passive intelligence for one supported Rytm kit snapshot
python -m rytm_randomizer.cli rytm-snapshot-mutation-preview-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --slot 7 --depth 2   # passive snapshot mutation preview; mock-only, no MIDI send
python -m rytm_randomizer.cli rytm-snapshot-mutation-preview-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --slot 7 --depth 2 --events --limit 24   # include capped mock CC event rows
python -m rytm_randomizer.cli rytm-style-snapshot-routing-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" birmingham_pressure --slot 7 --discovery 10   # passive reference-close Rytm style routing
python -m rytm_randomizer.cli rytm-style-snapshot-routing-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" birmingham_pressure --discovery 95 --json   # machine-readable wild-discovery Rytm style routing
python -m rytm_randomizer.cli rytm-style-mutation-intent-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" birmingham_pressure --slot 7 --discovery 45   # passive Rytm style zone/parameter intent
python -m rytm_randomizer.cli rytm-style-mutation-intent-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" birmingham_pressure --discovery 95 --json   # machine-readable Rytm style mutation intent
python -m rytm_randomizer.cli rytm-style-mutation-render-plan-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" birmingham_pressure --slot 7 --discovery 45   # passive Rytm style target-value windows
python -m rytm_randomizer.cli rytm-style-mutation-render-plan-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" birmingham_pressure --discovery 95 --json   # machine-readable Rytm style render-plan metadata
python -m rytm_randomizer.cli rytm-style-mutation-mock-preview-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" jose_core_techno --slot 7 --discovery 45 --events --limit 24   # passive Rytm style mock CC rows; no MIDI send
python -m rytm_randomizer.cli rytm-style-mutation-mock-preview-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" jose_core_techno --json   # machine-readable Rytm style mock preview for future GUI/analyzer use
python -m rytm_randomizer.cli analog-four-style-snapshot-routing-report "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" industrial_dark --slot 0 --discovery 50   # passive balanced Analog Four style routing
python -m rytm_randomizer.cli analog-four-style-snapshot-routing-report "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" industrial_dark --discovery 95 --json   # machine-readable Analog Four wild-discovery routing
python -m rytm_randomizer.cli analog-four-style-mutation-intent-report "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" birmingham_pressure --slot 0 --discovery 45   # passive Analog Four track/zone intent
python -m rytm_randomizer.cli analog-four-style-mutation-intent-report "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" birmingham_pressure --discovery 95 --json   # machine-readable Analog Four style mutation intent
python -m rytm_randomizer.cli analog-four-style-mutation-mock-preview-report "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" jose_core_techno --slot 0 --discovery 45 --events --limit 24   # passive Analog Four style mock CC rows when offsets are promoted
python -m rytm_randomizer.cli analog-four-style-mutation-mock-preview-report "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" jose_core_techno --json   # machine-readable Analog Four mock-preview readiness for future GUI/analyzer use
python -m rytm_randomizer.cli analog-four-kit-catalog-report "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --limit 16   # passive Analog Four decoded kit catalog
python -m rytm_randomizer.cli analog-four-kit-catalog-report "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --json   # machine-readable Analog Four kit catalog for future GUI/analyzer use
python -m rytm_randomizer.cli analog-four-style-kit-readiness-report "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" jose_core_techno --limit 16   # passive per-kit Analog Four style-readiness sweep
python -m rytm_randomizer.cli dual-machine-style-snapshot-routing-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" warehouse_peak --rytm-slot 7 --a4-slot 0 --discovery 45   # passive rig-level style routing
python -m rytm_randomizer.cli dual-machine-style-snapshot-routing-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" warehouse_peak --discovery 95 --json   # machine-readable rig style routing for future GUI/analyzer use
python -m rytm_randomizer.cli dual-machine-style-mutation-intent-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" birmingham_pressure --rytm-slot 7 --a4-slot 0 --discovery 45   # passive rig-level mutation intent
python -m rytm_randomizer.cli dual-machine-style-mutation-intent-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" birmingham_pressure --discovery 95 --json   # machine-readable rig mutation intent for future GUI/analyzer use
python -m rytm_randomizer.cli dual-machine-style-mutation-mock-preview-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" jose_core_techno --rytm-slot 7 --a4-slot 0 --discovery 45 --events --limit 24   # passive rig-level mock CC rows and A4 deferred rows
python -m rytm_randomizer.cli dual-machine-style-mutation-mock-preview-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" jose_core_techno --json   # machine-readable rig mock preview for future GUI/analyzer use
python -m rytm_randomizer.cli style-profile-report   # passive techno style profiles for later snapshot/audio-analysis routing
python -m rytm_randomizer.cli list-style-profiles   # list available style profiles
python -m rytm_randomizer.cli inspect-style-profile birmingham_pressure   # inspect one passive style profile
python -m rytm_randomizer.cli search-style-profiles hardgroove   # search style profiles by tag, summary, scene, or focus
python -m rytm_randomizer.cli style-target-report   # passive numeric style target vectors for future snapshot planning
python -m rytm_randomizer.cli inspect-style-target birmingham_pressure   # inspect one passive target vector
```

Aliases: `rytm-only` and `a4-only` are accepted. The reports are passive: they open no MIDI port and send no MIDI. The snapshot-pad compatibility report explains which legal Rytm pad/machine combinations are snapshot-mutable today and which remain selectable-only until the follow-up runtime slice. The snapshot intelligence report reads a local `.syx` file, scans framed C6-style dumps for supported Rytm kit snapshots, can list those slots, and prints decoded machine facts plus mutation readiness for the selected slot. The snapshot mutation preview report takes the selected snapshot slot one step further: it routes snapshot machine facts into the guarded mutation planner and renders the would-be mock message count/readiness without sending anything to hardware. Add `--events` to include capped mock CC event rows (`--limit 0` prints all rows) showing pad, profile, parameter, channel, CC, and value. The Analog Four path is candidate/manifest-gated; do not run armed Analog Four hardware sends until a readiness report says the plan is ready.

The style profiles are passive sound-design intent, not artist cloning. They name reusable underground-techno aesthetics such as Detroit minimal, hardgroove, Birmingham pressure, industrial dark, deep dark hypnosis, warehouse peak, and Jose Core Techno so future snapshot and audio-analyzer work can choose scenes, machine tendencies, and parameter emphasis from a stable vocabulary before any hardware message is sent. The Jose Core Techno profile captures the shared planning language for Jeff Mills / Oscar Mulero hypnosis, Glenn Wilson / Stigmata pressure, Regis / Surgeon industrial edge, and hard-loop warehouse drive. The Rytm mutation-intent report now maps ready pads to safe profile parameters with style bias/direction metadata, the Rytm render-plan report narrows those rows into deterministic target-value windows, and the Analog Four mutation-intent/mock-preview reports map tracks to favored sound-design zones with the same style pressure while clearly blocking decoded SysEx rows until A4 offsets are promoted.

Style target vectors turn those profiles into bounded 0-100 planning axes such as low-end weight, transient density, darkness, metallicity, grit, motion, hypnosis, and warehouse intensity. They are passive numeric intent only: they do not choose machines, mutate snapshots, send MIDI, or touch hardware.

The style-routing reports also accept `--discovery N` where `N` is 0-100. If omitted, the live-safe default is 45. Low values stay close to the captured kit snapshot, balanced values widen zone movement, and high values expose broader legal discovery candidates while still obeying Rytm pad compatibility and Analog Four readiness gates.

The Rytm style snapshot routing report is the first bridge from style intent to captured-kit planning. It reads a local Rytm kit dump, applies one style target vector, and reports favored mutation zones, route-ready pads, blocked pads, and legal machine candidates. It remains metadata-only: no mutation values are rendered, no MIDI port is opened, and no hardware message is sent.

The Rytm style mutation intent report takes that one passive step closer to the live tool: for each route-ready pad, it maps the chosen style and discovery band to safe profile parameters such as grit, body, amp, filter, LFO, and morph targets, then annotates each row with a style bias and direction such as higher, lower, shorter, longer, or center. It still renders no CC values and sends no MIDI; it is the machine-readable contract the future snapshot mutation renderer can consume.

The Rytm style mutation render-plan report turns those intent rows into deterministic target values and bounded value windows inside each profile's safe range. It is still passive metadata only: it does not resolve MIDI CC messages, open a MIDI port, send hardware messages, or claim to decode the current per-parameter values from the kit dump. It gives the future live renderer a tested value-envelope contract for style-aware snapshot mutation.

The Rytm style mutation mock-preview report takes the next passive step: it resolves render-ready style rows into mock CC event rows using the Rytm message renderer, while still opening no MIDI port and sending no hardware messages. It prints pad, profile, zone, parameter, channel, CC, value, window, depth, and target direction so the future GUI/live engine can show exactly what would move before an armed path exists.

The Analog Four style snapshot routing report mirrors that bridge for the A4 side of the rig. It reads a local Analog Four kit dump, applies one style target vector, and reports track-level favored zones while the low-level A4 parameter offsets remain candidate-only. It is still passive metadata only: no mutation values are rendered, no MIDI port is opened, and no hardware message is sent.

The Analog Four style mutation mock-preview report can now intake real saved-kit SysEx frames from `.syx` dumps, unpack the shared Elektron payload, and display the decoded kit name while still keeping A4 offsets candidate-only. Once offsets are promoted, the same path turns A4 style-intent rows into mock CC rows for CC-safe zones such as oscillator level, filter frequency, envelope decay, modulation speed, and send level. NRPN-only drive rows are listed as deferred instead of pretending they can be rendered as CC. It remains passive and opens no MIDI port.

The Analog Four kit catalog report is the operator-friendly intake view for full C6 kit dumps. It lists decoded kit slots and names, distinguishes saved-kit from candidate layouts, shows stable payload fingerprints plus raw/unpacked byte counts, and marks every decoded kit as candidate-only until offset promotion is validated. Use `--limit N` for a quick stage-readiness scan or `--json` for future GUI/audio-analyzer consumers.

The Analog Four style kit-readiness report layers style intent over that catalog. It scans every decoded kit in an A4 dump for a style target such as `jose_core_techno`, reports per-kit preview readiness, carries the same payload fingerprint for kit-state comparison, and explains which kits remain blocked by candidate-only offsets before any real mutation path is enabled.

The dual-machine style snapshot routing report sits above the two single-machine reports. It reads one Rytm kit dump and one Analog Four kit dump, applies the same style target to both, and summarizes whole-rig readiness so a future live workflow can decide whether the Rytm, the A4, or both machines can safely move toward the selected techno aesthetic.

The dual-machine style mutation mock-preview report combines those two passive mock-preview layers into one rig-level view. It reads one Rytm kit dump and one Analog Four kit dump, applies the same style target and discovery amount, totals rendered mock CC rows, lists A4 deferred/blocked rows, and can emit combined event rows with `--events` before any armed live path exists.

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
