# V1.34 Behavior Parity Packet 3B Legacy Mutation-Depth Plan Review

## Purpose

Review and accept the Packet 3B legacy mutation-depth plan.

Confirm this is a documentation-only review checkpoint. It does not implement
behavior, add tests, wire the CLI, dispatch commands, execute commands, open
ports, send MIDI, add package metadata, mutate state, or require hardware.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this documentation slice:

- 8ef8c8b Add Packet 3B legacy mutation depth plan

Current phase:

- Passive/Mock Foundation Phase
- Packet 1 complete for the current intent-only behavior phase
- Packet 2 accepted as meaningful read-only anchor/profile progress
- Packet 3A guarded numeric input behavior accepted
- Packet 3B legacy mutation-depth plan created
- Packet 3B legacy mutation-depth plan now reviewed

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Review Decision

Accepted plan:

- `Docs/V134_BEHAVIOR_PARITY_PACKET_3B_LEGACY_MUTATION_DEPTH_PLAN.md`

Accepted plan commit:

- 8ef8c8b Add Packet 3B legacy mutation depth plan

The Packet 3B plan is accepted as the current planning gate for the next tiny
mutation-depth behavior implementation slice.

This review does not authorize the rest of Packet 3. It only accepts the
future `M1`, `M2`, and `M3` implementation scope.

## Accepted Future Scope

Accepted future Packet 3B implementation keys:

- `M1`
- `M2`
- `M3`

Accepted future behavior:

- `M1`: deterministic read-only legacy single-profile full micro mutation
  intent
- `M2`: deterministic read-only legacy single-profile full groove mutation
  intent
- `M3`: deterministic read-only legacy single-profile full strong mutation
  intent

Accepted passive metadata source:

- `LEGACY_SINGLE_PROFILE_MUTATION_COMMANDS` in `rytm_randomizer/commands.py`

Accepted metadata semantics:

- use existing command labels
- use existing mutation area `full`
- use existing fixed mutation depths `micro`, `groove`, and `strong`
- record selected-profile dependency only
- do not invent selected-profile state
- do not invent runtime mutation output
- do not invent machine values
- do not invent pad state
- do not invent hardware state

## Accepted Future File Ownership

Future implementation ownership is limited to:

- `rytm_randomizer/behavior_mutation_depth.py`
- `tests/test_behavior_mutation_depth.py`

No closeout script update is expected because the test file is already covered
by:

- `=== Test: Behavior Mutation Depth ===`

## Accepted Existing Behavior Stability

Future Packet 3B implementation must preserve:

- existing Packet 3A behavior for guarded numeric inputs `1`, `2`, and `3`
- unknown-key safe failure
- unsupported non-Packet-3 command safe failure
- remaining deferred Packet 3 key safe failure
- Packet 1 menu/utility behavior stability
- Packet 2 anchor/profile behavior stability
- passive CLI behavior stability

## Accepted Deferred Scope

These Packet 3 areas remain deferred and unsafe to implement without a
separate plan:

- `S`
- `F`
- `A`
- `G`
- `K`
- `PM`
- `PS`
- `PF`
- `PA`
- `PL`
- `PO`
- `PB`
- `PG`
- prompt/depth context model
- selected-profile state model
- selected-isolated-pad state model
- runtime mutation result model
- mutation execution
- command dispatch
- CLI execution wiring

## Accepted Safety Boundaries

Packet 3B future work must remain:

- read-only
- deterministic
- intent-only
- metadata-driven
- side-effect free on import
- separate from CLI execution
- separate from runtime dispatch
- separate from real MIDI
- separate from hardware

Packet 3B future work must not add:

- prompt loops
- blocking input
- runtime state mutation
- selected-profile state mutation
- mutation execution
- command dispatch
- scene execution
- CLI wiring
- active CLI commands
- `execute-command`
- `send-command`
- `hardware-test`
- real MIDI imports
- `mido`
- `rtmidi`
- package metadata
- port discovery
- port opening
- MIDI sending
- hardware behavior
- hardware validation
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture

## Accepted Future Test Expectations

Future Packet 3B tests should verify:

- importing `rytm_randomizer.behavior_mutation_depth` prints nothing
- `M1`, `M2`, and `M3` return accepted read-only results
- `M1` records mutation depth `micro`
- `M2` records mutation depth `groove`
- `M3` records mutation depth `strong`
- all three record mutation area `full`
- all three record selected-profile scope/dependency only
- all three avoid prompt, state mutation, dispatch, execution, MIDI, ports,
  and hardware
- existing `1`, `2`, and `3` behavior remains unchanged
- remaining Packet 3 keys still fail safely
- unknown keys still fail safely
- passive CLI behavior remains unchanged
- V1.34 reference remains untouched
- package metadata files remain absent
- no Analog Four or Pads 5-12 scope appears

## Parallelization Decision

Parallel implementation remains not recommended for Packet 3B.

Reason:

- future write ownership is one behavior helper and one test file
- result-shape changes need tight coordination
- Packet 3A behavior must remain stable
- parallel workers would add coordination overhead without meaningful speedup

## Confirmed Absent Behavior

This review adds no:

- implementation
- tests
- CLI wiring
- command dispatch
- command execution
- scene execution
- prompt/input loop
- selected-profile state
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
- hardware behavior
- hardware validation
- machine/profile expansion
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture

`rytm_hybrid_randomizer_v134.py` remains untouched.

## Next Safe Options

- implement the tiny Packet 3B scope for `M1`, `M2`, and `M3`
- create a broader Packet 3 progress checkpoint
- pause at this clean Packet 3B planning review checkpoint

## Recommendation

Implement only the tiny Packet 3B scope next:

- `M1`
- `M2`
- `M3`

Do not implement the rest of Packet 3 yet.

## Decision

The Packet 3B legacy mutation-depth plan is accepted. Hardware remains off.
No real MIDI, ports, active CLI behavior, dispatch, execution, package
metadata, machine/profile expansion, or hardware validation exists.
