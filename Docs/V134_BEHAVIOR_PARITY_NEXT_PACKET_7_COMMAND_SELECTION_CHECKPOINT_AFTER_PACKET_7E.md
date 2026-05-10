# V1.34 Behavior Parity Next Packet 7 Command Selection Checkpoint After Packet 7E

## 1. Purpose

Choose the next safe Packet 7 Pad 3 lane behavior planning branch after the
accepted Packet 7E progress report review.

This is a documentation-only selection checkpoint. It does not add
implementation, tests, CLI wiring, dispatch, command execution, MIDI, ports,
package metadata, active behavior, runtime behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `2ae919b Add behavior parity progress report review after Packet 7E`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- Packet 7E Pad 3 lane behavior accepted
- progress report after Packet 7E accepted
- next Packet 7 command selection now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Current Packet 7 Progress

Accepted Packet 7 scope:

- `P3A`: Pad 3 SY Raw Mid Bass home anchor intent
- `SA`: Pad 3 SY Raw anchor return intent
- `SL`: Pad 3 SY Raw LP1 bassline mode-load intent
- `SB`: Pad 3 SY Raw Bandpass mid-bass mode-load intent
- `SX`: Pad 3 SY Raw sci-fi motion accent mode-load intent

Preserved Packet 1 ownership:

- `P3M`: show Pad 3 SY Raw bass / synth-percussion menu

Packet 7 is not complete.

## 4. Remaining Deferred Packet 7 Scope

Deferred Pad 3 scope:

- `SW`: Pad 3 SY Raw Wave + Balance discovery
- `P3R`: rotate Pad 3 through SY Raw behavior modes
- `P3X`: safely mutate the currently loaded Pad 3 mode

All remain unsupported/safe until separately planned and reviewed.

## 5. Selection Options

Option A:

- `SW`: Pad 3 SY Raw Wave + Balance discovery

Reason:

- It is an existing `PAD3_COMMANDS` command.
- It targets Pad 3 only.
- It is narrower than rotation or current-mode mutation behavior.
- It can be modeled as read-only discovery intent without runtime Pad 3 state.
- It introduces discovery vocabulary after the accepted mode-load cluster is
  complete.
- It does not require selecting or mutating a current Pad 3 mode.

Option B:

- `P3R`: rotate Pad 3 through SY Raw behavior modes

Reason to defer:

- Rotation implies behavior-mode ordering vocabulary and current-position
  meaning.
- It is broader than a single discovery intent.
- It should follow one simple discovery vocabulary slice.

Option C:

- `P3X`: safely mutate the currently loaded Pad 3 mode

Reason to defer:

- Mutation behavior implies current-mode context and is wider than a static
  read-only discovery intent.
- It should follow discovery and rotation planning.

## 6. Recommended Next Selection

Recommended next planning branch:

- docs-only Packet 7F Pad 3 lane behavior plan for `SW` only

Recommended future implementation scope:

- `SW` only

No implementation is authorized by this checkpoint.

## 7. Proposed Future Read-Only Behavior

The future plan should model `SW` as deterministic read-only intent only.

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

The helper may describe the discovery intent, but it must not mutate runtime
state, dispatch commands, execute commands, open ports, send MIDI, or touch
hardware.

## 8. Confirmed Safety Boundaries

Confirmed absent:

- implementation
- tests
- CLI execution wiring
- command dispatch
- command execution
- scene execution
- prompt/input loop
- active depth prompt
- runtime Pad 3 state
- selected Pad 3 mode runtime state
- runtime mode loading
- mutation execution
- discovery execution
- profile rotation execution
- real MIDI
- `mido`
- `rtmidi`
- port opening
- MIDI sending
- package metadata changes
- active CLI command
- active behavior
- hardware behavior
- hardware validation
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture

`rytm_hybrid_randomizer_v134.py` remains untouched.

Package metadata remains untouched.

## 9. Safe Next Options

Safe next options:

- create a docs-only review/acceptance gate for this selection checkpoint
- create a docs-only Packet 7F Pad 3 lane behavior plan for `SW` only after
  review
- pause at this selection checkpoint

## 10. Recommendation

Create a docs-only review/acceptance gate for this selection checkpoint next.

If accepted, create a docs-only Packet 7F Pad 3 lane behavior plan for `SW`
only.

## 11. Decision

The recommended next Packet 7 planning branch is:

- `SW` only

Hardware remains off.

No implementation in this slice.
