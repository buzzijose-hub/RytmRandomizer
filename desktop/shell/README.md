# RytmRandomizer Cockpit — Tauri shell

The desktop shell for the **Cockpit & Profile-Model (Phase 1)** UI. It is a
minimal Tauri 2 application that:

1. Opens **one window** (1440x900) that loads the web frontend from
   `../web/dist/index.html`. If the web build is missing, Tauri's built-in
   404 surface is shown — this is intentional so the operator immediately
   knows the frontend hasn't been built.
2. Spawns and **supervises** the Python sidecar
   (`python -m rytm_randomizer.app --arm --cockpit-kit-capture-sidecar`) that
   hosts the WebSocket server, input-only current-KIT capture, mutation engine,
   profile registry, and mock state adapter. Output remains separately armed.
3. Exposes a **system tray** with a single `Quit` menu item that shuts down
   the app cleanly.

The Rust surface is deliberately small (~80 LOC of behavior — sidecar
supervision + window plumbing + tray). All business logic lives in the
Python sidecar (workstreams A-G) and the web frontend (workstreams I-J).

See `docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md`
for the design and
`docs/superpowers/plans/2026-05-23-cockpit-and-profile-model.md` §3 WS-H for
the workstream contract.

## Layout

```
desktop/shell/
├── Cargo.toml            # Rust dependencies (tauri 2, tauri-plugin-shell, env_logger, nix on unix)
├── build.rs              # Tauri build-time entry; calls tauri_build::build()
├── tauri.conf.json       # Window 1440x900, tray icon, frontendDist = ../web/dist
├── icons/icon.png        # 256x256 placeholder for tray/dev surfaces — replace before release
├── icons/icon.ico        # Windows bundle/resource icon required by tauri-build
├── src/lib.rs            # Library root exposing the sidecar module for unit tests
├── src/sidecar.rs        # Sidecar spawn + shutdown + backoff math (with tests)
└── src/main.rs           # Tauri entry: window + tray + supervisor thread
```

## Sidecar supervision

Implemented in `src/sidecar.rs` and orchestrated by the supervisor thread in
`src/main.rs`.

- **Spawn:** `python -m rytm_randomizer.app --arm
  --cockpit-kit-capture-sidecar` inherits stdout/stderr so
  Python logs flow to the shell's console.
- **Restart on crash:** the supervisor thread polls the child every 250 ms;
  when it exits, the thread waits `backoff_delay(failures)` and respawns.
- **Backoff:** `1s, 2s, 4s, 8s, 16s`, capped at `16s` per `backoff_delay`.
  The failure counter resets to zero after the sidecar has stayed up for at
  least `BACKOFF_RESET_SECS` (60 s) of clean uptime.
- **Shutdown on window close (or tray Quit):** the supervisor sets its
  shutdown flag, then `shutdown_child` sends `SIGTERM` (Unix) or the
  Windows-equivalent terminate via `Child::kill` after the 5 s grace window,
  waits up to `SHUTDOWN_GRACE_SECS` (5 s) for the child to exit, then
  `SIGKILL`s if it is still alive.

The backoff calculation is a pure function (`backoff_delay`) and is
unit-tested in `src/sidecar.rs`.

## Build and dev

### Prerequisites

- **Rust toolchain** — install via [rustup](https://rustup.rs/). MSRV is
  Rust 1.88 (see `Cargo.toml` `rust-version`), matching the current Tauri 2
  transitive dependency graph resolved by Cargo.
- **Cargo resolver pins** — `Cargo.toml` currently pins the
  `brotli-decompressor` / `alloc-stdlib` / `alloc-no-stdlib` bridge because
  fresh 2026-06-14 `brotli` transitive releases can otherwise resolve
  incompatible 2.x/3.x allocator traits before the shell's own Rust code
  compiles.
- **Tauri 2 system deps** — see
  [tauri.app prerequisites](https://v2.tauri.app/start/prerequisites/) for
  per-OS native dependencies (WebView2 on Windows, webkit2gtk on Linux).
- **Python 3.11+** on the `PATH` (the supervisor invokes `python`).
- **Web frontend built** — `cd ../web && npm install && npm run build` so
  `../web/dist` exists.

### Commands (from `desktop/shell/`)

```bash
# Format check + lint + tests + debug build
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
cargo build

# Release build
cargo build --release
```

### CI verification

GitHub Actions runs the shell in the `desktop-shell` job on Windows with
Rust 1.88:

- `cargo fmt --check`
- `cargo test`
- `cargo clippy --all-targets -- -D warnings`

Run the same commands locally before changing the shell. Install Rust on
Windows via:

```powershell
winget install --id Rustlang.Rustup
rustup toolchain install 1.88.0
rustup default 1.88.0
```

Then re-run the verification commands from `desktop/shell/`.

## Tray

The tray icon uses `icons/icon.png` (256x256 PNG). Windows bundle/resource
generation also requires `icons/icon.ico`; both assets are declared in
`tauri.conf.json` and guarded by the architecture tests. The only menu item
is `Quit`, which calls the same shutdown path as the window-close handler:
flips the supervisor's shutdown flag, sends `SIGTERM` to the sidecar, waits
5 s, then `SIGKILL`s and exits Tauri with code 0.

## Replacing the placeholder icon

Generate or drop in a real 256x256 PNG at `icons/icon.png` and a matching
Windows ICO at `icons/icon.ico` before any release build. The current
placeholder is a solid navy background with a cyan accent square — adequate
for local dev, not adequate for distribution.

## Cross-references

- Spec: `docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md`
- Plan: `docs/superpowers/plans/2026-05-23-cockpit-and-profile-model.md` §3 WS-H
- Web frontend: `desktop/web/` (WS-I scaffold, WS-J cockpit UI)
- Python sidecar: `rytm_randomizer/cockpit/` (WS-A through WS-G)
