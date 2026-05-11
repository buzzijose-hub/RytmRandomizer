# V1.34 Behavior Parity PZ Decision Note After Packet 11A

## 1. Purpose

Decide how to treat `PZ` after the accepted remaining-gap audit after
Packet 11A.

This is a documentation-only decision note. It does not implement `PZ`, add
tests, wire CLI execution, dispatch commands, open ports, send MIDI, add
package metadata changes, add active behavior, add runtime behavior, or
require hardware.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this decision slice:

- `586a33c Add behavior parity remaining-gap audit review after Packet 11A`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- Packet 11A `L` selected isolated pad target intent complete and accepted
- remaining-gap audit after Packet 11A accepted
- `PZ` decision note now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Current Packet 11 State

Accepted Packet 11 state:

- `L`: covered and accepted for read-only selected isolated pad target intent
- `PZ`: deferred/safe

Current `PZ` metadata meaning:

- command key:
  - `PZ`
- label:
  - return selected isolated pad to anchor only
- current status:
  - not implemented as behavior parity
  - not active
  - not executable
  - not hardware-facing

## 4. Decision

Decision:

- keep `PZ` parked for now

This means:

- do not implement `PZ` now
- do not create a `PZ` behavior implementation plan yet
- do not add selected isolated pad runtime state
- do not add selected pad anchor return execution
- do not add dispatch, MIDI, ports, active behavior, or hardware behavior

## 5. Reasoning

`PZ` should stay parked for now because:

- `PZ` implies returning the selected isolated pad to an anchor.
- Anchor return semantics are closer to runtime state than `L`.
- The current modular behavior layer does not have selected isolated pad
  runtime state.
- The current modular behavior layer does not have selected pad anchor return
  execution.
- Packet 11A already gave the selected isolated pad surface a safe read-only
  entry point.
- The remaining-gap audit identified remaining anchor/profile widening as a
  safer planning area than moving directly into `PZ`.

## 6. What Would Need To Be True Before Revisiting `PZ`

Before `PZ` can move from parked to planned, the project should have:

- clean Git status
- full closeout passing
- V1.34 reference diff empty
- package metadata diff empty
- accepted remaining-gap audit
- accepted `PZ` decision note
- clear selected isolated pad target semantics
- clear anchor/profile semantics for the selected isolated pad
- a docs-only `PZ` behavior plan, if `PZ` is later approved
- explicit confirmation that `PZ` remains read-only and intent-only

Even then, any future `PZ` work must not add:

- selected isolated pad runtime state
- selected pad switching execution
- selected pad anchor return execution
- isolated pad mutation execution
- dispatch
- MIDI
- ports
- active behavior
- hardware behavior

## 7. Relationship To Remaining Anchor/Profile Widening

Remaining anchor/profile widening is a better next planning target than `PZ`.

Reason:

- anchor/profile widening can remain read-only and metadata-driven
- it may clarify anchor semantics before `PZ` is revisited
- it avoids selected isolated pad runtime state
- it avoids anchor return execution
- it may increase behavior-parity coverage without moving toward hardware

No anchor/profile widening implementation is authorized by this decision note.

## 8. Confirmed Absent Behavior

This decision note confirms no:

- CLI execution wiring
- command dispatch
- command execution
- scene execution
- prompt/input loop
- active depth prompt
- selected profile runtime state
- current profile runtime state
- selected isolated pad runtime state
- selected pad switching execution
- selected pad anchor return execution
- runtime scene state
- runtime group state
- runtime lane state
- runtime anchor state mutation
- runtime mutation result model
- runtime state mutation
- profile switching execution
- machine change execution
- anchor loading execution
- isolated pad mutation execution
- undo stack inspection
- undo stack mutation
- undo execution
- anchor commit execution
- anchor restore execution
- anchor persistence
- waveform exploration execution
- waveform selection
- waveform randomization
- real MIDI dependency
- `mido`
- `rtmidi`
- package metadata changes
- port discovery
- port opening
- MIDI sending
- active CLI command
- `execute-command`
- `send-command`
- `hardware-test`
- hardware behavior
- hardware validation
- machine/profile universe expansion
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture

`rytm_hybrid_randomizer_v134.py` remains untouched.

Package metadata remains untouched.

## 9. Safe Next Options

Safe next options:

- docs-only review/acceptance gate for this `PZ` decision note
- docs-only remaining anchor/profile widening audit
- user-facing behavior-parity progress/timeline update
- pause at this clean `PZ` decision checkpoint

## 10. Recommendation

Prefer a docs-only review/acceptance gate for this `PZ` decision note.

After that, prefer a docs-only remaining anchor/profile widening audit before
revisiting `PZ`.

Do not implement `PZ` yet.

Do not add selected isolated pad runtime state, selected pad switching
execution, selected pad anchor return execution, isolated pad mutation
execution, dispatch, MIDI, ports, package metadata changes, active behavior,
runtime execution, or hardware behavior from this decision note.

## 11. Decision Summary

`PZ` remains parked.

The next recommended branch is review/acceptance of this decision note.

After review, the next planning target should be remaining anchor/profile
widening audit.

Hardware remains off.

No implementation in this decision slice.
