# V1.34 Behavior Parity Packet 7B Pad 3 Lane Behavior Plan

## 1. Purpose

Define the next tiny behavior-parity implementation plan for Pad 3 lane
behavior after accepted Packet 7A progress.

This is a documentation-only planning slice. It does not add implementation,
tests, CLI wiring, dispatch, command execution, MIDI, ports, package metadata,
active behavior, runtime behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `32404ce Add next Packet 7 command selection review after Packet 7A`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- Packet 7A Pad 3 lane behavior accepted
- next Packet 7 command selection review accepted `SA` as the next planning
  branch

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Gate

The accepted upstream gate is:

- `Docs/V134_BEHAVIOR_PARITY_NEXT_PACKET_7_COMMAND_SELECTION_CHECKPOINT_AFTER_PACKET_7A_REVIEW.md`

That review accepts:

- docs-only Packet 7B Pad 3 lane behavior planning
- `SA` only
- existing `PAD3_COMMANDS` metadata only
- no runtime Pad 3 state
- no selected Pad 3 mode runtime state
- no runtime anchor loading
- no mutation execution
- no discovery execution
- no command dispatch
- no MIDI
- no ports
- no package metadata
- no active behavior
- no hardware behavior

## 4. Packet 7B Planning Choice

Recommended future Packet 7B implementation scope:

- `SA` only

Command:

- `SA`: return Pad 3 SY Raw to anchor

Reason:

- It is an existing `PAD3_COMMANDS` command.
- It targets Pad 3 only.
- It is anchor-return shaped.
- It is closer to accepted `P3A` behavior than the remaining load, discovery,
  rotation, or mutation commands.
- It can be modeled as read-only intent without runtime Pad 3 state.

## 5. Proposed Future Read-Only Behavior

The future implementation should model `SA` as deterministic read-only intent
only.

Expected future result shape:

- command key: `SA`
- label: return Pad 3 SY Raw to anchor
- source metadata: `PAD3_COMMANDS`
- target pad: `3`
- lane: Pad 3 SY Raw lane
- behavior family: `pad3-lane/sy-raw-anchor-return`
- lane action: `return_pad3_sy_raw_anchor`
- intent kind: `anchor_return`
- anchor concept: Pad 3 SY Raw anchor
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

Future tests for `SA` should prove:

- existing `P3A` behavior remains unchanged
- `SA` returns a deterministic accepted read-only result
- metadata is copied from existing `PAD3_COMMANDS`
- target pad is `3`
- lane and anchor concept are explicit
- display lines say no MIDI, no ports, no hardware, no command execution
- returned metadata is copied/mutation-safe
- unknown keys still fail safely
- unsupported keys still fail safely
- `P3M` remains covered by Packet 1 menu/status behavior
- passive CLI behavior remains unchanged
- no real MIDI library is imported
- no ports are opened
- no MIDI is sent
- no package metadata changes are required
- V1.34 reference remains untouched

## 7. Existing And Deferred Packet 7 Scope

Already implemented:

- `P3A`: Pad 3 SY Raw Mid Bass home anchor intent

Preserved Packet 1 ownership:

- `P3M`: show Pad 3 SY Raw bass / synth-percussion menu

Deferred Pad 3 scope:

- `SL`: Pad 3 SY Raw LP1 bassline mode
- `SB`: Pad 3 SY Raw Bandpass mid-bass mode
- `SX`: Pad 3 SY Raw sci-fi motion accent mode
- `SW`: Pad 3 SY Raw Wave + Balance discovery
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
- no profile rotation execution
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

Before any Packet 7B implementation:

- this plan must be reviewed and accepted
- git status must be clean
- closeout must pass
- V1.34 reference diff must be empty
- package metadata diff must be empty
- implementation must use TDD
- implementation must remain read-only
- implementation must support `SA` only as the new Packet 7B scope
- existing `P3A` behavior must remain unchanged
- no runtime execution, dispatch, MIDI, ports, package metadata, active
  behavior, or hardware behavior may be introduced

## 10. Safe Next Options

Safe next options:

- create a docs-only Packet 7B Pad 3 lane behavior plan review
- pause at this planning checkpoint
- write a short user-facing progress update

## 11. Recommendation

Create a docs-only Packet 7B Pad 3 lane behavior plan review next.

If accepted, the next implementation should be a tiny TDD slice for read-only
`SA` intent only.

## 12. Decision

Packet 7B planning selects `SA` as the recommended next tiny Pad 3 lane
behavior implementation target.

Hardware remains off.

No implementation in this slice.

## 13. Review Status

This plan is reviewed by:

- `Docs/V134_BEHAVIOR_PARITY_PACKET_7B_PAD3_LANE_BEHAVIOR_PLAN_REVIEW.md`

The review accepts `SA` only as the future Packet 7B implementation scope.
