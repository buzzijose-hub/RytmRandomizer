# V1.34 Behavior Parity Packet 5B BD FM Lane Behavior Plan Review

## 1. Purpose

Review and accept the Packet 5B BD FM lane behavior plan.

This is a documentation-only review checkpoint. It adds no implementation,
tests, CLI wiring, dispatch, MIDI, port opening, package metadata, active
behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this slice:

- `322fd38 Add Packet 5B BD FM lane behavior plan`

Current phase:

- Passive/Mock Foundation Phase
- Packet 1 complete and accepted
- Packet 2 accepted as meaningful anchor/profile progress
- Packet 3 complete and accepted
- Packet 4 complete and accepted
- Packet 5A complete and accepted
- Packet 5B BD FM lane behavior plan created
- Packet 5B BD FM lane behavior plan now reviewed and accepted

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Review Decision

Accepted plan document:

- `Docs/V134_BEHAVIOR_PARITY_PACKET_5B_BD_FM_LANE_BEHAVIOR_PLAN.md`

Accepted plan milestone:

- `322fd38 Add Packet 5B BD FM lane behavior plan`

Accepted packet identity:

- Packet 5B: Pad 1 BD FM Lane Behavior Parity

Decision:

- Packet 5B plan accepted.
- The next implementation target is a tiny read-only `FT`/`FK`/`FG`/`FZ`
  intent behavior slice.
- This review does not implement or authorize execution behavior by itself.
- Hardware remains off.

## 4. Accepted Packet 5B Scope

Accepted future implementation scope:

- `FT`: BD FM tone/FM discovery
- `FK`: BD FM kick/body discovery
- `FG`: BD FM grit discovery
- `FZ`: return Pad 1 BD FM to anchor

Already-covered context remains outside Packet 5B implementation:

- `FM`: show BD FM menu/status, covered by Packet 1
- `BF`: load Pad 1 BD FM profiled anchor, covered by Packet 2

Packet 5B may reference `FM` and `BF` as context, but must not reimplement or
change their existing behavior.

## 5. Accepted Packet 5B Semantics

Accepted future `FT`, `FK`, and `FG` semantics:

- read-only BD FM discovery intent
- target pad `1`
- lane `Pad 1 BD FM`
- copied metadata from `PAD1_COMMANDS`
- BD FM engine/profile dependency recorded only
- future discovery depth dependency recorded only
- no prompt loop
- no state mutation
- no dispatch
- no command execution
- no MIDI
- no port opening
- no hardware requirement

Accepted future `FZ` semantics:

- read-only BD FM anchor-return intent
- target pad `1`
- lane `Pad 1 BD FM`
- copied metadata from `PAD1_COMMANDS`
- BD FM anchor dependency recorded only
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

1. Extend `tests/test_behavior_pad1_lane.py` with failing tests for
   `FT`, `FK`, `FG`, and `FZ`.
2. Confirm the tests fail because Packet 5B remains deferred.
3. Implement only the minimal read-only Packet 5B behavior in
   `rytm_randomizer/behavior_pad1_lane.py`.
4. Run the targeted behavior test.
5. Run the full closeout suite.
6. Confirm V1.34 reference diff is empty.
7. Confirm package metadata diff is empty.
8. Confirm git status is clean after commit.

## 8. Deferred And Rejected Scope

Still deferred from Packet 5:

- BD Plastic load/discovery/anchor-return intent:
  - `BP`
  - `PT`
  - `PK`
  - `PX`
  - `PBH`
- BD Silky load/discovery/anchor-return intent:
  - `BI`
  - `ST`
  - `SK`
  - `SC`
  - `SBH`
- Pad 1 BD Acoustic anchor/profile behavior:
  - `BA`

Still rejected for the next tiny implementation slice:

- runtime engine rotation
- runtime current-engine mutation
- runtime discovery mutation
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

Do not parallelize the first Packet 5B implementation.

Reason:

- file ownership remains concentrated in the same helper module and test file
- Packet 5B must preserve Packet 5A `BR`/`BM` behavior exactly
- BD FM discovery/return vocabulary should stabilize before BD Plastic or BD
  Silky sub-slices are split out

Parallel implementation can be reconsidered after Packet 5B lands and future
Packet 5C/5D scopes are separately planned with disjoint ownership.

## 10. Safe Next Options

Safe next options:

- implement only the tiny Packet 5B read-only `FT`/`FK`/`FG`/`FZ` behavior
  slice with TDD
- write a user-facing progress/timeline update
- pause at this accepted planning checkpoint

## 11. Recommendation

Proceed next with the tiny Packet 5B implementation:

- `rytm_randomizer/behavior_pad1_lane.py`
- `tests/test_behavior_pad1_lane.py`

Keep BD Plastic, BD Silky, Pad 1 BD Acoustic, runtime mutation, MIDI, ports,
active behavior, package metadata, and hardware behavior deferred.

## 12. Decision

Packet 5B plan accepted.

The next implementation target should be Packet 5B: read-only Pad 1 BD FM lane
intent behavior for `FT`, `FK`, `FG`, and `FZ`.

No implementation is added by this review.
