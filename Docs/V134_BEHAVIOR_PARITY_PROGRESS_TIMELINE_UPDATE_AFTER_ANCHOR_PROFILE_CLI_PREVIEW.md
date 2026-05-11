# V1.34 Behavior Parity Progress Timeline Update After Anchor/Profile CLI Preview

## 1. Purpose

Provide a broader behavior-parity progress and timeline update after the
accepted passive anchor/profile behavior report CLI preview.

This report summarizes:

- what exists now
- what has been proven
- what remains parked or intentionally absent
- where the project is in the behavior-parity phase
- what the safe next branches are
- rough time expectations before the next phase

This report is documentation-only.

It adds no implementation, tests, CLI commands, runtime state, dispatch, MIDI,
ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this slice:

- `6ba7a06 Add anchor profile report CLI preview review`

Current phase:

- passive/mock foundation
- V1.34 behavior-parity implementation packets
- passive behavior reports and CLI visibility
- anchor/profile behavior report CLI preview implemented and accepted
- broader behavior-parity progress/timeline now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Current Behavior-Parity State

The project now has a substantial read-only behavior-parity foundation.

Implemented and accepted behavior helper surfaces include:

- menu/utility behavior
- anchor/profile behavior
- mutation-depth and guarded input behavior
- scene/group intent behavior
- Pad 1 lane behavior
- Pad 2 lane behavior
- Pad 3 lane behavior
- Pad 4 lane behavior
- undo/commit/state intent behavior
- selected-profile workflow intent
- selected isolated pad target intent

Additional read-only visibility now exists for:

- anchor/profile behavior report
- anchor/profile behavior report CLI preview

This means the project can now inspect and report a much larger slice of
V1.34-like behavior without executing anything.

## 4. Current Passive CLI Visibility

Current passive CLI visibility includes:

- `python -m rytm_randomizer.cli report`
- `python -m rytm_randomizer.cli mock-mapper-report`
- `python -m rytm_randomizer.cli active-boundary-report`
- `python -m rytm_randomizer.cli anchor-profile-report`
- `python -m rytm_randomizer.cli list-commands`
- `python -m rytm_randomizer.cli list-scenes`
- `python -m rytm_randomizer.cli list-group-profiles`
- `python -m rytm_randomizer.cli search-commands <query>`
- `python -m rytm_randomizer.cli search-scenes <query>`
- `python -m rytm_randomizer.cli search-group-profiles <query>`
- `python -m rytm_randomizer.cli inspect-command <key>`
- `python -m rytm_randomizer.cli inspect-scene <key>`
- `python -m rytm_randomizer.cli inspect-group-profile <key>`
- `python -m rytm_randomizer.cli preview-command <key>`
- `python -m rytm_randomizer.cli preview-scene <key>`
- `python -m rytm_randomizer.cli preview-group-profile <key>`

These commands remain passive/read-only.

They do not execute commands, open ports, send MIDI, mutate hardware, or
require hardware.

## 5. Latest Meaningful Milestone

Latest meaningful implementation milestone:

- `0e3de07 Add passive anchor profile report CLI preview`

Latest accepted checkpoint:

- `6ba7a06 Add anchor profile report CLI preview review`

What it means:

- the anchor/profile behavior report can now be viewed from the passive CLI
- passive CLI visibility is present
- active CLI wiring remains absent
- the report exposes parked `PZ`
- the report exposes parked group profile `4`
- closeout verifies the new visibility layer

This is another step toward a usable operator-facing control-room view without
crossing into execution.

## 6. What Has Been Proven

The current foundation proves:

- V1.34 reference protection is still working.
- Behavior intent can be represented in deterministic read-only helpers.
- Behavior reports can summarize cross-helper coverage safely.
- Passive CLI commands can expose reports without becoming active commands.
- Tests can distinguish passive CLI visibility from active CLI wiring.
- Parked scope can remain visible without being implemented.
- `PZ` can remain parked without blocking progress.
- Group profile `4` mock mapper support can remain parked without blocking
  progress.
