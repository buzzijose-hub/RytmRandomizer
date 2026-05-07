# Real MIDI Boundary Plan

## 1. Purpose

Define the future boundary between the current passive/mock foundation and any
later real MIDI implementation.

Keep this document at planning altitude only.

This document does not implement real MIDI.

This document does not add a real MIDI dependency.

This document does not authorize opening ports, sending MIDI, adding active CLI
commands, dispatching commands, executing scenes, or turning hardware on.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- f877da2 Add real MIDI boundary planning gate review

Current phase:

- Passive/Mock Foundation Phase
- project-level roadmap update accepted
- mock-first active boundary safety baseline accepted
- real MIDI boundary planning gate accepted
- real MIDI boundary plan now being documented
- no real MIDI or hardware validation started

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Current Accepted Foundation

The accepted foundation includes:

- passive CLI visibility
- mock MIDI scaffold
- mock message mapper and report
- mock mapper report CLI preview
- mock-only active candidate tests
- mock-first active boundary for group profile `"2"` / My BD Hard
- active boundary safety tests
- read-only active boundary report
- `active-boundary-report` passive CLI preview
- active boundary safety progress report and review
- project-level roadmap update and review
- real MIDI boundary planning gate and review

## 4. Current Scope

Current mock mapper support:

- group profile `"2"` / My BD Hard
- group profile `"3"` / My BD Classic

Current active-boundary support:

- group profile `"2"` / My BD Hard only

Unsupported by the active boundary:

- group profile `"3"` / My BD Classic
- scenes
- commands

Parked or unsupported:

- group profile `"4"` / My BD Acoustic
- real hardware paths

## 5. Boundary Principles

Future real MIDI behavior must be isolated behind an explicit boundary.

Passive CLI commands must remain read-only.

Passive imports must never open ports.

Passive imports must never import real MIDI libraries.

High-level active boundary logic must remain mockable.

Any future real send path must require explicit operator intent, explicit
arming, exact target selection, and separate review.

Real MIDI must never be reachable accidentally from report, list, search,
inspect, preview, mock mapper report, or active boundary report commands.

## 6. Conceptual Real MIDI Adapter Placement

A future real MIDI adapter may exist conceptually below the mock-first active
boundary.

Possible future ownership, documented as design only:

- `rytm_randomizer/midi_boundary.py`
- `rytm_randomizer/midi_port_provider.py`
- `rytm_randomizer/midi_sender.py`

These files do not exist in this slice.

These names are planning placeholders only. They do not authorize
implementation.

If implemented later, the real MIDI adapter must sit below a mockable sender
interface and must not be imported by passive CLI modules.

## 7. Import And Dependency Isolation

Any future real MIDI dependency must be isolated from passive imports.

Future passive modules must not import:

- mido
- real MIDI backends
- port discovery helpers
- hardware send helpers

Future unit tests must be able to run without any real MIDI dependency
installed.

If a real MIDI library is ever introduced later, it must be imported only in a
small hardware-facing adapter path that is excluded from passive CLI imports
and ordinary mock-only tests.

## 8. Port Discovery Boundary

Port discovery must remain separate from passive behavior.

Future port discovery must not happen during:

- package import
- passive CLI `--help`
- passive CLI report/list/search/inspect/preview
- `mock-mapper-report`
- `active-boundary-report`
- mock message mapping
- mock-first active boundary evaluation
- closeout tests unless explicitly mocked

Any future real port selection must require explicit operator choice.

No default port should be selected silently.

No port should be opened as a side effect of listing or previewing data.

## 9. Passive CLI Separation

These passive CLI commands must remain read-only:

- `report`
- `list-commands`
- `list-scenes`
- `list-group-profiles`
- `search-commands`
- `search-scenes`
- `search-group-profiles`
- `inspect-command`
- `inspect-scene`
- `inspect-group-profile`
- `preview-command`
- `preview-scene`
- `preview-group-profile`
- `mock-mapper-report`
- `active-boundary-report`

They must not:

- construct `MockMidiSender`
- construct a real MIDI sender
- evaluate active boundary requests
- open ports
- send MIDI
- dispatch commands
- execute commands
- execute scenes
- mutate hardware

