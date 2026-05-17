# Analog Four Starter Profiles Design

## Goal

Turn the single hard-coded Analog Four safe-starter bundle into named,
hardware-sendable starter profiles. This creates the first bridge between the
current dual-machine snapshot sender and the later style/audio-analyzer kit
designer.

## Profiles

The first pass supports four profiles:

- `balanced`: the current conservative 20-message A4 starter.
- `birmingham-dark`: darker, colder, more industrial pressure.
- `detroit-classic`: more open, melodic, and reverb-friendly.
- `peak-time`: brighter and more forceful.

Every profile keeps the same safe structure: four A4 tracks, five mapped CC
messages per track, and only reference-known CC controls.

## Interfaces

- `build_analog_four_safe_starter_plan(profile="balanced")`
- `build_dual_machine_mock_bridge(..., analog_four_profile="balanced")`
- Passive dual-machine CLI commands accept `--analog-four-profile <profile>`.
- Active app dual-machine snapshot send accepts `--analog-four-profile <profile>`.

The option applies only to the safe-starter A4 source. If an Analog Four SysEx
snapshot path is supplied, non-default starter profiles are rejected because
saved-offset A4 snapshot candidates are a different source and remain blocked
from real MIDI.

## Report Behavior

Bridge, active-plan, guarded dry-run, and hardware-send reports surface the
resolved profile key and label when the A4 side is using the safe-starter plan.

## Safety

- No new MIDI message type.
- No NRPNs.
- No live SysEx receive.
- No SysEx writes.
- No unverified Analog Four saved-offset event can become eligible.
- Existing default behavior remains `balanced`.
