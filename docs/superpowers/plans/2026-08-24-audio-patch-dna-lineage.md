# Audio-to-Patch DNA Lineage Audit

> Status: in-flight (implementation complete; review pending)

## Goal

Add a passive, deterministic audit that explains how each normalized audio
measurement contributes to each inferred Analog Four parameter in an
Audio-to-Patch DNA workspace.

The audit must distinguish authored creative-direction metadata from measured
evidence. It must never describe a static direction hint as acoustic closeness
or claim that an inferred patch matches the reference until rendered audio has
been captured and compared.

## User Outcome

For every one of the eight Audio-to-Patch DNA candidates, the audit records:

- each measured feature transformation from the shared source analysis;
- the exact canonical inference equation used for every audio-driven gene;
- each weighted term, feature product, contribution, multiplier, and clamp;
- the resulting screen and MIDI values already present in the candidate;
- whether the recomputed result exactly matches the generated patch;
- which genes come only from the deterministic template;
- an explicit `render_required` acoustic-verification boundary.

## Scope

- Expose the existing Analog Four inference feature-map and equation evaluator
  as typed public helpers without changing their behavior.
- Add frozen lineage dataclasses under `style_analysis/`.
- Build stable JSON-ready and Markdown representations.
- Reconcile every canonical inferred parameter against the generated patch.
- Add focused determinism, formula, boundary, and safety tests.
- Update durable style-analysis documentation.

## Non-Goals

- No audio decode, file I/O, MIDI enumeration, hardware access, or SysEx.
- No new inference equations or changes to generated patch values.
- No acoustic-fidelity score, artist attribution, or forensic reconstruction.
- No render capture or optimizer; those remain a later closed-loop phase.
- No CLI changes, V1.34 fixture changes, or hardware dependency changes.

## Architecture

```text
existing AudioPatchDnaWorkspace
  -> source/candidate feature deltas
  -> existing canonical A4 inference specs
  -> existing canonical feature-map + evaluator
  -> recomputed expected AnalogFourPatchValue
  -> exact reconciliation with generated candidate genes
  -> passive JSON/Markdown lineage audit
```

The generated patch remains the authoritative result. The lineage audit is a
read-only proof layer over the existing workspace and canonical inference fact
table.

## Worktree Assignment

- Branch: `codex/audio-patch-dna-lineage`
- Worktree: `.worktrees/audio-patch-dna-lineage`
- Base: `origin/modularize-v1.34`
- Integration shape: one direct, non-stacked PR
- PR #230 and PR #231 remain independent and unmodified.

## Resource And Safety Contract

- Run focused tests with one worker.
- Do not decode audio or start native-analysis child processes in verification.
- Do not import a MIDI backend, enumerate ports, construct a provider, or send
  MIDI/SysEx.
- Use synthetic typed workspace fixtures for deterministic tests.
- Stop broad verification if host stability degrades; focused evidence remains
  independently restartable.

## Verification

1. Focused lineage and existing Audio-to-Patch DNA tests with `-n 0`.
2. Touched-file statement and branch coverage at 100 percent.
3. Strict touched-file Pyright plus Ruff, Black, and isort.
4. Architecture suite with one worker.
5. Frozen V1.34 parity through the established review command.
6. Full suite with one worker only if the focused gates remain stable.
7. Exact diff, staged-path, and passive-import audits.

## Verification Evidence

- Focused lineage, Audio-to-Patch DNA, and A4 inference regression: 55 passed.
- Public package-surface regression after adding lineage exports: 48 passed.
- Touched production statement and branch coverage: 100 percent across 533
  statements and 88 branches.
- Architecture suite: 750 passed with one existing short-name warning.
- Frozen V1.34 parity: 685 passed.
- Full repository suite, one worker: 7,899 passed and 4 skipped.
- Strict touched-file Pyright: 0 errors and 0 warnings.
- Ruff, Black, isort, touched dead-code scan, and `git diff --check`: clean.
- Passive-boundary audit: no MIDI backend import, provider construction, port
  access, or send call in the new lineage surface.

## Plan Requirements Conformance

- [x] Gate 1 - New production branches require 100% touched-file coverage.
- [x] Gate 2 - V1.34 parity fixtures remain unchanged.
- [x] Gate 3 - Lint, formatting, and strict typing are required.
- [x] Gate 4 - Dead-code checks are included in review.
- [x] Gate 5 - Durable style-analysis documentation is updated.
- [x] Gate 6 - Frozen dataclasses and explicit types are used; no `Any`.
- [x] Gate 7 - Formula reconciliation fails closed on mismatch.
- [x] Gate 8 - Tests describe formula, boundary, and safety intent.
- [x] Gate 9 - New code stays in the existing `style_analysis` subpackage.
- [x] Gate 10 - No command or dispatch surface is added.
- [x] Gate 11 - Fixtures remain local unless genuinely shared.
- [x] Gate 12 - Module constants use `Final` and dataclasses are frozen.
- [x] Gate 13 - No environment variable is introduced.
- [x] Gate 14 - Existing inference abstractions are reused and audited.
- [x] Gate 15 - The evidence-boundary lesson is captured in documentation.
- [x] Gate 16 - Work lands as one direct non-stacked PR.
- [x] Gate 17 - Canonical specs, values, and workspace models are reused.
- [x] Gate 18 - Architecture-facing documentation is refreshed as needed.