- The closeout suite can protect an increasingly broad passive/mock surface.

## 7. Current Closeout Coverage

Current closeout coverage includes:

- scaffold
- validation
- inspection
- preview
- audit
- profile lookup
- scene lookup
- command lookup
- registry
- registry report
- registry report CLI
- passive CLI
- behavior menu utility
- behavior anchor profile
- behavior anchor profile report
- behavior mutation depth
- behavior scene group
- behavior Pad 1 lane
- behavior Pad 2 lane
- behavior Pad 3 lane
- behavior Pad 4 lane
- behavior undo/commit/state
- behavior selected profile
- behavior selected isolated pad
- mock MIDI
- mock message mapper
- mock mapper report
- mock-only active candidate
- active boundary
- active boundary report
- real MIDI import safety
- real MIDI passive CLI safety
- real MIDI adapter boundary

## 8. What Remains Parked

Parked/safe scope:

- `PZ`
- group profile `4` mock mapper support

`PZ` remains selected isolated pad anchor-return scope. It is closer to stateful
behavior than the already accepted `L` selected isolated pad target intent, so
it should not be rushed.

Group profile `4` remains useful as unsupported/safe mock mapper coverage.
Profiles `2` and `3` already prove multiple-profile mock support.

## 9. What Remains Intentionally Absent

Still absent:

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
- package metadata changes
- machine/profile universe expansion

`rytm_hybrid_randomizer_v134.py` remains untouched.

Package metadata remains untouched.

## 10. Progress Estimate

Approximate current progress:

- full dream project:
  - 30-35%
- core modular software foundation:
  - 85-90%
- passive CLI / dry-run / visibility foundation:
  - 95%+
- captured V1.34 passive metadata map:
  - 100% for the currently captured command surface
- read-only behavior-parity foundation:
  - 80-90%
- mock MIDI / mock active-boundary foundation:
  - 70-80%
- real MIDI / hardware validation:
  - 0% real hardware validation
- GUI/reference-analysis/performance ecosystem:
  - not started

These are planning estimates, not release promises.

## 11. Rough Timeline Expectations

If work continues in larger safe packets:

- next documentation/review checkpoint:
  - roughly 30-60 minutes
- remaining read-only behavior-parity planning and cleanup:
  - roughly 4-10 focused hours
- deciding and documenting `PZ` next steps:
  - roughly 1-3 focused hours
- implementing any tiny read-only `PZ`-adjacent visibility, if approved:
  - roughly 2-5 focused hours
- mock-only active-candidate refinement after read-only parity stabilizes:
  - roughly 6-12 focused hours
- real hardware validation preparation after mock-only confidence:
  - roughly 4-8 focused hours before any hardware is turned on

Real hardware validation should remain later and separately approved.

The next phase is closer, but it is not yet hardware execution.

The next phase is likely one of:

- final behavior-parity cleanup/decision work
- mock-only active-candidate refinement
- first real-MIDI boundary planning

## 12. Recommended Next Branches

Safe next branches:

- Option A: docs-only review/acceptance gate for this progress/timeline update
- Option B: docs-only `PZ` next-step decision note
- Option C: remaining behavior-parity gap audit after anchor/profile CLI
  visibility
- Option D: pause at this clean checkpoint
- Option E: broader user-facing progress report

## 13. Recommendation

Review and accept this progress/timeline update next.

Then choose between:

- a `PZ` next-step decision note, or
- a remaining behavior-parity gap audit.

Do not jump to real MIDI.

Do not turn on hardware.

Do not add active CLI commands yet.

Do not implement `PZ` without a separate decision.

Do not add profile `4` mock mapper support without a separate decision.

## 14. Decision

The behavior-parity visibility layer is now strong enough to pause, review, or
choose a tightly bounded next branch.

Hardware remains off.

No implementation in this slice.
