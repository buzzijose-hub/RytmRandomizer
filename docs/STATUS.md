# RytmRandomizer - Project Status

Last updated: 2026-05-18. This file is a hand-authored snapshot and is meant to be updated in place, never appended.

## Recent Cleanup

- 2026-05-18: WS-S5 — Device protocol + registry + AnalogRytmDevice wrapper. NEW rytm_randomizer/devices/{base,registry,analog_rytm}.py subpackage. `Device(@runtime_checkable Protocol)` declares the cross-machine boundary (device_id, display_name, default_midi_channel, track_count, sysex_manufacturer_id + decode_snapshot/plan_mutation/to_mock_messages/to_cc_messages). `MidiOutbox(Protocol)` for the outbound MIDI surface devices write to. `AnalogRytmDevice` wrapping class registers at import time so `get_device("analog_rytm_mk2")` resolves out of the box. 13 conformance tests verify Protocol shape, registry semantics, AnalogRytmDevice stub method types, and a PR #21 forward-compat test (arbitrary hand-rolled Device satisfies isinstance). Existing engine code unchanged; stub bodies expand when PR #21's snapshot path lands.
- 2026-05-18: WS-S2 — PadRuntimeState + IsolatedPadState `@runtime_checkable` Protocols + composable `PadRuntime` mutable dataclass added to engines/_runtime.py. Replaces the duck-typed mixin attribute contract with a pyright-static surface. Track-count-agnostic (no hard-coded 4); PR #21's pad-12 engines satisfy without change. Existing Pad{1-4}Engine + GroupRunner continue inheriting PadRuntimeMixin / IsolatedPadMixin (the additive change keeps the 505 V1.34 parity fixtures byte-identical); new engines should compose PadRuntime instead. 11 new conformance tests in tests/test_pad_runtime_protocol.py.
- 2026-05-18: WS-M2 — behavior/ subpackage relocation. 8 top-level behavior_*.py moved into behavior/ subpackage via git mv (history preserved); imports updated across the package and ~28 test files. Plus 3 inert-validation modules (anchor_state.py, selected_target_state.py, selected_isolated_pad_runtime_state.py) relocated to state/{anchor,selected_target,selected_isolated_pad}_validation.py with class names preserved. state/__init__.py extends to re-export the 3 new submodules. AnchorRuntimeState (state/anchor.py) and AnchorState (state/anchor_validation.py) coexist as distinct classes per the design. tests/architecture/test_import_direction.py's state-layer allowlist documents the 3 inert-validation modules' use of ..commands. tests/architecture/test_house_style.py excludes the 3 _validation.py modules from core-annotation enforcement (their bodies predate the standard; same exclusion as their previous top-level location).
- 2026-05-18: WS-M4 — test ergonomics. NEW tests/conftest.py centralizes RecordingOut + _FakeMessage + _install_fake_mido + _no_sleep (Gate 11 single-source-of-truth). Stripped 318 LOC of duplicated fixtures from 8 test files. tests/_parity_worker.py gained _update_index that writes tests/fixtures/v134_parity/_INDEX.json in capture mode only (Gate 13 safe default). pyproject.toml registers the `fast` marker; pytestmark = pytest.mark.fast applied to 77 non-parity test files; `pytest -m fast` is the new fast-iteration loop. 4 architecture tests added (test_shared_fixtures_available, test_parity_index_writer, test_fast_marker_coverage, plus test_layering_structure update for reports/). Full suite: 2157 passed, 685 V1.34 parity fixtures byte-identical.
- 2026-05-18: WS-S3 — closed the 8-arm if/elif tail in shell.dispatch. NEW DispatchEntry frozen dataclass with kind taxonomy: simple/quit/reselect/scene_lookup/depth_guard/depth_prompt/unknown. _SPECIAL map keys the 11 special-shaped commands (q/t/p/1/2/3/s/f/a/g/k) to typed DispatchEntry rows. Dispatcher consults SCENE_PRESETS first, then _SPECIAL (with kind-based branching), then _DISPATCH (84 uniform arms unchanged), then unknown-fallback. PR #21 forward-compat: codex's planned commands fit existing kinds without new taxonomy. 740/740 tests green incl. all 505 parity fixtures + 55 CLI golden tests.
- 2026-05-18: WS-M1 — docs curation pass. 19 process-exhaust files moved to `docs/archive/` via `git mv` (codex briefs, collaborator-review intake / triage / status checkpoints, public-API hardening checkpoints, project-identity rename parking, hardware-manual inventory, passive CLI quickstart, triage report). New `docs/README.md` index classifies the 11 active onboarding files + 4 ops references + orchestrator state files. New `docs/archive/README.md` documents the historical buckets. Reference-rot fix: `rytm_randomizer/project_status_report.py` constants + matching test/fixture updated to point at the new archive paths. Active onboarding count: 11 ≤ 12 cap.
- 2026-05-18: WS-S4 — extracted PassiveReportFormatter. New `rytm_randomizer/reports/formatter.py` holds the canonical "Safety:" header literal, "Source: rytm_randomizer.{module}" trailer template, "In-memory only: True" memory line, and `PassiveReportHeader` frozen dataclass + `safety_section_lines` / `passive_footer_lines` / `render_passive_report` / `passive_report_lines` helpers. Converted `reports.py` → `reports/__init__.py` subpackage per Gate 9 (subpackage by default). Migrated 4 trailing-footer call sites (registry, mock_mapper, runtime_plan, mock_runtime_active_bridge) and 2 safety-iterate call sites (anchor_profile, project_status). All 109 golden-fixture tests byte-identical; 685/685 parity fixtures green. Eliminates 6 sites of duplicated `"Source:"` + `"In-memory only: True"` literals.
- 2026-05-18: WS-S1 — introduced `MidiSender(Protocol)` in `midi_io.py`; retired 6 `Sender = Any` escape hatches across `shell.py`, `group_runner.py`, `engines/pad{1-4}.py` (founding instance of Gate 6 type-system hygiene). Flattened the redundant `__class__.__name__` string-sniff in `send_cc`. 685/685 parity tests green; 9 new Protocol-conformance tests added.
- 2026-05-17: resolved the test-only API audit. Removed 4 dead modules/blocks (~219 LOC of production code + ~452 LOC of tests/closeout invocations): the `command_lookup.py` + `scene_lookup.py` modules, the 3 unused getters in `profile_lookup.py`, the `_sync_channel_from_group_runner()` no-op stub in `shell.py`, the unused `REPORT_KEYS`/`build_report`/`format_report`/`summarize_report` dispatcher in `reports.py`, and the `registry_report.py` shim (re-homed into `python -m rytm_randomizer.cli report`). Documented 12 kept items as the "V1.34 parity API surface" in docs/ARCHITECTURE.md so future dead-code audits stop re-flagging them.
- 2026-05-17: retired the V1.34 `rytm_hybrid_randomizer_v134.py` monolith (2,950 LOC). Its reference behavior is now frozen as ~505 JSON goldens under `tests/fixtures/v134_parity/`; the parity test files (`test_engines_pad*`, `test_group_runner.py`, `test_scene_runner.py`) compare the engine output to those fixtures instead of to a live monolith run. `_parity_worker.py` gained capture/check modes (`PARITY_CAPTURE_MODE=1` regenerates fixtures). Future package changes are gated against the snapshot rather than against a running monolith.
- 2026-05-15: extracted PadRuntimeMixin (engines/_runtime.py) consolidating ~150 LOC duplicated across 5 engines/runners. No behavior change.
- 2026-05-15: dead-code audit removed three trivially-unused symbols (`_lazy_rehome_imports` in `observability/errors.py`, `log_extra` in `observability/logging.py`, the unused `self._provider` bookkeeping in `RealMidiSender.__init__`). No behavior change; 197 tests still green.
- 2026-05-15: extracted scene_menu_lines() data-driven generator; dedupes scene menu strings across shell.py + scene_runner.py + SCENE_PRESETS. No output change.
- 2026-05-16: shell.dispatch converted from a 92-arm if/elif chain (~396 LOC) to a module-level `_DISPATCH` table where each uniform arm is a one-line closure. Special-shaped arms (quit, target/profile re-selection that updates `self.channel`, scene preset lookup, depth-guardrail 1/2/3 message, depth-prompting zone mutations, unknown-command fallback) stay inline. shell.py net ~186 LOC reduction. Behavior byte-identical: full parity suite green.
- 2026-05-16: small-gap coverage tests added in tests/test_coverage_small_gaps.py — plugs single-branch holes in active_boundary, mock_midi, inspection, and validation (8 tests total). Bumps pure-branch coverage per the ratchet.
- 2026-05-17: coverage on observability/logging.py raised from 57% to 100% via tests/test_observability_logging.py.
- 2026-05-17: coverage on app.py raised from 69% to 100% via additional tests in tests/test_app_entry.py (covers --arm port-open production path, list_output_names dependency/port errors, _choose_arm_port_name EOF / invalid / out-of-range branches, --dry-run shell EOF swallowing, --arm/--dry-run mutually-exclusive flag conflict, unknown-flag rejection, --debug/--log-json passive boot). No behavior change.
- 2026-05-17: coverage on cli.py raised from 5% to 100% via tests/test_cli_coverage.py additions. Closes the largest single coverage gap in the package.
- 2026-05-17: coverage on mido_provider.py raised from 33% to 100% via tests/test_mido_provider.py.

