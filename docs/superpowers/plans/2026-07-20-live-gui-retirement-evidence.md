# Live-GUI paper-spec retirement evidence (verify-then-retire, decision gate ③)

**Date:** 2026-07-20
**Branch:** `rival-program` (HEAD `4e87d02`)
**Scope:** the 12 `live_gui_*` paper-spec report modules + the 2 controller-brain
re-stamps + the dead replay-command wiring in `live_gui_safety_checklist_model.py`.
> Status: in-flight (retirement executed on `rival-program` 2026-07-28 — see
> §7 for the execution record; flip to `shipped (PR #N)` when the bundle PR
> merges). Originally evidence-only; the maintainer-approved retirement
> (Decision Gate ③, 2026-07-22) authorized the execution.

The 12-module list was confirmed against `ls rytm_randomizer/reports/live_gui_*.py`
(38 files), excluding the `live_gui_*_model.py` data modules and the
runtime-consumed modules. The sixth module's actual filename is
`live_gui_screen_contract.py` (no `desktop_` prefix).

---

## 1. Summary table

Every module below is CLI-registered (via `rytm_randomizer/cli.py` lazy command
table + `rytm_randomizer/help_text.py`) and has its own test file. "Non-self
consumers" excludes: its own test file, the cli.py/help_text.py registration,
and `tests/architecture/test_abstraction_reuse.py` allowlist entries (common to
all 12) — those are listed once in the retirement checklist. **No module is
re-exported from `rytm_randomizer/reports/__init__.py`** (verified: zero
`live_gui` references in that file).

| Module (`rytm_randomizer/reports/`) | LOC | Registered command | Non-self consumers | Superseded by | Verdict |
|---|---|---|---|---|---|
| `live_gui_desktop_blueprint.py` | 1434 | `style-performance-arc-live-gui-desktop-blueprint-report` | `live_gui_desktop_app_plan.py` (in retire set) | Cockpit layout: `desktop/web/src/cockpit/Cockpit.tsx` + `PerformanceConsole.tsx` | **RETIRE** (as set)¹ |
| `live_gui_desktop_app_plan.py` | 1148 | `style-performance-arc-live-gui-desktop-app-plan-report` | `live_gui_desktop_component_contract.py` (in set) | Shipped app structure: `desktop/web/src/` + `App.tsx` + `styles.css` | **RETIRE** (as set)¹ |
| `live_gui_desktop_component_contract.py` | 1196 | `style-performance-arc-live-gui-desktop-component-contract-report` | `live_gui_desktop_view_model.py` (in set) | 20 cockpit components + `desktop/web/tests/cockpit/*.test.tsx` | **RETIRE** (as set)¹ |
| `live_gui_desktop_view_model.py` | 1197 | `style-performance-arc-live-gui-desktop-view-model-report` | `live_gui_desktop_render_contract.py` (in set) | `desktop/web/src/state/store.ts` + `cockpit/context.tsx` | **RETIRE** (as set)¹ |
| `live_gui_desktop_render_contract.py` | 1131 | `style-performance-arc-live-gui-desktop-render-contract-report` | `live_gui_desktop_render_harness.py` (in set) | `desktop/web/src/types/live_gui_protocol.ts` interfaces | **RETIRE** (as set)¹ |
| `live_gui_desktop_render_harness.py` | 937 | `style-performance-arc-live-gui-desktop-render-harness-report` | **`live_gui_cockpit_boundary_readiness.py:20` (KEPT)** | Vitest render harness: `desktop/web/tests/` | **ENTANGLED** — break import ① |
| `live_gui_screen_contract.py` | 1263 | `style-performance-arc-live-gui-screen-contract-report` | `live_gui_render_tree.py` (in set)² | The shipped JSX screen itself (`Cockpit.tsx`) | **RETIRE** (as set)¹ |
| `live_gui_render_tree.py` | 948 | `style-performance-arc-live-gui-render-tree-report` | **`live_gui_analyzer_overlay.py:27` (KEPT)** | The React component tree itself | **ENTANGLED** — break import ② |
| `live_gui_interaction_script.py` | 821 | `style-performance-arc-live-gui-interaction-script-report` | **`live_gui_action_reducer.py:23` (KEPT)** | `desktop/web/src/ws/protocol.ts` + `useLoggedCommand.ts` + `ActionBar.tsx` | **ENTANGLED** — break import ③ |
| `live_gui_implementation_bridge.py` | 1104 | `style-performance-arc-live-gui-implementation-bridge-report` | `live_gui_desktop_blueprint.py` (in set) | Real bridge: `rytm_randomizer/cockpit/ws/handlers.py:226-236, 689-693` | **RETIRE** (as set)¹ |
| `live_gui_test_harness_contract.py` | 853 | `style-performance-arc-live-gui-test-harness-contract-report` | `live_gui_test_harness_readiness.py` (in set) | Real harness: `desktop/web/tests/` vitest suite | **RETIRE** (as set)¹ |
| `live_gui_test_harness_readiness.py` | 982 | `style-performance-arc-live-gui-test-harness-readiness-report` | `live_gui_implementation_bridge.py` (in set) | Same — the harness exists and runs in CI | **RETIRE** (as set)¹ |
| `controller_brain_live_desktop_blueprint.py` | 681 | `controller-brain-live-desktop-blueprint-report` | `controller_brain_live_desktop_app_plan.py` (in pair) | Shipped `rytm_randomizer/cockpit/` + React cockpit | **ENTANGLED** — via ④ |
| `controller_brain_live_desktop_app_plan.py` | 740 | `controller-brain-live-desktop-app-plan-report` | **`controller_brain_live_desktop_component_contract.py:13` (KEPT, out of audit scope)** | Same | **ENTANGLED** — break import ④ |
| `live_gui_safety_checklist_model.py:300-304, 365` (dead wiring only) | n/a | **none — `live-gui-safety-checklist-model-report` is unregistered** | module itself is KEEP (see §4) | n/a | **RETIRE the dead replay string only** |

