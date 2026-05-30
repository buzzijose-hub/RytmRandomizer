# Analog Rytm MIDI Catalog Design

## Purpose

Build a passive, manual-backed Analog Rytm MKII OS 1.72 MIDI catalog so the
project can answer "which CC/NRPN parameters exist for every pad/machine?"
without widening the live mutation surface.

## Scope

This work adds documentation-grade data and reports only. It does not add new
runtime randomization, scene behavior, unattended sends, SysEx writes, pattern
or transport behavior, kit/project writes, or new V1.34 parity fixtures.

## Architecture

- Add `rytm_randomizer/data/analog_rytm_midi.py` as the pure data source for
  Appendix C CC/NRPN rows, machine SRC rows, and MIDI note triggers.
- Re-export the catalog from `rytm_randomizer/data/__init__.py`.
- Add `rytm_randomizer/reports/analog_rytm_midi_catalog.py` as a passive report
  that summarizes catalog coverage and safety status.
- Add a passive CLI command, `analog-rytm-midi-catalog-report`, using the
  existing `CliCommand` registry and passive report formatter.
- Keep `param_maps.py` and `profiles.py` as the V1.34 runtime-safe mutation
  source. The new catalog can point at validated runtime rows, but it does not
  make documented rows live-mutable.

## Data Model

`AnalogRytmCcMapping` records:

- `section`: manual section or machine label.
- `parameter`: operator-facing parameter name.
- `cc_msb` / `cc_lsb`: MIDI CC facts.
- `nrpn_msb` / `nrpn_lsb`: NRPN facts where listed.
- `scope`: broad area such as `src`, `filter`, `amp`, `lfo`, `fx`, or `kit`.
- `risk`: `low`, `medium`, or `high`.
- `mutation_status`: `validated_runtime`, `documented_only`, `locked_default`,
  or `forbidden`.
- `machine_key`: set only for machine SRC rows.

`AnalogRytmNoteTrigger` records the note trigger table from Appendix C without
pretending note triggers are CC parameters.

## Safety Classification

The default posture is conservative:

- Existing V1.34-backed profile parameters become `validated_runtime` when their
  manual machine row matches a current runtime profile mapping.
- Track volume, track level, mute/solo, active scene, machine switching,
  performance macros, FX mix/output levels, and similarly high-impact controls
  are `locked_default`.
- Transport, clock, program/pattern/project/kit write behaviors remain outside
  the CC catalog and are treated as forbidden by policy.
- Everything manual-backed but not validated for live mutation remains
  `documented_only`.

## Validation

Phase 4 is implemented as runbook/evidence discipline, not automatic hardware
mutation. The project already has one-CC 12-track outbound validation evidence;
this catalog adds a follow-up checklist that explains what is still required
before promoting additional documented rows into runtime mutation.

## Success Criteria

- All 33 known Rytm machine profiles have machine SRC rows in the passive
  catalog.
- All 12 pads are covered by the existing pad capability matrix.
- The report makes the gap explicit: the catalog is broad, while runtime
  mutation remains limited to validated V1.34 rows.
- Tests pin representative CC/NRPN rows, note-trigger rows, counts, safety
  classes, and CLI output.
