# Live GUI Analyzer Panel Model

> Status: in-flight (PR pending)

Per docs/PLAN_REQUIREMENTS.md, this plan scopes one passive GUI-ready model for the
future desktop analyzer panel shown in the mockup's lower-right surface.

## Intent

Jose asked whether the app can move toward the richer desktop workflow with
reference-track analysis, waveform/spectrum feedback, dry-run preview, and locked
hardware controls. Existing live analyzer reports cover readiness, overlays, and
frame rehearsal. This slice adds a smaller model that a desktop GUI can consume for
the "Analyzer (Post-Mutation Preview)" panel itself.

## Scope

- Add an immutable `LiveGuiAnalyzerPanelModel` report under `rytm_randomizer.reports`.
- Consume an already-created `FeatureReport`; do not read audio or invoke analysis.
- Emit deterministic waveform bins from `FeatureReport.energy_arc`.
- Emit deterministic spectrum bands from low-end, body, mid, high, and noise traits.
- Include declarative controls, blocked actions, replay commands, and safety flags.
- Keep the model passive: no GUI launch, audio capture, file writing, MIDI port
  opening, MIDI sending, command dispatch, or hardware mutation.

## Verification

- Red-first focused tests for the missing module.
- Focused unit tests for ready state, empty state, clamping, validation, JSON, and
  formatting.
- Touched-file coverage and architecture/lint/full-suite gates before push.

## 18-Gate Notes

- Gate 1 coverage: touched Python must stay at 100% branch coverage.
- Gate 2 integration: independent report module; no CLI or active wiring.
- Gate 3 data flow: consumes `FeatureReport` only.
- Gate 4 observability: metadata-only JSON/format surface.
- Gate 5 safety: blocked hardware/audio/GUI actions emitted explicitly.
- Gate 6 test realism: unit tests exercise the GUI payload shape.
- Gate 7 user path: gives the future desktop app a waveform/spectrum contract.
- Gate 8 no hidden IO: no reads, writes, ports, GUI, or hardware.
- Gate 9 architecture: subpackage-only report addition.
- Gate 10 parity: V1.34 fixtures untouched.
- Gate 11 fixtures: no generated fixtures.
- Gate 12 dependency: no new dependencies.
- Gate 13 permissions: local repo edits only.
- Gate 14 docs: this plan documents scope and verification.
- Gate 15 rollback: remove one report module, one test file, and this plan.
- Gate 16 PR shape: clean-base, non-stacked feature PR.
- Gate 17 abstraction reuse: reuses `FeatureReport` instead of new analysis schema.
- Gate 18 learning: captures the GUI panel contract for future front-end work.
