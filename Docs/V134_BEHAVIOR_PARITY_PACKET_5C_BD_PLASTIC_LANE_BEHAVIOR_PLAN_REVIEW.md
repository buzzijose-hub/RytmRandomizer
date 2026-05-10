# V1.34 Behavior Parity Packet 5C BD Plastic Lane Behavior Plan Review

## 1. Purpose

Review and accept the Packet 5C BD Plastic lane behavior plan.

This is a documentation-only review checkpoint. It adds no implementation,
tests, CLI wiring, dispatch, MIDI, port opening, package metadata, active
behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this slice:

- `9d88b2b Add Packet 5C BD Plastic lane behavior plan`

Current phase:

- Passive/Mock Foundation Phase
- Packet 1 complete and accepted
- Packet 2 accepted as meaningful anchor/profile progress
- Packet 3 complete and accepted
- Packet 4 complete and accepted
- Packet 5A complete and accepted
- Packet 5B complete and accepted
- broader behavior-parity progress report after Packet 5B accepted
- Packet 5C BD Plastic lane behavior plan created
- Packet 5C BD Plastic lane behavior plan now reviewed and accepted

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Review Decision

Accepted plan document:

- `Docs/V134_BEHAVIOR_PARITY_PACKET_5C_BD_PLASTIC_LANE_BEHAVIOR_PLAN.md`

Accepted plan milestone:

- `9d88b2b Add Packet 5C BD Plastic lane behavior plan`

Accepted packet identity:

- Packet 5C: Pad 1 BD Plastic Lane Behavior Parity

Decision:

- Packet 5C plan accepted.
- The next implementation target is a tiny read-only `BP`/`PT`/`PK`/`PX`/
  `PBH` intent behavior slice.
- This review does not implement or authorize execution behavior by itself.
- Hardware remains off.

## 4. Accepted Packet 5C Scope

Accepted future implementation scope:

- `BP`: load Pad 1 BD Plastic profiled anchor
- `PT`: BD Plastic tone/modulation discovery
- `PK`: BD Plastic kick/body discovery
- `PX`: BD Plastic rubber/experimental discovery
- `PBH`: return Pad 1 BD Plastic to anchor

Already-covered context remains outside Packet 5C implementation:

- `PD`: show BD Plastic menu/status, covered by Packet 1

Packet 5C may reference `PD` as context, but must not reimplement or change
its existing behavior.

## 5. Accepted Packet 5C Semantics

Accepted future `BP` semantics:

- read-only BD Plastic profiled anchor/load intent
- target pad `1`
- lane `Pad 1 BD Plastic`
- copied metadata from `PAD1_COMMANDS`
- BD Plastic anchor/profile dependency recorded only
- no anchor/load execution
- no state mutation
- no dispatch
- no command execution
- no MIDI
- no port opening
- no hardware requirement

Accepted future `PT`, `PK`, and `PX` semantics:

- read-only BD Plastic discovery intent
- target pad `1`
- lane `Pad 1 BD Plastic`
- copied metadata from `PAD1_COMMANDS`
- BD Plastic engine/profile dependency recorded only
- future discovery depth dependency recorded only
- no prompt loop
- no state mutation
- no dispatch
- no command execution
- no MIDI
- no port opening
- no hardware requirement

Accepted future `PBH` semantics:

- read-only BD Plastic anchor-return intent
- target pad `1`
- lane `Pad 1 BD Plastic`
- copied metadata from `PAD1_COMMANDS`
- BD Plastic anchor dependency recorded only
- no anchor-return execution
- no state mutation
- no dispatch
- no command execution
- no MIDI
- no port opening
- no hardware requirement

## 6. Accepted Future File Ownership

Allowed future implementation files:

- `rytm_randomizer/behavior_pad1_lane.py`
- `tests/test_behavior_pad1_lane.py`

Closeout script:

- no closeout script update should be needed
- `tests/test_behavior_pad1_lane.py` is already covered by
  `=== Test: Behavior Pad 1 Lane ===`

Files and areas that should remain untouched:

