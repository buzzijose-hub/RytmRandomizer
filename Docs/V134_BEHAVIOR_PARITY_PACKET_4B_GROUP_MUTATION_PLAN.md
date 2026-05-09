# V1.34 Behavior Parity Packet 4B Group Mutation Plan

## 1. Purpose

Define the next tiny behavior-parity implementation plan after the accepted
Packet 4 progress review.

Packet 4B should model four-pad group mutation intent for `X`, `D`, `I`, and
`4` as deterministic read-only metadata only. This plan does not implement
group mutation behavior, tests, CLI wiring, dispatch, runtime state mutation,
MIDI, port opening, package metadata, active CLI behavior, or hardware
behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `d9ec30d Add Packet 4 progress review`

Current phase:

- Passive/Mock Foundation Phase
- Packet 1 complete for the current intent-only behavior phase
- Packet 2 accepted as meaningful read-only anchor/profile progress
- Packet 3 complete for mutation-depth and guarded input intent
- Packet 4A scene intent behavior accepted
- Packet 4 progress review accepted
- Packet 4B group mutation planning now beginning

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Packet Identity

Packet name:

- Packet 4B: Group Mutation Intent Behavior Parity

Packet intent:

- model four-pad group mutation commands as deterministic read-only behavior
  metadata
- preserve the existing Packet 4A scene intent behavior
- keep lane-aware group mutation behavior deferred
- keep group mutation behavior separate from execution
- avoid real MIDI, ports, active CLI behavior, package metadata, and hardware

## 4. Accepted Sources

This packet plan is based on:

- `Docs/V134_BEHAVIOR_PARITY_PACKET_4_PROGRESS_REVIEW.md`
- `Docs/V134_BEHAVIOR_PARITY_PACKET_4_PROGRESS_CHECKPOINT.md`
- `Docs/V134_BEHAVIOR_PARITY_PACKET_4A_SCENE_INTENT_REVIEW.md`
- `Docs/V134_BEHAVIOR_PARITY_PACKET_4_SCENE_GROUP_PLAN_REVIEW.md`
- group command metadata in `rytm_randomizer/commands.py`
- current helper surface in `rytm_randomizer/behavior_scene_group.py`
- protected V1.34 reference as the future behavior source, not edited

## 5. Planned Packet 4B Scope

Packet 4B should support read-only group mutation intent for:

- `X`: balanced four-lane mutate full 4-pad group
- `D`: deeper four-lane mutation, Pads 2-4 pushed harder
- `I`: intense / controlled chaos four-lane mutation
- `4`: harder / wild four-lane mutation

The key `4` is a captured V1.34 group mutation command in `GROUP_COMMANDS`.
It must not change the existing guarded numeric input behavior for `1`, `2`,
and `3`.

## 6. Explicit Deferred Scope

Packet 4B must not include lane-aware group mutation intent:

- `Y`: lane-aware SRC/morph mutation on all 4 group pads
- `V`: lane-aware filter mutation on all 4 group pads
- `N`: lane-aware grit mutation on all 4 group pads

Packet 4B must not include group anchor load or return behavior:

- `O`: load full 4-pad group anchors
- `Z`: return all 4 group pads to anchors

These require separate review because they imply anchor loading or broader
group state semantics.

## 7. Future File Ownership

The future Packet 4B implementation should keep the write set narrow.

Allowed future implementation files:

- `rytm_randomizer/behavior_scene_group.py`
- `tests/test_behavior_scene_group.py`

Expected closeout behavior:

- no `Scripts/closeout_check.ps1` update should be needed because
  `tests/test_behavior_scene_group.py` is already covered by
  `=== Test: Behavior Scene Group ===`

Files that should remain untouched in the future implementation packet:

- `rytm_hybrid_randomizer_v134.py`
- `rytm_randomizer/cli.py`
- `rytm_randomizer/mock_midi.py`
- `rytm_randomizer/mock_message_mapper.py`
- `rytm_randomizer/mock_mapper_report.py`
- package metadata files
- runtime execution, dispatch, MIDI, or active CLI paths

