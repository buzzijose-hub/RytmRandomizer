# V1.34 Behavior Parity Packet 3D Selected Isolated Pad Mutation Plan

## 1. Purpose

Define the next tiny behavior-parity implementation scope for Packet 3D:
selected isolated pad mutation-depth intent.

This is a documentation-only planning slice. It does not implement tests or
behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `1be4421 Add Packet 3 post-3C progress checkpoint`

Current phase:

- Packet 1 complete for the current intent-only behavior phase.
- Packet 2 accepted as meaningful read-only anchor/profile progress.
- Packet 3A guarded numeric input behavior accepted.
- Packet 3B legacy mutation-depth behavior accepted.
- Packet 3C current-profile mutation-depth behavior accepted.
- Packet 3D selected isolated pad mutation-depth behavior is now being planned.

Hardware status:

- Analog Rytm MKII off.
- Analog Four MKII off.
- Hardware not required.

## 3. Packet 3D Scope

Packet 3D should cover selected isolated pad mutation intent for:

- `PM`
- `PS`
- `PF`
- `PA`
- `PL`
- `PO`
- `PB`
- `PG`

Planned command meanings:

- `PM`: mutate selected isolated pad only using its group default zone/depth
- `PS`: mutate selected isolated pad SRC only, choose depth
- `PF`: mutate selected isolated pad Filter only, choose depth
- `PA`: mutate selected isolated pad Amp only, choose depth
- `PL`: mutate selected isolated pad LFO only, choose depth
- `PO`: mutate selected isolated pad Morph only, choose depth
- `PB`: mutate selected isolated pad Body only, choose depth
- `PG`: mutate selected isolated pad Grit only, choose depth

Existing passive metadata source:

- `ISOLATED_PAD_MUTATION_COMMANDS` in `rytm_randomizer/commands.py`

## 4. Planned File Ownership

Future implementation ownership should be limited to:

- `rytm_randomizer/behavior_mutation_depth.py`
- `tests/test_behavior_mutation_depth.py`

No closeout script update is expected because:

- `tests/test_behavior_mutation_depth.py` is already covered by `=== Test: Behavior Mutation Depth ===`.

## 5. Planned Result Semantics

Future Packet 3D results should remain read-only intent descriptions.

Shared planned semantics:

- `accepted`: `True`
- `behavior_family`: `mutation-depth/selected-isolated-pad`
- `reason`: `supported_selected_isolated_pad_mutation_intent`
- `scope`: `selected_isolated_pad`
- `command_family`: `isolated_pad_mutation`
- selected-isolated-pad dependency recorded only
- no selected-isolated-pad state mutation
- no prompt loop
- no runtime mutation
- no dispatch
- no execution
- no MIDI
- no ports
- no hardware
- no active behavior

Planned `PM` semantics:

- `mutation_area`: `full`
- `uses_group_default_zone_depth`: `True`
- `requires_depth_prompt_context`: `False`
- `prompt_required`: `False`
- `prompt_available`: `False`

Planned `PS`, `PF`, `PA`, `PL`, `PO`, `PB`, and `PG` semantics:

- `requires_depth_prompt_context`: `True`
- `prompt_required`: `True`
- `prompt_available`: `False`
- future depth selection required

Planned mutation areas:

- `PS`: `src`
- `PF`: `filter`
- `PA`: `amp`
- `PL`: `lfo`
- `PO`: `morph`
- `PB`: `body`
- `PG`: `grit`

## 6. Planned Helper Shape

Future implementation may add:

- `PACKET_3D_SELECTED_ISOLATED_PAD_MUTATION_KEYS`
- `_accepted_selected_isolated_pad_mutation_result(command_key)`

Future `evaluate_mutation_depth_behavior(command_key)` routing should accept
Packet 3D keys after Packet 3C routing.

After Packet 3D implementation, the current known Packet 3 deferred key set
should become empty or otherwise explicitly indicate that no known Packet 3
mutation-depth keys remain deferred in the read-only behavior helper.

This must not remove safe failure behavior for:

- unknown keys
- unsupported non-Packet 3 command keys

## 7. Planned Display Contract

Future display lines should communicate:

- selected isolated pad mutation intent
- mutation area
- selected-isolated-pad dependency is recorded only
- no selected-isolated-pad state exists in the helper
- future depth selection requirement for `PS`, `PF`, `PA`, `PL`, `PO`, `PB`,
  and `PG`