- `rytm_hybrid_randomizer_v134.py`
- `rytm_randomizer/cli.py`
- `rytm_randomizer/mock_midi.py`
- `rytm_randomizer/mock_message_mapper.py`
- `rytm_randomizer/mock_mapper_report.py`
- `rytm_randomizer/active_boundary.py`
- `rytm_randomizer/active_boundary_report.py`
- `rytm_randomizer/real_midi_adapter.py`
- package metadata files
- active CLI command files or paths
- runtime execution/dispatch/MIDI logic
- docs, except for a later implementation checkpoint/review

## 7. Accepted Future TDD Plan

Future implementation should:

1. Extend `tests/test_behavior_pad1_lane.py` with failing tests for `BP`,
   `PT`, `PK`, `PX`, and `PBH`.
2. Confirm the tests fail because Packet 5C remains deferred.
3. Implement only the minimal read-only Packet 5C behavior in
   `rytm_randomizer/behavior_pad1_lane.py`.
4. Preserve Packet 5A `BR`/`BM` behavior exactly.
5. Preserve Packet 5B `FT`/`FK`/`FG`/`FZ` behavior exactly.
6. Run the targeted behavior test.
7. Run the full closeout suite.
8. Confirm V1.34 reference diff is empty.
9. Confirm package metadata diff is empty.
10. Confirm git status is clean after commit.

## 8. Deferred And Rejected Scope

Still deferred from Packet 5:

- BD Silky load/discovery/anchor-return intent:
  - `BI`
  - `ST`
  - `SK`
  - `SC`
  - `SBH`
- Pad 1 BD Acoustic anchor/profile behavior:
  - `BA`

Still rejected for the next tiny implementation slice:

- BD Plastic anchor/load execution
- BD Plastic discovery execution
- BD Plastic anchor-return execution
- runtime engine rotation
- runtime current-engine mutation
- runtime discovery mutation
- runtime anchor load
- runtime anchor return
- Pad 1 selected-engine state
- Pad 1 lane mode state
- prompt/input loop behavior
- command dispatch
- command execution
- CLI execution wiring
- active CLI commands
- real MIDI
- `mido`
- `rtmidi`
- package metadata changes
- port discovery
- port opening
- MIDI sending
- hardware behavior
- hardware validation
- Analog Four
- Pads 5-12
- machine/profile expansion
- SysEx
- GUI/capture

## 9. Parallelization Decision

Do not parallelize the first Packet 5C implementation.

Reason:

- file ownership remains concentrated in the same helper module and test file
- Packet 5C must preserve Packet 5A `BR`/`BM` behavior exactly
- Packet 5C must preserve Packet 5B `FT`/`FK`/`FG`/`FZ` behavior exactly
- BD Plastic anchor/load, discovery, and return vocabulary should stabilize
  before BD Silky or Pad 1 BD Acoustic sub-slices are split out

Parallel implementation can be reconsidered after Packet 5C lands and future
Packet 5D/5E scopes are separately planned with disjoint ownership.

## 10. Safe Next Options

Safe next options:

- implement only the tiny Packet 5C read-only `BP`/`PT`/`PK`/`PX`/`PBH`
  behavior slice with TDD
- write a user-facing progress/timeline update
- pause at this accepted planning checkpoint

## 11. Recommendation

Proceed next with the tiny Packet 5C implementation:

- `rytm_randomizer/behavior_pad1_lane.py`
- `tests/test_behavior_pad1_lane.py`

Keep BD Silky, Pad 1 BD Acoustic, runtime mutation, MIDI, ports, active
behavior, package metadata, and hardware behavior deferred.

## 12. Decision

Packet 5C plan accepted.

The next implementation target should be Packet 5C: read-only Pad 1 BD Plastic
lane intent behavior for `BP`, `PT`, `PK`, `PX`, and `PBH`.

No implementation is added by this review.

## 13. Implementation Follow-Up

Packet 5C read-only Pad 1 BD Plastic lane behavior was implemented in:

- `2067d43 Add Packet 5C BD Plastic lane behavior`

The implementation checkpoint is:

- `Docs/V134_BEHAVIOR_PARITY_PACKET_5C_BD_PLASTIC_LANE_BEHAVIOR_CHECKPOINT.md`

The implementation keeps BD Silky, Pad 1 BD Acoustic, runtime mutation,
dispatch, MIDI, ports, package metadata, active behavior, and hardware
behavior deferred.
