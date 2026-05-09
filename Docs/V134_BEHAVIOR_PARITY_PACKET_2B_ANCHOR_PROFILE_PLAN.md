# V1.34 Behavior Parity Packet 2B Anchor/Profile Plan

## Purpose

Define the next tiny anchor/profile behavior implementation packet after
Packet 2A.

Packet 2B is planning-only. It does not add implementation, tests, runtime
behavior, CLI wiring, command dispatch, command execution, scene execution,
real MIDI, port opening, package metadata, active CLI behavior, or hardware
behavior.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 5cad62b Add Packet 2A anchor profile checkpoint review

Current phase:

- Passive/Mock Foundation Phase
- Packet 1 complete for the current intent-only behavior phase
- Packet 2A anchor/profile behavior implemented and accepted
- Packet 2B anchor/profile behavior planning now begins

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Accepted Planning Sources

This packet plan is grounded in:

- `Docs/V134_BEHAVIOR_PARITY_PACKET_2_ANCHOR_PROFILE_PLAN.md`
- `Docs/V134_BEHAVIOR_PARITY_PACKET_2_ANCHOR_PROFILE_PLAN_REVIEW.md`
- `Docs/V134_BEHAVIOR_PARITY_PACKET_2A_ANCHOR_PROFILE_REVIEW.md`
- accepted passive command metadata in `rytm_randomizer/commands.py`
- protected V1.34 reference as behavior reference only

The protected V1.34 reference remains read-only and untouched.

## Packet Identity

Packet name:

- Packet 2B: Anchor/Profile Behavior Parity

Packet intent:

- add one more deterministic read-only Pad 1 anchor-load intent
- prove the anchor/profile helper can represent an anchor command that has
  passive command metadata but no existing group-profile metadata
- preserve the current no-MIDI, no-port, no-dispatch safety boundary

## Recommended Packet 2B Implementation Scope

Recommended Packet 2B scope:

- `BS`

Packet 2B should model only deterministic read-only Pad 1 anchor/profile load
intent for:

- `BS`: load Pad 1 BD Sharp anchor

Reasons for this tiny scope:

- `BS` is the next direct Pad 1 anchor-load command after `BH` and `BC`
- it does not require selected-profile state
- it does not require profile rotation
- it does not require multi-pad group behavior
- it does not touch profile `"4"` / BD Acoustic
- it tests a useful edge case: command metadata exists, but no group-profile
  metadata exists for BD Sharp

## Existing Metadata Boundary

Existing passive command metadata for `BS` is captured in
`rytm_randomizer/commands.py:PAD1_COMMANDS`.

Existing group-profile metadata currently covers:

- `"2"` / My BD Hard
- `"3"` / My BD Classic
- `"4"` / My BD Acoustic
- `"5"` / Pad 3 SY Raw Mid Bass

There is no existing group-profile key for BD Sharp.

Packet 2B must not invent a new group-profile key, machine value, profile
name, or machine/profile universe expansion for BD Sharp.

Future `BS` behavior should use deterministic safe absent values for
profile-specific fields, such as:

- `profile_key`: empty string
- `machine_value`: `None`

The result metadata should clearly record that group-profile metadata is
absent instead of invented.

## Deferred Packet 2 Scope

Defer these areas until separately reviewed:

- `P` and `M` selected profile workflow
- `O` and `Z` full four-pad group anchor load/return
- rotations: `BR`, `P2R`, `P3R`, and `P4R`
- Pad 2 anchor/profile commands
- selected isolated pad anchor return
- Pad 3 mode and anchor commands
- Pad 4 anchor/profile commands
- Pad 1 profile `"4"` / BD Acoustic command `BA`
- BD FM, BD Plastic, and BD Silky anchors and returns: `BF`, `FZ`, `BP`,
  `PBH`, `BI`, and `SBH`

Profile `"4"` / My BD Acoustic and BD Acoustic-related expansion remain
parked unless separately approved.

## Proposed Future File Ownership

If Packet 2B is implemented later, accepted ownership is:

- modify `rytm_randomizer/behavior_anchor_profile.py`
- modify `tests/test_behavior_anchor_profile.py`

No closeout script update is expected because `tests/test_behavior_anchor_profile.py`
is already covered by:

- `=== Test: Behavior Anchor Profile ===`

Do not edit:

- `rytm_hybrid_randomizer_v134.py`
- `rytm_randomizer/cli.py`
- `rytm_randomizer/mock_midi.py`
- `rytm_randomizer/mock_message_mapper.py`
- `rytm_randomizer/mock_mapper_report.py`
- real MIDI adapter files
- package metadata files
- runtime execution or dispatch logic

## Expected Future Packet 2B Semantics

For `BS`:

- behavior family should remain `anchor/profile`
- result should describe anchor/profile intent only
- target pad should be `1`
- anchor name should be `BD Sharp`
- profile key should be an empty string
- machine value should be `None`
- metadata should record `source: PAD1_COMMANDS`
- metadata should record that group-profile metadata is absent
- no prompt should run
- no state should change
- no command should dispatch
- no command should execute
- no scene should execute
- no MIDI should be sent
- no ports should open
- no hardware should be required
- no active behavior should exist

Existing `BH` and `BC` behavior must remain unchanged.

## Required Future Tests

Packet 2B tests should prove:

- `BH` behavior remains unchanged
- `BC` behavior remains unchanged
- `BS` returns deterministic read-only Pad 1 BD Sharp anchor intent
- `BS` uses no invented profile key
- `BS` uses no invented machine value
- `BS` metadata records absent group-profile metadata safely
- accepted results expose no state mutation, prompts, ports, MIDI, hardware,
  dispatch, execution, or active behavior
- repeated evaluations are deterministic
- unknown keys still fail safely
- deferred keys still remain unsupported/safe
- profile `"4"` / BD Acoustic-related scope remains parked
- passive CLI behavior remains unchanged
- no real MIDI library is imported
- no package metadata files are introduced
- V1.34 reference remains untouched
- no Pads 5-12 support is exposed
- no Analog Four support is exposed

## Parallelization Decision

Do not parallelize the immediate Packet 2B implementation.

Reason:

- the write set is one behavior module and one test file
- the main task is preserving and extending a small result shape safely

Parallel work can be reconsidered after Packet 2B is implemented, reviewed,
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
- new group-profile metadata
- machine/profile universe expansion
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
- SysEx
- GUI/capture

## Stop Conditions For Future Implementation

Stop immediately if:

- implementation scope expands beyond `BS`
- any new profile metadata is introduced for BD Sharp
- any machine/profile universe expansion appears
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

- review and accept this Packet 2B plan
- pause at this planning checkpoint
- if accepted, implement only Packet 2B for `BS`

## Recommendation

Review and accept this plan.

Then implement only Packet 2B:

- read-only anchor/profile intent for `BS`

Hardware remains off.

## Decision

Packet 2B anchor/profile behavior is planned.

No implementation is added in this slice.
