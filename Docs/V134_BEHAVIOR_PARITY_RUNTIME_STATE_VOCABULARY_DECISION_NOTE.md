# V1.34 Behavior Parity Runtime-State Vocabulary Decision Note

## 1. Purpose

Define a shared vocabulary for discussing future runtime-state work without
implementing runtime state.

This note exists because the accepted user-facing behavior-parity progress
report identified runtime state as the next boundary to discuss before any
future implementation.

This document is documentation-only.

It adds no implementation, tests, CLI commands, runtime state, dispatch, MIDI,
ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this decision slice:

- `b92c4ba Add behavior parity user progress report review after anchor profile CLI visibility`

Current phase:

- passive/mock foundation
- V1.34 behavior-parity implementation packets
- passive behavior reports and CLI visibility
- user-facing behavior-parity progress report accepted
- runtime-state vocabulary now being discussed at documentation level

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Prior State-Related Context

Existing related documents include:

- `Docs/STATE_CAPTURE_ROADMAP.md`
- `Docs/V134_BEHAVIOR_PARITY_PACKET_5_PAD1_LANE_STATE_MODELING_DECISION_NOTE.md`
- `Docs/V134_BEHAVIOR_PARITY_PACKET_5_PAD1_LANE_STATE_DESCRIPTORS_CHECKPOINT.md`

Those documents already distinguish between:

- static read-only descriptors
- future soft capture
- future true hardware capture
- deferred deeper lane-state modeling

This decision note does not replace those documents. It creates a broader
project-level vocabulary so future planning can use consistent words.

## 4. Current Decision

Decision:

- define runtime-state vocabulary only
- do not implement runtime state
- do not plan implementation yet
- keep `PZ` parked
- keep profile `4` mock mapper support parked

This decision allows future planning documents to discuss state more clearly
without crossing into execution.

## 5. Vocabulary

### Passive Metadata

Static project knowledge represented as data.

Examples:

- command metadata
- scene metadata
- group profile metadata
- read-only support status

Passive metadata is safe to list, search, inspect, preview, and report.

### Read-Only Behavior Intent

A deterministic description of what a command means without executing it.

Examples:

- anchor/profile behavior intent
- scene/group intent
- lane behavior intent
- selected-profile workflow intent
- selected isolated pad target intent

Read-only behavior intent is not runtime state.

### Descriptor State

A static read-only description of a possible behavior state. It is derived
from metadata or accepted helper logic and does not change over time.

Existing example:

- Pad 1 lane-state descriptors

Descriptor state is safe because it does not represent live runtime mutation.

### Mock State

Test-only in-memory state used to prove future behavior without hardware.

Examples:

- mock MIDI sender recorded messages
- mock message mapper output
- mock-only active candidate result

Mock state must remain isolated from real MIDI, ports, and hardware.

### Runtime State

Future in-memory state that would represent what the modular program currently
believes is selected, loaded, mutated, or undoable during a running session.

Possible future examples:

- selected profile
- selected isolated pad
- current lane family
- current anchor reference
- current mutation result
- undo stack
- armed status

Runtime state does not exist as implementation in this phase.

### Hardware State

The actual state of the Analog Rytm or another device.

Hardware state is not currently read, captured, mutated, or trusted by the
modular system.

Hardware state requires a later explicit hardware-validation phase.

### Soft Capture

Future capture of what the software already knows because it created or
tracked it.

Soft capture is not true hardware capture.

Soft capture should be considered before true hardware capture if capture work
is ever planned.

### True Hardware Capture

Future capture of actual hardware state, likely through hardware-facing
requests or dump parsing.

True hardware capture is much later scope.

It is not authorized by this decision note.

### Anchor State

Future representation of a known anchor source or current anchor reference.

Anchor state may include:

- known software anchor
- selected profile anchor
- selected isolated pad anchor
- captured anchor

Anchor state is runtime-adjacent and not implemented here.

### Selected Target State

Future representation of what the operator has selected as a current target.

Possible future target concepts:

- selected profile
- selected isolated pad
- selected lane family
- selected command scope

This vocabulary matters for `PZ`, because `PZ` depends on knowing which
isolated pad is selected before any anchor-return behavior can be discussed.

### Mutation Result State

Future representation of a produced mutation result before commit, undo, or
anchor return.

This remains future runtime vocabulary only.

### Armed State

Future explicit operator intent state for hardware-facing behavior.

Armed state does not exist yet.

If it is ever implemented, missing arming must fail safely.

## 6. Relationship To PZ

`PZ` remains parked because it depends on selected target state and anchor
state.

The current project can describe that `PZ` is parked, but it cannot safely
implement `PZ` until the selected isolated pad state and selected pad anchor
semantics are designed and reviewed.

This vocabulary note makes that dependency explicit.

It does not authorize `PZ` implementation.

## 7. Relationship To Active And Hardware Work

Runtime-state vocabulary is not active execution.

Runtime-state vocabulary is not hardware validation.

Runtime-state vocabulary is not real MIDI.

Future active or hardware-facing work must still pass through separate design,
review, test, arming, and validation gates.

## 8. Confirmed Absent Behavior

This decision note confirms no:

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

## 9. Preconditions Before Any Runtime-State Plan

Before any runtime-state plan begins:

- clean Git status
- full closeout passing
- V1.34 reference diff empty
- package metadata diff empty
- this vocabulary decision note reviewed and accepted
- clear distinction between descriptor state, mock state, runtime state, and
  hardware state
- explicit statement that runtime state remains non-hardware-facing unless a
  later active boundary is accepted

## 10. Safe Next Options

Safe next options:

- docs-only review/acceptance gate for this vocabulary decision note
- docs-only runtime-state vocabulary plan, if more detail is needed
- docs-only `PZ` behavior plan, only after this vocabulary is accepted
- docs-only profile `4` support plan, only if explicitly approved
- pause at this clean checkpoint

## 11. Recommendation

Review and accept this runtime-state vocabulary decision note next.

After that, prefer either:

- a docs-only runtime-state vocabulary plan, or
- a docs-only `PZ` behavior plan if `PZ` becomes the approved next branch.

Do not implement runtime state yet.

Do not implement `PZ`.

Do not add profile `4` mock mapper support.

Do not add MIDI, ports, active behavior, runtime execution, package metadata
changes, or hardware behavior.

## 12. Decision Summary

The project now has shared vocabulary for future runtime-state discussion.

Runtime state remains unimplemented.

`PZ` remains parked.

Hardware remains off.

No implementation in this decision slice.

## 13. Review Status

This decision note is now followed by:

- `Docs/V134_BEHAVIOR_PARITY_RUNTIME_STATE_VOCABULARY_DECISION_NOTE_REVIEW.md`

That review accepts the runtime-state vocabulary for planning while keeping
runtime state unimplemented, `PZ` parked, and profile `4` mock mapper support
parked.
