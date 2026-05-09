# V1.34 Behavior Parity Packet 3 Mutation-Depth And Guarded Input Plan

## Purpose

Define the next non-anchor behavior-parity implementation packet after the
accepted Packet 1 menu/utility baseline and accepted Packet 2 anchor/profile
progress baseline.

Packet 3 is planning-only in this slice. It does not add implementation,
tests, runtime behavior, CLI wiring, command dispatch, command execution,
scene execution, prompt/input loops, real MIDI, port opening, package metadata,
active CLI behavior, or hardware behavior.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 44d5558 Add behavior parity implementation progress review

Current phase:

- Passive/Mock Foundation Phase
- Packet 1 complete for the current intent-only behavior phase
- Packet 2 accepted as meaningful read-only anchor/profile progress
- broader behavior-parity implementation progress review accepted
- Packet 3 mutation-depth and guarded input planning now begins

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Accepted Planning Sources

This packet plan is grounded in:

- `Docs/V134_BEHAVIOR_PARITY_IMPLEMENTATION_PROGRESS_REVIEW.md`
- `Docs/V134_BEHAVIOR_PARITY_MATRIX_MUTATION_DEPTH_GUARDED_INPUT_SLICE.md`
- `Docs/V134_BEHAVIOR_PARITY_MATRIX_MUTATION_DEPTH_GUARDED_INPUT_SLICE_REVIEW.md`
- accepted passive command metadata in `rytm_randomizer/commands.py`
- protected V1.34 reference as behavior reference only

The protected V1.34 reference remains read-only and untouched.

## Packet Identity

Packet name:

- Packet 3: Mutation-Depth And Guarded Input Behavior Parity

Packet intent:

- model mutation-depth and guarded numeric-input intent as deterministic
  read-only behavior
- preserve V1.34's guard that bare main-prompt `1`, `2`, and `3` are not
  standalone execution commands
- represent future depth-dependent mutation commands without prompting,
  mutating state, dispatching, executing, or touching hardware
- keep all behavior helper output inert, deterministic, and inspection-only

## Full Accepted Packet 3 Planning Scope

The accepted matrix slice includes these command keys:

- `1`
- `2`
- `3`
- `M1`
- `M2`
- `M3`
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

Included behavior areas:

- guarded main-prompt numeric depth inputs
- legacy single-profile fixed-depth mutations
- current-profile page mutations that require a future depth selection
- selected isolated pad mutations that either use group default zone/depth or
  require a future depth selection

Not included in Packet 3:

- group mutation rows
- lane-aware group mutation rows
- Pad 1 BD lane discovery/mutation rows
- Pad 2 discovery/current-profile mutation rows
- Pad 3 discovery/current-mode mutation rows
- Pad 4 current-mode mutation rows
- scene execution rows
- anchor load/return rows already covered by Packet 2 progress
- undo/commit/state rows
- waveform exploration rows
- active execution
- real MIDI behavior
- hardware validation

## Recommended Packet 3A Implementation Scope

Recommended first implementation subset:

- `1`
- `2`
- `3`

Packet 3A should model only deterministic read-only guarded numeric input
behavior for bare main-prompt depth values.

Reasons for this tiny first scope:

- `1`, `2`, and `3` are the safest Packet 3 foundation because they must
  remain guarded at the main prompt
- they prove the behavior layer can represent "recognized but not executable"
  input
- they avoid mutation semantics, selected-profile state, selected-pad state,
  prompt loops, depth context, and hardware-facing parameter changes
- they protect a known V1.34 safety rule before modeling mutation commands
- the write set can remain limited to one new behavior module, one new test
  file, and one closeout label

## Deferred Packet 3 Scope

Defer these Packet 3 areas until Packet 3A is reviewed:

- `M1`, `M2`, and `M3` legacy single-profile fixed-depth mutation intent
- `S`, `F`, `A`, `G`, and `K` current-profile page mutation intent
- `PM` selected isolated pad group default zone/depth mutation intent
- `PS`, `PF`, `PA`, `PL`, `PO`, `PB`, and `PG` selected isolated pad
  depth-choice mutation intent
- any prompt/depth context model
- any selected-profile state model
- any selected-isolated-pad state model
- any runtime mutation result model

Each deferred area still requires a separate plan or review before
implementation.

## Proposed Future File Ownership

If Packet 3A is implemented later, accepted ownership should be:

- create `rytm_randomizer/behavior_mutation_depth.py`
- create `tests/test_behavior_mutation_depth.py`
- update `Scripts/closeout_check.ps1` only to add the new test file under:
  `=== Test: Behavior Mutation Depth ===`

Do not edit:

- `rytm_hybrid_randomizer_v134.py`
- `rytm_randomizer/cli.py`
- `rytm_randomizer/mock_midi.py`
- `rytm_randomizer/mock_message_mapper.py`
- `rytm_randomizer/mock_mapper_report.py`
- `rytm_randomizer/real_midi_adapter.py`
- package metadata files
- runtime execution or dispatch logic

