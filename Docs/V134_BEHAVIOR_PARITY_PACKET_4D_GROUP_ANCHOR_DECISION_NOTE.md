# V1.34 Behavior Parity Packet 4D Group Anchor Decision Note

## Purpose

Decide how to treat the remaining Packet 4 group anchor commands before any
implementation.

This is a documentation-only decision note. It adds no implementation, tests,
CLI wiring, dispatch, MIDI, port opening, package metadata, active behavior,
or hardware behavior.

## Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this slice:

- `2366894 Add Packet 4C lane-aware group mutation review`

Current phase:

- Passive/Mock Foundation Phase
- Packet 1 complete
- Packet 2 accepted progress
- Packet 3 complete
- Packet 4A scene intent accepted
- Packet 4B group mutation intent accepted
- Packet 4C lane-aware group mutation intent accepted
- remaining Packet 4 group anchor scope now being decided

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Remaining Packet 4 Scope

The remaining Packet 4 group anchor commands are:

- `O`: load full 4-pad group anchors
- `Z`: return all 4 group pads to anchors

These commands are different from the already accepted Packet 4A, 4B, and 4C
intent slices because they imply anchor load/return semantics across multiple
pads.

## Current Decision

Keep `O` and `Z` deferred for now.

Do not implement `O` or `Z` behavior in this slice.

Any future `O`/`Z` support must be separately approved as a tiny read-only
intent-only Packet 4D implementation plan before code or tests change.

## Reasons To Keep Deferred For Now

- Packet 4A already covers read-only scene intent.
- Packet 4B already covers read-only group mutation intent for `X`, `D`, `I`,
  and `4`.
- Packet 4C already covers read-only lane-aware group mutation intent for
  `Y`, `V`, and `N`.
- `O` and `Z` involve group anchor load/return meaning, which is closer to
  runtime state semantics than the prior Packet 4 intent slices.
- Keeping `O` and `Z` deferred preserves a clear safe-failure case.
- A dedicated plan should decide the exact read-only metadata shape before any
  implementation.

## Future Packet 4D Plan Requirements

If `O` and `Z` are planned later, the plan must define:

- read-only behavior only
- copied passive command metadata only
- deterministic behavior family names
- deterministic reason values
- explicit `accepted` / `unsupported` semantics
- no anchor loading
- no anchor return execution
- no group mutation execution
- no scene execution
- no runtime group state
- no runtime anchor state
- no command dispatch
- no MIDI
- no ports
- no hardware requirement

## Candidate Future Read-Only Semantics

Document as future design only:

- `O` could be represented as read-only group anchor load intent.
- `Z` could be represented as read-only group anchor return intent.
- Both should remain metadata-only unless a future review explicitly approves
  a tiny implementation.

No final implementation shape is approved by this decision note.

## Confirmed Absent Behavior

This decision note confirms the project still has:

- no CLI execution wiring
- no dispatch
- no command execution
- no scene execution
- no group anchor load execution
- no group anchor return execution
- no group mutation execution
- no lane-aware group mutation execution
- no prompt/input loop
- no runtime scene/group/lane/anchor state mutation
- no real MIDI dependency
- no `mido`
- no `rtmidi`
- no package metadata changes
- no port discovery
- no port opening
- no MIDI sending
- no active CLI command
- no `execute-command`
- no `send-command`
- no `hardware-test`
- no hardware behavior
- no hardware validation
- no machine/profile expansion
- no Analog Four support
- no Pads 5-12 support
- no SysEx
- no GUI/capture

`rytm_hybrid_randomizer_v134.py` remains untouched.

## Packet 4 Status

Accepted Packet 4 progress:

- Packet 4A scene intent
- Packet 4B group mutation intent
- Packet 4C lane-aware group mutation intent

Deferred Packet 4 scope:

- `O` group anchor load intent
- `Z` group anchor return intent

Packet 4 is not complete until `O` and `Z` are either implemented as
read-only intent behavior through a separately approved Packet 4D slice or
explicitly left deferred in a Packet 4 closeout decision.

## Next Safe Options

Safe next options:

- docs-only Packet 4D group anchor load/return plan
- broader Packet 4 near-completion checkpoint that leaves `O` and `Z`
  deferred
- user-facing progress/timeline update
- pause at this accepted Packet 4C plus `O`/`Z` decision checkpoint

## Recommendation

Create a docs-only Packet 4D group anchor load/return plan only if we want to
finish the remaining Packet 4 intent surface now.

Otherwise, create a broader Packet 4 near-completion checkpoint that records
`O` and `Z` as intentionally deferred.

Do not implement `O` or `Z` yet.

## Decision

`O` and `Z` remain deferred and safe.

Packet 4 remains partially complete.

Hardware remains off.
