# Cockpit Local Testing Feedback Bundle Implementation Plan

> Status: in-flight

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn Jose's local cockpit testing transcript into one repo-appropriate, mock-safe PR that fixes the installed app connection path, clarifies the hardware boundary, expands the cockpit to the 12-pad Rytm surface, improves parameter visibility, and repairs the profile wizard's browse/analyze flow.

**Architecture:** Keep the cockpit mock-first and passive by default. The Python sidecar remains the only WebSocket command authority; the Tauri shell bridges only the per-launch token into the WebView and does not open MIDI. The React app consumes the existing snapshot/history/send-plan protocol, renders all 12 pads in one view, and surfaces command/connection feedback without changing V1.34 engine parity.

**Tech Stack:** Python FastAPI sidecar, Rust/Tauri shell, React + TypeScript cockpit web UI, Zustand stores, Vitest/Testing Library, pytest.

---

## Scope From Local Testing

This plan addresses the locally reproduced issues from the May 28 cockpit testing pass:

- Installed cockpit stuck on "Connecting..." after launch.
- Installed app cannot be trusted as the operator path because the WebView does not receive the sidecar token.
- UI made the app look like it could send hardware while it was actually mock/dry-run.
- Rytm surface showed or implied only four active pads, but the product direction requires all 12 Rytm pads.
- Pad cards exposed only tune/decay/level/filter and hid important Overbridge/manual-facing groups.
- Snapshot history was too small to act as a practical session cue.
- UI had too little connection/error logging for operators to report failures.
- Profile wizard Browse did not help in non-Tauri fallback paths.
- Profile wizard "Analyze" required a second hidden step and felt like it did nothing.

## Deliberate Boundaries

- No unattended hardware behavior.
- No real MIDI port opening from tests.
- No dependency bump to `mido` or `python-rtmidi`.
- No V1.34 parity fixture regeneration.
- No new top-level Python package.
- No stacked PR.
- The Analog Four remains visible as a staged/planned device unless a later device-strategy PR wires full Analog Four mutation/send support.
- Full per-engine, per-machine CC coverage for every Analog Rytm machine is not completed in this PR; this PR exposes the operator-facing parameter groups and richer default mock snapshot data so the UI can support the full control surface shape. The exact canonical machine-specific parameter map should land in a follow-up data/strategy PR.

## Files

- Modify `desktop/shell/src/sidecar.rs`: resolve a token file path, pass `RYTM_RAND_WS_TOKEN_FILE` into the sidecar, read the token file, and build a WebView bootstrap script that writes `window.__RYTM_RAND_WS_TOKEN__` and localStorage.
- Modify `desktop/shell/src/main.rs`: start a token-bridge thread after the main window exists, poll the token file, inject the bootstrap script, and cleanly join on shutdown.
- Modify `rytm_randomizer/cockpit/__main__.py`: expand the deterministic mock startup snapshot to carry the richer Rytm parameter groups.
- Modify `desktop/web/src/cockpit/PadCard.tsx`: render grouped parameter sections instead of a fixed four-knob row.
- Modify `desktop/web/src/cockpit/DeviceRail.tsx`: mark all 12 Rytm pads active/compatible and preserve Analog Four as staged.
- Modify `desktop/web/src/cockpit/HistoryStrip.tsx` and `desktop/web/src/cockpit/SnapshotPanel.tsx`: make history an expandable, label-rich list suitable for recall/cue use.
- Modify `desktop/web/src/cockpit/HeaderBar.tsx`, `ActionBar.tsx`, `ProfileChips.tsx`, and state/client bindings: surface connection state, command acks/rejections, and mock-vs-live send clarity.
- Modify `desktop/web/src/wizard/AddStep.tsx` and `Wizard.tsx`: improve Browse fallback and make the Add-step Analyze action actually start analysis.
- Modify `desktop/web/src/cockpit/styles.css` and `desktop/web/src/wizard/styles.css`: support the denser single-view layout without overlapping text.
- Add/update focused Vitest and pytest tests for every behavior above.

## Tasks

### Task 1: Installed Shell Token Bridge

