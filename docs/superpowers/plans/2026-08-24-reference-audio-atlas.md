# Reference Audio Atlas

> Status: implementation and local verification complete; review pending

## Goal

Add a passive, resource-bounded way to analyze a long recording or DJ mix as
multiple short windows, select a small set of musically diverse moments, and
reuse the existing Analog Four patch-genome and reference-style blueprint
builders for each selected moment.

The result is an evidence atlas, not a claim that the system has identified an
artist's exact equipment, patch, or production process.

## User Outcome

An operator can run one local command against a long audio file and receive a
deterministic JSON or text report containing:

- the bounded windows that were analyzed;
- the moments selected for diversity and their source time ranges;
- the existing four-candidate A4 patch genome for each selected moment;
- the existing Rytm/A4 reference-style blueprint for each selected moment;
- explicit safety, provenance, and non-forensic interpretation statements.

This advances the project from one short reference at a time toward mix-scale
Reference -> Discovery work without requiring a studio or touching hardware.

## Scope

- Add bounded offset/duration extraction to the existing lazy audio extractor.
- Add a pure reference-audio-atlas domain module under `style_analysis/`.
- Select moments deterministically by mean-feature distance with stable
  earliest-window tie breaking.
- Reuse `build_analog_four_patch_genome` and
  `build_reference_style_blueprint`; do not create parallel inference systems.
- Register one passive `reference-audio-atlas-report` command.
- Add focused tests and update the user, CLI, status, architecture, and diagram
  documentation.

## Non-Goals

- No MIDI enumeration, port open, or MIDI/SysEx transmission.
- No live device adapter or armed application path.
- No claim of forensic patch reconstruction or artist attribution.
- No unbounded full-file decode into memory.
- No model training, source separation, render comparison, or automatic
  hardware audition in this change.
- No changes to V1.34 parity fixtures or hardware-pinned dependencies.

## Architecture

```text
audio path
  -> duration probe
  -> bounded sequential windows
  -> existing FeatureReport extraction
  -> deterministic diversity selection
  -> existing A4 patch genome + reference-style blueprint
  -> passive text/JSON report
```

The atlas owns orchestration and selection only. Feature measurement, patch
candidate construction, and style blueprint construction remain in their
existing modules.

## Resource And Determinism Contract

- Window duration is constrained to 5-120 seconds.
- At most 240 windows may be scanned.
- At most 8 moments may be selected.
- Windows are decoded and processed sequentially.
- Selection is deterministic for identical numeric features and configuration.
- `analysis_id` excludes timestamps, source paths, and evidence hashes so the
  same analysis remains stable across locations and runs.
- Per-window FeatureReport evidence hashes remain intact in embedded genome and
  blueprint evidence.

## Workstream Graph

```text
WS-A extractor window API
  -> WS-B atlas domain + selection
  -> WS-C passive report + CLI registration
  -> WS-D tests + documentation + verification
```

These nodes are one tightly coupled behavioral contract. They execute in one
isolated worktree and one direct PR because separate branches would be stacked
and would duplicate fixtures and integration edits. Independent read-only
audits and verification commands may run in parallel only when that does not
increase local resource pressure.

## Worktree Assignment

- Branch: `codex/reference-audio-atlas`
- Worktree: `.worktrees/reference-audio-atlas`
- Base: `origin/modularize-v1.34`
- Integration shape: one direct, non-stacked PR
- Existing audio-patch refinement PRs and worktrees are read-only context and
  must not be rewritten.

## Self-Driving And Recovery

- No human decision is required for implementation or passive verification.
- Use one pytest worker and avoid high-load local processes because the host has
  recently restarted under load.
- Each test phase is independently restartable; no generated state is required
  to resume.
- A failure stops only the failing verification phase. Diagnose, patch, and
  rerun the narrowest relevant command before broader verification.
- Termination condition: exact staged diff audited, required low-load gates
  green, one commit pushed, direct PR opened, and reviewer requested.

## Maintainability And Reuse Audit

- The existing librosa-backed extractor remains the sole audio measurement
  implementation.
- The existing FeatureReport remains the sole numeric audio evidence contract.
- The existing A4 patch-genome builder remains the sole audio-to-A4 candidate
  inference path.
- The existing reference-style blueprint remains the sole cross-device style
  interpretation path.
- The existing `CliCommand` registry remains the passive command boundary.
- New dataclasses are frozen and new callable seams are Protocol-typed.
- No `Any`, environment variable, top-level package module, or eager MIDI
  dependency is introduced.

## Verification

Run with `PYTEST_XDIST_AUTO_NUM_WORKERS=1` where xdist is active:

1. Focused atlas, report, and extractor-window tests with `-n 0`.
2. Targeted Ruff, Black, and isort over touched Python files.
3. Architecture tests with `-n 0`.
4. Touched-file strict type checking and statement/branch coverage at 100%.
5. V1.34 parity through the established mechanical review command.
6. Full suite with one worker.
7. Full-repository Ruff, Black, and isort checks.
8. `git diff --check`, exact staged-path audit, and passive import/CLI checks.

No verification step may enumerate or open MIDI ports.

Fresh low-load results from the isolated contribution worktree:

- Focused atlas, report, CLI, and passive-safety suite: 573 passed.
- Touched production modules: 100 percent statement and branch coverage.
- Architecture suite: 751 passed.
- Frozen V1.34 parity suite: 685 passed; fixtures unchanged.
- Full suite: 7,939 passed, 4 skipped.
- Full-package coverage: 99.57 percent total and 99.20 percent branch; the
  repository-wide 100 percent branch helper therefore remains red on existing
  unrelated gaps, while this contribution's touched modules are fully covered.
- Ruff, Black, isort, strict touched-file Pyright, and `git diff --check` pass.

## Plan Requirements Conformance

- [x] Gate 1 - New production branches receive 100% touched-file statement and branch coverage.
- [x] Gate 2 - V1.34 parity fixtures remain byte-identical and are not regenerated.
- [x] Gate 3 - Lint, format, and strict touched-file type checks are required.
- [x] Gate 4 - Dead-code checks run through the repository review gate.
- [x] Gate 5 - README, CLI, style-analysis, status, and plan docs are updated.
- [x] Gate 6 - Protocols and frozen dataclasses are used; no `Any` escape hatch is added.
- [x] Gate 7 - The path is bounded and fail-closed; existing report diagnostics are reused.
- [x] Gate 8 - Tests are intent-named and mirror the source behavior.
- [x] Gate 9 - New production code stays inside existing subpackages.
- [x] Gate 10 - CLI dispatch uses the existing `CliCommand` registry.
- [x] Gate 11 - Shared fixtures are used only when genuinely shared; local helpers stay local.
- [x] Gate 12 - Module constants use `Final` and dataclasses are frozen.
- [x] Gate 13 - No environment variable is introduced.
- [x] Gate 14 - Reuse and maintainability are audited before and after implementation.
- [x] Gate 15 - Learning is captured in durable architecture and safety documentation; add a reusable skill only if verification reveals a novel pattern.
- [x] Gate 16 - Work executes autonomously in an isolated worktree and lands as one non-stacked PR; the single-workstream choice is justified above.
- [x] Gate 17 - Existing extraction, genome, blueprint, and CLI abstractions are reused.
- [x] Gate 18 - Architecture docs, diagrams, command surfaces, and module counts are refreshed.

## Learning Capture

The durable lesson is architectural: long-form audio support does not require a
second inference engine. A bounded window scheduler plus deterministic moment
selection can turn the existing short-reference pipeline into a mix-scale
discovery surface while preserving provenance, resource ceilings, and passive
hardware safety.
