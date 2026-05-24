# Profile Wizard Implementation Plan — Phase 2

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development. This plan is structured for **maximum-parallelization autonomous execution** per Gate 16 — seven workstreams run concurrently in isolated worktrees, bundle into ONE pull request against `modularize-v1.34`.

**Goal:** Build the Profile Wizard — the authoring UI + analysis pipeline + `ProfileModel` builder — that lets the operator create user-authored profiles from inspiration sources (kits, sounds, songs, albums, artists, folders) and drop them into the cockpit's `ProfileRegistry`.

**Architecture:** Adds a `cockpit/wizard/` Python subpackage (state · analysis · builder), extends `cockpit/ws/` with wizard commands + events, adds a `desktop/web/src/wizard/` React surface that consumes the extended WS protocol. Reuses existing `style_analysis/`, `cockpit/data`, `cockpit/profiles`, `cockpit/ws` infrastructure from PR #99.

**Tech Stack:** Python 3.11 + existing cockpit · React 18 + TypeScript 5 + Vite 5 · Tauri 2 dialog plugin for file/folder pickers. No new third-party dependencies expected (Tauri's `dialog` plugin is already part of Tauri 2 standard kit).

**Source spec:** `docs/superpowers/specs/2026-05-24-profile-wizard-design.md`.

---

## 1. Workstream graph

| WS | Title | Depends on | Parallel-safe with | Owner files |
|---|---|---|---|---|
| **WS-A** | Wizard data model | — | B,C,D,E,F,G | `cockpit/wizard/state.py`, `cockpit/wizard/__init__.py` |
| **WS-B** | Analysis adapter | A | C,D,E,F,G | `cockpit/wizard/analyze.py`, `cockpit/wizard/sysex_analyzer.py`, `cockpit/wizard/reference_analyzer.py` |
| **WS-C** | ProfileBuilder | A | B,D,E,F,G | `cockpit/wizard/builder.py`, `cockpit/wizard/pad_mapping.py` |
| **WS-D** | Wizard WS extensions | A,C | B,E,F,G | `cockpit/ws/wizard_protocol.py`, `cockpit/ws/wizard_handlers.py`, `cockpit/ws/wizard_session.py` |
| **WS-E** | Web wizard UI | — (only consumes WS-D's protocol contract) | A,B,C,D,F,G | `desktop/web/src/wizard/**`, `desktop/web/src/state/wizard_store.ts`, `desktop/web/src/cockpit/MutationPanel.tsx` (small launcher add) |
| **WS-F** | Integration tests | A,B,C,D | E,G | `tests/cockpit/test_wizard_*.py`, `tests/cockpit/test_integration_wizard_flow.py` |
| **WS-G** | Docs + diagrams | — | A,B,C,D,E,F | `docs/ARCHITECTURE.md`, `docs/ARCHITECTURE_DIAGRAMS.md`, `docs/COCKPIT_QUICKSTART.md`, `docs/STATUS.md`, `README.md` |

**Parallelization waves:**
- **Wave 1 (t=0, fully parallel):** WS-A, WS-E, WS-G — fully independent.
- **Wave 2 (after WS-A):** WS-B, WS-C — depend only on WS-A's typed data.
- **Wave 3 (after WS-A,C):** WS-D — wires builder + state through WS.
- **Wave 4 (after WS-A,B,C,D):** WS-F — integration tests.

Orchestrator dispatches all 7 at t=0; dependent WSes block on predecessors' `ws_done` markers.

---

## 2. Per-workstream detail

### WS-A · Wizard data model

- **Worktree:** `RytmRandomizer-worktrees/ws-a-wizard-data`
- **Branch:** `feat/wizard-data-model`
- **Owns:** `rytm_randomizer/cockpit/wizard/__init__.py`, `cockpit/wizard/state.py`, `tests/cockpit/test_wizard_state.py`
- **Delivers:**
  - `InspirationSource` frozen dataclass (source_id ULID, kind Literal, mode Literal, location, display_name, added_at)
  - `AnalysisJob` frozen dataclass (source_id, status Literal, progress float, error str|None, extracted_traits tuple[StyleTrait,...])
  - `WizardState` frozen dataclass (wizard_id ULID, step Literal, name, description, sources tuple, jobs tuple, candidate_profile ProfileModel|None)
  - `WizardState.next_step()`, `.with_source(...)`, `.with_job_update(...)`, `.with_candidate(...)` — pure state-transition methods
  - JSON round-trip (`to_dict`, `from_dict`) for each
  - **100% branch coverage** on `cockpit/wizard/state.py`

### WS-B · Analysis adapter

- **Worktree:** `RytmRandomizer-worktrees/ws-b-wizard-analyze`
- **Branch:** `feat/wizard-analyze`
- **Owns:** `cockpit/wizard/analyze.py`, `cockpit/wizard/sysex_analyzer.py`, `cockpit/wizard/reference_analyzer.py`, `tests/cockpit/test_wizard_analyze.py`, `tests/cockpit/test_wizard_sysex_analyzer.py`, `tests/cockpit/test_wizard_reference_analyzer.py`
- **Delivers:**
  - `analyze_source(source: InspirationSource) -> tuple[StyleTrait, ...]` — dispatcher on `kind` + `mode`
  - **Audio path:** wrap `rytm_randomizer.style_analysis.extractor.extract_features(path)` → call `feature_report_to_traits(...)` (new helper in `analyze.py`) that maps `FeatureReport` numeric fields to `StyleTrait`s
  - **Folder path:** iterate path's contents matching `*.wav|*.mp3|*.flac|*.aif|*.aiff|*.syx` per kind, analyze each, weighted average of results
  - **SysEx path:** `sysex_analyzer.extract_kit_traits(path)` — parses kit dump (use existing `snapshot/` helpers if available; otherwise stub deterministic byte-stats → traits), returns a tuple[StyleTrait,...]
  - **Reference path:** `reference_analyzer.lookup_traits(text)` — built-in `Final` dict of 20 known artist/album names mapped to trait profiles; unknown names return a neutral profile with low confidence
  - All three analyzers are deterministic and side-effect free except for reading files
  - **100% branch coverage** on touched files

### WS-C · ProfileBuilder

- **Worktree:** `RytmRandomizer-worktrees/ws-c-wizard-builder`
- **Branch:** `feat/wizard-builder`
- **Owns:** `cockpit/wizard/builder.py`, `cockpit/wizard/pad_mapping.py`, `tests/cockpit/test_wizard_builder.py`, `tests/cockpit/test_wizard_pad_mapping.py`
- **Delivers:**
  - `pad_mapping.TRAIT_TO_PAD: Final[Mapping[str, int]]` — built-in trait → pad assignment (e.g., `"rolling_low_end" -> 1`, `"metallic_tension" -> 2`, `"hat_density" -> 3`, `"filter_motion" -> 4`)
  - `build_profile(name: str, description: str|None, jobs: tuple[AnalysisJob,...]) -> ProfileModel` — aggregates OK jobs' traits by weighted average, normalizes to 0..1, derives `pad_mappings` from `TRAIT_TO_PAD`, sets `kind="user"`, `model_version="1.0.0"`, `transition_curve="progressive"`, computes `source_summary` like "5 sources · 1,243 analyzed signals"
  - Edge cases: no OK jobs → raises `EmptyAnalysisError`; jobs with no extracted_traits → contribute nothing to the average
  - **100% branch coverage**

### WS-D · Wizard WS extensions

- **Worktree:** `RytmRandomizer-worktrees/ws-d-wizard-ws`
- **Branch:** `feat/wizard-ws`
- **Owns:** `cockpit/ws/wizard_protocol.py`, `cockpit/ws/wizard_handlers.py`, `cockpit/ws/wizard_session.py`, `tests/cockpit/test_ws_wizard_protocol.py`, `tests/cockpit/test_ws_wizard_handlers.py`
- **Delivers:**
  - `WizardSession` mutable dataclass tracking active wizard state per WS client connection
  - 8 new command handlers matching the spec's wizard command list (start, set_metadata, add_source, remove_source, analyze, review, save, cancel) — dispatched via the existing `cockpit.ws.handlers.handle_command` (add `elif cmd_type.startswith("wizard_")` branch that delegates to `wizard_handlers`)
  - 3 new event emitters: `wizard_state_changed`, `analysis_progress`, `profile_created`
  - `wizard_analyze` runs the analyzer per source synchronously, emitting `analysis_progress` between sources (use `asyncio.to_thread` for blocking analyzers so the event loop stays responsive)
  - `wizard_save` writes to `~/.rytm-randomizer/profiles/<wizard_id>.json` via the existing `ProfileRegistry.save(profile)` method, then emits `profile_created` + `profile_changed`
  - Updates `cockpit/ws/protocol.py`'s `COMMAND_TYPES` and `EVENT_TYPES` constants to include the new types
  - **100% branch coverage**

### WS-E · Web wizard UI

- **Worktree:** `RytmRandomizer-worktrees/ws-e-wizard-web`
- **Branch:** `feat/wizard-web`
- **Owns:** `desktop/web/src/wizard/**` (every wizard component), `desktop/web/src/state/wizard_store.ts`, `desktop/web/src/types/wizard_protocol.ts`, small edit to `desktop/web/src/cockpit/MutationPanel.tsx` (add "Create profile…" button), `desktop/web/tests/wizard/**`
- **Delivers:**
  - `<Wizard />` — top-level container that mounts when route is `/wizard`
  - `<WizardSteps />`, `<NameStep />`, `<AddStep />`, `<AnalyzeStep />`, `<ReviewStep />` — one per step per the spec
  - `wizard_store.ts` — zustand slice with current `WizardState`; subscribes to `wizard_state_changed` + `analysis_progress` + `profile_created` events
  - `wizard_protocol.ts` — TypeScript types matching `cockpit/ws/wizard_protocol.py` exactly
  - File/folder picker: use `@tauri-apps/plugin-dialog` `open({ directory: true })` and `open({ multiple: false })`; reference picker is a plain text input
  - **100% branch coverage on `src/wizard/**`** + the small `MutationPanel` add

### WS-F · Integration tests

- **Worktree:** `RytmRandomizer-worktrees/ws-f-wizard-integration`
- **Branch:** `feat/wizard-integration-tests`
- **Owns:** `tests/cockpit/test_wizard_flow.py`, `tests/cockpit/test_integration_wizard_flow.py`, additions to `tests/cockpit/conftest.py` (a `wizard_client` fixture if needed)
- **Delivers:**
  - End-to-end test via `TestClient` + WebSocket:
    - `wizard_start` → ack with wizard_id + `wizard_state_changed` event
    - `wizard_set_metadata(name="test")` → state update
    - `wizard_add_source(kind="artist", mode="reference", location="Surgeon", display_name="Surgeon")` → state update with new source
    - `wizard_analyze` → multiple `analysis_progress` events → all jobs reach `ok`
    - `wizard_review` → state with `candidate_profile` populated
    - `wizard_save` → `profile_created` event + `profile_changed` event + profile appears in registry
    - `wizard_cancel` → state cleared
  - Negative tests: invalid source path, analyzer failure, save before review, etc.
  - **100% branch coverage** on the integration test code

### WS-G · Docs + diagrams

- **Worktree:** `RytmRandomizer-worktrees/ws-g-wizard-docs`
- **Branch:** `feat/wizard-docs`
- **Owns:** `docs/ARCHITECTURE.md` (new "Profile Wizard layer" subsection in §6.2 cockpit section), `docs/ARCHITECTURE_DIAGRAMS.md` (new diagram for wizard flow), `docs/COCKPIT_QUICKSTART.md` (new "Creating your first profile" walkthrough), `docs/STATUS.md` (recent-cleanup entry), `README.md` (add wizard to the Cockpit (alpha) section)
- **Delivers:**
  - 1 new mermaid sequence diagram: Name → Add → Analyze → Review → Save (with WS events overlaid)
  - 1 new mermaid component diagram: Wizard sub-system (state · analyze · builder · ws extensions · web wizard surface)
  - Profile-wizard walkthrough in COCKPIT_QUICKSTART
  - README and STATUS entries

---

## 3. Disjoint-file ownership matrix

| Path prefix | WS-A | WS-B | WS-C | WS-D | WS-E | WS-F | WS-G |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| `rytm_randomizer/cockpit/wizard/__init__.py` + `state.py` | ✅ | | | | | | |
| `cockpit/wizard/analyze.py` + `sysex_analyzer.py` + `reference_analyzer.py` | | ✅ | | | | | |
| `cockpit/wizard/builder.py` + `pad_mapping.py` | | | ✅ | | | | |
| `cockpit/ws/wizard_*.py` | | | | ✅ | | | |
| `cockpit/ws/protocol.py` (small enum addition) | | | | ✅ | | | |
| `cockpit/ws/handlers.py` (small dispatch addition) | | | | ✅ | | | |
| `desktop/web/src/wizard/**` + `state/wizard_store.ts` + `types/wizard_protocol.ts` + small MutationPanel add | | | | | ✅ | | |
| `tests/cockpit/test_wizard_state.py` | ✅ | | | | | | |
| `tests/cockpit/test_wizard_analyze*.py` + `test_wizard_sysex_analyzer.py` + `test_wizard_reference_analyzer.py` | | ✅ | | | | | |
| `tests/cockpit/test_wizard_builder.py` + `test_wizard_pad_mapping.py` | | | ✅ | | | | |
| `tests/cockpit/test_ws_wizard_*.py` | | | | ✅ | | | |
| `desktop/web/tests/wizard/**` | | | | | ✅ | | |
| `tests/cockpit/test_wizard_flow.py` + `test_integration_wizard_flow.py` | | | | | | ✅ | |
| `tests/cockpit/conftest.py` (additive fixture) | | | | | | ✅ | |
| `docs/ARCHITECTURE*.md` + `STATUS.md` + `README.md` + `docs/COCKPIT_QUICKSTART.md` | | | | | | | ✅ |

**Cross-WS conflicts at integration:**
- `cockpit/ws/protocol.py` (small) + `cockpit/ws/handlers.py` (small) — only WS-D touches; no conflict expected
- `desktop/web/src/cockpit/MutationPanel.tsx` — only WS-E touches; no conflict
- `tests/cockpit/conftest.py` — only WS-F touches (additive); no conflict
- `pyproject.toml` — no WS adds dependencies; no conflict

---

## 4. Agent crew per WS

Same pattern as Phase 1 plan §5:
1. **Implementer** — bite-sized TDD per task → produces files + tests
2. **Coverage gate** — `pytest --cov=<touched> --cov-branch --cov-fail-under=100`
3. **Lint** — ruff + black + isort (Python); eslint + tsc (web)
4. **Self-review** — agent verifies own work

A WS is `ws_done` when 1–4 all green.

---

## 5. Self-driving decision rules

Per Phase 1 plan §6 — same state machine: `INIT → RUNNING → INTEGRATING → CI_ITERATION → DONE`. Same retry semantics. Same "no AskUserQuestion during the run" rule.

---

## 6. Integration phase

```bash
git checkout modularize-v1.34 && git pull
git checkout feat/profile-wizard-bundle  # this branch is what holds spec+plan; merges land on top

# Merge dependency order:
git merge --no-ff origin/feat/wizard-data-model
git merge --no-ff origin/feat/wizard-analyze
git merge --no-ff origin/feat/wizard-builder
git merge --no-ff origin/feat/wizard-ws
git merge --no-ff origin/feat/wizard-web
git merge --no-ff origin/feat/wizard-integration-tests
git merge --no-ff origin/feat/wizard-docs
```

Bundle verification (full gate battery from Phase 1 plan §7):
- `python -m pytest -q` (full suite)
- `python -m pytest tests/architecture/ -q`
- V1.34 parity untouched (verify `git status --short tests/fixtures/v134_parity/` empty)
- Lint trio + tsc + eslint
- Whole-package coverage stays ≥ 95% floor
- `cd desktop/web && npm test -- --run --coverage` green

---

## 7. The single PR

- **Base:** `modularize-v1.34` · **Head:** `feat/profile-wizard-bundle`
- **Title:** `feat: profile wizard (Phase 2 — authoring UI + analysis pipeline + ProfileBuilder)`
- **Body:** Full 18-gate conformance checklist (§9) + strict-rules confirmation + links to spec + plan
- **Status:** draft initially; ready-for-review once `INTEGRATING` lands green; codex review hook fires automatically

---

## 8. Operational guardrails

- **Hard time budget:** 72 hours wall-clock (smaller than Phase 1 since the surface area is smaller)
- **Recovery:** same as Phase 1 — read on-disk state, query `gh pr list`, resume from reconciled state
- **Permission profile:** `acceptEdits`; refuse force-push to protected branches, V1.34 fixture regen, hardware-pin bumps, `--no-verify`
- **Hard stops:** V1.34 parity fixture diff that survives 2 reverts · bundle integration conflict outside §6 table · code-reviewer Critical that survives 2 fix cycles · budget exhaustion

---

## 9. Plan-requirements conformance

Per `docs/PLAN_REQUIREMENTS.md`:

- [x] **Gate 1** — 100% branch coverage on touched files (per-WS enforcement)
- [x] **Gate 2** — V1.34 parity byte-identical (no engine code touched)
- [x] **Gate 3** — lint/format/type clean
- [x] **Gate 4** — no new dead code
- [x] **Gate 5** — docs updated (WS-G)
- [x] **Gate 6** — frozen dataclasses + Protocols + no bare `Any` + strict TypeScript
- [x] **Gate 7** — `get_metrics().record_*` on wizard commands + analysis decisions
- [x] **Gate 8** — intent-named tests
- [x] **Gate 9** — new `cockpit/wizard/` subpackage; no new top-level `*.py`
- [x] **Gate 10** — `Literal` types for `kind`, `mode`, `status`, `step`
- [x] **Gate 11** — `wizard_client` shared fixture
- [x] **Gate 12** — `Final` constants
- [x] **Gate 13** — no new env vars
- [x] **Gate 14** — maintainability audit included (pre- and post-)
- [x] **Gate 15** — learning extraction
- [x] **Gate 16** — execution shape: 7 parallel WSes, one bundled PR
- [x] **Gate 17** — abstraction reuse: `style_analysis/`, `cockpit/data`, `cockpit/profiles`, `cockpit/ws` all reused; new wizard layer composes them
- [x] **Gate 18** — architecture-doc + diagram freshness (WS-G)

Exceptions: none.

---

## 10. Execution handoff

**Kickoff** (operator runs in chat):
```
/loop run docs/superpowers/plans/2026-05-24-profile-wizard.md
```

Orchestrator follows §5, runs §6 integration, opens the PR per §7, iterates §5's `CI_ITERATION` until green + reviewed, writes `DONE`.

**Out-of-scope:** Phase 3 model export pipeline · Phase 4 hardware runtime · operator-editable trait→pad mapping (future iteration).