- [x] Add Rust unit tests in `desktop/shell/src/sidecar.rs` covering token path resolution, sidecar env propagation, token trimming, missing token handling, and JS bootstrap generation.
- [x] Update `spawn_sidecar` to accept a token file path and set `RYTM_RAND_WS_TOKEN_FILE`.
- [x] Add `read_token_file`, `clear_token_file`, and `token_bootstrap_script`.
- [x] Update `desktop/shell/src/main.rs` to start the token bridge for the `main` WebView and inject the token into the WebView whenever the sidecar writes a new token.
- [x] Verify with Rust tests if Rust is installed; otherwise document that CI must run them.

### Task 2: 12-Pad Active Rytm Surface

- [x] Update `desktop/web/tests/cockpit/DeviceRail.test.tsx` so all 12 Rytm pads are active/compatible and pads 5-12 are no longer planned/locked.
- [x] Update `DeviceRail.tsx` to remove the four-pad active cap and adjust readiness summaries.
- [x] Add/update Python tests in `tests/cockpit/test_ws_main.py` proving the startup snapshot carries 12 pads and richer parameter keys.
- [x] Expand `_default_initial_snapshot()` parameters without touching V1.34 engine outputs.

### Task 3: Overbridge-Inspired Parameter Visibility

- [x] Update `desktop/web/tests/cockpit/PadCard.test.tsx` to require grouped parameter labels such as Synth, Sample, Filter Envelope, Amp Envelope, LFO, Sweep Time, Snap Amount, Hold Time, Overdrive, Delay, and Reverb.
- [x] Implement grouped parameter metadata in the cockpit web layer.
- [x] Render all populated groups on each pad card with compact knobs and fallback "not mapped" states for absent values.
- [x] Keep preview ghost overlays working for any displayed parameter key.

### Task 4: Operator Feedback and Send Clarity

- [x] Add tests that command rejections and socket status changes are visible in the operator log.
- [x] Extend the store/client binding with a bounded operator log and connection status.
- [x] Wrap key cockpit commands so errors/negative acks are logged instead of silently doing nothing.
- [x] Make the send button label/status clear that mock mode is a dry-run send, not a hardware send.

### Task 5: Snapshot History as a Left-Panel Recall Surface

- [x] Update `HistoryStrip` tests to expect an expandable list with snapshot labels, kind, via, current status, and load buttons.
- [x] Replace dot-only history with a compact expandable list.
- [x] Keep keyboard navigation and click-to-load behavior covered.

### Task 6: Wizard Browse and Analyze Flow

- [x] Update `AddStep` tests so a missing Tauri dialog opener displays a useful fallback message and keeps manual paste flow obvious.
- [x] Update `Wizard` tests so the Add-step Analyze action sends `wizard_analyze` immediately.
- [x] Implement the browse fallback message and auto-start analysis transition.
- [x] Keep retry/manual "Run analysis" behavior.

### Task 7: Verification and PR Packaging

- [ ] Run focused Vitest tests for cockpit and wizard components. Local blocker: this Windows session has Node but no `npm`, `npx`, `pnpm`, `yarn`, or installed `desktop/web/node_modules`; CI must run these.
- [x] Run focused pytest tests for cockpit sidecar startup and WebSocket/session behavior.
- [x] Run architecture tests if local environment allows.
- [ ] Run frontend typecheck/build if dependencies are present. Local blocker: same missing package manager / frontend dependency install as above.
- [x] Exact-stage only intended files, avoiding CRLF/parity noise.
- [ ] Open one PR against `modularize-v1.34` with the 18-gate checklist and this plan linked.

## Verification Notes

- `python -m pytest tests/cockpit -q -n 0` -> 1333 passed, 3 skipped.
- `python -m pytest tests/architecture/ -q` -> 546 passed, 1 warning.
- `python -m pytest -m fast` -> 4485 passed, 3 skipped.
- `python -m ruff check rytm_randomizer/cockpit/__main__.py tests/cockpit/test_ws_main.py`; `python -m black --check --target-version=py311 rytm_randomizer/cockpit/__main__.py tests/cockpit/test_ws_main.py`; `python -m isort --profile black --check-only rytm_randomizer/cockpit/__main__.py tests/cockpit/test_ws_main.py` -> passed.
- Frontend Vitest/typecheck/build and Rust unit tests were not runnable in this local session because the desktop toolchains were absent (`npm`/`npx`/`pnpm`/`yarn`/`cargo`/`rustc` not on PATH; no local `desktop/web/node_modules`).