## 8. Proposed Future Behavior Shape

Future implementation may extend the existing `SceneGroupBehaviorResult`
instead of creating a new result type if that keeps the helper simple and
readable.

Planned read-only result values for accepted Packet 4B keys:

- `accepted`: `True`
- `behavior_family`: `scene-group/group-mutation-intent`
- `reason`: `supported_group_mutation_intent`
- `scene_scope`: `four_pad_group`
- `state_changed`: `False`
- `prompt_required`: `False`
- `dispatches_command`: `False`
- `executes_scene`: `False`
- `executes_group_mutation`: `False`
- `sends_real_midi`: `False`
- `opens_ports`: `False`
- `hardware_required`: `False`
- `active_behavior`: `False`

Planned metadata should be copied from `GROUP_COMMANDS` and may include:

- `source`: `GROUP_COMMANDS`
- `source_group_command_label`
- `source_group_command_type`
- `source_group_command_scope`
- `source_v134_reference_command`
- `source_scaffold_only`
- `group_mutation_mode`
- `mutation_intensity`
- `executes_group_mutation`: `False`
- `dispatches_command`: `False`
- `mock_only`: `True`
- `sends_real_midi`: `False`
- `opens_ports`: `False`
- `hardware_required`: `False`
- `active_behavior`: `False`
- `mutates_runtime_state`: `False`

Suggested deterministic mode and intensity vocabulary:

- `X`: mode `balanced_four_lane`, intensity `balanced`
- `D`: mode `deeper_four_lane`, intensity `deeper`
- `I`: mode `intense_controlled_chaos`, intensity `intense`
- `4`: mode `harder_wild_four_lane`, intensity `wild`

Names are planning vocabulary only. Do not implement them in this slice.

## 9. Proposed Display Lines

Future display lines should remain passive and unambiguous, such as:

- `<key>: <label>`
- `Read-only group mutation intent.`
- `Group mutation mode: <mode>`
- `Group scope: four_pad_group`
- `No group mutation would execute.`
- `No scene would execute.`
- `No state would change.`
- `No command would dispatch.`
- `No MIDI would be sent.`
- `No ports would be opened.`

For `4`, the future result should also carry an early-hardware guardrail such
as:

- `Early hardware scope: forbidden.`

This is intent metadata only, not active execution authorization.

## 10. Safe Failure Expectations

The future Packet 4B implementation should fail safely for:

- unknown command keys
- lane-aware group mutation keys `Y`, `V`, and `N`
- group anchor keys `O` and `Z`
- unsupported group command metadata
- missing group command metadata

Safe failure means:

- deterministic result
- `accepted`: `False`
- no prompt loop
- no dispatch
- no scene execution
- no group mutation execution
- no runtime state mutation
- no MIDI
- no port opening
- no CLI active behavior
- no hardware requirement

## 11. Required Future TDD Steps

Future implementation should use the existing behavior scene/group test file.

### Step 1: Write Failing Packet 4B Tests

Add tests to `tests/test_behavior_scene_group.py` for:

- `X`, `D`, `I`, and `4` return accepted read-only group mutation intent
- each accepted key has deterministic mode and intensity metadata
- each accepted key copies metadata from `GROUP_COMMANDS`
- each accepted key keeps `executes_group_mutation` false
- `4` remains early hardware scope forbidden
- `Y`, `V`, and `N` remain deferred and safe
- `O` and `Z` remain unsupported/deferred and safe
- Packet 4A scene keys remain unchanged
- Packet 1, Packet 2, Packet 3, and passive CLI behavior remain unchanged

Run:

```powershell
python .\tests\test_behavior_scene_group.py
```

Expected red result:

- fails because `X`, `D`, `I`, and `4` are still
  `deferred_group_mutation_command`

### Step 2: Implement Minimal Packet 4B Behavior

Update `rytm_randomizer/behavior_scene_group.py` only.

Expected implementation shape:

