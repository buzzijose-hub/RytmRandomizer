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
profile and depth, PREPARE an exact plan, confirm SEND, audition, and recover
from history. The
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

Everything below is the **developer path** — building the three layers
yourself from a clone.

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

# Windows PowerShell
$env:WIZARD_SOURCE_ROOTS="C:\Users\you\Music\inspiration;C:\Users\you\Sounds\kits"
python -m rytm_randomizer.app --arm --cockpit-kit-capture-sidecar
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
targets and locks, and independent coordinated stage state. Its semantic
mutation plan remains zero-event and unsendable until saved-KIT mappings are
evidence-promoted; the lane does not add an A4 SEND path or output authority.

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
   plan; PREPARE again.
6. **Hit SEND** — mock mode applies the exact prepared plan locally. Armed
   mode opens a second confirmation dialog and requires that same current
   plan id plus `confirm: true`; the snapshot/history advance and preview
   clears only after success.
7. **SAVE is refused.** Cockpit does not claim a persistent hardware write.
   Save the kit on the instrument itself if you want to keep it.
8. **Hit UNDO** — adopts the previous snapshot as the in-memory anchor and
   revokes any candidate/plan derived from the newer state.

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
A4 captured-kit mutation remains blocked and zero-event until saved-KIT
semantic offsets, value encodings, track stride, and physical behavior are
promoted from evidence. Do not treat the existing live CC vocabulary as
saved-KIT offset evidence.

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

### 6a. Deterministic first studio rehearsal

Before launch, save the current Rytm and A4 kits into spare hardware slots.
Keep the original `.syx` captures and record their SHA-256 fingerprints.

1. Launch Cockpit and verify the stage says OXI owns sequencing and neither
   device was auto-selected for output.
2. Open **Capture Current Kit** for Rytm, select the exact input, dump the
   current kit from the hardware, and record the displayed fingerprint.
3. Select only **Pad 2** as the Rytm target and lock **Pad 2** once to prove
   the effective scope becomes empty; unlock Pad 2, then lock a different pad
   such as Pad 1. Set depth to **10%**.
4. Choose a profile, preview, and PREPARE. Record the exact output port, plan
   id, affected pad list, and message count. The affected set must contain
   Pad 2 only and must exclude every locked/untargeted pad.
5. Confirm SEND once. Audition while OXI continues to own notes/triggers. Save
   a screenshot and the Cockpit log line carrying the plan id and packet
   count. Verify Pad 1 and at least one untargeted pad against the before
   capture.
6. Recover in Cockpit with UNDO/load of the captured anchor, then reload the
   saved hardware kit. Re-capture and compare fingerprints. After any cable
   disconnect or sidecar reconnect, discard the old plan, capture again, and
   PREPARE a new plan before sending.
7. Emergency stop: close the confirmation dialog without confirming, DISARM,
   close Cockpit or press Ctrl-C on the sidecar, and reload the saved hardware
   kit. If the MIDI transport itself is wedged, disconnect the selected USB
   MIDI path only after disarming.

For the A4 mapping gap, do not send a Cockpit plan. Use one scratch kit and
capture this exact two-control matrix:

1. Filter 1 Frequency on Track 1 at 0, 63, and 127:
   `A4_T1_FILTER1_FREQ_{000,063,127}_SLOT_<n>.syx`.
2. Filter 1 Frequency at 63 on Tracks 1, 2, 3, and 4 to prove track stride:
   `A4_T{1,2,3,4}_FILTER1_FREQ_063_SLOT_<n>.syx`.
3. Amp Attack on Track 1 at 0, 63, and 127 to distinguish the second field
   offset/encoding from the track stride:
   `A4_T1_AMP_ATTACK_{000,063,127}_SLOT_<n>.syx`.

For every frame, preserve the exact original, verify codec round-trip, record
only semantic unpacked-byte diffs, infer value encoding, reload and physically
audition the intended control, and capture the returned kit. Mapping promotion
requires all five: offset, encoding, track stride, round-trip fixture, and
physical verification.

The machine-readable blocked-state contract and exact capture matrix live in
[`2026-08-26-targeted-live-kit-mutation_A4_MAPPING_GAP.json`](2026-08-26-targeted-live-kit-mutation_A4_MAPPING_GAP.json).

Studio evidence to keep together: before/after `.syx` files, SHA-256 values,
kit slots, exact port names, target/lock/depth settings, plan id, affected pad
ids, message count, screenshots, Cockpit logs, physical listening notes, and
the final capture after manually reloading the original hardware KIT. Cockpit
does not provide persistent restore.

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
