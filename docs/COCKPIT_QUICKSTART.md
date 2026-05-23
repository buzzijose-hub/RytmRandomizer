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
| Rust | 1.75 stable | [rustup.rs](https://rustup.rs/) |
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

Authoring your own `kind="user"` profiles needs the Phase 2 Profile
Wizard, which is out of scope for this Phase 1 cockpit (it gets its own
spec). Until then, the seven built-in scenes are the starting set.

Profiles live as flat JSON files under `~/.rytm-randomizer/profiles/` on
Linux (`$XDG_CONFIG_HOME/rytm-randomizer/profiles/` is honored if set),
and platform-appropriate paths on macOS and Windows. You can hand-edit
the JSON to author profiles before the wizard ships.

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

- [`docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md`](superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md) — full design spec (events, commands, profile model, mutation engine, phasing).
- [`docs/superpowers/plans/2026-05-23-cockpit-and-profile-model.md`](superpowers/plans/2026-05-23-cockpit-and-profile-model.md) — 12-workstream parallel implementation plan.
- [`docs/ARCHITECTURE.md` §6.2](ARCHITECTURE.md#62-cockpit--profile-model-layer-phase-1) — where the cockpit fits in the package architecture.
- [`docs/ARCHITECTURE_DIAGRAMS.md` §28 + §29](ARCHITECTURE_DIAGRAMS.md#28-cockpit--profile-model-c4-component-diagram-phase-1) — C4 component diagram and SEND command sequence diagram.
- [`CONTRIBUTING.md` § Cockpit / desktop development](../CONTRIBUTING.md#cockpit--desktop-development) — developer setup, build commands, dev-loop tips.
