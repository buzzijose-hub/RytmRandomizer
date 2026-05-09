# V1.34 Behavior Parity Packet 2 Anchor/Profile Plan

## Purpose

Define the next behavior-parity implementation packet after the accepted
Packet 1 menu/utility behavior baseline.

Packet 2 covers anchor/profile behavior intent from the accepted V1.34
behavior parity matrix. This document is planning-only. It adds no
implementation, tests, dispatch, command execution, scene execution, MIDI,
port opening, active CLI behavior, package metadata, or hardware behavior.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 7b3fe8c Add Packet 1 completion checkpoint review

Current phase:

- Passive/Mock Foundation Phase
- Packet 1A menu/status behavior implemented and accepted
- Packet 1B utility/session behavior implemented and accepted
- Packet 1 accepted as complete for the current intent-only behavior phase
- Packet 2 anchor/profile behavior planning now begins

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Accepted Planning Sources

This packet plan is grounded in:

- `Docs/V134_BEHAVIOR_PARITY_PACKET_1_COMPLETION_REVIEW.md`
- `Docs/V134_BEHAVIOR_PARITY_MATRIX_ANCHOR_PROFILE_SLICE.md`
- `Docs/V134_BEHAVIOR_PARITY_MATRIX_ANCHOR_PROFILE_SLICE_REVIEW.md`
- passive command metadata in `rytm_randomizer/commands.py`
- the protected V1.34 reference as behavior reference only

The protected V1.34 reference remains read-only and untouched.

## Packet Identity

Packet name:

- Packet 2: Anchor/Profile Behavior Parity

Packet intent:

- model anchor/profile load, return, and selection intent as deterministic
  read-only behavior before any real execution exists
- preserve the current no-MIDI, no-port, no-dispatch safety boundary
- keep future active behavior separate from this intent-only layer

## Full Accepted Packet 2 Planning Scope

The accepted anchor/profile matrix includes these command keys:

- `P`
- `M`
- `O`
- `Z`
- `BR`
- `BH`
- `BS`
- `BC`
- `BA`
- `BF`
- `FZ`
- `BP`
- `PBH`
- `BI`
- `SBH`
- `P2B`
- `P2H`
- `P2C`
- `P2F`
- `P2R`
- `P2Z`
- `PZ`
- `SL`
- `SB`
- `SX`
- `SA`
- `P3R`
- `P3A`
- `P4R`
- `P4A`

This full planning scope is not the first implementation scope.

## Recommended Packet 2A Implementation Scope

The first implementation slice should be much smaller than the full matrix
scope.

Recommended Packet 2A scope:

- `BH`
- `BC`

Packet 2A should model only deterministic read-only Pad 1 anchor/profile load
intent for:

- `BH`: load Pad 1 BD Hard anchor, primary default
- `BC`: load Pad 1 BD Classic anchor

Reasons for this tiny scope:

- both commands are direct Pad 1 anchor-load intent
- both avoid rotation, selected-profile state, and multi-pad group behavior
- both align with the already-supported mock mapper profiles `"2"` and `"3"`
- profile `"4"` / BD Acoustic remains parked and unsupported for now
- this is enough to stabilize an anchor/profile result shape before widening
  behavior coverage

## Deferred Packet 2 Scope

Defer these areas until separately reviewed:

- `P` and `M` selected profile workflow
- `O` and `Z` full four-pad group anchor load/return
- rotations: `BR`, `P2R`, `P3R`, and `P4R`
- Pad 2 anchor/profile commands: `P2B`, `P2H`, `P2C`, `P2F`, and `P2Z`
- selected isolated pad anchor return: `PZ`
- Pad 3 mode and anchor commands: `SL`, `SB`, `SX`, `SA`, and `P3A`
- Pad 4 anchor/profile commands: `P4A`
- Pad 1 non-initial anchors and returns: `BS`, `BA`, `BF`, `FZ`, `BP`,
  `PBH`, `BI`, and `SBH`

