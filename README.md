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

Analog Rytm curated style kits can render all 12 pads. Dry-run first:

```bash
python -m rytm_randomizer.app --dry-run --rytm-kit-style detroit-deep
```

Armed sends require a saved/disposable kit and an explicit confirmation flag:

```bash
python -m rytm_randomizer.app --arm --rytm-kit-style detroit-deep --confirm-rytm-kit-send
```

Current Rytm styles are `detroit-deep`, `deeper-rolling`, `hard-groove`,
`banging-warehouse`, `flow-shift`, `hypnotic-pressure`, and `mills-drive`.
They select legal machines across pads 1-12 and send manual-backed CC MSB
values; they do not use samples, performance macros, source level, track level,
or amp volume.

The all-12-pad interactive shell starts from those curated styles, then lets
you preview, send, undo, reset, and apply role-safe mutations across every pad:

```bash
python -m rytm_randomizer.app --dry-run --rytm-12-pad-shell
python -m rytm_randomizer.app --arm --rytm-12-pad-shell --confirm-rytm-12-pad-send
```

Inside the shell, use `load detroit-deep`, `preview`, `send`, `roll`, `deep`,
`grit`, `intense`, `warehouse`, `undo`, `reset`, and `q`. Kick filter-frequency
mutations are clamped to the sub-safe range learned during hardware testing.

The all-12-pad snapshot shell starts from a current-kit SysEx dump instead of a
curated style anchor, then gives you the old V1.34 performance command feel
across all 12 pads:

```bash
python -m rytm_randomizer.app --arm --rytm-live-snapshot-shell --confirm-rytm-snapshot-shell-send
python -m rytm_randomizer.app --dry-run --rytm-snapshot-shell captures/current-kit.syx
python -m rytm_randomizer.app --arm --rytm-snapshot-shell captures/current-kit.syx --confirm-rytm-snapshot-shell-send
```

The live command is the fresh-performance workflow: choose the Rytm input, send
`GLOBAL SETTINGS > SYSEX DUMP > SYSEX SEND > KIT` from the hardware, then the
software decodes that received kit and opens the mutation shell. The file-based
commands remain useful for dry-runs and replaying a saved capture. While an
armed live snapshot shell is running, `kit` or `resnapshot` waits for one more
Rytm KIT SysEx dump from the same selected input, replaces the captured anchor,
clears the staged mutation, and keeps the current session guardrails.

Inside the shell, use `S1A`, `S3A`, `S3B`, `S4B`, `4`, `Y`, `V`, `N`, `Z`,
`U`, `preview`, `changes`, `send`, `go`, `again`, `next`, `kit`,
`resnapshot`, `mode`, `depth`, `lane`, `lock`, `unlock`, `pad`, `preset`,
`guards reset`, `status`, and `q`. `Y`, `V`, and `N` ask for depth (`micro`,
`groove`, or `strong`). `send` repeats the currently staged plan; type `go` to
make the next variation and send it in one step, or type the same mutation
command again, `again`, or `next` to stage the next variation before sending.

In live use, treat the shell as a second performer beside an OXI or another
sequencer. The OXI decides when notes, triggers, mutes, and pattern motion
happen; RytmRandomizer changes what the captured Rytm sounds become when those
events happen. `randomize` proposes a safe staged sound-design variation, `go`
generates and sends the next variation, `kit` captures a newly loaded Rytm kit
as the new anchor, and `Z` plus `send` returns the hardware to the captured
safe kit.

Session guardrails are live-only settings that reset when the shell exits:

```text
mode live
depth gentle
lane tune micro
lane noise normal
lane fx micro
lane filter normal
lane amp normal
lane lfo off
pad 1 gentle
pad 3 strong
lock 5
status
randomize
4
changes
send
go
preset live
preset kick-safe
preset all-gentle
preset studio
guards reset
fresh
kit
```

Global mutations respect each pad's session lane. In `live` mode, Pad 1 is
gentle by default, toms and hats are gentle, pads 2-4 and 11-12 are normal, and
per-pad overrides can intentionally push selected pads harder. Locked pads are
left out of armed `send` messages, and `status` separates active pad overrides
from inactive overrides parked behind locked pads. Session presets apply common
guardrail setups without persistence: `preset live` is live/gentle with no
locks, `preset kick-safe` locks Pad 1 while auditioning the rest of the kit,
`preset all-gentle` clears pad overrides and keeps the whole shell gentle, and
`preset studio` opens the wider studio/wild lane. `guards reset` clears locks
and overrides back to the default live/normal profile. Live/studio depth lanes
are total anchor-relative envelopes, so repeated `4` or `again` commands vary
the kit inside the selected lane instead of walking farther away from the
received snapshot. Pad 1 has an additional kick-foundation policy: its filter
page, LFO page, and AMP attack time are omitted from active sends, while Pad 1
source tuning parameters stay within plus or minus 3 of their captured-kit
values. Lane guardrails add a second permission layer over those pad controls:
`lane tune|noise|fx|filter|amp|lfo off|micro|normal|wide` can freeze a lane,
keep it tiny, allow normal live movement, or open it for studio-width
variation. Live defaults are `tune=micro`, `noise=normal`, `fx=micro`,
`filter=normal`, `amp=normal`, and `lfo=off`, so anchors like kick and snare
stay trustworthy while hats, synth voices, and section-change effects can move
more deliberately. The snapshot shell mutates manual-backed CC MSB rows from
the captured kit, including the current-machine SRC rows on pads 1-12, does not
switch machines, and avoids samples, performance macros, source level, track
level, amp volume, SysEx writes, transport, pattern changes, and kit/project
writes. Zone commands (`Y`, `V`, and `N`) layer on the current staged plan; use
`fresh` or `Z` first when you want an anchor-only zone mutation.

