# V1.34 Behavior Parity Packet 4C Lane-Aware Group Mutation Plan

## 1. Purpose

Define the next tiny behavior-parity implementation plan after the accepted
Packet 4 progress review after Packet 4B.

Packet 4C should model lane-aware four-pad group mutation intent for `Y`,
`V`, and `N` as deterministic read-only metadata only. This plan does not
implement lane-aware group mutation behavior, tests, CLI wiring, dispatch,
runtime state mutation, MIDI, port opening, package metadata, active CLI
behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `baebeab Add Packet 4 progress review after 4B`

Current phase:

- Passive/Mock Foundation Phase
- Packet 1 complete for the current intent-only behavior phase
- Packet 2 accepted as meaningful read-only anchor/profile progress
- Packet 3 complete for mutation-depth and guarded input intent
- Packet 4A scene intent behavior accepted
- Packet 4B group mutation intent behavior accepted
- Packet 4 progress review after 4B accepted
- Packet 4C lane-aware group mutation planning now beginning

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Packet Identity

Packet name:

- Packet 4C: Lane-Aware Group Mutation Intent Behavior Parity

Packet intent:

- model lane-aware four-pad group mutation commands as deterministic read-only
  behavior metadata
- preserve existing Packet 4A scene intent behavior
- preserve existing Packet 4B group mutation intent behavior
- keep group anchor load/return behavior deferred
- keep lane-aware mutation behavior separate from execution
- avoid real MIDI, ports, active CLI behavior, package metadata, and hardware

## 4. Accepted Sources

This packet plan is based on:

- `Docs/V134_BEHAVIOR_PARITY_PACKET_4_PROGRESS_REVIEW_AFTER_4B.md`
- `Docs/V134_BEHAVIOR_PARITY_PACKET_4_PROGRESS_CHECKPOINT_AFTER_4B.md`
- `Docs/V134_BEHAVIOR_PARITY_PACKET_4B_GROUP_MUTATION_REVIEW.md`
- `Docs/V134_BEHAVIOR_PARITY_PACKET_4_SCENE_GROUP_PLAN_REVIEW.md`
- group command metadata in `rytm_randomizer/commands.py`
- current helper surface in `rytm_randomizer/behavior_scene_group.py`
- current tests in `tests/test_behavior_scene_group.py`
- protected V1.34 reference as the future behavior source, not edited

## 5. Planned Packet 4C Scope

Packet 4C should support read-only lane-aware group mutation intent for:

- `Y`: lane-aware SRC/morph mutation on all 4 group pads
- `V`: lane-aware filter mutation on all 4 group pads
- `N`: lane-aware grit mutation on all 4 group pads

These keys are already captured in `GROUP_COMMANDS` with:

- `type`: `mutation`
- `scope`: `four_pad_group`
- `command_family`: `lane_aware_page`
- `executable`: `False`
- `v134_reference_command`: `True`
- `scaffold_only`: `True`

Packet 4C should not widen beyond these three keys.

## 6. Explicit Deferred Scope

Packet 4C must not include group anchor load or return behavior:

- `O`: load full 4-pad group anchors
- `Z`: return all 4 group pads to anchors

Packet 4C must not include:

- scene execution
- group mutation execution
- lane-aware group mutation execution
- runtime lane state
- runtime group state
- prompt/input loop
- command dispatch
- MIDI or hardware behavior

`O` and `Z` require separate review because they imply anchor loading or
broader group state semantics.

## 7. Future File Ownership

The future Packet 4C implementation should keep the write set narrow.

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
- `Scripts/closeout_check.ps1`
- package metadata files
- runtime execution, dispatch, MIDI, or active CLI paths

## 8. Proposed Future Behavior Shape

Future implementation may extend the existing `SceneGroupBehaviorResult`
instead of creating a new result type if that keeps the helper simple and
readable.

Planned helper surface:

- add `PACKET_4C_LANE_AWARE_GROUP_MUTATION_INTENT_KEYS = ("Y", "V", "N")`
- keep `PACKET_4A_SCENE_INTENT_KEYS`
- keep `PACKET_4B_GROUP_MUTATION_INTENT_KEYS`
- keep safe handling for unsupported group anchor keys `O` and `Z`
- keep `evaluate_scene_group_behavior(command_key)` as the public entry point

Planned read-only result values for accepted Packet 4C keys:

- `accepted`: `True`
- `behavior_family`: `scene-group/lane-aware-group-mutation-intent`
- `reason`: `supported_lane_aware_group_mutation_intent`
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
- `source_group_command_family`
- `source_v134_reference_command`
- `source_scaffold_only`
- `lane_aware_page`
- `lane_aware_mutation_mode`
- `executes_scene`: `False`
- `executes_group_mutation`: `False`
- `dispatches_command`: `False`
- `mock_only`: `True`
- `sends_real_midi`: `False`
- `opens_ports`: `False`
- `hardware_required`: `False`
- `active_behavior`: `False`
- `mutates_runtime_state`: `False`

