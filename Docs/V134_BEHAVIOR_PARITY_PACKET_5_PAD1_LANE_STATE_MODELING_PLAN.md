# V1.34 Behavior Parity Packet 5 Pad 1 Lane State Modeling Plan

## 1. Purpose

Define a docs-only plan for deeper Packet 5 Pad 1 lane state modeling.

This plan describes future read-only state vocabulary and a possible tiny
future implementation scope. It does not implement lane-state modeling. It adds
no tests, CLI wiring, dispatch, command execution, MIDI, ports, package
metadata, active behavior, runtime behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `a8ae115 Add Packet 5 Pad 1 lane state modeling decision review`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity matrix documented and reviewed
- Packet 1 complete and accepted
- Packet 2 accepted as meaningful read-only anchor/profile progress
- Packet 3 complete and accepted
- Packet 4 complete and accepted
- Packet 5A accepted progress
- Packet 5B accepted progress
- Packet 5C accepted progress
- Packet 5D accepted progress
- Packet 5E accepted progress
- Packet 5 progress report after Packet 5E accepted
- Packet 5 Pad 1 lane state modeling decision note accepted
- deeper Pad 1 lane state modeling now being planned, not implemented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Current Accepted Packet 5 Surface

Accepted Packet 5A:

- `BR`: read-only Pad 1 current BD engine rotation intent
- `BM`: read-only Pad 1 current BD engine safe mutation intent

Accepted Packet 5B:

- `FT`: read-only BD FM tone/FM discovery intent
- `FK`: read-only BD FM kick/body discovery intent
- `FG`: read-only BD FM grit discovery intent
- `FZ`: read-only BD FM anchor-return intent

Accepted Packet 5C:

- `BP`: read-only BD Plastic profiled anchor/load intent
- `PT`: read-only BD Plastic tone/modulation discovery intent
- `PK`: read-only BD Plastic kick/body discovery intent
- `PX`: read-only BD Plastic rubber/experimental discovery intent
- `PBH`: read-only BD Plastic anchor-return intent

Accepted Packet 5D:

- `BI`: read-only BD Silky profiled anchor/load intent
- `ST`: read-only BD Silky smooth tone discovery intent
- `SK`: read-only BD Silky kick/body discovery intent
- `SC`: read-only BD Silky click/dust discovery intent
- `SBH`: read-only BD Silky anchor-return intent

Accepted Packet 5E:

- `BA`: read-only Pad 1 BD Acoustic anchor/load intent

Packet 5 is not complete.

## 4. Planning Objective

The future lane-state model should make the accepted Pad 1 lane behavior easier
to reason about without introducing runtime state.

The model should answer read-only questions such as:

- Which Pad 1 lane family does a key belong to?
- Is the key an anchor/load, anchor-return, discovery, rotation, or mutation
  intent?
- Does the key depend on a profiled engine, an anchor, or current engine
  context?
- Is the key metadata-only and non-executing?
- Is the key safe to describe without touching hardware?

The model must not answer live runtime questions such as:

- What machine is currently loaded on the hardware?
- What profile is currently selected in a running prompt loop?
- What state should be mutated now?
- What MIDI should be sent?

## 5. Meaning Of Lane State In This Plan

Lane state means a read-only description of expected Pad 1 lane context.

Lane state does not mean:

- live hardware state
- persisted runtime state
- selected profile state
- current prompt-loop state
- mutable command execution state
- MIDI output state

Any future implementation must keep this distinction visible in names,
metadata, tests, and documentation.

## 6. Proposed Future Lane Families

Future read-only lane-state vocabulary may include these Pad 1 lane families:

- `current_bd_engine`
  - keys: `BR`, `BM`
  - meaning: current loaded BD engine context only
- `bd_fm`
  - keys: `FT`, `FK`, `FG`, `FZ`
  - meaning: BD FM discovery/anchor-return context
- `bd_plastic`
  - keys: `BP`, `PT`, `PK`, `PX`, `PBH`
  - meaning: BD Plastic anchor/discovery/anchor-return context
- `bd_silky`
  - keys: `BI`, `ST`, `SK`, `SC`, `SBH`
  - meaning: BD Silky anchor/discovery/anchor-return context
- `bd_acoustic`
  - keys: `BA`
  - meaning: Pad 1 BD Acoustic anchor/load context only

These are planning names only until a future implementation is separately
approved.

## 7. Proposed Future State Descriptor Fields

A future read-only state descriptor may include:

- `source_key`
- `target_pad`
- `lane_family`
- `lane_action`
- `intent_kind`
- `requires_current_engine`
- `requires_anchor`
- `requires_profiled_engine`
- `anchor_key`
- `return_key`
- `discovery_depth`
- `mutation_depth`
- `metadata_only`
- `executes`
- `sends_midi`
- `opens_ports`
- `hardware_required`
- `notes`

The descriptor must be copied/mutation-safe and deterministic.