Analog Four soft live capture is input-only:

```bash
python -m rytm_randomizer.app --arm --a4-soft-capture
```

It opens an Analog Four MIDI input port, observes pending CC messages, labels manual-backed Appendix D CCs, prints a known/unknown state report for tracks 1-4, and sends no MIDI.

Analog Rytm CC observe is also input-only:

```bash
python -m rytm_randomizer.app --arm --rytm-cc-observe
```

It opens an Analog Rytm MIDI input port, observes pending CC messages, prints
raw pad/channel/control/value observations, lists known candidate Rytm labels,
decodes standard NRPN-style CC99/CC98/CC6/CC38 sequences, and sends no MIDI.
Add `--rytm-cc-observe-snapshot current-kit.syx` when a current-kit dump is
available to replace candidate SRC labels with exact pad/machine labels from
that kit.

Analog Four named parameter sends are active and require an explicit armed
output-port choice:

```bash
python -m rytm_randomizer.app --arm --a4-send-param --parameter "OSC1 PWM Depth" --channel 0 --value 32
```

The command resolves the parameter through the manual-backed Appendix D CC
table, sends one CC MSB message, closes the output port, and exits. Channels
are zero-based mido channels for A4 tracks 1-4, so `--channel 0` targets track
1.

Analog Four kit recipes are active and also require an explicit armed
output-port choice:

```bash
python -m rytm_randomizer.app --arm --a4-kit-recipe detroit-minimal
```

The recipe command sends a coordinated manual-backed four-track CC recipe,
closes the output port, and exits. Current recipes are `detroit-minimal` and
`bell-techno-grid`; `bell-techno-grid` is the more controlled initialized-kit
target.

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

The scene system below is the validated V1.34 four-pad layer. These tables are
the canonical reference for what commands exist there; `rytm_randomizer.shell`
dispatches them. For all-12-pad style mutation, use
`python -m rytm_randomizer.app --dry-run --rytm-12-pad-shell` first, then the
armed form with `--confirm-rytm-12-pad-send`.

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
- Pads 5-12 have passive matrix/compatibility reports, curated Analog Rytm
  style kits can actively send full 12-pad manual-backed CC MSB recipes behind
  `--arm --confirm-rytm-kit-send`, and the all-12-pad shell can mutate loaded
  style plans behind `--arm --rytm-12-pad-shell --confirm-rytm-12-pad-send`.
  The all-12-pad snapshot shell can mutate a current-kit SysEx anchor behind
  `--arm --rytm-snapshot-shell <file.syx> --confirm-rytm-snapshot-shell-send`
  or receive that anchor live behind
  `--arm --rytm-live-snapshot-shell --confirm-rytm-snapshot-shell-send`; in the
  live shell, `kit` / `resnapshot` can receive a new KIT anchor without
  restarting the process.
- Main-prompt `1`, `2`, and `3` remain guarded and send no MIDI.
- Four-pad scene/global commands auto-load anchors if needed.
- Free-form all-row mutation, samples, performance macros, source level, track level, amp volume, NRPN style-kit sends, SysEx, transport, pattern changes, and kit/project writes remain out of scope.
- Analog Four sends are candidate/manifest-gated and require an explicit `--arm` path plus a ready plan; the passive default touches no hardware.
- Analog Rytm CC observe is input-only: `python -m rytm_randomizer.app --arm --rytm-cc-observe` opens a Rytm MIDI input port, observes pending CC messages, prints raw CC/NRPN observations with candidate labels, optionally sharpens labels with `--rytm-cc-observe-snapshot current-kit.syx`, and sends no MIDI.
- Analog Four soft live capture is input-only: `python -m rytm_randomizer.app --arm --a4-soft-capture` opens an A4 MIDI input port, observes pending CC messages, prints a known/unknown state report, and sends no MIDI.
- Analog Four named parameter sends are active: `python -m rytm_randomizer.app --arm --a4-send-param --parameter "OSC1 PWM Depth" --channel 0 --value 32` prompts for an A4 output port, sends one manual-backed CC MSB message, closes the port, and exits.
- Analog Four kit recipes are active: `python -m rytm_randomizer.app --arm --a4-kit-recipe bell-techno-grid` prompts for an A4 output port, sends a coordinated manual-backed four-track CC recipe, closes the port, and exits.

### Dual-machine target commands

The passive CLI exposes the current machine target surface, passive 12-pad machine matrix, snapshot readiness, and Analog Rytm MIDI catalog without opening a MIDI port:

```bash
python -m rytm_randomizer.cli dual-machine-target-report rytm   # Analog Rytm only
python -m rytm_randomizer.cli dual-machine-target-report a4     # Analog Four only
python -m rytm_randomizer.cli dual-machine-target-report both   # both registered devices
python -m rytm_randomizer.cli rytm-12-pad-machine-matrix-report   # passive Rytm 12-pad machine compatibility matrix
python -m rytm_randomizer.cli rytm-snapshot-pad-compatibility-report   # passive snapshot readiness per Rytm pad
python -m rytm_randomizer.cli analog-rytm-midi-catalog-report   # passive OS 1.72 Rytm CC/NRPN catalog
```

Aliases: `rytm-only` and `a4-only` are accepted. The reports are passive: they open no MIDI port and send no MIDI. The snapshot-pad compatibility report explains which legal Rytm pad/machine combinations are snapshot-mutable today and which remain selectable-only until the follow-up runtime slice. The Analog Rytm MIDI catalog records OS 1.72 CC/NRPN rows with safety status labels; documented-only rows are not promoted to mutation until a separate approved hardware-validation pass. The Analog Four path is candidate/manifest-gated; do not run armed Analog Four hardware sends until a readiness report says the plan is ready.

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
