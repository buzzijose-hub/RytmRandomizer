# Real MIDI Dependency Candidate Evaluation

## 1. Purpose

Evaluate possible future real MIDI dependency paths after the accepted
re-decision gate.

This is a documentation-only candidate evaluation.

This document does not select a dependency.

This document does not install dependencies.

This document does not edit package metadata.

This document does not import real MIDI libraries, open ports, send MIDI, add
active CLI commands, add hardware behavior, or start hardware validation.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 7feb3ac Add real MIDI dependency re-decision gate review

Current phase:

- Passive/Mock Foundation Phase
- mock-first active boundary exists for test-only evaluation
- first fake-provider-only real MIDI adapter boundary exists
- real MIDI dependency re-decision gate is reviewed and accepted
- dependency candidate evaluation is now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Baseline

Accepted baseline:

- `Docs/REAL_MIDI_DEPENDENCY_DECISION_NOTE.md`
- `Docs/REAL_MIDI_DEPENDENCY_DECISION_REVIEW.md`
- `Docs/REAL_MIDI_DEPENDENCY_REDECISION_GATE.md`
- `Docs/REAL_MIDI_DEPENDENCY_REDECISION_GATE_REVIEW.md`
- `Docs/REAL_MIDI_ADAPTER_FIRST_IMPLEMENTATION_CHECKPOINT.md`
- `Docs/REAL_MIDI_ADAPTER_FIRST_IMPLEMENTATION_CHECKPOINT_REVIEW.md`
- `rytm_randomizer/real_midi_adapter.py`
- `tests/test_real_midi_adapter_boundary.py`

Accepted current position:

- no real MIDI dependency
- no `mido`
- no `python-rtmidi`
- no package metadata change
- no real MIDI backend
- no real port opening
- no MIDI sending
- no active CLI command
- no hardware validation

## 4. Evaluation Criteria

Any future dependency candidate must satisfy:

- passive imports remain quiet
- passive CLI commands remain read-only
- passive CLI commands do not import real MIDI libraries
- passive CLI commands do not open ports
- passive CLI commands do not send MIDI
- adapter import remains side-effect free
- adapter tests remain fake-provider-only by default
- missing dependency fails safely
- missing provider fails safely
- unknown port fails safely
- package metadata changes are separately reviewed
- hardware is not required for unit tests
- V1.34 reference remains untouched

## 5. Candidate A: Continue With No Real MIDI Dependency

Description:

- Keep the current fake-provider-only adapter boundary.
- Keep dependency selection deferred.
- Keep package metadata unchanged.

Benefits:

- lowest risk
- preserves current closeout safety
- avoids accidental import or port behavior
- keeps passive CLI completely isolated
- keeps hardware off

Costs:

- no real MIDI backend is available yet
- no real port discovery can be tested yet
- hardware validation remains blocked

Safety result:

- safest current option
- compatible with current closeout
- compatible with current passive/mock foundation

Evaluation:

- Candidate A remains the recommended current position.

## 6. Candidate B: Future `mido`-Style Adapter Backend

Description:

- Consider a future `mido`-style dependency path only after separate review.
- Treat any backend required by that path as a separate dependency decision.
- Keep imports isolated behind `rytm_randomizer/real_midi_adapter.py`.

Potential benefits:

- may provide a familiar MIDI message and port abstraction
- may fit the existing adapter boundary concept
- may reduce custom backend code later

Risks and required proof:

- must not load during passive imports
- must not load during passive CLI commands
- must not open ports during import
- must not send MIDI during tests
- must not require hardware for unit tests
- must be covered by package metadata review
- must preserve fake-provider tests

Evaluation:

- not selected
- requires primary-source verification before any future selection
- requires a separate package metadata plan before any install

## 7. Candidate C: Future Direct Backend Adapter

Description:

- Consider a future direct backend dependency only after separate review.
- Keep backend-specific objects out of passive CLI and high-level active
  boundary logic.
- Keep backend access isolated behind explicit provider/sender injection.

Potential benefits:

- may expose lower-level control over port behavior
- may reduce abstraction layers if carefully isolated

Risks and required proof:

- higher risk of backend-specific behavior leaking into project code
- must not load during passive imports
- must not open ports during import
- must not require connected hardware for unit tests
- must preserve fake-provider adapter tests
- must preserve deterministic safe failures
- must be covered by package metadata review

Evaluation:

- not selected
- remains a later comparison candidate only
- requires separate documentation and review before any package changes

## 8. Candidate D: Custom Or OS-Specific MIDI Path

Description:

- Avoid a library dependency and attempt custom OS-specific MIDI integration.

Potential benefits:

- no third-party MIDI package dependency

Risks:

- higher maintenance burden
- likely platform-specific behavior
- harder to keep tests isolated
- higher risk of port behavior leaking into runtime
- not aligned with current narrow adapter boundary

Evaluation:

- not recommended for the current phase
- not selected
- should remain parked unless a future requirement makes it necessary

## 9. Evaluation Decision

Decision:

- keep dependency selection deferred
- keep package metadata unchanged
- keep no-dependency Candidate A as the current accepted position
- do not select `mido`
- do not select `python-rtmidi`
- do not select a direct backend dependency
- do not select an OS-specific custom path

The project is not ready to install a real MIDI dependency yet.

## 10. Required Future Package Metadata Plan

Before any dependency can be installed, a separate documentation-only package
metadata plan must be created and reviewed.

That future plan must identify:

- exact package name
- exact package version policy
- exact metadata file or files to edit
- whether a lockfile is involved
- install and rollback steps
- import-safety verification commands
- passive CLI safety verification commands
- adapter boundary verification commands
- package metadata diff expectations

This evaluation does not authorize package metadata edits.

## 11. Required Future Dependency Selection Review

Before dependency installation:

- this candidate evaluation must be reviewed and accepted
- a specific candidate must be selected in a separate review
- a package metadata plan must be reviewed and accepted
- dependency addition must be explicitly approved
- closeout must pass
- V1.34 reference diff must be empty
- hardware must remain off

## 12. Preconditions Before Future Hardware Validation

This evaluation does not authorize hardware validation.

Before any future hardware validation:

- all mock-only tests must pass
- all real MIDI import and port safety tests must pass
- all adapter boundary tests must pass
- any dependency selection must be reviewed and accepted
- any package metadata changes must be reviewed and accepted
- exact target device must be selected
- exact MIDI output port must be confirmed
- exact command/pad/channel scope must be confirmed
- current Analog Rytm kit/project must be saved
- monitoring volume must be lowered
- hardware validation checklist must be accepted
- user must explicitly confirm hardware validation is starting

Analog Rytm and Analog Four remain off during this evaluation.

## 13. Confirmed Absent Behavior

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

## 14. Safe Next Options

Safe next options:

- review and accept this dependency candidate evaluation
- pause at this no-dependency evaluation checkpoint
- create a documentation-only package metadata plan only after explicit
  approval
- create a broader project progress checkpoint
- return to passive/project documentation

Unsafe next moves:

- adding `mido`
- selecting or installing a real MIDI dependency without review
- changing package metadata without a package metadata plan
- opening real MIDI ports
- sending MIDI
- adding active CLI commands
- turning on hardware
- implementing profile `"4"`
- adding profile `"3"` active-boundary support
- starting hardware validation

## 15. Recommendation

Prefer a documentation-only review/acceptance gate for this dependency
candidate evaluation next.

The review gate for this dependency candidate evaluation is:

- `Docs/REAL_MIDI_DEPENDENCY_CANDIDATE_EVALUATION_REVIEW.md`

The review accepts Candidate A, continue with no real MIDI dependency, as the
current position. It does not authorize dependency selection, package metadata
changes, real port opening, MIDI sending, active CLI commands, hardware
behavior, hardware validation, or hardware-on authorization.

Keep Candidate A, no real MIDI dependency, as the current position.

Do not select a dependency yet.

Do not change package metadata.

Do not open ports.

Do not send MIDI.

Do not add active CLI commands.

Do not turn on hardware.

## 16. Decision

The dependency candidate evaluation is documented.

No dependency is selected.

Candidate A, continue with no real MIDI dependency, remains the current
recommended position.

Package metadata remains unchanged.

No real MIDI behavior is added.

Hardware validation remains blocked.

Hardware remains off.

No implementation is added in this slice.
