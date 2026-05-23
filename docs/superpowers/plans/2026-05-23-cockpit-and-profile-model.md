# Cockpit & Profile-Model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan. Steps use `- [ ]` checkbox syntax. This plan is structured for **maximum-parallelization autonomous execution** per `docs/PLAN_REQUIREMENTS.md` Gate 16 — twelve workstreams run concurrently in isolated worktrees, bundle into ONE pull request against `modularize-v1.34`.

**Goal:** Build the Phase 1 cockpit — Tauri+web frontend talking to a Python sidecar over WebSocket — that consumes the 24 existing `live_gui_*` declarative contracts in `rytm_randomizer/reports/` and implements the v10 UX (Snapshot panel · Mutation Panel · ghost preview · per-pad lock · snapshot history · profile selection · SEND/REGEN/UNDO/SAVE/EXPORT).

**Architecture:** Tauri (Rust) shell spawns a Python sidecar that hosts the WebSocket server, mutation engine, profile registry, and device adapter. The web frontend (React + TypeScript + Vite) renders the v10 cockpit, subscribes to the engine's typed events, and emits typed commands. The mutation engine is a pure deterministic function with two reference implementations: Python (primary) + a C-portable algorithm spec (document only in Phase 1; reference C code follows in a later spec).

**Tech Stack:** Python 3.11 (existing), FastAPI + `websockets` (new), Rust + Tauri 2 (new), TypeScript + React 18 + Vite 5 (new), MessagePack (`msgpack-python` + `@msgpack/msgpack`), Playwright (E2E, optional Phase 1).

**Source spec:** `docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md` (committed `97f0891`).

---

## 1. Scope, non-goals, and "already-built leverage"

**In scope (Phase 1):**
- Tauri shell that manages window + spawns/supervises Python sidecar
- Web frontend implementing the v10 cockpit UI
- WebSocket Protocol (events out + commands in, JSON over WS)
- Python mutation engine (pure function · deterministic PRNG · per-trait per-pad bias)
- Profile registry (load/save profiles from `~/.rytm-randomizer/profiles/`)
- Snapshot + History data model + in-memory store
- Device adapter (mock first; real-MIDI adapter wired through the existing `mido_provider`)
- Model export pipeline (MessagePack + header + CRC)
- 100% branch coverage on every touched `.py` file (Gate 1)
- Full architecture-doc + diagram updates (Gate 18)

**Out of scope:** Phase 2 Profile Wizard UI · Phase 3 standalone model-export CLI · Phase 4 hardware runtime · the actual reference C implementation of the engine (the *algorithm spec* is in scope).

**Already-built leverage (the 24 `live_gui_*` modules):** the codex agents have shipped a complete declarative GUI contract framework — `live_gui_desktop_app_plan`, `live_gui_desktop_component_contract`, `live_gui_desktop_view_model`, `live_gui_desktop_render_contract`, `live_gui_screen_contract`, `live_gui_action_reducer`, `live_gui_render_tree`, `live_gui_test_harness_contract`, plus the analyzer/capture/rehearsal/session bundle. **The implementation conforms to these contracts.** The plan treats them as authoritative specifications: the web frontend's components, props, state slices, action transitions, and test selectors are derived directly from the corresponding `live_gui_*` contract module.

---

## 2. Workstream graph

| WS | Title | Depends on | Parallel-safe with | Owner files |
|---|---|---|---|---|
| **WS-A** | Python data model + serialization | — | B,C,D,E,F,G,H,I,J,K,L | `cockpit/data/**` |
| **WS-B** | Mutation engine (Python + spec) | A | C,D,E,F,G,H,I,J,K,L | `cockpit/engine/**`, `cockpit/engine_spec.md` |
| **WS-C** | Profile registry (disk-backed) | A | D,E,F,G,H,I,J,K,L | `cockpit/profiles/**` |
| **WS-D** | History store (in-memory) | A | E,F,G,H,I,J,K,L | `cockpit/history/**` |
| **WS-E** | WebSocket server (FastAPI) | A,B,C,D | F,G,H,I,J,K,L | `cockpit/ws/**` |
| **WS-F** | Device adapter (mock + real-MIDI wiring) | A | G,H,I,J,K,L | `cockpit/device/**` |
| **WS-G** | Model export pipeline (MessagePack) | A | H,I,J,K,L | `cockpit/export/**` |
| **WS-H** | Tauri shell (Rust) | — | A,B,C,D,E,F,G,I,J,K,L | `desktop/shell/**` |
| **WS-I** | Web frontend scaffold (Vite+React+TS) | — | A,B,C,D,E,F,G,H,J,K,L | `desktop/web/**` (skeleton + tooling) |
| **WS-J** | Web frontend cockpit UI (v10) | I | A,B,C,D,E,F,G,H,K,L | `desktop/web/src/cockpit/**` |
| **WS-K** | Integration tests + WS round-trip | A,B,C,D,E,F,G | H,I,J,L | `tests/test_cockpit_*` |
| **WS-L** | Docs + diagrams (Gate 18) | — | A,B,C,D,E,F,G,H,I,J,K | `docs/ARCHITECTURE.md`, `docs/ARCHITECTURE_DIAGRAMS.md`, `docs/STATUS.md`, `README.md` |

