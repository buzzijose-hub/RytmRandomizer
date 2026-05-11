# V1.34 Behavior Parity PZ Next-Step Decision Note After Anchor/Profile CLI Preview

## 1. Purpose

Revisit the parked `PZ` scope after the accepted behavior-parity
progress/timeline review following the passive anchor/profile report CLI
preview.

This is a current-state decision note. It does not replace the earlier accepted
`PZ` decision note after Packet 11A. It confirms whether anything about the
newer anchor/profile report visibility changes the `PZ` decision.

This document is documentation-only.

It adds no implementation, tests, CLI commands, runtime state, dispatch, MIDI,
ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this decision slice:

- `394ce13 Add behavior parity progress timeline review`

Current phase:

- passive/mock foundation
- V1.34 behavior-parity implementation packets
- passive behavior reports and CLI visibility
- passive anchor/profile report CLI preview implemented and accepted
- behavior-parity progress/timeline update accepted
- `PZ` next-step decision now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Prior Accepted PZ Decision

Earlier accepted `PZ` decision note:

- `Docs/V134_BEHAVIOR_PARITY_PZ_DECISION_NOTE_AFTER_PACKET_11A.md`

Earlier accepted review:

- `Docs/V134_BEHAVIOR_PARITY_PZ_DECISION_NOTE_AFTER_PACKET_11A_REVIEW.md`

Accepted earlier decision:

- keep `PZ` parked

Reasoning that still applies:

- `PZ` implies returning the selected isolated pad to an anchor.
- Anchor return semantics are closer to runtime state than `L`.
- The modular behavior layer still has no selected isolated pad runtime state.
- The modular behavior layer still has no selected pad anchor return execution.
- `L` already provides a safe read-only selected isolated pad target surface.

## 4. What Changed Since The Prior PZ Decision

Since the earlier `PZ` decision, the project added more read-only visibility:

- anchor/profile behavior report
- passive `anchor-profile-report` CLI preview
- behavior-parity progress/timeline update after that CLI preview
- review and acceptance of that progress/timeline update

These changes improve reporting and operator visibility.

They do not add:

- selected isolated pad runtime state
- selected pad switching execution
- selected pad anchor return execution
- mutation execution
- dispatch
- active CLI behavior
- MIDI
- ports
- hardware behavior

## 5. Current Decision

Decision:

- keep `PZ` parked

Do not implement `PZ` now.

Do not create a `PZ` implementation plan now.

Do not add selected isolated pad runtime state.

Do not add selected pad anchor return execution.

Do not add dispatch, MIDI, ports, active behavior, runtime execution, package
metadata changes, or hardware behavior.

## 6. Why PZ Remains Parked

`PZ` remains parked because the newer anchor/profile report visibility is still
read-only reporting. It does not solve the state questions behind selected
isolated pad anchor return behavior.

The current project can now show that `PZ` is parked, but it should not execute
or simulate the runtime effects of returning a selected pad to an anchor.

This is useful because:

- the operator can see the parked boundary
- tests can protect passive visibility
- behavior-parity work can continue without crossing into runtime state
- future `PZ` work can be designed only when the selected-pad state boundary is
  intentionally addressed

## 7. Preconditions Before Revisiting PZ Again

Before `PZ` can move from parked to planned, the project should have:

- clean Git status
- full closeout passing
- V1.34 reference diff empty
- package metadata diff empty
- accepted current `PZ` next-step decision
- clear selected isolated pad target semantics
- clear selected isolated pad anchor semantics
- explicit decision about whether selected-pad state remains read-only or gets
  a mock-only representation first
- docs-only `PZ` behavior plan, if later approved

Even then, future `PZ` work must remain read-only and intent-only unless a
separate active/runtime design is accepted.

## 8. Confirmed Absent Behavior

This decision note confirms no:

- active CLI command
- `execute-command`
- `send-command`
- `hardware-test`
- dispatch
- command execution
- scene execution
- mutation execution
- runtime state
- selected profile runtime state
- selected isolated pad runtime state
- selected pad switching execution
- selected pad anchor return execution
- `PZ` implementation
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
- package metadata changes
- machine/profile universe expansion

`rytm_hybrid_randomizer_v134.py` remains untouched.

Package metadata remains untouched.

## 9. Safe Next Options

Safe next options:

- docs-only review/acceptance gate for this current `PZ` next-step decision
- remaining behavior-parity gap audit after anchor/profile CLI visibility
- broader user-facing behavior-parity progress report
- pause at this clean checkpoint

## 10. Recommendation

Review and accept this current `PZ` next-step decision note next.

After that, prefer a remaining behavior-parity gap audit after anchor/profile
CLI visibility.

Do not implement `PZ`.

Do not add profile `4` mock mapper support.

Do not add MIDI, ports, active behavior, runtime execution, package metadata
changes, or hardware behavior.

## 11. Decision Summary

`PZ` remains parked after the passive anchor/profile report CLI preview.

The newer report visibility makes the parked boundary clearer, but it does not
authorize implementation.

The next recommended branch is a docs-only review/acceptance gate for this note.

Hardware remains off.

No implementation in this decision slice.
