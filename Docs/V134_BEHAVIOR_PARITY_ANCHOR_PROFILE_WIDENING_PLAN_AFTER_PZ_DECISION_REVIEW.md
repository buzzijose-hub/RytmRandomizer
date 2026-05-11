# V1.34 Behavior Parity Anchor/Profile Widening Plan Review After PZ Decision

## 1. Purpose

Review and accept the anchor/profile widening plan after the accepted
remaining anchor/profile audit review.

This is a review checkpoint only. It does not implement behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this slice:

- `3cbd925 Add anchor profile widening plan after PZ decision`

Current phase:

- passive/mock foundation
- V1.34 behavior-parity implementation packets
- Packet 11A `L` accepted for read-only selected isolated pad target intent
- `PZ` parked by accepted decision note review
- remaining anchor/profile widening audit accepted
- anchor/profile widening plan created

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Review Decision

Accepted plan:

- `Docs/V134_BEHAVIOR_PARITY_ANCHOR_PROFILE_WIDENING_PLAN_AFTER_PZ_DECISION.md`

Accepted plan milestone:

- `3cbd925 Add anchor profile widening plan after PZ decision`

The anchor/profile widening plan is accepted as the current planning baseline.

This review does not authorize implementation by itself.

## 4. Accepted Plan Decision

Accepted plan decision:

- the next implementation target should be a read-only anchor/profile behavior
  report
- do not widen behavior helpers directly yet
- do not implement `PZ`
- do not add profile `4` mock mapper support
- keep the first report implementation free of CLI wiring

## 5. Accepted Future Implementation Target

Accepted future implementation files:

- `rytm_randomizer/behavior_anchor_profile_report.py`
- `tests/test_behavior_anchor_profile_report.py`

Accepted future closeout update:

- `Scripts/closeout_check.ps1`
- label:
  - `=== Test: Behavior Anchor Profile Report ===`

These files are not created in this review slice.

## 6. Accepted Future Report Scope

The future report may summarize existing read-only coverage for:

- direct Packet 2 anchor/profile behavior:
  - `BH`
  - `BC`
  - `BS`
  - `BF`
- Pad 1 lane anchor/profile intent:
  - `FZ`
  - `BP`
  - `PBH`
  - `BI`
  - `SBH`
  - `BA`
- Pad 2 lane anchor/profile intent:
  - `P2B`
  - `P2H`
  - `P2C`
  - `P2F`
  - `P2Z`
- Pad 3 anchor intent:
  - `P3A`
  - `SA`
- Pad 4 anchor intent:
  - `P4A`
- group anchor intent:
  - `O`
  - `Z`
- current-anchor state intent:
  - `B`
  - `E`
- selected-profile workflow intent:
  - `P`
  - `M`
- selected isolated pad target intent:
  - `L`
- parked/safe scope:
  - `PZ`
  - group profile `4` mock mapper support

## 7. Accepted Future Data Sources

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

The report must not call CLI entry points.

The report must not call mock message mapping.

The report must not create runtime state.

## 8. Accepted Future Test Requirements

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

## 9. Confirmed Absent Behavior

This review confirms the plan adds no:

- code changes
- tests
- closeout script changes
- package metadata changes
- CLI behavior
- runtime state
- dispatch
- command execution
- scene execution
- mutation execution
- selected pad switching execution
- selected pad anchor return execution
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
- SysEx
- GUI/capture
- Analog Four support
- Pads 5-12 support
- machine/profile universe expansion

`rytm_hybrid_randomizer_v134.py` remains untouched.

Package metadata remains untouched.

## 10. Preconditions Before Future Report Implementation

Before any read-only anchor/profile report implementation:

- clean Git status
- full closeout passing
- V1.34 reference diff empty
- package metadata diff empty
- this plan review accepted
- `PZ` remains parked
- profile `4` mock mapper support remains parked unless separately approved
- passive helpers remain read-only
- no runtime state introduced
- no CLI wiring introduced in the first implementation
- no MIDI, ports, active behavior, or hardware behavior introduced

## 11. Safe Next Options

Safe next options:

- read-only anchor/profile behavior report implementation with focused tests
- broader user-facing progress/timeline update
- pause at this clean checkpoint

## 12. Recommendation

Proceed next with the tiny read-only anchor/profile behavior report
implementation.

Keep it focused on report construction and tests only.

Do not add CLI wiring in the first report implementation.

Keep `PZ` parked.

Keep profile `4` mock mapper support parked.

Do not add MIDI, ports, active behavior, runtime execution, package metadata
changes, or hardware behavior.

## 13. Decision

The anchor/profile widening plan after the `PZ` decision is accepted.

The next recommended branch is the read-only anchor/profile behavior report
implementation.

Hardware remains off.

No implementation in this review slice.
