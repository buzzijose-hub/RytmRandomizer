# V1.34 Behavior Parity Remaining Gap Audit After Anchor/Profile CLI Visibility

## 1. Purpose

Audit the remaining V1.34 behavior-parity gaps after the accepted passive
anchor/profile report CLI preview and the accepted current `PZ` next-step
decision review.

This document summarizes:

- what is already covered in read-only behavior-parity form
- what is visible from passive CLI/report surfaces
- what remains parked
- what remains intentionally absent
- what the safest next branches are

This is documentation-only.

It adds no implementation, tests, CLI commands, runtime state, dispatch, MIDI,
ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this audit slice:

- `3b7605e Add PZ next-step decision review after anchor profile CLI preview`

Current phase:

- passive/mock foundation
- V1.34 behavior-parity implementation packets
- passive behavior reports and CLI visibility
- passive anchor/profile report CLI preview implemented and accepted
- behavior-parity progress/timeline update accepted
- current `PZ` next-step decision accepted
- remaining behavior-parity gaps now being audited

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Current Read-Only Behavior-Parity Coverage

Accepted read-only behavior helper coverage includes:

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

Accepted behavior report and CLI visibility includes:

- anchor/profile behavior report
- passive `anchor-profile-report` CLI preview
- behavior-parity progress/timeline update and review
- current `PZ` next-step decision and review

These surfaces remain read-only, deterministic, import-safe, non-dispatching,
non-executing, non-mutating, and hardware-free.

## 4. Current Passive CLI Visibility

Current passive CLI visibility includes:

- `report`
- `mock-mapper-report`
- `active-boundary-report`
- `anchor-profile-report`
- list/search/inspect/preview commands

The CLI can now show a substantial behavior-parity control-room view without
executing commands or touching hardware.

## 5. Remaining Parked Scope

Parked/safe scope remains:

- `PZ`
- group profile `4` mock mapper support

`PZ` remains parked because it implies selected isolated pad anchor return
semantics, which are closer to runtime state than the accepted read-only `L`
selected isolated pad target intent.

Group profile `4` remains parked because profiles `2` and `3` already prove
multiple-profile mock mapper support, while profile `4` remains useful as
unsupported/safe mock mapper coverage.

## 6. Remaining Gap Categories

The remaining gaps are no longer simple missing metadata or report entries.
They are mostly boundary decisions.

### Gap A: Selected Isolated Pad Anchor Return

Representative parked command:

- `PZ`

Current status:

- visible as parked
- not implemented
- not executable
- not wired to CLI execution
- no selected isolated pad runtime state exists
- no selected pad anchor return execution exists

Safe next treatment:

- keep parked unless a separate docs-only `PZ` behavior plan is approved

### Gap B: Mock Mapper Profile 4

Representative parked profile:

- group profile `4` / My BD Acoustic

Current status:

- visible as unsupported/safe
- not mapped by mock message mapper
- not needed to prove multiple-profile support

Safe next treatment:

- keep parked unless a separate profile `4` support plan is approved

### Gap C: Runtime State And Execution

Still absent:

- runtime prompt behavior
- selected profile runtime state
- selected isolated pad runtime state
- current profile runtime state
- lane runtime state
- anchor state mutation
- mutation result state
- dispatch
- command execution
- scene execution
- mutation execution

Safe next treatment:

- do not implement from this audit
- keep future runtime work behind separate design and review gates

### Gap D: Active CLI And Hardware Boundary

Still absent:

- active CLI command
- `execute-command`
- `send-command`
- `hardware-test`
- real MIDI dependency
- port discovery
- port opening
- MIDI sending
- hardware validation

Safe next treatment:

- do not implement from this audit
- keep hardware off
- keep active work behind existing mock-only and real-MIDI boundary gates

## 7. What Appears Covered Enough For Now

The following areas appear covered enough for the current read-only
behavior-parity phase:

- menu/utility intent
- direct Pad 1 anchor/profile intent
- mutation depth and guarded input intent
- scene/group intent
- Pad 1 lane intent
- Pad 2 lane intent
- Pad 3 lane intent
- Pad 4 lane intent
- undo/commit/state intent
- selected-profile workflow intent
- selected isolated pad target intent through `L`
- anchor/profile visibility through report and CLI preview

This does not mean those areas are active or hardware-ready. It means their
current read-only parity representation is sufficient to avoid widening them
without a fresh reason.

## 8. Confirmed Absent Behavior

This audit confirms no:

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
- machine/profile universe expansion

`rytm_hybrid_randomizer_v134.py` remains untouched.

Package metadata remains untouched.

## 9. Findings

Findings:

- The passive behavior-parity foundation is broad enough that the remaining
  work is now more about boundary decisions than missing read-only helpers.
- `PZ` remains the clearest runtime-adjacent selected isolated pad gap.
- Profile `4` remains the clearest mock mapper parked case.
- The passive CLI now exposes enough reporting to support informed operator
  review without active behavior.
- No immediate behavior implementation should be added from this audit.

## 10. Safe Next Options

Safe next options:

- docs-only review/acceptance gate for this audit
- broader user-facing behavior-parity progress report
- docs-only `PZ` behavior plan, only if explicitly approved
- docs-only profile `4` support plan, only if explicitly approved
- pause at this clean checkpoint

## 11. Recommendation

Review and accept this remaining gap audit next.

After that, prefer a broader user-facing behavior-parity progress report before
any new implementation.

Do not implement `PZ`.

Do not add profile `4` mock mapper support.

Do not add MIDI, ports, active behavior, runtime execution, package metadata
changes, or hardware behavior.

## 12. Decision

The remaining behavior-parity gaps after anchor/profile CLI visibility have
been audited at documentation level.

The safest next branch is a docs-only review/acceptance gate for this audit.

Hardware remains off.

No implementation in this audit slice.