## Current Version

**V1.34** musical behavior, owned end-to-end by the modular package as of Wave 4 / WS-O. Stable tag: `v1.34-stable-expanded-scene-layer`. Working branch: `wave-4-integration`.

## What Works

- **The package IS the tool.** `pip install rytm-randomizer` provides the `rytm-randomizer` console entry point. It opens a real MIDI port (via the `mido`-backed provider in `rytm_randomizer.mido_provider`) and sends CC messages to the Elektron Analog Rytm MK2 hardware. Three modes are exposed by `rytm_randomizer.app`:
  - **Default (no flag)**: passive read-only inspection / preview menu. Opens no port, sends no MIDI.
  - `--arm`: opens a real MIDI port and runs the interactive command shell (`rytm_randomizer.shell.InteractiveShell`). This is the supported way to drive the Rytm.
  - `--dry-run`: runs the same interactive command shell against `rytm_randomizer.mock_midi.MockMidiSender`. No hardware, no port opened.
- Pad coverage is complete relative to V1.34: BD engine anchors/discovery (Pad 1), snare/secondary percussion (Pad 2), SY Raw bass (Pad 3), BD Acoustic (Pad 4), a four-pad group layer, scenes (S0-S5 plus variants), isolated single-pad mutation, legacy single-profile mutation, and the full command surface.
- The V1.34 reference behavior is preserved as JSON goldens under `tests/fixtures/v134_parity/`. The original `rytm_hybrid_randomizer_v134.py` monolith was retired in 2026-05-17; the parity tests (`tests/test_engines_pad*`, `tests/test_group_runner.py`, `tests/test_scene_runner.py`) now compare engine output to those fixtures via `tests/_parity_worker.py`.

