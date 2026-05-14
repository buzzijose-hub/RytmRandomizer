# RytmRandomizer — Project Status

Last updated: 2026-05-14. This file is a hand-authored snapshot and is meant to
be updated in place, never appended.

## Current Version

**V1.34** — `rytm_hybrid_randomizer_v134.py` at the repository root.
Stable tag: `v1.34-stable-expanded-scene-layer`. Working branch: `modularize-v1.34`.

## What Works

- **The monolith is the tool.** `rytm_hybrid_randomizer_v134.py` is the
  hardware-validated MIDI randomizer/mutator for the Elektron Analog Rytm MK2.
  It opens a MIDI port (via `mido`) and sends CC messages to hardware. This is
  the only component that touches hardware, and it is the supported way to run
  RytmRandomizer today.
- It covers Pads 1-4: BD engine anchors/discovery (Pad 1), snare/secondary
  percussion (Pad 2), SY Raw bass (Pad 3), BD Acoustic (Pad 4), a 4-pad group
  layer, scenes (S0-S5 plus variants), isolated single-pad mutation, and
  legacy single-profile mutation.

## What's In Progress

- **Modularization** of the monolith into an installable package under
  `rytm_randomizer/`. The goal is a unified, importable package that
  eventually reaches behavior parity with V1.34.
- The package is currently **passive / read-only**. It does not open MIDI
  ports or send MIDI. `rytm_randomizer/app.py` is a placeholder entry point;
  `rytm_randomizer/cli.py` exposes only inspection/report/list/search/preview
  commands over copied passive metadata.
- The package carries passive metadata registries (commands, scenes,
  profiles), behavior-parity evaluators, mock MIDI/mapping layers, and a
  guarded active boundary — all non-executing scaffolding.
- ~48 hardware-free tests under `tests/` validate metadata shape and safety
  constraints. `Scripts/closeout_check.ps1` runs them and verifies the V1.34
  reference file diff stays empty.

## Known Gaps

- The modular package cannot drive hardware. There is no active runtime,
  no real MIDI sending, no command dispatch — use the V1.34 monolith for that.
- Behavior parity between the package and V1.34 is partial and ongoing.
- Out of scope for the current phase: Pads 5-12, additional machines/profiles,
  new CC mappings, GUI/capture, SysEx, and Analog Four support.
- A creative project rename is parked (see `docs/PROJECT_IDENTITY_*`); the
  project ships as rytm-randomizer.

## Reference Docs

- `docs/ARCHITECTURE_DIAGRAMS.md` — current code-derived architecture maps.
- `docs/MODULARIZATION_RULES.md`, `docs/CODEX_MODULARIZATION_PROTOCOL.md`,
  `docs/CODEX_REFACTOR_PROMPT.md` — modularization constraints and protocol.
- `docs/V134_OPERATOR_COMMAND_SURFACE_REFERENCE.md` — the V1.34 command surface.
- `docs/PASSIVE_CLI_OPERATOR_QUICKSTART.md` — how to run the passive CLI.
- `docs/HARDWARE_MANUAL_REFERENCE_INVENTORY.md`,
  `docs/LOCAL_DEV_TOOLING_NOTES.md` — reference/tooling notes.
- `docs/TRIAGE_REPORT.md` — audit record of the Docs/ accuracy triage.
