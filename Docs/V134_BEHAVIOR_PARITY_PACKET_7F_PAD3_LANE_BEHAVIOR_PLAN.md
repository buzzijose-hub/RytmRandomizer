# V1.34 Behavior Parity Packet 7F Pad 3 Lane Behavior Plan

## 1. Purpose

Define the next tiny Packet 7F Pad 3 lane behavior planning slice for `SW`
only.

This is documentation-only. It does not add implementation, tests, CLI wiring,
dispatch, command execution, MIDI, ports, package metadata, active behavior,
runtime behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `ffa2f19 Add next Packet 7 command selection review after Packet 7E`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- Packet 7E accepted
- progress report after Packet 7E accepted
- next Packet 7 command selection after Packet 7E accepted
- Packet 7F Pad 3 lane behavior now being planned

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Gate

Accepted upstream selection review:

- `Docs/V134_BEHAVIOR_PARITY_NEXT_PACKET_7_COMMAND_SELECTION_CHECKPOINT_AFTER_PACKET_7E_REVIEW.md`

The selection review accepts docs-only Packet 7F Pad 3 lane behavior planning
for `SW` only.

Accepted future Packet 7F planning vocabulary:

- Pad 3 SY Raw Wave + Balance discovery intent
- existing `PAD3_COMMANDS` metadata
- target pad `3`
- lane `Pad 3 SY Raw lane`
- behavior family `pad3-lane/sy-raw-wave-balance-discovery`
- lane action `describe_pad3_sy_raw_wave_balance_discovery_intent`
- intent kind `discovery`
- discovery concept `Pad 3 SY Raw Wave + Balance discovery`
- read-only intent only

The upstream gate does not authorize implementation, tests, runtime Pad 3
state, discovery execution, mutation, rotation, dispatch, MIDI, ports, package
metadata, active behavior, or hardware behavior.

## 4. Packet 7F Planning Choice

Packet 7F planning scope:

- `SW` only

Command meaning:

- `SW`: Pad 3 SY Raw Wave + Balance discovery

Reasons for choosing `SW` next:

- It is an existing `PAD3_COMMANDS` command.
- It targets Pad 3 only.
- It follows the accepted Pad 3 lane helper shape.
- It introduces discovery vocabulary after the accepted mode-load cluster.
- It is narrower than rotation or current-mode mutation behavior.
- It can be modeled as read-only intent without runtime Pad 3 state.

## 5. Proposed Future Read-Only Behavior

A future Packet 7F implementation may model `SW` as deterministic read-only
intent only.

Expected future result shape:

- command key: `SW`
- label: Pad 3 SY Raw Wave + Balance discovery
- source metadata: `PAD3_COMMANDS`
- target pad: `3`
- lane: Pad 3 SY Raw lane
- behavior family: `pad3-lane/sy-raw-wave-balance-discovery`
- lane action: `describe_pad3_sy_raw_wave_balance_discovery_intent`
- intent kind: `discovery`
- discovery concept: Pad 3 SY Raw Wave + Balance discovery
- accepted: true
- mock-only: true
- sends real MIDI: false
- opens ports: false
- hardware required: false
- active behavior: false

The helper may describe the intended discovery concept, but it must not run
discovery, mutate runtime state, dispatch commands, execute commands, open
ports, send MIDI, or touch hardware.

## 6. Expected Future Test Coverage

Future tests should verify:

- existing `P3A` behavior remains unchanged
- existing `SA` behavior remains unchanged
- existing `SL` behavior remains unchanged
- existing `SB` behavior remains unchanged
- existing `SX` behavior remains unchanged
- `SW` returns deterministic accepted read-only intent data
- `SW` copies existing `PAD3_COMMANDS` metadata
- `SW` records target pad `3`
- `SW` records lane `Pad 3 SY Raw lane`
- `SW` records behavior family
  `pad3-lane/sy-raw-wave-balance-discovery`
- `SW` records lane action
  `describe_pad3_sy_raw_wave_balance_discovery_intent`
- `SW` records intent kind `discovery`
- `SW` records discovery concept `Pad 3 SY Raw Wave + Balance discovery`
- displayed or formatted behavior says no MIDI, no ports, no hardware, and no
  execution
- returned metadata is copied and mutation-safe
- unknown keys still fail safely
- unsupported deferred keys still fail safely
- `P3M` remains Packet 1 menu/status behavior
- passive CLI behavior remains unchanged
- no real MIDI library is imported
- package metadata remains untouched
- V1.34 reference remains untouched

## 7. Existing And Deferred Packet 7 Scope

Already implemented and accepted:

- `P3A`: Pad 3 SY Raw Mid Bass home anchor intent
- `SA`: Pad 3 SY Raw anchor return intent
- `SL`: Pad 3 SY Raw LP1 bassline mode-load intent
- `SB`: Pad 3 SY Raw Bandpass mid-bass mode-load intent
- `SX`: Pad 3 SY Raw sci-fi motion accent mode-load intent

Preserved Packet 1 ownership:

- `P3M`: show Pad 3 SY Raw bass / synth-percussion menu

Deferred/safe Packet 7 scope:

- `P3R`: rotate Pad 3 through SY Raw behavior modes
- `P3X`: safely mutate the currently loaded Pad 3 mode

The deferred commands remain unsupported/safe until separately planned and
reviewed.

## 8. Non-Goals

No implementation in this slice.

No tests in this slice.

No CLI execution wiring.

No dispatch.

No command execution.

No scene execution.

No prompt/input loop.

No runtime Pad 3 state.

No selected Pad 3 mode runtime state.

No runtime discovery execution.

No runtime mode loading.

No mutation execution.

No profile rotation execution.

No real MIDI.

No `mido`.

No `rtmidi`.

No port opening.

No MIDI sending.

No package metadata changes.

No active CLI command.

No active behavior.

No hardware behavior.

No hardware validation.

No Analog Four support.

No Pads 5-12 support.

No SysEx.

No GUI/capture.

## 9. Preconditions Before Implementation

Before any future Packet 7F implementation:

- this plan must be reviewed and accepted
- git status must be clean
- closeout must pass
- V1.34 reference diff must be empty
- package metadata diff must be empty
- implementation must use TDD
- implementation must remain read-only
- implementation must support `SW` only
- implementation must preserve `P3A`, `SA`, `SL`, `SB`, and `SX`
- implementation must keep `P3M` in Packet 1 menu/status ownership
- implementation must keep `P3R` and `P3X` unsupported/safe
- implementation must not add runtime Pad 3 state
- implementation must not add discovery execution
- implementation must not add dispatch, MIDI, ports, active behavior, or
  hardware behavior

## 10. Safe Next Options

Safe next options:

- create a docs-only review/acceptance gate for this Packet 7F plan
- pause at this planning checkpoint
- write a short progress update before implementation

## 11. Recommendation

Create a docs-only Packet 7F plan review next.

If accepted, proceed with a tiny TDD implementation for read-only `SW`
discovery intent only.

## 12. Decision

Packet 7F planning selects:

- `SW` only

Hardware remains off.

No implementation in this slice.
