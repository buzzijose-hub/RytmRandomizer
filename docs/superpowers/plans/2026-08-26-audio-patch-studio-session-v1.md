# Audio-to-Patch Studio Session V1

> Status: in-flight (implementation and verification complete; PR pending)

## Goal

Join the merged passive Audio-to-Patch DNA selection and bounded Analog Four
render-refinement workflows into one resumable studio session. The operator
must be able to stop after candidate export, record the hardware later, and
resume from a cryptographically verified commit marker without rerunning or
silently replacing earlier work.

## Scope

- Add a typed passive session service under `cockpit/export/`.
- Start from one reference audio file, one source A4 kit, and one selected DNA
  direction.
- Reuse the existing DNA workspace exporter and one-candidate A4 exporter.
- Commit relative artifact paths and SHA-256 identities in
  `studio-session.json` plus a readable Markdown summary.
- Resume with one recorded render and reuse the existing bounded
  accept/refine service.
- Keep the global DNA direction distinct from the selected batch's local
  manifest candidate number.
- Make identical start/resume requests idempotent and reject input or artifact
  drift.
- Register one passive CLI command with explicit start and resume forms.

## Out Of Scope

- No audio recording, DAW control, MIDI enumeration, port access, or MIDI and
  SysEx transmission.
- No new synthesis inference, acoustic scoring, or refinement equations.
- No repeated optimizer loop, model training, forensic recreation claim, or
  artist/equipment attribution.
- No Analog Rytm export, live application, UI, or V1.34 parity change.

## Workflow

```text
reference audio + source A4 kit + DNA direction
  -> existing Audio-to-Patch DNA workspace/export
  -> SHA-bound studio-session.json commit marker
  -> operator records selected A4 candidate
  -> verify reference, kit, manifest, and committed artifacts
  -> existing one-pass accept/refine service
  -> terminal accepted/refined session state
```

## Plan Requirements

- [x] Gate 1 - Coverage: focused statement and branch coverage is required for
  both new production modules.
- [x] Gate 2 - Parity: the workflow composes passive exporters and does not
  alter V1.34 behavior or fixtures.
- [x] Gate 3 - Lint, format, and type safety: run Ruff, Black, isort, and the
  strict touched-production typecheck.
- [x] Gate 4 - Dead code: expose only the registered command and typed service
  API used by tests and the CLI.
- [x] Gate 5 - Documentation: update README, CLI reference, status, plan index,
  architecture, and architecture diagrams.
- [x] Gate 6 - Type hygiene: use frozen dataclasses and explicit mappings; no
  `Any` escape hatches.
- [x] Gate 7 - Observability: preserve the child export services' RED telemetry
  and publish a durable hash-bound session state and readable summary.
- [x] Gate 8 - Test hygiene: use synthetic files and monkeypatched child
  services; tests open no hardware and send nothing.
- [x] Gate 9 - Module organization: add the service beside the existing
  passive export services under `cockpit/export/`.
- [x] Gate 10 - String dispatch: register one canonical CLI command through the
  existing registry and lazy root dispatcher.
- [x] Gate 11 - Shared fixtures: keep narrow local fake result builders in the
  focused test module because no repository-wide fixture is shared.
- [x] Gate 12 - Final constants: schema and artifact filenames are immutable
  module constants.
- [x] Gate 13 - Environment variables: add none.
- [x] Gate 14 - Maintainability: centralize hashing, relative artifact
  validation, state loading, and atomic commit-marker publication.
- [x] Gate 15 - Learning: record durable operator and architecture behavior in
  the existing docs; no new reusable learned skill is warranted.
- [x] Gate 16 - Execution shape: one clean branch and one direct non-stacked PR
  against `modularize-v1.34`.
- [x] Gate 17 - Abstraction reuse: call the existing DNA and refinement export
  services and canonical atomic writer instead of duplicating them.
- [x] Gate 18 - Architecture freshness: update both the responsibility table
  and command/dependency diagrams.

## Verification

- Focused Studio Session service and CLI: 53 passed; both new production
  modules reached 100 percent statement and branch coverage.
- Existing DNA, A4 batch reader/export, render-rank, and refinement regression
  slice: 437 passed.
- Architecture gate: 777 passed.
- Frozen V1.34 parity gate: 685 passed.
- Full suite with two workers: 8,264 passed, 4 skipped; total package coverage
  was 99.59 percent.
- Ruff, Black, isort, strict touched-production typecheck, and diff checks all
  passed.

## Termination Condition

The phase is complete when start and resume are deterministic, idempotent, and
fail closed on drift; the same render cannot be replaced after a terminal
result; all repository gates are green; and one non-stacked PR is ready for
CODEOWNER review.
