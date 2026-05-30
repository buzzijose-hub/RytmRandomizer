# Reference Style Blueprint V1 Plan

> Status: shipped in PR #131.

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

- [x] Gate 1 coverage: focused tests cover blueprint shape, hashing,
  JSON serialization, source confidence, and CLI behavior.
- [x] Gate 2 parity: no V1.34 engine/group/scene output changes.
- [x] Gate 3 source safety: report consumes local description/audio/library
  metadata only; no network lookups or copyrighted reconstruction.
- [x] Gate 4 deterministic output: blueprint hash and source hash are stable
  for identical inputs.
- [x] Gate 5 docs: `docs/STYLE_ANALYSIS.md`, `docs/CLI_REFERENCE.md`,
  `README.md`, `docs/ARCHITECTURE.md`, `docs/ARCHITECTURE_DIAGRAMS.md`,
  and `docs/STATUS.md` describe the surface.
- [x] Gate 6 boundaries: all new DTOs are frozen dataclasses.
- [x] Gate 7 side effects: passive report only; stdout/JSON only.
- [x] Gate 8 observability: no new logger/trace path required because the
  command performs no active I/O.
- [x] Gate 9 placement: new work stays inside `style_analysis/` and
  `reports/`.
- [x] Gate 10 enums/literals: source confidence/type flows through existing
  guardrail schema enums.
- [x] Gate 11 shared fixtures: tests use existing public style-analysis
  helpers and CLI invocation patterns.
- [x] Gate 12 constants: module constants are annotated `Final`; mutable
  lookup tables remain immutable at runtime.
- [x] Gate 13 parity fixtures: no parity fixture capture or regeneration.
- [x] Gate 14 passive CLI safety: command is auto-discovered by the passive
  safety sweep and imports no MIDI adapter path.
- [x] Gate 15 rollback: remove the `reference_style_blueprint` report and
  `style_analysis.blueprint` export to revert without touching V1.34 runtime.
- [x] Gate 16 cascade: implemented inside the single PR #131 bundle; no
  stacked PR.
- [x] Gate 17 abstraction reuse: reuses `FeatureReport`, guardrail schema
  source/confidence enums, passive report CLI patterns, and existing
  style-analysis extraction.
- [x] Gate 18 docs/diagrams: architecture docs and diagrams now list the
  report/module/command surface.
- [x] Hardware rule: no hardware, no ports, no MIDI.
