# V1.34 Behavior Parity PZ Behavior Plan After Runtime-State Vocabulary

## 1. Purpose

Define the future behavior boundary for `PZ` after the accepted runtime-state
vocabulary review.

This is a documentation-only behavior plan.

It describes what would need to be true before `PZ` can move beyond parked
status.

It adds no implementation, tests, CLI commands, runtime state, dispatch, MIDI,
ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this planning slice:

- `36e4905 Add runtime-state vocabulary review`

Current phase:

- passive/mock foundation
- V1.34 behavior-parity implementation packets
- passive behavior reports and CLI visibility
- runtime-state vocabulary accepted for planning
- `PZ` behavior boundary now being planned at documentation level

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Prior Accepted PZ Context

Relevant prior documents:

- `Docs/V134_L_PZ_PASSIVE_METADATA_CHECKPOINT.md`
- `Docs/V134_BEHAVIOR_PARITY_PZ_DECISION_NOTE_AFTER_PACKET_11A.md`
- `Docs/V134_BEHAVIOR_PARITY_PZ_DECISION_NOTE_AFTER_PACKET_11A_REVIEW.md`
- `Docs/V134_BEHAVIOR_PARITY_PZ_NEXT_STEP_DECISION_NOTE_AFTER_ANCHOR_PROFILE_CLI_PREVIEW.md`
- `Docs/V134_BEHAVIOR_PARITY_PZ_NEXT_STEP_DECISION_NOTE_AFTER_ANCHOR_PROFILE_CLI_PREVIEW_REVIEW.md`
- `Docs/V134_BEHAVIOR_PARITY_RUNTIME_STATE_VOCABULARY_DECISION_NOTE.md`
- `Docs/V134_BEHAVIOR_PARITY_RUNTIME_STATE_VOCABULARY_DECISION_NOTE_REVIEW.md`

Accepted current state:

- `L` exists as read-only selected isolated pad target intent.
- `PZ` exists as passive metadata.
- `PZ` is reported as deferred/safe.
- `PZ` is not implemented as runtime behavior.
- `PZ` does not switch pads.
- `PZ` does not return any pad to an anchor.
- `PZ` does not dispatch, execute, send MIDI, open ports, or touch hardware.

## 4. Current PZ Meaning

Current passive metadata meaning:

- command key:
  - `PZ`
- label:
  - return selected isolated pad to anchor only
- current behavior state:
  - parked
  - read-only/deferred
  - non-executable
  - non-hardware-facing

Current read-only behavior helper state:

- `PZ` evaluates as deferred selected isolated pad anchor return intent.
- `PZ` records anchor return intent as a concept.
- `PZ` does not execute anchor return.
- `PZ` does not create selected isolated pad runtime state.
- `PZ` does not mutate runtime state.

## 5. Behavior Problem PZ Represents

`PZ` is not just a static metadata gap.

`PZ` implies:

- a selected isolated pad exists
- that selected pad has a known anchor
- returning that selected pad to its anchor is meaningful
- the return can fail safely if the target or anchor is unknown

Those are runtime-state questions.

The current modular project intentionally has no runtime selected isolated pad
state and no selected pad anchor return execution.

## 6. Accepted Vocabulary Dependencies

`PZ` depends on the accepted runtime-state vocabulary:

- selected target state
- anchor state
- runtime state
- mutation result state
- read-only behavior intent
- hardware state

For `PZ`, the critical distinction is:

- read-only behavior intent can describe what `PZ` means
- runtime state would be required to know what `PZ` should act on
- hardware state is not currently read or mutated

This plan does not implement any of those state concepts.

## 7. Selected Target State Questions

Before `PZ` can be implemented later, a future plan must answer:

- What is the selected isolated pad?
- Is there a default selected isolated pad?
- Does `L` only describe default Pad 3 intent, or can it later set a target?
- How does the system represent "no selected isolated pad"?
- How does the system represent an unsupported selected pad?
- Can the selected target be stale?
- Does selecting a target mutate runtime state, mock state, or only report
  intent?