**Parallelization:**
- **Wave 1 (parallel from t=0):** WS-A, WS-H, WS-I, WS-L — fully independent.
- **Wave 2 (parallel as soon as WS-A is `ws_done`):** WS-B, WS-C, WS-D, WS-F, WS-G — depend only on WS-A's typed data model.
- **Wave 3 (after WS-A,B,C,D):** WS-E (WebSocket server wires the engine + registry + history + commands).
- **Wave 4 (after WS-I):** WS-J (web cockpit UI builds on the frontend scaffold).
- **Wave 5 (after WS-A,B,C,D,E,F,G):** WS-K (integration tests run end-to-end on the assembled stack).

In practice the orchestrator dispatches all 12 WSes at t=0; dependent WSes block on their predecessors' `ws_done` markers in the state file.

---

## 3. Per-workstream detail

### WS-A · Python data model + serialization

- **Worktree:** `RytmRandomizer-worktrees/ws-a-data-model`
- **Branch:** `feat/cockpit-data-model`
- **Owns:** `rytm_randomizer/cockpit/data/__init__.py`, `cockpit/data/snapshot.py`, `cockpit/data/profile_model.py`, `cockpit/data/mutation_candidate.py`, `cockpit/data/history.py`, `cockpit/data/types.py`, `tests/cockpit/test_data_*.py`
- **Delivers:**
  - Frozen dataclasses per spec §"Core Data Abstractions": `PadState`, `Snapshot`, `StyleTrait`, `TraitPadWeight`, `ProfileModel`, `PadDelta`, `MutationCandidate`, `HistoryEntry`, `History`.
  - JSON round-trip serialization (`to_dict`, `from_dict`) for each.
  - `ULID` generation helper (stdlib `uuid` + base32 OK; no new dep).
  - Type tests + round-trip tests + immutability tests → **100% branch coverage** on the new module.
- **Crew:** implementer → coverage gate → reviewer.

### WS-B · Mutation engine (Python + spec)

- **Worktree:** `RytmRandomizer-worktrees/ws-b-mutation-engine`
- **Branch:** `feat/cockpit-mutation-engine`
- **Owns:** `rytm_randomizer/cockpit/engine/__init__.py`, `cockpit/engine/mutate.py`, `cockpit/engine/prng.py`, `cockpit/engine/spec.md`, `tests/cockpit/test_engine_*.py`
- **Delivers:**
  - `mutate(snapshot, profile, depth, seed) -> MutationCandidate` — pure function, deterministic.
  - `xorshift32(state) -> (value, new_state)` — the documented PRNG (in `prng.py`).
  - `engine/spec.md` — normative C-portable algorithm spec with pseudocode, value ranges, clamping rules, and a fixture-corpus reference.
  - Conformance fixtures: `tests/cockpit/fixtures/engine_conformance/*.json` — 50+ (snapshot, profile, depth, seed) → expected `MutationCandidate` tuples, used to lock the algorithm.
  - Tests covering: determinism for same seed, variation across seeds, depth-scaling, per-pad bias from `TraitPadWeight`, range-clamping, `safety_status` derivation.
- **Crew:** implementer → coverage gate → reviewer.
- **CRITICAL:** the algorithm must produce identical output across implementations. No `random.choice` on iteration-order-dependent collections; no numpy; no language-level RNG.

### WS-C · Profile registry (disk-backed)

