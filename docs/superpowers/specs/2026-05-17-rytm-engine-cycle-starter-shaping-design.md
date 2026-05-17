# Rytm Engine Cycle Starter Shaping Design

## Goal

Add a passive 12-pad starter-shaping layer for the existing Rytm engine-cycle plan.
The engine-cycle plan already chooses the best machine candidate for each pad from a
style prompt. This checkpoint adds musical first-pass CC shaping after each selected
engine so pads are not only switched to useful engines, but also nudged toward
usable kick, hat, metallic, percussion, bell, atmosphere, and wild roles.

## Scope

This slice is passive and mock-only. It creates deterministic starter profiles and
a CLI report that captures the planned CC stream into `MockMidiSender`. It does
not change the existing guarded or armed Rytm engine-cycle sender yet.

The starter layer uses mapped Rytm CCs that are common across the existing machine
maps:

- `FLT Frequency` / CC74
- `FLT Resonance` / CC75
- `FLT Type` / CC76
- `AMP Decay` / CC80
- `AMP Overdrive` / CC81
- `AMP Pan` / CC10

These values are a musical starting surface, not a final per-engine SRC tuning
system. Per-engine SRC maps remain a later milestone after this common shaping
stream is visible, tested, and easy to promote into guarded sending.

## Profiles

The first profiles mirror the Analog Four starter-profile vocabulary:

- `balanced`
- `birmingham-dark`
- `detroit-classic`
- `peak-time`

Profile lookup accepts aliases such as `birmingham_dark`, `dark-techno`, and
`peak time`. Unknown profile names must fail with valid choices.

## Data Flow

1. `build_rytm_engine_cycle_plan(style, discovery)` chooses 12 top machine
   candidates.
2. `build_rytm_engine_cycle_starter_plan(engine_plan, profile)` adds the selected
   profile's starter CCs per pad.
3. `capture_rytm_engine_cycle_starter_mock_messages(starter_plan)` captures one
   CC15 machine-select message plus six starter CC messages per pad.
4. `format_rytm_engine_cycle_starter_plan_report(starter_plan)` prints a passive
   report for review and future hardware-send promotion.

## Safety

The new module must be import-passive and silent. It must not import `mido`,
`rtmidi`, open ports, receive MIDI or SysEx, send real MIDI, write SysEx, execute
commands, or mutate hardware.

The CLI command is passive:

```text
python -m rytm_randomizer.cli rytm-engine-cycle-starter-plan-report --style <text> [--discovery <0..1>] [--profile <profile>]
```

## Success Criteria

- The starter plan covers all 12 Rytm pads for a normal style prompt.
- Each pad emits one machine-select event and six common mapped starter events.
- Reports show style, discovery, selected starter profile, planned pads, starter
  message count, per-pad summaries, mock stream preview, and safety language.
- Existing `rytm-engine-cycle-plan-report` behavior remains unchanged.
