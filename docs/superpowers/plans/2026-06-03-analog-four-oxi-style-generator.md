# Analog Four OXI-Style Generator Slice

Status: in-flight

## Purpose

Add the first passive Analog Four OXI-style macro planning surface without
moving the project closer to uncontrolled hardware behavior.

## Scope

This slice adds:

- manual-backed Analog Four OXI macro data in `rytm_randomizer/data/`
- a passive in-memory report in `rytm_randomizer/reports/`
- a passive CLI command:
  `python -m rytm_randomizer.cli analog-four-oxi-macro-report`
- tests for data immutability, deterministic report generation, JSON output,
  passive CLI help, and no real-MIDI imports

## Safety Boundary

This slice does not add:

- real MIDI rendering
- MIDI sending
- MIDI port opening
- active CLI execution
- app/runtime send wiring
- SysEx writes
- hardware mutation
- Analog Four hardware validation

The new command is report-only. It previews deterministic four-track values
from the existing manual-backed Analog Four CC table so future cockpit and
hardware-gated work has a visible vocabulary to review first.

## Macro Vocabulary

- `home`
- `hard-groove`
- `dub-pressure`
- `industrial-transition`

Each macro covers Analog Four tracks 1-4 and only references parameters already
present in `rytm_randomizer/data/analog_four_midi.py`.

## Test Plan

- `python -m pytest tests/test_analog_four_oxi_macros.py -n 0`
- `python -m pytest tests/test_analog_four_oxi_macro_report.py -n 0`
- `python -m pytest tests/test_cli.py -n 0`
- `python -m pytest tests/test_real_midi_passive_cli_safety.py -n 0`
- architecture and lint gates before PR

## Next Safe Branch

After this PR is reviewed, the next safe branch is either:

- cockpit UI display of these passive A4 macro names and preview rows, or
- a docs/test-only A4 hardware validation plan for one approved macro row.

Do not wire these macros into `rytm_randomizer.app` or a SEND path until a
separate review explicitly approves that hardware-facing step.
