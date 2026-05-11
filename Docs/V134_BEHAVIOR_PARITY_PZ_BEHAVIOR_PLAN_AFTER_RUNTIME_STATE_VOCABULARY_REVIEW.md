# V1.34 Behavior Parity PZ Behavior Plan After Runtime-State Vocabulary Review

## 1. Purpose

Review and accept the `PZ` behavior plan after the accepted runtime-state
vocabulary review.

This is a documentation-only review gate.

It accepts the plan as a planning boundary only.

It adds no implementation, tests, CLI commands, runtime state, dispatch, MIDI,
ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this review slice:

- `57a8d45 Add PZ behavior plan after runtime-state vocabulary`

Current phase:

- passive/mock foundation
- V1.34 behavior-parity implementation packets
- passive behavior reports and CLI visibility
- runtime-state vocabulary accepted for planning
- `PZ` behavior plan created
- `PZ` behavior plan now being reviewed

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Review Decision

Accepted behavior plan:

- `Docs/V134_BEHAVIOR_PARITY_PZ_BEHAVIOR_PLAN_AFTER_RUNTIME_STATE_VOCABULARY.md`

Accepted behavior plan milestone:

- `57a8d45 Add PZ behavior plan after runtime-state vocabulary`

Decision:

- accept the `PZ` behavior plan as the current planning boundary
- keep `PZ` parked
- keep runtime state unimplemented
- keep selected isolated pad runtime state unimplemented
- keep selected pad anchor return execution unimplemented
- require separate planning before any selected target state implementation
- require separate planning before any anchor state implementation

This review accepts planning only.

It does not authorize implementation.

## 4. Accepted PZ Boundary

Accepted `PZ` boundary:

- `PZ` means selected isolated pad anchor return intent.
- `PZ` depends on selected target state.
- `PZ` depends on anchor state.
- `PZ` depends on future runtime-state design before behavior can exist.
- `PZ` must fail safely if selected target or anchor state is unknown.
- `PZ` must remain separate from active and hardware-facing behavior.

The current project may describe this boundary.

The current project may not execute it.

## 5. Accepted Current PZ State

Accepted current state:

- `PZ` exists as passive metadata.
- `PZ` reports deferred/safe selected isolated pad anchor return intent.
- `PZ` does not switch pads.
- `PZ` does not return a pad to an anchor.
- `PZ` does not create selected isolated pad runtime state.
- `PZ` does not create anchor state.
- `PZ` does not mutate runtime state.
- `PZ` does not dispatch commands.
- `PZ` does not send MIDI.
- `PZ` does not open ports.
- `PZ` does not touch hardware.

## 6. Accepted Future Planning Dependencies

Accepted dependencies before any future `PZ` implementation plan:

- selected target state design
- anchor state design
- safe failure design
- mock-only tests planned before implementation
- explicit runtime-state boundary
- explicit statement that `PZ` remains non-hardware-facing

The next future planning branch should be selected target state, anchor state,
or a narrower selected isolated pad runtime-state plan.

## 7. Accepted Safe Failure Requirements

The review accepts that any future `PZ` implementation plan must fail safely
for:

- unknown command key
- unset selected isolated pad
- unsupported selected isolated pad
- missing anchor
- unsupported anchor
- stale selected target
- unsupported runtime mode
- missing explicit approval
- accidental active path
- accidental hardware-facing path

Safe failure must mean:

- no state mutation
- no dispatch
- no command execution
- no MIDI
- no ports
- no hardware mutation
- deterministic explanatory result

## 8. Accepted Test Requirements For Future Work

Before any future `PZ` runtime implementation, tests should prove:

- `PZ` remains deferred/safe until explicitly approved
- `L` behavior remains unchanged
- unknown keys fail safely
- unset selected target fails safely
- missing anchor fails safely
- unsupported selected target fails safely
- no messages are emitted
- no real MIDI library is imported
- no ports are opened
- passive CLI behavior remains unchanged
- V1.34 reference remains untouched
- package metadata remains untouched

No tests are added by this review.

## 9. Confirmed Absent Behavior

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

## 10. Passive Commands Remain Read-Only

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

## 11. Safe Next Options

Safe next options:

- docs-only selected target state plan
- docs-only anchor state plan
- docs-only selected isolated pad runtime-state plan
- broader behavior-parity progress report after `PZ` plan acceptance
- pause at this clean accepted checkpoint

## 12. Recommendation

Prefer a docs-only selected target state plan next.

Reason:

- `PZ` cannot become meaningful until the project defines what selected target
  means.
- selected target state can still be planned without implementation.
- selected target state planning can preserve the same no-MIDI, no-ports,
  no-active-behavior boundary.

Do not implement selected target state yet.

Do not implement `PZ`.

Do not add runtime state yet.

Do not add profile `4` mock mapper support.

Do not add MIDI, ports, active behavior, runtime execution, package metadata
changes, or hardware behavior.

## 13. Decision Summary

`Docs/V134_BEHAVIOR_PARITY_PZ_BEHAVIOR_PLAN_AFTER_RUNTIME_STATE_VOCABULARY.md`
is accepted for planning.

`PZ` remains parked.

Runtime state remains unimplemented.

Selected isolated pad runtime state remains unimplemented.

Selected pad anchor return execution remains unimplemented.

Hardware remains off.

No implementation in this review slice.

## 14. Follow-Up Status

This accepted review is now followed by:

- `Docs/V134_BEHAVIOR_PARITY_SELECTED_TARGET_STATE_PLAN_AFTER_PZ_REVIEW.md`

That plan describes the future selected target state boundary while keeping
selected target state unimplemented and `PZ` parked.
