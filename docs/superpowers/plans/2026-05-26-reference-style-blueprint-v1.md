# Reference Style Blueprint V1 Plan

> Status: draft (PR pending)

## Goal

Create a passive, deterministic bridge from a measured or described reference
track into an original Analog Rytm plus Analog Four starting blueprint.

The feature must answer Jose's workflow question: if a reference track suggests
heavy low end, metallic pressure, groove density, texture, and arrangement
energy, what 12 Rytm pad roles and 4 Analog Four track roles should the system
prepare for future mock preview and GUI surfaces?

## Scope

- Add a `style_analysis.blueprint` module that consumes `FeatureReport`.
- Emit frozen dataclasses for traits, 12 Rytm pad suggestions, 4 Analog Four
  track suggestions, safety flags, and deterministic hashes.
- Add a passive CLI report: `reference-style-blueprint-report`.
- Support `--description`, `--audio`, and `--library` sources with `--json`.
- Preserve the influence-not-replica rule and keep all output metadata-only.

## Non-Goals

- No MIDI port opening.
- No MIDI sending.
- No pattern generation.
- No GUI launch.
- No file export/write behavior.
- No copyrighted melody, arrangement, or patch reconstruction.

## Verification

- Focused TDD coverage for blueprint shape, hashing, JSON serialization,
  low-confidence safety caps, and CLI behavior.
- Existing style-analysis public-surface test updated for the new exports.
- Architecture, fast, and full verification required before PR handoff.

## Plan-Gate Notes

- Gate 1 coverage: tests cover new backend and CLI branches.
- Gate 2 parity: no V1.34 engine/group/scene output changes intended.
- Gate 6 boundaries: all new DTOs are frozen dataclasses.
- Gate 7 side effects: passive report only; no logger/trace decision path.
- Gate 9 placement: new work stays inside `style_analysis/` and `reports/`.
- Gate 12 constants: module constants are annotated `Final`.
- Gate 16 cascade: clean branch from `origin/modularize-v1.34`; not stacked on PR #118.
- Hardware rule: no hardware, no ports, no MIDI.