Suggested deterministic page and mode vocabulary:

- `Y`: page `src_morph`, mode `lane_aware_src_morph`
- `V`: page `filter`, mode `lane_aware_filter`
- `N`: page `grit`, mode `lane_aware_grit`

Names are planning vocabulary only. Do not implement them in this slice.

## 9. Proposed Display Lines

Future display lines should remain passive and unambiguous, such as:

- `<key>: <label>`
- `Read-only lane-aware group mutation intent.`
- `Lane-aware page: <page>`
- `Group scope: four_pad_group`
- `No lane-aware group mutation would execute.`
- `No group mutation would execute.`
- `No scene would execute.`
- `No state would change.`
- `No command would dispatch.`
- `No MIDI would be sent.`
- `No ports would be opened.`

This is intent metadata only, not active execution authorization.

## 10. Safe Failure Expectations

The future Packet 4C implementation should fail safely for:

- unknown command keys
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
- no lane-aware group mutation execution
- no runtime state mutation
- no MIDI
- no port opening
- no CLI active behavior
- no hardware requirement

## 11. Required Future TDD Steps

Future implementation should use the existing behavior scene/group test file.

### Step 1: Write Failing Packet 4C Tests

Add tests to `tests/test_behavior_scene_group.py` for:

- `Y`, `V`, and `N` return accepted read-only lane-aware group mutation
  intent
- each accepted key has deterministic page and mode metadata
- each accepted key copies metadata from `GROUP_COMMANDS`
- each accepted key preserves `command_family` as `lane_aware_page`
- each accepted key keeps `executes_group_mutation` false
- each accepted key keeps `dispatches_command` false
- `O` and `Z` remain unsupported/deferred and safe
- Packet 4A scene keys remain unchanged
- Packet 4B group mutation keys remain unchanged
- Packet 1, Packet 2, Packet 3, and passive CLI behavior remain unchanged

Run:

```powershell
python .\tests\test_behavior_scene_group.py
```

Expected result before implementation:

- fail because `Y`, `V`, and `N` still return
  `deferred_lane_aware_group_mutation_command`

### Step 2: Implement Minimal Read-Only Packet 4C Behavior

Update `rytm_randomizer/behavior_scene_group.py` only.

Expected minimal implementation shape:

- introduce `PACKET_4C_LANE_AWARE_GROUP_MUTATION_INTENT_KEYS`
- add a deterministic lane-aware details mapping for `Y`, `V`, and `N`
- route those keys before the safe deferred/unsupported branches
- copy metadata from `GROUP_COMMANDS`
- set all execution, dispatch, MIDI, port, runtime mutation, active behavior,
  and hardware flags to false
- keep `O` and `Z` unsupported/deferred and safe

### Step 3: Run Packet 4C Tests

Run:

```powershell
python .\tests\test_behavior_scene_group.py
```

Expected result after implementation:

- pass

### Step 4: Run Targeted Regression Tests

Run:

```powershell
python .\tests\test_behavior_menu_utility.py
python .\tests\test_behavior_anchor_profile.py
python .\tests\test_behavior_mutation_depth.py
python .\tests\test_cli.py
python .\tests\test_behavior_scene_group.py
```

Expected result:

- all targeted behavior and passive CLI tests pass

### Step 5: Run Full Closeout

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
- git status only shows intended Packet 4C implementation files before commit

## 12. Parallelization Recommendation

Do not parallelize the future Packet 4C implementation.

Reason:

- the future write set is tiny
- `rytm_randomizer/behavior_scene_group.py` and
  `tests/test_behavior_scene_group.py` are shared with Packet 4A and Packet 4B
- result vocabulary and routing order must remain consistent
- one focused TDD pass is safer than splitting this slice across agents

## 13. Confirmed Non-Goals

Packet 4C does not include:

- implementation in this documentation slice
- tests in this documentation slice
- scene execution
- group mutation execution
- lane-aware group mutation execution
- group anchor load/return behavior
- runtime scene state
- runtime group state
- runtime lane state
- command dispatch
- CLI execution wiring
- real MIDI dependency
- `mido`
- `rtmidi`
- package metadata
- MIDI port opening
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

## 14. Next Safe Options

Safe next options:

- review and accept this Packet 4C lane-aware group mutation plan
- write a more user-facing progress/timeline update
- pause at this clean Packet 4C planning checkpoint

## 15. Recommendation

Review and accept this Packet 4C plan next.

After acceptance, implement Packet 4C only if the future slice stays limited
to read-only lane-aware group mutation intent for `Y`, `V`, and `N`.

Do not add runtime execution, dispatch, MIDI, ports, package metadata, active
behavior, or hardware behavior.

## 16. Decision

Packet 4C is planned as the next tiny read-only behavior-parity implementation
scope.

The future implementation scope is limited to `Y`, `V`, and `N`.

`O` and `Z` remain deferred and safe.

Hardware remains off.
