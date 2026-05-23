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

### Passive CLI reports and planning commands

The passive CLI exposes the current machine target surface, passive 12-pad machine matrix, local saved-kit snapshot intelligence, style-planning reports, reference performance arcs, and live rehearsal packets without opening a MIDI port:

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
python -m rytm_randomizer.cli rytm-style-kit-readiness-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" jose_core_techno --limit 16   # passive per-kit Rytm style-readiness sweep
python -m rytm_randomizer.cli rytm-style-kit-readiness-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" jose_core_techno --json   # machine-readable Rytm kit readiness for future GUI/analyzer use
python -m rytm_randomizer.cli analog-four-style-snapshot-routing-report "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" industrial_dark --slot 0 --discovery 50   # passive balanced Analog Four style routing
python -m rytm_randomizer.cli analog-four-style-snapshot-routing-report "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" industrial_dark --discovery 95 --json   # machine-readable Analog Four wild-discovery routing
python -m rytm_randomizer.cli analog-four-style-mutation-intent-report "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" birmingham_pressure --slot 0 --discovery 45   # passive Analog Four track/zone intent
python -m rytm_randomizer.cli analog-four-style-mutation-intent-report "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" birmingham_pressure --discovery 95 --json   # machine-readable Analog Four style mutation intent
python -m rytm_randomizer.cli analog-four-style-mutation-mock-preview-report "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" jose_core_techno --slot 0 --discovery 45 --events --limit 24   # passive Analog Four style mock CC rows when offsets are promoted
python -m rytm_randomizer.cli analog-four-style-mutation-mock-preview-report "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" jose_core_techno --json   # machine-readable Analog Four mock-preview readiness for future GUI/analyzer use
python -m rytm_randomizer.cli analog-four-kit-catalog-report "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --limit 16   # passive Analog Four decoded kit catalog
python -m rytm_randomizer.cli analog-four-kit-catalog-report "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --json   # machine-readable Analog Four kit catalog for future GUI/analyzer use
python -m rytm_randomizer.cli analog-four-style-kit-readiness-report "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" jose_core_techno --limit 16   # passive per-kit Analog Four style-readiness sweep
python -m rytm_randomizer.cli dual-machine-style-kit-readiness-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" jose_core_techno --limit 16   # passive ranked Rytm+A4 kit-pair readiness sweep
python -m rytm_randomizer.cli dual-machine-style-kit-readiness-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" jose_core_techno --json   # machine-readable rig kit readiness for future GUI/analyzer use
python -m rytm_randomizer.cli dual-machine-style-kit-selection-report jose_core_techno --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --limit 8   # passive best live kit selections across both machines
python -m rytm_randomizer.cli dual-machine-style-kit-selection-report jose_core_techno --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --scope rytm-only --json   # mutate/select Rytm snapshot only and leave A4 unchanged
python -m rytm_randomizer.cli dual-machine-style-selection-mock-preview-report jose_core_techno --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --events --limit 24   # passive best-selection mock preview without manually copying slots
python -m rytm_randomizer.cli dual-machine-style-live-audition-report jose_core_techno birmingham_pressure warehouse_peak --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --events --limit 8   # passive live audition set across multiple style targets
python -m rytm_randomizer.cli dual-machine-style-performance-set-plan-report jose_core_techno birmingham_pressure warehouse_peak --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --total-minutes 300 --discovery-start 35 --discovery-end 75 --events --limit 8   # passive timed performance set plan for a long-form live arc
python -m rytm_randomizer.cli style-performance-arc-report   # list curated reference arcs for long-form live planning
python -m rytm_randomizer.cli inspect-style-performance-arc jose_warehouse_five_hour   # inspect Jose's Jeff Mills / Oscar Mulero / Stigmata / Birmingham arc
python -m rytm_randomizer.cli style-performance-arc-set-plan-report jose_warehouse_five_hour --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --events --limit 8   # expand a reference arc into the timed dual-machine performance set planner
python -m rytm_randomizer.cli style-performance-arc-readiness-report --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --limit 8   # rank all reference arcs against saved kit banks for the best live audition starting point
python -m rytm_randomizer.cli style-performance-arc-audition-packet-report --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --events --limit 8   # pick the best-ready reference arc and embed its timed set-plan preview
python -m rytm_randomizer.cli style-performance-arc-rehearsal-manifest-report --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --events --limit 8   # turn the best-ready reference arc into a preflight checklist and segment runbook
python -m rytm_randomizer.cli style-performance-arc-live-session-packet-report --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --events --limit 8   # package the chosen reference arc into a launch checklist, passive commands, and live segment cards
python -m rytm_randomizer.cli style-performance-arc-live-render-bundle-report --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --events --limit 8   # preview segment-level mock render rows and A4 deferred rows for the selected live arc
python -m rytm_randomizer.cli style-performance-arc-live-cue-sheet-report --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --events --limit 8   # turn the live render bundle into a live cue sheet with risk labels, hands-on moves, and recovery cues
python -m rytm_randomizer.cli style-performance-arc-reference-match-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --events --limit 8   # reference-match nonblank text/audio/library influence evidence to a curated performance arc, cue sheet, passive snapshot preview, and stage packet
python -m rytm_randomizer.cli style-performance-arc-live-runbook-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --events --limit 8   # live runbook that turns a selected arc/reference into a launch brief, stage packet, timeline cards, and recovery cues
python -m rytm_randomizer.cli style-performance-arc-stage-routing-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --events --limit 8   # stage routing report with cue-by-cue route cards, saved-kit slots/fingerprints, mock/deferred rows, and live rescue sequence
python -m rytm_randomizer.cli style-performance-arc-stage-rehearsal-state-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --events --limit 8   # stage rehearsal state with go/rehearse/do-not-arm cue states, Rytm/A4 machine states, and recovery prompts
python -m rytm_randomizer.cli style-performance-arc-live-set-cockpit-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --events --limit 8   # one-screen live set cockpit with launch controls, machine panels, cue cards, recovery controls, and go/rehearse/do-not-arm state
python -m rytm_randomizer.cli style-performance-arc-live-show-export-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --events --limit 8   # live show export packet with deterministic export id, machine handoff manifest, cue launch script, recovery script, and passive show handoff JSON
python -m rytm_randomizer.cli style-performance-arc-live-transition-timeline-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --events --limit 8   # live transition timeline with prep windows, transition cards, launch/hold/recovery prompts, machine handoffs, and passive replay commands
python -m rytm_randomizer.cli style-performance-arc-live-command-deck-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --cue 1 --lookahead 2 --events --limit 8   # live command deck with current-cue command cards, prep/launch/hold/recovery actions, machine handoffs, and passive replay commands
python -m rytm_randomizer.cli style-performance-arc-live-state-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --cue 1 --lookahead 2 --events --limit 8   # GUI-ready live state packet with now/next cues, machine panels, action bar, warning stack, recovery stack, and passive replay commands
python -m rytm_randomizer.cli style-performance-arc-live-readiness-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --cue 1 --lookahead 2   # GUI/audio-analyzer readiness gates, launch mode, machine panels, analyzer handoff, and operator next actions
python -m rytm_randomizer.cli style-performance-arc-live-control-surface-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --cue 1 --lookahead 2   # GUI/audio-analyzer control surface with header tiles, transport controls, cue cards, machine cards, analyzer cards, decisions, recovery, and passive replay commands
python -m rytm_randomizer.cli style-performance-arc-live-analyzer-handoff-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --cue 1 --lookahead 2 --matches 3   # analyzer handoff with FeatureReport meters, top influence matches, control-surface sync cards, capture prompts, and passive replay commands
python -m rytm_randomizer.cli style-performance-arc-live-analyzer-targets-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --cue 1 --lookahead 2 --matches 3   # analyzer target packet with rehearsal target bands, cue checkpoints, calibration steps, warning thresholds, and future live analyzer comparison JSON
python -m rytm_randomizer.cli style-performance-arc-live-gui-analyzer-readiness-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --cue 1 --lookahead 2 --matches 3   # GUI/audio-analyzer readiness bundle with panel manifest, stream wiring, operator workflow, blocked active actions, and passive replay commands
python -m rytm_randomizer.cli style-performance-arc-live-gui-rehearsal-session-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --cue 1 --lookahead 2 --matches 3 --takes 2   # GUI rehearsal session packet with task cards, listen-only rehearsal take cards, operator checklist, blocked active actions, and passive replay commands
python -m rytm_randomizer.cli style-performance-arc-live-gui-capture-queue-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --cue 1 --lookahead 2 --matches 3 --takes 2 --capture-prefix warehouse   # GUI/audio analyzer capture queue with capture slots, suggested filenames, analyzer job cards, operator checklist, blocked active actions, and passive replay commands
python -m rytm_randomizer.cli style-performance-arc-live-gui-capture-review-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --capture-description "captured warehouse take with tight low end and building pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --cue 1 --lookahead 2 --matches 3 --takes 2 --slot capture-001 --capture-prefix warehouse   # GUI/audio analyzer capture review with go/repeat/hold decisions, metric drift notes, hold reasons, blocked active actions, and passive replay commands
python -m rytm_randomizer.cli style-performance-arc-live-gui-sidecar-session-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --capture-description "captured warehouse take with tight low end and building pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --cue 1 --lookahead 2 --matches 3 --takes 2 --slot capture-001 --capture-prefix warehouse --sidecar-label "Warehouse sidecar"   # sidecar-ready GUI state with panels, analyzer rows, capture decisions, disabled active controls, blocked actions, and passive replay commands
python -m rytm_randomizer.cli style-performance-arc-live-gui-screen-contract-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --capture-description "captured warehouse take with tight low end and building pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --cue 1 --lookahead 2 --matches 3 --takes 2 --slot capture-001 --capture-prefix warehouse --sidecar-label "Warehouse sidecar" --screen-label "Warehouse screen"   # GUI screen contract with ordered regions, component state, table rows, disabled interaction controls, blocked actions, and passive replay commands
python -m rytm_randomizer.cli style-performance-arc-live-gui-render-tree-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --capture-description "captured warehouse take with tight low end and building pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --cue 1 --lookahead 2 --matches 3 --takes 2 --slot capture-001 --capture-prefix warehouse --sidecar-label "Warehouse sidecar" --screen-label "Warehouse screen" --render-target desktop-sidecar --density standard   # GUI render tree with deterministic root/region/component tree, source bindings, disabled controls, blocked actions, and passive replay commands
python -m rytm_randomizer.cli style-performance-arc-live-gui-analyzer-overlay-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --capture-description "captured warehouse take with tight low end and building pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --cue 1 --lookahead 2 --matches 3 --takes 2 --slot capture-001 --capture-prefix warehouse --sidecar-label "Warehouse sidecar" --screen-label "Warehouse screen" --render-target desktop-sidecar --density standard --overlay-label "Warehouse overlay"   # GUI analyzer overlay with meter widgets, threshold markers, selected capture badge, node annotations, blocked actions, and passive replay commands
python -m rytm_randomizer.cli style-performance-arc-live-gui-analyzer-frame-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --capture-description "captured warehouse take with tight low end and building pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --cue 1 --lookahead 2 --matches 3 --takes 2 --slot capture-001 --capture-prefix warehouse --sidecar-label "Warehouse sidecar" --screen-label "Warehouse screen" --render-target desktop-sidecar --density standard --overlay-label "Warehouse overlay" --frame-label "Warehouse frame"   # GUI analyzer frame with ordered frame events, visual assertions, blocked actions, and passive replay commands
python -m rytm_randomizer.cli style-performance-arc-live-gui-interaction-script-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --capture-description "captured warehouse take with tight low end and building pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --cue 1 --lookahead 2 --matches 3 --takes 2 --slot capture-001 --capture-prefix warehouse --sidecar-label "Warehouse sidecar" --screen-label "Warehouse screen" --render-target desktop-sidecar --density standard --overlay-label "Warehouse overlay" --frame-label "Warehouse frame" --interaction-label "Warehouse interactions"   # GUI interaction script with ordered interaction steps, control bindings, disabled hardware locks, blocked actions, and passive replay commands
python -m rytm_randomizer.cli style-performance-arc-live-gui-action-reducer-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --capture-description "captured warehouse take with tight low end and building pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --cue 1 --lookahead 2 --matches 3 --takes 2 --slot capture-001 --capture-prefix warehouse --sidecar-label "Warehouse sidecar" --screen-label "Warehouse screen" --render-target desktop-sidecar --density standard --overlay-label "Warehouse overlay" --frame-label "Warehouse frame" --interaction-label "Warehouse interactions" --reducer-label "Warehouse reducer"   # GUI action reducer with deterministic control transition decisions, disabled hardware locks, blocked actions, and passive replay commands
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

