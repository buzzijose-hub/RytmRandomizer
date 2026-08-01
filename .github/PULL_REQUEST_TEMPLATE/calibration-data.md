<!--
Tiered template: CALIBRATION-DATA class.
For PRs whose diff is data-only calibration content — guardrail profiles,
calibration tables, captured measurement JSON under data/ or docs/ — with
NO runtime code change. Select it by appending
`?template=calibration-data.md` to the compare/PR-creation URL.
If the PR touches any rytm_randomizer/*.py runtime behavior, use the full
default template (.github/PULL_REQUEST_TEMPLATE.md) instead.
-->

# Summary

<!-- One paragraph: what calibration data does this PR add/update, and where did it come from (capture session, hardware study, analysis run)? -->

## Data provenance

<!-- Source of the data: device, firmware version, capture command, analysis skill (DataAnalysisGuardrails / MusicLibraryGuardrails), date. -->

## Plan-requirements conformance (calibration-data tier)

Per [`docs/PLAN_REQUIREMENTS.md`](../../docs/PLAN_REQUIREMENTS.md). Load-bearing gates for this class — mark each `[x]`:

- [ ] **Gate 1** — 100% branch coverage on touched files (data tables consumed via `data/` re-exports are exercised by the drift-guard tests).
- [ ] **Gate 2** — V1.34 parity untouched: `tests/fixtures/v134_parity/` has zero diff and `PARITY_CAPTURE_MODE` was never set.
- [ ] **Gate 3** — lint clean (ruff + black `--target-version=py311` + isort `--profile black`).
- [ ] **Gate 5** — `docs/STATUS.md` line added describing the new/updated calibration data.
- [ ] **Gate 8** — test hygiene (`test_<unit>_<behavior>_when_<condition>` naming for any new drift-guard tests).
- [ ] **Gate 11** — shared fixtures (any new fixture lives in `tests/conftest.py`, not duplicated).

Remaining gates, pre-marked for this class:

- [ ] Gate 4 — N/A: data-only calibration class
- [ ] Gate 6 — N/A: data-only calibration class
- [ ] Gate 7 — N/A: data-only calibration class
- [ ] Gate 9 — N/A: data-only calibration class
- [ ] Gate 10 — N/A: data-only calibration class
- [ ] Gate 12 — N/A: data-only calibration class
- [ ] Gate 13 — N/A: data-only calibration class
- [ ] Gate 14 — N/A: data-only calibration class
- [ ] Gate 15 — N/A: data-only calibration class
- [ ] Gate 16 — N/A: data-only calibration class
- [ ] Gate 17 — N/A: data-only calibration class
- [ ] Gate 18 — N/A: data-only calibration class

<!-- If any pre-marked gate DOES apply to your diff, replace its N/A line with a real [x]/justification — the pre-marks assume a pure data-only diff. -->

## Strict rules — non-negotiables

- [ ] **All six strict rules hold** — no hardware in tests; lazy MIDI imports; `mido==1.3.3` / `python-rtmidi==1.5.8` untouched; passive default (`python -m rytm_randomizer.cli` opens no real port); no stacked PRs (base is `modularize-v1.34`); no `--no-verify`.