¹ "RETIRE (as set)": the only non-self consumer is another member of the retire
set, so the module is provably dead once the set is removed together **and** the
three named entanglement imports are broken. The dependency chain
`cockpit_boundary_readiness → render_harness → render_contract → view_model →
component_contract → app_plan → blueprint → implementation_bridge →
test_harness_readiness → test_harness_contract` means a *single* kept import
(① below) transitively pins 10 of the 12 modules.

² `live_gui_implementation_bridge.py` mentions `live_gui_screen_contract` /
`live_gui_render_tree` only as JSON-key strings (`live_gui_implementation_bridge.py:277,286,444`),
not imports — verified.

### The four imports to break

| # | Kept module → import to break | Frees |
|---|---|---|
| ① | `rytm_randomizer/reports/live_gui_cockpit_boundary_readiness.py:20` — `from .live_gui_desktop_render_harness import (StylePerformanceArcLiveGuiDesktopRenderHarnessReport, build_…, parse_…, to_…_json)` | render_harness → render_contract → view_model → component_contract → app_plan → blueprint → implementation_bridge → test_harness_readiness → test_harness_contract (**10 modules**, incl. screen_contract via ②'s chain independence) |
| ② | `rytm_randomizer/reports/live_gui_analyzer_overlay.py:27` — `from .live_gui_render_tree import (StylePerformanceArcLiveGuiRenderNode, …Report, build_…, parse_…, to_…_json)` | render_tree → screen_contract (**2 modules**) |
| ③ | `rytm_randomizer/reports/live_gui_action_reducer.py:23` — `from .live_gui_interaction_script import (StylePerformanceArcLiveGuiControlBinding, …Report, build_…, parse_…, to_…_json)` | interaction_script (**1 module**) |
| ④ | `rytm_randomizer/reports/controller_brain_live_desktop_component_contract.py:13` — `from .controller_brain_live_desktop_app_plan import (DESKTOP_APP_PLAN_STATUS, DESKTOP_APP_PLAN_VERSION, ControllerBrainDesktopComponentFileHint, ControllerBrainDesktopStateSlice, build_…)` | cb_app_plan → cb_blueprint (**2 modules**) |

Break strategy per import (orchestrator decision): each kept module imports the
upstream *paper report builder* purely to embed the upstream packet inside its
own output. Options: (a) drop the embedded upstream section from the kept
report (output change → update that module's test expectations), (b) inline the
few dataclass shapes needed, or (c) extend the retire set to the kept paper
module itself. For ① and ④ specifically, option (c) deserves consideration:
`live_gui_cockpit_boundary_readiness` (968 LOC) is itself a paper "readiness"
spec for the cockpit boundary that has since shipped, and the remaining
`controller_brain_live_desktop_{component_contract,view_model,render_contract}`
chain is the same re-stamp shape (`controller_brain_live_desktop_render_contract.py:13`
imports `…view_model`, which imports `…component_contract`). Auditing those four
as follow-up retire candidates would make breaks ① and ④ free.

---

## 2. Per-module evidence

Common facts for all 12 `live_gui_*` modules: passive/read-only, register a
`CliCommand` at import via `..cli_registry.register`, take an optional
`FeatureReport` JSON path, emit a deterministic "packet" of frozen dataclasses
rendered through `formatter.passive_report_lines` with a `--json` twin, and
carry a SHA-256 payload hash. Each embeds its upstream report in full — that is
what creates the daisy-chain. None is imported by any runtime path
(`rytm_randomizer/cockpit/`, `rytm_randomizer/app.py`, `desktop/`): verified by
repo-wide grep — the only package importers are the sibling paper modules named
in the table.

The shipped React cockpit's actual contract channel is
`rytm_randomizer/reports/live_gui_*_model.py` → WebSocket payload
(`cockpit/ws/handlers.py`) → `desktop/web/src/types/live_gui_protocol.ts`, whose
header says: *"Source of truth: the sibling TypedDict contracts in
`rytm_randomizer/reports/live_gui_*_model.py`"*, mechanically pinned by
`tests/architecture/test_live_gui_protocol_ts_matches_python_typeddicts.py`.
The paper-spec modules audited here are **not** part of that channel.

### 2.1 `live_gui_desktop_blueprint.py` — RETIRE (as set)

- **Emits:** "GUI desktop blueprint with desktop shell, viewports, regions,
  widgets, bindings" (docstring: "Passive live GUI desktop blueprint for future
  operator surfaces"). Sources `LIVE_GUI_DESKTOP_VIEWPORT_SPECS`,
  `LIVE_GUI_DESKTOP_REGION_SPECS`, `LIVE_GUI_DESKTOP_MOUNT_REGION_SPECS` from
  `data/live_gui_contracts.py:108-186`; embeds the implementation-bridge report.
- **Consumers:** cli.py:443-446 + help_text.py:3060-3086, 4223 | own test
  `tests/test_live_gui_desktop_blueprint_report.py` (530 LOC; also imported by
  `tests/test_live_gui_desktop_app_plan_report.py`,
  `tests/test_live_gui_desktop_component_contract_report.py` — both die with the
  set) | no `__init__` re-export | OTHER: `live_gui_desktop_app_plan.py` (in set).
- **Supersession:** its six paper mount regions (`region-current-cue`,
  `region-machine-grid`, `region-analyzer`, `region-capture-review`,
  `region-controls`, `region-harness`) are realized functionally by the shipped
  cockpit: machine grid → `PadCard.tsx` / `DeviceRail.tsx` /
  `AnalogFourTrackCard.tsx`; analyzer → the `LiveGuiAnalyzerPanelControlDict`
  section rendered in `PerformanceConsole.tsx`; controls → `ActionBar.tsx` +
  `MutationPanel.tsx`; current cue → `HeaderBar.tsx` + `HistoryStrip.tsx`;
  harness → `desktop/web/tests/` (real, running); capture review → reshaped into
  the snapshot-history flow (`live_gui_snapshot_history_model.py` →
  `SnapshotPanel.tsx` / `HistoryStrip.tsx`) rather than a literal
  capture-review panel — the shipped model path covers the operator need; no
  unbuilt functionality remains that this spec uniquely describes.
- **VERDICT: RETIRE** once import ① is broken (transitively pinned via app_plan).

### 2.2 `live_gui_desktop_app_plan.py` — RETIRE (as set)

- **Emits:** "GUI desktop app plan with app shell, routes, component file
  hints, state slices, style tokens" (sources
  `LIVE_GUI_DESKTOP_APP_STYLE_TOKEN_SPECS`); embeds the blueprint report.
- **Consumers:** cli.py:447-450 + help_text.py:3087-3113, 4226 | own test (556
  LOC) | no re-export | OTHER: `live_gui_desktop_component_contract.py` (in set).
- **Supersession:** the app it plans exists: `desktop/web/src/` file tree,
  `App.tsx` routing (verified by `desktop/web/tests/router.test.tsx`), state
  slices → `state/store.ts` + `state/wizard_store.ts`, style tokens →
  `cockpit/styles.css`. The plan's `framework-target` options
  (`desktop-python|web-desktop|test-harness`) were decided — web-desktop shipped.
- **VERDICT: RETIRE** (as set; pinned via component_contract → ①).

### 2.3 `live_gui_desktop_component_contract.py` — RETIRE (as set)

- **Emits:** "GUI desktop component contract with component props, disabled
  actions, test selectors"; embeds the app-plan report.
- **Consumers:** cli.py:451-454 + help_text.py:3114-3140, 4229 | own test (513
  LOC) | no re-export | OTHER: `live_gui_desktop_view_model.py` (in set).
- **Supersession:** real component props live in the 20 shipped components under
  `desktop/web/src/cockpit/` with `context.tsx` as the prop/context seam; real
  test selectors live in `desktop/web/tests/cockpit/*.test.tsx` (20 test files
  + `_fixtures.ts` + `performanceConsoleFixture.ts`).
- **VERDICT: RETIRE** (as set; pinned via view_model → ①).

### 2.4 `live_gui_desktop_view_model.py` — RETIRE (as set)

- **Emits:** "GUI desktop view model with component view models, state
  bindings, disabled actions, style tokens" (sources
  `LIVE_GUI_DESKTOP_MOUNT_REGION_SPECS`); embeds the component-contract report.
