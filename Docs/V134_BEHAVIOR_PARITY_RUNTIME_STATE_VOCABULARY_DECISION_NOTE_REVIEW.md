# V1.34 Behavior Parity Runtime-State Vocabulary Decision Note Review

## 1. Purpose

Review and accept the runtime-state vocabulary decision note as the current
planning vocabulary for future runtime-state discussion.

This is a review checkpoint only.

It adds no implementation, tests, CLI commands, runtime state, dispatch, MIDI,
ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this review slice:

- `ff6df01 Add runtime-state vocabulary decision note`

Current phase:

- passive/mock foundation
- V1.34 behavior-parity implementation packets
- passive behavior reports and CLI visibility
- runtime-state vocabulary decision note created
- runtime-state vocabulary now being reviewed

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Review Decision

Decision:

- accept `Docs/V134_BEHAVIOR_PARITY_RUNTIME_STATE_VOCABULARY_DECISION_NOTE.md`
  as the current planning vocabulary
- keep runtime state unimplemented
- keep `PZ` parked
- keep profile `4` mock mapper support parked
- require a separate planning slice before any runtime-state implementation

This review accepts vocabulary only.

It does not authorize implementation.

## 4. Accepted Vocabulary

The accepted vocabulary includes:

- passive metadata
- read-only behavior intent
- descriptor state
- mock state
- runtime state
- hardware state
- soft capture
- true hardware capture
- anchor state
- selected target state
- mutation result state
- armed state

These words can now be used consistently in future planning documents.

## 5. Accepted Boundary Meanings

Accepted meanings:

- passive metadata is static read-only project knowledge
- read-only behavior intent describes what a command means without executing it
- descriptor state is static and does not represent live runtime mutation
- mock state is test-only and isolated from hardware
- runtime state is future in-memory session state and is not implemented
- hardware state is actual device state and is not currently read or mutated
- soft capture is future software-known state capture
- true hardware capture is much later hardware-facing scope
- anchor state, selected target state, and mutation result state remain future
  runtime vocabulary
- armed state remains a future operator-intent concept

## 6. Relationship To PZ

`PZ` remains parked.

This review accepts that `PZ` depends on future selected target state and
future anchor state.

Any future `PZ` behavior plan must remain documentation-only until separately
approved.

This review does not authorize `PZ` implementation.

## 7. Relationship To Profile 4

Group profile `4` mock mapper support remains parked.

This review does not authorize profile `4` mock mapper implementation.

Profile `4` remains useful as an unsupported/safe case unless a later approved
slice changes that decision.

## 8. Confirmed Absent Behavior

This review confirms no:

- code changes
- test changes
- closeout script changes
- package metadata changes
- active CLI command
- `execute-command`
- `send-command`
- `hardware-test`
- dispatch
- command execution
- scene execution
- mutation execution
- runtime state implementation
- selected profile runtime state
- selected isolated pad runtime state
- selected pad switching execution
- selected pad anchor return execution
- `PZ` implementation
- profile `4` mock mapper support
- direct behavior helper execution from CLI
- real MIDI dependency
- `mido`
- `rtmidi`
- port discovery
- port opening
- MIDI sending
- hardware behavior
- hardware validation
- SysEx
- GUI/capture
- Analog Four support
- Pads 5-12 support
- machine/profile universe expansion

`rytm_hybrid_randomizer_v134.py` remains untouched.

Package metadata remains untouched.

## 9. Passive Commands Remain Read-Only

These commands remain passive/read-only:

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
- `behavior-menu-report`
- `anchor-profile-report`

They must not construct runtime state, dispatch behavior, open ports, or send
MIDI.

## 10. Preconditions Before Any Runtime-State Plan

Before any runtime-state plan begins:

- clean Git status
- full closeout passing
- V1.34 reference diff empty
- package metadata diff empty
- runtime-state vocabulary decision note accepted
- clear distinction between descriptor state, mock state, runtime state, and
  hardware state
- explicit statement that runtime state remains non-hardware-facing unless a
  later active boundary is accepted
- no MIDI dependency added
- no package metadata change added
- no active CLI behavior added

## 11. Preconditions Before Any PZ Behavior Plan

Before any `PZ` behavior plan begins:

- this review must be accepted
- `PZ` must remain documentation-only during planning
- selected target state must be described
- anchor state must be described
- selected isolated pad semantics must be described
- failure behavior for unknown or unset selected targets must be described
- no runtime implementation may be added by the plan itself
- no MIDI, ports, active behavior, package metadata changes, or hardware
  behavior may be added

## 12. Safe Next Options

Safe next options:

- docs-only runtime-state vocabulary plan, if more detail is needed
- docs-only `PZ` behavior plan, if `PZ` becomes the approved next branch
- docs-only profile `4` support plan, only if explicitly approved
- broader progress report after accepting the runtime-state vocabulary boundary
- pause at this clean checkpoint

## 13. Recommendation

Prefer a docs-only `PZ` behavior plan next if the project wants to move toward
the remaining selected isolated pad gap.

If more caution is useful, create a docs-only runtime-state vocabulary plan
first.

Do not implement runtime state yet.

Do not implement `PZ`.

Do not add profile `4` mock mapper support.

Do not add MIDI, ports, active behavior, runtime execution, package metadata
changes, or hardware behavior.

## 14. Decision Summary

`Docs/V134_BEHAVIOR_PARITY_RUNTIME_STATE_VOCABULARY_DECISION_NOTE.md` is
accepted for planning.

Runtime state remains unimplemented.

`PZ` remains parked.

Profile `4` remains parked.

Hardware remains off.

No implementation in this review slice.
