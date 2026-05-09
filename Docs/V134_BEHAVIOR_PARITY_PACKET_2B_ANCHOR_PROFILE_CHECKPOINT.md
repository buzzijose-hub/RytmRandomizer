# V1.34 Behavior Parity Packet 2B Anchor/Profile Checkpoint

## Purpose

Record completion of the Packet 2B anchor/profile behavior implementation.

Packet 2B adds deterministic read-only intent behavior for:

- `BS`

It does not add CLI wiring, command dispatch, command execution, scene
execution, selected-profile state, profile rotation, real MIDI, port opening,
package metadata, hardware behavior, or hardware validation.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this documentation slice:

- 7872d8c Add Packet 2B anchor profile behavior

Current phase:

- Passive/Mock Foundation Phase
- Packet 1 complete for the current intent-only behavior phase
- Packet 2A anchor/profile behavior implemented and accepted
- Packet 2B anchor/profile plan accepted
- Packet 2B anchor/profile behavior implemented
- Packet 2B checkpoint now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Milestone Commit

- 7872d8c Add Packet 2B anchor profile behavior

## Files Changed By The Milestone

- `rytm_randomizer/behavior_anchor_profile.py`
- `tests/test_behavior_anchor_profile.py`

No closeout script update was needed because `tests/test_behavior_anchor_profile.py`
is already covered by:

- `=== Test: Behavior Anchor Profile ===`

## Behavior Added

Packet 2B adds:

- `PACKET_2B_ANCHOR_PROFILE_KEYS`
- `SUPPORTED_ANCHOR_PROFILE_KEYS`
- deterministic read-only `BS` handling in `evaluate_anchor_profile_behavior(command_key)`

Supported read-only Packet 2B anchor/profile key:

- `BS`

`BS` now returns:

- behavior family: `anchor/profile`
- reason: `supported_anchor_profile_intent`
- label: `load Pad 1 BD Sharp anchor`
- target pad: `1`
- anchor name: `BD Sharp`
- profile key: empty string
- machine value: `None`
- group profile metadata exists: `False`
- no prompt execution
- no state mutation
- no MIDI
- no ports
- no hardware
- no active behavior

The `BS` metadata records that group-profile metadata is absent instead of
inventing a profile key, profile name, machine value, or group-profile entry.

Existing Packet 2A behavior remains unchanged:

- `BH` remains read-only Pad 1 BD Hard anchor/profile intent for profile `"2"`
- `BC` remains read-only Pad 1 BD Classic anchor/profile intent for profile `"3"`

Unknown keys still fail safely with a deterministic unknown-command result.

Deferred anchor/profile keys still fail safely with a deterministic unsupported
result.

## Deferred Scope Preserved

Packet 2B keeps these areas deferred:

- `P` and `M` selected profile workflow
- `O` and `Z` full group anchor load/return
- rotations such as `BR`, `P2R`, `P3R`, and `P4R`
- Pad 2 anchor/profile commands
- selected isolated pad anchor return
- Pad 3 mode and anchor commands
- Pad 4 anchor/profile commands
- profile `"4"` / My BD Acoustic command `BA`
- BD FM, BD Plastic, and BD Silky anchors and returns: `BF`, `FZ`, `BP`,
  `PBH`, `BI`, and `SBH`

Profile `"4"` / My BD Acoustic remains parked unless separately approved.

## Test And Closeout Coverage

Existing test coverage was extended in:

- `tests/test_behavior_anchor_profile.py`

Closeout already includes:

- `=== Test: Behavior Anchor Profile ===`

The tests verify:

- importing the module prints nothing
- `BH` behavior remains stable
- `BC` behavior remains stable
- `BS` returns deterministic read-only Pad 1 BD Sharp anchor/profile intent
- `BS` uses no invented profile key
- `BS` uses no invented machine value
- `BS` metadata records absent group-profile metadata safely
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

- new Packet 2B tests were written first
- targeted test failed before implementation because `BS` was still unsupported
- targeted test passed after the minimal implementation
- full closeout passed after implementation

## Safety Boundary

Packet 2B adds no:

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
- BD Sharp group-profile metadata
- new group-profile entry
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
- no selected profile state model
- no profile rotation model
- no full group anchor behavior
- no Pad 2/3/4 anchor/profile behavior
- no profile `"4"` implementation
- no BD Sharp group-profile metadata
- display text remains deterministic safety/intent text, not full V1.34 output

## Next Safe Options

- review and accept this Packet 2B checkpoint
- create a docs-only Packet 2C anchor/profile behavior plan
- pause at this clean checkpoint

## Recommendation

Review and accept Packet 2B now.

Do not widen Packet 2 behavior until a separate Packet 2C plan is documented
and accepted.

## Decision

Packet 2B is complete. Hardware remains off. No real MIDI, ports, active CLI
behavior, dispatch, execution, package metadata, machine/profile expansion, or
hardware validation was added.
