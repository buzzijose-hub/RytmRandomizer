# V1.34 Behavior Parity Packet 2A Anchor/Profile Checkpoint

## Purpose

Record completion of the Packet 2A anchor/profile behavior implementation.

Packet 2A adds deterministic read-only intent results for:

- `BH`
- `BC`

It does not add CLI wiring, command dispatch, command execution, scene
execution, selected-profile state, profile rotation, real MIDI, port opening,
package metadata, hardware behavior, or hardware validation.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this documentation slice:

- cf82881 Add Packet 2A anchor profile behavior

Current phase:

- Passive/Mock Foundation Phase
- Packet 1 complete for the current intent-only behavior phase
- Packet 2 anchor/profile behavior plan accepted
- Packet 2A anchor/profile behavior implemented
- Packet 2A checkpoint now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Milestone Commit

- cf82881 Add Packet 2A anchor profile behavior

## Files Changed By The Milestone

- `rytm_randomizer/behavior_anchor_profile.py`
- `tests/test_behavior_anchor_profile.py`
- `Scripts/closeout_check.ps1`

## Behavior Added

Packet 2A adds:

- `PACKET_2A_ANCHOR_PROFILE_KEYS`
- `AnchorProfileBehaviorResult`
- `evaluate_anchor_profile_behavior(command_key)`

Supported read-only anchor/profile keys:

- `BH`
- `BC`

`BH` now returns:

- behavior family: `anchor/profile`
- reason: `supported_anchor_profile_intent`
- label: `load Pad 1 BD Hard anchor, primary default`
- target pad: `1`
- anchor name: `BD Hard`
- profile key: `"2"`
- machine value: `0`
- no prompt execution
- no state mutation
- no MIDI
- no ports
- no hardware
- no active behavior

`BC` now returns:

- behavior family: `anchor/profile`
- reason: `supported_anchor_profile_intent`
- label: `load Pad 1 BD Classic anchor`
- target pad: `1`
- anchor name: `BD Classic`
- profile key: `"3"`
- machine value: `1`
- no prompt execution
- no state mutation
- no MIDI
- no ports
- no hardware
- no active behavior

Unknown keys fail safely with a deterministic unknown-command result.

Deferred anchor/profile keys fail safely with a deterministic unsupported
result.

## Deferred Scope Preserved

Packet 2A keeps these areas deferred:

- `P` and `M` selected profile workflow
- `O` and `Z` full group anchor load/return
- rotations such as `BR`, `P2R`, `P3R`, and `P4R`
- Pad 2 anchor/profile commands
- selected isolated pad anchor return
- Pad 3 mode and anchor commands
- Pad 4 anchor/profile commands
- Pad 1 non-initial anchors and returns
- profile `"4"` / BD Acoustic-related expansion

Profile `"4"` / My BD Acoustic remains parked unless separately approved.

## Test And Closeout Coverage

New test coverage:

- `tests/test_behavior_anchor_profile.py`

Closeout now includes:

- `=== Test: Behavior Anchor Profile ===`

The tests verify:

- importing the module prints nothing
- `BH` returns deterministic read-only Pad 1 BD Hard anchor/profile intent
- `BC` returns deterministic read-only Pad 1 BD Classic anchor/profile intent
- metadata is copied and immutable
- repeated evaluations are deterministic
- unknown keys fail safely
- deferred keys remain unsupported/safe
- passive CLI behavior remains unchanged
- no real MIDI library is imported
- no package metadata files are introduced
- no active command names are exposed
- no Analog Four or Pads 5-12 scope is exposed

TDD evidence:

- new Packet 2A tests were written first
- targeted test failed before implementation with `ModuleNotFoundError`
- targeted test passed after the minimal implementation
- full closeout passed after adding the closeout hook

## Safety Boundary

Packet 2A adds no:

- CLI wiring
- command dispatch
- command execution
- scene execution
- prompt/input loop
- selected profile state
- profile rotation
- full group anchor loading
- runtime state mutation
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
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture

`rytm_hybrid_randomizer_v134.py` remains untouched.

## Current Limitations

- no CLI exposure of the behavior module
- no routing loop
- no active command execution
- no selected profile state model
- no profile rotation model
- no full group anchor behavior
- no Pad 2/3/4 anchor/profile behavior
- no profile `"4"` implementation
- display text remains deterministic safety/intent text, not full V1.34 output

## Next Safe Options

- review and accept this Packet 2A checkpoint
- create a docs-only Packet 2B anchor/profile behavior plan
- pause at this clean checkpoint

## Recommendation

Review and accept Packet 2A now.

Do not widen Packet 2 behavior until a separate Packet 2B plan is documented
and accepted.

## Decision

Packet 2A is complete. Hardware remains off. No real MIDI, ports, active CLI
behavior, dispatch, execution, package metadata, or hardware validation was
added.