## 10. Active Boundary Relationship

The current mock-first active boundary remains the only accepted active-facing
software boundary.

Current accepted candidate:

- group profile `"2"` / My BD Hard

Current unsupported active-boundary scope:

- group profile `"3"` / My BD Classic
- group profile `"4"` / My BD Acoustic
- scenes
- commands
- real hardware paths

Future real MIDI planning must not widen the active-boundary candidate scope.

Profile `"3"` active-boundary support and profile `"4"` implementation remain
blocked unless separately approved.

## 11. Arming And Operator Intent

Any future hardware-facing path must require:

- explicit active command design
- explicit `--armed`-style confirmation
- exact source key
- exact target device
- exact MIDI output port
- passive preview first
- mock-only proof first
- visible safety summary
- clean closeout
- clean Git status
- empty V1.34 reference diff
- explicit user approval

Missing arming must fail safely.

Unknown keys must fail safely.

Unsupported keys must fail safely.

No hardware-facing path may be default behavior.

## 12. Required Tests Before Implementation

Before any future real MIDI implementation, tests must prove:

- passive imports do not import real MIDI libraries
- passive CLI commands do not open ports
- passive CLI commands do not send MIDI
- passive CLI commands do not evaluate active boundary requests
- passive CLI commands do not construct `MockMidiSender`
- missing arming fails safely
- unknown keys fail safely
- unsupported keys fail safely
- mock-only active boundary still uses injected senders only
- real MIDI adapter imports are isolated from passive modules
- port discovery is isolated and mockable
- V1.34 reference remains untouched
- profile `"3"` remains unsupported by the active boundary unless separately
  approved
- profile `"4"` remains parked unless separately approved

## 13. Future Implementation Gates

This plan does not authorize implementation.

Before any future implementation, the project needs:

- review and acceptance of this real MIDI boundary plan
- a separate real MIDI implementation design/spec
- a separate real MIDI implementation test plan
- explicit file ownership
- explicit dependency decision
- explicit no-passive-import proof
- explicit arming failure tests
- explicit user approval

## 14. Hardware Validation Remains Later

This plan does not authorize hardware validation.

Before hardware validation could be considered later:

- all mock-only and real MIDI boundary tests must pass
- real MIDI adapter implementation must be reviewed and accepted
- exact target device must be selected
- exact MIDI output port must be confirmed
- exact command/pad/channel scope must be confirmed
- current Analog Rytm kit/project must be saved
- monitoring volume must be lowered
- hardware validation checklist must be accepted
- user must explicitly confirm that hardware validation is starting

Analog Rytm and Analog Four remain off during this planning phase.

## 15. Forbidden Scope

This plan does not authorize:

- implementation
- real MIDI imports
- mido dependency
- MIDI port opening
- MIDI sending
- hardware detection
- hardware send
- active CLI commands
- passive CLI active-boundary evaluation
- passive CLI construction of `MockMidiSender`
- dispatch
- command execution
- scene execution
- hardware mutation
- SysEx
- GUI/capture
- Analog Four support
- Pads 5-12 support
- machine/profile expansion
- profile `"4"` implementation
- profile `"3"` active-boundary support
- hardware validation

## 16. Safe Next Options

Safe next options:

- review and accept this real MIDI boundary plan
- pause at this clean planning checkpoint
- return to passive/project documentation
- create a separate docs-only real MIDI implementation design/spec only after
  this plan is accepted

Unsafe next moves:

- adding real MIDI
- importing mido
- opening ports
- sending MIDI
- adding active CLI commands
- wiring passive CLI to active boundary evaluation
- turning on hardware
- implementing profile `"4"` without separate approval
- adding profile `"3"` active-boundary support without separate approval

## 17. Recommendation

Review and accept this real MIDI boundary plan before any further real
MIDI-facing planning.

Do not implement real MIDI yet.

Do not add mido.

Do not open ports.

Do not add active CLI commands.

Do not turn on hardware.

## 18. Decision

The real MIDI boundary is defined at planning level only.

Real MIDI implementation remains blocked.

Hardware validation remains blocked.

Hardware remains off.

No implementation is added in this slice.
