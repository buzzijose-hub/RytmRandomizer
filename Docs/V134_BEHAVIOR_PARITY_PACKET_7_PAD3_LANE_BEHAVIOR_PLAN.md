# V1.34 Behavior Parity Packet 7 Pad 3 Lane Behavior Plan

## 1. Purpose

Define the next tiny behavior-parity implementation plan for Pad 3 lane
behavior.

This is a documentation-only planning slice. It does not add implementation,
tests, CLI wiring, dispatch, command execution, MIDI, ports, package metadata,
active behavior, runtime behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `794aabb Add next behavior parity packet selection review after Packet 6J`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity matrix documented and reviewed
- Packet 1 Menu/Utility Behavior Parity complete and accepted
- Packet 2 Anchor/Profile Behavior Parity has meaningful read-only progress
- Packet 3 Mutation-Depth and Guarded Input Behavior Parity complete and
  accepted
- Packet 4 Scene and Group Intent Behavior Parity complete and accepted
- Packet 5 Pad 1 Lane Behavior Parity has meaningful read-only progress
- Packet 6 Pad 2 Lane Behavior command-helper scope is covered by read-only
  intent helpers
- Packet 7 Pad 3 lane behavior planning is now beginning

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Gate

The accepted upstream gate is:

- `Docs/V134_BEHAVIOR_PARITY_NEXT_PACKET_SELECTION_CHECKPOINT_AFTER_PACKET_6J_REVIEW.md`

That review accepts:

- docs-only Packet 7 Pad 3 lane behavior planning
- one tiny Pad 3 command only after review
- existing metadata only
- no runtime Pad 3 state
- no selected Pad 3 mode runtime state
- no runtime anchor loading
- no mutation execution
- no discovery execution
- no dispatch
- no MIDI
- no ports
- no hardware behavior

## 4. Packet 7 Planning Choice

Recommended first Packet 7 implementation scope:

- `P3A` only

Command:

- `P3A`: return Pad 3 to SY Raw Mid Bass anchor / home

Reason:

- It is an existing `PAD3_COMMANDS` command.
- It targets Pad 3 only.
- It is anchor-return shaped and smaller than rotation, mutation, or discovery
  behavior.
- It can be modeled as a read-only intent helper without runtime Pad 3 state.
- `P3M` is already covered by Packet 1 menu/status behavior.

## 5. Proposed Future Read-Only Behavior

The future implementation should model `P3A` as deterministic read-only intent
only.

Expected future result shape:

- command key: `P3A`
- label: return Pad 3 to SY Raw Mid Bass anchor / home
- source metadata: `PAD3_COMMANDS`
- target pad: `3`
- lane: Pad 3 SY Raw lane
- behavior family: `pad3-lane/sy-raw-mid-bass-home-anchor`
- lane action: `return_pad3_sy_raw_mid_bass_home_anchor`
- intent kind: `anchor_return`
- anchor concept: Pad 3 SY Raw Mid Bass home anchor
- accepted: true
- mock-only: true
- sends real MIDI: false
- opens ports: false
- hardware required: false
- active behavior: false

The helper may describe the intent, but it must not load anchors, mutate
runtime state, dispatch commands, execute commands, open ports, send MIDI, or
touch hardware.

## 6. Expected Future Test Coverage

Future tests for `P3A` should prove:

- importing the Pad 3 behavior module prints nothing
- `P3A` returns a deterministic accepted read-only result
- metadata is copied from existing `PAD3_COMMANDS`
- target pad is `3`
- lane and anchor concept are explicit
- display lines say no MIDI, no ports, no hardware, no command execution
- returned metadata is copied/mutation-safe
- unknown keys fail safely
- unsupported existing keys fail safely
- `P3M` remains covered by Packet 1 menu/status behavior
- passive CLI behavior remains unchanged
- no real MIDI library is imported
- no ports are opened
- no MIDI is sent
- no package metadata changes are required
- V1.34 reference remains untouched

## 7. Deferred Packet 7 Scope

Deferred Pad 3 scope:

- `P3M`: already covered by Packet 1 menu/status behavior
- `SW`: Pad 3 SY Raw Wave + Balance discovery
- `SL`: Pad 3 SY Raw LP1 bassline mode
- `SB`: Pad 3 SY Raw Bandpass mid-bass mode
- `SX`: Pad 3 SY Raw sci-fi motion accent mode
- `SA`: return Pad 3 SY Raw to anchor
- `P3R`: rotate Pad 3 through SY Raw behavior modes
- `P3X`: safely mutate the currently loaded Pad 3 mode

None of these are implemented by this plan.

## 8. Non-Goals

- no implementation
- no tests
- no CLI execution wiring
- no command dispatch
- no command execution
- no prompt/input loop
- no runtime Pad 3 state
- no selected Pad 3 mode runtime state
- no runtime anchor loading
- no mutation execution
- no discovery execution
- no real MIDI
- no `mido`
- no `rtmidi`
- no port opening
- no MIDI sending
- no package metadata changes
- no active CLI command
- no active behavior
- no hardware behavior
- no hardware validation
- no Analog Four support
- no Pads 5-12 support
- no SysEx
- no GUI/capture

`rytm_hybrid_randomizer_v134.py` must remain untouched.

Package metadata must remain untouched.

## 9. Preconditions Before Implementation

Before any Packet 7 implementation:

- this plan must be reviewed and accepted
- git status must be clean
- closeout must pass
- V1.34 reference diff must be empty
- package metadata diff must be empty
- implementation must use TDD
- implementation must remain read-only
- implementation must support `P3A` only
- no runtime execution, dispatch, MIDI, ports, package metadata, active
  behavior, or hardware behavior may be introduced

## 10. Safe Next Options

Safe next options:

- create a docs-only Packet 7 Pad 3 lane behavior plan review
- pause at this planning checkpoint

## 11. Recommendation

Create a docs-only Packet 7 Pad 3 lane behavior plan review next.

If accepted, the next implementation should be a tiny TDD slice for read-only
`P3A` intent only.

## 12. Decision

Packet 7 planning selects `P3A` as the recommended first tiny Pad 3 lane
behavior implementation target.

Hardware remains off.

No implementation in this slice.

## 13. Review Status

This plan is reviewed by:

- `Docs/V134_BEHAVIOR_PARITY_PACKET_7_PAD3_LANE_BEHAVIOR_PLAN_REVIEW.md`

The review accepts `P3A` only as the future Packet 7A implementation scope.
