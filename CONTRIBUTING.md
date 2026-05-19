# Contributing to RytmRandomizer

## Table of contents

- [Strict rules — non-negotiables](#strict-rules--non-negotiables)
- [Branching model](#branching-model)
- [Local development setup](#local-development-setup)
- [Cross-platform operation](#cross-platform-operation)
- [End-to-end contributor flow](#end-to-end-contributor-flow)
- [Verification gate](#verification-gate)
- [Linting and formatting — the exact rule set](#linting-and-formatting--the-exact-rule-set)
- [Plan requirements — the 16 gates every PR must satisfy](#plan-requirements--the-16-gates-every-pr-must-satisfy)
- [Test suite structure](#test-suite-structure)
- [Common contributor tasks](#common-contributor-tasks)
- [Skill catalog](#skill-catalog)
- [Preserve parity with the V1.34 reference](#preserve-parity-with-the-v134-reference)
- [Commit conventions](#commit-conventions)
- [PR bundling — one PR per logical change, not per commit](#pr-bundling--one-pr-per-logical-change-not-per-commit)
- [PR size guidance](#pr-size-guidance)
- [Plan documents — when and how](#plan-documents--when-and-how)
- [gh CLI quick reference](#gh-cli-quick-reference)
- [Data vs code](#data-vs-code)
- [Definition of done includes docs](#definition-of-done-includes-docs)
- [Architecture standard](#architecture-standard)
- [Hardware safety boundaries](#hardware-safety-boundaries)
- [Automated post-push code review](#automated-post-push-code-review)
- [Releasing](#releasing)

## Strict rules — non-negotiables

Every PR must satisfy ALL of these. If you cannot satisfy one, do not open the PR; coordinate with @buzzijose-hub.

1. **V1.34 parity** — 685/685 byte-identical JSON goldens under `tests/fixtures/v134_parity/`. Do not regenerate without explicit approval.
2. **Coverage ratchet** — ≥95% pure-branch coverage project-wide (enforced by `scripts/coverage_ratchet.py`).
3. **Architecture tests** — all 14 tests under `tests/architecture/` pass. Do not add to allowlists without justification in the PR body.
4. **Lint clean** — `ruff check`, `black --check --target-version=py311`, `isort --profile black --check-only` all clean. No exceptions; auto-fix locally before pushing.
5. **No hardware in tests** — no test opens a real MIDI port; no test mutates a connected device.
6. **Lazy MIDI imports** — `mido` and `python-rtmidi` are imported lazily inside `real_midi_adapter.py`. Never at module top-level. Enforced by `tests/architecture/test_no_side_effects.py`.
7. **Hardware-pinned packages** — `mido==1.3.3` and `python-rtmidi==1.5.8`. Do not bump.
8. **Passive default** — `rytm-randomizer` with no `--arm` flag must NEVER open a real port.
9. **No bare `Any`** — use `Protocol`, generic dataclasses, or explicit types. Enforced by `tests/architecture/test_no_any_escape_hatches.py`.
10. **No new top-level modules** — use a subpackage. Enforced by `tests/architecture/test_no_new_top_level_modules.py`.
11. **String-literal dispatch sites must consume `data/modes.py` constants** — the allowlist is drained. Enforced by `tests/architecture/test_no_string_literal_mode_dispatch.py`.
12. **No stacked PRs** — see [PR bundling](#pr-bundling--one-pr-per-logical-change-not-per-commit).
13. **Conformance checklist in PR body** — the 16 gates from [`docs/PLAN_REQUIREMENTS.md`](docs/PLAN_REQUIREMENTS.md), each marked `[x]` or `[ ] N/A — reason`.
14. **Docs updated** — `README.md`, this file, `docs/STATUS.md`, and any relevant `docs/` entries reflect the new reality (Gate 5).
15. **No `--no-verify`** — never skip pre-commit hooks. If a hook fails, fix the cause.

## Branching model

- `main` is the integration target. (The `main` branch is being created by a parallel workstream; until it lands, integration happens on the active modularization branch.)
- Do work on feature branches.
- Feature branches merge into the integration target via pull request — no direct pushes to the integration branch.

## Local development setup

```bash
# 1. Clone
git clone https://github.com/buzzijose-hub/RytmRandomizer.git
cd RytmRandomizer

# 2. Create a virtualenv (Python >=3.11 — see pyproject.toml)
python -m venv .venv

# 3. Activate (see cross-platform notes below)
# macOS / Linux:
source .venv/bin/activate
# Windows PowerShell:
.venv\Scripts\Activate.ps1

# 4. Install in editable mode with dev extras
pip install -e ".[dev]"

# 5. (Optional but recommended) install the pre-commit hooks
pre-commit install
```

**Linux only:** `python-rtmidi` (a hard dependency for the real-MIDI path) may not have a wheel; install ALSA headers first:

```bash
sudo apt-get install libasound2-dev
```

**Hardware pinning:** `mido==1.3.3` and `python-rtmidi==1.5.8` are pinned because they encode the exact byte-level MIDI wire format the Elektron Analog Rytm MK2 accepts. **Do not bump these versions**, even for CVE advisories, without coordinating with @buzzijose-hub. See `.claude/skills/learned/pip-audit-editable-install/SKILL.md` for the `pip-audit` policy on these pins.

## Cross-platform operation

The codebase runs on **Windows, macOS, and Linux**. CI exercises all three on `python 3.11`. Contributor pitfalls to avoid:

| Concern | Windows | macOS / Linux |
|---|---|---|
| Shell | PowerShell 5.1 (default) or `pwsh` | bash / zsh |
| Path separator | `\` literal; `/` accepted by Python | `/` only |
| Activate venv | `.venv\Scripts\Activate.ps1` | `source .venv/bin/activate` |
| Closeout check | `Scripts\closeout_check.ps1` | `python scripts/closeout_check.py` |
| Quick status | `Scripts\quick_status.ps1` | `python scripts/quick_status.py` (if absent, use `pytest -m fast`) |
| pytest invocation | `python -m pytest` | `pytest` |
| Default file encoding | UTF-16 LE (PowerShell `Out-File`) | UTF-8 |
| MIDI backend (real port) | `python-rtmidi` wheel | `python-rtmidi` + ALSA on Linux |

**PowerShell-specific gotchas** (from `.claude/skills/python-on-windows/SKILL.md`):

- `&&` chaining is **not available** in Windows PowerShell 5.1. Use `; if ($?) { ... }` instead.
- When writing files other tools will read, pass `-Encoding utf8` to `Out-File` / `Set-Content` (default is UTF-16 LE with BOM and breaks other tools).
- `pytest` invoked locally on Windows: prepend `python -m` (`python -m pytest`) — bare `pytest` may resolve to a different venv.
- For long pytest runs that hit pytest-xdist worker isolation, see `.claude/skills/learned/parallel-agents-need-git-worktrees/SKILL.md`.

**Always-cross-platform code rules:**

- Use `pathlib.Path`, never raw `os.path.join` with hard-coded separators.
- Use `tempfile.gettempdir()` for temp paths; never `/tmp` literals.
- Use `subprocess.run([...], check=True)` with list-of-args, not shell-string commands.
- When writing scripts under `scripts/`, prefer Python (`scripts/closeout_check.py`) over PowerShell-only (`Scripts/closeout_check.ps1`). The PowerShell scripts under `Scripts/` are legacy duplicates kept for Windows-default operator convenience; new tooling goes under lowercase `scripts/` as Python.

## End-to-end contributor flow

The full path from idea to merged PR. Follow this even for a small change.

```
1. Triage / plan
   ├─ Is this a new feature, refactor, or bug fix? Bug fix → smaller scope.
   ├─ Does it span multiple workstreams? Plan to bundle (see PR bundling).
   ├─ Does it touch V1.34 parity surface? If yes, read parity rules first.
   └─ Does it need a written plan doc? See "Plan documents" section.

2. Branch
   ├─ git fetch origin
   ├─ git checkout modularize-v1.34       (base branch until main lands)
   ├─ git pull --ff-only
   └─ git checkout -b <type>/<short-slug>
        e.g. fix/coverage-ratchet-windows-skip
             feat/dual-machine-bank-readiness
             docs/contributing-pr-bundling-rule
             refactor/snapshot-decoder-protocol

3. Implement (TDD where applicable)
   ├─ Write failing test first
   ├─ Make it pass with minimal code
   ├─ Refactor
   ├─ Commit in small steps with imperative summaries
   └─ Re-run `python -m pytest -m fast` frequently (<60s iteration loop)

4. Pre-push verification (run all four, in order)
   ├─ python -m pytest -q                          # full suite
   ├─ python -m pytest tests/architecture/ -q      # architecture conformance
   ├─ python -m ruff check . && python -m black --check --target-version=py311 . && python -m isort --profile black --check-only .
   └─ python -m pytest --cov=rytm_randomizer --cov-branch
       └─ Confirm pure-branch coverage stays >= 95%

5. Push
   └─ git push -u origin <your-branch>
        ├─ post-push code-review hook fires automatically (Claude Code harness)
        └─ Or run manually: /agent code-reviewer  or  /skill code-review

6. Open PR
   ├─ gh pr create --base modularize-v1.34 \
   │      --title "<conventional-commit-style title>" \
   │      --body-file <path-to-prepared-body>
   ├─ PR body MUST include:
   │      • What changed and why
   │      • Test plan (checklist of what was verified)
   │      • Plan-requirements conformance checklist (16 gates)
   │      • Link to any plan doc under docs/superpowers/plans/ or docs/
   └─ Confirm CI starts (gh pr checks <PR#>)

7. Iterate on CI to green
   ├─ Watch: gh pr checks <PR#> --watch
   ├─ Address every failing check
   ├─ Re-run pre-push verification locally before each push
   └─ Standing order: do not stop until ALL checks pass

8. Request review
   ├─ The base branch requires CODEOWNERS review (@buzzijose-hub).
   ├─ Post a merge-ready comment summarizing: CI state, test count,
   │  coverage %, parity status, gates satisfied.
   └─ Address review comments; do not amend force-pushes without
       coordinating (review comments lose their anchors otherwise).

9. Merge (after approval)
   ├─ gh pr merge <PR#> --squash
   ├─ Delete the feature branch (--delete-branch=true) unless WIP
   └─ Bump docs/STATUS.md "Recent Cleanup" if applicable
```

## Verification gate

Before opening a PR, run the verification gate:

```bash
# Run on Windows, macOS, or Linux:
python -m pytest

# Architecture-conformance subset (also a required CI check):
python -m pytest tests/architecture/ -q

# Fast iteration (excludes 685 V1.34 parity goldens; <60s wall-clock):
python -m pytest -m fast

# Coverage with branch coverage (matches CI):
python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing
```

All tests must pass. Coverage must stay ≥95% pure-branch (the ratchet floor, enforced by `scripts/coverage_ratchet.py` and `.coveragerc`).

Lint / format / type-check gates (also required CI checks):

```bash
python -m ruff check rytm_randomizer/ tests/
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
```

Run `python -m ruff check . --fix` and `python -m black . --target-version=py311` and `python -m isort --profile black .` to auto-fix before committing.

Pre-commit hooks (configured in `.pre-commit-config.yaml`) run a subset of these automatically; install with `pre-commit install`.

## Linting and formatting — the exact rule set

All three tools have explicit configuration in `pyproject.toml`. The rule packs and ignores are intentional; do not silently widen them.

### Ruff — `[tool.ruff.lint]` in `pyproject.toml`

Enabled rule packs:

| Pack | Rules | Purpose |
|---|---|---|
| `E` | pycodestyle errors | PEP 8 errors. |
| `F` | pyflakes | Logical errors (unused imports, undefined names, etc.). |
| `B` | flake8-bugbear | Common bug patterns (mutable defaults, unused loop vars, raising bare exceptions). |
| `S` | flake8-bandit | **Security backstop**: hardcoded passwords, insecure subprocess, eval/exec, weak crypto. |
| `SIM` | flake8-simplify | Code-style simplifications (with project-specific carve-outs below). |
| `UP` | pyupgrade | Modern Python syntax preferences. |
| `C4` | flake8-comprehensions | Comprehension idioms. |

Project-wide ignores (with documented reasons):

- `E501` — line-length is left to black; ruff's check duplicates the formatter.
- `SIM105` — `contextlib.suppress` often less readable than explicit try/except/pass.
- `SIM102` — explicit nested ifs often more readable when each guard has its own semantic meaning.
- `SIM108` — explicit if/else preferred over ternary for branchy logic.

Per-file ignores for `tests/**` (with reasons documented in `pyproject.toml`):

- `S101` — pytest asserts are how tests express invariants.
- `S105` — loop variables named `token` for AST iteration trigger bandit's hardcoded-password rule (false positive).
- `S110` — defensive try/except/pass in fixtures.
- `S311` — the project IS a non-crypto randomizer; tests intentionally exercise seeded `random.Random()`.
- `S603` / `S607` — `subprocess.run([...])` with static lists, no shell.
- `E402` — tests insert `PROJECT_ROOT` on `sys.path` before imports; intentional order.
- `B007`, `B011`, `B017`, `B904` — documented per-site test patterns.

Run:

```bash
python -m ruff check .                # check
python -m ruff check . --fix          # auto-fix
```

**Adding a new ignore is a code-review decision**, not a unilateral one. Justify in the PR body why the new ignore is correct.

### Black — `[tool.black]` in `pyproject.toml`

- `line-length = 100` (matches ruff's `E501` baseline; black actually formats up to 100).
- `target-version = ["py311"]` (CI matrix). Do not narrow to py39/py310 — the dropped versions are not on CI.

Run:

```bash
python -m black --check --target-version=py311 .   # check
python -m black --target-version=py311 .           # auto-fix
```

### isort — `[tool.isort]` in `pyproject.toml`

- Profile: `black` (matches black's formatting choices for imports).
- Three-section import order: stdlib → third-party → first-party (`rytm_randomizer`).

Run:

```bash
python -m isort --profile black --check-only .     # check
python -m isort --profile black .                  # auto-fix
```

### Pre-commit hooks (`.pre-commit-config.yaml`)

Subset that runs on every commit. Install once:

```bash
pre-commit install
```

To run all hooks across the whole repo:

```bash
pre-commit run --all-files
```

**Do not bypass.** `--no-verify` is forbidden by Strict Rule 15 above.

### Type checking

There is no `mypy` / `pyright` enforcement in CI today, but new code must:

- Use type annotations on every public function/method signature (Gate 6).
- Prefer `@runtime_checkable Protocol` over ABCs (Gate 6).
- Annotate module-level constants with `Final` (Gate 12).
- Avoid `Any` outside the documented allowlist. Use `object`, narrow union types, or generic Protocols instead.

The `tests/architecture/test_no_any_escape_hatches.py` test mechanically rejects new `Any` introductions outside the allowlist.

## Plan requirements — the 16 gates every PR must satisfy

[`docs/PLAN_REQUIREMENTS.md`](docs/PLAN_REQUIREMENTS.md) is the contract
for **every** non-trivial PR, not just an internal "plan" PR. It defines 16
gates:

| Gate | Topic |
|---|---|
| 1 | Coverage (100% branch on touched files; ≥95% project-wide pure-branch ratchet) |
| 2 | V1.34 parity fixtures byte-identical (685/685 goldens) |
| 3 | Lint/format/type clean (ruff + black `--target-version=py311` + isort `--profile black`) |
| 4 | Dead-code purge (vulture `--min-confidence 80`) |
| 5 | Docs updated (README/CONTRIBUTING/STATUS reflect the change) |
| 6 | Type-system hygiene (no `Any` escape hatches; Protocols over ABCs) |
| 7 | Observability adoption (logging/tracing/metrics where applicable) |
| 8 | Test hygiene (name `test_<unit>_<behavior>_when_<condition>`; shared fixtures) |
| 9 | Module-organization hygiene (subpackages over flat top-level) |
| 10 | String-literal dispatch hygiene (consume `data/modes.py` constants; allowlist drained) |
| 11 | Shared fixtures (canonical definitions in `tests/conftest.py`) |
| 12 | `Final` constants (module-level constants annotated `Final`) |
| 13 | Env var docs (every read env var documented) |
| 14 | Maintainability review (timing tracked, complexity bounded) |
| 15 | Learning capture (extract `.claude/skills/learned/` + `.claude/rules/` where applicable) |
| 16 | Execution shape (cascade-merge for autonomous multi-WS runs) |

**Before opening a PR**, read [`docs/PLAN_REQUIREMENTS.md`](docs/PLAN_REQUIREMENTS.md) and include a
conformance checklist in the PR body (one line per gate, `[x]` or `[ ]
N/A — reason`). PR #35 (the Wave-1 simplification bundle) is the canonical
example of a fully-conformant PR body.

Sub-rules under `.claude/rules/` extend the 16 gates:

- [`architecture.md`](.claude/rules/architecture.md) — agent-facing architecture distillation.
- [`skill-routing.md`](.claude/rules/skill-routing.md) — which skill applies to which task.
- [`parity-fixture-discipline.md`](.claude/rules/parity-fixture-discipline.md) — Gate 2 details; when and how to regenerate V1.34 fixtures.
- [`coverage-gate-100pct.md`](.claude/rules/coverage-gate-100pct.md) — Gate 1 details; branch coverage and per-file ratchet.
- [`cascade-merge-pattern.md`](.claude/rules/cascade-merge-pattern.md) — Gate 16 enforcement for autonomous multi-WS runs.

Architecture-enforcement tests under `tests/architecture/` mechanically
verify a subset of these gates on every CI run; do not skip them locally.

## Test suite structure

The suite has 1631+ tests across these layers:

| Layer | Where | Purpose |
|---|---|---|
| Unit / behavior | `tests/test_*.py` | Per-module unit and behavior tests. |
| V1.34 parity | `tests/test_engines_pad{1..4}.py`, `tests/test_group_runner.py`, `tests/test_scene_runner.py` | Lock 685 byte-identical JSON goldens under `tests/fixtures/v134_parity/`. |
| Architecture conformance | `tests/architecture/` | Mechanically check Gate 6 / 8 / 9 / 10 / 11 / 12 invariants. |
| Coverage ratchet | `scripts/coverage_ratchet.py` | Post-pytest hook that fails CI if pure-branch coverage drops below 95%. |
| E2E | `tests/test_*_e2e.py` | End-to-end smoke (no hardware; runs through `MockMidiSender`). |
| Fast subset | `pytest -m fast` | Lightweight tests; skip 685 parity goldens for sub-60s iteration. |

**Architecture tests** (don't break these):

| File | What it enforces |
|---|---|
| `test_no_any_escape_hatches.py` | No `Any` escape hatches outside an allowlist. |
| `test_no_new_top_level_modules.py` | No new top-level modules under `rytm_randomizer/` — use a subpackage. |
| `test_no_string_literal_mode_dispatch.py` | Dispatch sites consume `data/modes.py` constants, not inline strings. Allowlist is drained. |
| `test_shared_fixtures_available.py` | Fixtures used in >1 test file live in `tests/conftest.py`. |
| `test_parity_index_writer.py` | The parity-fixture index writer round-trips. |
| `test_fast_marker_coverage.py` | Every test file declares `pytestmark = pytest.mark.fast` (or explicitly omits it with a comment). |
| `test_plan_requirements_referenced.py` | `docs/PLAN_REQUIREMENTS.md` is linked from each plan/spec. |
| `test_layering_structure.py` | Subpackages import only in the documented direction. |
| `test_house_style.py` | House-style invariants (docstrings, naming). |
| `test_import_direction.py` | Import direction guards (no `tests` → `tests` cross-imports, etc.). |
| `test_no_side_effects.py` | No I/O / port-open / sleep at module import time. |
| `test_observability.py` | Hot paths call `get_metrics().record_*`. |
| `test_ci_workflow.py` | The CI workflow files match the documented contract. |
| `test_data_not_code.py` | "Tables of facts" live as data, not as functions. |

**Parity fixtures.** The 685 JSON goldens under `tests/fixtures/v134_parity/` are the authoritative V1.34 reference. Regenerate only when an intentional reference-output change is being committed:

```bash
PARITY_CAPTURE_MODE=1 python -m pytest \
  tests/test_engines_pad*.py \
  tests/test_group_runner.py \
  tests/test_scene_runner.py
```

PowerShell equivalent:

```powershell
$env:PARITY_CAPTURE_MODE = "1"
python -m pytest tests/test_engines_pad*.py tests/test_group_runner.py tests/test_scene_runner.py
Remove-Item Env:\PARITY_CAPTURE_MODE
```

See [`.claude/rules/parity-fixture-discipline.md`](.claude/rules/parity-fixture-discipline.md) for the full discipline.

**Pytest markers** (registered in `pyproject.toml`):

- `fast` — lightweight in-process tests; safe to run under `pytest -m fast` for <60s iteration.

**CI workflows** under `.github/workflows/`:

- `test.yml` — main suite: lint + test + e2e + architecture + security on `[windows-latest, macos-latest, ubuntu-latest] × py3.11`, plus the `required-checks` gate, the coverage ratchet, and a docs-gate.
- `codeql.yml` — CodeQL static analysis.
- `release.yml` — triggered on `v*` tags; builds wheel + sdist and publishes a GitHub Release.
- `installers.yml` — builds platform installers.

## Common contributor tasks

For "where do I add X?" answers, the source of truth is
[`docs/ARCHITECTURE.md` §6](docs/ARCHITECTURE.md#6-where-to-put-new-work).
The table there maps change types to the right module and the right skill.

Quick links for the most common tasks:

- **Add a new V1.34-equivalent command** — `shell.py` dispatch + relevant
  runner/engine. Skill: [`add-pad-command`](.claude/skills/add-pad-command/SKILL.md).
- **Add a new fact table** — a new module under `rytm_randomizer/data/` plus
  the re-export in `__init__.py`. Skill: [`extend-data-layer`](.claude/skills/extend-data-layer/SKILL.md).
- **Change MIDI primitives** — `midi_io.py`. Keep `mido` lazy. Requires
  architecture review.
- **Add a passive read-only report** — extend `reports/` (the post-WS-S4
  subpackage) and wire it through `cli.py`. The passive CLI never opens a
  MIDI port; see `docs/ARCHITECTURE.md` §2.

For the full list of change types, see `docs/ARCHITECTURE.md` §6.

## Skill catalog

Skills under `.claude/skills/` package repeatable knowledge so an agent (or a human) can re-do a task quickly without re-deriving the pattern. Three categories:

### Repo-specific skills

| Skill | When to invoke |
|---|---|
| [`add-pad-command`](.claude/skills/add-pad-command/SKILL.md) | Adding a new V1.34-equivalent shell command. |
| [`extend-data-layer`](.claude/skills/extend-data-layer/SKILL.md) | Adding a new fact table to `rytm_randomizer/data/`. |
| [`code-review`](.claude/skills/code-review/SKILL.md) | Running the standardized post-push code review. |
| [`coverage-ratchet`](.claude/skills/coverage-ratchet/SKILL.md) | Updating the coverage floor when a legitimate floor change is needed. |
| [`docs-update-with-pr`](.claude/skills/docs-update-with-pr/SKILL.md) | Updating docs (README/CONTRIBUTING/STATUS) as part of a PR. |
| [`ci-workflow-invariants`](.claude/skills/ci-workflow-invariants/SKILL.md) | Editing `.github/workflows/*.yml` without breaking the contract. |
| [`python-on-windows`](.claude/skills/python-on-windows/SKILL.md) | Working around PowerShell-specific gotchas during contributor onboarding. |
| [`DataAnalysisGuardrails`](.claude/skills/DataAnalysisGuardrails/SKILL.md) | Safe data analysis (no hardware I/O, no port opens). |
| [`MusicLibraryGuardrails`](.claude/skills/MusicLibraryGuardrails/SKILL.md) | Working with the music-library data with safety boundaries. |

### Learned skills (extracted from past runs; `.claude/skills/learned/`)

| Skill | What was learned |
|---|---|
| [`cascade-merge-pattern`](.claude/skills/learned/cascade-merge-pattern/SKILL.md) | Bundle N workstreams into one PR under approval-gated branches. |
| [`parallel-agent-bundle`](.claude/skills/learned/parallel-agent-bundle/SKILL.md) | Dispatch N agents in parallel on disjoint file sets, then bundle. |
| [`parallel-agents-need-git-worktrees`](.claude/skills/learned/parallel-agents-need-git-worktrees/SKILL.md) | When parallel agents must operate on separate worktrees vs. shared branches. |
| [`rebase-after-squash-merge`](.claude/skills/learned/rebase-after-squash-merge/SKILL.md) | How to rebase a branch after the base squash-merged. |
| [`coverage-py-blended-vs-pure-branch`](.claude/skills/learned/coverage-py-blended-vs-pure-branch/SKILL.md) | Why the ratchet uses pure-branch (not blended) coverage. |
| [`elektron-sysex-envelope`](.claude/skills/learned/elektron-sysex-envelope/SKILL.md) | Elektron 7-bit SysEx envelope structure (Rytm + A4 + Digitakt). |
| [`pip-audit-editable-install`](.claude/skills/learned/pip-audit-editable-install/SKILL.md) | Running pip-audit when the package is editable-installed; how to handle hardware-pinned packages. |
| [`github-actions-matrix-conditional`](.claude/skills/learned/github-actions-matrix-conditional/SKILL.md) | Conditional matrix expansion in `.github/workflows/test.yml`. |
| [`github-token-no-workflow-trigger`](.claude/skills/learned/github-token-no-workflow-trigger/SKILL.md) | Pushing from a workflow without triggering recursive CI. |
| [`branch-protection-with-path-filters`](.claude/skills/learned/branch-protection-with-path-filters/SKILL.md) | Configuring branch protection together with `paths:` filters. |

### Adding a new skill

When you complete work where you wish you'd had a skill at the start, extract one. Create `.claude/skills/<short-kebab-name>/SKILL.md` with the format described in the parent of any existing learned skill. Update the table above in the same PR. See Gate 15.

## Preserve parity with the V1.34 reference

The V1.34 hardware-validated musical behavior is the baseline of truth. It was validated against the actual Analog Rytm MK2. **Any change must preserve parity with that behavior.**

As of Wave 4 / WS-O the modular package owns the interactive runtime end-to-end (`rytm_randomizer.app` -> `rytm_randomizer.shell`). The V1.34 monolith (`rytm_hybrid_randomizer_v134.py`) has been retired; its byte-for-byte reference behavior is preserved as JSON goldens under `tests/fixtures/v134_parity/` and asserted by the parity tests (`tests/test_engines_pad*`, `tests/test_group_runner.py`, `tests/test_scene_runner.py`) via `tests/_parity_worker.py`.

Concretely:

- The committed JSON goldens under `tests/fixtures/v134_parity/` are the authoritative V1.34 reference. New behavior lives in the `rytm_randomizer/` package and is locked against the goldens by the parity tests. Regenerate fixtures with `PARITY_CAPTURE_MODE=1 pytest tests/test_engines_pad*.py tests/test_group_runner.py tests/test_scene_runner.py` only when an intentional reference-output change is being committed.
- The following are **not allowed** without explicit approval:
  - New MIDI CC mappings.
  - New pad profiles or machines.
  - Pads 5-12 expansion (this is the 12-pad work — gated behind explicit per-machine pad-compatibility validation; see the rytm/dual-machine branches).
  - Parameter range changes.
  - Command behavior changes (the shell's command alphabet mirrors the V1.34 reference exactly).
- **Allowed:** further refactoring within the package; readability improvements that do not change behavior; new tests; documentation updates; new passive read-only reports.
- Add tests when you split code. Test after each major split.

## Commit conventions

- Short, imperative summaries (e.g. `Split scene plans into scenes module`).
- Conventional-commit-style prefixes are welcome (`feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`, `ci:`).
- Commit in small steps within a branch; **bundle into one PR** per the rule below.

## PR bundling — one PR per logical change, not per commit

Commit in small steps, but open **one bundled PR** for related work rather
than a cascade of small PRs stacked on each other. The base branch
(`modularize-v1.34` until `main` lands) requires CODEOWNERS review on every
PR, so a 5-deep cascade is N approvals; a bundled PR is 1.

**Specifically:**

- If your change spans multiple workstreams (e.g. dual-machine = Rytm + A4 +
  shared orchestration), implement each workstream on its own feature branch
  in parallel, then bundle them into one integration branch via
  `git merge --no-ff` and open **one** PR. See
  [`.claude/rules/cascade-merge-pattern.md`](.claude/rules/cascade-merge-pattern.md)
  for the operational recipe.
- Do not open a PR whose base is another open PR's head (a "stacked PR"). If
  the second piece truly cannot land without the first, finish the first
  PR first; otherwise merge them in the source branch.
- **Exception:** if the base branch is unprotected (no CODEOWNERS gate), the
  per-PR cascade is fine — it gives independent revert capability and
  finer-grained reviewer attention. The bundling rule is specifically for
  approval-gated branches.

If you are an autonomous agent (codex, claude-code, etc.) wired to open
one PR per workstream under an approval-gated branch, **the orchestrator
configuration is wrong**, not the policy — fix it to bundle before merging
the next PR. The PR #35 run is the canonical example
([`docs/SIMPLIFICATION_RUN_REPORT.md`](docs/SIMPLIFICATION_RUN_REPORT.md)).

## PR size guidance

There is no hard upper bound (PR #35 was 175 files / +17,686 / -10,671), but reviewer attention is finite. Use these heuristics:

| Size | Files | Net LOC | Recommended approach |
|---|---|---|---|
| Tiny | 1 | < 50 | One commit; minimal PR body. |
| Small | 2-10 | 50-500 | Standard PR; full conformance checklist. |
| Medium | 10-30 | 500-2,000 | Standard PR + before/after architecture sketch in body. |
| Large | 30-100 | 2,000-10,000 | Bundle multiple workstreams; PR body includes per-workstream sub-summaries; consider a written plan doc under `docs/superpowers/plans/`. |
| Bundled refactor | 100+ | 10,000+ | Must have a published plan doc; canonical run report in `docs/SIMPLIFICATION_RUN_REPORT.md` style; multiple `[reviewers]` recommended for review surface coverage. |

**Per-file LOC sanity check.** A new module > 500 LOC is a signal to split. Existing modules above 500 LOC (`shell.py`, `cli.py`, several `engines/*.py`, `essence/rytm_engine_cycle_starter_profiles.py` at 859, `dual_machine/mock_bridge.py` at 621) are tolerated because splitting them invites parity regressions; new code should aim for ≤300 LOC per module.

**When to split a planned PR before opening it:**

- The PR touches more than one architectural layer with unrelated concerns (e.g. UI + MIDI boundary + data layer). Split by concern.
- The PR has a clear "land first" + "land second" dependency. Land the first; open the second as a normal PR (not a stacked PR).
- The PR's changes for any single architecture layer exceed 5,000 LOC. Split by layer.
- The PR mixes a refactor + a behavior change. Split: refactor lands first (must be byte-identical against V1.34 parity), behavior change lands second.

**When NOT to split:**

- The pieces only make sense together (e.g. you cannot have the Protocol without one implementation).
- The split would create a stacked-PR cascade under CODEOWNERS.
- The pieces share a parity-fixture regeneration.

## Plan documents — when and how

For any PR that meets at least one of:

- Net LOC > 2,000
- Files changed > 30
- Spans 2 or more workstreams
- Introduces a new architectural surface (Protocol, registry, subpackage)
- Changes the V1.34 parity surface (requires explicit approval first)

…write a plan document **before** writing code. Plans live under one of:

- `docs/superpowers/plans/<YYYY-MM-DD>-<short-slug>.md` — for in-flight feature plans (codex-style; the most common location).
- `docs/superpowers/specs/<YYYY-MM-DD>-<short-slug>-design.md` — for design specs that need to be reviewed before plan execution.
- `docs/SIMPLIFICATION_PLAN.md` style at repo root — for large multi-WS refactor plans.

A plan document must answer:

1. **Why** — the motivation. Link the issue / Slack thread / past PR that surfaced it.
2. **What changes** — the file-level scope and the architectural shape (Protocols, dataclasses, registry entries).
3. **Workstreams** — for any multi-WS plan, the explicit WS table with owns / depends-on / parallel-with.
4. **Parity impact** — does this touch V1.34 fixtures? If yes, justify and obtain explicit approval.
5. **Plan-requirements conformance** — pre-fill the 16-gate checklist with expected satisfaction. Gates marked N/A must be justified.
6. **Test plan** — how the change will be verified before opening the PR. Includes new test files and new architecture-test additions.
7. **Rollback plan** — what reverts cleanly, what doesn't.
8. **Done criteria** — concrete done state (e.g. "X tests pass; coverage stays ≥95%; Y allowlist drained").

The plan doc is committed in the same branch as the implementation and referenced from the PR body. Reviewers read the plan first; the diff second.

For very large multi-WS bundled runs (PR #35 scale), see [`docs/AUTONOMOUS_RUN_PLAYBOOK.md`](docs/AUTONOMOUS_RUN_PLAYBOOK.md) for the orchestrator pattern.

## gh CLI quick reference

The repo uses GitHub heavily; `gh` is the primary CLI surface. Install: <https://cli.github.com/>.

```bash
# AUTH
gh auth status
gh auth login   # if not already

# DAILY
gh pr list --state open                           # what's in flight
gh pr view <PR#>                                  # PR summary
gh pr view <PR#> --json statusCheckRollup         # raw CI state
gh pr checks <PR#>                                # CI table
gh pr checks <PR#> --watch                        # live CI poll
gh pr diff <PR#>                                  # diff
gh pr comments <PR#>                              # discussion

# OPENING A PR
gh pr create --base modularize-v1.34 \
   --title "<title>" \
   --body-file path/to/body.md

# UPDATING A PR
gh pr edit <PR#> --body-file path/to/new-body.md
gh pr comment <PR#> --body "<comment>"

# REVIEWING
gh pr review <PR#> --comment --body "<comment>"
gh pr review <PR#> --approve     # CODEOWNERS approval (only by owners)
gh pr review <PR#> --request-changes --body "<comment>"

# MERGING
gh pr merge <PR#> --squash --delete-branch=false
gh pr merge <PR#> --squash --admin            # only if you have admin
gh pr merge <PR#> --auto --squash             # enable auto-merge when CI passes

# CI / WORKFLOWS
gh run list --workflow=test.yml --limit=5
gh run view <run-id> --log-failed
gh run rerun <run-id> --failed                # re-run only the failed jobs

# RAW API (when gh's typed commands don't cover the case)
gh api repos/buzzijose-hub/RytmRandomizer/branches/modularize-v1.34
gh api graphql -f query='{ repository(...) { ... } }'
```

For autonomous flows from a Claude Code harness, prefer `gh` over web UI clicks — it's scriptable and deterministic.

## Data vs code

Anything that is "a table of facts" — commands, parameters, scenes, pad profiles — should live as **data** (a dataclass registry or a data file), not as bespoke per-item functions. Prefer one generic handler driven by a registry over many near-identical hand-written functions.

This is enforced by `tests/architecture/test_data_not_code.py`.

## Definition of done includes docs

Any structural change must update the docs it affects. A change is not done until the `README.md`, this file, and any relevant `docs/` entries reflect the new reality. See Gate 5 above and skill [`docs-update-with-pr`](.claude/skills/docs-update-with-pr/SKILL.md).

## Architecture standard

The codebase has a fixed architecture documented in `docs/ARCHITECTURE.md`
and enforced by tests under `tests/architecture/`. Read both before any
non-trivial change.

The agent-facing distillation lives in [`.claude/rules/architecture.md`](.claude/rules/architecture.md) and the
skill-routing table is in [`.claude/rules/skill-routing.md`](.claude/rules/skill-routing.md).

### Verification gate (architecture)

Before opening a PR, in addition to the full suite:

```bash
python -m pytest tests/architecture/ -q
```

This is also a required CI check (see `.github/workflows/test.yml`) and is
listed in `scripts/apply-branch-protection.sh`.

## Hardware safety boundaries

The package has explicit hardware-safety boundaries that **must not regress**:

- **Passive default.** `rytm-randomizer` with no `--arm` flag must NEVER open a real MIDI port. The CLI's default exercises `MockMidiSender` only.
- **Lazy MIDI imports.** `mido` and `python-rtmidi` are imported lazily inside the real-MIDI adapter (`rytm_randomizer/real_midi_adapter.py`) — never at module top level. The architecture test `test_no_side_effects.py` enforces this.
- **Boundary classes.** All real-MIDI calls go through the `RealMidiSender` / `RealMidiPortProvider` boundary in `real_midi_adapter.py`. Tests must use the boundary, not raw `mido`.
- **No hardware in tests.** No test opens a real port; no test mutates a connected device. The `MockMidiSender` + `_FakeMessage` are the testing surfaces. CI does not have a Rytm or A4 attached.
- **Hardware-pinned packages.** `mido==1.3.3` and `python-rtmidi==1.5.8` are pinned in `pyproject.toml`. Do not bump (see [Local development setup](#local-development-setup)).
- **Pad expansion gating.** Pads 5-12 are gated behind per-machine pad-compatibility validation (see the `rytm/` and `dual_machine/` subpackages). The 4-pad surface (pads 1-4) is the validated baseline.

## Automated post-push code review

The repo-local `.claude/settings.json` configures a `PostToolUse` hook that
fires the `code-reviewer` agent (`.claude/agents/code-reviewer.md`) after any
`git push` invocation made through the Claude Code harness. The agent reads
the diff, runs the architecture gate (`pytest tests/architecture/`), and
returns a structured Critical / Important / Minor verdict.

**Harness fallback.** If your harness version does not yet support the
`Agent` action type for hooks, the hook is silently ignored. You can run the
same review manually:

```
/agent code-reviewer
```

or invoke the skill directly:

```
/skill code-review
```

The hook config is committed at `.claude/settings.json`; you can override it
locally in `.claude/settings.local.json` if you prefer a different trigger.

## Releasing

RytmRandomizer follows [Semantic Versioning](https://semver.org/). The release
process is defined and repeatable — there is **no version-in-filename** (the
old `v131` / `v132` / `v134` naming is historical only).

**Single source of version truth:** the `[project] version` field in
`pyproject.toml`. Nothing else declares the version.

To cut a release `vX.Y.Z`:

1. **Bump the version** — update `[project] version` in `pyproject.toml` to
   `X.Y.Z`.
2. **Update the changelog** — in `CHANGELOG.md`, move the entries under
   `## [Unreleased]` into a new `## [X.Y.Z] - YYYY-MM-DD` section, leave fresh
   empty `Added` / `Changed` / `Fixed` subsections under `[Unreleased]`, and
   update the link references at the bottom of the file.
3. **Commit** the `pyproject.toml` and `CHANGELOG.md` changes (e.g.
   `Release vX.Y.Z`).
4. **Tag** the commit: `git tag vX.Y.Z`.
5. **Push the tag**: `git push origin vX.Y.Z`.

Pushing a `v*` tag triggers `.github/workflows/release.yml`, which builds the
wheel + sdist from `pyproject.toml`, runs the `pytest` gate (a release cannot
ship if tests fail), and publishes a GitHub Release with the `dist/*` artifacts
attached.