## Expected Future Packet 3A Semantics

For `1`, `2`, and `3`:

- behavior family should be `mutation-depth/guarded-input`
- result should describe guarded numeric input intent only
- result should record the numeric depth value
- result should record that bare main-prompt use is guarded
- result should record that the input is only valid inside a future depth
  prompt context
- result should record no active depth prompt exists now
- no prompt should run
- no state should change
- no command should dispatch
- no command should execute
- no scene should execute
- no MIDI should be sent
- no ports should open
- no hardware should be required
- no active behavior should exist

Future result metadata should be copied/immutable enough that callers cannot
mutate source metadata.

## Expected Future Result Shape

Future implementation may define a result shape such as:

- `MutationDepthBehaviorResult`
- `evaluate_mutation_depth_behavior(command_key)`

Useful future result fields may include:

- `command_key`
- `supported`
- `behavior_family`
- `description`
- `depth_value`
- `guarded_input`
- `requires_depth_prompt_context`
- `prompt_available`
- `state_changed`
- `dispatches_command`
- `executes_command`
- `sends_midi`
- `opens_ports`
- `hardware_required`
- `active_behavior`
- `metadata`

These names are planning vocabulary only. They are not implementation in this
slice.

## Required Future Packet 3A Tests

Packet 3A tests should prove:

- importing `rytm_randomizer.behavior_mutation_depth` prints nothing
- `1`, `2`, and `3` return deterministic guarded numeric input results
- each result records the expected depth value
- each result records that bare main-prompt use is guarded
- each result records that no depth prompt context exists now
- each result exposes no state mutation, prompt loop, dispatch, execution,
  ports, MIDI, hardware, or active behavior
- repeated evaluations are deterministic
- returned metadata is copy-safe
- unknown keys fail safely
- deferred Packet 3 mutation keys remain unsupported/safe until separately
  implemented
- Packet 1 menu/utility behavior remains unchanged
- Packet 2 anchor/profile behavior remains unchanged
- passive CLI behavior remains unchanged
- no real MIDI library is imported
- no package metadata files are introduced
- V1.34 reference remains untouched
- no Pads 5-12 support is exposed
- no Analog Four support is exposed

## Future Packet 3B And Later Direction

After Packet 3A is implemented and reviewed, future Packet 3 widening can be
planned in small reviewed slices:

- Packet 3B: `M1`, `M2`, and `M3` fixed-depth legacy mutation intent
- Packet 3C: `S`, `F`, `A`, `G`, and `K` current-profile page mutation intent
- Packet 3D: `PM`, `PS`, `PF`, `PA`, `PL`, `PO`, `PB`, and `PG` selected
  isolated pad mutation intent

Those future packets should remain read-only behavior helpers unless a later
separate planning gate explicitly authorizes otherwise.

## Parallelization Decision

Do not parallelize the immediate Packet 3A implementation.

Reason:

- the first guarded-input result shape should be designed and stabilized in one
  module and one test file
- the write set is small
- the most important risk is semantic drift, not throughput

Parallel work can be reconsidered after Packet 3A is implemented, reviewed,
and accepted. Later Packet 3B/3C/3D planning may become independent enough for
parallel review or implementation, but only after the Packet 3A result shape is
stable.

## Work Not Authorized By This Plan

This plan does not authorize:

- implementation
- tests
- runtime behavior changes
- CLI wiring
- command dispatch
- command execution
- scene execution
- prompt/input loop execution
- selected profile state
- selected isolated pad state
- runtime state mutation
- mutation execution
- real MIDI dependency
- `mido`
- `rtmidi`
- package metadata changes
- MIDI port discovery
- MIDI port opening
- MIDI sending
- active CLI commands
- `execute-command`
- `send-command`
- `hardware-test`
- hardware behavior
- hardware validation
- profile `"4"` implementation
- machine/profile universe expansion
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture

## Stop Conditions For Future Implementation

Stop immediately if:

- implementation scope expands beyond `1`, `2`, and `3` for Packet 3A
- a prompt loop or blocking input is introduced
- any runtime state mutation appears
- any mutation execution appears
- any CLI wiring appears
- any real MIDI import appears
- any package metadata file appears
- any port-opening behavior appears
- any command dispatch or execution appears
- any passive CLI behavior changes unexpectedly
- any V1.34 reference diff appears
- any Analog Four or Pads 5-12 scope appears

## Next Safe Options

After this plan:

- review and accept this Packet 3 mutation-depth and guarded input plan
- pause at this planning checkpoint
- if accepted, implement only Packet 3A for guarded numeric inputs `1`, `2`,
  and `3`

## Recommendation

Review and accept this plan.

Then implement only Packet 3A:

- read-only guarded numeric input behavior for `1`, `2`, and `3`

Hardware remains off.

## Decision

Packet 3 mutation-depth and guarded input behavior is planned.

No implementation is added in this slice.