## Decomposition Complete

Wave 4 is closed. The monolith decomposition extracted, in order:

- **WS-K** -- MIDI I/O primitives + randomization core (`rytm_randomizer.midi_io`, `rytm_randomizer.randomization`).
- **WS-L** -- per-domain runtime state (`rytm_randomizer.state.*`).
- **WS-M** -- per-pad engines (`rytm_randomizer.engines.pad1` .. `pad4`).
- **WS-N** -- group + scene orchestration (`rytm_randomizer.group_runner`, `rytm_randomizer.scene_runner`).
- **WS-O** -- the interactive command shell and final convergence (`rytm_randomizer.shell.InteractiveShell` + the wired-up `rytm_randomizer.app.main`).

Each step is locked against the V1.34 reference by characterization tests.

## What's Next

- A more detailed `docs/ARCHITECTURE.md` map of the post-decomposition package (planned).
- Further hardening: coverage policy, lint baseline, type-check baseline.
- Out of scope for now: Pads 5-12, additional machines/profiles, new CC mappings, GUI/capture, SysEx, and Analog Four support.

## Reference Docs

- `docs/ARCHITECTURE_DIAGRAMS.md` -- current code-derived architecture maps.
- `docs/MODULARIZATION_RULES.md` -- modularization constraints. (Historical CODEX briefs moved to `docs/archive/`.)
- `docs/V134_OPERATOR_COMMAND_SURFACE_REFERENCE.md` -- the V1.34 command surface, as preserved by `rytm_randomizer.shell`.
- `docs/LOCAL_DEV_TOOLING_NOTES.md` -- tooling notes. (Historical operator quickstarts + manual inventory + 2026-05-14 docs accuracy triage moved to `docs/archive/`.)
