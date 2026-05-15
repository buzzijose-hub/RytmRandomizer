---
name: ci-workflow-invariants
description: Three invariants that the CI workflow must always satisfy — lint-tool versions matching between `.github/workflows/test.yml` and `.pre-commit-config.yaml`, every `actions/setup-python@v6` step using pip caching, and the `required-checks` aggregate listing every other job in `needs:`. Use this skill whenever you are about to edit `.github/workflows/test.yml`, `.pre-commit-config.yaml`, bump a lint tool version, add a new CI job, or add a new `setup-python` step. The architecture tests in `tests/architecture/test_ci_workflow.py` will fail loudly if any of these invariants are broken — this skill explains how to keep them satisfied the first time.
---

# CI workflow invariants

Three things must hold true at all times in the CI configuration. Each one is enforced by an architecture test, so breaking it will fail the build — but it's much nicer to get it right while you're editing than to chase a red CI run.

## Invariant 1 — Lint tool versions match between workflow and pre-commit

The versions of `ruff`, `black`, `mypy`, etc. pinned in `.github/workflows/test.yml` (typically via `pip install ruff==X.Y.Z`) must match the `rev:` field for the same tool in `.pre-commit-config.yaml`.

**Why:** if the two diverge, a contributor's local pre-commit pass will pass while CI fails (or vice versa). Wasted PR cycles, frustrated devs, and arbitrary "fix it in CI" patches that don't actually fix the local hook.

**Enforced by:** `tests/architecture/test_ci_workflow.py::test_lint_tool_versions_match_between_workflow_and_precommit`.

**When bumping a lint tool version:**

1. Update the version in `.github/workflows/test.yml`.
2. Update the matching `rev:` in `.pre-commit-config.yaml`.
3. Run `pre-commit run --all-files` locally to make sure the new version is happy with existing code.
4. Run the architecture test to confirm: `pytest tests/architecture/test_ci_workflow.py -q`.

If you only update one file, the test fails with a clear diff of which tool is mismatched and which version is in which file.

## Invariant 2 — Every `setup-python` step uses pip caching

Every `actions/setup-python@v6` step in `.github/workflows/test.yml` MUST include both:

```yaml
- uses: actions/setup-python@v6
  with:
    python-version: "3.13"
    cache: pip
    cache-dependency-path: pyproject.toml
```

**Why:** `pyproject.toml` pins our dev dependencies; without the cache, every CI run re-resolves and re-downloads them, adding ~30s per job. Multiply by 5 jobs and you've lost a minute of every run for no reason.

**Enforced by:** `tests/architecture/test_ci_workflow.py::test_every_setup_python_step_uses_pip_caching`.

**When adding a new `setup-python` step:** copy the snippet above verbatim. Don't omit `cache:` "just for this one job" — the test will fail.

## Invariant 3 — `required-checks` aggregate covers every upstream job

There's a job named `required-checks` at the bottom of the workflow whose only purpose is to be the single status check the branch-protection rule depends on. It must `needs:` every other job in the file.

```yaml
required-checks:
  runs-on: ubuntu-latest
  needs: [test, lint, type-check, docs-gate, coverage-ratchet, ...]
  steps:
    - run: echo "All required checks passed."
```

**Why:** GitHub branch protection rules can only require a fixed list of named checks. If we listed each job individually, we'd have to update branch protection every time we added a job. By making `required-checks` the single required check, adding a new job is a one-line edit to its `needs:` list — no GitHub admin needed.

**Enforced by:** `tests/architecture/test_ci_workflow.py::test_required_checks_aggregate_covers_every_upstream_job`.

**When adding a new CI job named `foo`:**

1. Add the job definition somewhere above `required-checks`.
2. Add `foo` to the `needs:` array on `required-checks`.
3. Run the architecture test. If you forget step 2, the test fails with a clear list of jobs that exist but aren't in `needs:`.

## Verifying all three at once

```bash
"$PYTHON" -m pytest tests/architecture/test_ci_workflow.py -q
```

(Use the absolute Python path — see the `python-on-windows` skill.)

## When to invoke this skill

- Before editing `.github/workflows/test.yml` for any reason.
- Before editing `.pre-commit-config.yaml`.
- When bumping a linter version (ruff, black, mypy, etc.).
- When adding a new CI job or a new `setup-python` step.
- When a CI architecture test is failing and you need to understand what it's checking.