The style profiles are passive sound-design intent, not artist cloning. They name reusable underground-techno aesthetics such as Detroit minimal, hardgroove, Birmingham pressure, industrial dark, deep dark hypnosis, warehouse peak, and Jose Core Techno so future snapshot and audio-analyzer work can choose scenes, machine tendencies, and parameter emphasis from a stable vocabulary before any hardware message is sent. The Jose Core Techno profile captures the shared planning language for Jeff Mills / Oscar Mulero hypnosis, Glenn Wilson / Stigmata pressure, Regis / Surgeon industrial edge, and hard-loop warehouse drive. The performance-arc reports now climb from catalog, readiness, audition packet, rehearsal manifest, live session packet, and live render bundle into a live cue sheet and live runbook: passive operator reports that give launch/checklist context, segment-level mock render rows, A4 deferred rows, risk labels, hands-on moves, recovery cues, replayable passive commands, and JSON for future GUI/audio-analyzer rehearsal workflows. The stage routing report turns that runbook into show-facing route cards: each cue lists saved-kit slots, kit fingerprints, planned pads/tracks, Rytm mock row counts, A4 deferred/candidate rows, blockers, and the rescue sequence without opening ports or sending MIDI. The stage rehearsal state report wraps those route cards into go/rehearse/do-not-arm cue states, aggregate Rytm/A4 machine states, rehearsal steps, operator prompts, and capped event previews so a performer can know what is ready, what needs soundcheck, and what stays blocked before arming. The live set cockpit report sits on top as the show-facing dashboard: launch controls, machine panels, cue cockpit cards, recovery controls, next-best-action text, and deterministic JSON in one passive packet. The live show export report turns that cockpit into a passive show handoff with a deterministic export id, machine handoff manifest, cue launch script, recovery script, replayable passive commands, and JSON for future GUI/live-performance routing without writing files. The live transition timeline report consumes that export and lays out cue-to-cue prep windows, transition cards, launch/hold/recovery prompts, machine handoff summaries, and passive replay commands for GUI/operator rehearsal. The live command deck consumes the transition timeline and condenses it into current-cue command cards for cue prep, launch, hold, recovery, machine handoff checks, lookahead, and passive replay. The live state packet consumes that command deck and normalizes it into a GUI-ready current screen state: now/next cues, Rytm/A4 machine panels, action bar, warning stack, recovery stack, and replayable passive commands. The live readiness report consumes that state packet and adds GUI/audio-analyzer readiness gates, launch mode, machine-panel rows, analyzer handoff text, operator next actions, and replayable passive commands so the future GUI knows whether to perform, rehearse, or hold without touching hardware. The live control surface turns readiness into operator controls, current/next cue cards, machine cards, analyzer cards, decision rows, recovery controls, and replayable passive commands. The live analyzer handoff report pairs that control surface with reference-match FeatureReport meters, top influence matches, control-surface sync cards, next-cue sync cards, capture prompts, deterministic JSON, and replayable passive commands so future audio-analysis panels can compare measured evidence to the current live plan without opening ports or sending MIDI. The live analyzer target packet turns that handoff into rehearsal target bands, cue checkpoints, calibration steps, warning thresholds, deterministic JSON, and replayable passive commands for future live analyzer comparison without opening ports or sending MIDI. The live GUI/audio-analyzer readiness bundle turns that target packet into a panel manifest, analyzer stream wiring, operator workflow, blocked active actions, deterministic JSON, and replayable passive commands so the future desktop surface can rehearse the whole compare workflow without opening ports or sending MIDI. The live GUI rehearsal session packet wraps that readiness bundle into session task cards, listen-only rehearsal take cards, operator checklists, blocked active actions, deterministic JSON, and replayable passive commands so a future GUI can guide repeated cue captures without opening ports or sending MIDI. The live GUI/audio analyzer capture queue turns that session into deterministic capture slots, suggested capture filenames, analyzer job cards, operator capture checklists, blocked active actions, deterministic JSON, and replayable passive commands so a future GUI can queue repeated listen-only rehearsal takes without writing files, opening ports, or sending MIDI. The live GUI/audio analyzer capture review consumes that queue plus captured FeatureReport evidence and emits deterministic go/repeat/hold decisions, metric drift notes, hold reasons, deterministic JSON, and replayable passive commands so the future GUI can decide whether a rehearsal take is close enough without recording, opening ports, or sending MIDI. The reference-match report now adds a reference-selected snapshot preview and stage packet when saved Rytm/A4 kit banks are supplied, flattening the selected arc into readiness, mock/deferred totals, planned Rytm pads, planned Analog Four tracks, kit names, compact stage cards, and passive operator action before any MIDI send is possible. The Rytm mutation-intent report maps ready pads to safe profile parameters with style bias/direction metadata, the Rytm render-plan report narrows those rows into deterministic target-value windows, and the Analog Four mutation-intent/mock-preview reports map tracks to favored sound-design zones with the same style pressure while clearly blocking decoded SysEx rows until A4 offsets are promoted.