- **Consumers:** cli.py:455-458 + help_text.py:3141-3167, 4232 | own test (566
  LOC; also imported by `tests/test_live_gui_desktop_render_contract_report.py`,
  `tests/test_live_gui_desktop_render_harness_report.py` — in-set) | OTHER:
  `live_gui_desktop_render_contract.py` (in set).
- **Supersession:** the real view model is the typed store
  (`desktop/web/src/state/store.ts`) fed by `live_gui_protocol.ts` dicts —
  the schema-driven channel that made a paper view-model spec redundant.
- **VERDICT: RETIRE** (as set; pinned via render_contract → ①).

### 2.5 `live_gui_desktop_render_contract.py` — RETIRE (as set)

- **Emits:** "GUI desktop render contract with render surfaces, render
  bindings, style-token bindings"; embeds the view-model report.
- **Consumers:** cli.py:459-462 + help_text.py:3168-3194, 4235 | own test (591
  LOC) | OTHER: `live_gui_desktop_render_harness.py` (in set).
- **Supersession:** render-contract fields are realized as the 30+
  `LiveGui*Dict` interfaces in `desktop/web/src/types/live_gui_protocol.ts`
  (e.g. `LiveGuiRytmPadSurfaceCardDict`, `LiveGuiDeviceInventoryCardDict`,
  `LiveGuiAnalyzerPanelModelDict`, `LiveGuiHardwareRailModelDict`), pinned to
  the Python TypedDicts by
  `tests/architecture/test_live_gui_protocol_ts_matches_python_typeddicts.py`.