Profile `"4"` / My BD Acoustic and BD Acoustic-related expansion remain
parked unless separately approved.

## Proposed Future File Ownership

If Packet 2A is implemented later, proposed file ownership is:

- create `rytm_randomizer/behavior_anchor_profile.py`
- create `tests/test_behavior_anchor_profile.py`
- update `Scripts/closeout_check.ps1` only to add the new test label

Do not edit:

- `rytm_hybrid_randomizer_v134.py`
- `rytm_randomizer/cli.py`
- `rytm_randomizer/mock_midi.py`
- `rytm_randomizer/mock_message_mapper.py`
- `rytm_randomizer/mock_mapper_report.py`
- real MIDI adapter files
- package metadata files
- runtime execution or dispatch logic

## Proposed Future Behavior Shape

Future Packet 2A implementation should expose a small deterministic result
shape such as `AnchorProfileBehaviorResult`.

Useful future result fields may include:

- `command_key`
- `label`
- `behavior_family`
- `accepted`
- `reason`
- `target_pad`
- `anchor_name`
- `profile_key`
- `machine_value`
- `display_lines`
- `state_changed`
- `prompt_required`
- `sends_real_midi`
- `opens_ports`
- `hardware_required`
- `active_behavior`
- `metadata`

All metadata should be copied or immutable. No source metadata should be
mutated.

## Expected Future Packet 2A Semantics

For accepted keys:

- behavior family should be `anchor/profile`
- result should describe anchor/profile intent only
- no prompt should run
- no state should change
- no command should dispatch
- no command should execute
- no scene should execute
- no MIDI should be sent
- no ports should open
- no hardware should be required
- no active behavior should exist

For unsupported keys:

- fail safely
- return deterministic no-op or unsupported results
- emit no messages
- open no ports
- mutate no state

## Required Future Tests

Packet 2A tests should prove:

- importing the module prints nothing
- `BH` returns deterministic read-only Pad 1 BD Hard anchor intent
- `BC` returns deterministic read-only Pad 1 BD Classic anchor intent
- accepted results expose no state mutation, prompts, ports, MIDI, hardware,
  dispatch, execution, or active behavior
- result metadata is copied or immutable
- repeated evaluations are deterministic
- unknown keys fail safely
- deferred keys remain unsupported/safe
- profile `"4"` / BD Acoustic-related scope remains parked
- passive CLI behavior remains unchanged
- no real MIDI library is imported
- no package metadata files are introduced
- V1.34 reference remains untouched
- no Pads 5-12 support is exposed
- no Analog Four support is exposed

## Parallelization Decision

Do not parallelize the immediate Packet 2A implementation.

Reason:

- the first anchor/profile result shape should stabilize in one small module
  and one small test file before any independent workstream is useful

Parallel work can be reconsidered after Packet 2A is implemented, reviewed,
and accepted.

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
- profile rotation
- full group anchor loading
- profile `"4"` implementation
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
- Analog Four support
- Pads 5-12 support
- machine/profile expansion
- SysEx
- GUI/capture

## Stop Conditions For Future Implementation

Stop immediately if:

- implementation scope expands beyond `BH` and `BC`
- any real MIDI import appears
- any package metadata file appears
- any port-opening behavior appears
- any command dispatch or execution appears
- any passive CLI behavior changes unexpectedly
- any V1.34 reference diff appears
- any profile `"4"` implementation slips in
- any Analog Four or Pads 5-12 scope appears

## Next Safe Options

After this plan:

- review and accept this Packet 2 plan
- pause at this planning checkpoint
- if accepted, implement only Packet 2A for `BH` and `BC`

## Recommendation

Review and accept this plan.

Then implement only Packet 2A:

- read-only anchor/profile intent for `BH`
- read-only anchor/profile intent for `BC`

Hardware remains off.

## Decision

Packet 2 anchor/profile behavior is planned.

No implementation is added in this slice.
