# Audio-to-Rytm Recipe Inference

> Status: in-flight
>
> Implementation is complete; review is pending.

## Goal

Add the missing passive bridge between measured reference-audio features and an
explainable Analog Rytm recipe proposal. The result must be useful for musical
direction while remaining honest about which values are verified device writes
and which are still hypotheses or mapping gaps.

## Problem

The repository can measure audio and has verified Rytm machine, pad-role, and
AL16 writable-field facts. It does not yet have a focused layer that combines
those facts into a deterministic pad-level proposal without crossing into codec,
SysEx, or hardware responsibilities.

## Scope

- Consume an already-built `AudioFeatureAnalysis`; do not read or decode audio.
- Preserve the permanent AL16 12-pad role layout.
- Propose bounded fields for pads 1, 3, 6, and 9, preserving every other pad.
- Validate proposed machines against the repository machine catalog.
- Reuse the AL16 verified writable-field allowlist.
- Record the exact source feature and equation for every proposed value.
- Express pitch as machine-specific tuning intent and fail closed when the
  approved tuning table has no exact machine/note pair.
- Produce a deterministic canonical recipe identifier and serializable payload.

## Evidence model

The implementation distinguishes three layers:

1. `RytmAudioFeatureEvidence`: measured normalized facts from audio analysis.
2. `RytmRecipeFieldProposal`: bounded musical intent plus provenance equation.
3. Mapping status: whether that intent has a verified downstream write path.

`writable_proposal` means that the semantic field is in the current approved
AL16 mapping surface. `mapping_required` means the musical proposal is retained
but downstream compilation must preserve the current hardware value. Neither
status means the proposal has been auditioned or hardware verified.

## Architecture

```text
AudioFeatureAnalysis
  -> normalized evidence snapshot
  -> stable AL16 pad-role planner
  -> bounded field equations
  -> machine compatibility validation
  -> writable/mapping-required classification
  -> deterministic proposal payload + recipe SHA-256
```

The module lives under `style_analysis/`. It imports only passive data facts and
standard-library helpers. It adds no command, file writer, codec dependency,
MIDI provider, or hardware entry point.

## Non-goals

- No SysEx encoding, kit patching, destination-slot selection, or file output.
- No MIDI enumeration, port open, transmission, or hardware interaction.
- No replacement for the in-flight dual-device codec/export work.
- No competing render-feedback evaluator.
- No claim that measured audio uniquely determines a synthesizer patch.
- No guessed machine-specific raw tuning values.

## Verification plan

- Deterministic output and recipe identifier for identical analysis.
- Stable pad roles and legal machine choices.
- Explicit preserved pads and mapping gaps.
- All writable proposals remain within the verified 7-bit domain.
- Feature changes alter their intended proposal dimensions.
- Pitch cannot become a raw tune value without an exact approved table entry.
- Runtime validation rejects incompatible machines and invalid analysis types.
- Touched-file statement and branch coverage at 100%.
- Architecture, V1.34 parity, full suite, strict typing, and lint gates.
- Static audit proving no MIDI/provider/hardware import or side effect.

## Verification results

- Focused proposal tests: 11 passed.
- Broader Rytm/style-analysis tests: 121 passed.
- Touched production coverage: 174 statements and 12 branches at 100%.
- Architecture enforcement: 750 passed.
- Frozen V1.34 parity: 685 passed.
- Complete repository suite: 7,904 passed and 4 skipped.
- Strict touched-module Pyright: 0 errors and 0 warnings.
- Ruff, Black, isort, and `git diff --check`: passed.
- Safety audit: no MIDI/provider import, port enumeration/open, transmission,
  SysEx/file emission, or hardware interaction was added or exercised.

## Plan-requirements conformance

- [x] Gate 1 - tests are planned at public behavior and branch boundaries.
- [x] Gate 2 - behavior remains passive and deterministic.
- [x] Gate 3 - strict typed dataclasses and payload shapes; no `Any` escape.
- [x] Gate 4 - no new top-level package module.
- [x] Gate 5 - existing data facts are reused rather than duplicated.
- [x] Gate 6 - invalid machine/pad combinations fail closed.
- [x] Gate 7 - mapping gaps remain visible in the output.
- [x] Gate 8 - no import-time work or hidden I/O.
- [x] Gate 9 - V1.34 behavior and frozen fixtures remain untouched.
- [x] Gate 10 - no MIDI dependency or physical-device path.
- [x] Gate 11 - focused tests use local helpers only where clearer than fixtures.
- [x] Gate 12 - deterministic SHA-256 covers the complete proposal payload.
- [x] Gate 13 - documentation states limits and evidence levels explicitly.
- [x] Gate 14 - no dependency or workflow changes.
- [x] Gate 15 - no installer, generated binary, or private artifact changes.
- [x] Gate 16 - branch is based directly on `modularize-v1.34`, not another PR.
- [x] Gate 17 - implementation does not overlap codec/export or render scoring.
- [x] Gate 18 - review will include architecture, abstraction, docs, and safety.
