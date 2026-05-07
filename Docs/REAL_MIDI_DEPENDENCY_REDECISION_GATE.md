# Real MIDI Dependency Re-Decision Gate

## 1. Purpose

Create the current gate for revisiting the real MIDI dependency decision now
that the first fake-provider-only adapter boundary exists.

This is a documentation-only gate.

This document does not select a dependency.

This document does not install dependencies.

This document does not edit package metadata.

This document does not import real MIDI libraries, open ports, send MIDI, add
active CLI commands, add hardware behavior, or start hardware validation.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- ede500e Add first real MIDI adapter boundary review

Current phase:

- Passive/Mock Foundation Phase
- mock-first active boundary exists for test-only evaluation
- first real MIDI adapter boundary exists
- first real MIDI adapter boundary checkpoint is reviewed and accepted
- dependency selection remains deferred

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Current Baseline

Accepted current baseline:

- `Docs/REAL_MIDI_DEPENDENCY_DECISION_NOTE.md`
- `Docs/REAL_MIDI_DEPENDENCY_DECISION_REVIEW.md`
- `Docs/REAL_MIDI_ADAPTER_FIRST_IMPLEMENTATION_CHECKPOINT.md`
- `Docs/REAL_MIDI_ADAPTER_FIRST_IMPLEMENTATION_CHECKPOINT_REVIEW.md`
- 96b20a4 Add first real MIDI adapter boundary
- a7d0fec Update checkpoint after first real MIDI adapter boundary
- ede500e Add first real MIDI adapter boundary review

The current accepted dependency decision remains:

- do not add `mido` yet
- do not add any real MIDI dependency yet
- do not install MIDI packages yet
- do not edit package metadata yet
- do not import real MIDI libraries yet
- do not open ports
- do not send MIDI

## 4. Why This Gate Exists

The original dependency decision deferred real MIDI dependency selection until
after a reviewed adapter boundary existed.

That adapter boundary now exists, but it is still fake-provider-only.

This gate creates a controlled checkpoint before any future dependency
candidate evaluation.

This gate does not mean a dependency should be added next.

This gate means dependency selection may only be revisited through another
documentation-only decision process.

## 5. Current Adapter Boundary Position

Current adapter boundary position:

- `rytm_randomizer/real_midi_adapter.py` exists
- the adapter is Python standard-library-only
- the adapter imports without loading `mido`, `rtmidi`, or `pythonrtmidi`
- the adapter requires explicit provider injection
- the adapter supports fake-provider tests only
- fake-provider sends are observable in tests
- `sent_real_midi` remains `False`
- passive CLI remains unwired from adapter behavior
- active CLI commands remain absent

The adapter boundary does not select or require a real MIDI backend.

## 6. Current Dependency Position

Current dependency position:

- no real MIDI dependency
- no `mido`
- no `python-rtmidi`
- no port provider dependency
- no sender dependency
- no real MIDI backend
- no dependency installation
- no dependency lockfile change
- no package metadata change

No dependency candidate is selected by this gate.

## 7. Required Future Dependency Evaluation

Before any dependency can be selected, a future documentation-only dependency
evaluation must be created and reviewed.

That future evaluation must answer:

- whether a real MIDI dependency is needed yet
- whether the safest next step is still to defer dependency selection
- which library candidates are being considered
- what each candidate imports at runtime
- how each candidate opens ports
- how each candidate handles unavailable ports
- how each candidate can be isolated from passive CLI imports
- how tests can prove passive commands remain passive
- what package metadata would need to change
- how package metadata changes would be reviewed separately
- how unit tests avoid real hardware and real ports

That future evaluation may discuss `mido` or another MIDI library, but this
gate does not choose one.

## 8. Required Future Package Metadata Plan

Before package metadata can change, a future documentation-only package
metadata plan must be created and reviewed.

That future plan must identify:

- exact file or files to edit
- exact dependency name and version policy
- whether a lockfile is involved
- how dependency installation is verified
- how import safety tests remain green
- how passive CLI tests remain green
- how real MIDI adapter boundary tests remain fake-provider-safe
- rollback steps if dependency installation causes risk

This gate does not authorize package metadata edits.

## 9. Required Tests Before Any Dependency Slice

Before any future dependency slice:

- closeout must pass
- V1.34 reference diff must be empty
- package metadata diff must be empty before the approved package plan
- passive imports must remain quiet
- passive imports must not open ports
- passive CLI commands must not open ports
- passive CLI commands must not send MIDI
- passive CLI commands must not construct real senders
- adapter imports must remain side-effect free
- adapter tests must remain fake-provider-only
- missing provider must fail safely
- unknown ports must fail safely
- unsupported message types must fail safely

## 10. Preconditions Before Any Future Dependency Slice

Before any future dependency slice:

- clean Git status
- closeout passes
- V1.34 reference diff is empty
- this re-decision gate is reviewed and accepted
- dependency evaluation document is created
- dependency evaluation document is reviewed and accepted
- package metadata plan is created if metadata changes are needed
- package metadata plan is reviewed and accepted
- dependency addition is explicitly approved
- hardware remains off

## 11. Preconditions Before Future Hardware Validation

This gate does not authorize hardware validation.

Before any future hardware validation:

- all mock-only tests must pass
- all real MIDI import and port safety tests must pass
- all adapter boundary tests must pass
- dependency decision must be revisited and accepted
- package metadata changes must be reviewed and accepted
- exact target device must be selected
- exact MIDI output port must be confirmed
- exact command/pad/channel scope must be confirmed
- current Analog Rytm kit/project must be saved
- monitoring volume must be lowered
- hardware validation checklist must be accepted
- user must explicitly confirm hardware validation is starting

Analog Rytm and Analog Four remain off during this gate.

## 12. Confirmed Absent Behavior

Confirmed absent:

- no `mido`
- no real MIDI dependency
- no package metadata change
- no real MIDI backend
- no real port discovery
- no real port listing
- no real port opening
- no real MIDI sending
- no active CLI command
- no execute-command
- no send-command
- no hardware-test
- no dispatch
- no command execution
- no scene execution
- no hardware behavior
- no hardware detection
- no SysEx
- no GUI/capture
- no Analog Four support
- no Pads 5-12 support
- no machine/profile expansion
- no profile `"4"` implementation
- no profile `"3"` active-boundary support
- no hardware validation

## 13. Safe Next Options

Safe next options:

- review and accept this re-decision gate
- pause at this clean dependency gate
- create a documentation-only dependency candidate evaluation
- create a broader project progress checkpoint
- return to passive/project documentation

Unsafe next moves:

- adding `mido`
- selecting or installing a real MIDI dependency
- changing package metadata
- opening real MIDI ports
- sending MIDI
- adding active CLI commands
- turning on hardware
- implementing profile `"4"`
- adding profile `"3"` active-boundary support
- starting hardware validation

## 14. Recommendation

Prefer a documentation-only review/acceptance gate for this dependency
re-decision gate next.

After that, if dependency planning continues, create a documentation-only
dependency candidate evaluation.

Do not select a dependency yet.

Do not change package metadata.

Do not open ports.

Do not send MIDI.

Do not add active CLI commands.

Do not turn on hardware.

## 15. Decision

The real MIDI dependency decision may be revisited only through a controlled
documentation-first process.

The current dependency decision remains deferred.

No dependency is selected.

No package metadata is changed.

No real MIDI behavior is added.

Hardware validation remains blocked.

Hardware remains off.

No implementation is added in this slice.
