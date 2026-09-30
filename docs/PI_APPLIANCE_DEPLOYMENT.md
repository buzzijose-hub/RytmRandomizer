# Pi appliance deployment

The appliance presents the **same React production build and Python Cockpit**
used by the desktop application. `scripts/pi_appliance.py` packages the shared
source, serves its production assets on the existing authenticated loopback
backend, and launches Chromium in the existing Wayland graphical session.
The Tauri desktop shell remains available; no Rust ARM cross-build is needed
for this presentation path.

The declared deployment target is **Raspberry Pi OS 64-bit, Bookworm or Trixie,
with the desktop and labwc/Wayland session**, initially on a Pi 4 or Pi 5.
800×480, 480×320 and 1024×600 are layout targets, not a claim about installed
touchscreen hardware. Pi OS Lite, 32-bit images, X11 and a compositor launched
outside the graphical session are outside this initial target.

## Dependency evidence

Checked September 30, 2026 against primary documentation. Raspberry Pi documents
labwc/Wayland as the default from Bookworm onward. See
[Raspberry Pi configuration: Wayland and X11](https://www.raspberrypi.com/documentation/computers/configuration.html#switch-between-wayland-and-x11).
Debian publishes ARM64 Chromium for
[Bookworm](https://packages.debian.org/bookworm/chromium) and
[Trixie](https://packages.debian.org/trixie/chromium), and provides
[Trixie labwc](https://packages.debian.org/trixie/labwc).
The venv packages are available for
[Bookworm](https://packages.debian.org/bookworm/python3-venv) and
[Trixie](https://packages.debian.org/trixie/python3-venv).

These checks establish OS package availability. They do **not** establish an
ARM64 Python dependency build, Chromium sandbox operation, touchscreen access,
systemd session startup, ALSA MIDI access or a successful physical boot.
The target-only wheelhouse command builds against the actual target's Python
ABI and records source SHA, architecture, Python version and wheel hashes.
Hardware dependencies remain exactly
[`mido==1.3.3`](https://pypi.org/project/mido/1.3.3/) and
[`python-rtmidi==1.5.8`](https://pypi.org/project/python-rtmidi/1.5.8/).
Native wheel compilation may need the OS compiler and ALSA development headers;
Debian provides [build-essential](https://packages.debian.org/trixie/build-essential)
and [libasound2-dev](https://packages.debian.org/trixie/libasound2-dev).

## Build a source-SHA-bound package

Run in the integrated, committed checkout. The packaging command refuses
tracked changes so its source-SHA claim refers to the exact committed source.
Node follows the existing frontend `package.json` engine constraint. Use the
existing lockfile; do not generate a second frontend dependency graph.

```sh
cd desktop/web
npm ci
cd ../..
python scripts/pi_appliance.py build
python scripts/pi_appliance.py package --output output/rytm-appliance.tar
```

This creates a deterministic uncompressed tar, adjacent `.sha256`, and a
manifest covering source, production web assets, launcher and service templates.
`build` checks installed package versions against the existing npm lock, runs the
shared production build, and writes a bounded `web-build-receipt.json` containing
clean source SHA, lockfile hash and every asset hash. `package` requires that exact
receipt; missing, stale, extra or altered web assets refuse before publication.
The ordinary `npm run build` command remains useful during development; packaged
deliverables use the launcher `build` command from the final committed checkout.
Archive members have stable ordering, timestamps and modes. An archive without
wheels needs explicitly opted-in online installation. A source package is **not
an ARM64 native build**. The frontend is architecture independent; Python native
wheels still need validation on the target.

For reproducible offline installation, on an ARM64 target with the **same commit
and Python minor version** first create the wheelhouse:

```sh
python3 -m venv .venv-appliance-build
.venv-appliance-build/bin/python -m pip install --upgrade pip
.venv-appliance-build/bin/python scripts/pi_appliance.py wheelhouse \
  --wheelhouse output/arm64-wheels
```

The command downloads/builds the project's existing `[cockpit]` dependency set,
including the pinned MIDI dependencies, and writes `receipt.json` alongside the
wheels. Its source SHA and machine identity must match during packaging. Build
on a clean exact commit into a new or empty wheelhouse directory. The command
refuses leftover wheels and rechecks the source identity after building, so a
receipt cannot relabel an older build. Transfer that wheelhouse back to the packaging host if
necessary, then include it without resolving dependencies again:

```sh
python scripts/pi_appliance.py package --wheelhouse output/arm64-wheels \
  --output output/rytm-appliance.tar
```

Retain the wheelhouse receipt and OS image/version with acceptance evidence.
`npm ci` and the native wheelhouse build need network connectivity; installed
runtime assets and a complete verified wheelhouse support offline operation.
Compiler/dependency failures are blockers, not a reason to unpin hardware
packages or substitute x86 wheels.

## Install as the graphical-session user

Prepare the supported OS desktop separately. If required, the operator can
install the supported OS packages using the normal OS package manager:

```sh
sudo apt update
sudo apt install chromium python3-venv python3-dev build-essential libasound2-dev pkg-config
```

The appliance installer itself refuses root, non-ARM64 hosts and unsupported OS
codenames. It does not flash a disk, change boot files, grant groups, add udev
rules, alter GPIO, change compositor configuration or enable automatic login.
MIDI access uses the graphical user's existing ALSA/session permissions. Resolve
access problems through the OS operator's normal device policy.

Transfer the tar and matching `.sha256` file. Run the checked-in launcher from
the source checkout with a standard Python interpreter; it uses only stdlib for
installation and creates a separate runtime venv at its final release path:

```sh
python3 scripts/pi_appliance.py install --archive /path/to/rytm-appliance.tar
```

Offline is the default. Missing wheels, a mismatched Python ABI, corrupt package
bytes, missing runtime members, unsupported manifest format or insufficient disk
space fail before the active release changes. The online alternative must be
explicit:

```sh
python3 scripts/pi_appliance.py install --archive /path/to/rytm-appliance.tar --online
```

Online installation resolves the committed dependency ranges and records the
installed requirements; reproduce those bytes by retaining a target wheelhouse.
The installer validates dependencies before atomically switching `current`.
An identical release is reused; a different manifest under the same release
identity is refused. Previous releases remain available for rollback.

Default deployment locations:

| Content | Location |
|---|---|
| Immutable release and runtime venv | `~/.local/share/rytm-appliance/releases/<version>-<sha>` |
| Active/previous release pointers | `~/.local/share/rytm-appliance/current`, `previous` |
| Shared Cockpit profiles/library/Show Bank | existing `~/.config/rytm-randomizer/` |
| Chromium profile and rotating backend logs | `~/.local/state/rytm-appliance/` |
| Runtime launch credential and separate WS/ARM secrets | `$XDG_RUNTIME_DIR/rytm-appliance/` |
| User service units | `~/.config/systemd/user/` |

Persistent profile policy is shared with the desktop backend. No armed flag,
pending command, session history authority or assumption of live synchronization
is stored in a release. Replacing or rolling back code never removes user data.
Keep independent backups of user profiles and retained captures when changing
schema versions; rollback does not silently downgrade or overwrite those files.

## Start, stop and optional graphical startup

Inside the existing graphical session:

```sh
~/.local/share/rytm-appliance/current/.venv/bin/python \
  ~/.local/share/rytm-appliance/current/pi_appliance.py session-start
```

The helper imports that session's display environment into the user systemd
manager and restarts `rytm-appliance.target`. The backend binds only
`127.0.0.1:4317`. Chromium is launched with its sandbox intact and a private
profile; it visits a private `file://` launch document whose hidden POST form
authenticates the resulting production page. No secret is put in argv or URLs.
The page's history becomes `/appliance` after bootstrap.

To opt in to the user's graphical-session startup during installation, add
`--autostart`. This writes an XDG autostart entry for the same session helper.
It leaves OS boot/autologin configuration to the operator. Starting this target
from SSH without the graphical session environment will give an actionable
Wayland-session error.

```sh
systemctl --user status rytm-appliance-backend.service rytm-appliance-kiosk.service
systemctl --user stop rytm-appliance.target
systemctl --user reset-failed rytm-appliance-backend.service rytm-appliance-kiosk.service
```

Both services allow five starts in five minutes with ten seconds between
restarts. A repeatedly failing launch stops instead of looping indefinitely.
Chromium normal exits also restart in kiosk mode until the target is stopped.
After a backend restart, the kiosk detects the changed private launch credential,
closes only its own browser process group and repeats bootstrap; it never replays
an application command. Stop allows fifteen seconds for graceful shutdown, with
systemd control-group cleanup as the backstop. Existing Cockpit teardown revokes
output authority. Backend output rotates at 2 MiB with three backups; records
are bounded to 4096 characters. Remaining startup diagnostics go to the OS
journal, subject to its existing rotation and service rate limits.

## Production input and output boundaries

Default deployed startup is a **production disconnected/passive session**.
The optional `--simulation` flag is reserved for an explicitly labeled preview.
Simulation removes the server-minted ARM capability at backend composition;
neither the touch surface nor the preserved studio surface can grant it. The
launcher imports only its own checkout or verified release `src` tree, even if
the interpreter has an editable install pointing to another checkout.
To enable input-only KIT capture, invoke the same launcher with
`serve --hardware-input`; it delegates exactly to the established
`python -m rytm_randomizer.app --arm --cockpit-kit-capture-sidecar` composition.
This is an explicit launch choice. It does not auto-arm an output.

For supervised hardware-input startup, the operator can create a user-systemd
override for the backend service that replaces `ExecStart` with the existing
line plus `--hardware-input`. Keep all other arguments and service restrictions.
Then restart the appliance target and verify readiness in the UI. Every actual
output action still needs explicit UI arming and confirmation through
`ArmedApply`. A4 blocked rows remain blocked. Saved-KIT capture does not prove
the current unsaved working state, and a local send receipt does not prove that
hardware accepted or retained a value.

An input capture runs as one owned asynchronous action so the authenticated
WebSocket reader can still receive DISARM. Other mutations refuse during that
wait. DISARM, owner disconnect, last-connection teardown and connection loss
invalidate the capture generation; a late frame cannot adopt a snapshot or
restore a revoked candidate. The app-owned provider checks a cancellation event
between input polls and closes its input in `finally`. An injected provider that
lacks cooperative cancellation may finish its input-only wait at the existing
120-second timeout; its result is still discarded immediately after cancellation.
These are software checks with fake inputs, not physical timing evidence.

## Desktop-host production preview

Build the frontend above and use the repository's existing runtime environment:

```sh
python scripts/pi_appliance.py serve --web-root desktop/web/dist \
  --runtime-dir output/pi-preview-runtime --port 4317 --simulation
```

On the current Windows workspace, the reliable interpreter is
`C:/Users/Jose Buzzi/Documents/RytmRandomizer/.venv/Scripts/python.exe`.
Open the generated `output/pi-preview-runtime/launch.html` in the desktop
browser. It performs the same private POST bootstrap into the same production
`/appliance` page. This uses the explicit simulation state, `MIDI_BACKEND=off`,
no input opener and no hardware output authority. Closing the serving process
gracefully removes its launch and secret files. Windows permission protection
relies on the user's workspace ACL; POSIX runtime files use mode 0600 inside a
mode-0700 directory.

An x86 desktop preview validates software composition and layout. It is not a
Pi touchscreen, native ARM64 dependency build, ARM emulation or physical MIDI
acceptance test. Screenshots and integrated verification receipts accompany the
bundled feature closeout separately.

## Diagnostics, rollback and uninstall

```sh
python scripts/pi_appliance.py diagnose
python scripts/pi_appliance.py rollback
python scripts/pi_appliance.py uninstall
```

Diagnose reports the actual host architecture, supported OS check, Python,
Chromium/labwc/session availability, disk headroom, dependency consistency and
loopback `/health` response. It does not print authentication material. If the
backend is missing, start it; if a service is rate-limited, inspect its journal,
repair the cause and reset its failed state before restarting. Inspect the
bounded backend log under `~/.local/state/rytm-appliance/backend.log`.

Rollback validates the prior release identity, immutable file inventory, hashes,
dependencies and service templates before stopping the healthy target. It then
restores that release's service configuration, switches the active pointer,
reloads the user service manager and starts the shared target. The existing
autostart choice is preserved. It does not migrate user data
backward or replay any hardware transaction. Without a prior release it refuses.
Uninstall removes only the appliance's user service/autostart entries, retaining
release artifacts, browser profile, logs, all shared Cockpit profiles and captures.

The private credential admits the production document; the existing first-frame
WS token still gates commands. HTTP Host and exact WS Origin checks reject DNS
rebinding and foreign browser tabs. Documents are `no-store`, frame-blocked and
served under a local CSP. Assets are bounded and constrained to the production
web root; source, package manifests and secret files are never static assets.
Only a read-only health response is public on the exact loopback host.
