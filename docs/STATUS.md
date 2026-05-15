# RytmRandomizer - Project Status

Last updated: 2026-05-14. This file is a hand-authored snapshot and is meant to be updated in place, never appended.

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
