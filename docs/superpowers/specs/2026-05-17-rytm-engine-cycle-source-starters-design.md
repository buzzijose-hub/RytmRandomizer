# Rytm Engine Cycle Source Starters Design

## Goal

Add an optional engine-source starter layer above the existing Rytm engine-cycle
starter shaping. This starts moving from "engine switch plus common filter/amp
shape" toward "engine switch plus machine-family source tuning."

## Behavior

The current default stays unchanged:

- `--rytm-engine-cycle` sends 12 CC15 machine-select messages.
- `--rytm-engine-cycle --engine-cycle-starter-profile <profile>` sends 84
  messages: one CC15 machine select plus six common filter/amp starter values
  per pad.

The new opt-in flag is:

```text
--engine-cycle-source-starters
```

When supplied with a starter profile, the plan sends 132 messages:

- 12 machine-select events
- 48 engine-source starter events
- 72 common filter/amp starter events

Each pad receives four engine-source starter values immediately after machine
selection and before common filter/amp shaping. For fully profiled V1.34 engines
the source names use known parameter labels when available. For broader
machine-selectable engines, the starter uses generic SRC slot labels (`SRC Slot
1`, `SRC Slot 2`, etc.) so it does not claim unverified official names.

## Safety

Source starters are deterministic CC values in the Rytm SRC slot range CC16-23.
They do not receive SysEx, write SysEx, read hardware state, or run continuous
tracking. They are sent only through the existing guarded dry-run or armed
`SEND` confirmation paths.