The live GUI sidecar session report composes the capture review into one sidecar-ready GUI state. It includes overview/current-cue/machine/analyzer/capture/safety panels, analyzer rows, capture decisions, disabled active controls, blocked actions, deterministic JSON, and passive replay commands.

The live GUI screen contract report composes that sidecar state into the deterministic screen model the future desktop surface can render. It includes ordered regions, component state, analyzer/capture table rows, disabled interaction controls, blocked actions, deterministic JSON, and passive replay commands without launching a GUI, writing files, opening ports, or sending MIDI.

The live GUI render tree report composes the screen contract into the deterministic root/region/component tree a future desktop surface or test harness can consume. It includes node parent/child relationships, source bindings, disabled controls, blocked actions, deterministic JSON, and passive replay commands without launching a GUI, writing files, opening ports, or sending MIDI.

The live GUI analyzer overlay report composes the render tree into audio-analyzer-facing GUI metadata. It includes meter widgets, threshold markers, selected capture badges, render-node annotations, blocked actions, deterministic JSON, and passive replay commands without launching a GUI, recording audio, writing files, opening ports, or sending MIDI.

The live GUI analyzer frame report composes that overlay into deterministic GUI test-harness metadata. It includes ordered frame events, visual assertions, blocked actions, deterministic JSON, and passive replay commands without rendering a GUI frame, recording audio, writing files, opening ports, or sending MIDI.