- **VERDICT: RETIRE** (as set; pinned via render_harness → ①).

### 2.6 `live_gui_desktop_render_harness.py` — ENTANGLED

- **Emits:** "GUI desktop render harness with surface harnesses, binding
  harnesses, style-token checks"; embeds the render-contract report.
- **Consumers:** cli.py:463-466 + help_text.py:3195-3221, 4238 | own test (562
  LOC; also imported by `tests/test_live_gui_cockpit_boundary_readiness_report.py`)
  | **OTHER: `live_gui_cockpit_boundary_readiness.py:20` — a KEPT, registered
  module** (`style-performance-arc-live-gui-cockpit-boundary-readiness-report`).
- **Supersession:** the real render harness is the vitest suite
  (`desktop/web/tests/cockpit/PerformanceConsole.test.tsx`, `Cockpit.test.tsx`,
  et al.) exercising the shipped components against fixture payloads.
- **VERDICT: ENTANGLED** — retirable once import ① is broken. This is the
  single import pinning the entire desktop chain (10 modules).

### 2.7 `live_gui_screen_contract.py` — RETIRE (as set)

- **Emits:** "GUI screen contract with ordered regions, component state, table
  rows, disabled interaction controls" (sources
  `LIVE_GUI_SCREEN_COMPONENT_SPECS` from `data/live_gui_contracts.py:65`);
  embeds the sidecar-session report (`live_gui_sidecar_session` — KEPT, and
  that dependency direction is fine: retire-candidate imports kept).
- **Consumers:** cli.py:395-398 + help_text.py:2734-2761, 4187 | own test (536
  LOC) | OTHER: `live_gui_render_tree.py` (in set, itself ENTANGLED via ②).
- **Supersession:** the screen it specifies is shipped JSX: `Cockpit.tsx`
  mounts `HeaderBar`, `DeviceRail`, `MutationPanel`, `SnapshotPanel`,
  `SafetyRail`, `LiveReadinessPanel`, `PatchGenomePanel` under
  `CockpitClientProvider`.
- **VERDICT: RETIRE** — conditional on breaking import ② (render_tree is its
  only non-self consumer and render_tree is pinned by analyzer_overlay).

### 2.8 `live_gui_render_tree.py` — ENTANGLED

- **Emits:** "GUI render tree — deterministic root/region/component tree,
  source bindings, disabled controls"; embeds the screen-contract report.
- **Consumers:** cli.py:399-402 + help_text.py:2762-2789, 4190 | own test (426
  LOC; also imported by `tests/test_live_gui_analyzer_overlay_report.py`) |
  **OTHER: `live_gui_analyzer_overlay.py:27` — KEPT, registered.**
- **Supersession:** the render tree is the React component tree itself; its
  "source bindings" concept shipped as the model→protocol→component pipeline.
- **VERDICT: ENTANGLED** — retirable once import ② is broken.

### 2.9 `live_gui_interaction_script.py` — ENTANGLED

- **Emits:** "GUI interaction script with ordered interaction steps, control
  bindings, disabled hardware locks"; embeds the analyzer-frame report
  (`live_gui_analyzer_frame` — KEPT; fine direction).
- **Consumers:** cli.py:411-414 + help_text.py:2844-2871, 4199 | own test (430
  LOC; also imported by `tests/test_live_gui_action_reducer_report.py` and
  `tests/test_live_gui_controller_state_report.py`) | **OTHER:
  `live_gui_action_reducer.py:23` — KEPT, registered.**
