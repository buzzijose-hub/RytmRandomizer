# Audio Reference Suitability

> Status: in-flight
>
> Implementation is complete; review is pending.

## Goal

Add a deterministic, passive decision layer between measured audio evidence
and patch/rhythm inference. The layer must say what the evidence can support,
retain every threshold used, and avoid treating artistic quality or artist
intent as measurable facts.

## Architecture

```text
AudioFeatureAnalysis
  -> explicit suitability checks
  -> four independent workflow outcomes
  -> deterministic next-workflow recommendation
```

The implementation belongs in `style_analysis/`, consumes only existing typed
measurement artifacts, and has no I/O or hardware dependency.

## Policy boundaries

- Focused timbre inference and rhythm interpretation are assessed separately.
- Note-specific synthesis requires resolved pitch plus confidence and stability.
- A saturated duration measurement routes to segmentation before patch DNA.
- Thresholds are versioned policy, not claims about objective audio quality.
- Missing evidence fails closed or remains explicitly limited.

## Verification plan

- Focused unit tests for every status and recommendation branch.
- 100% statement and branch coverage on touched production modules.
- Architecture and frozen V1.34 parity gates.
- Full suite with one worker to protect the studio PC.
- Strict touched-production typing and the repository lint trio.

## Verification evidence

- Focused suitability and public-surface tests: 63 passed.
- Composed audio-pipeline tests: 196 passed.
- Touched production coverage: 100% statements and branches
  (171 statements, 36 branches).
- Architecture gate: 750 passed.
- Frozen V1.34 parity gate: 685 passed.
- Full repository suite: 7,905 passed, 4 skipped.
- Strict touched-production Pyright: 2 modules, 0 errors, 0 warnings.
- Ruff, Black, and isort: passed.
- Hardware safety: no MIDI ports were enumerated, opened, or written.

## Maintainability audit

1. **Duplication:** one shared check and workflow payload path.
2. **Complexity:** four small lane evaluators and one recommendation reducer.
3. **Naming:** workflow, status, and recommendation are closed enums.
4. **Typing:** frozen dataclasses, TypedDict payloads, and no `Any`.
5. **Side effects:** pure functions only; no import-time work.
6. **Observability:** all decisions retain checks, reasons, and next actions.
7. **Compatibility:** no existing behavior or frozen parity output changes.
8. **Documentation:** policy boundaries and exact thresholds are public.

## Gate conformance

All 18 plan gates apply. The change is one logical direct-base contribution,
adds no top-level package module, changes no dependency, touches no hardware
boundary, regenerates no frozen fixture, and will not be marked review-ready
until focused coverage, architecture, parity, full-suite, typing, and lint
evidence are green.
