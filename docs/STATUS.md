# RytmRandomizer - Project Status

Last updated: 2026-05-17. This file is a hand-authored snapshot and is meant to be updated in place, never appended.

## Recent Cleanup

- 2026-05-17: resolved the test-only API audit. Removed 4 dead modules/blocks (~219 LOC of production code + ~452 LOC of tests/closeout invocations): the `command_lookup.py` + `scene_lookup.py` modules, the 3 unused getters in `profile_lookup.py`, the `_sync_channel_from_group_runner()` no-op stub in `shell.py`, the unused `REPORT_KEYS`/`build_report`/`format_report`/`summarize_report` dispatcher in `reports.py`, and the `registry_report.py` shim (re-homed into `python -m rytm_randomizer.cli report`). Documented 12 kept items as the "V1.34 parity API surface" in docs/ARCHITECTURE.md so future dead-code audits stop re-flagging them.
- 2026-05-15: extracted PadRuntimeMixin (engines/_runtime.py) consolidating ~150 LOC duplicated across 5 engines/runners. No behavior change.
- 2026-05-15: dead-code audit removed three trivially-unused symbols (`_lazy_rehome_imports` in `observability/errors.py`, `log_extra` in `observability/logging.py`, the unused `self._provider` bookkeeping in `RealMidiSender.__init__`). No behavior change; 197 tests still green.
- 2026-05-15: extracted scene_menu_lines() data-driven generator; dedupes scene menu strings across shell.py + scene_runner.py + SCENE_PRESETS. No output change.
- 2026-05-16: shell.dispatch converted from a 92-arm if/elif chain (~396 LOC) to a module-level `_DISPATCH` table where each uniform arm is a one-line closure. Special-shaped arms (quit, target/profile re-selection that updates `self.channel`, scene preset lookup, depth-guardrail 1/2/3 message, depth-prompting zone mutations, unknown-command fallback) stay inline. shell.py net ~186 LOC reduction. Behavior byte-identical: full parity suite green.
- 2026-05-16: small-gap coverage tests added in tests/test_coverage_small_gaps.py — plugs single-branch holes in active_boundary, mock_midi, inspection, and validation (8 tests total). Bumps pure-branch coverage per the ratchet.

## Current Version

**V1.34** musical behavior, owned end-to-end by the modular package as of Wave 4 / WS-O. Stable tag: `v1.34-stable-expanded-scene-layer`. Working branch: `wave-4-integration`.

## What Works

- **The package IS the tool.** `pip install rytm-randomizer` provides the `rytm-randomizer` console entry point. It opens a real MIDI port (via the `mido`-backed provider in `rytm_randomizer.mido_provider`) and sends CC messages to the Elektron Analog Rytm MK2 hardware. Three modes are exposed by `rytm_randomizer.app`:
  - **Default (no flag)**: passive read-only inspection / preview menu. Opens no port, sends no MIDI.
  - `--arm`: opens a real MIDI port and runs the interactive command shell (`rytm_randomizer.shell.InteractiveShell`). This is the supported way to drive the Rytm.
  - `--dry-run`: runs the same interactive command shell against `rytm_randomizer.mock_midi.MockMidiSender`. No hardware, no port opened.
- Pad coverage is complete relative to V1.34: BD engine anchors/discovery (Pad 1), snare/secondary percussion (Pad 2), SY Raw bass (Pad 3), BD Acoustic (Pad 4), a four-pad group layer, scenes (S0-S5 plus variants), isolated single-pad mutation, legacy single-profile mutation, and the full command surface.
- The V1.34 monolith (`rytm_hybrid_randomizer_v134.py`) is retained on disk byte-for-byte as a frozen reference for the byte-parity tests (`tests/test_engines_pad*`, `tests/test_group_runner.py`, `tests/test_scene_runner.py`). It is not invoked by any production code path.

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
- `docs/MODULARIZATION_RULES.md`, `docs/CODEX_MODULARIZATION_PROTOCOL.md`, `docs/CODEX_REFACTOR_PROMPT.md` -- modularization constraints and protocol.
- `docs/V134_OPERATOR_COMMAND_SURFACE_REFERENCE.md` -- the V1.34 command surface, as preserved by `rytm_randomizer.shell`.
- `docs/PASSIVE_CLI_OPERATOR_QUICKSTART.md` -- how to run the passive CLI.
- `docs/HARDWARE_MANUAL_REFERENCE_INVENTORY.md`, `docs/LOCAL_DEV_TOOLING_NOTES.md` -- reference/tooling notes.
- `docs/TRIAGE_REPORT.md` -- audit record of the `docs/` accuracy triage.