- **Worktree:** `RytmRandomizer-worktrees/ws-c-profile-registry`
- **Branch:** `feat/cockpit-profile-registry`
- **Owns:** `rytm_randomizer/cockpit/profiles/__init__.py`, `cockpit/profiles/registry.py`, `cockpit/profiles/builtin.py`, `tests/cockpit/test_profiles_*.py`
- **Delivers:**
  - `ProfileRegistry` — load profiles from `~/.rytm-randomizer/profiles/*.json`, write new ones, list all, get by id.
  - Built-in scenes (`kind="scene"`): `industrial`, `hypnotic`, `garage`, `peak_time`, `rolling`, `birmingham`, `drone` — seven default scenes hand-crafted with reasonable trait weights (the user-curated profiles are authored via the Phase 2 wizard, which isn't in this plan).
  - `XDG_CONFIG_HOME` honored on Linux; sensible defaults on macOS/Windows.
  - Tests with `tmp_path` for filesystem isolation. **100% branch coverage.**

### WS-D · History store (in-memory)

- **Worktree:** `RytmRandomizer-worktrees/ws-d-history`
- **Branch:** `feat/cockpit-history`
- **Owns:** `rytm_randomizer/cockpit/history/__init__.py`, `cockpit/history/store.py`, `tests/cockpit/test_history_*.py`
- **Delivers:**
  - `HistoryStore` — append-only chain of snapshots with `current_id` pointer; load (sets `current_id`), undo (walks back one), promote-to-saved (with optional label).
  - In-memory only for Phase 1 (state lost on restart; persistence is a follow-up).
  - Tests covering: append-after-send, undo from various positions, load arbitrary entry, promote-current-to-saved, parent_id chain integrity. **100% branch coverage.**

### WS-E · WebSocket server (FastAPI)

- **Worktree:** `RytmRandomizer-worktrees/ws-e-ws-server`
- **Branch:** `feat/cockpit-ws-server`
- **Owns:** `rytm_randomizer/cockpit/ws/__init__.py`, `cockpit/ws/server.py`, `cockpit/ws/protocol.py`, `cockpit/ws/handlers.py`, `cockpit/__main__.py`, `tests/cockpit/test_ws_*.py`
- **Delivers:**
  - FastAPI app exposing one WebSocket endpoint `/ws`.
  - Event types: `snapshot_changed`, `mutation_previewed`, `history_updated`, `profile_changed`, `session_status` (full state per event, not deltas).
  - Command handlers per spec: `select_profile`, `set_depth`, `set_pad_lock`, `toggle_preview`, `regen`, `send`, `save`, `load_snapshot`, `undo`, `export_profile_model`.
  - Each handler wires through to WS-B/C/D/F/G as appropriate.
  - `python -m rytm_randomizer.cockpit` launches the server on `127.0.0.1:4317` (env var `RYTM_RAND_WS_PORT` overrides).
  - WebSocket round-trip tests using `websockets` test client; 100% branch coverage.

### WS-F · Device adapter

- **Worktree:** `RytmRandomizer-worktrees/ws-f-device`
- **Branch:** `feat/cockpit-device-adapter`
- **Owns:** `rytm_randomizer/cockpit/device/__init__.py`, `cockpit/device/adapter.py`, `cockpit/device/mock.py`, `cockpit/device/real.py`, `tests/cockpit/test_device_*.py`
- **Delivers:**
  - `DeviceAdapter` Protocol: `capture_snapshot() -> Snapshot`, `apply(candidate, pad_locks) -> Snapshot`, `commit_kit(snapshot, label) -> None`, `is_armed: bool`.
  - `MockDeviceAdapter` — in-memory device that the cockpit defaults to (mock-safe, no MIDI). Always-on for development.
  - `RealMidiDeviceAdapter` — wraps the existing `mido_provider` + `real_midi_adapter`; only constructed when `--arm` flag is set. **Stays in Python, never sends from CLI path** (Gate 9 invariant).
  - Tests cover both adapters' interface conformance + mock behavior; real-adapter tests use mock fake `mido` (per `tests/conftest.py` fixtures).

### WS-G · Model export pipeline

- **Worktree:** `RytmRandomizer-worktrees/ws-g-export`
- **Branch:** `feat/cockpit-export-pipeline`
- **Owns:** `rytm_randomizer/cockpit/export/__init__.py`, `cockpit/export/model_format.py`, `cockpit/export/serialize.py`, `tests/cockpit/test_export_*.py`
- **Delivers:**
  - `pack_profile_model(profile) -> bytes` — produces the versioned binary per spec §"Model Export" (magic `RYMP`, format_version, model_version, payload, crc32).
  - `unpack_profile_model(bytes) -> ProfileModel` — round-trip parser for testing + future hardware-runtime reference.
  - MessagePack serialization of the dataclass tree.
  - Tests covering: roundtrip parity, header validation, CRC mismatch detection, unsupported format_version rejection, truncated-input handling. **100% branch coverage.**

### WS-H · Tauri shell (Rust)

- **Worktree:** `RytmRandomizer-worktrees/ws-h-tauri-shell`
- **Branch:** `feat/cockpit-tauri-shell`
- **Owns:** `desktop/shell/Cargo.toml`, `desktop/shell/src/main.rs`, `desktop/shell/tauri.conf.json`, `desktop/shell/build.rs`, `desktop/shell/icons/**`, `desktop/shell/.gitignore`
- **Delivers:**
  - Tauri 2 application that opens one window, loads the web frontend from `../web/dist`, and spawns the Python sidecar (`python -m rytm_randomizer.cockpit`).
  - Sidecar supervision: restart on crash (with backoff); send SIGTERM on window close.
  - System tray with `Quit`.
  - ~80 LOC of Rust; deliberately minimal.
  - `cargo build --release` produces a single binary; cross-platform smoke test in CI (Linux only for Phase 1).

### WS-I · Web frontend scaffold

- **Worktree:** `RytmRandomizer-worktrees/ws-i-web-scaffold`
- **Branch:** `feat/cockpit-web-scaffold`
- **Owns:** `desktop/web/package.json`, `desktop/web/tsconfig.json`, `desktop/web/vite.config.ts`, `desktop/web/index.html`, `desktop/web/src/main.tsx`, `desktop/web/src/App.tsx`, `desktop/web/src/ws/**`, `desktop/web/src/state/**`, `desktop/web/src/types/**`, `desktop/web/tests/**`, `desktop/web/.eslintrc.json`, `desktop/web/.gitignore`
- **Delivers:**
  - Vite + React 18 + TypeScript 5 + Vitest setup.
  - `src/ws/client.ts` — WebSocket client wrapping `set_depth`, `send`, etc. as typed command-emitters; subscribes to `snapshot_changed` etc.
  - `src/state/store.ts` — minimal state container (Zustand or plain `useSyncExternalStore`); state is the union of latest event payloads.
  - `src/types/protocol.ts` — TypeScript types matching the Python event/command payload shapes (one-to-one with `cockpit/ws/protocol.py`).
  - Empty `<App />` displays "Connecting…" until the first `session_status` event arrives.
  - Vitest covering the WS client + store with mocked WebSocket. 100% branch coverage on `src/ws/**` and `src/state/**`.

### WS-J · Web frontend cockpit UI (v10)

- **Worktree:** `RytmRandomizer-worktrees/ws-j-web-cockpit`
- **Branch:** `feat/cockpit-web-ui`
- **Owns:** `desktop/web/src/cockpit/**` (every cockpit component), `desktop/web/src/cockpit/styles.css`
- **Delivers:** component hierarchy implementing the v10 mockup:
  - `<Cockpit />` — top-level layout
  - `<SnapshotPanel />` — left panel
    - `<PadCard />` — per-pad card with `<Knob />` ×N, `<LockButton />`, current/ghost indicator
    - `<HistoryStrip />` — bottom history dots
  - `<MutationPanel />` — right panel
    - `<ProfileToggle />` — Scene/Inspiration tabs
    - `<ProfileChips />` — `[★ buzzi] [kanye] [warehouse]` + active card
    - `<DepthSlider />` — DJ-style slider (10–90%)
    - `<ActionBar />` — PREVIEW toggle + REGEN + SEND + UNDO + SAVE
  - `<HeaderBar />` — top status strip
  - Components consume `cockpit/state/store.ts` for data; emit commands via `cockpit/ws/client.ts`.
  - Component tests with `@testing-library/react` covering interaction → command emission + rendering against mocked store. 100% branch on touched files.

### WS-K · Integration tests + WS round-trip

- **Worktree:** `RytmRandomizer-worktrees/ws-k-integration`
- **Branch:** `feat/cockpit-integration-tests`
- **Owns:** `tests/cockpit/test_integration_*.py`, `tests/cockpit/conftest.py`
- **Delivers:**
  - End-to-end flow tests against an in-process FastAPI test client:
    - Connect → receive initial `session_status`, `snapshot_changed`, `profile_changed`, `history_updated`
    - `select_profile` → `profile_changed` event
    - `set_depth` → `mutation_previewed` event (with PREVIEW on)
    - `toggle_preview` → on/off cycle
    - `regen` → new candidate with different seed
    - `send` → `snapshot_changed` + `history_updated` (auto entry)
    - `set_pad_lock` → subsequent `send` skips locked pad
    - `undo` → snapshot reverts, history pointer moves
    - `save` → history entry becomes `kind="saved"`, gets label
    - `load_snapshot` → history pointer moves to chosen entry
    - `export_profile_model` → bytes returned, round-trip parses
  - Shared `cockpit_client` fixture for spinning up the server in-process.
  - 100% branch coverage on integration code.

### WS-L · Docs + diagrams

- **Worktree:** `RytmRandomizer-worktrees/ws-l-docs`
- **Branch:** `feat/cockpit-docs`
- **Owns:** `docs/ARCHITECTURE.md` (cockpit section), `docs/ARCHITECTURE_DIAGRAMS.md` (new mermaid diagrams), `docs/STATUS.md` (recent-cleanup entry), `README.md` (cockpit quickstart), `docs/COCKPIT_QUICKSTART.md` (new), `CONTRIBUTING.md` (Tauri/web dev-loop note)
- **Delivers:**
  - New `ARCHITECTURE.md` section: "Cockpit & Profile-Model layer" describing the package layout, Protocol, mutation engine constraints.
  - Two new mermaid diagrams:
    - C4 component-level diagram: Tauri shell ↔ web frontend ↔ Python sidecar ↔ device adapter ↔ Elektron device.
    - Sequence diagram for SEND command flow (UI emits → engine validates → mutates → applies via adapter → emits events → UI re-renders).
  - `README.md` gets a "Cockpit (alpha)" section with the launch command.
  - `docs/COCKPIT_QUICKSTART.md` — operator-facing quickstart: install Rust toolchain, build Tauri, launch.
  - `STATUS.md` entry naming the plan.

---

## 4. Disjoint-file ownership matrix

| Path prefix | WS-A | WS-B | WS-C | WS-D | WS-E | WS-F | WS-G | WS-H | WS-I | WS-J | WS-K | WS-L |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| `rytm_randomizer/cockpit/data/` | ✅ |  |  |  |  |  |  |  |  |  |  |  |
| `rytm_randomizer/cockpit/engine/` |  | ✅ |  |  |  |  |  |  |  |  |  |  |
| `rytm_randomizer/cockpit/profiles/` |  |  | ✅ |  |  |  |  |  |  |  |  |  |
| `rytm_randomizer/cockpit/history/` |  |  |  | ✅ |  |  |  |  |  |  |  |  |
| `rytm_randomizer/cockpit/ws/` |  |  |  |  | ✅ |  |  |  |  |  |  |  |
| `rytm_randomizer/cockpit/__main__.py` |  |  |  |  | ✅ |  |  |  |  |  |  |  |
| `rytm_randomizer/cockpit/device/` |  |  |  |  |  | ✅ |  |  |  |  |  |  |
| `rytm_randomizer/cockpit/export/` |  |  |  |  |  |  | ✅ |  |  |  |  |  |
| `desktop/shell/` |  |  |  |  |  |  |  | ✅ |  |  |  |  |
| `desktop/web/` (top + tooling) |  |  |  |  |  |  |  |  | ✅ |  |  |  |
| `desktop/web/src/cockpit/` |  |  |  |  |  |  |  |  |  | ✅ |  |  |
| `tests/cockpit/test_data_*` | ✅ |  |  |  |  |  |  |  |  |  |  |  |
| `tests/cockpit/test_engine_*` |  | ✅ |  |  |  |  |  |  |  |  |  |  |
| `tests/cockpit/test_profiles_*` |  |  | ✅ |  |  |  |  |  |  |  |  |  |
| `tests/cockpit/test_history_*` |  |  |  | ✅ |  |  |  |  |  |  |  |  |
| `tests/cockpit/test_ws_*` |  |  |  |  | ✅ |  |  |  |  |  |  |  |
| `tests/cockpit/test_device_*` |  |  |  |  |  | ✅ |  |  |  |  |  |  |
| `tests/cockpit/test_export_*` |  |  |  |  |  |  | ✅ |  |  |  |  |  |
| `tests/cockpit/test_integration_*` |  |  |  |  |  |  |  |  |  |  | ✅ |  |
| `docs/ARCHITECTURE*.md`, `STATUS.md`, `README.md` |  |  |  |  |  |  |  |  |  |  |  | ✅ |

**Cross-WS shared files (integration phase resolves):**
- `pyproject.toml` — every Python WS may add dependencies. Resolution: union all `[project.dependencies]` additions.
- `tests/conftest.py` — WS-K may add a top-level `cockpit_client` fixture; nothing else touches it.
- `.gitignore` — WS-H, WS-I add `desktop/shell/target/`, `desktop/web/node_modules/`, `desktop/web/dist/`. Resolution: union of additions.

---

## 5. Agent crew per workstream

Each WS runs this crew in its worktree:

1. **Implementer** — works the WS detail spec → produces files + tests. Bite-sized TDD steps: write failing test → implement → run → commit. One commit per task or per logical group.
2. **Coverage gate** — runs `pytest --cov=<touched_files> --cov-branch --cov-fail-under=100 --cov-report=term-missing`. Gap → re-dispatch implementer.
3. **Lint** — `python -m ruff check .` + `black --check` + `isort --check-only` + (for Rust) `cargo fmt --check` + `cargo clippy` + (for web) `eslint` + `tsc --noEmit`.
4. **Code review** — `code-reviewer` agent against the WS branch.
5. **Doc-updater** (subset: WS-L runs as its own WS, but other WSes verify their docstrings + module-level docs are present).

A WS is `ws_done` when all five gate steps green AND the WS's own architecture-test contribution (if any) passes.

---

## 6. Self-driving decision rules

Zero `AskUserQuestion` during the run. Deterministic transitions:

| State | Condition | Action |
|---|---|---|
| `INIT` | plan kicked off | Create 12 worktrees + branches; write `STATE.json`; dispatch all 12 WS implementer crews → `RUNNING` |
| `RUNNING` | WS finished, all crew gates green | Mark `ws_done` in `STATE.json` |
| `RUNNING` | WS gate failed | Re-dispatch that WS's implementer with the failure; retry ≤ 3; on 4th failure write `BLOCKED:<ws>` + push partial state → `HALTED_AT_INTEGRATION` (let integration proceed without that WS) |
| `RUNNING` | all 12 `ws_done` | → `INTEGRATING` |
| `INTEGRATING` | — | Run §7 integration procedure |
| `INTEGRATING` | bundle full-suite green | Push to PR · → `CI_ITERATION` |
| `INTEGRATING` | bundle red | Diagnose: single-WS regression → re-dispatch implementer; cross-WS conflict → escalate to `architect` review |
| `CI_ITERATION` | CI red | Pull CI logs · diagnose · fix · push · re-watch (no retry cap on CI iteration — "stop at nothing until CI passes") |
| `CI_ITERATION` | CI green | Run `code-reviewer` skill on full PR diff · address Critical/Important · push fixes |
| `CI_ITERATION` | code-reviewer verdict "Ready to merge" | → `DONE`; write completion marker; report to user |
| any | wall-clock budget (default **96 h**) exhausted | Write `BUDGET_EXCEEDED` snapshot to run log; push current state to PR with status comment; halt without merging |
| any | STOP signal | Write `INTERRUPTED`; halt |

**Note on Gate 1 (100% branch coverage):** strictly enforced per WS in step 2 of the crew. The orchestrator may NOT lower `fail_under` to make CI pass — if coverage is below 100% on a touched file, the implementer must add tests or remove the un-covered branch.

---

## 7. Integration phase (cascade-merge)

Runs once all 12 WSes report `ws_done`. Follows `.claude/rules/cascade-merge-pattern.md`.

```bash
git checkout modularize-v1.34 && git pull
git checkout -b feat/cockpit-and-profile-model-bundle    # or check it out if already exists

# Merge in dependency order (data → engine/profiles/history/device/export → ws → tauri → web → web-cockpit → integration → docs)
git merge --no-ff feat/cockpit-data-model
git merge --no-ff feat/cockpit-mutation-engine
git merge --no-ff feat/cockpit-profile-registry
git merge --no-ff feat/cockpit-history
git merge --no-ff feat/cockpit-device-adapter
git merge --no-ff feat/cockpit-export-pipeline
git merge --no-ff feat/cockpit-ws-server
git merge --no-ff feat/cockpit-tauri-shell
git merge --no-ff feat/cockpit-web-scaffold
git merge --no-ff feat/cockpit-web-ui
git merge --no-ff feat/cockpit-integration-tests
git merge --no-ff feat/cockpit-docs
```

**Conflict resolution rules:**
- `pyproject.toml` — union all `[project.dependencies]` additions.
- `tests/conftest.py` — accept all additions (each WS adds distinct fixtures).
- `.gitignore` — union additions.
- `docs/ARCHITECTURE.md`, `ARCHITECTURE_DIAGRAMS.md`, `STATUS.md`, `README.md` — only WS-L touches; no conflict expected.
- Any conflict outside this list — escalate, do not guess.

**Bundle verification:** the integration agent runs the full gate battery:
- `python -m pytest -q` (full suite — must stay green)
- `python -m pytest tests/architecture/ -q`
- `python -m pytest tests/test_engines_pad*.py tests/test_group_runner.py tests/test_scene_runner.py -q` (685 V1.34 parity items byte-identical)
- `python -m ruff check . && python -m black --check . && python -m isort --profile black --check-only .`
- `python -m pytest --cov=rytm_randomizer --cov-branch --cov-fail-under=95` (whole-package floor stays)
- `cd desktop/web && npm test -- --run --coverage` (web frontend tests)
- `cd desktop/shell && cargo test && cargo clippy --all-targets -- -D warnings`
- `git status --short tests/fixtures/v134_parity/` → must be empty (no V1.34 golden rewritten)

Green → push to the PR branch. Red → diagnosis loop.

---

## 8. The single PR

- **Base:** `modularize-v1.34`. **Head:** `feat/cockpit-and-profile-model-bundle`.
- **Title:** `feat: cockpit & profile-model (Phase 1 — Tauri + web + Python sidecar over WebSocket)`
- **Body:** full 18-gate conformance checklist (§13) + the strict-rules confirmation + this plan and the spec linked from the body.
- **Opened with:** `gh pr create --base modularize-v1.34 --head feat/cockpit-and-profile-model-bundle --title "..." --body-file <generated>`
- **Status:** opened as draft initially (during WS execution); marked ready-for-review once `INTEGRATING` lands green; codex's existing review hook (`.codex/hooks.json`) fires automatically and posts the 8-step verdict as a comment.

---

## 9. Operational guardrails

**Kickoff:** `/loop run docs/superpowers/plans/2026-05-23-cockpit-and-profile-model.md` (one-shot via the loop skill, `<<autonomous-loop-dynamic>>` re-entry).

**Hard time budget:** **96 hours** (4 days) wall-clock. Larger than the passive-layer-framework's 72h because of the additional Rust + web frontend toolchain bootstrap, CI iteration, and 12 WSes.

**Recovery procedure (every wake-up):** read `STATE.json` → `gh pr list` for the open PR → `git branch --list` → per-WS `git log` in each worktree → reconcile → resume from §6 at the reconciled state.

**Permission profile:** `acceptEdits`. Refuses: force-push to `modularize-v1.34`/`main`, deleting branches not owned, `PARITY_CAPTURE_MODE=1`, bumping `mido`/`python-rtmidi`, `--no-verify`, adding architecture-test allowlist entries (none should be needed — verified during planning).

**Stop signals:** `STOP` in chat → `TaskStop` monitors, push current state with `INTERRUPTED` comment, halt. Closing the PR → orchestrator detects, writes `PLAN_REVOKED`, halts.

**Hard stops requiring a human:** any V1.34 parity-fixture diff that survives 2 revert+retry cycles · bundle integration conflict outside the §7 table · code-reviewer Critical that survives 2 fix cycles · budget exhaustion · external dependency unavailable (e.g., `cargo` not installed in CI).

---

## 10. Persistent state on disk

Both files committed to the integration branch so they travel with the bundle:

- **`docs/superpowers/plans/2026-05-23-cockpit-and-profile-model_STATE.json`** — schema:

```json
{
  "plan": "2026-05-23-cockpit-and-profile-model",
  "state": "INIT|RUNNING|INTEGRATING|CI_ITERATION|DONE|HALTED",
  "kickoff_utc": "2026-05-23T00:00:00Z",
  "budget_hours": 96,
  "workstreams": {
    "WS-A": {"phase": "pending|implementing|ws_done|blocked", "branch": "feat/cockpit-data-model", "worktree": "RytmRandomizer-worktrees/ws-a-data-model", "last_sha": null, "retries": 0},
    "WS-B": {...},
    "...": {},
    "WS-L": {...}
  },
  "integration_branch": "feat/cockpit-and-profile-model-bundle",
  "pr_url": null,
  "ci_iterations": 0,
  "last_ci_status": null
}
```

- **`docs/superpowers/plans/2026-05-23-cockpit-and-profile-model_RUN_LOG.md`** — append-only event log; never gitignored.

---

## 11. Learning extraction (Gate 15)

After CI green + code-review clean, before final report:

- **`docs/superpowers/plans/2026-05-23-cockpit-and-profile-model_RUN_REPORT.md`** — timeline, per-WS LOC, escalations, lessons.
- **`docs/2026-05-23-cockpit-and-profile-model_MAINTAINABILITY_REPORT.md`** — Gate 14 post-plan re-audit scoring the 10 questions against the §12 baseline.
- **`.claude/skills/learned/`** — candidates: "tauri-shell-with-python-sidecar," "websocket-protocol-for-typed-events," "100pct-coverage-on-mixed-python-and-typescript."
- **`.claude/rules/`** update if a new repo-wide invariant emerged (candidate: "the cockpit and profile-model layer is the new active-runtime surface — all GUI work goes here, no parallel UI subpackages").

---

## 12. Pre-plan maintainability audit (Gate 14)

1. **Onboarding curve** — a new contributor needs to know: (a) the existing `live_gui_*` contract framework, (b) the Tauri/web/Python boundary, (c) the Protocol. The cockpit quickstart doc + ARCHITECTURE section make this navigable.
2. **Naming hygiene** — `cockpit/`, `desktop/`, `engine`, `profiles`, `history`, `device`, `export` — direct, no abbreviations.
3. **Coupling/boundaries** — clean three-tier boundary: Rust shell knows nothing about business; web frontend talks only Protocol; Python sidecar owns all state.
4. **Magic numbers/strings** — `Literal` types for `kind`/`status`/`via`/`transition_curve`; PRNG seed format documented in `engine/spec.md`.
5. **Configuration vs convention** — port (env var), profile directory (XDG-honored), tempo/swing (state).
6. **Test maintainability** — shared `cockpit_client` fixture; per-WS test files mirror source.
7. **Build/dev loop** — Python tests unchanged-fast; web tests via Vitest (<2s for unit); Rust build slower but cached.
8. **Error messages** — WebSocket command errors carry `{ok: false, error: <message>}`; UI displays inline.
9. **Versioning/release** — `cockpit/data/__init__.py` carries `PROTOCOL_VERSION`; web frontend's `protocol.ts` mirrors.
10. **Future-proofing** — Phase 2 wizard reuses `cockpit/profiles/` registry; Phase 3 export pipeline reuses `cockpit/export/`; Phase 4 hardware loads via `cockpit/export/unpack`.

No regressions identified. Post-plan re-audit re-scores in §11.

---

## 13. Plan-requirements conformance

Per `docs/PLAN_REQUIREMENTS.md`:

- [x] **Gate 1** — 100% branch coverage on touched files. Crew step 2 per WS. Hard-enforced; no `fail_under` lowering.
- [x] **Gate 2** — V1.34 parity byte-identical. No WS touches `engines/`, `group_runner.py`, `scene_runner.py`, or the V1.34 parity fixtures. The new mutation engine is layered alongside the existing engine.
- [x] **Gate 3** — lint/format/type clean (Python: ruff + black + isort; Rust: fmt + clippy; web: eslint + tsc).
- [x] **Gate 4** — no new dead code. Crew step 2 includes `vulture --min-confidence 80` for Python.
- [x] **Gate 5** — docs updated (WS-L).
- [x] **Gate 6** — type-system hygiene: frozen dataclasses, Protocols, `from __future__ import annotations`, no bare `Any`. Web frontend uses strict TypeScript.
- [x] **Gate 7** — observability: `get_metrics().record_*` on every command handled by the WS server + every mutation produced + every device send.
- [x] **Gate 8** — test hygiene: intent-named tests, shared fixtures.
- [x] **Gate 9** — module organization: new top-level `cockpit/` subpackage (justified — distinct concern), new top-level `desktop/` directory (not a Python package — Rust + web). No new top-level `*.py` files; the architecture test allowlist is unchanged.
- [x] **Gate 10** — string-literal dispatch hygiene: `Literal` types throughout.
- [x] **Gate 11** — shared test fixtures: `cockpit_client` lives in `tests/cockpit/conftest.py`.
- [x] **Gate 12** — `Final` constants throughout.
- [x] **Gate 13** — env vars documented + safe-default: `RYTM_RAND_WS_PORT` (default 4317) documented in `CONTRIBUTING.md` + `docs/COCKPIT_QUICKSTART.md`.
- [x] **Gate 14** — maintainability review (§12 pre-plan; §11 post-plan re-audit in learning phase).
- [x] **Gate 15** — learning phase (§11).
- [x] **Gate 16** — execution shape: this whole plan is the Gate-16 structure.
- [x] **Gate 17** — abstraction reuse: cockpit consumes the existing 24 `live_gui_*` contracts as authoritative specs; reuses `style_analysis/` for trait derivation (Phase 2); reuses `data/profiles.py` for CC-number lookups; reuses `observability/metrics`; reuses `cli_registry` if any CLI hooks added; reuses existing `mido_provider`/`real_midi_adapter` for the real-MIDI device path.
- [x] **Gate 18** — architecture-doc + diagram freshness: WS-L delivers `ARCHITECTURE.md` section + 2 new mermaid diagrams.

Exceptions: none.

---

## 14. Execution handoff

**Kickoff command (operator runs in chat):**

```
/loop run docs/superpowers/plans/2026-05-23-cockpit-and-profile-model.md
```

The orchestrator follows §6, runs §7 integration, opens the PR per §8, iterates per §6 `CI_ITERATION` until green + reviewed, runs §11 learning phase, writes `DONE` to the run log, reports completion.

**Out-of-scope reminder:** Phase 2 Profile Wizard UI, Phase 3 standalone model-export CLI, Phase 4 hardware runtime — each gets its own future spec.
