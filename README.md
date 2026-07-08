<div align="center">

<img src="docs/assets/hero-banner.svg" alt="RytmRandomizer — your musical taste, on hardware" width="100%" />

# RytmRandomizer

**A creative cockpit for the Elektron Analog Rytm MK2.**
**Author a profile · mutate live · ship to hardware as a signed file.**

[![License](https://img.shields.io/badge/license-PolyForm%20Noncommercial%201.0.0-orange.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-3776AB.svg?logo=python&logoColor=white)](pyproject.toml)
[![Tests](https://img.shields.io/badge/tests-3%2C900%2B-9be8a0.svg)](#testing)
[![Phase 1 · Cockpit](https://img.shields.io/badge/Phase%201%20%C2%B7%20Cockpit-shipped-7cc4ff.svg)](#cockpit)
[![Phase 2 · Wizard](https://img.shields.io/badge/Phase%202%20%C2%B7%20Wizard-shipped-9be8a0.svg)](#profile-wizard)
[![Phase 3 · Export](https://img.shields.io/badge/Phase%203%20%C2%B7%20Export-shipped-9be8a0.svg)](#export-pipeline)
[![Phase 4 · Hardware](https://img.shields.io/badge/Phase%204%20%C2%B7%20Hardware-next-ffcf7c.svg)](#roadmap)

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
| **Device rail** | Switch the cockpit view between the Analog Rytm MKII 12-pad surface and the Analog Four MKII four-track mock/staged surface. |
| **Snapshot panel** | All 12 pads at a glance, with a ghost overlay showing what the next mutation would change. Lock any pad to protect it. |
| **Mutation panel** | Pick a profile, set depth (0.10 → 0.90), regen on demand. Every change is deterministic for a given (snapshot, profile, depth, seed). |
| **History strip** | Saved + auto snapshots. Undo any move. Jump to any past snapshot. |
| **SEND-plan readiness** | The cockpit refuses to fire SEND until the server confirms the plan is ready. Stale plans clear automatically after candidate or lock changes. |
| **Profile chips** | Switch profiles mid-set without losing your snapshot or your locks. |

**Passive by construction.** The cockpit defaults to a mock device adapter. No MIDI port opens until you explicitly `--arm`.

The Analog Four cockpit view is currently visibility-only. It shows four synth
tracks, the existing A4 strategy zones, and OXI-style track macro rows for
Anchor / Shape / Pressure / Space dry-run review, but it does not add an A4
SEND path, open ports, or send MIDI. The passive
`analog-four-oxi-macro-report` command previews four-track OXI-style A4 macro
shapes from manual-backed CC metadata before any future send path is promoted.
The paired passive `analog-four-oxi-macro-readiness-report` command turns those
rows into a soft-capture-first validation workflow, operator-present one-row
validation commands, recovery notes, and promotion gates while explicitly
keeping full A4 macro SEND blocked until separate hardware evidence promotes it.
The passive `analog-four-oxi-macro-set-planner-report` command sequences those
macro/readiness cards into a current/up-next set plan for future Cockpit queue
work, including the report-owned replay command, without adding A4 playback,
automation, port opening, or MIDI sending.
The passive `live-gui-performance-console-report` also composes that set
planner with the A4 readiness payload into a Cockpit A4 Review Surface: the UI
can show the `warehouse-arc` sequence, the next macro's readiness rows,
soft-capture preflight, validation steps, recovery notes, promotion gates, and
blocked full-SEND/unattended-playback actions while every A4 Review/Promote
control remains disabled.
The same passive console now exposes a Rytm Lane Policy Matrix beside the
12-pad surface. It makes the OXI-style macro rules visible before anything is
sent: pads 5, 9, 10, and 11 stay SRC-first with filter/LFO off and AMP limited
to overdrive/delay/reverb; pads 6-8 get useful tom/source movement with light
filter and no LFO craziness; Pad 12 remains product-supported even when a live
operator chooses not to use it. Apply/Send controls for that matrix remain
disabled in Cockpit; real sends still happen only from the explicitly armed
snapshot shell.
The Performance Console route renders those passive packets in a cinematic
operator HUD: top safety bar, device rail, all-12-pad snapshot deck, Style
Crates/queue mutation panel, blocked hardware actions, command queue, safety
checklist, and bottom session strip. The layout is still review-only: it
does not dispatch sidecar commands, open MIDI ports, arm hardware, or send
MIDI.
It also supports local-only rehearsal interactions for selecting crates,
queued moves, snapshots, preview depth, dry-run summary, and journal saves;
those controls update in-memory preview state only and still do not dispatch
sidecar commands, open MIDI ports, arm hardware, or send MIDI.
The same local layer can stage multiple set-plan steps, promote the next staged
move into a current local set-plan step, label the remaining move as up next,
show an operator handoff with current/next/recovery notes, complete the current
step, skip or clear queued moves, reset the local plan, and keep a local
operator activity log while remaining component-local and mock-safe.
It also supports browser-local auto-save plus copy-ready JSON export/import for
that rehearsal state, so operators can recover or move a local plan without any
sidecar command, file write, MIDI port, hardware arm path, or MIDI send.
The same persistence surface can wrap that local rehearsal snapshot in a
portable rehearsal package with a manifest, current packet compatibility
checks, device/safety evidence, blocked-action evidence, and recovery notes.
The passive live-kit audition lane now feeds a browser-local Live Kit Operator
Package panel: captured-base, hard-groove, industrial, dub, and recovery
audition slots can be staged into the local set-plan, reviewed with explicit
recovery requirements, and exported with `auditionSource` / `operatorPackage`
metadata so the package records which captured-kit move inspired it.
Package import still accepts the older raw local snapshot JSON shape for
backward compatibility, recalculates compatibility against the current passive
packet, and now renders a browser-local package review workbench that compares
the package against the currently loaded cockpit packet and stages review
evidence in the operator log. The package flow remains browser-local only: no
sidecar command, project file write, MIDI port, hardware arm path, or MIDI send.

**Sidecar security guarantees** (post CODE_REVIEW.md sweep, 2026-05):

- **Per-launch HMAC handshake token.** The sidecar mints a fresh URL-safe token on every start (`secrets.token_urlsafe(32)`), writes it to `RYTM_RAND_WS_TOKEN_FILE` (or `~/.rytm-randomizer/cockpit-ws-token` in dev), and refuses every command until the first WS frame echoes the token under `hmac.compare_digest`. A foreign browser tab that can't read the token file cannot drive the cockpit.
- **Pinned subprotocol** (`rytm-rand-cockpit-v1`). Casual `new WebSocket(url)` connections from a browser tab omit the subprotocol and fail the upgrade.
- **Per-message size cap** (1 MiB by default; override via `RYTM_RAND_WS_MAX_MESSAGE_BYTES`). Oversize frames are rejected before parsing so a hostile client can't OOM the sidecar.
- **Wizard-source path allow-list.** Filesystem locations sent to the analyzer must resolve inside one of the roots in `WIZARD_SOURCE_ROOTS` (defaults to `~/.rytm-randomizer/wizard-sources/`). Symlinks and out-of-root paths are rejected with a categorical reason that never echoes the path back over the wire.
- **Architecture-enforced.** Nine prevention tests under `tests/architecture/` (e.g. `test_no_unauthenticated_ws_endpoints`, `test_no_unconstrained_path_inputs`, `test_no_raw_exception_messages_on_wire`, `test_no_silent_overwrite_writes`) hard-fail CI if any of these invariants regresses.

For the dev-loop launch (two-terminal split) see [`docs/COCKPIT_QUICKSTART.md`](docs/COCKPIT_QUICKSTART.md). The release Tauri bundle spawns the sidecar automatically.

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

A profile in the cockpit is one thing. A **deployable artifact** is another. Phase 3 turns the in-memory `ProfileModel` into a tiny, self-describing, signed file (`cockpit-export-profile-model` for the write, `cockpit-export-rehearsal-report` for the passive pre-flight; see [`docs/COCKPIT_QUICKSTART.md`](docs/COCKPIT_QUICKSTART.md) §5c for the operator walkthrough):

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

> The signed installers (Windows `.msi`, macOS `.pkg`, Linux AppImage / `.deb`) are wired up via [BeeWare briefcase](https://briefcase.beeware.org/) for the Python CLI and a Tauri 2 bundle for the cockpit GUI. Phase 3's export pipeline is the last on-disk artifact gate before the first signed release; OS signing / notarization is the only outstanding piece.

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
`resnapshot`, `drum-core`, `kit-core`, `hard-groove`, `industrial`,
`dub-pressure`, `transition`, `home`, `macro NAME`, `mode`, `depth`, `lane`,
`lock`, `unlock`, `pad`, `preset`, `guards reset`, `status`, and `q`. `Y`,
`V`, and `N` ask for depth (`micro`, `groove`, or `strong`). `send` repeats
the currently staged plan; type `go` to
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
drum-core
kit-core
hard-groove
industrial
dub-pressure
transition
home
macro hard-groove
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

Named live staging macros capture the OXI-style hardware-testing direction.
`drum-core` keeps the hardware-proven four-pad recipe: `preset live`, LFO off,
FX micro, Pad 1 locked as the kick anchor, and pads 2-4 wide/full with Pad 2
looser and pads 3-4 grittier. `kit-core` extends that idea to the whole
captured kit while keeping Jose's pad 5-12 lane discipline: Pad 1 stays locked;
pads 2-4 keep the drum-core recipe; pads 6-8 are treated as tom/discovery
voices with wide/full source movement, light filter movement, no LFO movement,
and AMP limited to overdrive, delay, and reverb; pads 5, 9, 10, and 11 do not
move filter or LFO rows and also limit AMP movement to overdrive, delay, and
reverb. The newer macro shortcuts layer on top of that same safety model:
`hard-groove` is dry pressure for OXI patterns that already carry the groove,
`industrial` adds metallic pressure and controlled grit, `dub-pressure` opens a
darker spacious pressure lane, `transition` stages section movement, and `home`
returns the staged plan to the captured anchor. You can also type
`macro hard-groove`, `macro industrial`, `macro dub-pressure`,
`macro transition`, or `macro home`. Every macro stages changes first. Inspect
`changes`, then explicitly type `send` or `go` when you are ready. Use `Z` plus
`send` or `home` plus `send` to recover the captured kit.

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
Add `--rytm-cc-observe-live-snapshot` to receive one current-kit SysEx from
the same selected input before observing CCs, which gives exact pad/machine SRC
labels without a separate file.
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

<a id="roadmap"></a>
## Roadmap

```
✅ Phase 1 · Cockpit                      Tauri shell, WS sidecar, mutation engine,
   shipped (PR #99)                       snapshot history, profile registry,
                                          v10 UX (snapshot · mutation · history).

✅ Phase 2 · Profile Wizard               In-cockpit authoring of kind="user"
   shipped (PR #102)                      profiles from kits, audio, references.
                                          Plus Playwright E2E + 17 arch guards.

✅ Phase 3 · Export Pipeline              Production-grade pipeline around the
   shipped (PR #106)                      Phase 1 serializer: HMAC-SHA256
                                          signing (stdlib only, timing-safe),
                                          atomic file writes (sibling temp +
                                          fsync + os.replace), never-raises
                                          integrity verifier, CLI driver, and
                                          passive pre-flight rehearsal report.
                                          7 WSes, 1 bundled PR, Phase-4-ready
                                          wire format pinned by arch tests.

🔮 Phase 4 · Hardware Runtime             Dedicated device that loads .rymp
   next                                   from flash, runs an embedded C
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
pytest                    # full suite — 3,900+ tests, ~30s on a multi-core machine
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

The full surface is large - see [`docs/CLI_REFERENCE.md`](docs/CLI_REFERENCE.md) for every command and its flags. The headline ones:

The scene system below is the validated V1.34 four-pad layer. These tables are
the canonical reference for what commands exist there; `rytm_randomizer.shell`
dispatches them. For all-12-pad style mutation, use
`python -m rytm_randomizer.app --dry-run --rytm-12-pad-shell` first, then the
armed form with `--confirm-rytm-12-pad-send`.

```bash
# Cockpit + wizard + export
python -m rytm_randomizer.cockpit                                     # sidecar
cockpit-export-profile-model --profile-id X --output Y.rymp           # ship a profile (Phase 3)
cockpit-export-rehearsal-report --profile-id X                        # passive pre-flight
manual-feedback-packet-report --scenario profile                      # collect installer/wizard/export feedback

# Live-set planning
style-performance-arc-live-set-cockpit-report                         # one-screen cockpit packet
style-performance-arc-live-show-export-report                         # handoff manifest
style-performance-arc-stage-routing-report                            # cue-by-cue route cards
style-crates-queue-journal-report --json                              # crates, staged moves, journal seeds
style-crate-rehearsal-deck-report --json                              # GUI-ready crate/queue/journal rehearsal cards
reference-style-blueprint-report --description "Glenn Wilson pressure" # 12-pad + A4 influence blueprint

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
- Analog Rytm CC observe is input-only: `python -m rytm_randomizer.app --arm --rytm-cc-observe` opens a Rytm MIDI input port, observes pending CC messages, prints raw CC/NRPN observations with candidate labels, optionally sharpens labels with `--rytm-cc-observe-live-snapshot` or `--rytm-cc-observe-snapshot current-kit.syx`, and sends no MIDI.
- Analog Four soft live capture is input-only: `python -m rytm_randomizer.app --arm --a4-soft-capture` opens an A4 MIDI input port, observes pending CC messages, prints a known/unknown state report, and sends no MIDI.
- Analog Four named parameter sends are active: `python -m rytm_randomizer.app --arm --a4-send-param --parameter "OSC1 PWM Depth" --channel 0 --value 32` prompts for an A4 output port, sends one manual-backed CC MSB message, closes the port, and exits.
- Analog Four kit recipes are active: `python -m rytm_randomizer.app --arm --a4-kit-recipe bell-techno-grid` prompts for an A4 output port, sends a coordinated manual-backed four-track CC recipe, closes the port, and exits.

</details>

The passive CLI exposes the current machine target surface, passive 12-pad machine matrix, snapshot readiness, and Analog Rytm MIDI catalog without opening a MIDI port:

```bash
python -m rytm_randomizer.cli dual-machine-target-report rytm   # Analog Rytm only
python -m rytm_randomizer.cli dual-machine-target-report a4     # Analog Four only
python -m rytm_randomizer.cli dual-machine-target-report both   # both registered devices
python -m rytm_randomizer.cli rytm-12-pad-machine-matrix-report   # passive Rytm 12-pad machine compatibility matrix
python -m rytm_randomizer.cli rytm-snapshot-pad-compatibility-report   # passive snapshot readiness per Rytm pad
python -m rytm_randomizer.cli analog-rytm-midi-catalog-report   # passive OS 1.72 Rytm CC/NRPN catalog
python -m rytm_randomizer.cli oxi-live-macro-catalog-report   # passive OXI live macro cards, live flow, and A4 runway state
python -m rytm_randomizer.cli controller-brain-mapping-report --json   # passive 16-encoder controller-brain intent map
python -m rytm_randomizer.cli controller-brain-rehearsal-report --json   # passive controller-brain template/rehearsal export packet
python -m rytm_randomizer.cli controller-brain-operator-package-report --json   # passive controller gestures to operator package ledger
python -m rytm_randomizer.cli rytm-live-macro-hardware-rehearsal-report --json   # passive next-studio Rytm macro rehearsal checklist
python -m rytm_randomizer.cli live-gui-performance-flow-model-report --json   # cockpit-ready Rytm/A4 performance flow model
python -m rytm_randomizer.cli live-gui-performance-console-report --json   # full passive Cockpit performance console packet with lane policy, macro action, rehearsal board, live-kit capture workbench/package audition/operator package/review ledger, and controller-brain panel
python -m rytm_randomizer.cli oxi-live-set-strategy-report --json   # passive OXI set chapters, operator cues, rehearsal/replay commands, pad policy, and A4 review-only actions
python -m rytm_randomizer.cli analog-four-oxi-macro-report hard-groove --seed 23 --intensity 6 --events --limit 0
python -m rytm_randomizer.cli analog-four-oxi-macro-readiness-report hard-groove --seed 0 --intensity 4 --limit 4
python -m rytm_randomizer.cli analog-four-oxi-macro-set-planner-report --json
```

The Operator Package WebSocket bridge is still mock-safe: the Performance Console
can rehearse one operator-package step (`rehearse_operator_package_step`) or the
whole package sequence (`rehearse_operator_package_sequence`), preview the apply
plan, mock-apply it (`mock_apply_operator_package`), and build a receipt audit
(`build_operator_package_receipt`). These review acks prove no MIDI port opened,
no MIDI was sent, no file was written, no snapshot mutated, no send plan applied,
and no event stream emitted.

Aliases: `rytm-only` and `a4-only` are accepted. The reports are passive: they open no MIDI port and send no MIDI. The snapshot-pad compatibility report explains which legal Rytm pad/machine combinations are snapshot-mutable today and which remain selectable-only until the follow-up runtime slice. The Analog Rytm MIDI catalog records OS 1.72 CC/NRPN rows with safety status labels; documented-only rows are not promoted to mutation until a separate approved hardware-validation pass. The controller-brain mapping report turns a generic 16-encoder surface into reviewed intent pages for global macro depth, all 12 Rytm pads, Analog Four runway tracks, Style Crates, live queue staging, snapshot recovery, and the Mutation Journal; it deliberately blocks MIDI controller input, raw CC learn, WebSocket dispatch, hardware arming, and hardware sends. The controller-brain rehearsal report derives 112 controller-template rows from that same map, resolves virtual encoder gestures into deterministic intent outcomes, emits blocked-action evidence, and provides a JSON export packet future controller software can render without opening controller input or sending MIDI. The controller-brain operator-package report composes those virtual gestures with the Live Kit Operator Package slots so macro, pad-lane, crate, queue, A4 review, and recovery intents can be staged as package-review metadata without controller input, WebSocket dispatch, file writes, or MIDI sends. The live GUI performance-flow model emits the cockpit-ready sequence that joins Rytm OXI macro commands with Analog Four review-only actions. The live GUI performance-console report composes the Rytm 12-pad snapshot surface, Rytm Lane Policy Matrix, device inventory, Style Crates queue and Mutation Journal cards, snapshot history, command queue, safety checklist, Analog Four set-plan review, a passive macro action deck for `kit-core`, `hard-groove`, `industrial`, `dub-pressure`, `transition`, and `home`, a passive Rehearsal Board, a passive Controller Brain panel, a passive Live Kit Capture panel, a passive Live Kit Capture Workbench, and a passive Live Kit Package Audition surface. The panel shows the "Mutate the kit you are actually playing." workflow: receive KIT SysEx in the armed snapshot shell, review the captured kit, mutate from that exact anchor, manually `go`, recover with `home`/`Z` plus `send`, or `resnapshot` a new anchor. The workbench packages that workflow into capture slots, anchor verification, mutation-readiness gates, recovery gates, and future package-manifest metadata while keeping receive/apply/export/send controls disabled. The package audition surface turns that package metadata into review-only audition slots, queue order, package checks, and a journal-preview seed so future active work has GUI-ready structure without writing package files or sending MIDI. The Operator Package bridge lets the Performance Console send typed mock-safe WebSocket commands for package-step rehearsal, sequence rehearsal, apply preview, mock apply, and receipt audit; the acks record no port opened, no MIDI sent, no files written, no snapshot mutated, no send plan applied, and no event stream emitted, so it remains a runtime rehearsal bridge rather than a hardware-send path. The Operator Package Review Ledger renders those same apply-preview, mock-apply, and receipt-audit stages as passive packet evidence with one row per package step, package export-key proof, readiness proof, blocked actions, safety lines, and a disabled ledger apply control. It stays passive/mock-safe and represents hardware sends, lane-policy dispatch, queue dispatch, snapshot-history SEND, Cockpit macro fire/prepare, Cockpit rehearsal launch/fire, live-kit receive/mutate/send, captured-kit package apply/export/audition, controller MIDI learn/input, controller WebSocket dispatch, and A4 outbound macro send as blocked actions. The lane matrix preserves the pad 5/9/10/11 SRC-first lane discipline, the pad 6-8 tom/source lane, and Pad 12 product availability directly in the console contract. The Rytm live macro hardware rehearsal report turns the macro list into a next-studio checklist with the armed shell launch command, per-macro checkpoints, Pad 5/9/10/11 SRC-first notes, Pad 6-8 tom/source notes, Pad 12 availability notes, and `home`/`Z` recovery checks. The OXI live set strategy report ties `kit/resnapshot`, `kit-core`, `hard-groove`, `industrial`, `dub-pressure`, `transition`, and `home` into operator chapters while preserving the pad 5/9/10/11 SRC+FX lane discipline, the pad 6-8 tom/source lane, Pad 12 availability for users who rely on it, the next Rytm/A4 validation runway, the A4 promotion gates, an operator cue sheet for what OXI keeps handling, what RytmRandomizer stages, what Jose inspects, what fires, what recovers, rehearsal checkpoints for capture, review, fire, recovery, A4 gating, and after-set notes, and replay/rehearsal command metadata for passive reports, A4 review, Rytm shell launch, `changes`, manual fire, and recovery. The A4 readiness report adds the soft-capture preflight command plus one-row validation commands and stop/recovery notes. The A4 set planner sequences current/up-next macros for Cockpit style-queue review while keeping full A4 macro SEND blocked. The Analog Four path is candidate/manifest-gated; do not run armed Analog Four hardware sends until a readiness report says the plan is ready.

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
