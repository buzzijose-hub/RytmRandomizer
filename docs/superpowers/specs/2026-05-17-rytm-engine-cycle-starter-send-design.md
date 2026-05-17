# Rytm Engine Cycle Starter Send Design

## Goal

Promote the passive 12-pad Rytm engine-cycle starter-shaping plan into the
guarded dry-run and armed hardware engine-cycle send flows.

## Design

The existing `--rytm-engine-cycle` behavior stays unchanged by default: it sends
or mocks one CC15 machine-select event per pad. A new optional
`--engine-cycle-starter-profile <profile>` modifier turns the engine-cycle plan
into a starter-shaping send plan. That plan emits one machine-select event plus
six common filter/amp starter values per pad.

The supported profile names come from
`rytm_randomizer.rytm_engine_cycle_starter_profiles`:

- `balanced`
- `birmingham-dark`
- `detroit-classic`
- `peak-time`

## Safety Contract

The starter send path inherits the existing guard rails:

- `--dry-run --rytm-engine-cycle --engine-cycle-starter-profile <profile>` emits
  to `MockMidiSender` only.
- `--arm --rytm-engine-cycle --engine-cycle-starter-profile <profile>` opens a
  selected MIDI port only after the existing port-choice prompt and sends real
  MIDI only after exact `SEND` confirmation.
- Unknown profiles fail before any port opens.
- Plans with unresolved pads emit no partial messages.

## Non-Goals

This does not add continuous snapshot capture, SysEx receive, SysEx writes,
engine-specific SRC tuning, or audio analysis. It only sends the common mapped
starter-shaping CCs already defined by the passive planner.
