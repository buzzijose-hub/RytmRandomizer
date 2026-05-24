# Cockpit Quickstart

> **Status: alpha.** The Phase 1 cockpit is in active implementation against
> `feat/cockpit-and-profile-model-bundle`. Treat this guide as the operator-
> facing entry point; the [design spec](superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md)
> is the authoritative architectural reference, and [`docs/ARCHITECTURE.md` §6.2](ARCHITECTURE.md#62-cockpit--profile-model-layer-phase-1)
> is the architecture-doc explanation.

The Cockpit is a desktop window that gives you a single-screen view of your
Elektron rig's current state and lets you generate new kits from your own
authored intelligence. Pick a profile, slide a depth knob, hit SEND, audition,
SAVE the good ones, UNDO the bad ones. Walk forward through history. The
whole point is to keep you at the rig, not at the laptop.

This guide gets you from a clean clone to a working cockpit window on your
machine.

---

## 1. Prerequisites

The cockpit is a Tauri 2 desktop app (Rust) wrapping a web frontend (Vite +
React + TypeScript) that talks to a Python sidecar (your existing
RytmRandomizer install) over WebSocket. You need three toolchains plus
Tauri's per-OS system dependencies.

### Toolchain versions

| Toolchain | Version | Install link |
|---|---|---|
| Python | 3.11 | [python.org/downloads](https://www.python.org/downloads/) |
| Rust | 1.88 stable | [rustup.rs](https://rustup.rs/) |
| Node.js | 20 LTS | [nodejs.org](https://nodejs.org/), or use `nvm` / `fnm` |

### Tauri system prerequisites by OS

Tauri renders the frontend using the system's native WebView, which needs
a small set of platform libraries. The Tauri team maintains canonical
install instructions; the summary below is verified against the
[Tauri Prerequisites](https://tauri.app/start/prerequisites/) page.

**Windows 10 / 11**

- [Microsoft Visual Studio C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) — required for compiling the Tauri shell.
- [WebView2 Runtime](https://developer.microsoft.com/microsoft-edge/webview2/) — bundled on Windows 11; install manually on Windows 10.

```powershell
# Verify the build tools and WebView2 are reachable
where cl
Get-AppxPackage -Name Microsoft.WebView2*
```

**macOS 12 (Monterey) or newer**

- Xcode Command Line Tools: `xcode-select --install` (one-time).

```bash
# Verify
xcode-select -p
```

**Linux (Debian / Ubuntu reference)**

```bash
sudo apt update
sudo apt install -y \
  libwebkit2gtk-4.1-dev \
  build-essential \
  curl \
  wget \
  file \
  libxdo-dev \
  libssl-dev \
  libayatana-appindicator3-dev \
  librsvg2-dev
```

For Fedora, openSUSE, Arch, and other distributions, see the
[Tauri Linux setup page](https://tauri.app/start/prerequisites/#linux)
for the equivalent package names.

---

## 2. Install RytmRandomizer (Python sidecar)

The cockpit sidecar IS the RytmRandomizer Python package — same install
path as the existing CLI.

```bash
git clone https://github.com/buzzijose-hub/RytmRandomizer.git
cd RytmRandomizer
python -m venv .venv

# macOS / Linux:
source .venv/bin/activate
# Windows PowerShell:
.venv\Scripts\Activate.ps1

pip install -e ".[dev]"
```

Verify the sidecar starts:

```bash
python -m rytm_randomizer.cockpit
# Expected: "Cockpit WebSocket server listening on 127.0.0.1:4317"
# Stop with Ctrl-C.
```

If port 4317 is taken, override it:

```bash
RYTM_RAND_WS_PORT=4318 python -m rytm_randomizer.cockpit
```

The same env var configures the Tauri shell when it spawns the sidecar.

---

## 3. Build the web frontend

```bash
cd desktop/web
npm install
npm run build
```

`npm run build` writes the production bundle to `desktop/web/dist/`. The
Tauri shell loads it from there.

For active UI development, run `npm run dev` instead — it serves the
frontend at `http://localhost:5173` with hot module reload. You can point
a browser at that URL while the sidecar is running and the cockpit works
the same way as inside the Tauri window. Useful when iterating on the
React tree without paying the Rust rebuild cost.

---

## 4. Build and launch the Tauri shell

```bash
cd desktop/shell
cargo build
cargo run
```

`cargo run` opens the cockpit window and spawns the Python sidecar
automatically. First build is multi-minute on a cold Rust cache;
subsequent rebuilds are seconds.

For a standalone redistributable binary:

```bash
cargo build --release
# Binary at desktop/shell/target/release/rytm-randomizer-cockpit
```

The release binary embeds the web frontend (from `desktop/web/dist/`)
and spawns the sidecar via the `python -m rytm_randomizer.cockpit`
command on your PATH.

---

## 5. Your first profile

When the window opens you see the v10 cockpit: a Snapshot panel on the
left (your current pad state) and a Mutation Panel on the right
(profile, depth, SEND/REGEN/UNDO/SAVE).

1. **Pick a built-in scene** — the right panel lists seven shipped
   `kind="scene"` profiles (industrial, hypnotic, garage, peak_time,
   rolling, birmingham, drone). Click one to make it active.
2. **Slide the depth** — somewhere mid-range (45%) is the live-safe
   default. The ghost overlay on the pad cards previews the proposed
   parameter changes.
3. **Toggle PREVIEW off and on** — confirms the overlay tracks the
   active candidate.
4. **Hit REGEN** — same depth, new seed, different candidate.
5. **Hit SEND** — the candidate becomes the new snapshot; a grey dot
   joins the history strip; preview clears.
6. **Hit SAVE** with a label** — promotes the current snapshot to a
   persistent kit slot; the dot turns green.
7. **Hit UNDO** — walks the history back one step.

Profiles live as flat JSON files under `~/.rytm-randomizer/profiles/` on
Linux (`$XDG_CONFIG_HOME/rytm-randomizer/profiles/` is honored if set),
and platform-appropriate paths on macOS and Windows. You can hand-edit
the JSON to author profiles, but the supported authoring path is the
Phase 2 Profile Wizard described below.

---

## 5b. Creating your first profile

The Phase 2 **Profile Wizard** is the in-cockpit authoring surface for
`kind="user"` profiles. It turns a pile of musical inspiration — a
folder of Rytm SysEx kits, a song file, an artist name — into a
deployable `ProfileModel` you can select from the cockpit's
`ProfileChips` and drive with the depth slider. The wizard is passive
by construction: it reads files, decodes SysEx in memory, and writes
one JSON file at save time. It never opens a MIDI port and never sends
MIDI; the armed runtime is the only thing in the cockpit that touches
hardware.

The walkthrough below assumes the cockpit is already launched per
sections 1–4 and you are looking at the v10 window.

1. **Open the wizard.** Click the **+ Create profile…** button in the
   Mutation Panel (right side of the window, under the depth slider).
   The cockpit navigates to `#/wizard` (the wizard surface lives behind
   the hash router mounted in `App.tsx`) and shows the four-step
   indicator at the top: **Name · Add · Analyze · Review**.

2. **Step 1 — Name.** Type a profile name (e.g. `buzzi`), an optional
   description (e.g. `industrial-leaning hypnotic techno`), and an
   optional color tag. Click **Next** to advance. The cockpit's
   sidecar emits a `wizard_state_changed` event so the step indicator
   updates immediately.

3. **Step 2 — Add inspiration sources.** Click the per-kind add
   buttons (`+ kit`, `+ sound`, `+ song`, `+ album`, `+ artist`) to
   build a source list. For the worked example below, add three
   sources:

   - `+ kit` → opens a Tauri folder picker → pick a folder of `.syx`
     kit dumps (the wizard reads every supported Rytm kit it finds).
   - `+ song` → opens a Tauri file picker → pick one audio file
     (`.wav`, `.mp3`, `.flac`, `.aif`, `.aiff`).
   - `+ artist` → opens a plain text input → type a reference name
     (`Surgeon`, `Daniel Avery`, etc.). The built-in lookup table maps
     20 known names to trait profiles; unknown names contribute a
     neutral, low-confidence trait set.

   Each added source appears in the list with a remove (×) affordance.
   Add as many sources as you like, in any order. Click **Next** when
   the list looks right.

4. **Step 3 — Analyze.** Click **Analyze**. The wizard runs each
   source through the analysis pipeline on a worker thread and emits
   one `analysis_progress` event per source as it advances:

   - Audio file / folder → existing `style_analysis.extractor` produces
     a `FeatureReport`, then the wizard's `feature_report_to_traits`
     mapper converts the report into a tuple of `StyleTrait`s.
   - SysEx file / folder → `sysex_analyzer.extract_kit_traits` parses
     the kit dump with the shared `snapshot/envelope.py` helpers and
     derives per-pad parameter statistics that map to traits.
   - Reference text → `reference_analyzer.lookup_traits` consults the
     built-in lookup table.

   The Analyze step shows one progress bar per source; jobs go from
   `pending` to `analyzing` to `ok` (or `failed` with a fix
   affordance: retry, remove, or replace). When every job reaches a
   terminal state, the **Review** button enables. Failures here are
   recoverable — fix the source and re-analyze without restarting the
   wizard.

5. **Step 4 — Review.** Click **Review**. The wizard's
   `ProfileBuilder` aggregates the OK jobs' traits by weighted
   average, normalizes to 0..1, and assembles a candidate
   `ProfileModel`. The Review step renders:

   - The derived `StyleTrait` bars (the same shape the cockpit's
     reference panel uses).
   - The `TraitPadWeight` mapping table, derived from the built-in
     `TRAIT_TO_PAD` table (standard mapping is
     `rolling_low_end → Pad 1`, `metallic_tension → Pad 2`,
     `hat_density → Pad 3`, `filter_motion → Pad 4`).
   - A source summary line (e.g. `5 sources, 1,243 analyzed signals`).
   - A rename / description-edit affordance plus a **Back to Analyze**
     button if you want to add more sources or re-analyze.

6. **Step 4 (continued) — Save.** Click **Save**. The wizard writes
   the new profile to `~/.rytm-randomizer/profiles/<id>.json` via the
   existing `ProfileRegistry.save(profile)` call, then emits both
   `profile_created` (the wizard's confirmation) and `profile_changed`
   (the cockpit's existing active-profile event). The hash route flips
   back from `#/wizard` to the cockpit root and the new profile chip
   appears in the `ProfileChips` strip, already selected as the active
   profile and ready to drive with the depth slider.

7. **Verify the round-trip.** Slide the depth knob, watch the ghost
   overlay update against the trait weights you just authored, and
   hit **REGEN** for a new candidate at the same depth. Hit **SEND**
   to apply the candidate (the mock device adapter records the
   message internally; the armed path is gated behind an explicit
   arm step per §6 below).

If you want to abandon a wizard in flight, the **Cancel** button on
any step emits `wizard_cancel`, drops the in-flight `WizardSession`,
and returns you to the cockpit with no profile written.

---

## 6. Connecting to real hardware

The cockpit defaults to a **mock device adapter**: it opens no MIDI port
and sends no MIDI, even when you hit SEND. This is the same passive-
default discipline the rest of the project uses.

The real-MIDI path is gated behind an explicit arm step (configured per
release; the design ships a tray menu item plus a settings surface). On
the back end, arming swaps the `MockDeviceAdapter` for a
`RealMidiDeviceAdapter` that wraps the existing
`rytm_randomizer.mido_provider` and `rytm_randomizer.real_midi_adapter`
boundary — the same path the armed CLI uses.

**Hardware rules that do not change:**

- `mido==1.3.3` and `python-rtmidi==1.5.8` are pinned. Do not bump.
- The MIDI port is opened once, when you arm; it stays open until you
  close the window or explicitly disarm.
- Locked pads are skipped on SEND. Use this to protect your kick.
- SAVE writes a Rytm SysEx kit dump to the device's persistent kit
  memory. Pick the label and slot deliberately.

---

## 7. Troubleshooting

**"Cockpit WebSocket server listening on 127.0.0.1:4317" but the window
shows "Connecting..."**

The Tauri shell did not pick up the sidecar. Make sure the port matches:
if you set `RYTM_RAND_WS_PORT=4318` for the sidecar, set the same env
var before launching the shell. On Windows PowerShell:
`$env:RYTM_RAND_WS_PORT='4318'; cargo run`.

**`cargo build` fails with a `libwebkit2gtk-4.1-dev` error on Linux**

Tauri 2 needs `webkit2gtk-4.1`. Install the dev package per §1 above;
some distros still ship `webkit2gtk-4.0` only — install both if the
package manager allows.

**`npm install` reports `node-gyp` errors**

You're on Node < 20. Upgrade — the project pins Node 20 LTS for its
ECMAScript and tooling baseline.

**Port 4317 is already in use**

Set `RYTM_RAND_WS_PORT=<free port>` before launching both the sidecar
and the shell, or kill the process holding 4317 (`lsof -i :4317` on
macOS / Linux; `Get-NetTCPConnection -LocalPort 4317` on Windows).

**Sidecar crashes on connect with "no profiles found"**

The first launch generates `~/.rytm-randomizer/profiles/` and writes the
seven built-in scenes. If something previously emptied the directory,
delete it and restart the sidecar — it re-creates the defaults.

**The window opens but no pad state shows**

The default `MockDeviceAdapter` returns a clean Snapshot on connect, so
this is unexpected. Check the sidecar logs (visible in the spawning
terminal); a Python traceback there is the most useful diagnostic. File
an issue with the traceback attached.

**I want a Tauri development workflow with hot reload across both layers**

Tauri 2 supports `tauri dev`, which spawns the Vite dev server and
hot-reloads both the frontend and the Rust shell on changes. Install
`@tauri-apps/cli` (`npm install -D @tauri-apps/cli` inside
`desktop/web/`) and run `npx tauri dev` from `desktop/web/`. The Vite
dev server, Rust hot-reload, and the sidecar all spin up together.

---

## Reference

- [`docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md`](superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md) — full Phase 1 cockpit design spec (events, commands, profile model, mutation engine, phasing).
- [`docs/superpowers/plans/2026-05-23-cockpit-and-profile-model.md`](superpowers/plans/2026-05-23-cockpit-and-profile-model.md) — 12-workstream Phase 1 parallel implementation plan.
- [`docs/superpowers/specs/2026-05-24-profile-wizard-design.md`](superpowers/specs/2026-05-24-profile-wizard-design.md) — Phase 2 Profile Wizard design spec (wizard flow, data abstractions, analyzers, ProfileBuilder).
- [`docs/superpowers/plans/2026-05-24-profile-wizard.md`](superpowers/plans/2026-05-24-profile-wizard.md) — 7-workstream Phase 2 parallel implementation plan.
- [`docs/ARCHITECTURE.md` §6.2](ARCHITECTURE.md#62-cockpit--profile-model-layer-phase-1) — where the Phase 1 cockpit fits in the package architecture.
- [`docs/ARCHITECTURE.md` §6.3](ARCHITECTURE.md#63-profile-wizard-layer-phase-2) — where the Phase 2 Profile Wizard fits in the package architecture.
- [`docs/ARCHITECTURE_DIAGRAMS.md` §28 + §29](ARCHITECTURE_DIAGRAMS.md#28-cockpit--profile-model-c4-component-diagram-phase-1) — Phase 1 C4 component diagram and SEND command sequence diagram.
- [`docs/ARCHITECTURE_DIAGRAMS.md` §30 + §31](ARCHITECTURE_DIAGRAMS.md#30-profile-wizard-sequence-name--add--analyze--review--save-phase-2) — Phase 2 wizard sequence diagram and component diagram.
- [`CONTRIBUTING.md` § Cockpit / desktop development](../CONTRIBUTING.md#cockpit--desktop-development) — developer setup, build commands, dev-loop tips.