- **Supersession:** real interactions ship as `desktop/web/src/ws/protocol.ts`
  + `ws/client.ts` command round-trips, `cockpit/useLoggedCommand.ts`, and
  `ActionBar.tsx`/`LockButton.tsx`/`usePadLocks.ts` (hardware-lock behavior is
  live code with tests, not a script).
- **VERDICT: ENTANGLED** — retirable once import ③ is broken.

### 2.10 `live_gui_implementation_bridge.py` — RETIRE (as set)

- **Emits:** "GUI implementation bridge with view-model packets, disabled
  component mounts, fixture bundles"; embeds the test-harness-readiness report.
- **Consumers:** cli.py:439-442 + help_text.py:3033-3059, 4220 | own test (507
  LOC; also imported by `tests/test_live_gui_desktop_blueprint_report.py`,
  `tests/test_live_gui_desktop_app_plan_report.py` — in-set) | OTHER:
  `live_gui_desktop_blueprint.py` (in set).
- **Supersession:** the real implementation bridge is
  `rytm_randomizer/cockpit/ws/handlers.py` — it serves
  `live_gui_performance_console_model_payload()` over WebSocket at lines
  226-236 (`performance_console_changed` event) and 689-693 (request path).
  "Fixture bundles" ship as `desktop/web/tests/_fixtures.ts` +
  `performanceConsoleFixture.ts`.
- **VERDICT: RETIRE** (as set; pinned via blueprint → ①).

### 2.11 `live_gui_test_harness_contract.py` — RETIRE (as set)

- **Emits:** "GUI test-harness contract with harness suites, fixtures,
  bindings, blocked actions"; embeds the playback-validation report
  (`live_gui_playback_validation` — KEPT; fine direction).
- **Consumers:** cli.py:431-434 + help_text.py:2979-3005, 4214 | own test (412
  LOC; also imported by `tests/test_live_gui_test_harness_readiness_report.py`)
  | OTHER: `live_gui_test_harness_readiness.py` (in set).
- **Supersession:** the harness it contracts exists:
  `desktop/web/tests/{cockpit,a11y,wizard}`, `store.test.ts`,
  `router.test.tsx`, `ws-client.test.ts` — running vitest suites.
- **VERDICT: RETIRE** (as set; pinned via test_harness_readiness → ①).

### 2.12 `live_gui_test_harness_readiness.py` — RETIRE (as set)

- **Emits:** "GUI test-harness readiness with readiness gates, checks,
  rehearsal steps"; embeds the test-harness-contract report.
- **Consumers:** cli.py:435-438 + help_text.py:3006-3032, 4217 | own test (456
  LOC; also imported by `tests/test_live_gui_implementation_bridge_report.py`,
  `tests/test_live_gui_desktop_blueprint_report.py` — in-set) | OTHER:
  `live_gui_implementation_bridge.py` (in set).
- **Supersession:** readiness was achieved — the harness runs in CI; a paper
  readiness gate for a shipped harness has no remaining function.
- **VERDICT: RETIRE** (as set; pinned via implementation_bridge → ①).

### 2.13 `controller_brain_live_desktop_blueprint.py` — ENTANGLED

- **Emits:** "Passive desktop blueprint metadata for future controller-brain
  Cockpit work" — desktop regions, component contracts, view-model bindings,
  fixture hints, acceptance checks; composes the (kept)
  `controller_brain_live_implementation_bridge` report.
- **Consumers:** cli.py:219-222 + help_text.py:1757-1792, 4098 |
  `tests/test_controller_brain_live_desktop_blueprint_report.py` (306 LOC) |
  OTHER: `controller_brain_live_desktop_app_plan.py` (in pair, itself pinned by ④).
- **Supersession:** "future controller-brain Cockpit work" shipped — the
  `rytm_randomizer/cockpit/` package (ws handlers, data, wizard) plus the React
  cockpit. Same re-stamp shape as §2.1, one abstraction level over.
- **VERDICT: ENTANGLED** — retirable once import ④ is broken (transitively).

### 2.14 `controller_brain_live_desktop_app_plan.py` — ENTANGLED

- **Emits:** controller-brain desktop app routes, component file hints, state
  slices, style tokens, acceptance checks; embeds the cb blueprint report.
- **Consumers:** cli.py:223-226 + help_text.py:1793-…, 4101 | own test (362
  LOC) | **OTHER: `controller_brain_live_desktop_component_contract.py:13` —
  KEPT (out of audit scope), imports 5 symbols.**
- **Supersession:** as §2.2, realized by the shipped desktop/web app.
- **VERDICT: ENTANGLED** — retirable once import ④ is broken. Recommend
  follow-up audit of the rest of the cb chain
  (`…component_contract` → `…view_model` → `…render_contract`, verified same
  daisy-chain shape) so ④ becomes free.

---

## 3. Dead-wiring audit: `live_gui_safety_checklist_model.py:300-304`