- group default zone/depth usage for `PM`
- no active depth prompt
- no prompt would run
- no state would change
- no command would dispatch
- no command would execute
- no MIDI would be sent
- no ports would be opened

## 8. Planned Metadata Contract

Future metadata should include:

- `source`: `ISOLATED_PAD_MUTATION_COMMANDS`
- `source_command_type`: `mutation`
- `command_family`: `isolated_pad_mutation`
- `mutation_area`
- `scope`: `selected_isolated_pad`
- `mock_only`: `True`
- `sends_real_midi`: `False`
- `opens_ports`: `False`
- `hardware_required`: `False`
- `active_behavior`: `False`
- `mutates_runtime_state`: `False`

For `PM`, metadata should also include:

- `uses_group_default_zone_depth`: `True`

For `PS`, `PF`, `PA`, `PL`, `PO`, `PB`, and `PG`, metadata should also include:

- `requires_depth_selection`: `True`

## 9. Planned Tests

Future tests should extend `tests/test_behavior_mutation_depth.py`.

Planned test coverage:

- importing `rytm_randomizer.behavior_mutation_depth` still prints nothing.
- `PM`, `PS`, `PF`, `PA`, `PL`, `PO`, `PB`, and `PG` return accepted read-only
  results.
- each Packet 3D key has the expected label and mutation area.
- each Packet 3D key uses `selected_isolated_pad` scope.
- each Packet 3D key uses `isolated_pad_mutation` command family.
- `PM` records `uses_group_default_zone_depth`.
- `PS`, `PF`, `PA`, `PL`, `PO`, `PB`, and `PG` require future depth selection.
- active prompt remains unavailable.
- display output includes no prompt, state mutation, dispatch, execution,
  MIDI, or port behavior.
- repeated Packet 3D evaluations are deterministic.
- metadata remains immutable.
- Packet 3A behavior remains unchanged.
- Packet 3B behavior remains unchanged.
- Packet 3C behavior remains unchanged.
- unknown keys still fail safely.
- passive CLI behavior remains unchanged.
- V1.34 reference remains untouched.
- no real MIDI library is imported.
- no package metadata files are created.
- no active command names are exposed.
- no Analog Four support is exposed.
- no Pads 5-12 support is exposed.

## 10. Required TDD Flow

Future implementation should use a red/green flow:

1. Add failing Packet 3D tests in `tests/test_behavior_mutation_depth.py`.
2. Run:

   ```powershell
   python tests\test_behavior_mutation_depth.py
   ```

3. Confirm the new Packet 3D assertions fail while keys remain deferred.
4. Implement the minimal read-only Packet 3D behavior in
   `rytm_randomizer/behavior_mutation_depth.py`.
5. Run:

   ```powershell
   python tests\test_behavior_mutation_depth.py
   ```

6. Run full closeout:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
   ```

## 11. Parallelization Recommendation

Do not parallelize Packet 3D implementation.

Reason:

- ownership is concentrated in one behavior module and one test file
- the result shape must remain consistent with Packet 3A, Packet 3B, and
  Packet 3C
- the next implementation is small enough for one focused TDD pass

## 12. Deferred Scope

Packet 3D must not implement:

- selected isolated pad runtime state
- actual isolated pad mutation
- prompt/depth runtime
- command dispatch
- command execution
- CLI execution wiring
- real MIDI
- port opening
- hardware behavior

Broader runtime concepts remain deferred:

- selected-profile state model
- selected-isolated-pad state model
- runtime mutation result model
- mutation execution
- command dispatch
- CLI execution wiring

## 13. Confirmed Absent Behavior In This Slice

This planning slice adds no:

- implementation
- tests
- CLI wiring
- command dispatch
- command execution
- scene execution
- prompt/input loop
- selected isolated pad state mutation
- runtime state mutation
- mutation execution
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

## 14. Next Safe Options

Safe next options:

- review and accept this Packet 3D plan
- pause at this clean Packet 3D planning checkpoint
- implement only the accepted Packet 3D read-only behavior after review

## 15. Recommendation

Review and accept this Packet 3D plan next. If accepted, implement only the
tiny Packet 3D read-only selected isolated pad mutation-depth behavior in a
single focused TDD slice.

## 16. Decision

Packet 3D is planned, not implemented.

The future implementation scope is limited to read-only selected isolated pad
mutation-depth intent for:

- `PM`
- `PS`
- `PF`
- `PA`
- `PL`
- `PO`
- `PB`
- `PG`

Hardware remains off.