The live GUI interaction script report composes that analyzer frame into deterministic GUI operator metadata. It includes ordered interaction steps, control bindings, disabled hardware locks, blocked actions, deterministic JSON, and passive replay commands without launching a GUI, dispatching GUI events, writing files, opening ports, or sending MIDI.

The live GUI action reducer report composes that interaction script into deterministic GUI controller metadata. It includes control transition decisions, blocked hardware/action locks, deterministic JSON, and passive replay commands without launching a GUI, dispatching GUI events, writing files, opening ports, or sending MIDI.

Live set card for the current validated Rytm performance layer:

```text
Preflight: run the passive reports first, especially style-performance-arc-live-gui-action-reducer-report after style-performance-arc-live-gui-interaction-script-report, style-performance-arc-live-gui-analyzer-frame-report, style-performance-arc-live-gui-analyzer-overlay-report, style-performance-arc-live-gui-render-tree-report, style-performance-arc-live-gui-screen-contract-report, style-performance-arc-live-gui-sidecar-session-report, style-performance-arc-live-gui-capture-review-report, style-performance-arc-live-gui-capture-queue-report, style-performance-arc-live-gui-rehearsal-session-report, style-performance-arc-live-gui-analyzer-readiness-report, style-performance-arc-live-analyzer-targets-report, style-performance-arc-live-analyzer-handoff-report, style-performance-arc-live-control-surface-report, style-performance-arc-live-readiness-report, style-performance-arc-live-state-report, style-performance-arc-live-command-deck-report, style-performance-arc-live-transition-timeline-report, style-performance-arc-live-show-export-report, style-performance-arc-live-set-cockpit-report, style-performance-arc-stage-routing-report, and style-performance-arc-stage-rehearsal-state-report.
Armed path: rytm-randomizer --arm -> choose the Rytm output -> target Pad 1 -> profile 1.
Performance flow: SCN -> GM -> S1A -> S3A -> S3B -> S4B -> S5 -> Z -> Q.
Rescue sequence: S5 -> Z -> Q.
Keep volume moderate before S3B and S4B.
```

