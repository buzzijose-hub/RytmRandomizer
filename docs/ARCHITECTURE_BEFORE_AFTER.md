# Architecture Before / After — Simplification Run (PR #35)

Side-by-side view of `rytm_randomizer/` before and after the Wave 1 bundle. Top-level module count and new subpackage / Protocol / dataclass surface.

---

## Top-level files in `rytm_randomizer/`

### Before (base: `modularize-v1.34` @ `0bd46aa`, ~37 top-level entries)

```
__init__.py                              behavior_anchor_profile.py
active_boundary.py                       behavior_menu_utility.py
app.py                                   behavior_mutation_depth.py
cli.py                                   behavior_pad_lane.py
commands.py                              behavior_scene_group.py
constants.py                             behavior_selected_isolated_pad.py
data/                                    behavior_selected_profile.py
engines/                                 behavior_undo_commit_state.py
group_runner.py                          state/
guardrails/                              style_analysis/
help_text.py                             validation.py
inspection.py
midi_io.py                               anchor_state.py
mido_provider.py                         selected_target_state.py
mock_message_mapper.py                   selected_isolated_pad_runtime_state.py
mock_midi.py
mock_runtime_active_bridge.py
observability/   (logging, tracing, errors)
profile_lookup.py
profiles.py
project_status_report.py
randomization.py
real_midi_adapter.py
registry.py
reports.py        (single module)
runtime_plan.py
scene_runner.py
scenes.py
shell.py
```

8 `behavior_*.py` files at top level. 3 `*_state.py` validation-only modules at top level. `reports.py` a single file. No `devices/` or `snapshot/` subpackage. No `cli_registry.py`. No `observability/metrics.py`. No `data/modes.py`.

### After (Wave 1 bundle on `refactor/wave1-bundled`)

```
__init__.py                              behavior/                   <-- NEW subpackage (was 8 top-level)
active_boundary.py                          anchor_profile.py
app.py                                      menu_utility.py
cli.py                                      mutation_depth.py
cli_registry.py            <-- NEW          pad_lane.py
commands.py                                 scene_group.py
constants.py                                selected_isolated_pad.py
data/                                       selected_profile.py
   modes.py                <-- NEW          undo_commit_state.py
devices/                   <-- NEW         state/
   __init__.py                                anchor_validation.py            <-- relocated (was top-level)
   base.py                                    selected_target_validation.py   <-- relocated
   registry.py                                selected_isolated_pad_validation.py <-- relocated
   analog_rytm.py
engines/                                 snapshot/                   <-- NEW subpackage
group_runner.py                             __init__.py
guardrails/                                 envelope.py
help_text.py                                decoder.py
inspection.py                               planner.py
midi_io.py                                  mock_runtime.py
mido_provider.py                         style_analysis/
mock_message_mapper.py                   validation.py
mock_midi.py
mock_runtime_active_bridge.py
observability/
   logging.py
   tracing.py
   errors.py
   metrics.py              <-- NEW
profile_lookup.py
profiles.py
project_status_report.py
randomization.py
real_midi_adapter.py
registry.py
reports/                   <-- NEW (was single file)
   __init__.py
   formatter.py
runtime_plan.py
scene_runner.py
scenes.py
shell.py
```

Net change: 4 new subpackages (`devices/`, `snapshot/`, `behavior/`, `reports/`), 4 new top-level entries collapse into them, ~5 new boundary files.

---

## New Protocols (cross-layer boundaries)

| Protocol | Location | Replaces | Consumers |
|---|---|---|---|
| `MidiSender` | `midi_io.py` | 6 `Sender = Any` aliases across shell.py + group_runner.py + engines/pad{1..4}.py | every layer that sends MIDI |
| `PadRuntimeState` | `engines/_runtime.py` | duck-typed mixin attribute contract | future pad engines (track-count-agnostic) |
| `IsolatedPadState` | `engines/_runtime.py` | duck-typed isolated-pad mixin | future single-pad engines |
| `Device` (`@runtime_checkable`) | `devices/base.py` | (none — new cross-machine boundary) | `devices/analog_rytm.py`, future `devices/analog_four.py` etc. |
| `MidiOutbox` | `devices/base.py` | (none — new outbound MIDI surface) | every `Device` implementation |
| `SnapshotDecoder` (`@runtime_checkable`) | `snapshot/decoder.py` | hand-rolled per-device decoder shims | PR #21 Analog Four work |
| `MutationPlanner` (`@runtime_checkable`) | `snapshot/planner.py` | hand-rolled per-device planner shims | PR #21 Analog Four work |
| `MockRuntime` (`@runtime_checkable`) | `snapshot/mock_runtime.py` | duplicated `BaseMockRuntime` per device | PR #21 Analog Four work |

---

## New frozen dataclasses (DTOs at module boundaries)

| Dataclass | Location | Purpose |
|---|---|---|
| `PadRuntime` | `engines/_runtime.py` | Composable mutable runtime state for new engines (replaces mixin inheritance) |
| `PassiveReportHeader` | `reports/formatter.py` | The canonical "Safety:" + "Source:" + "In-memory only: True" header data |
| `MidiMetrics` | `observability/metrics.py` | `Counter` fields: `cc_sent_by_channel`, `cc_blocked_by_guardrail_by_pad`, `errors_by_kind` |
| `CliCommand` | `cli_registry.py` | Registry row: `name`, `short_help`, `long_help`, `handler` |
| `DispatchEntry` | `shell.py` | Special-shaped command row with `kind` taxonomy (simple/quit/reselect/scene_lookup/depth_guard/depth_prompt/unknown) |
| `AnalogRytmDevice` | `devices/analog_rytm.py` | Concrete `Device` implementation registered at import time |

---

## Retired / deprecated surface

| Symbol | Status | Replacement |
|---|---|---|
| `Sender = Any` (6 sites) | retired | `MidiSender(Protocol)` |
| `behavior_*.py` (8 top-level) | relocated | `behavior/*.py` (history preserved via `git mv`) |
| `anchor_state.py`, `selected_target_state.py`, `selected_isolated_pad_runtime_state.py` (3 top-level) | relocated | `state/{anchor,selected_target,selected_isolated_pad}_validation.py` |
| `reports.py` (single file) | converted | `reports/` subpackage |
| Inline `RecordingOut` / `_FakeMessage` / `_install_fake_mido` / `_no_sleep` in 8 test files | retired (318 LOC) | `tests/conftest.py` (single source) |

---

## Cross-references

- `docs/ARCHITECTURE.md` — full architecture description (updated by `doc-updater` phase 9 of each WS).
- `docs/ARCHITECTURE_DIAGRAMS.md` — code-derived dependency maps.
- `docs/PR21_MODULE_MAPPING.md` — codex's 33 new top-level files mapped to the new Protocols / subpackages.
