# Analog Rytm MIDI Catalog Implementation Plan

> Status: in-flight (branch codex/rytm-snapshot-pad-compatibility-pr1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive, manual-backed Analog Rytm MKII MIDI catalog and report that cover Appendix C CC/NRPN rows, every known Rytm machine SRC mapping, and the safety status for promotion into runtime mutation.

**Architecture:** Put facts in `rytm_randomizer/data/analog_rytm_midi.py`, re-export them through `data/__init__.py`, summarize them through a passive `reports/` module, and expose one passive CLI command. The existing V1.34 runtime maps remain the only live mutation source.

**Tech Stack:** Python 3.11 stdlib, frozen dataclasses, `MappingProxyType`, existing passive CLI registry, pytest.

---

## File Structure

- Create: `rytm_randomizer/data/analog_rytm_midi.py`
  - Pure manual-backed CC/NRPN and note-trigger fact table.
- Modify: `rytm_randomizer/data/__init__.py`
  - Re-export the Rytm catalog without disturbing existing A4 exports.
- Create: `rytm_randomizer/reports/analog_rytm_midi_catalog.py`
  - Passive report builder/formatter/CLI command.
- Modify: `rytm_randomizer/cli.py`
  - Lazy-register the passive report command.
- Modify: `rytm_randomizer/help_text.py`
  - Add command help.
- Modify: `tests/test_data_layer.py`
  - Drift-guard representative Rytm manual rows and safety statuses.
- Create: `tests/test_analog_rytm_midi_catalog.py`
  - Focused catalog/report tests.
- Modify: `tests/test_cli.py`
  - Passive CLI coverage.
- Modify: `tests/test_real_midi_passive_cli_safety.py`
  - Ensure the command opens no MIDI port.
- Modify: `README.md`, `docs/ARCHITECTURE.md`, `docs/MANUAL_HARDWARE_VALIDATION.md`, `docs/STATUS.md`
  - Record the new passive catalog and its validation boundary.

## Tasks

- [ ] Write failing data/report tests for counts, representative rows, safety statuses, and note triggers.
- [ ] Implement `data/analog_rytm_midi.py` with immutable catalog data.
- [ ] Re-export data and update data-layer drift guards.
- [ ] Add passive report and CLI help/dispatch.
- [ ] Update README, architecture, hardware validation, and status docs.
- [ ] Run targeted tests, architecture gate, and lint checks.

## Safety Boundary

The catalog may document rows before they are live-mutable. Only rows that
already match V1.34-backed runtime profiles are marked `validated_runtime`.
All other manual-backed rows remain `documented_only` or `locked_default` until
separate, explicit hardware validation promotes them.
