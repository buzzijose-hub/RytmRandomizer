<div align="center">

<img src="docs/assets/hero-banner.svg" alt="RytmRandomizer — your musical taste, on hardware" width="100%" />

# RytmRandomizer

**A creative cockpit for the Elektron Analog Rytm MK2.**
**Author a profile · mutate live · ship to hardware as a signed file.**

[![License](https://img.shields.io/badge/license-PolyForm%20Noncommercial%201.0.0-orange.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-3776AB.svg?logo=python&logoColor=white)](pyproject.toml)
[![Tests](https://img.shields.io/badge/tests-3%2C700%2B-9be8a0.svg)](#testing)
[![Phase 1 · Cockpit](https://img.shields.io/badge/Phase%201%20%C2%B7%20Cockpit-shipped-7cc4ff.svg)](#cockpit)
[![Phase 2 · Wizard](https://img.shields.io/badge/Phase%202%20%C2%B7%20Wizard-shipped-9be8a0.svg)](#profile-wizard)
[![Phase 3 · Export](https://img.shields.io/badge/Phase%203%20%C2%B7%20Export-in%20flight-ffcf7c.svg)](#export-pipeline)
[![Phase 4 · Hardware](https://img.shields.io/badge/Phase%204%20%C2%B7%20Hardware-future-5b6573.svg)](#roadmap)

</div>

---

## What is it?

You own an Analog Rytm. You also own a musical taste — a sound you keep chasing when you sit in front of the machine. RytmRandomizer is the desktop tool that **bridges the two**.

1. **Point it at your inspiration** — a folder of tracks, a kit dump, the name of an artist you love.
2. **It learns your style** as a deployable *Profile* (12 pads × style traits).
3. **Mutate live** during a session: preview the change as a ghost, lock pads you love, undo any move, fire SEND only when the cockpit's pre-flight check says the plan is ready.
4. **Export the Profile** as a tiny signed file you can share, version-pin, or load onto dedicated hardware (Phase 4).

Passive by default — nothing touches MIDI unless you explicitly `--arm`. Byte-identical mutation across Python today and embedded C tomorrow.

---

<a id="cockpit"></a>
## The Cockpit

<div align="center">
<img src="docs/assets/cockpit-mockup.svg" alt="Cockpit GUI mockup — snapshot panel, mutation panel, ghost preview, locks, SEND-plan readiness" width="100%" />
</div>

A Tauri desktop window backed by a Python sidecar that hosts the mutation engine, snapshot history, profile registry, and the device adapter.

| Surface | What it does |
|---|---|
| **Snapshot panel** | All 12 pads at a glance, with a ghost overlay showing what the next mutation would change. Lock any pad to protect it. |
| **Mutation panel** | Pick a profile, set depth (0.10 → 0.90), regen on demand. Every change is deterministic for a given (snapshot, profile, depth, seed). |
| **History strip** | Saved + auto snapshots. Undo any move. Jump to any past snapshot. |
| **SEND-plan readiness** | The cockpit refuses to fire SEND until the server confirms the plan is ready. Stale plans clear automatically after candidate or lock changes. |
| **Profile chips** | Switch profiles mid-set without losing your snapshot or your locks. |

**Passive by construction.** The cockpit defaults to a mock device adapter. No MIDI port opens until you explicitly `--arm`.

---

<a id="profile-wizard"></a>
## The Profile Wizard

<div align="center">
<img src="docs/assets/wizard-flow.svg" alt="Profile Wizard five-step flow — Name, Add sources, Analyze, Review, Save" width="100%" />
</div>

Click **"+ Create profile…"** in the cockpit and walk through five steps to author a `kind="user"` profile from whatever inspires you:

- **Kits** — SysEx dumps from your library
- **Sounds** — folders of `.wav` / `.aif` / `.flac` samples
- **Songs / albums** — audio files run through the existing `style_analysis/` extractor
- **Artists** — names looked up against a curated reference table (e.g. "Surgeon" → industrial/metallic / rolling-low-end)
- **Folders** — point at a directory and the wizard does the right thing per file

Each source is analyzed, the derived `StyleTrait`s are averaged, and the wizard maps them onto pads via a tunable `TRAIT_TO_PAD` table. Hit **Save** and the new profile lands in `~/.rytm-randomizer/profiles/` — the cockpit's profile chips pick it up automatically.

> 🛡️ The wizard is passive — it never opens a MIDI port and never sends MIDI.

---

<a id="export-pipeline"></a>
## Export Pipeline · Phase 3

<div align="center">
<img src="docs/assets/export-pipeline.svg" alt="Export pipeline — ProfileModel through pack, sign, atomic write, verify, to a portable .rymp file" width="100%" />
</div>

A profile in the cockpit is one thing. A **deployable artifact** is another. Phase 3 turns the in-memory `ProfileModel` into a tiny, self-describing, signed file:

```bash
rytm-randomizer cockpit-export-profile-model \
    --profile-id buzzi \
    --output ~/exports/buzzi-v1.0.0.rymp \
    --key-hex $RYMP_SIGNING_KEY --key-id buzzi-2026
```

What it does:

1. **`pack`** the `ProfileModel` to MessagePack with a 4-byte magic (`RYMP`), versioned header, payload length, CRC32.
2. **`sign`** with HMAC-SHA256 (stdlib only — no crypto library dep). Wrap in a `RYMS` envelope carrying the algorithm, key id, and 32-byte signature.
3. **`write`** atomically: temp-file in the same directory → `fsync` → `os.replace`. **No partial files ever land on disk** — works identically on POSIX and Windows.
4. **`verify`** the bytes that were just written. The verifier never raises; it returns a `VerificationResult` with `ok` + a `reason` from a finite set.

The output is a ~8 KB file you can email, hash-check, version-pin in a sample-pack zip, and eventually load onto dedicated hardware.

**Rehearse before you ship.** Run the passive `cockpit-export-rehearsal-report` first to see exactly what file would land — path, payload size, format version, CRC, signing status — without writing anything.

---

## Architecture

<div align="center">
<img src="docs/assets/architecture.svg" alt="System architecture — Cockpit UI, Python sidecar, Analog Rytm hardware, future embedded loader" width="100%" />
</div>

Four boundaries. Same `ProfileModel` shape lives in three of them: the cockpit's in-memory tree, the exported `.rymp` binary, and (eventually) the embedded hardware loader. **Same model → same mutation output** across Python and embedded C.

A few invariants the codebase actively defends:

- **Passive by default.** A subprocess-driven test sweep asserts that no passive CLI command imports `mido` / `rtmidi` / any adapter module. Auto-discovered, so every new command is automatically covered.
- **V1.34 parity is byte-frozen.** The reference mutation engine's behaviour is captured as JSON goldens under `tests/fixtures/v134_parity/` — 685 byte-identical fixtures asserted on every PR.
- **The mutation engine is deterministic.** Same `(snapshot, profile, depth, seed)` → same `MutationCandidate`. Always.
- **Exception taxonomy enforced.** Every `raise` either uses the `RytmRandomizerError` taxonomy or a validation-allowed stdlib class. Architecture tests fail loudly if a new bare exception slips in.
- **Architecture invariants** pin everything from the wire format of the export binary to the existence of the wizard's hash router, so the same regression cannot ship twice.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the long form; [`docs/ARCHITECTURE_DIAGRAMS.md`](docs/ARCHITECTURE_DIAGRAMS.md) for the diagrams.

---

## Use cases

**🎛️ Live-set sound design.** You're three hours into a warehouse set and you need the kit to evolve without losing the bones. Pick a profile, slide depth to ~0.4, REGEN until the ghost overlay looks right, lock the kick, SEND. Two unsaved sends, undo if it didn't land. The 4-pad scene system below the cockpit (Rolling / Deeper / Intense / Wild) gives you another lever for the longer arcs.

**🎹 Dual-machine rigs.** If you run an Elektron Analog Four MKII alongside the Rytm, the same surface plans both. The dual-machine planner accepts saved-kit dumps from both, ranks kit-pairs by readiness against a target style, and produces unified mock previews — keeping the Analog Four's sends candidate / manifest-gated until you explicitly arm it.

**🎚️ Studio profile authoring.** Drop a folder of reference tracks into the wizard, let the style analyzer chew on them, review the trait bars, save as `kind="user"`. Now you have a deployable model that captures *that producer's sound* — not a copy, a reference. Use it next time you want to evoke them without sampling them.

**📦 Share a sound with a friend.** Export your profile as a `~/exports/buzzi-v1.0.0.rymp`. They drop it into their `~/.rytm-randomizer/profiles/`, the cockpit picks it up, they're running mutations against your taste in 60 seconds. CRC32 + HMAC-SHA256 means the file you sent is the file they ran.

**🤖 Future: laptop-free performance.** Phase 4's dedicated hardware loads a `.rymp` from flash, accepts a snapshot over SysEx, generates a `MutationCandidate` using a C-port of the same engine, and emits the resulting CC back to the Rytm. One push-button = a new kit, no laptop in the loop.

---

<a id="install"></a>
## Install

### 🚀 Recommended — native installer (coming soon)

> The signed installers (Windows `.msi`, macOS `.pkg`, Linux AppImage / `.deb`) are wired up via [BeeWare briefcase](https://briefcase.beeware.org/) for the Python CLI and a Tauri 2 bundle for the cockpit GUI. The first signed release ships with Phase 3.

Two install paths because there are two artifacts:

| Artifact | What it includes | Build target |
|---|---|---|
| **Briefcase installer** | Python CLI sidecar — passive reports, armed `rytm-randomizer` runtime, export CLI | `.github/workflows/installers.yml` `briefcase` |
| **Cockpit Tauri bundle** | React cockpit GUI + Profile wizard + bundled Python sidecar | `.github/workflows/installers.yml` `desktop-bundle` |

Install both if you want the GUI cockpit *and* the CLI. See [`docs/BUILDING_INSTALLERS.md`](docs/BUILDING_INSTALLERS.md) for the build matrix and per-OS prerequisites.

### 🛠️ pip (works today)

```bash
pip install rytm-randomizer
# or, from a clone:
pip install -e .
```

### Launch

```bash
# Passive menu — no MIDI port, no MIDI sent. Safe to explore.
rytm-randomizer

# Full interactive logic against an in-memory mock sender.
rytm-randomizer --dry-run

# Open a real MIDI port and drive the Analog Rytm.
rytm-randomizer --arm
```

`--arm` and `--dry-run` are mutually exclusive; pick one, or neither for the passive menu.

### Launching the cockpit

```bash
# Terminal 1 — Python sidecar (WebSocket on 127.0.0.1:4317)
python -m rytm_randomizer.cockpit

# Terminal 2 — Tauri shell + web frontend
cd desktop/shell && cargo run
```

(In a release build, the Tauri shell auto-spawns the sidecar — the two-terminal split is for development only.) See [`docs/COCKPIT_QUICKSTART.md`](docs/COCKPIT_QUICKSTART.md) for prerequisites, install steps, and the first-profile walkthrough.

---

<a id="roadmap"></a>
## Roadmap

```
✅ Phase 1 · Cockpit                      Tauri shell, WS sidecar, mutation engine,
   shipped (PR #99)                       snapshot history, profile registry,
                                          v10 UX (snapshot · mutation · history).

✅ Phase 2 · Profile Wizard               In-cockpit authoring of kind="user"
   shipped (PR #102)                      profiles from kits, audio, references.
                                          Plus Playwright E2E + 17 arch guards.

🚧 Phase 3 · Export Pipeline              Production-grade pipeline around the
   in flight                              Phase 1 serializer: HMAC-SHA256
                                          signing, atomic file writes,
                                          never-raises verifier, CLI driver,
                                          passive pre-flight rehearsal report.

🔮 Phase 4 · Hardware Runtime             Dedicated device that loads .rymp
   future                                 from flash, runs an embedded C
                                          port of the same mutation engine,
                                          emits CC back to the Rytm.
                                          One push-button = new kit, no laptop.
```

See [`docs/STATUS.md`](docs/STATUS.md) for the dated activity log and the per-phase implementation plans under [`docs/superpowers/plans/`](docs/superpowers/plans/).

---

## For contributors

```bash
git clone https://github.com/buzzijose-hub/RytmRandomizer.git
cd RytmRandomizer
pip install -e ".[dev]"
pytest                    # full suite — 3,700+ tests, ~30s on a multi-core machine
just check                # pre-PR gate (ruff + black + isort + tests + arch)
```

The test suite uses `pytest-xdist` (`-n auto`) for parallel execution and a 180-second per-test timeout. Don't pass `-o addopts=''` for normal runs — it disables xdist and triples the runtime.

**Repository map** (high-level):

| Path | Purpose |
|---|---|
| `rytm_randomizer/cockpit/` | Phase 1 cockpit · data · engine · profiles · history · device · ws · export |
| `rytm_randomizer/cockpit/wizard/` | Phase 2 wizard · state · analyze · sysex/reference analyzers · builder · pad mapping |
| `rytm_randomizer/cockpit/export/` | Phase 3 export pipeline · pack · sign · write · verify · CLI |
| `rytm_randomizer/devices/` | Cross-machine `Device` Protocol + registry (Analog Rytm + Analog Four) |
| `rytm_randomizer/reports/` | 50+ passive reports — CLI-driven, no MIDI side effects |
| `rytm_randomizer/engines/`, `group_runner.py`, `scene_runner.py` | V1.34 Analog Rytm orchestration (byte-frozen reference) |
| `rytm_randomizer/data/`, `state/`, `guardrails/`, `observability/` | Fact tables, runtime state, policy, logging |
| `desktop/shell/` | Tauri 2 Rust shell — spawns the Python sidecar, wraps the web frontend |
| `desktop/web/` | React + TypeScript + Vite cockpit + wizard UI · vitest + Playwright |
| `tests/` | 3,700+ tests across 170+ modules — arch invariants, V1.34 parity, integration, E2E |
| `docs/` | Architecture, status, plans, specs, install + cockpit quickstart |

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the workflow (plan → TDD → code review → ship), the parity rules around V1.34, and the per-PR gate battery. Agentic contributors should read [`AGENTS.md`](AGENTS.md) and [`docs/CODEX_CONTRIBUTING.md`](docs/CODEX_CONTRIBUTING.md).

---

## CLI cheat-sheet

The full surface is large — see [`docs/CLI_REFERENCE.md`](docs/CLI_REFERENCE.md) for every command and its flags. The headline ones:

```bash
# Cockpit + wizard + export
python -m rytm_randomizer.cockpit                                     # sidecar
cockpit-export-profile-model --profile-id X --output Y.rymp           # ship a profile (Phase 3)
cockpit-export-rehearsal-report --profile-id X                        # passive pre-flight

# Live-set planning
style-performance-arc-live-set-cockpit-report                         # one-screen cockpit packet
style-performance-arc-live-show-export-report                         # handoff manifest
style-performance-arc-stage-routing-report                            # cue-by-cue route cards

# Dual-machine targets
dual-machine-target-report rytm | a4 | both                           # safe target surface
dual-machine-style-kit-selection-report STYLE --rytm KITS --analog-four KITS

# Snapshot intelligence
rytm-snapshot-intelligence-report KITS.syx --slot N                   # one Rytm kit snapshot
rytm-snapshot-mutation-preview-report KITS.syx --slot N --depth 2     # mock-only preview
```

Every command above is **passive by construction** — no MIDI port opens, no MIDI is sent. The full list is auto-discovered and swept on every PR by `tests/test_real_midi_passive_cli_safety.py`.

---

## Scenes and commands · V1.34

The validated V1.34 layer is the byte-frozen reference behaviour for the interactive armed runtime. These are the canonical command tables that `rytm_randomizer.shell` dispatches.

<details>
<summary><b>Scene system</b></summary>

```text
S0  = Home / Clean anchors
S1  = Rolling          S1A = Rolling Light       S1B = Rolling Push
S2  = Deeper           S2A = Deeper Groove       S2B = Deeper Pressure
S3  = Intense          S3A = Intense Motion      S3B = Intense Grit
S4  = Wild             S4A = Wild Controlled     S4B = Wild Maximum
S5  = Back to Clean anchors
```

</details>

<details>
<summary><b>Four-lane pad layout</b></summary>

```text
Pad 1 = BD Hard      / protected kick foundation
Pad 2 = BD Classic   / secondary percussion lane
Pad 3 = SY Raw       / bass + synth-percussion motion lane
Pad 4 = BD Acoustic  / body + accent pressure lane
```

</details>

<details>
<summary><b>Example scene flow</b></summary>

A typical four-pad live arc:

```text
SCN     GM      S1A     S3A     S3B     S4B     S5      1       Z       Q
```

Keep volume moderate for S3B and S4B.

</details>

<details>
<summary><b>Safety rules</b></summary>

- No new machine profiles.
- No new MIDI CC mappings.
- No new parameter ranges.
- Pads 5-12 have a passive machine matrix report; armed 12-pad runtime mutation remains gated.
- Main-prompt `1`, `2`, and `3` remain guarded and send no MIDI.
- Four-pad scene/global commands auto-load anchors if needed.
- Analog Four sends are candidate/manifest-gated and require an explicit `--arm` path plus a ready plan; the passive default touches no hardware.

</details>

---

## License

**Free for personal and noncommercial use. Commercial license available.**

RytmRandomizer is licensed under the [PolyForm Noncommercial License
1.0.0](LICENSE) — a [source-available](https://en.wikipedia.org/wiki/Source-available_software)
license that lets anyone clone, run, modify, share, and contribute to the
project for any **noncommercial** purpose. That includes hobby projects,
personal use, research, education, charitable work, and government use.

What requires a separate commercial license:

- Bundling RytmRandomizer (or a derivative) into a paid product
- Hosting RytmRandomizer as a paid service or SaaS offering
- OEM bundling, white-label distribution, or paid integrations
- Any other revenue-generating use

For commercial licensing inquiries, open an issue or contact the project
owners via the [GitHub project page](https://github.com/buzzijose-hub/RytmRandomizer).

Copyright (c) 2025-2026 Jose Buzzi ([@buzzijose-hub](https://github.com/buzzijose-hub))
and Edward Rosado ([@edward-rosado](https://github.com/edward-rosado)).

<div align="center">

**Made for the Analog Rytm MK2. Built so the same model runs on hardware tomorrow.**

[Docs](docs/) · [Status](docs/STATUS.md) · [Cockpit Quickstart](docs/COCKPIT_QUICKSTART.md) · [Architecture](docs/ARCHITECTURE.md) · [Contributing](CONTRIBUTING.md)

</div>
