# V1.34 Behavior Parity Runtime/Execution Boundary Decision Note After PZ Timeline Review

## 1. Purpose

Decide how to treat future runtime and execution concepts after the accepted
post-`PZ` progress timeline review.

This note clarifies:

- what runtime-readiness vocabulary is allowed to exist safely
- what execution behavior remains forbidden
- what must be proven before any future runtime-adjacent or active-facing work
- which next branch is safe

This is a documentation-only decision note.

It adds no implementation, tests, CLI wiring, runtime execution, dispatch,
MIDI, ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this decision slice:

- `71857a2 Add behavior parity progress timeline review after PZ`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- post-`PZ` progress timeline reviewed and accepted
- runtime/execution boundary decision now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Current Accepted State

The accepted post-`PZ` timeline records:

- passive/mock foundation is mature
- behavior-parity read-only layer is strong
- runtime-readiness vocabulary has started and is useful
- `PZ` is represented as read-only selected isolated pad anchor-return
  readiness
- active execution is not started
- real MIDI and hardware validation are not started

This means the project may continue to describe readiness and safe-failure
states.

It does not mean the project may execute commands.

## 4. Runtime-Readiness Boundary

Runtime-readiness vocabulary may describe:

- whether required context is present
- whether a selected target is known
- whether an anchor is known
- whether selected isolated pad anchor return is ready
- why a future action would fail safely
- what metadata would be needed before any future execution path

Runtime-readiness vocabulary must remain:

- read-only
- deterministic
- side-effect free
- non-dispatching
- non-hardware-facing
- safe to exercise in closeout

Runtime-readiness vocabulary must not mutate state or perform the future
action it describes.

## 5. Execution Boundary

Execution remains outside the current project phase.

Execution means any behavior that would:

- perform a command
- perform a scene
- switch a selected pad
- return an anchor
- mutate runtime state
- mutate hardware state
- send a MIDI message
- open or select a real MIDI port
- depend on attached hardware

None of that is authorized by the current behavior-parity layer.

Any future execution layer must be separately designed, reviewed, tested with
mocks first, and explicitly armed before real hardware validation is even
considered.

## 6. Allowed Future Planning Concepts

The following may be planned in future documentation or mock-only test plans:

- runtime-readiness checks
- safe-failure reasons
- mock-only active candidate test design
- missing arming failure design
- unknown/unsupported key failure design
- passive command safety regression checks
- mock-only sender expectations
- explicit active boundary interfaces as planning vocabulary

These concepts must remain documentation-only or mock-only until separately
approved.

## 7. Forbidden Current Scope

The following remain forbidden in the current phase:

- CLI execution wiring
- command dispatch
- command execution
- scene execution
- selected pad switching execution
- selected pad anchor return execution
- isolated pad mutation execution
- runtime mutation
- real MIDI dependency
- `mido`
- `rtmidi`
- port discovery
- port opening
- MIDI sending
- active CLI command
- `execute-command`
- `send-command`
- `hardware-test`
- hardware behavior
- hardware validation
- package metadata changes
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture

`rytm_hybrid_randomizer_v134.py` remains untouched.

Package metadata remains untouched.

## 8. Preconditions Before Any Runtime-Adjacent Mock-Only Test Design

Before any future runtime-adjacent mock-only test design begins:

- clean Git status
- closeout passes
- V1.34 reference diff is empty
- package metadata diff is empty
- this decision note is reviewed and accepted
- passive CLI remains read-only
- runtime-readiness helpers remain side-effect free
- mock MIDI remains inert
- no real MIDI libraries are required
- no hardware is required
- no ports are opened

## 9. Preconditions Before Any Future Execution Implementation

Execution implementation is not authorized by this note.

Before any future execution implementation can even be considered:

- runtime/execution boundary must be reviewed and accepted
- first-candidate mock-only active test design must be written
- mock-only tests must prove safe failures
- missing arming must fail safely
- unknown keys must fail safely
- unsupported keys must fail safely
- passive commands must still be proven passive
- real MIDI boundary must be separately designed and reviewed
- operator/hardware checklist must be separately reviewed
- user must explicitly approve implementation scope

## 10. Hardware Position

Hardware remains off.

Analog Rytm MKII must not be turned on for this decision note.

Analog Four MKII must not be turned on for this decision note.

Hardware is not required for this phase.

Hardware validation remains later than mock-only design, mock-only tests, real
MIDI boundary design, and an explicit operator checklist.

## 11. Safe Next Options

Safe next branches:

- Option A: review/accept this runtime/execution boundary decision note
- Option B: create a first runtime-adjacent mock-only test plan
- Option C: create a broader roadmap update after accepting this boundary
- Option D: pause at this clean planning checkpoint

## 12. Recommendation

Do a docs-only review/acceptance gate for this decision note next.

After that, the safest forward branch is a first runtime-adjacent mock-only
test plan.

Do not implement execution yet.

Do not add real MIDI.

Do not open ports.

Do not turn on hardware.

## 13. Decision

Runtime-readiness vocabulary may continue as read-only planning and safety
language.

Execution remains outside the current project phase.

The next recommended task is a docs-only review/acceptance gate for this
decision note.

Hardware remains off.

No implementation in this slice.

## 14. Review Status

This decision note is reviewed and accepted by:

- `Docs/V134_BEHAVIOR_PARITY_RUNTIME_EXECUTION_BOUNDARY_DECISION_NOTE_AFTER_PZ_TIMELINE_REVIEW_REVIEW.md`

The review accepts the runtime/execution boundary as the current planning
gate.

The next recommended task is a first runtime-adjacent mock-only test plan.
