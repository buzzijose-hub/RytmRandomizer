# Rytm Engine Cycle Auto Starter Profile Design

## Goal

Let the operator ask for starter shaping without remembering profile names by
using `--engine-cycle-starter-profile auto`.

## Behavior

Manual starter profiles keep working exactly as they do now. The existing
default remains unchanged: if `--engine-cycle-starter-profile` is omitted,
`--rytm-engine-cycle` emits only the 12 CC15 machine-select events.

When the profile value is `auto`, the starter planner chooses a profile from
the style prompt:

- Birmingham, dark, industrial, noise, or raw prompts use `birmingham-dark`.
- Detroit or classic prompts use `detroit-classic`.
- Peak, driving, hard, hardcore, schranz, or big-room prompts use `peak-time`.
- Unclear prompts use `balanced`.

The selected profile is reported in the existing dry-run, armed, and passive
starter-plan reports.

## Safety

Auto profile selection is a deterministic local string classifier. It does not
open MIDI ports, send MIDI, receive SysEx, write SysEx, or mutate hardware. It
only chooses which already-tested starter profile is passed into the existing
guarded send path.
