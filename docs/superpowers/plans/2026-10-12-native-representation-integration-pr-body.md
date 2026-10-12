# Summary

Continue the bounded offline reference-sound workflow for A4 MKII and Rytm MKII
with parameter-specific native representation and passive working-KIT inspection.
Exact source bytes, scope/locks, candidate identities, local favorites and
recording comparison remain distinct from instrument application and recovery.
This is reference-to-discovery, not forensic reconstruction or a trained renderer.

## What changed

- Separate A4 F1 and ordinary Rytm LFO Depth contracts, literal boundary/order/
  collision witnesses and canonical u14 reuse. Native, display and wire values
  remain distinct; arithmetic models do not grant output authority.
- Validated indexed52 versus working58 responses without changing9-byte/MSB/
  2410-body coordinates or raw identities. Working frames remain inspect-only.
- Raw indexed-source validation protects generation, show-bank adoption/import,
  saved recapture and preflight, including all-locked candidates. Specific
  refusal text, fingerprint, journal/log and fixed counter survive each boundary.
- Operator labels/loss disclosure do not rewrite v1 records or sampling bounds.
  Genuine pre-change e30 mutable/protected favorites now verify exact old IDs,
  bytes, labels, reasons and scratch exports. Existing frozen corpora are unchanged.
- Reproduced integer-zero depth persistence failure repaired through the shared
  numeric validator before canonical publication; booleans remain refused.
- Six-file comparison reports every raw/body difference and repeat/save/recovery
  check. It performs no query; supervised acquisition remains a separate gate.
- Audio-enabled package workflow and existing guarded Rytm scope are retained.
  A4/BOTH, CYRide SRC, paired precision, unsaved synchronization and automatic
  restore remain held. Local favorites/export are not hardware SAVE or recovery.

## Why this matters

The operator can inspect legal native words and precision loss without changing
favorite identity or mistaking working-RAM/body equality for saved-state proof.
The next studio session has one bounded F1 experiment, not another broad manual
calibration sweep. Physical observations and protected approval remain pending.

## Test plan

Final source658c8f9f:11813 passed/5skipped/6warnings824.40s; all76 touched
production files100%line/branch, project99.42%pure-branch with99%floor unchanged.
Earlier486501dd's acceptance is separately retained. Focused review composition
24passed; latest boundary/taxonomy/u14 cases271passed. Frontend1294/81files/all
fourcoverage100%; pinned Pyright all76 modules zero errors/warnings. Whole
Ruff/Black/isort/Vulture80 clean. New Windows package/native acceptance and fresh
published CI remain pending and are not marked satisfied.

- [x] Local pytest passes (full suite).
- [x] `tests/architecture/` passes.
- [x] Lint trio (ruff + black + isort) clean.
- [x] Coverage stays >=95% pure-branch.
- [x] 685/685 V1.34 parity items byte-identical.
- [x] No new dead code (vulture --min-confidence 80).
- [ ] Exact-source new Windows package and affected native journeys pass.
- [ ] Fresh CI/required-checks complete on the published source.
- [ ] Protected human approval; latest Eddie review remains October3 CHANGES_REQUESTED.

## Plan-requirements conformance

Per [`docs/PLAN_REQUIREMENTS.md`](https://github.com/buzzijose-hub/RytmRandomizer/blob/codex/studio-evidence-handoff/docs/PLAN_REQUIREMENTS.md).

- [x] **Gate 1** — 100% branch coverage on touched files; project ≥95% pure-branch.
- [x] **Gate 2** — V1.34 parity byte-identical (505 goldens / 685 pytest items).
- [x] **Gate 3** — lint clean and strict Pyright clean on every touched production module (`python scripts/typecheck_touched.py`).
- [x] **Gate 4** — no new dead code (vulture --min-confidence 80).
- [x] **Gate 5** — docs updated (`README.md`, `CONTRIBUTING.md`, `docs/STATUS.md`, relevant `docs/` reflect the change).
- [x] **Gate 6** — type-system hygiene (Protocol over ABC, `Final` constants, no bare `Any`).
- [x] **Gate 7** — observability adoption (hot paths call `get_metrics().record_*`).
- [x] **Gate 8** — test hygiene (`test_<unit>_<behavior>_when_<condition>` naming; shared fixtures in `tests/conftest.py`).
- [x] **Gate 9** — module-organization hygiene (subpackages over flat top-level).
- [x] **Gate 10** — string-literal dispatch hygiene (consume `data/modes.py` constants; allowlist drained).
- [x] **Gate 11** — shared fixtures (canonical definitions in `tests/conftest.py`).
- [x] **Gate 12** — `Final` constants on module-level constants.
- [x] **Gate 13** — env var docs (every read env var documented in `docs/LOCAL_DEV_TOOLING_NOTES.md` or a relevant doc).
- [ ] **Gate 14** — maintainability review (timing tracked, complexity bounded).
- [x] **Gate 15** — learning capture (extract `.claude/skills/learned/` + `.claude/rules/` where applicable).
- [ ] **Gate 16** — execution shape (cascade-merge for autonomous multi-WS; no stacked PRs).
- [x] **Gate 17** — abstraction reuse: every new module/class surveyed against the existing-abstraction catalog (`Device` Protocol, `senders/`, `snapshot/envelope`, `cli_registry`, `data/`, `observability/metrics`, ...); no reimplementation; net-new shapes justified.
- [x] **Gate 18** — architecture-doc + diagram freshness: `docs/ARCHITECTURE.md` + `docs/ARCHITECTURE_DIAGRAMS.md` updated for any architecture-surface change; quoted counts re-verified.

Historical PR254 Gate14 retrospective-baseline and Gate16 crew/execution
deviations remain unresolved and must stay unchecked. The current increment's
pre-code audit, timed bounded verification and isolated direct-base integration
do not retroactively certify earlier work or bypass protected human approval.

## Strict rules — non-negotiables

- [x] **No hardware in tests** — no test opens a real MIDI port; no test mutates a connected device.
- [x] **Lazy MIDI imports** — `mido` and `python-rtmidi` imported only inside `real_midi_adapter.py` / `mido_provider.py`.
- [x] **Hardware-pinned packages** — `mido==1.3.3` and `python-rtmidi==1.5.8` not bumped.
- [x] **Passive default** — `python -m rytm_randomizer.cli` does not open a real port.
- [x] **No stacked PRs** — this PR's base is `modularize-v1.34` (or the integration target), not another open PR's head.
- [x] **No `--no-verify`** — pre-commit hooks were not bypassed.

## Plan document

[Native integration plan](https://github.com/buzzijose-hub/RytmRandomizer/blob/codex/studio-evidence-handoff/docs/superpowers/plans/2026-10-12-native-representation-integration.md).
The earlier reference-sound plan/delivery remains preserved and separately accounted.

## Reviewer notes

Consolidated dimensional review will be posted separately. Static research,
synthetic audio, fixtures and software tests are not physical validation.
Working-state synchronization, instrument recordings/application/save/reload,
manual recovery and show rehearsal remain pending. No protected merge is requested
without the required approval; no FULL FEATURE COMPLETE or show-ready claim.