For now, these questions remain planning-only.

## 8. Anchor State Questions

Before `PZ` can be implemented later, a future plan must answer:

- What anchor belongs to the selected isolated pad?
- Is the anchor known from passive metadata?
- Is the anchor known from a prior software action?
- Is the anchor only a read-only behavior concept?
- What happens if no anchor is known?
- What happens if the selected target and anchor disagree?
- What happens if the selected target is outside the supported passive scope?

For now, no anchor state is created, stored, updated, or restored.

## 9. Current Safe Behavior Decision

Current decision:

- keep `PZ` parked
- define future behavior requirements only
- do not implement `PZ`
- do not create runtime selected isolated pad state
- do not create anchor state
- do not add selected pad switching
- do not add selected pad anchor return execution
- do not wire `PZ` to CLI execution

This preserves the safe boundary while making the future path clearer.

## 10. Future PZ Behavior Shape

If `PZ` is ever planned for implementation later, the safest conceptual shape
would be:

- validate selected target state
- validate anchor state
- refuse unknown or unset target
- refuse unknown or unsupported anchor
- produce a deterministic read-only preview first
- produce mock-only test coverage before any runtime behavior
- remain isolated from hardware
- require a separate runtime-state design before execution

This is a future shape only.

It is not implementation authorization.

## 11. Future Safe Failure Requirements

Any future `PZ` implementation plan must require safe failure for:

- unknown command key
- unset selected isolated pad
- unsupported selected isolated pad
- missing anchor
- unsupported anchor
- stale selected target
- unsupported runtime mode
- missing explicit approval
- any accidental active or hardware-facing path

Safe failure means:

- no state mutation
- no dispatch
- no command execution
- no MIDI
- no ports
- no hardware mutation
- deterministic explanatory result

## 12. Future Mock-Only Test Requirements

Before any future `PZ` runtime implementation, tests should prove:

- `PZ` still reports deferred/safe until implementation is explicitly approved
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

These tests are not added by this plan.

## 13. Relationship To CLI

No new CLI command is added by this plan.

Existing passive CLI commands must remain read-only:

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

Future `PZ` planning must not wire CLI to runtime execution without a separate
accepted runtime-state design.

## 14. Relationship To Active And Hardware Work

`PZ` planning is not active execution.

`PZ` planning is not real MIDI.

`PZ` planning is not hardware validation.

Even if future `PZ` behavior is implemented as runtime state later, it must
remain separate from real hardware-facing behavior unless a later active
boundary is reviewed and accepted.

Hardware remains off.

## 15. Confirmed Absent Behavior

This plan confirms no:

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

## 16. Preconditions Before Any Future PZ Implementation Plan

Before any future `PZ` implementation plan:

- clean Git status
- full closeout passing
- V1.34 reference diff empty
- package metadata diff empty
- this behavior plan reviewed and accepted
- selected target state design accepted
- anchor state design accepted
- failure behavior accepted
- tests planned before implementation
- explicit statement that implementation remains mock-only/runtime-only and
  not hardware-facing

## 17. Safe Next Options

Safe next options:

- docs-only review/acceptance gate for this `PZ` behavior plan
- docs-only selected target state plan
- docs-only anchor state plan
- docs-only runtime-state plan for selected isolated pad only
- pause at this clean checkpoint

## 18. Recommendation

Review and accept this `PZ` behavior plan next.

After that, prefer a docs-only selected target state plan before any
implementation.

Do not implement `PZ` yet.

Do not add runtime state yet.

Do not add profile `4` mock mapper support.

Do not add MIDI, ports, active behavior, runtime execution, package metadata
changes, or hardware behavior.

## 19. Decision Summary

The future `PZ` behavior boundary is now described.

`PZ` remains parked.

Runtime state remains unimplemented.

Hardware remains off.

No implementation in this planning slice.