`_safety_checklist_replay_command()` (lines 300-304) builds the string
`python -m rytm_randomizer.cli live-gui-safety-checklist-model-report --session-label …`
and injects it into the packet at line 365 (`replay_commands=(…)`). That CLI
command is **registered nowhere**: zero hits in `rytm_randomizer/cli.py`,
`cli_registry.py`, `help_text.py`, `docs/CLI_REFERENCE.md`, and
`tests/fixtures/cli_help_expected.txt`. Any operator pasting the replay command
gets an unknown-command error.

**VERDICT (dead registration only): RETIRE the dead wiring** — either register
the command (against the bundle's direction) or, preferred, drop/replace the
`replay_commands` entry and update `tests/test_live_gui_safety_checklist_model.py`
expectations. **The module itself is KEEP** — see §4.

---

## 4. CRITICAL KEEP-list verification

| Module | Why it must stay (verified) |
|---|---|
| `live_gui_common.py` (48 LOC) | **27 in-package importers** (verified `grep -rln` = 27). Shared helpers `format_cli_error`, `pop_option_value`, `replace_replay_command`, `status_severity` used by paper and model modules alike. |
| `live_gui_performance_console_model.py` | Runtime-consumed by `rytm_randomizer/cockpit/ws/handlers.py:229-236` (the `performance_console_changed` WebSocket event) and `:689-693` (request handler) via `live_gui_performance_console_model_payload()`. Also the module that composes `live_gui_safety_checklist_model` (`:43-45`, `:976-978`) into the payload the frontend `LiveReadinessPanel`/`PerformanceConsole` tests assert against. |
| `live_gui_performance_flow_model.py` | Frontend-pinned by `tests/architecture/test_live_gui_performance_flow_values_match_frontend.py` (file verified present). |
| Every `live_gui_*_model.py` feeding packets (`12_pad_surface`, `device_inventory`, `scene_queue`, `status_footer`, `snapshot_history`, `safety_checklist`, `command_queue`, `analyzer_panel`, `hardware_rail`, `snapshot_compatibility`, `dual_device_rig_readiness`) | Named as the *source of truth* in the `desktop/web/src/types/live_gui_protocol.ts` header and pinned field-for-field by `tests/architecture/test_live_gui_protocol_ts_matches_python_typeddicts.py`; their dicts (`LiveGui…ModelDict`) are rendered by the shipped cockpit. |

Also staying (kept consumers named in §1): `live_gui_cockpit_boundary_readiness.py`,
`live_gui_action_reducer.py`, `live_gui_analyzer_overlay.py`,
`live_gui_analyzer_frame.py`, `live_gui_sidecar_session.py`,
`live_gui_playback_validation.py`, `controller_brain_live_implementation_bridge.py`
— unless the orchestrator widens the retire set per the ①/④ recommendations.

---

## 5. Retirement checklist (per RETIRE module, after breaking imports ①-④)

For each module `<m>` in the retire set (12 live_gui + 2 controller_brain):

1. Delete `rytm_randomizer/reports/<m>.py`.
2. Delete its test file:
   `tests/test_<m>_report.py` (live_gui set: `test_live_gui_desktop_blueprint_report.py`,
   `test_live_gui_desktop_app_plan_report.py`, `test_live_gui_desktop_component_contract_report.py`,
   `test_live_gui_desktop_view_model_report.py`, `test_live_gui_desktop_render_contract_report.py`,
   `test_live_gui_desktop_render_harness_report.py`, `test_live_gui_screen_contract_report.py`,
   `test_live_gui_render_tree_report.py`, `test_live_gui_interaction_script_report.py`,
   `test_live_gui_implementation_bridge_report.py`, `test_live_gui_test_harness_contract_report.py`,
   `test_live_gui_test_harness_readiness_report.py`; cb:
   `test_controller_brain_live_desktop_blueprint_report.py`,
   `test_controller_brain_live_desktop_app_plan_report.py`).
3. Remove the `cli.py` lazy-table entry (4-line dict entries:
   screen_contract 395-398, render_tree 399-402, interaction_script 411-414,
   test_harness_contract 431-434, test_harness_readiness 435-438,
   implementation_bridge 439-442, desktop_blueprint 443-446,
   desktop_app_plan 447-450, desktop_component_contract 451-454,
   desktop_view_model 455-458, desktop_render_contract 459-462,
   desktop_render_harness 463-466; cb blueprint 219-222, cb app_plan 223-226 —
   line numbers as of HEAD `4e87d02`).
4. Remove the `help_text.py` help function + its registration line
   (function/registration pairs: screen 2734/4187, render_tree 2762/4190,
   interaction 2844/4199, harness-contract 2979/4214, harness-readiness
   3006/4217, bridge 3033/4220, blueprint 3060/4223, app_plan 3087/4226,
   component_contract 3114/4229, view_model 3141/4232, render_contract
   3168/4235, render_harness 3195/4238; cb blueprint 1757/4098, cb app_plan
   1793/4101).
5. Regenerate `tests/fixtures/cli_help_expected.txt` (28 command-name
   occurrences today) via the fixture's regen path — this is the cli_help
   fixture, **not** a v134 parity fixture.
6. Remove `docs/CLI_REFERENCE.md` rows: live_gui set at lines 590-591, 594,
   599-607; cb at lines 318-319, example block 347-350, prose sections at
   462-… and 470-….
7. `__init__` re-export: **none to remove** — `rytm_randomizer/reports/__init__.py`
   re-exports no live_gui/controller_brain module (verified).
8. Remove/refresh the `_GRANDFATHERED_DUPLICATE_NAMES` entries in
   `tests/architecture/test_abstraction_reuse.py` that reference retired files
   (**178 line references** to the 12 modules today). The allowlist's own rule 2
   says entries must be removed when the duplicate disappears, and the
   stale-tuple companion check fails on leftover paths.
9. Remove the modules' entries from the parametrized command lists in
   `tests/test_cli.py` and `tests/test_cli_coverage.py`.
10. After the full live_gui desktop set retires, `data/live_gui_contracts.py`
    specs `LIVE_GUI_DESKTOP_VIEWPORT_SPECS`, `LIVE_GUI_DESKTOP_REGION_SPECS`,
    `LIVE_GUI_DESKTOP_MOUNT_REGION_SPECS`, `LIVE_GUI_DESKTOP_APP_STYLE_TOKEN_SPECS`,
    `LIVE_GUI_SCREEN_COMPONENT_SPECS` lose their only package consumers
    (blueprint, app_plan, view_model, screen_contract) — follow-up removal
    candidate together with `tests/test_live_gui_contract_data.py` and the
    `data/__init__.py` re-exports.
11. Dead wiring fix (independent of the set): drop/replace the unregistered
    replay command in `live_gui_safety_checklist_model.py:300-304, 365` and
    update `tests/test_live_gui_safety_checklist_model.py`.
12. Docs gate: touch `docs/STATUS.md` (and this plan doc links from the PR body).

---

## 6. LOC removed by the RETIRE set

| Bucket | LOC |
|---|---|
| 12 `live_gui_*` paper modules | **13,014** |
| Their 12 test files | **6,085** |
| 2 `controller_brain_live_desktop_*` modules | **1,421** |
| Their 2 test files | **668** |
| cli.py + help_text.py + CLI_REFERENCE.md blocks (est.) | ~450 |
| **Total (all four imports broken)** | **≈ 21,600** |

If only the clean in-set retirements were executed *without* breaking imports
①-④, **zero** modules could be removed — every candidate is transitively pinned
by one of the four kept-module imports. The entire payoff hinges on those four
import breaks (or on widening the retire set per §1's recommendation).

---

## 7. Execution record (2026-07-28, branch `rival-program`)

> Status of this doc: executed. Maintainer approval on record (2026-07-22,
> Decision Gate ③): the full enumerated list was approved, with the 4
> widening candidates to be audited under the same rubric and auto-included
> on PASS.

### 7.1 Widening-audit verdicts (all four PASS → joined the retire set)

| Candidate | Verdict | Evidence |
|---|---|---|
| `live_gui_cockpit_boundary_readiness.py` (968 LOC) | **PASS — retired** | Paper "readiness" spec for the cockpit boundary that shipped: the real boundary is `rytm_randomizer/cockpit/ws/handlers.py` serving `live_gui_performance_console_model_payload()` over WebSocket to the React cockpit (`desktop/web/src/ws/client.ts` → `Cockpit.tsx`), with arming kept behind `python -m rytm_randomizer.app --arm`. Non-self consumers: none — only its cli.py/help_text.py registration, its own test file, and arch-test census entries (verified by repo-wide grep). Deleting it made break ① free (its import was the single pin on the 10-module desktop chain). |
| `controller_brain_live_desktop_component_contract.py` (864 LOC) | **PASS — retired** | Same re-stamp shape as §2.3, one abstraction level over ("Passive desktop component-contract metadata for **future** controller-brain Cockpit work" — that work shipped as the 20 cockpit components under `desktop/web/src/cockpit/` + `desktop/web/tests/cockpit/*.test.tsx`). Only non-self consumer: `controller_brain_live_desktop_view_model.py` (in this candidate set). |
| `controller_brain_live_desktop_view_model.py` (805 LOC) | **PASS — retired** | Supersession per §2.4: the real view model is `desktop/web/src/state/store.ts` fed by `live_gui_protocol.ts` dicts. Only non-self consumer: `controller_brain_live_desktop_render_contract.py` (in this candidate set). |
| `controller_brain_live_desktop_render_contract.py` (819 LOC) | **PASS — retired** | Supersession per §2.5: render-contract fields realized as the `LiveGui*Dict` interfaces in `desktop/web/src/types/live_gui_protocol.ts`, mechanically pinned to the Python TypedDicts. Non-self consumers: none. |

With ① and ④ freed by the audit, only breaks ② and ③ required code motion.

### 7.2 How breaks ② and ③ were executed (byte-frozen kept commands)

The kept commands embed the full upstream packet, so "drop the section"
(option a) was ruled out by the byte-frozen goldens. Executed as verbatim
relocation/inlining of the builder machinery (dataclasses, packet builders,
JSON renderers, CLI arg parsers, usage/id/version constants), dropping only
each retired module's CLI registration, text formatter, and `__all__`:

- **② `live_gui_analyzer_overlay` → `live_gui_render_tree` (+ transitively
  `live_gui_screen_contract`):** builders relocated verbatim (no renames) to
  the new support subpackage `rytm_randomizer/reports/live_gui_overlay/`
  (`screen_contract.py` 1054 LOC, `render_tree.py` 778 LOC — both under the
  1,500-LOC reports comprehensibility cap; a single-file inline was rejected
  by `tests/architecture/test_reports_max_module_size.py` at 2,630 LOC).
  `live_gui_analyzer_overlay.py` is otherwise byte-identical to its previous
  version except the import source.
- **③ `live_gui_action_reducer` → `live_gui_interaction_script`:** the needed
  interaction-script machinery was inlined verbatim into
  `live_gui_action_reducer.py` (now 1,291 LOC, under the cap), with colliding
  private helpers carrying an `_interaction_script` prefix and the
  byte-identical shared `_normalize_nonblank` / `_test_id` helpers kept once.
  `action_reducer` now imports the (kept) `live_gui_analyzer_frame` builders
  directly.

**Byte-identity verification:** with `style_analysis` clocks frozen (the
`FeatureReport.derived_at` timestamp is second-precision wall clock), the
pre/post outputs of `…analyzer-overlay-report`, `…action-reducer-report`,
`…analyzer-frame-report`, and `…controller-state-report` were captured across
14 invocations (text, JSON, option-heavy incl. `--render-target/--density/
--viewport/--scope/--labels`, and 6 error paths incl. invalid render-target/
density/viewport, blank label, and bad-usage) — all byte-identical, including
the retired upstream `_USAGE` strings and replay-command text that the frozen
outputs embed.

### 7.3 Deleted set (50 files)

18 report modules: the 12 §1 live_gui paper specs, `live_gui_cockpit_boundary_readiness`,
`controller_brain_live_desktop_{blueprint,app_plan,component_contract,view_model,render_contract}`.
18 test files (one per module). 10 controller-brain-desktop report goldens.
4 orphaned data-layer dump fixtures (`LIVE_GUI_DESKTOP_{VIEWPORT,REGION,MOUNT_REGION,APP_STYLE_TOKEN}_SPECS.json`).

Unwired in place: 18 cli.py lazy-table entries, 18 help_text.py help
functions + registrations + 18 top-level USAGE segments + 18 `--help` usage
lines, 32 `docs/CLI_REFERENCE.md` lines, the retired commands' entries in
`tests/test_cli.py` (12 readme-mention tests + USAGE literal),
`tests/test_cli_coverage.py` (65 statements), and
`tests/test_real_midi_passive_cli_safety.py` (26 invocation tuples).
`data/live_gui_contracts.py` kept only `LIVE_GUI_SCREEN_COMPONENT_SPECS`
(still consumed by the relocated screen-contract builder); the four desktop
spec tables and their dataclasses were deleted with their `data/__init__.py`
re-exports and test.

Dead wiring (§3): `_safety_checklist_replay_command()` removed from
`live_gui_safety_checklist_model.py`; the packet now ships
`replay_commands=()`. Regenerated nets confirmed the only kept-golden delta
is exactly that removal (`live-gui-performance-console-report.json.txt` and
`desktop/web/tests/cockpit/fixtures/performance_console.json`, three lines
each); `desktop/web/src/types/live_gui_protocol.ts` regenerated identical.

Arch-test allowlists: 64 census lines pruned from
`test_report_module_shape.py`; `_GRANDFATHERED_DUPLICATE_NAMES` in
`test_abstraction_reuse.py` updated per the test's own prescriptions (31
entries removed outright, 21 rewritten to the surviving duplicate sets, then
13 rewritten again for the subpackage paths); no new allowlist names added.

### 7.4 Gates

- `tests/architecture/` — 673 passed.
- Affected test modules (cli, cli_coverage, passive-safety, report goldens,
  data layer, safety-checklist, performance-console, analyzer-overlay,
  action-reducer, analyzer-frame, controller-state) — 516 passed.
- Full suite + ruff/black/isort — see the bundle PR gate log.

Net diff (excluding pre-existing CRLF churn on untouched files):
78 files changed, ~+6,800 / −46,300 lines; 50 files deleted.
