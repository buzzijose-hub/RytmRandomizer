# Plan Requirements — RytmRandomizer

**Status:** Required for every plan that touches `rytm_randomizer/`, `tests/`, or `Scripts/`.
**Scope:** This document is the canonical contract. Any `docs/*PLAN*.md` (manual or auto-generated) that proposes code changes must either satisfy these requirements per workstream or explicitly document why a requirement does not apply (with a one-line rationale).
**Authority:** This file is the single source of truth. If `docs/SIMPLIFICATION_PLAN.md` and this file ever disagree, this file wins.
**Owner:** Updated by any PR that demonstrably uncovers a new gated requirement (see "How to update" at the bottom).

---

## Why this exists

The cleanup batch (PRs #22–#28) and the in-flight simplification plan converged on the same set of non-negotiable gates. Re-deriving them per plan wastes effort and risks drift. This file lifts them out of any one plan so every future contributor — human or agent — inherits them automatically.

When this file is updated, every open plan PR is expected to rebase and re-validate against the new requirements.

---

## The hard gates (apply per workstream, no exceptions)

A workstream does not reach `pr_open` (i.e. cannot call `gh pr create`) until **every gate below** passes locally. CI failures in any gate auto-revert the last commit and re-enter the implementation phase.

### Gate 1 — Branch coverage on touched files: **100%**

```powershell
$touched = git diff --name-only origin/<base>...HEAD -- 'rytm_randomizer/*.py'
$cov_args = $touched | ForEach-Object { "--cov=$($_ -replace '/', '.' -replace '\.py$','')" }
pytest @cov_args --cov-branch --cov-fail-under=100 --cov-report=term-missing
```

- Branch (not line) coverage. Catches `if resolved_bounds is None` and `if depth == 0` corners that the duck-typed boundaries currently let slip.
- Applies to **touched files only**. The whole-package floor in `.coveragerc` is a separate ratchet; this gate is stricter and per-WS.
- A gap re-spawns `tdd-guide` with the missing-branch report. Max 2 retries before escalating to `architect`.
- `# pragma: no cover` requires a one-line justification comment pointing at either `docs/ARCHITECTURE.md` §8 (parity API) or a specific `docs/SIMPLIFICATION_RUN_LOG.md` incident.

### Gate 2 — V1.34 parity fixtures byte-identical

```powershell
pytest tests/test_engines_pad*.py tests/test_group_runner.py tests/test_scene_runner.py
```

- All 505 JSON fixtures in `tests/fixtures/v134_parity/` byte-identical.
- The orchestrator **never** sets `PARITY_CAPTURE_MODE=1` in any WS — capture is a deliberate, separate workstream by itself.
- The 11 parity-API symbols in `docs/ARCHITECTURE.md` §8 are untouchable; any plan proposing to remove one of them must include a parity-layer change as a sibling WS.

### Gate 3 — Lint / format / type clean

```powershell
python -m ruff check .
python -m black --check .
python -m isort --profile black --check-only .
python -m pyright --strict <touched paths>
```

- `ruff` rule packs at minimum: `E,F,B,S,SIM,UP,C4,PLR,ERA,ARG`. `B904` (raise-from in except) is **always on** — no opt-out.
- `black` `target-version` is pinned to the CI matrix (`py39, py310, py311` only — `py312`/`py313` excluded per the PR #28 lesson).
- `pyright --strict` on touched paths, not the whole package (whole-package pyright is a separate future workstream).

### Gate 4 — Dead-code purge clean

Runs before Gate 1 (coverage gate). Catches dead code so it doesn't get tested into permanence.

```powershell
python -m vulture $touched --min-confidence 80
python -m ruff check --select F401,F811,F841,ARG001,ARG002,ERA001 $touched
```

- Vulture clean at confidence 80; borderline cases re-run at 60 and require a `# vulture: ignore` + parity-API §8 reference if kept.
- Zero commented-out code, zero unused imports, zero assigned-but-unused locals.
- Whole-package sweep (`vulture --min-confidence 70` on `rytm_randomizer/`) runs in a dedicated sweep WS once per plan.

### Gate 5 — Documentation update

The `everything-claude-code:doc-updater` agent runs **before** PR open, not after merge.

- `docs/STATUS.md` "Recent Cleanup" entry committed in the same PR. **No exceptions.**
- `docs/ARCHITECTURE.md` updated if the WS touches a documented boundary (Protocols, registries, subpackages, the parity API surface).
- `docs/CODEMAPS/*` updated if the WS adds new top-level modules.
- Cross-links resolve: `grep -rE '\]\([^)]+\)' docs/ .claude/ | grep -v http` returns no broken paths.

### Gate 6 — Type-system hygiene (Pattern-Review-WS-S1 findings, made permanent)

Lifted from the holistic pattern review of 2026-05-18. Made permanent because the patterns recur across every new module:

| Rule | Enforcement |
|---|---|
| No new `Sender = Any` or equivalent module-level type aliases that resolve to `Any`. | `tests/architecture/test_no_any_escape_hatches.py` greps for `^\s*\w+\s*=\s*Any\s*$` outside the modules WS-S1 is explicitly refactoring. |
| Every new module boundary uses a `Protocol` (with `@runtime_checkable` when `isinstance` is needed), never an ABC. | Code review by `python-reviewer`; ABCs are not banned globally, but new boundaries must justify the choice in the module docstring. |
| Every new record-shaped value is a `@dataclass(frozen=True)` or `TypedDict`. No new `Mapping[str, Any]` DTOs at module boundaries. | `python-reviewer` flags any new `Mapping[str, Any]` parameter in a public function signature. |
| `raise X(...) from exc` is mandatory inside `except` blocks. | `ruff B904` always on. Today only 2 of N translation sites comply; new code must comply. |
| `from __future__ import annotations` at the top of every new module. | Project convention; `ruff` rule via `--select FA100`. |

### Gate 7 — Observability adoption (Pattern-Review-WS-S9 findings, made permanent)

Every module that performs a **state transition**, **sends a CC**, or **makes a guardrail decision** must:

1. Obtain `_logger = get_logger(__name__)` at module level.
2. Emit a structured `_logger.debug` (or `info`/`warning`/`error` per severity) per decision, with `extra={...}` payload containing at least: the decision name, the inputs, the outcome.
3. Use `@trace` (from `observability.tracing`) on any function whose execution time is operator-relevant (e.g. "this scene = N CC sends").
4. Increment the appropriate `observability/metrics.py` counter (when introduced by WS-S9).
5. Chain to `raise X from exc` so the trace span captures the cause.

Enforcement: `tests/architecture/test_observability_adoption.py` walks `rytm_randomizer/engines/`, `rytm_randomizer/randomization.py`, `rytm_randomizer/scene_runner.py`, `rytm_randomizer/group_runner.py`, `rytm_randomizer/behavior_*.py`, `rytm_randomizer/guardrails/` and fails if any module performs a decision-shaped operation without a logger and a per-decision log line.

Blocked-by-guardrail sends are **never silent** — a `clamped is None` branch always emits `_logger.debug("guardrail_block", extra={...})`.

The `observability/` library itself (`logging.py`, `tracing.py`, `errors.py`, future `metrics.py`) is already world-class — this gate enforces *adoption on the hot path*, not redesign of the library.

### Gate 8 — Test hygiene

- Tests reuse fixtures from `tests/conftest.py` and `tests/_parity_worker.py`. **Do not** redefine `RecordingOut`, `_FakeMessage`, or `_install_fake_mido` per file. The cleanup batch found these duplicated across `tests/test_engines_pad{1,2,3,4}.py`.
- New tests named to communicate intent: `test_<unit>_<behavior>_when_<condition>`.
- Test files mirror source structure: `tests/test_X.py` ↔ `rytm_randomizer/X.py` (or `tests/<subpackage>/test_X.py` for subpackaged sources).
- `unittest.mock.patch` is the exception, not the rule. Manual fakes (`MockMidiSender`) are preferred for hardware-shape behavior.

### Gate 9 — Module-organization hygiene

- **New top-level modules require architect sign-off.** Default home for a new concept is a subpackage. The PR #21 lesson: 33 new top-level files is not a refactor, it's a flood.
- Subpackages that exist and should grow when relevant: `data/`, `engines/`, `guardrails/`, `observability/`, `state/`, `style_analysis/`. New subpackages need a one-line `__init__.py` docstring stating their purpose.
- If a plan adds more than 3 new top-level modules, it must justify each in the plan body or relocate them into a subpackage.

---

## How a plan declares conformance

Every plan PR must include, in its body, a checklist confirming each gate:

```markdown
## Plan-requirements conformance

Per docs/PLAN_REQUIREMENTS.md, this plan commits to:

- [x] Gate 1 (100% branch coverage on touched files) — applies to all WS.
- [x] Gate 2 (V1.34 parity fixtures byte-identical) — applies to all WS.
- [x] Gate 3 (lint/format/type clean) — applies to all WS.
- [x] Gate 4 (dead-code purge) — per-WS step + dedicated sweep WS.
- [x] Gate 5 (docs updated before PR open) — `doc-updater` is mandatory phase 9.
- [x] Gate 6 (type-system hygiene) — Protocols + frozen dataclasses, no `Any`.
- [x] Gate 7 (observability adoption) — every hot-path module logs + traces.
- [x] Gate 8 (test hygiene) — shared fixtures, intent-named tests.
- [x] Gate 9 (module-organization hygiene) — subpackages by default.

Exceptions (with rationale):
- (none, or list with one-line rationale each)
```

Plans that omit this checklist are not approved.

---

## How to update this file

This document is itself maintained under the same gates. Updates land via a PR that:

1. Adds the new rule with an enforcement mechanism (CI check, lint rule, architecture test, or reviewer protocol).
2. Cites the run-log entry, PR, or incident that demonstrates the rule is needed.
3. Updates `tests/architecture/test_plan_requirements_referenced.py` so every `docs/*PLAN*.md` is greppable for "Per docs/PLAN_REQUIREMENTS.md".
4. Updates `.claude/CLAUDE.md` if the rule affects every-session agent behavior (not just specific plans).

The file is **append-only-by-default** — gates are removed only when their underlying issue is structurally impossible (e.g. the dead-code purge gate could relax if the language gained native dead-code detection). Loosening a gate requires the same kind of post-mortem evidence that tightening one does.

---

## Cross-references

- `docs/SIMPLIFICATION_PLAN.md` — the current in-flight plan; first plan governed by this file.
- `docs/ARCHITECTURE.md` §8 — the V1.34 parity API surface (untouchable).
- `docs/STATUS.md` — append entries for every cleanup that lands.
- `.claude/skills/learned/` — reusable agent skills extracted from past runs.
- `.claude/rules/` — agent-runtime rules (separate from plan-time rules); see `parity-fixture-discipline.md`, `coverage-gate-100pct.md`, `cascade-merge-pattern.md` when WS-L lands.
- `.coveragerc` — the package-wide coverage ratchet (currently 87% floor; targeted to ratchet to 100% as part of WS-S8).
- `pyproject.toml [tool.ruff]` + `[tool.black]` — the enforcement config for Gate 3.
