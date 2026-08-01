<!-- Tiered templates exist for narrow PR classes: data-only calibration PRs may use `?template=calibration-data.md` and report/docs-only PRs `?template=docs-report.md` (both under .github/PULL_REQUEST_TEMPLATE/) appended to the compare URL. Everything else uses this full template. -->

# Summary

<!-- One paragraph: what does this PR do and why? Link the issue / Slack thread / past PR that surfaced it. -->

## What changed

<!-- Bullet list of the concrete changes. File paths welcome. -->

-

## Why this matters

<!-- The motivation — often a constraint, deadline, incident, or design decision. Skip if the Summary already covers it. -->

## Test plan

<!-- How was this verified? Commands run, expected outputs, manual steps, hardware checks. Be explicit. -->

```bash
# Example: paste actual commands you ran.
python -m pytest
python -m pytest tests/architecture/ -q
python scripts/typecheck_touched.py
python -m ruff check . && python -m black --check --target-version=py311 . && python -m isort --profile black --check-only .
```

- [ ] Local pytest passes (full suite).
- [ ] `tests/architecture/` passes.
- [ ] Lint trio (ruff + black + isort) clean.
- [ ] Coverage stays ≥95% pure-branch.
- [ ] 685/685 V1.34 parity items byte-identical (or fixtures regenerated with explicit approval — link below).
- [ ] No new dead code (vulture --min-confidence 80).
- [ ] CI matrix green on all 3 OSes (or known PR-event macOS-drop noted).

## Plan-requirements conformance

Per [`docs/PLAN_REQUIREMENTS.md`](../docs/PLAN_REQUIREMENTS.md) — every non-trivial PR must satisfy all 18 gates. Mark each `[x]`, or `[ ] N/A — <reason>`.

- [ ] **Gate 1** — 100% branch coverage on touched files; project ≥95% pure-branch.
- [ ] **Gate 2** — V1.34 parity byte-identical (505 goldens / 685 pytest items).
- [ ] **Gate 3** — lint clean and strict Pyright clean on every touched production module (`python scripts/typecheck_touched.py`).
- [ ] **Gate 4** — no new dead code (vulture --min-confidence 80).
- [ ] **Gate 5** — docs updated (`README.md`, `CONTRIBUTING.md`, `docs/STATUS.md`, relevant `docs/` reflect the change).
- [ ] **Gate 6** — type-system hygiene (Protocol over ABC, `Final` constants, no bare `Any`).
- [ ] **Gate 7** — observability adoption (hot paths call `get_metrics().record_*`).
- [ ] **Gate 8** — test hygiene (`test_<unit>_<behavior>_when_<condition>` naming; shared fixtures in `tests/conftest.py`).
- [ ] **Gate 9** — module-organization hygiene (subpackages over flat top-level).
- [ ] **Gate 10** — string-literal dispatch hygiene (consume `data/modes.py` constants; allowlist drained).
- [ ] **Gate 11** — shared fixtures (canonical definitions in `tests/conftest.py`).
- [ ] **Gate 12** — `Final` constants on module-level constants.
- [ ] **Gate 13** — env var docs (every read env var documented in `docs/LOCAL_DEV_TOOLING_NOTES.md` or a relevant doc).
- [ ] **Gate 14** — maintainability review (timing tracked, complexity bounded).
- [ ] **Gate 15** — learning capture (extract `.claude/skills/learned/` + `.claude/rules/` where applicable).
- [ ] **Gate 16** — execution shape (cascade-merge for autonomous multi-WS; no stacked PRs).
- [ ] **Gate 17** — abstraction reuse: every new module/class surveyed against the existing-abstraction catalog (`Device` Protocol, `senders/`, `snapshot/envelope`, `cli_registry`, `data/`, `observability/metrics`, ...); no reimplementation; net-new shapes justified.
- [ ] **Gate 18** — architecture-doc + diagram freshness: `docs/ARCHITECTURE.md` + `docs/ARCHITECTURE_DIAGRAMS.md` updated for any architecture-surface change; quoted counts re-verified.

## Strict rules — non-negotiables

Per [`CONTRIBUTING.md` § Strict rules](../CONTRIBUTING.md#strict-rules--non-negotiables) — confirm each:

- [ ] **No hardware in tests** — no test opens a real MIDI port; no test mutates a connected device.
- [ ] **Lazy MIDI imports** — `mido` and `python-rtmidi` imported only inside `real_midi_adapter.py` / `mido_provider.py`.
- [ ] **Hardware-pinned packages** — `mido==1.3.3` and `python-rtmidi==1.5.8` not bumped.
- [ ] **Passive default** — `python -m rytm_randomizer.cli` does not open a real port.
- [ ] **No stacked PRs** — this PR's base is `modularize-v1.34` (or the integration target), not another open PR's head.
- [ ] **No `--no-verify`** — pre-commit hooks were not bypassed.

## Plan document

<!-- For PRs >2k LOC, >30 files, ≥2 workstreams, new architectural surface, or V1.34-parity changes, link the plan doc. -->

Plan doc (if applicable): `docs/superpowers/plans/YYYY-MM-DD-<short-slug>.md`

## Reviewer notes

<!-- Anything reviewers should know that isn't obvious from the diff (e.g. "this commit is the byte-identical refactor; the behavior change comes in commit 3"). -->

---

<!--
Reminder for AI-agent contributors (Claude Code, codex, etc.):
This template's checklist is mandatory. Do NOT omit gate checkmarks.
If a gate is N/A, write "[ ] Gate N — N/A: <reason>". Do not silently drop gates.
See `.claude/rules/pr-body-conformance-checklist.md` for the full rule.
-->
