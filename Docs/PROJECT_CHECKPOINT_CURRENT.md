# RytmRandomizer Current Project Checkpoint

Date: May 4, 2026
Status: Active branch is modularize-v1.34

## Current Stable Reference

The protected stable reference is V1.34 expanded scene layer.

Git tag:

v1.34-stable-expanded-scene-layer

V1.34 remains the behavior reference until the modular version is fully validated.

## Current Git State

Current branch:

modularize-v1.34

Recent checkpoint history:

- c7d5489 Refine command metadata consistency
- a87f7bb Add Codex modularization protocol
- e3a37e3 Add individual pad command metadata scaffold
- 90f1677 Refine scene command metadata scaffold
- 556a7ba Add group command metadata scaffold
- 1130205 Clean up scaffold metadata tests
- 35e598f Add menu command metadata scaffold
- a0f5005 Add forbidden action guardrail metadata
- defbf43 Add out-of-scope pad guardrail metadata
- 8be1dfa Add validated constants metadata scaffold
- 57d3502 Add group profile metadata scaffold
- ae112cf Add main prompt depth guardrail metadata
- 0b94806 Add group layout metadata scaffold
- 3222200 Expand scene metadata scaffold
- b1d04e6 Add initial modular scaffold and tests
- 7de1691 Add Codex modularization task brief
- 50b83f9 Add modularization rules
- a762bd0 Add capture tools and project docs
- cc5ce71 Baseline V1.34 expanded scene layer checkpoint

## Current Priority

Finish behavior-preserving modularization of V1.34.

No new features should be added until the modular version behaves exactly like V1.34.

## Current Modular Scaffold

The modular scaffold is still metadata-only. Current scaffold coverage includes:

- constants / pad scope guardrails
- out-of-scope Pads 5-12 guardrails
- scene command metadata
- group layout / profile metadata
- menu / status command metadata
- forbidden / no-touch action metadata
- four-lane group command metadata
- individual Pad 1-4 command metadata
- command metadata consistency checks
- scaffold metadata tests
- Codex modularization protocol

Command metadata consistency now covers:

- MENU_COMMANDS protocol fields
- full passive SCENE_COMMANDS metadata preserved inside COMMANDS
- guarded main-prompt 1/2/3 protocol fields
- all applicable command metadata remains executable: False
- no forbidden execution fields or runtime hooks

All metadata registries are passive. They do not dispatch commands, send MIDI,
read input, open ports, mutate state, or call runtime functions.

V1.34 remains protected. No runtime execution, MIDI sending, input handling,
Pads 5-12 expansion, GUI, capture, SysEx, or Analog Four work has been added.

## Validated Rytm Scope

Current validated system focuses on Analog Rytm MKII Pads 1-4.

- Pad 1 = main kick / BD engine lane
- Pad 2 = secondary percussion / snare lane
- Pad 3 = SY Raw bass / synth-percussion lane
- Pad 4 = BD Acoustic body / accent lane

## Validated Scene Layer

V1.34 includes the expanded scene system:

- S1A = Rolling Light
- S1B = Rolling Push
- S2A = Deeper Groove
- S2B = Deeper Pressure
- S3A = Intense Motion
- S3B = Intense Grit
- S4A = Wild Controlled
- S4B = Wild Maximum
- S5 = return to clean anchors

## Permanent Safety Principle

Load anchors remain permanent.

Capture features may be added later, but capture does not replace validated anchors.

Validated anchors remain the safety net.
