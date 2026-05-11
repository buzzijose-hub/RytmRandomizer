# V1.34 Behavior Parity Anchor/Profile Widening Plan After PZ Decision

## 1. Purpose

Define the next safe anchor/profile widening path after the accepted remaining
anchor/profile audit review.

This plan decides what the next implementation target should be, but does not
implement it.

This is documentation-only.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this slice:

- `b8b335f Add remaining anchor profile widening audit review after PZ decision`

Current phase:

- passive/mock foundation
- V1.34 behavior-parity implementation packets
- Packet 11A `L` accepted for read-only selected isolated pad target intent
- `PZ` parked by accepted decision note review
- remaining anchor/profile widening audit accepted

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Inputs

This plan builds on:

- `Docs/V134_BEHAVIOR_PARITY_REMAINING_ANCHOR_PROFILE_WIDENING_AUDIT_AFTER_PZ_DECISION.md`
- `Docs/V134_BEHAVIOR_PARITY_REMAINING_ANCHOR_PROFILE_WIDENING_AUDIT_AFTER_PZ_DECISION_REVIEW.md`

Accepted audit finding:

- anchor/profile-like behavior is already spread across several read-only
  helpers
- the next useful branch is visibility/planning, not immediate behavior
  expansion
- `PZ` remains parked
- group profile `4` mock mapper support remains parked

## 4. Plan Decision

The next implementation target should be a read-only anchor/profile behavior
report.

Do not widen behavior helpers directly yet.

Do not implement `PZ`.

Do not add profile `4` mock mapper support.

The future report should summarize existing read-only helper coverage and
parked scope in one deterministic in-memory structure.

## 5. Future Report Concept

Future report purpose:

- show current anchor/profile-related behavior coverage
- show parked/safe anchor/profile scope
- show passive-only safety boundaries
- give the project a single place to inspect this surface before further
  widening

The report should remain:

- read-only
- deterministic
- in-memory
- mutation-safe
- passive/import-safe
- hardware-free

## 6. Proposed Future Files

Future implementation files, if this plan is later accepted:

- `rytm_randomizer/behavior_anchor_profile_report.py`
- `tests/test_behavior_anchor_profile_report.py`

Future closeout update:

- `Scripts/closeout_check.ps1`
- label:
  - `=== Test: Behavior Anchor Profile Report ===`

Do not create these files in this planning slice.

## 7. Future Report Scope

The future report should summarize existing read-only coverage for:

Direct Packet 2 anchor/profile behavior:

- `BH`
- `BC`
- `BS`
- `BF`

Pad 1 lane anchor/profile intent:

- `FZ`
- `BP`
- `PBH`
- `BI`
- `SBH`
- `BA`

Pad 2 lane anchor/profile intent:

- `P2B`
- `P2H`
- `P2C`
- `P2F`
- `P2Z`

Pad 3 anchor intent:

- `P3A`
- `SA`

Pad 4 anchor intent:

- `P4A`

Group anchor intent:

- `O`
- `Z`

Current-anchor state intent:

- `B`
- `E`

Selected-profile workflow intent:

- `P`
- `M`

Selected isolated pad target intent:

- `L`

Parked/safe scope:

- `PZ`
- group profile `4` mock mapper support

## 8. Proposed Future Data Sources

The future report should use existing passive/read-only modules only:

- `rytm_randomizer.behavior_anchor_profile`
- `rytm_randomizer.behavior_pad1_lane`
- `rytm_randomizer.behavior_pad2_lane`
- `rytm_randomizer.behavior_pad3_lane`
- `rytm_randomizer.behavior_pad4_lane`
- `rytm_randomizer.behavior_scene_group`
- `rytm_randomizer.behavior_undo_commit_state`
- `rytm_randomizer.behavior_selected_profile`
- `rytm_randomizer.behavior_selected_isolated_pad`

The report should not call CLI entry points.

The report should not call mock message mapping.

The report should not create runtime state.

## 9. Proposed Future Report Shape

A future report may include:

- title
- phase
- supported sections
- parked sections
- safety summary
- closeout coverage references
- recommended next branch

Each supported entry should include:

- command key
- behavior family
- label or concept
- source helper
- target pad or target scope when available
- read-only status
- sends real MIDI: false
- opens ports: false
- hardware required: false
- active behavior: false

Parked entries should include:

- key or profile
- reason parked
- required approval before implementation
- safety boundaries

## 10. Future Testing Requirements

Future tests should prove:

- importing the report module prints nothing
- report output is deterministic
- returned data is copied or immutable enough for test safety
- direct Packet 2 anchor/profile keys appear
- Pad 1-4 anchor/profile-related keys appear
- group anchor keys appear
- current-anchor state keys appear
- selected-profile keys appear
- selected isolated pad target key `L` appears
- `PZ` appears as parked, not supported
- group profile `4` appears as parked, not implemented
- no real MIDI library is imported
- no ports are opened
- no MIDI is sent
- no active behavior names are exposed
- passive CLI behavior remains unchanged
- V1.34 reference diff remains empty
- package metadata remains untouched

## 11. Future CLI Position

Do not add CLI wiring in the first report implementation.

If the read-only report is later implemented and reviewed, a separate future
slice may decide whether to add a passive CLI preview command.

Any future CLI command must:

- print the existing formatted report only
- remain read-only
- open no ports
- send no MIDI
- dispatch no command
- execute no command
- require no hardware

## 12. What Remains Forbidden

This plan does not authorize:

- `PZ` implementation
- profile `4` mock mapper support
- real MIDI
- `mido`
- `rtmidi`
- port discovery
- port opening
- MIDI sending
- active CLI behavior
- runtime state
- dispatch
- command execution
- scene execution
- mutation execution
- selected pad switching execution
- selected pad anchor return execution
- hardware behavior
- hardware validation
- SysEx
- GUI/capture
- Analog Four support
- Pads 5-12 support
- package metadata changes
- machine/profile universe expansion

`rytm_hybrid_randomizer_v134.py` remains untouched.

## 13. Preconditions Before Future Implementation

Before any read-only anchor/profile report implementation:

- this plan must be reviewed and accepted
- Git status must be clean
- full closeout must pass
- V1.34 reference diff must be empty
- package metadata diff must be empty
- `PZ` must remain parked
- profile `4` mock mapper support must remain parked unless separately
  approved
- passive helpers must remain read-only
- no runtime state, MIDI, ports, active behavior, or hardware behavior may be
  introduced

## 14. Safe Next Options

Safe next options:

- docs-only review/acceptance gate for this plan
- read-only anchor/profile behavior report implementation, only after review
- broader user-facing progress/timeline update
- pause at this clean checkpoint

The follow-up review/acceptance gate is:

- `Docs/V134_BEHAVIOR_PARITY_ANCHOR_PROFILE_WIDENING_PLAN_AFTER_PZ_DECISION_REVIEW.md`

## 15. Recommendation

Review and accept this plan next.

If accepted, create the tiny read-only anchor/profile behavior report in a
separate implementation slice with focused tests and closeout coverage.

Keep `PZ` parked.

Keep profile `4` mock mapper support parked.

Do not add MIDI, ports, active behavior, runtime execution, package metadata
changes, or hardware behavior.

## 16. Decision

The preferred next implementation target is a read-only anchor/profile behavior
report.

The immediate next task is a docs-only review/acceptance gate for this plan.

Hardware remains off.

No implementation in this slice.