The descriptor must not contain real MIDI objects, port objects, command
dispatch callables, or hardware references.

## 8. Proposed Future Tiny Implementation Scope

If this plan is reviewed and accepted later, the first implementation should be
tiny and static.

Recommended first implementation:

- add a read-only helper that describes the lane-state context for accepted
  Packet 5 keys only
- support keys already accepted in Packet 5A through Packet 5E
- return copied/mutation-safe metadata
- fail safely for unknown keys
- fail safely for unsupported Packet 5 concepts
- keep `BA` separate from group profile `"4"`
- keep `BA` separate from Pad 4 BD Acoustic behavior

Possible future helper names for discussion only:

- `describe_pad1_lane_state(key)`
- `get_pad1_lane_family(key)`
- `build_pad1_lane_state_descriptor(key)`

Do not implement these in this slice.

## 9. Explicit Non-Goals

This plan does not authorize:

- runtime lane state
- runtime selected profile state
- runtime current profile state
- runtime anchor state
- runtime state mutation
- prompt/input loop behavior
- command dispatch
- command execution
- scene execution
- mutation execution
- discovery execution
- Pad 1 engine rotation execution
- anchor loading execution
- MIDI sending
- MIDI port opening
- package metadata changes
- active CLI commands
- hardware behavior
- profile `"4"` support
- Pad 4 BD Acoustic behavior

## 10. Future Test Requirements

If implementation is approved later, tests should verify:

- importing the module prints nothing
- existing Packet 5A through Packet 5E behavior remains unchanged
- accepted Packet 5 keys map to deterministic lane families
- descriptors are copied/mutation-safe
- `BR` and `BM` remain current-BD-engine context only
- `FT`, `FK`, `FG`, and `FZ` remain BD FM context only
- `BP`, `PT`, `PK`, `PX`, and `PBH` remain BD Plastic context only
- `BI`, `ST`, `SK`, `SC`, and `SBH` remain BD Silky context only
- `BA` remains Pad 1 BD Acoustic anchor context only
- `BA` does not depend on group profile `"4"`
- `BA` does not depend on Pad 4
- unknown keys fail safely
- unsupported concepts fail safely
- no real MIDI library is imported
- no ports are opened
- no MIDI is sent
- no CLI execution wiring is added
- no dispatch is added
- package metadata remains untouched
- V1.34 reference remains untouched

## 11. Future File Ownership

If implementation is separately approved later, expected file ownership is:

- `rytm_randomizer/behavior_pad1_lane.py`
- `tests/test_behavior_pad1_lane.py`

No closeout script update is expected if the existing Behavior Pad 1 Lane test
file remains the only test file touched.

Do not edit unrelated behavior helpers, CLI, registry report, mock MIDI,
mock message mapper, mock mapper report, package metadata, runtime scaffolds,
or V1.34 reference without separate approval.

## 12. Safety Boundaries

The following boundaries remain in force:

- no CLI execution wiring
- no dispatch
- no command execution
- no scene execution
- no runtime prompt loop
- no runtime state mutation
- no real MIDI dependency
- no `mido`
- no `rtmidi`
- no package metadata changes
- no port discovery
- no port opening
- no MIDI sending
- no active CLI command
- no `execute-command`
- no `send-command`
- no `hardware-test`
- no hardware behavior
- no hardware validation
- no machine/profile universe expansion
- no Analog Four support
- no Pads 5-12 support
- no SysEx
- no GUI/capture

`rytm_hybrid_randomizer_v134.py` remains untouched.

Package metadata remains untouched.

## 13. Preconditions Before Any Implementation

Before any implementation begins:

- Git status must be clean.
- Full closeout must pass.
- V1.34 reference diff must be empty.
- Package metadata diff must be empty unless separately approved.
- This plan must be reviewed and accepted.
- Tests must be written first.
- Existing Packet 5A through Packet 5E behavior must remain unchanged.
- Unknown-key safety must remain unchanged.
- Runtime mutation must remain absent.
- Dispatch, command execution, MIDI, ports, package metadata, active behavior,
  and hardware behavior must remain absent.

## 14. Safe Next Options

Safe next options:

- Review and accept this lane-state modeling plan.
- Pause at this clean planning checkpoint.
- Write a user-facing progress/timeline update.
- After review only, consider a tiny test-first implementation of static
  read-only lane-state descriptors.

## 15. Recommendation

Prefer a docs-only review/acceptance gate for this plan next.

After review, choose explicitly between:

- tiny test-first implementation of static read-only lane-state descriptors
- a user-facing progress/timeline update
- pausing at the clean planning checkpoint

Do not implement from this plan until it has been reviewed and accepted.

## 16. Decision

Deeper Packet 5 Pad 1 lane state modeling is planned at documentation level
only.

Packet 5 has accepted read-only progress through Packet 5E, but Packet 5 is
not complete.

Hardware remains off.

No real MIDI, ports, active behavior, package metadata, runtime execution, or
hardware behavior exists.
