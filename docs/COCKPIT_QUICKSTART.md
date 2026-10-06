# Cockpit Quickstart

> **Status: integrated Cockpit operator guide.** Treat this as the launch and
> studio-rehearsal entry point. The
> [design spec](superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md)
> remains the data/protocol reference, and
> [`docs/ARCHITECTURE.md` §6.2](ARCHITECTURE.md#62-cockpit--profile-model-layer-phase-1)
> explains the package boundary.

The Cockpit is a desktop window that gives you a single-screen view of your
Elektron rig's current state and lets you generate new kits from your own
authored intelligence. Capture a current kit, select targets and locks, pick a
profile and depth, PREPARE an exact plan, confirm SEND, and audition. History
changes local state only; hardware recovery requires a manual saved-KIT reload
and fresh capture. The
whole point is to keep you at the rig, not at the laptop.

This guide gets you from a clean clone to a working cockpit window on your
machine.

---

## 0. The double-click launch (installed bundle)

If you have a CI-built cockpit bundle (the `cockpit-bundle-<OS>` artifact
from `.github/workflows/installers.yml` — `.msi`/`.exe` on Windows,
`.dmg`/`.app` on macOS, `.deb`/`.rpm`/AppImage on Linux), you don't need
any of the toolchains below. Install it, double-click the app, and the
shell does the rest:

1. **Spawns the bundled sidecar.** The bundle embeds a self-contained
   `rytm-sidecar` binary whose entry stub calls
   `rytm_randomizer.app.main(["--arm", "--cockpit-kit-capture-sidecar"])`;
   no Python install is required on your machine. A dev checkout without the
   bundled binary automatically falls back to
   `python -m rytm_randomizer.app --arm --cockpit-kit-capture-sidecar` from
   PATH (sections 1–4 below). At startup this grants only input-side KIT
   capture; output authority still requires a separate in-UI arm, exact port,
   token, and per-action confirmation.
2. **Picks a free port.** The shell uses 4317 when it's free and asks
   the OS for a free ephemeral port otherwise, passing the choice to
   both the sidecar (`RYTM_RAND_WS_PORT`) and the webview — a busy port
   can no longer brick the launch.
3. **Bridges the handshake token.** The shell sets
   `RYTM_RAND_WS_TOKEN_FILE`, reads back the per-launch token the
   sidecar mints, and injects it into the window (§2.1).
4. **Tells you when something is wrong.** If the sidecar fails to spawn
   three times in a row, the shell shows an error dialog with the
   actual OS error (and keeps retrying in the background) instead of
   crash-looping silently.
5. **Shuts down cleanly.** Closing the window sends the sidecar a
   graceful shutdown (a stdin sentinel on every OS, plus SIGTERM on
   macOS/Linux) and only hard-kills after a 5-second grace.

> **Signing is currently deferred:** the CI artifacts are unsigned dev
> builds, so expect a Gatekeeper prompt on macOS (right-click → Open)
> and a SmartScreen prompt on Windows ("More info → Run anyway"). See
> [`docs/BUILDING_INSTALLERS.md` § Signing](BUILDING_INSTALLERS.md#signing).

Power-user overrides: `RYTM_RAND_SIDECAR_BIN=<path>` forces a specific
sidecar binary; `RYTM_RAND_WS_PORT=<port>` forces a specific port.

Record the portable copy's `BUILD-MANIFEST.json` source commit and both binary
hashes before a studio session. Keep `binaries/` beside the shell. See
[Building installers: identified Windows studio copy](BUILDING_INSTALLERS.md#identified-windows-cockpit-studio-copy)
for the artifact receipt. An earlier package does not acquire newer source
safety fixes by reading this guide. PR #252 is Pi touch UI/packaging groundwork:
non-simulation APPLY is refused and deployment is on hold pending focused work.
Touch/display behavior and packaging remain unvalidated; this Windows handoff
does not validate them.

Everything below is the **developer path** — building the three layers
yourself from a clone.

The October 5 Studio source shows canonical SRC names, CC/NRPN addresses,
catalog evidence and shared-policy blockers on each pad card. Missing/protected
values remain unavailable; display metadata cannot grant SEND authority. All
CY Ride SRC controls are blocked pending saved-slot evidence. Of 29 newly
eligible fallback SRC rows, 25 remain documented-only guarded-CC7 eligible,
not physically validated. See the
[exact row audit](RYTM_MAPPING_STATUS.md#october-5-fallback-src-audit) and
[one bounded Studio rehearsal](hardware-validation/2026-09-04-show-kit-forge-studio-checklist.md#next-studio-session-one-bounded-rehearsal).
Local favorites/bank saves and exported `.show-pack` files do not save or reload
a hardware KIT; manual save, reload and fresh recapture remain separate actions.

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
| Node.js | `^20.19.0 \|\| >=22.12.0` (package engine range) | [nodejs.org](https://nodejs.org/), or use `nvm` / `fnm` |

### Tauri system prerequisites by OS

Tauri renders the frontend using the system's native WebView, which needs
a small set of platform libraries. The Tauri team maintains canonical
install instructions; the summary below is verified against the
[Tauri Prerequisites](https://tauri.app/start/prerequisites/) page.

**Windows 10 / 11**

- [Microsoft Visual Studio C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) — required for compiling the Tauri shell.
- [WebView2 Runtime](https://developer.microsoft.com/microsoft-edge/webview2/) — bundled on Windows 11; install manually on Windows 10.

Use the C++ desktop workload and Windows SDK, then open the toolchain's
Developer PowerShell for source builds. A portable copy needs WebView2, not
the compiler toolchains. Do not use an Appx listing as proof WebView2 works;
the actual packaged-window smoke is the evidence.

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

Verify the passive-only sidecar starts (this development smoke check does not
enable KIT capture):

```bash
python -m rytm_randomizer.cockpit
# Expected: "Cockpit WebSocket server listening on 127.0.0.1:4317"
# In dev mode you ALSO see: "[cockpit] WS token: <43-char urlsafe>"
# Stop with Ctrl-C.
```

If port 4317 is taken, override it:

```bash
RYTM_RAND_WS_PORT=4318 python -m rytm_randomizer.cockpit
```

The same env var configures the Tauri shell when it spawns the sidecar.

### Windows source handoff

Use the canonical operator checkout at
`C:\Users\Jose Buzzi\Documents\RytmRandomizer` only after the handoff PR is
integrated/checked out and its required software verification is recorded.
The temporary dependency-review worktree has no `.venv`; it is not the operator
launch path. Every Windows block below starts at the canonical repo root.
Rust/Tauri commands temporarily enter `desktop/shell` and return to that root.

Prerequisites are the toolchains in section 1 and an existing root `.venv`
created with Python 3.11. Create it with `python -m venv .venv` only after
`python` resolves to a real supported interpreter, not a Microsoft Store shim.
Do not run the following venv commands until `.venv\Scripts\python.exe` exists.
Install the editable dev extras there; keep `mido==1.3.3` and
`python-rtmidi==1.5.8` unchanged. These instructions do not attest that the
checkout, venv, tests or builds have been prepared by this documentation pass.

```powershell
Set-Location -LiteralPath 'C:\Users\Jose Buzzi\Documents\RytmRandomizer'
& .\.venv\Scripts\python.exe -m pip install -e '.[dev]'
& .\.venv\Scripts\python.exe -m rytm_randomizer.cockpit
```

Expected: the loopback server and launch token appear; this entry cannot
capture hardware or send MIDI. Stop with Ctrl-C before launching the shell,
which owns its own sidecar. The shell's input-capable composition is
`python -m rytm_randomizer.app --arm --cockpit-kit-capture-sidecar`; its
`--arm` spelling does not auto-arm a Cockpit output. These are operator launch
instructions, not a record that a launch or hardware action occurred.

### 2.1 The WebSocket handshake token (post CODE_REVIEW.md sweep)

Every time the sidecar boots it mints a fresh per-launch HMAC token via
`secrets.token_urlsafe(32)`. Every WebSocket client (the Tauri shell, an
integration test, a curl-driven debugger) MUST echo that token in its
first frame or the sidecar closes the connection with code `1008`
(`auth_required` / `auth_failed`). This is what stops a foreign browser
tab from driving the cockpit when you forget to close the window.

**Where the token lives:**

| Environment | Path | How the client reads it |
|---|---|---|
| Interactive dev (no env var) | `~/.rytm-randomizer/cockpit-ws-token` (mode `0o600`) | Printed to stdout when the sidecar starts; also readable from the file. |
| Production / Tauri-spawned | path set in `RYTM_RAND_WS_TOKEN_FILE` env var | Tauri sets the env var to a path it controls, then reads the file back. |

**Token lifecycle:** the token is regenerated on every sidecar restart;
the file is overwritten so a stale token cannot survive across restarts.
File mode `0o600` is best-effort on Windows (`$HOME` is already
user-private; the chmod call is harmless if it fails on platforms that
don't honour POSIX bits).

**Per-message size cap (SX1).** Inbound frames are checked against
`RYTM_RAND_WS_MAX_MESSAGE_BYTES` (default 1 MiB) BEFORE `json.loads`.
Override only if you have a legitimate reason (very large profile
exports the sidecar replays in a test); the default is generous.

**Subprotocol gate (L8).** The sidecar negotiates the subprotocol
`rytm-rand-cockpit-v1` on `accept()`. A casual `new WebSocket(url)` from
a browser tab without the subprotocol fails the upgrade before our
handler runs — this is defence-in-depth on top of the token.

**Wizard source paths (C2/H4).** The wizard's `wizard_add_source`
command validates every `location` string through `WizardPathPolicy.validate(location)`.
Paths outside the allow-list (default `~/.rytm-randomizer/wizard-sources/`,
overridable via `WIZARD_SOURCE_ROOTS` — a `:`-separated list on POSIX, `;` on
Windows) are rejected with a categorical reason that never echoes the
rejected path back over the wire. Symlinks are rejected before
`resolve()` would chase them. If your inspiration sources live elsewhere
on disk, set `WIZARD_SOURCE_ROOTS` before starting the sidecar:

```bash
# POSIX
WIZARD_SOURCE_ROOTS="$HOME/Music/inspiration:$HOME/Sounds/kits" python -m rytm_randomizer.app --arm --cockpit-kit-capture-sidecar
```

```powershell
Set-Location -LiteralPath 'C:\Users\Jose Buzzi\Documents\RytmRandomizer'
$env:WIZARD_SOURCE_ROOTS="C:\Users\you\Music\inspiration;C:\Users\you\Sounds\kits"
& .\.venv\Scripts\python.exe -m rytm_randomizer.app --arm --cockpit-kit-capture-sidecar
```

An empty or whitespace value silently falls back to the default root so
a typo never disables the policy.

---

## 3. Build the web frontend

```bash
cd desktop/web
npm install
npm run build
```

Windows, from any directory:

```powershell
Set-Location -LiteralPath 'C:\Users\Jose Buzzi\Documents\RytmRandomizer'
npm --prefix desktop/web ci
npm --prefix desktop/web run build
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
cd ../shell                     # when continuing from desktop/web above
cargo build
cargo run
```

Windows debug source launch: start the frontend in one terminal and leave no
standalone sidecar running:

```powershell
Set-Location -LiteralPath 'C:\Users\Jose Buzzi\Documents\RytmRandomizer'
npm --prefix desktop/web run dev
```

Then launch the shell in another terminal with the configured root venv:

```powershell
Set-Location -LiteralPath 'C:\Users\Jose Buzzi\Documents\RytmRandomizer'
. .\.venv\Scripts\Activate.ps1
Push-Location -LiteralPath '.\desktop\shell'
try {
    cargo run
} finally {
    Pop-Location
}
```

To compile the matching studio binaries locally, install the
`cockpit,packaging` extras at the repo root and build the sidecar before the
frontend and Tauri executable:

```powershell
Set-Location -LiteralPath 'C:\Users\Jose Buzzi\Documents\RytmRandomizer'
& .\.venv\Scripts\python.exe -m pip install -e '.[cockpit,packaging]'
& .\.venv\Scripts\python.exe scripts/build_sidecar_binary.py --output-dir desktop/shell/binaries
npm --prefix desktop/web ci
npm --prefix desktop/web run build
Push-Location -LiteralPath '.\desktop\shell'
try {
    npm exec --yes --package=@tauri-apps/cli@2.11.4 -- tauri build --no-bundle
} finally {
    Pop-Location
}
```

This is the existing studio build spelling. The identified portable artifact
and installers come from the workflow in [Building installers](BUILDING_INSTALLERS.md#identified-windows-cockpit-studio-copy),
which also applies resource/signing configuration and writes the build
manifest. The commands above alone do not assemble that portable artifact.
For a local launch, activate the venv for PATH-Python fallback or explicitly
set `RYTM_RAND_SIDECAR_BIN` to the built sidecar's absolute path before running
`desktop/shell/target/release/rytm-randomizer-shell.exe`. A bare Cargo release
build is not the identified Tauri studio build.
Build instructions are prerequisites for a later resource-approved run, not
verification performed by this documentation handoff.

`cargo run` opens the cockpit window and spawns the Python sidecar
automatically. First build is multi-minute on a cold Rust cache;
subsequent rebuilds are seconds.

For a local release executable (not a self-contained studio package):

```bash
cargo build --release
# Binary at desktop/shell/target/release/rytm-randomizer-shell.exe on Windows
```

The release binary embeds the web frontend (from `desktop/web/dist/`)
and spawns the sidecar via
`python -m rytm_randomizer.app --arm --cockpit-kit-capture-sidecar`
on your PATH — unless a bundled `rytm-sidecar` binary is
present in `desktop/shell/binaries/` (or the app resources), in which
case the shell prefers it. See
[`docs/BUILDING_INSTALLERS.md` § Bundled Python sidecar](BUILDING_INSTALLERS.md#bundled-python-sidecar-pyinstaller)
for producing that binary locally.

---

## 5. Your first profile

When the window opens you see the v10 cockpit: a Snapshot panel on the
left (your current pad state) and a Mutation Panel on the right
(profile, depth, SEND/REGEN/UNDO/SAVE).

The device rail can switch the center view between the default Analog Rytm
MKII 12-pad snapshot surface and the Analog Four MKII four-track staged
surface. The Analog Four lane supports input-only verified KIT capture, track
targets and locks, and independent coordinated stage state. Show Kit Forge may
render evidence-backed native fields for selected, unlocked A4 tracks as offline
saved-KIT candidates. Studio's canonical parameter table shows mutable and
protected fields separately; a known source value is required. This renderer
grants no output authority: **A4 SEND remains blocked**, and unpromoted native
fields, independent FIN and OXI AMP remain immutable.

The Style Crates queue also includes a passive Analog Four set-plan card. It
renders the current/up-next A4 `warehouse-arc` macro sequence from
`analog-four-oxi-macro-set-planner-report --json`, blocked A4 send actions, and
the report-owned replay command/no-MIDI safety flags so the Cockpit can show
where the A4 side will fit before any outbound A4 macro path exists.

1. **Pick a built-in scene** — the right panel lists seven shipped
   `kind="scene"` profiles (industrial, hypnotic, garage, peak_time,
   rolling, birmingham, drone). Click one to make it active.
2. **Slide the depth** — 45% is the mock-workbench default. Start at **10%**
   for the first operator-present hardware rehearsal. The ghost overlay on
   unlocked target pads previews the proposed parameter changes.
3. **Toggle PREVIEW off and on** — confirms the overlay tracks the
   active candidate.
4. **Hit REGEN** — same depth, new seed, different candidate.
5. **Hit PREPARE** — inspect the exact port (when armed), plan id, affected
   pad ids, and message count. A target/lock/profile/depth change revokes the
   plan; PREPARE again. `paired_control_precision_unverified` blocks the
   entire plan, even if other rows are single-CC-safe. Inspect the retained
   blocked plan; do not send a filtered subset or round a fractional value.
6. **Hit SEND** — mock mode applies the exact prepared plan locally. Armed
   mode opens a second confirmation dialog and requires that same current
   plan id plus `confirm: true`; the snapshot/history advance and preview
   clears only after success.
7. **SAVE is refused.** Cockpit does not claim a persistent hardware write.
   Save the kit on the instrument itself if you want to keep it.
8. **Hit UNDO** — adopts the previous snapshot as the in-memory anchor and
   revokes any candidate/plan derived from the newer state.

### 5a. Building a Show Kit Forge bank

Open **Show Kit Forge** when you want an ordered bank of paired Rytm/A4
favorites rather than a single live mutation.

1. Create or select a versioned bank, then adopt the current round-trip-
   verified Rytm and A4 captures. Their source fingerprints and recorded
   hardware slots are immutable anchors.
2. Add cue/transition/recovery notes and optional OXI project, pattern, and
   chapter labels. These OXI fields are metadata only; Cockpit sends no OXI
   command and OXI remains the sequencer.
3. Choose **Small (25%)**, **Medium (50%)**, **Large (75%)**, or a custom
   depth, plus the seed/profile and each device's targets and locks. Effective
   scope is `(targets or complete domain) - locks`.
4. Generate and compare candidate pairs. Selecting a candidate is separate
   from **Mark favorite**. For Rytm, Preview -> PREPARE -> confirmed SEND uses
   the existing exact-plan `ArmedApply` route and is labelled **Live unsaved
   hardware**. For A4, the candidate is a local scoped native saved-KIT
   artifact only; the control stays labelled **A4 SEND blocked — offline
   only**.
   Every newly generated A4 artifact is retained atomically with the paired
   recipe. The explicit retention action remains for older candidates.
   Cockpit shows its content-addressed filename, SHA-256, and byte count;
   retention grants no A4 SEND authority.
   **Review A4 preparation** revalidates the selected candidate's exact source,
   bytes, track scope and recovery evidence. An optional exact output name is
   review intent only. The report expires when the cue, capture, scope, port
   intent or session changes, and A4 SEND remains blocked even when its bytes
   verify. Physical scratch evidence and a separately verified live MIDI value
   mapping are still required; a saved-KIT Q8.8 value is not a live packet.
   With every A4 track locked, the paired A4 artifact preserves the source
   bytes exactly. Before each live Show Forge SEND, manually reload the Rytm
   source and take a fresh exact source dump through the device rail. Capturing
   clears the current candidate and prepared plan. Click **Select for audition**
   again, then **Preview Rytm**. Arm only the exact Rytm output, **Prepare exact
   plan**, acknowledge the manual source reload in the SEND form, and confirm
   that current plan once. A saved-KIT dump alone cannot establish unsaved RAM
   state.
5. Mark the chosen pair favorite. This means only “chosen in Cockpit.” It is
   not a hardware save.
6. Follow the displayed instruction: **Save on instrument, then recapture**.
   Save manually on both instruments, record each 1–128 destination slot, and
   make fresh input-only current-KIT dumps. Until recapture matches, a manual
   save is only **attested/unverified**.
   Destination slots must differ from every protected source slot for that
   device in the open workspace. A source remains available for recovery.
7. Verify the paired recaptures. This checks each favorite's promoted semantic
   projection and can advance the cue to **Verified**; it does not make the cue
   show-ready.
8. Immediately before use, capture both current KITs again and run **Run
   show-time preflight**. Only exact equality between both fresh whole-payload
   fingerprints and their retained verified-recapture fingerprints grants
   **Show-ready**. Either mismatch revokes readiness and keeps the evidence for
   recovery.
9. Retain required source/favorite evidence explicitly before export. The
   server accepts filename-safe package ids under its configured roots; paths
   never arrive over the wire. A `.show-pack` is accepted only after its
   canonical manifest, complete file set, checksums, SysEx framing, cue order,
   and recovery text all verify.

Banks and retained frames live in `show-banks/`; exported packages and import
inputs live in the sibling `show-packs/` directory. On Windows these are
under `%APPDATA%/rytm-randomizer/`, on macOS under
`~/Library/Application Support/rytm-randomizer/`, and on Linux under
`${XDG_CONFIG_HOME:-~/.config}/rytm-randomizer/`. To import, copy a complete
`<package-id>.show-pack` directory into `show-packs/` and enter its package id
in the panel. Reusing an existing package or bank id is refused; use a new
export id. Receiving a dump never automatically retains its `.syx` file.
Bank IDs allow 64 characters; package IDs allow 96. Import starts revision zero
in a new local catalog while preserving the original package manifest. This
also permits importing a valid package exported at the maximum bank revision.

Imported show packs are verified local catalogs, not audition authority. They
can be inspected, reordered, annotated, preflighted with newly dumped current
KITs, and re-exported, but an imported Rytm candidate cannot reach PREPARE or
ArmedApply. Capture fresh paired sources in Cockpit to begin a new mutation
session. Likewise, a saved `show-ready` record is historical after restart;
Cockpit requires new paired current-KIT dumps in the present process before it
shows a live show-ready grant.

`favorite`, `hardware-saved`, `verified`, and `show-ready` are deliberately
different states. **Reset Cockpit audition to source** changes only Cockpit's
in-memory source projection; it does not touch either instrument. Manually load
both immutable source slots to return the hardware. The reset clears the active
selection/live audition and current show-ready grant but preserves prior
candidate, favorite, save, and recapture evidence.

Profiles live as flat JSON files under `~/.config/rytm-randomizer/profiles/` on
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

## 5c. Exporting a profile for hardware

Phase 3 introduces the **Model Export Pipeline** — the CLI and passive
report that turn a profile from `~/.rytm-randomizer/profiles/<id>.json`
into a signed, byte-stable `.rymp` file the Phase 4 hardware loader
will read directly from an SD card or flash. The pipeline runs entirely
on your machine: it never opens a MIDI port, never makes a network
call, and uses only Python stdlib (HMAC-SHA256 + CRC32) plus the
MessagePack dependency already shipped with the cockpit. See
[`docs/superpowers/specs/2026-05-24-phase-3-export-pipeline-design.md`](superpowers/specs/2026-05-24-phase-3-export-pipeline-design.md)
for the full design.

The walkthrough below picks up where §5b ended — you have at least one
saved profile under `~/.rytm-randomizer/profiles/` and you want to ship
it as a `.rymp` file for the hardware (or for sharing).

1. **Pre-flight: rehearse the export.** Run the passive rehearsal
   report first to see exactly what bytes WOULD be written without
   actually writing anything:

   ```bash
   rytm-randomizer cockpit-export-rehearsal-report \
       --profile-id <id> \
       --profiles-dir ~/.rytm-randomizer/profiles \
       --key-id <label>
   ```

   The report prints the same panels the GUI surfaces: profile
   identity, payload length, projected signature length, key resolution
   status, and the verification result the pipeline WOULD return if the
   bytes were written and re-read. The `--json` flag emits the same
   data as deterministic JSON (sort_keys) for tooling. The report
   writes nothing, opens no MIDI port, makes no network call — it is
   passive by construction, pinned by
   `tests/architecture/test_export_pipeline_invariants.py`.

2. **Execute the export.** Once the rehearsal report says the export
   would succeed (`status: ready`), run the real CLI:

   ```bash
   rytm-randomizer cockpit-export-profile-model \
       --profile-id <id> \
       --output ~/profiles/my-profile.rymp \
       --key-id <label>
   ```

   The CLI orchestrates the full pipeline:

   - Resolves the profile from the registry (the same
     `ProfileRegistry.load(profile_id)` the cockpit uses).
   - Packs it through `pack_profile_model` to the Phase 1 binary
     format (`RYMP` magic + format version + model version +
     MessagePack payload + CRC32 trailer).
   - Signs the packed bytes with HMAC-SHA256 over `algo || 0x1f ||
     key_id || 0x1f || payload`, wrapping the result in the Phase 3
     `RYMS` envelope.
   - Writes the envelope to `--output` ATOMICALLY: a temp file in the
     same directory is fsync'd to durable storage, then `os.replace`'d
     onto the target path. The write either fully succeeds or leaves
     the target path untouched — there is no observable partial-write
     state, even across power loss.
   - Post-flight verifies the written file end-to-end. The verifier
     dispatches on the leading magic (`RYMS` -> envelope check + inner
     CRC; `RYMP` -> plain CRC; anything else -> `bad_magic`) and
     returns a typed `VerificationResult`. Never raises.

   If you do not yet have a keystore set up, the `--unsigned` flag
   writes the Phase 1 packed bytes directly (no envelope). Unsigned
   `.rymp` files carry integrity (CRC32) but not authenticity (no
   signature). A future hardware loader may refuse them; the
   recommended path is to set up a keystore (Phase 3.5) once you intend
   to ship a profile to hardware.

3. **Verify the result.** The CLI prints the verification outcome
   inline at the end of the export. A successful export ends with:

   ```text
   file written: /Users/you/profiles/my-profile.rymp
   bytes:       4_217
   signed:      yes (hmac-sha256, key_id="<label>")
   verified:    ok
   ```

   A non-zero exit code means the file was written but failed
   post-flight verification — that should never happen in normal use
   and indicates a bug the operator should report; do not trust the
   file.

4. **What the `.rymp` file is good for.** The output is the same
   format the Phase 4 hardware loader will consume. The bytes are
   stable across releases (the magic, format version, and signing
   algorithm are pinned by architecture invariants). You can copy the
   file to an SD card, share it with another operator, archive it
   alongside the source profile JSON, or feed it back through
   `cockpit-export-rehearsal-report --plan-file <path>` to inspect its
   contents without re-deriving them from the source profile. When
   Phase 4's hardware ships, the same `.rymp` will load directly from
   flash — no re-export step needed.

If you want to inspect or share a `.rymp` file you did not create, run
the rehearsal report against the file rather than the profile id. The
report will tell you which key id signed it, the signature outcome
against any key you provide via `--key-bytes`, and the profile's name +
trait set + pad-mapping summary.

---

### 5d. Offline Preparation From Original Files

Local import/recall/storage refusals distinguish missing, integrity failure,
incompatible schema, source mismatch, unsafe location, access failure and an
existing destination. Restore a complete verified package or original source;
choose a new destination ID rather than overwriting another bank. Do not treat
an unsuccessful import as a recovered hardware KIT. Refusal/cancellation leaves
the previous complete bank and favorite intact. Unexpected programming errors
remain generic and go to diagnostics instead of exposing exception details.
Generation refuses requests that omit current locks or expand current targets;
refresh the authoritative scope before retrying a stale request.
Generating choices clears the active preview and preparation; it does not
reactivate an older retained selection. Inspect a candidate and explicitly
select it or mark it as a local favorite before preparing an audition.

Keep the MIDI-off launcher selected. This procedure is software preparation,
not a hardware backup, instrument SAVE or rehearsal approval.

1. Use your backed-up original Rytm and A4 KIT `.syx` files. Place them in
   `captures` beneath the launch working directory. In Show Kit Forge, create
   a bank, choose **Import captures folder**, then **Refresh source files**.
   Select one original file per device and explicitly record source slots.
   **Adopt source files** validates exact framing, family identity and hashes;
   it does not mark either instrument connected or physically captured.
2. Choose a profile. In **Mutation parameter scope**, choose device, pad/track
   and page. Start with **Select none**, then select individual eligible rows.
   Protected rows explain their refusal. Targets and locks remain independent;
   locks always win. A4 displays exact source/native precision, not MIDI values.
3. Forge one or more Small/Large candidates with a seed. Zero depth preserves
   the source. Scope, protection and native-domain validation run before the
   proposal is generated, not by filtering a blocked send plan afterwards.
4. Expand **Compare musical changes**. Inspect exact requested fields, source
   and proposed screen/native values, source and candidate hashes, and scope.
   A4 preparation can verify these bytes but always reports output blocked.
5. Mark a local favorite, name its cue and record transition/recovery notes.
   Duplicate/reorder cues to form the bank. Original sources and generated A4
   frames are retained atomically; Rytm favorites retain exact semantic values
   and recipe, not a newly rendered Rytm hardware KIT file.
6. Export a draft local pack. Import by package ID; if the bank already exists,
   supply an unused **New bank ID** to import a separate copy. Both original
   and imported banks remain intact. Imported history is catalog-only and
   cannot authorize output. Unsupported schemas, missing/truncated frames,
   hash/family/scope mismatch and failed deterministic replay refuse the import.
7. Restart, select the bank and select the retained candidate again. Check exact
   source, profile, scope, locks, seed, depth, values and cue order. Recall is
   disarmed and requires fresh preparation. A reconnect does not re-arm or
   restore instrument RAM. Local UNDO and **Return to source** change only
   local state; hardware recovery is a manual saved-KIT reload and fresh dump.

See [field-level native evidence](A4_OFFLINE_NATIVE_FIELD_EVIDENCE.md) and
[the reproducible support inventory](DEVICE_SUPPORT_INVENTORY.md).
The next physical gate remains the separately supervised Pad 2 four-control
10% audition, DISARM, manual KIT reload and exact fresh baseline comparison.
This does not unlock general A4/BOTH sending, CY Ride SRC, paired precision,
automatic restore, hardware SAVE or Pi operation.

## 6. Connecting to real hardware

The cockpit defaults to a **mock device adapter**: it opens no MIDI port
and sends no MIDI, even when you hit SEND. This is the same passive-
default discipline the rest of the project uses.

The installed shell and development fallback start Cockpit with input-only
current-KIT reception enabled:

```bash
python -m rytm_randomizer.app --arm --cockpit-kit-capture-sidecar
```

That capture authority can list and open the input selected in **Capture
Current Kit**, but the capture flow has no output surface and cannot transmit a
request or a kit. Cockpit's separate outbound surface remains unavailable until
the operator completes the explicit arm flow described below.
Rytm and A4 frames must pass the family codec, checksum/length validation,
and an exact decode/re-encode check before becoming in-memory captures.
`session_status.capture_enabled` is the authoritative capability flag. The
ordinary passive sidecar reports `false`; the app composition above reports
`true`. `list_capture_inputs` returns a device id plus a flat
`capture_inputs: string[]` only after the operator opens the capture workflow,
and `kit_captures_changed` publishes the complete
`captures: KitCaptureResult[]` list in stable device order.

The real-MIDI path is gated behind an explicit arm step. In the cockpit
UI that means choosing the **exact** MIDI output port from the arm
dialog's selector and entering the per-launch arm token — nothing is
auto-selected, because with a Rytm and an Analog Four both connected a
guess can arm the wrong instrument.

On the back end, arming does **not** swap the device adapter. It
constructs an `ArmedApplySession` (`rytm_randomizer.senders.armed_apply`)
that opens the one real output port through
`rytm_randomizer.mido_provider`, and every armed SEND routes through that
session's `confirm()` + `apply()` lifecycle. `MockDeviceAdapter` keeps
modelling snapshot/history state throughout.

Rytm and A4 are independent lanes in the stage state. A Rytm capture, target,
lock, candidate, plan, and armed authority cannot grant A4 authority. Rytm
connection phases come from its armed-output manager; the A4 lane reflects
capture/session evidence and is not continuous independent hot-plug telemetry.
A4 live mutation and Cockpit SEND remain blocked. The 2026-08-28 captured
saved-KIT evidence establishes the legacy offline Filter 1 Frequency path:
unsigned big-endian Q8.8 over `0x0000..0x7F00`, native Track 1 offset 128, and
350-byte track stride. Do not generalize that local-file capability to another
field, to destination-slot semantics, or to hardware-send authority. The
separate legacy saved-KIT writer remains hardware-write-validated only for
Filter 2 Resonance.

The newer scoped native algorithm has its own field-level saved-format evidence
and mandatory protection policy; see [offline preparation](#5d-offline-preparation-from-original-files) and the native evidence table.
Its additional offline support does not inherit the specific F1/F2 physical
observations or unlock general A4/BOTH output.

OXI One remains beside Cockpit as owner of sequencing, notes, triggers, mutes,
and pattern motion. Cockpit owns mutation/performance intelligence, target
selection, locks, depth, preview, and exact plan confirmation. It does not
claim direct OXI hardware control.

**What an armed SEND may and may not do:** live-dial CC changes (the
device's working RAM) are sent. Writes to *saved* kits and sounds are
refused, because capture-before-write and restore are not implemented —
so the app cannot promise you can undo them. Reload the kit from the
device to discard live-dial changes.

**Hardware rules that do not change:**

- `mido==1.3.3` and `python-rtmidi==1.5.8` are pinned. Do not bump.
- The MIDI port is opened once, when you arm; it stays open until you
  close the window or explicitly disarm.
- Locked pads are skipped on SEND. Use this to protect your kick.
- SAVE is refused. It neither writes to the device nor promotes an in-memory
  snapshot, because no persistent-write plus capture-before-write restore seam
  exists. Use the instrument's own save to keep a kit on the hardware.

### 6a. Remaining operator-present studio rehearsal

**Pending, not performed by software verification.** Work in disposable
projects/KIT slots, preserve the real show project separately, use a safe
monitoring level, and keep one output path active at a time. No exhaustive
pad/track mapping rounds are requested. Use the existing blank
[studio checklist](hardware-validation/2026-09-04-show-kit-forge-studio-checklist.md)
for observations; a successful command is not a listening or recovery result.

Before connecting, review the passive support inventory from the repo root:

```powershell
Set-Location -LiteralPath 'C:\Users\Jose Buzzi\Documents\RytmRandomizer'
& .\.venv\Scripts\python.exe -m rytm_randomizer.cli device-support-inventory-report
& .\.venv\Scripts\python.exe -m rytm_randomizer.cli device-support-inventory-report --json
```

Text is a concise summary; JSON contains the canonical rows, domains,
compatibility, blockers and evidence references. A4 native locations, semantic
fields and synth MIDI controls are independent totals; its MIDI catalog also
includes track/performance controls and NRPN-only rows. Catalog coverage, native
saved-file support, live transport/precision and physical proof are separate. It
does not enumerate hardware, prepare a plan, or unlock SEND. Record the report
alongside the exact source/build identity; an older installed sidecar may not
include this new command. See [Device Support Inventory](DEVICE_SUPPORT_INVENTORY.md)
for the independent dimensions and known gaps.

Run the isolated stages in this order, stopping after each restored baseline:

| Stage | Expected result | Evidence and recovery |
|---|---|---|
| 1. Source capture, no output | Exact input selected once, one valid family frame, checksum and codec round trip pass; no auto-arm | Manually save spare sources; retain both exact `.syx` frames, slots, frame SHA-256 and distinct whole-payload fingerprints. Stop on duplicate/ambiguous input names or invalid/multiple frames; keep the prior source. |
| 2. First physical output: one Rytm Show Kit Forge audition | Pad 2 only, depth 10%, Pad 1 locked, all A4 tracks locked; one ready exact plan and one confirmed RAM-only SEND | Follow the sequence below. Record plan id/port/packets, selected-pad observation and locked/untargeted comparisons, then DISARM, manually reload source and recapture an exact baseline. |
| 3. Separate legacy A4 single-CC probe | One integer single-CC message affects the configured A4 track/parameter only; not a Forge plan | Close Cockpit first. Use the bounded probe below, record console plus front-panel/listening evidence, then manually reload the spare source and recapture. No A4/BOTH general send, recipes, paired CC, NRPN or fractional MIDI in this pass. |
| 4. A4 offline scratch return | Only the existing four Filter 1 Frequency values return after a manual hardware save | Use the fixture/hash below and checklist slot 20 precautions. Manual librarian transfer is not Cockpit SEND. Save on A4, capture fresh, check values, byte isolation and recovery; do not repeat the August 28 mapping matrix. |
| 5. Favorite/show acceptance, only after isolated gates pass | Favorite -> manual saves -> fresh semantic recaptures -> another fresh exact whole-payload preflight | Local selection, candidate retention or bank save never saves/reloads hardware. Protect source slots; keep both devices' save/recapture evidence. Either preflight mismatch blocks the pair. |

**First physical test: one Rytm candidate, one confirmation, then stop.**
The first present action is input-only source capture and exact-plan inspection.
Studio now has canonical page/parameter selection. Choose **Pad 2 rehearsal**
to include only Filter Frequency, AMP Decay, Overdrive and Reverb Send, with
other pads and all A4 tracks locked. Its physical validation on the new build
is pending. An empty parameter selection means no mutations; unselected values
remain exact before generation. A full-pad candidate is still not guaranteed
to be SEND-ready; changed paired Rytm LFO Depth blocks it as a whole.
Rytm Filter Frequency is the single CC74 control, distinct
from the blocked A4 Filter 1 Frequency live boundary. The safety rail displays
each current plan refusal, including high-risk/protected changes, mismatched
profile/source and an empty supported plan. Do not trim a blocked plan into a
subset or assume lowering depth removes every blocker.

For offline rehearsal, retain the current scoped candidate as a **local
rehearsal favorite** in the existing library. Reopen it after restarting and
compare the source identity, selected cells, locks, seed/depth and exact values.
Recall leaves output disarmed and clears prepared plans/confirmations. Prepare
again; a fresh source capture is required before any later hardware audition.
Local retention is not the refused hardware SAVE command, exported show-bank
files or a manual instrument KIT save/reload. Corrupt/newer records refuse
without resetting the prior files. A4 selection remains offline-only and does
not unlock general A4/BOTH output.

Adopt retained paired sources, set the scope in Stage 2, generate a candidate
and record its id. Manually reload the immutable Rytm source KIT, then take a
fresh matching source capture through the device rail. Capture clears the
current candidate and plan. Re-select that candidate with **Select for
audition**, then **Preview Rytm**. Arm only the exact Rytm output and use
**Prepare exact plan**; inspect its current id, port, affected pads and counts.
If any row needs an unverified paired control, the whole plan stays blocked
with `paired_control_precision_unverified`; retain the blocker and stop, even
if some other rows could be sent. Do not bypass it with the legacy probe.
When ready, acknowledge the manual source reload in the SEND form and confirm
that exact plan once. Compare the physical changes and unaffected pads, DISARM,
use **Reset Cockpit audition to source** for local state only, manually reload
the source on Rytm, and make a fresh input-only recapture. Require exact
baseline whole-payload equality plus the actual front-panel/listening recovery
observation. A saved-state dump alone cannot prove unsaved RAM restoration.
Repeat manual reload, fresh capture, selection and PREPARE for **every** later
candidate or retry, including after any send attempt or disconnect.

**Legacy A4 probe, separately operator-approved.** The existing May 29 handoff
and `app.py` define this one-message spelling. On a spare saved A4 KIT, set
Track 1's OSC1 PWM Depth to `31` and save manually first; confirm MIDI channel
1 targets that track (`--channel 0` is zero-based). At the port prompt choose
the exact intended A4 output; cancel on uncertainty. This is not the Cockpit
arm form, and `--a4-output-port` is not an option for this helper.

```powershell
Set-Location -LiteralPath 'C:\Users\Jose Buzzi\Documents\RytmRandomizer'
& .\.venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-param --parameter 'OSC1 PWM Depth' --channel 0 --value 32
```

Expected console result: `Sent exactly one A4 parameter CC message.` The helper
closes its output and exits. Separately observe only that track/parameter at
`32`, listen, then manually reload the spare source and verify `31` returns
before fresh capture. Preserve both observations even if the command succeeds.
This proves only that single integer CC in that setup, not saved-KIT offsets,
fractional/paired transport, a generated patch or A4/BOTH Cockpit SEND. See the
[legacy handoff](hardware-validation/2026-05-29-a4-live-midi-session-handoff.md).

The offline scratch file is
`tests/fixtures/analog_four_saved_kit/filter1_freq_tracks_16_25_48_50_80_75_112_25_pending.syx`,
SHA-256 `829eee0209a248012a968e96df33acd007619a0078255c4fd034b5afda3520dd`.
It addresses disposable slot 20; protect the source in another slot/project.
Expected Filter 1 Frequency values are T1 `16.25`, T2 `48.50`, T3 `80.75`,
T4 `112.25`. These are saved-file Q8.8 values, not permitted MIDI arguments.
Manually transfer, inspect/listen, save on A4, then recapture exact bytes and
verify codec, values and unrelated-byte isolation. Record any slot/header
normalization instead of claiming full-frame equality. Existing evidence is in
[the August 28 record](hardware-validation/2026-08-28-a4-filter1-frequency-saved-kit-evidence.md)
and [the pending scratch manifest](../tests/fixtures/analog_four_saved_kit/filter1_frequency_pending_scratch_validation.json).

**Stop/recovery:** cancel an unconfirmed SEND, DISARM, then close Cockpit or
stop the sidecar and manually reload the protected sources. On a transport
failure, assume partial delivery, preserve the blocker/log and never retry the
old plan. Disconnect the selected MIDI path only after disarming if transport
is wedged. Reconnect never re-arms. Providers that cannot cancel may keep the
capture input reservation for up to 120 seconds after disconnect; wait for
release before another capture or mutation. The production mido provider
supports cooperative cancellation. A cancelled/timed-out/disconnected capture
must not later replace the prior source; a passive browser disconnect or
rejected DISARM must not erase offline candidate/plan/source identity within
the same running sidecar session. Explicit local retention/bank save is needed
for durable work across restarts. Record a violation and stop; do not create it
deliberately on a live rig to fill a box.

**Evidence unlock:** the first Rytm pass supports only that scoped audition
and verified recovery. The A4 probe supports only its single integer control;
the scratch return can support review of that offline field only. General
A4/BOTH SEND still needs independently reviewed live value/destination mapping,
precision, exact-plan lifecycle and physical restore evidence. Persistent
KIT writes need an implemented, verified capture/restore route. Pi #252 is
touch UI/packaging groundwork, not live acceptance: non-simulation APPLY is
refused, deployment is on hold, and touch/display behavior and packaging remain
unvalidated pending focused work and their own physical acceptance.

Keep the build/source identity, before/after files, both hash types, capture
ids/times, kit slots, exact ports, scope/depth/seed/profile, candidate/plan ids,
packet counts, screenshots/logs, listening notes and manual-save attestations
together. Leave every unobserved result blank.

---

## 6b. Running the end-to-end suite (Playwright)

The e2e suite drives a real Chromium against the Vite dev server and a
real per-test sidecar (spawned by the fixture with an isolated config
dir — your own profiles and library are never touched).

```bash
cd desktop/web
npx playwright install chromium   # first time only
npm run e2e                       # headless run, list reporter
npx playwright test --ui          # interactive UI mode for authoring/debugging
npx playwright test e2e/no_device_journey.spec.ts   # a single spec
```

Requirements: the repo venv installed (`pip install -e ".[dev]"`),
`npm ci` done, and **port 4317 free** (the fixture spawns its own
sidecar there; stop any standalone sidecar first). The same suite runs
in CI in the `desktop-web-e2e` job.

No hardware is ever needed. Two sidecar env seams make every device
state reachable:

- `RYTM_RAND_MIDI_BACKEND=off` — MIDI discovery disabled; the UI shows
  the honest "No hardware detected" scanning state.
- `RYTM_RAND_MIDI_BACKEND=fake` — a list-only fake enumerator presents
  an Elektron-shaped port (`Elektron Analog Rytm MKII` by default;
  override with `RYTM_RAND_FAKE_PORTS="Name A,Name B"`), so the
  `listening` phase and the arm dialog's port list are testable with
  zero devices. The fake has no transmit surface — it can only be
  *listed*, never opened for output.

Both values also work for manual testing: launch the sidecar with
either env var and explore the corresponding UI state.

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

The Tauri shell handles this automatically: it picks a free ephemeral
port when 4317 is busy and passes the choice to the sidecar and the
webview. If you are running the sidecar standalone (no shell), set
`RYTM_RAND_WS_PORT=<free port>` before launching it, or kill the
process holding 4317 (`lsof -i :4317` on macOS / Linux;
`Get-NetTCPConnection -LocalPort 4317` on Windows).

**The window opens but a "sidecar failed to start" dialog appears**

The shell could not spawn the sidecar three times in a row; the dialog
shows the underlying OS error. In a dev checkout this almost always
means `python` is not on PATH for GUI-launched apps, or the project is
not installed in that Python (`pip install -e ".[dev]"`). The shell
keeps retrying with backoff — once the spawn succeeds the window
connects on its own. To point the shell at a specific bundled binary,
set `RYTM_RAND_SIDECAR_BIN=<path>`.

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