Style target vectors turn those profiles into bounded 0-100 planning axes such as low-end weight, transient density, darkness, metallicity, grit, motion, hypnosis, and warehouse intensity. They are passive numeric intent only: they do not choose machines, mutate snapshots, send MIDI, or touch hardware.

Style performance arcs bundle those profiles into named live-set narratives. For example, `jose_warehouse_five_hour` expands Jeff Mills, Oscar Mulero, Stigmata/Birmingham, Regis/Surgeon, Glenn Wilson/Nightshift, Thomas Krome, and early Kay D Smith references into the existing dual-machine performance set planner with a default five-hour duration and reference-to-discovery ramp. These arcs are still passive metadata and plan expansion only; they do not clone artists, open ports, or send MIDI.

The style performance arc readiness report ranks one or all curated arcs against the saved Rytm and Analog Four kit banks before a live audition. It summarizes ready, partial, and blocked arc counts, averages selection scores across each arc's timed segments, and recommends whether the operator should audition, refine, or add better-matching kit material. Like the other style reports, it is file-only planning: no MIDI port is opened and no hardware message is sent.

The style performance arc audition packet is the one-command live prep view: it evaluates the same readiness matrix, selects the highest-ranked arc, and embeds that arc's timed set-plan preview with optional mock event rows. Use it before a studio or show rehearsal when you want the software to say "start here" from the saved Rytm/A4 kit banks while still staying passive and hardware-safe.

