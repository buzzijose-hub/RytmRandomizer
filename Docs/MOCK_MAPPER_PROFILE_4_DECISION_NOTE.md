# Mock Mapper Profile 4 Decision Note

## Purpose

This document decides how to treat existing group profile `"4"` / My BD
Acoustic before any mapper expansion.

It is documentation-only. No implementation is added by this document.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- a7f2e28 Add mock mapper profile 3 progress checkpoint

Current mock mapper status:

- profile `"2"` / My BD Hard supported
- profile `"3"` / My BD Classic supported
- profile `"4"` / My BD Acoustic remains unsupported/safe

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Current Decision

- Keep profile `"4"` / My BD Acoustic unsupported for now.
- Do not implement profile 4 mapping in this slice.
- Any future profile 4 support must be separately approved as a tiny mock-only expansion.

## Decision Options For Later

- Option A: keep profile `"4"` unsupported for now.
- Option B: plan a tiny mock-only expansion for profile `"4"`.
- Option C: stop mapper expansion here and move to broader mock mapper report/summary work.

## Reasons To Keep Unsupported For Now

- Profile 4 is a different target concept from profile 2 and 3.
- The mapper has already proven multiple-profile support with 2 and 3.
- Keeping 4 unsupported confirms unsupported existing keys fail safely.
- No need to expand scope until we decide the next phase.

## Safety Boundaries

- no real MIDI
- no mido
- no port opening
- no MIDI sending
- no active execution
- no CLI wiring
- no dispatch
- no hardware behavior
- no SysEx
- no GUI/capture
- no Analog Four
- no Pads 5-12
- no machine/profile universe expansion
- `rytm_hybrid_randomizer_v134.py` remains untouched

## Acceptance Criteria For Any Future Profile 4 Mapper Expansion

- Must remain test-only/mock-only.
- Must not import real MIDI libraries.
- Must not open ports.
- Must not send MIDI.
- Must not wire into CLI or active execution.
- Must preserve profile 2 and profile 3 behavior.
- Must preserve unknown/unsupported key safety.
- Must pass full closeout.
- Must leave V1.34 reference diff empty.

## Decision

- Profile `"4"` remains unsupported for now.
- Next recommended task can be:
  - broader mock mapper progress report
  - profile 4 mock-only expansion only after explicit approval
