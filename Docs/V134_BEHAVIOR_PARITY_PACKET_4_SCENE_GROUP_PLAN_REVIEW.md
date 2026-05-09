# V1.34 Behavior Parity Packet 4 Scene And Group Intent Plan Review

## 1. Purpose

Review and accept the Packet 4 scene and group intent plan as the current
planning gate.

This review is documentation-only. It does not implement tests, runtime
behavior, CLI wiring, dispatch, scene execution, group mutation execution,
MIDI, port opening, package metadata, active CLI behavior, or hardware
behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `9ad10d2 Add Packet 4 scene group behavior plan`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity matrix documented and reviewed
- Packet 1 complete and accepted
- Packet 2 accepted as meaningful read-only anchor/profile progress
- Packet 3 complete and accepted
- broader behavior-parity progress report after Packet 3 accepted
- Packet 4 scene and group intent plan now being reviewed and accepted

Hardware status:

- Analog Rytm MKII off.
- Analog Four MKII off.
- Hardware not required.

## 3. Review Decision

Accepted plan:

- `Docs/V134_BEHAVIOR_PARITY_PACKET_4_SCENE_GROUP_PLAN.md`

Accepted planning milestone:

- `9ad10d2 Add Packet 4 scene group behavior plan`

Accepted Packet 4 identity:

- Packet 4: Scene And Group Intent Behavior Parity

Accepted first future implementation scope:

- Packet 4A: read-only scene intent behavior only

Accepted future implementation scene keys:

- `S0`
- `S1`
- `S1A`
- `S1B`
- `S2`
- `S2A`
- `S2B`
- `S3`
- `S3A`
- `S3B`
- `S4`
- `S4A`
- `S4B`
- `S5`

## 4. Accepted Future Packet 4A Behavior

Packet 4A may model deterministic read-only scene intent behavior for the
accepted scene keys.

Accepted behavior family:

- `scene-group/scene-intent`

Accepted result intent:

- identify scene command metadata
- copy scene name, description, action, and scope metadata
- mark the result as read-only and intent-only
- record that scene execution is unavailable
- record that no runtime state changes
- record that no MIDI, ports, dispatch, active CLI behavior, or hardware is
  involved

Packet 4A must not execute scenes, load anchors, mutate group pads, dispatch
commands, run a prompt loop, or touch hardware.

## 5. Accepted Deferred Packet 4 Scope

Deferred group mutation keys:

- `X`
- `D`
- `I`
- `4`

Deferred lane-aware group mutation keys:

- `Y`
- `V`
- `N`

Deferred concepts:

- group mutation execution
- lane-aware group mutation execution
- scene selection runtime state
- four-pad group runtime state
- four-pad anchor/profile runtime state
- lane model
- command dispatch
- scene execution
- MIDI or hardware behavior

These remain future behavior gaps and require a separate plan and review
before implementation.

## 6. Accepted Future File Ownership

Accepted future implementation files:

- `rytm_randomizer/behavior_scene_group.py`
- `tests/test_behavior_scene_group.py`
- `Scripts/closeout_check.ps1`, only to add the future test label

Files that remain out of scope for Packet 4A:

- `rytm_hybrid_randomizer_v134.py`
- `rytm_randomizer/cli.py`
- `rytm_randomizer/mock_midi.py`
- `rytm_randomizer/mock_message_mapper.py`
- `rytm_randomizer/mock_mapper_report.py`
- `rytm_randomizer/real_midi_adapter.py`
- package metadata files
- active CLI command files or paths
- runtime execution/dispatch/MIDI logic outside the accepted packet files

## 7. Accepted Future Tests

Accepted future Packet 4A tests should verify:

- importing the new module prints nothing
- supported scene keys return deterministic read-only behavior results
- `S0` returns home/clean scene intent without anchor loading
- `S1A` returns Rolling Light scene intent without scene execution
- `S4B` returns Wild Maximum scene intent while remaining forbidden for early
  hardware scope
- `S5` returns Back to Clean scene intent without anchor loading
- all scene results include copied scene metadata
- repeated scene evaluations are deterministic
- unknown keys fail safely
- `X`, `D`, `I`, `4`, `Y`, `V`, and `N` remain deferred or fail safely until
  separately approved
- Packet 1 behavior remains unchanged
- Packet 2 behavior remains unchanged
- Packet 3 behavior remains unchanged
- passive CLI behavior remains unchanged
- no real MIDI library is imported
- no ports are opened
- no MIDI is sent
- no active CLI command is added
- V1.34 reference remains untouched
- package metadata files remain absent unless separately approved
- no Analog Four or Pads 5-12 support is exposed

## 8. Accepted Future TDD Flow

Future Packet 4A implementation should:

1. Add failing scene-intent tests in `tests/test_behavior_scene_group.py`.
2. Verify the new tests fail for the expected missing behavior.
3. Implement the smallest read-only scene-intent helper.
4. Verify the new tests pass.
5. Run targeted behavior tests for Packet 1, Packet 2, Packet 3, and Packet
   4A.
6. Run full closeout:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
   ```

## 9. Parallelization Decision

Do not parallelize Packet 4A implementation.

Accepted reason:

- implementation ownership is concentrated in one new helper module and one
  test file
- scene intent result vocabulary should stabilize before group mutation
  behavior is planned
- group mutation and lane-aware group mutation remain deferred
- the implementation is small enough for one focused TDD pass

Parallel implementation can be reconsidered after Packet 4A lands cleanly and
Packet 4B or later scope is separately planned.

## 10. Rejected Scope

Packet 4A does not authorize:

- group mutation behavior
- lane-aware group mutation behavior
- scene execution
- anchor loading
- command dispatch
- command execution
- CLI execution wiring
- prompt/input loop
- runtime state mutation
- real MIDI
- port opening
- hardware behavior
- package metadata

## 11. Confirmed Absent Behavior

This review adds no:

- implementation
- tests
- scene execution
- group mutation execution
- lane-aware group mutation execution
- command dispatch
- command execution
- CLI execution wiring
- prompt/input loop
- runtime state mutation
- real MIDI dependency
- `mido`
- `rtmidi`
- package metadata
- port discovery
- port opening
- MIDI sending
- active CLI command
- `execute-command`
- `send-command`
- `hardware-test`
- hardware behavior
- hardware validation
- machine/profile expansion
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture

`rytm_hybrid_randomizer_v134.py` remains untouched.

## 12. Next Safe Options

Safe next options:

- implement only the accepted Packet 4A read-only scene intent behavior
- write a more user-facing progress/timeline update
- pause at this clean Packet 4 planning review checkpoint

## 13. Recommendation

Implement only Packet 4A as a tiny read-only scene intent behavior slice.

Do not add group mutation behavior, lane-aware group mutation behavior, scene
execution, dispatch, CLI execution wiring, real MIDI, ports, package metadata,
active CLI behavior, or hardware behavior.

## 14. Decision

The Packet 4 scene and group intent plan is accepted.

The next implementation scope is limited to read-only scene intent behavior
for:

- `S0`
- `S1`
- `S1A`
- `S1B`
- `S2`
- `S2A`
- `S2B`
- `S3`
- `S3A`
- `S3B`
- `S4`
- `S4A`
- `S4B`
- `S5`

Group mutation and lane-aware group mutation remain deferred.

Hardware remains off.
