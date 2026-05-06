# Active Layer Design Spec Review

## Purpose

This document reviews and accepts `ACTIVE_LAYER_DESIGN_SPEC.md` as the current
planning spec.

It confirms that the project is still passive/read-only and that no
active/hardware-facing behavior has been implemented.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 6e90f21 Add active-layer design spec

Current phase:

- passive CLI / dry-run foundation with active-layer design/spec complete

Current hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Active-Layer Design Acceptance Summary

`ACTIVE_LAYER_DESIGN_SPEC.md` is accepted as the current planning spec.

- Active behavior is still not implemented.
- Any future active behavior must remain isolated behind an explicit boundary.
- Passive CLI commands must remain read-only by default.
- Future active behavior must require explicit operator intent, arming, target confirmation, and mockable MIDI testing before real hardware validation.

## Accepted Design Concepts

- mockable MIDI boundary
- arming model
- passive preview preflight
- explicit target device/port confirmation
- visible safety summary before send
- first-test constraints
- forbidden early active scope
- required tests before implementation
- stop conditions
- operator checklist

## Confirmed Safety Invariants

- no MIDI sending
- no MIDI port opening
- no dispatch
- no command execution
- no scene execution
- no hardware mutation
- no SysEx
- no GUI
- no capture
- no Analog Four support
- no Pads 5-12 support
- no machine/profile expansion
- `rytm_hybrid_randomizer_v134.py` remains untouched

## Preconditions Before Any Future Mock MIDI Implementation

- clean Git status
- closeout passes
- V1.34 reference diff is empty
- active-layer design/spec accepted
- passive-to-active boundary accepted
- passive CLI remains read-only
- mock MIDI boundary must be test-only first
- no real MIDI ports may open in unit tests
- no real hardware required

## Preconditions Before Any Future Real Hardware Validation

- all mock MIDI tests pass
- passive commands still proven passive
- missing arming fails safely
- unknown key fails safely
- unsupported command fails safely
- operator explicitly confirms hardware validation phase
- Analog Rytm kit/project saved
- monitoring volume lowered
- correct MIDI output port identified
- passive preview confirms intended action
- one tiny low-risk action selected and reviewed

## Rejected/Forbidden Next Moves

- Do not jump directly to MIDI sending.
- Do not turn on the Rytm yet.
- Do not add real port opening yet.
- Do not add execute-command yet.
- Do not add send-command yet.
- Do not add scene execution.
- Do not add global mutation execution.
- Do not add Pads 5-12.
- Do not add Analog Four.
- Do not add GUI/capture.
- Do not add SysEx.
- Do not add pattern/project/transport/clock behavior.

## Decision

- Active-layer design/spec accepted for planning.
- Proceed next with mock MIDI boundary planning or test-only mock MIDI design.
- Hardware remains off.

## Next Recommended Task

Create a test-only mock MIDI boundary plan/spec.

Do not implement real MIDI yet.

Keep hardware off.
