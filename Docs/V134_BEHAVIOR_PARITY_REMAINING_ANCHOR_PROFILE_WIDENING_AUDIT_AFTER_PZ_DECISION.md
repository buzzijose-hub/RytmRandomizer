# V1.34 Behavior Parity Remaining Anchor/Profile Widening Audit After PZ Decision

## 1. Purpose

Audit the remaining anchor/profile widening surface after the accepted `PZ`
decision note review.

This document summarizes what is already covered, what remains parked or
intentionally absent, and which safe next branches are available.

This is documentation-only. It does not implement behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this slice:

- `dc5fc0d Add PZ decision note review after Packet 11A`

Current phase:

- passive/mock foundation
- V1.34 behavior-parity implementation packets
- Packet 11A `L` accepted for read-only selected isolated pad target intent
- `PZ` parked by accepted decision note review

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Packet 2 Anchor/Profile Baseline

The direct Packet 2 anchor/profile helper is:

- `rytm_randomizer/behavior_anchor_profile.py`

Current tests:

- `tests/test_behavior_anchor_profile.py`

Current closeout label:

- `=== Test: Behavior Anchor Profile ===`

Currently supported direct anchor/profile keys:

- `BH`: Pad 1 BD Hard anchor, profile key `2`, machine value `0`
- `BC`: Pad 1 BD Classic anchor, profile key `3`, machine value `1`
- `BS`: Pad 1 BD Sharp anchor, no group profile metadata invented
- `BF`: Pad 1 BD FM profiled anchor, no group profile metadata invented

The Packet 2 helper remains read-only and records intent only:

- no prompt
- no state change
- no command dispatch
- no command execution
- no MIDI
- no ports
- no hardware

## 4. Related Anchor/Profile Coverage Already Present

Anchor/profile-like behavior is now covered across multiple read-only helpers.

Pad 1 lane behavior:

- `rytm_randomizer/behavior_pad1_lane.py`
- `tests/test_behavior_pad1_lane.py`
- includes read-only Pad 1 current-engine, anchor-load, anchor-return, and
  discovery intent such as:
  - `BR`
  - `BM`
  - `FZ`
  - `BP`
  - `PBH`
  - `BI`
  - `SBH`
  - `BA`

Pad 2 lane behavior:

- `rytm_randomizer/behavior_pad2_lane.py`
- `tests/test_behavior_pad2_lane.py`
- includes read-only Pad 2 anchor-load and anchor-return intent such as:
  - `P2B`
  - `P2H`
  - `P2C`
  - `P2F`
  - `P2Z`

Pad 3 lane behavior:

- `rytm_randomizer/behavior_pad3_lane.py`
- `tests/test_behavior_pad3_lane.py`
- includes read-only Pad 3 anchor/mode intent such as:
  - `P3A`
  - `SA`

Pad 4 lane behavior:

- `rytm_randomizer/behavior_pad4_lane.py`
- `tests/test_behavior_pad4_lane.py`
- includes read-only Pad 4 BD Acoustic anchor/mode intent such as:
  - `P4A`

Scene/group behavior:

- `rytm_randomizer/behavior_scene_group.py`
- `tests/test_behavior_scene_group.py`
- includes read-only group anchor intent:
  - `O`
  - `Z`

Undo/commit/state behavior:

- `rytm_randomizer/behavior_undo_commit_state.py`
- `tests/test_behavior_undo_commit_state.py`
- includes read-only current-anchor and current-state anchor intent:
  - `B`
  - `E`

Selected-profile workflow behavior:

- `rytm_randomizer/behavior_selected_profile.py`
- `tests/test_behavior_selected_profile.py`
- includes read-only profile selection and selected-profile anchor-load intent:
  - `P`
  - `M`

Selected isolated pad behavior:

- `rytm_randomizer/behavior_selected_isolated_pad.py`
- `tests/test_behavior_selected_isolated_pad.py`
- includes read-only selected isolated pad target intent:
  - `L`
- `PZ` remains parked because selected isolated pad anchor-return semantics are
  closer to runtime state.

## 5. Current Mock Mapper Boundary

The test-only mock message mapper currently supports:

- group profile `2` / My BD Hard
- group profile `3` / My BD Classic

Current intentionally unsupported/safe profile:

- group profile `4` / My BD Acoustic

This remains useful because profile `4` proves unsupported existing metadata
can fail safely while profiles `2` and `3` prove multiple-profile mock support.

## 6. Remaining Widening Question

The remaining anchor/profile work is no longer simply "add the next command."

The repo now has many read-only anchor/profile surfaces across separate
helpers. The next useful widening question is whether to create a consolidated
anchor/profile behavior visibility layer.

Possible future visibility layer:

- a docs-only anchor/profile widening plan
- a read-only anchor/profile behavior report
- possibly a later passive CLI preview/report command

Any such work must summarize existing intent. It must not add runtime state,
dispatch, execution, MIDI, ports, or hardware behavior.

## 7. Candidate Future Report Scope

A future read-only anchor/profile report could summarize:

- direct Pad 1 anchors:
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
- Pad 2 anchor/profile intent:
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
- parked selected-isolated-pad anchor return:
  - `PZ`
- parked mock mapper profile:
  - group profile `4`

This is a future candidate only, not implementation in this slice.

## 8. What Should Stay Parked

Keep these parked unless separately approved:

- `PZ`
- selected isolated pad runtime state
- selected isolated pad anchor-return execution
- profile `4` mock mapper support
- real MIDI
- port opening
- active CLI behavior
- hardware validation

## 9. Safety Boundaries

This audit adds no:

- code changes
- test changes
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

## 10. Findings

Findings:

- Direct Packet 2 anchor/profile behavior is already covered for `BH`, `BC`,
  `BS`, and `BF`.
- Later behavior packets already cover many anchor/profile-like intents in
  read-only form.
- `PZ` remains the important parked runtime-adjacent selected isolated pad
  anchor-return case.
- Profile `4` remains the important parked mock mapper case.
- The next useful anchor/profile task should be visibility/planning, not
  immediate behavior expansion.

## 11. Safe Next Options

Safe next options:

- docs-only review/acceptance gate for this audit
- docs-only anchor/profile widening plan
- read-only anchor/profile behavior report design
- broader user-facing progress/timeline update
- pause at this clean checkpoint

The follow-up review/acceptance gate is:

- `Docs/V134_BEHAVIOR_PARITY_REMAINING_ANCHOR_PROFILE_WIDENING_AUDIT_AFTER_PZ_DECISION_REVIEW.md`

## 12. Recommendation

Review and accept this audit next.

After that, prefer a docs-only anchor/profile widening plan or a read-only
anchor/profile behavior report design before adding any new implementation.

Do not implement `PZ`.

Do not add profile `4` mock mapper support unless separately approved.

Do not add real MIDI, ports, active behavior, runtime execution, package
metadata changes, or hardware behavior.

## 13. Decision

The remaining anchor/profile widening surface has been audited at documentation
level.

The safest next branch is a review/acceptance gate for this audit.

Hardware remains off.

No implementation in this slice.
