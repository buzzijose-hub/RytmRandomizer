# V1.34 Behavior Parity Selected Target State Plan After PZ Review Review

## 1. Purpose

Review and accept the selected target state plan after the accepted `PZ`
behavior plan review.

This is a documentation-only review gate.

It accepts selected target state as a planning boundary only.

It adds no implementation, tests, CLI commands, runtime state, dispatch, MIDI,
ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this review slice:

- `2c4fe39 Add selected target state plan after PZ review`

Current phase:

- passive/mock foundation
- V1.34 behavior-parity implementation packets
- passive behavior reports and CLI visibility
- runtime-state vocabulary accepted for planning
- `PZ` behavior plan accepted for planning
- selected target state plan created
- selected target state plan now being reviewed

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Review Decision

Accepted selected target state plan:

- `Docs/V134_BEHAVIOR_PARITY_SELECTED_TARGET_STATE_PLAN_AFTER_PZ_REVIEW.md`

Accepted selected target state plan milestone:

- `2c4fe39 Add selected target state plan after PZ review`

Decision:

- accept selected target state as the current planning boundary
- keep selected target state unimplemented
- keep runtime state unimplemented
- keep `PZ` parked
- keep anchor state as future planning scope
- require separate planning before any selected target state implementation
- require separate planning before any anchor state implementation

This review accepts planning only.

It does not authorize implementation.

## 4. Accepted Selected Target Boundary

Accepted selected target boundary:

- selected target state is future in-memory session state
- the current scope is selected isolated pad target only
- selected target state answers what is selected
- selected target state does not answer what anchor belongs to that target
- selected target state is required before future `PZ` implementation can be
  planned safely
- selected target state must remain non-hardware-facing unless a later active
  boundary is accepted

The current project may describe this boundary.

The current project may not execute it.

## 5. Accepted Target State Values

The accepted planning vocabulary for future selected target values is:

- unset
- defaulted
- explicit
- unsupported
- stale
- invalid

These are planning values only.

No enum, dataclass, runtime state object, storage, or behavior is added by
this review.

## 6. Accepted Current Passive Equivalent

Accepted current passive equivalent:

- `L` remains read-only selected isolated pad target intent
- `L` describes default Pad 3 intent
- `L` does not create selected isolated pad state
- `L` does not execute selected pad switching
- `L` does not mutate runtime state

The accepted plan distinguishes this passive intent from future runtime
selected target state.

## 7. Relationship To PZ

This review accepts that `PZ` depends on selected target state because `PZ`
means:

- return selected isolated pad to anchor only

Before `PZ` can become anything more than parked behavior, the project must be
able to answer:

- what isolated pad is selected
- whether the selected pad is known
- whether the selected pad is supported
- whether the selected pad was explicit or defaulted
- whether the selected pad can be paired with a known anchor

`PZ` remains parked.

## 8. Relationship To Anchor State

Selected target state is not anchor state.

This review accepts:

- selected target state answers what is selected
- anchor state answers what known anchor belongs to that target
- `PZ` requires both before implementation can be planned safely

Anchor state remains the next docs-only planning branch.

## 9. Accepted Safe Failure Requirements

The review accepts that any future selected target state implementation plan
must fail safely for:

- unset target
- unsupported target
- stale target
- invalid target
- target outside supported pad range
- target outside selected isolated pad scope
- attempt to use target for `PZ` without accepted anchor state
- accidental active path
- accidental hardware-facing path

Safe failure must mean:

- no dispatch
- no command execution
- no anchor return execution
- no MIDI
- no ports
- no hardware mutation
- deterministic explanatory result

## 10. Accepted Future Test Planning Requirements

Before any future selected target state implementation, tests should be planned
for:

- defaulted selected target behavior
- explicit selected target behavior
- unset target safe failure
- unsupported target safe failure
- stale target safe failure
- invalid target safe failure
- `L` behavior remains read-only until implementation is approved
- `PZ` remains parked until implementation is approved
- passive CLI behavior remains unchanged
- no MIDI libraries are imported
- no ports are opened
- no MIDI is sent
- V1.34 reference remains untouched
- package metadata remains untouched

No tests are added by this review.

## 11. Confirmed Absent Behavior

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
- selected target state implementation
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

## 12. Passive Commands Remain Read-Only

Existing passive CLI commands remain read-only:

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

## 13. Safe Next Options

Safe next options:

- docs-only anchor state plan
- docs-only selected isolated pad runtime-state plan
- broader behavior-parity progress report after selected target plan acceptance
- pause at this clean accepted checkpoint

## 14. Recommendation

Prefer a docs-only anchor state plan next.

Reason:

- `PZ` needs selected target state and anchor state.
- selected target state is now accepted for planning.
- anchor state is the next missing planning boundary before any runtime-state
  implementation plan can be considered.

Do not implement anchor state yet.

Do not implement selected target state yet.

Do not implement `PZ`.

Do not add runtime state yet.

Do not add profile `4` mock mapper support.

Do not add MIDI, ports, active behavior, runtime execution, package metadata
changes, or hardware behavior.

## 15. Decision Summary

`Docs/V134_BEHAVIOR_PARITY_SELECTED_TARGET_STATE_PLAN_AFTER_PZ_REVIEW.md` is
accepted for planning.

Selected target state remains unimplemented.

Runtime state remains unimplemented.

`PZ` remains parked.

Anchor state remains future planning scope.

Hardware remains off.

No implementation in this review slice.