- add Packet 4B accepted key constants
- add a tiny deterministic metadata table for mode and intensity
- add an accepted group mutation intent result builder
- keep Packet 4A scene behavior unchanged
- keep `Y`, `V`, and `N` deferred and safe
- keep `O` and `Z` unsupported/deferred and safe

### Step 3: Verify Targeted Tests

Run:

```powershell
python .\tests\test_behavior_scene_group.py
python .\tests\test_behavior_menu_utility.py
python .\tests\test_behavior_anchor_profile.py
python .\tests\test_behavior_mutation_depth.py
python .\tests\test_cli.py
```

Expected green result:

- all targeted tests pass

### Step 4: Run Full Closeout

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
git diff -- rytm_hybrid_randomizer_v134.py
git diff -- pyproject.toml requirements.txt setup.py setup.cfg
git status --short
```

Expected result:

- closeout passes
- V1.34 reference diff is empty
- package metadata diff is empty
- `git status --short` shows only intended files before commit

## 12. Required Future Tests

Future Packet 4B tests should verify:

- importing `rytm_randomizer.behavior_scene_group` prints nothing
- `X` returns balanced four-lane read-only group mutation intent
- `D` returns deeper four-lane read-only group mutation intent
- `I` returns intense / controlled chaos read-only group mutation intent
- `4` returns harder / wild read-only group mutation intent
- accepted group mutation results have scope `four_pad_group`
- accepted group mutation results copy metadata from `GROUP_COMMANDS`
- accepted group mutation results are deterministic across repeated calls
- accepted group mutation metadata is copied and immutable
- accepted group mutation results do not execute group mutation
- accepted group mutation results do not dispatch commands
- accepted group mutation results do not change runtime state
- accepted group mutation results do not send MIDI
- accepted group mutation results do not open ports
- `4` records early hardware scope forbidden
- `Y`, `V`, and `N` remain deferred and safe
- `O` and `Z` remain unsupported/deferred and safe
- unknown keys still fail safely
- Packet 4A scene behavior remains unchanged
- Packet 1, Packet 2, and Packet 3 behavior remain unchanged
- passive CLI behavior remains unchanged
- no real MIDI library is imported
- no ports are opened
- no MIDI is sent
- no active CLI command is added
- package metadata files remain absent
- V1.34 reference remains untouched
- no Analog Four or Pads 5-12 support is exposed

## 13. Parallelization Decision

Do not parallelize the future Packet 4B implementation.

Reason:

- `rytm_randomizer/behavior_scene_group.py` and
  `tests/test_behavior_scene_group.py` are the shared write set
- the result vocabulary should remain coherent with Packet 4A
- the implementation should be small enough for one focused TDD slice

Parallel work can be reconsidered later for independent documentation,
reporting, or separate behavior packets with disjoint files.

## 14. Non-Goals

Packet 4B planning does not include:

- implementation in this slice
- tests in this slice
- lane-aware group mutation behavior
- scene execution
- group mutation execution
- lane-aware group mutation execution
- group anchor loading or return behavior
- runtime scene state
- runtime group state
- runtime state mutation
- command dispatch
- prompt/input loop
- CLI execution wiring
- active CLI command
- real MIDI dependency
- `mido`
- `rtmidi`
- package metadata
- port discovery
- port opening
- MIDI sending
- hardware behavior
- hardware validation
- machine/profile expansion
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture

## 15. Stop Conditions

Stop and re-plan if future implementation would require:

- editing `rytm_hybrid_randomizer_v134.py`
- introducing package metadata
- importing a real MIDI library
- opening a port
- sending MIDI
- adding CLI execution wiring
- adding command dispatch
- adding runtime state mutation
- executing a scene or group mutation
- adding lane-aware group mutation behavior
- adding Analog Four or Pads 5-12 scope
- changing Packet 1, Packet 2, Packet 3, or Packet 4A behavior unexpectedly
- touching hardware

## 16. Next Recommended Task

Review and accept this Packet 4B group mutation plan.

If accepted, implement Packet 4B as a tiny TDD slice limited to read-only
group mutation intent for `X`, `D`, `I`, and `4`.

Hardware remains off.
