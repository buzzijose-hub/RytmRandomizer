# Building native end-user installers

RytmRandomizer ships as both a `pip`-installable package **and** as native
end-user installers (`.msi` on Windows, `.pkg` on macOS, `.deb` / `.rpm` /
AppImage on Linux). The installer story is owned by
[BeeWare briefcase](https://briefcase.beeware.org/) and lives entirely in
`[tool.briefcase.*]` tables in `pyproject.toml` plus this guide.

This document is for the **release engineer** — the human (or CI job) that
builds and ships an artifact. End users never see this; they just download
the right file for their OS.

---

## TL;DR — the 4-step briefcase flow

From a clone of the repo, with the `installer` extra installed:

```bash
pip install -e ".[installer]"

briefcase create     # 1. scaffold per-OS build dirs under build/
briefcase build      # 2. compile + freeze into a native app skeleton
briefcase package    # 3. wrap into a distributable artifact (.msi/.pkg/AppImage)
briefcase run        # 4. (optional) launch the built artifact to smoke-test
```

The output artifacts land under `dist/` once `briefcase package` finishes.

You run these on **the same OS as the target installer**. See the
"Cross-OS caveat" section below.

---

## Cockpit / wizard desktop bundle

Briefcase ships the **Python CLI sidecar only**. It does not include the
React cockpit, the Profile Wizard, or any of the `desktop/` tree —
those are a separate artifact lineage with their own build tool and
their own per-OS output.

The Cockpit GUI (and therefore the Phase 2 Profile Wizard layered on
top of it) ships as a **Tauri 2 bundle**, built from `desktop/shell/`.
That bundle is the only way an end user gets the wizard surface; the
Briefcase `.msi` / `.pkg` / `.deb` / AppImage carry the passive CLI,
armed runtime, and Python sidecar dependencies, but nothing from the
React/Tauri GUI tree.

### Local build

```bash
npm --prefix desktop/web ci
npm --prefix desktop/web run build
cd desktop/shell
cargo install tauri-cli --version "^2"
cargo tauri build
```

The `just desktop-bundle` recipe wraps the same steps for local builds
and CI parity. The recipe and the manual block produce identical
output.

The first `cargo tauri build` on a cold Rust cache is multi-minute;
subsequent builds finish in seconds because `desktop/shell/target/`
is cached.

### Per-OS artifacts

Tauri writes per-OS installers under
`desktop/shell/target/release/bundle/`:

| OS | Artifact path under `bundle/` |
|---|---|
| Windows | `msi/RytmRandomizerCockpit_<version>_x64_en-US.msi` (plus a `nsis/` `.exe` if NSIS is configured) |
| macOS | `dmg/RytmRandomizerCockpit_<version>_x64.dmg` and `macos/RytmRandomizerCockpit.app` |
| Linux | `deb/`, `rpm/`, and `appimage/` subdirectories |

These are GUI installers (the operator double-clicks the file), unlike
the CLI-oriented Briefcase artifacts. They embed the web frontend from
`desktop/web/dist/` and they expect the Python sidecar's
`python -m rytm_randomizer.cockpit` entry point to be reachable on PATH
at launch time - typically because the operator has also installed the
Briefcase artifact, or has an editable `pip install -e ".[cockpit]"`
or `pip install -e ".[dev]"` checkout active.

### Runtime supervision

The Tauri bundle is a process supervisor. When the operator launches
the cockpit binary, the Rust shell in `desktop/shell/src/main.rs`:

1. **Allocates a per-launch token file path** under the user's data dir
   (e.g. `%APPDATA%\rytm-randomizer\cockpit-ws-token` on Windows,
   `~/Library/Application Support/rytm-randomizer/cockpit-ws-token` on
   macOS, `~/.local/share/rytm-randomizer/cockpit-ws-token` on Linux).
   This path is owned by the user-private app data dir; the shell creates
   the parent directory with platform-appropriate permissions.
2. **Sets `RYTM_RAND_WS_TOKEN_FILE` in the sidecar's environment** to
   the path from step 1 BEFORE spawning the sidecar. This is REQUIRED
   for the cockpit to work post CODE_REVIEW.md sweep (PR 1): the sidecar
   mints a fresh token on every boot, writes it to the path the env var
   names, and refuses every WS command until the first frame echoes the
   token under `hmac.compare_digest`. A shell that fails to set the env
   var falls back to the dev-default `~/.rytm-randomizer/cockpit-ws-token`,
   which still works but is not the production-recommended path.
3. Optionally sets `RYTM_RAND_WS_PORT` (default 4317) and
   `WIZARD_SOURCE_ROOTS` (default `~/.rytm-randomizer/wizard-sources/`)
   per the operator's preferences.
4. Starts the embedded web frontend in the Tauri window.
5. Spawns the Python sidecar (`python -m rytm_randomizer.cockpit`) as
   a child process with the env from steps 2–3 applied.
6. **Reads the token back from the same file** (the sidecar has now
   written it) and hands it to the web frontend via Tauri's IPC so the
   first WS frame the React client sends can be
   `{"type": "hello", "token": "<urlsafe>"}`.
7. Bridges the two over WebSocket on `127.0.0.1:<port>` (default 4317),
   negotiating the subprotocol `rytm-rand-cockpit-v1` (defence-in-depth
   on top of the token).

When the window closes, the shell terminates the sidecar and removes
the per-launch token file (the file mode is `0o600` on POSIX; on Windows
the user-private app data dir already restricts access). The operator
never has to manage the sidecar lifecycle directly — the bundle owns
both halves.

**Why the env var is mandatory for a release bundle:** the dev default
prints the token to stdout for interactive copy-paste. A bundled
release has no stdout the operator sees, so the only way for the Tauri
shell to learn the token is to set the env var, spawn the sidecar, and
read the file the sidecar writes to that path. A shell that skips this
step ships a sidecar the cockpit window cannot connect to.

**Phase 3 export CLI is shipped inside the same Tauri bundle.** The
Phase 3 Model Export Pipeline (`cockpit-export-profile-model` plus the
passive `cockpit-export-rehearsal-report`; see
[`docs/superpowers/specs/2026-05-24-phase-3-export-pipeline-design.md`](superpowers/specs/2026-05-24-phase-3-export-pipeline-design.md)
and [`docs/COCKPIT_QUICKSTART.md` §5c](COCKPIT_QUICKSTART.md#5c-exporting-a-profile-for-hardware))
adds no new system dependency — HMAC + SHA-256 + CRC32 are stdlib and
MessagePack is already a Phase 1 dependency. Both CLI entry points run
through the same Python sidecar that powers the cockpit, so launching
the export from inside the Tauri shell uses the bundled sidecar's
`python -m rytm_randomizer.cli cockpit-export-profile-model ...` entry
without spawning a second interpreter. Operators who installed only the
Briefcase CLI artifact (no GUI) get the same export entry on PATH; the
bundle and the CLI artifact share the export pipeline byte-for-byte.

### CI

`.github/workflows/installers.yml` has a `desktop-bundle` matrix job
that runs the four-step build on every release (per OS) and uploads
the per-OS artifacts. The artifacts are attached to each GitHub
Release alongside the Briefcase outputs, so an operator picks the file
for their OS regardless of which lineage they want.

Two CI path details are deliberate:

- The Linux Briefcase job installs into a `.venv-briefcase` virtualenv
  created by the runner's system `python3`. Briefcase Linux system
  package builds compare their interpreter against the host `python3`;
  using `actions/setup-python` on Linux exits before `briefcase create`.
- The Tauri `beforeDevCommand` and `beforeBuildCommand` use
  `npm --prefix web ...`. Tauri resolves those commands from
  `desktop/`, so `../web` points at the repository root's missing
  `web/package.json` instead of `desktop/web/package.json`.

---

## Per-OS prerequisites

### Windows (`.msi`)

| Requirement | Why | How |
|-------------|-----|-----|
| Python 3.10+ | Briefcase itself | [python.org](https://www.python.org/) installer |
| **WiX Toolset v3** | briefcase shells out to WiX to produce the `.msi` | `dotnet tool install --global wix` *or* [WiX 3 installer](https://github.com/wixtoolset/wix3/releases) — briefcase will print the install command if missing |
| .NET 6+ runtime | WiX's modern host | Bundled with most Windows 11; otherwise install from Microsoft |
| Git | source checkout | any reasonable distribution |

Briefcase's first `briefcase build windows` run will detect a missing WiX
and print the exact `dotnet tool install` command — follow it, re-run.

### macOS (`.pkg`)

| Requirement | Why | How |
|-------------|-----|-----|
| Python 3.10+ | Briefcase itself | python.org installer (system Python is too old / unstable) |
| **Xcode Command Line Tools** | `codesign`, `pkgbuild`, `productbuild`, native compilers for `python-rtmidi`'s C extension | `xcode-select --install` |
| `codesign` Developer ID certificate | mandatory for distribution outside the Mac App Store (otherwise Gatekeeper blocks the install) | enrol in the Apple Developer Program (\~\$99/yr), provision a "Developer ID Application" + "Developer ID Installer" cert in Apple Developer portal, install into login keychain |
| Apple notarization credentials | required since macOS Catalina for non-MAS distribution | `xcrun notarytool store-credentials` with an app-specific password |

RytmRandomizer's `[tool.briefcase.app.rytm-randomizer]` declares
`console_app = true`. On macOS this **forces the `.pkg` output format** —
a `.app` bundle is GUI-only by spec, and Apple's Launch Services will
not give a `.app` a usable stdin/stdout terminal. The `.pkg` installer
drops a `rytm-randomizer` binary into `/Applications/RytmRandomizer` (or
similar) and registers a CLI launcher; the user opens Terminal and runs
`rytm-randomizer`. Briefcase handles that wrapper for us.

### Linux (AppImage / `.deb` / `.rpm`)

| Requirement | Why | How |
|-------------|-----|-----|
| Python 3.10+ | Briefcase itself | distro package manager |
| **Docker** | Briefcase builds Linux artifacts inside `manylinux` containers for portability | `apt install docker.io` / equivalent, plus add your user to the `docker` group |
| ALSA runtime (`libasound2t64` on Ubuntu 24.04+) | Briefcase's Linux system-package dependency check requires the runtime shared-library package on the host | `apt install libasound2t64` on current GitHub-hosted Ubuntu runners; older distros may still use `libasound2` |
| `libfuse2` | required to **run** an AppImage on the build host (the AppImage filesystem is FUSE-based) | `apt install libfuse2` on Debian/Ubuntu (the package was split out of the default install in Ubuntu 22.04+) |
| ALSA dev headers (`libasound2-dev`) | `python-rtmidi`'s C extension links against ALSA. Already declared in `pyproject.toml` `system_requires`, but the briefcase build container needs Docker to fetch them | n/a — handled by briefcase |
| `appimagetool` | only required if building AppImages **outside** Docker | most users won't need this; let briefcase run the Docker path |

Briefcase officially **discourages AppImages** for distribution (the
project's own docs flag binary-wheel quirks and recommend system
packages or Flatpaks). RytmRandomizer ships AppImage anyway because it
gives non-technical Linux users a single-file download that
"just runs" without adding a third-party apt/dnf repo. If the AppImage
build breaks on a release, fall back to `.deb` + `.rpm` (also produced
by briefcase via `tool.briefcase.app.rytm-randomizer.linux.system`) and
document the loss for that release.

---

## Cross-OS caveat (READ BEFORE A RELEASE)

**Briefcase must build each OS's artifact ON that OS.** You cannot:

- Build a Windows `.msi` from macOS or Linux (WiX is Windows-only).
- Build a macOS `.pkg` from Windows or Linux (`codesign` is macOS-only).
- Build a fully native Linux `.deb` from Windows without a Linux VM.

To ship all three artifacts for a single release tag, you have two options:

1. **Manual per-OS builds.** The release engineer keeps a machine of each
   OS (or VMs / cloud instances) and runs `briefcase package` on each in
   turn, then uploads the three artifacts to the GitHub Release.
2. **CI matrix.** `.github/workflows/installers.yml` runs the 3-OS matrix
   on tag push and on `workflow_dispatch`, and uploads each artifact as a
   workflow artifact. The release engineer downloads, signs, and uploads
   to the Release. **This is the recommended path.**

The installer workflow is **not** a required check on PRs — installer
builds take \~20 minutes per OS and don't add signal on day-to-day
changes. The existing `test` / `e2e` / `architecture` jobs continue to
gate PRs. The installer job runs only on `v*` tags and manual dispatch.

---

## Signing

**Required before public release.** Unsigned `.msi` / `.pkg` artifacts
trigger SmartScreen / Gatekeeper warnings that look identical to malware
to a non-technical end user. Signing is also a hard requirement for
Apple notarization, which is itself required for distribution outside the
Mac App Store on macOS 10.15+.

### Windows EV code signing

1. Acquire an **EV code-signing certificate** from a CA (DigiCert,
   Sectigo, etc. — \~\$300–500/yr). EV (vs. OV) is what bypasses SmartScreen
   without a "reputation" warm-up period.
2. The cert ships on a hardware HSM token (FIPS 140-2 requirement); the
   release engineer must plug the token in at sign time.
3. Add to `pyproject.toml`:

   ```toml
   [tool.briefcase.app.rytm-randomizer.windows]
   # TODO(owner): fill in once the EV cert is provisioned.
   # signing_identity = "<CA-issued subject CN>"
   ```

   Briefcase passes `signing_identity` to `signtool.exe`. The token PIN
   is prompted at sign time, not stored in repo.

### macOS Developer ID signing + notarization

1. Enrol in the Apple Developer Program. Provision two certs in the
   developer portal:
   - **Developer ID Application** — signs the `rytm-randomizer` binary.
   - **Developer ID Installer** — signs the outer `.pkg`.
2. Generate an **app-specific password** for `notarytool` from
   appleid.apple.com.
3. Store credentials once locally:

   ```bash
   xcrun notarytool store-credentials "rytm-notary-profile" \
     --apple-id "your@apple.id" --team-id "TEAMID" --password "app-specific-pw"
   ```

4. Add to `pyproject.toml`:

   ```toml
   [tool.briefcase.app.rytm-randomizer.macOS]
   # TODO(owner): fill in once the Developer ID is provisioned.
   # signing_identity = "Developer ID Application: <Name> (TEAMID)"
   # installer_signing_identity = "Developer ID Installer: <Name> (TEAMID)"
   ```

5. After `briefcase package macOS`, notarize and staple:

   ```bash
   xcrun notarytool submit dist/RytmRandomizer-*.pkg \
     --keychain-profile "rytm-notary-profile" --wait
   xcrun stapler staple dist/RytmRandomizer-*.pkg
   ```

   Briefcase 0.3.20+ runs notarytool for you if `signing_identity` is set
   and `--no-notarize` is not passed.

### Linux

AppImages and `.deb` / `.rpm` packages are not signed in the same sense.
For `.deb` and `.rpm`, distros prefer **GPG-signed** package repositories
(out of scope for briefcase; the release engineer publishes the artifacts
to a signed apt/dnf repo separately). For AppImage, optional GPG signing
is supported via the AppImageUpdate spec; we are not adopting that yet.

---

## Versioning

The version string lives in two places:

- `[project] version` — what `pip install` and PyPI see.
- `[tool.briefcase] version` — what briefcase stamps into the installer.

**They must match.** Today this is a manual edit on both lines before
tagging a release. A future improvement (good first issue) is a
pre-commit / pre-tag check that fails if the two diverge, or a release
script that bumps both. For now: when you change one, change the other,
and the `release.yml` workflow's tag-vs-pyproject check catches the
`[project]` half.

---

## Smoke-testing a local build

The first sanity check is `briefcase create` from a fresh checkout. It:

- Reads `pyproject.toml`.
- Validates the schema.
- Scaffolds a `build/rytm-randomizer/<platform>/` tree.
- Drops your source into it.

This step does **not** require WiX / Xcode / Docker. However, it
**does** require a working C compiler if any of your declared `requires`
is a source-only Python package on the briefcase-bundled Python version.
RytmRandomizer hits this because `python-rtmidi` is a C extension that
may not have a prebuilt wheel for the exact `app_packages` interpreter
briefcase bundles (Python 3.x latest on each OS). On Windows you need
MSVC build tools; on macOS the Xcode CLT covers it; on Linux briefcase
builds inside a `manylinux` container that already has GCC.

If `briefcase create` reports a TOML / schema validation failure, the
bug is in `pyproject.toml`. If it reports `metadata-generation-failed`
on `python-rtmidi` (or similar source-build failure), the bug is in
the host environment — install MSVC (Windows) / Xcode CLT (macOS) and
re-run.

`briefcase build` and `briefcase package` additionally require the
per-OS installer-toolchain prerequisites listed in the platform table
above (WiX / Xcode / Docker). A clean local dev box may legitimately
not have them; in that case rely on CI (or a dedicated release-engineer
machine).

---

## Quick reference: file map

| Path | Purpose |
|------|---------|
| `pyproject.toml` `[tool.briefcase.*]` | All briefcase config |
| `installer-assets/icon.svg` | Placeholder app icon — see `installer-assets/README.md` |
| `installer-assets/icon.{ico,icns,png}` | **Not yet committed.** Designer-supplied raster icons |
| `.github/workflows/installers.yml` | CI matrix building artifacts on `v*` tags + manual dispatch |
| `build/` | briefcase scratch dir (in `.gitignore`) |
| `dist/` | Final artifacts land here (in `.gitignore`) |

---

## Troubleshooting

- **"WiX Toolset is not installed"** — see Windows section. Briefcase
  prints the exact `dotnet tool install` command; copy/paste/run.
- **macOS: "code object is not signed at all"** — Gatekeeper is rejecting
  the unsigned binary. Either fully provision Developer ID signing
  (see above) or run with `--no-sign` for a personal-use build.
- **Linux: `Package 'libasound2' has no installation candidate`** —
  Ubuntu 24.04 exposes the runtime as the concrete `libasound2t64`
  provider. Install `libasound2t64` on current GitHub-hosted runners
  and keep `pyproject.toml` `system_runtime_requires` aligned with
  that concrete package name, because Briefcase validates the configured
  dependency list before `briefcase create`.
- **Linux CI uploads no artifact even though `dist/*.deb` exists** —
  keep the `installers.yml` Linux artifact glob as a YAML block scalar
  with one path per line. `actions/upload-artifact` treats a
  space-separated `"dist/*.AppImage dist/*.deb"` string as one missing
  path.
- **Linux: "AppImage failed to mount"** — the build host is missing
  `libfuse2`. `sudo apt install libfuse2`.
- **`briefcase create` fails with TOML error** — your `pyproject.toml`
  diverged from the briefcase schema. Run
  `python -c "import tomllib; tomllib.load(open('pyproject.toml','rb'))"`
  to confirm the TOML itself parses, then re-read the
  [briefcase configuration reference](https://briefcase.beeware.org/en/stable/reference/configuration.html).
- **`python-rtmidi` wheel build fails inside the briefcase build
  container** — the ALSA dev headers aren't present. They're declared in
  `system_requires` already, but if you've edited that section confirm
  `libasound2-dev` is listed.

---

## See also

- BeeWare briefcase docs: <https://briefcase.beeware.org/>
- `pyproject.toml` `[tool.briefcase.*]` — the live config.
- `installer-assets/README.md` — icon export checklist.
- `.github/workflows/installers.yml` — CI matrix.
- `docs/MANUAL_HARDWARE_VALIDATION.md` — the human-driven validation
  sweep that should run on a real Analog Rytm before any installer ships
  publicly.
