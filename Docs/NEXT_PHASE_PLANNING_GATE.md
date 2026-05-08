# Next Phase Planning Gate

## Purpose

Define the next safe planning gate after completing the currently captured
V1.34 command surface as passive metadata.

This gate decides what may be planned next. It does not implement features,
edit runtime behavior, add tests, send MIDI, open ports, add active CLI
behavior, or authorize hardware validation.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- f01ed9e Add user-facing project progress report

Current phase:

- Passive/Mock Foundation Phase
- captured V1.34 command surface complete as passive metadata
- passive/mock safety foundation active
- hardware not required

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off

## Accepted Current State

The accepted passive metadata state is:

- passive command count: 109
- captured V1.34 operator entries modeled as passive command metadata: 106
- remaining captured command-surface gaps: 0
- registry report command count: `commands: 109`

The accepted progress state is:

- full dream project: roughly 25-30%
- core modular software foundation: roughly 75-85%
- passive CLI / dry-run foundation: 95%+
- captured V1.34 passive metadata map: 100%
- mock MIDI / mock active-boundary foundation: 60-70%
- real hardware validation: 0%

## What This Gate Allows

This gate allows planning work only.

Allowed next planning branches:

- review whether any V1.34 behavior is still uncaptured outside the command
  vocabulary
- strengthen mock/fake-provider active-boundary planning
- revisit real MIDI dependency planning as documentation only
- create a first hardware-validation planning checklist, still hardware-off
- write broader user-facing roadmap/timeline documents
- pause at the clean checkpoint

## What This Gate Does Not Allow

This gate does not allow:

- real MIDI sending
- `mido`
- real MIDI dependency selection
- MIDI port opening
- runtime dispatch
- command execution
- scene execution
- depth prompt execution
- current-profile mutation execution
- selected-profile runtime mutation
- hardware mutation
- SysEx writes
- GUI
- capture
- Analog Four support
- Pads 5-12 support
- machine/profile expansion
- package metadata changes
- hardware validation

## Recommended Branch Order

Recommended order:

1. Create a docs-only uncaptured V1.34 behavior review.
2. If that review is clean, create a mock/fake-provider active-boundary
   strengthening plan.
3. Only after mock/fake-provider planning is accepted, revisit real MIDI
   dependency or adapter planning.
4. Only after explicit approval, create a hardware-validation checklist.

This keeps the project moving toward the fun work without skipping the safety
checks that protect the working V1.34 reference and hardware.

## Why Review Uncaptured Behavior First

The command vocabulary is complete, but command vocabulary is not the same as
full behavior parity.

A behavior review can check whether anything important remains documented only
in prose, tests, anchors, ranges, operator habits, state transitions, or the
protected V1.34 script rather than in the passive modular model.

Examples to review later:

- anchor assumptions
- parameter ranges
- mutation-depth meaning
- current profile behavior
- selected pad/profile behavior
- state/undo assumptions
- menu/status behavior
- hardware-facing preconditions

The review should remain documentation-only.

## Safety Requirements For Any Next Slice

Every next slice must preserve:

- clean Git status before and after
- full closeout passing
- empty `git diff -- rytm_hybrid_randomizer_v134.py`
- empty package metadata diff
- package metadata files absent unless separately planned and approved
- passive CLI commands remaining read-only
- hardware remaining off

## Decision

The next recommended task is a docs-only uncaptured V1.34 behavior review.

Do not turn on hardware. Do not add real MIDI. Do not add active execution.
Runtime behavior remains unchanged.
