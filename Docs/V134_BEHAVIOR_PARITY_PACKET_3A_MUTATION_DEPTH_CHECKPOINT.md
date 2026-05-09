# V1.34 Behavior Parity Packet 3A Mutation-Depth Checkpoint

## Purpose

Record completion of the Packet 3A mutation-depth and guarded numeric input
behavior implementation.

Packet 3A adds deterministic read-only intent behavior for:

- `1`
- `2`
- `3`

It does not add CLI wiring, command dispatch, command execution, scene
execution, prompt/input loops, selected-profile state, selected-pad state,
runtime state mutation, real MIDI, port opening, package metadata, active CLI
behavior, machine/profile expansion, hardware behavior, or hardware
validation.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this documentation slice:

- bda0db9 Add Packet 3A mutation depth behavior

Current phase:

- Passive/Mock Foundation Phase
- Packet 1 complete for the current intent-only behavior phase
- Packet 2 accepted as meaningful read-only anchor/profile progress
- Packet 3 mutation-depth and guarded input plan accepted
- Packet 3A mutation-depth behavior implemented
- Packet 3A checkpoint now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Milestone Commit

- bda0db9 Add Packet 3A mutation depth behavior

## Files Changed By The Milestone

- `rytm_randomizer/behavior_mutation_depth.py`
- `tests/test_behavior_mutation_depth.py`
- `Scripts/closeout_check.ps1`

Closeout now includes:

- `=== Test: Behavior Mutation Depth ===`

## Behavior Added

Packet 3A adds:

- `PACKET_3A_GUARDED_DEPTH_KEYS`
- `DEFERRED_PACKET_3_MUTATION_DEPTH_KEYS`
- `MutationDepthBehaviorResult`
- `evaluate_mutation_depth_behavior(command_key)`

Supported read-only Packet 3A guarded numeric input keys:

- `1`
- `2`
- `3`

For each supported key, `evaluate_mutation_depth_behavior(command_key)` returns:

- behavior family: `mutation-depth/guarded-input`
- reason: `supported_guarded_depth_input`
- depth value matching the command key
- guarded input: `True`
- requires future depth prompt context: `True`
- prompt available: `False`
- no prompt execution
- no state mutation
- no command dispatch
- no command execution
- no scene execution
- no MIDI
- no ports
- no hardware
- no active behavior

The result metadata records:

- source: `MAIN_PROMPT_DEPTH_GUARDRAIL`
- source command type: `guarded_depth`
- depth prompt context from existing passive command metadata
- mock-only/read-only safety fields
- no runtime state mutation

## Guarded Numeric Input Semantics

Packet 3A preserves the V1.34 safety rule that bare main-prompt `1`, `2`, and
`3` are recognized depth inputs but are not standalone execution commands.

The behavior helper records that these inputs are valid only inside a future
depth prompt context. No active depth prompt exists now.

## Deferred Scope Preserved

Packet 3A keeps these areas deferred:

- `M1`, `M2`, and `M3` legacy single-profile fixed-depth mutation intent
- `S`, `F`, `A`, `G`, and `K` current-profile page mutation intent
- `PM` selected isolated pad group default zone/depth mutation intent
- `PS`, `PF`, `PA`, `PL`, `PO`, `PB`, and `PG` selected isolated pad
  depth-choice mutation intent
- prompt/depth context model
- selected-profile state model
- selected-isolated-pad state model
- runtime mutation result model

Deferred Packet 3 mutation keys fail safely with a deterministic
`deferred_mutation_depth_command` result.

Unknown keys fail safely with a deterministic `unknown_command` result.

## Test And Closeout Coverage

New test coverage was added in:

- `tests/test_behavior_mutation_depth.py`

Closeout now includes:

- `=== Test: Behavior Mutation Depth ===`

The tests verify:

- importing the module prints nothing
- `1`, `2`, and `3` return deterministic guarded numeric input results
- each result records the expected depth value
- each result records that bare main-prompt use is guarded
- each result records that no depth prompt context exists now
- each result exposes no state mutation, prompt loop, dispatch, execution,
  ports, MIDI, hardware, or active behavior
- repeated evaluations are deterministic
- metadata is copied and immutable
- unknown keys fail safely
- deferred Packet 3 mutation keys remain unsupported/safe
- Packet 1 menu/utility behavior remains unchanged
- Packet 2 anchor/profile behavior remains unchanged
- passive CLI behavior remains unchanged
- no real MIDI library is imported
- no package metadata files are introduced
- no active command names are exposed
- no Analog Four or Pads 5-12 scope is exposed

TDD evidence:

- new Packet 3A tests were written first
- targeted test failed before implementation because
  `rytm_randomizer.behavior_mutation_depth` did not exist
- targeted test passed after the minimal implementation
- full closeout passed after implementation

## Safety Boundary

Packet 3A adds no:

- CLI wiring
- command dispatch
- command execution
- scene execution
- prompt/input loop
- selected-profile state
- selected-isolated-pad state
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
- profile `"4"` implementation
- machine/profile universe expansion
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture

`rytm_hybrid_randomizer_v134.py` remains untouched.

## Current Limitations

- no CLI exposure of the behavior module
- no routing loop
- no active command execution
- no prompt/depth context model
- no selected-profile state model
- no selected-isolated-pad state model
- no mutation execution
- no legacy single-profile mutation behavior for `M1`, `M2`, or `M3`
- no current-profile page mutation behavior for `S`, `F`, `A`, `G`, or `K`
- no selected isolated pad mutation behavior for `PM`, `PS`, `PF`, `PA`,
  `PL`, `PO`, `PB`, or `PG`
- display text remains deterministic safety/intent text, not full V1.34 output

## Next Safe Options

- review and accept this Packet 3A checkpoint
- create a docs-only Packet 3B plan for `M1`, `M2`, and `M3` only
- create a broader Packet 3 progress checkpoint
- pause at this clean checkpoint

## Recommendation

Review and accept Packet 3A now.

Do not widen Packet 3 behavior until a separate Packet 3B plan is documented
and accepted.

## Decision

Packet 3A is complete. Hardware remains off. No real MIDI, ports, active CLI
behavior, dispatch, execution, package metadata, machine/profile expansion, or
hardware validation was added.