The style-routing reports also accept `--discovery N` where `N` is 0-100. If omitted, the live-safe default is 45. Low values stay close to the captured kit snapshot, balanced values widen zone movement, and high values expose broader legal discovery candidates while still obeying Rytm pad compatibility and Analog Four readiness gates.

The Rytm style snapshot routing report is the first bridge from style intent to captured-kit planning. It reads a local Rytm kit dump, applies one style target vector, and reports favored mutation zones, route-ready pads, blocked pads, and legal machine candidates. It remains metadata-only: no mutation values are rendered, no MIDI port is opened, and no hardware message is sent.

The Rytm style mutation intent report takes that one passive step closer to the live tool: for each route-ready pad, it maps the chosen style and discovery band to safe profile parameters such as grit, body, amp, filter, LFO, and morph targets, then annotates each row with a style bias and direction such as higher, lower, shorter, longer, or center. It still renders no CC values and sends no MIDI; it is the machine-readable contract the future snapshot mutation renderer can consume.

The Rytm style mutation render-plan report turns those intent rows into deterministic target values and bounded value windows inside each profile's safe range. It is still passive metadata only: it does not resolve MIDI CC messages, open a MIDI port, send hardware messages, or claim to decode the current per-parameter values from the kit dump. It gives the future live renderer a tested value-envelope contract for style-aware snapshot mutation.

The Rytm style mutation mock-preview report takes the next passive step: it resolves render-ready style rows into mock CC event rows using the Rytm message renderer, while still opening no MIDI port and sending no hardware messages. It prints pad, profile, zone, parameter, channel, CC, value, window, depth, and target direction so the future GUI/live engine can show exactly what would move before an armed path exists.

The Analog Four style snapshot routing report mirrors that bridge for the A4 side of the rig. It reads a local Analog Four kit dump, applies one style target vector, and reports track-level favored zones while the low-level A4 parameter offsets remain candidate-only. It is still passive metadata only: no mutation values are rendered, no MIDI port is opened, and no hardware message is sent.

The Analog Four style mutation mock-preview report can now intake real saved-kit SysEx frames from `.syx` dumps, unpack the shared Elektron payload, and display the decoded kit name while still keeping A4 offsets candidate-only. Once offsets are promoted, the same path turns A4 style-intent rows into mock CC rows for CC-safe zones such as oscillator level, filter frequency, envelope decay, modulation speed, and send level. NRPN-only drive rows are listed as deferred instead of pretending they can be rendered as CC. It remains passive and opens no MIDI port.

The Analog Four kit catalog report is the operator-friendly intake view for full C6 kit dumps. It lists decoded kit slots and names, distinguishes saved-kit from candidate layouts, shows stable payload fingerprints plus raw/unpacked byte counts, and marks every decoded kit as candidate-only until offset promotion is validated. Use `--limit N` for a quick stage-readiness scan or `--json` for future GUI/audio-analyzer consumers.

The Rytm style kit-readiness report layers style intent over every decoded Rytm kit in a dump. It runs the existing passive style/mock preview readiness path per kit, carries a stable payload fingerprint for exact kit-state comparison, and reports preview-ready versus blocked kits plus planned pads/mock-row counts before any armed path exists.

The Analog Four style kit-readiness report layers style intent over that catalog. It scans every decoded kit in an A4 dump for a style target such as `jose_core_techno`, reports per-kit preview readiness, carries the same payload fingerprint for kit-state comparison, and explains which kits remain blocked by candidate-only offsets before any real mutation path is enabled.

The dual-machine style kit-readiness report combines the Rytm and Analog Four sweeps into a ranked rig-level pairing table. It reads both kit banks, applies the same style target and discovery amount, scores every Rytm+A4 pairing as ready, partial, or blocked, and exposes fingerprints for both sides so future GUI/audio-analyzer/live workflows can choose a promising rig state before sending MIDI.

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
