---
name: pip-audit-editable-install
description: pip-audit --strict fails when an editable install is present, even with --skip-editable. Generate a frozen requirements file via pip freeze --exclude-editable and audit that instead.
user-invocable: false
origin: auto-extracted
---

# pip-audit + editable install: use pip freeze --exclude-editable

**Extracted:** 2026-05-15
**Context:** You have a Python project that contributors install with `pip install -e .[dev]` and you want a CI security gate via pip-audit. The project itself is not published on PyPI (it's local-only or in active development).

## Problem

In CI you run:

```bash
pip install -e ".[dev]"
pip install "pip-audit>=2.10,<3"
pip-audit --strict
```

The job fails:

```
ERROR:pip_audit._cli:rytm-randomizer: Dependency not found on PyPI and could not be audited: rytm-randomizer (1.34.0)
```

pip-audit sees the editable distribution of your own project, tries to look it up on PyPI, fails, and `--strict` exits non-zero.

You try the documented fix:

```bash
pip-audit --strict --skip-editable
```

That ALSO fails:

```
ERROR:pip_audit._cli:rytm-randomizer: distribution marked as editable
```

`--skip-editable` in strict mode converts a silent skip into a hard error. `--strict` refuses to silently miss anything, including the thing you told it to skip.

You try auditing the project file directly:

```bash
pip-audit --strict .
```

That fails too: pip-audit's project-path mode shells out to a fresh `pip install` of the project's declared deps, which builds python-rtmidi from source — and CI has no compiler.

## Solution

Install the project as editable to resolve the full transitive dependency closure, then export EXACTLY those transitive dependencies (minus the editable project itself) into a pinned requirements file, and audit that:

```yaml
- name: Install package with dev extras
  run: pip install -e ".[dev]"

- name: Install pip-audit
  run: pip install "pip-audit>=2.10,<3"

- name: Generate audit input from installed env
  # pip freeze --exclude-editable drops the project's own editable
  # entry and leaves third-party deps with == pins -- exactly what
  # pip-audit wants.
  run: pip freeze --exclude-editable > .pip-audit-input.txt

- name: Run pip-audit
  run: pip-audit --strict -r .pip-audit-input.txt
```

This has all the right properties:

- **Single source of truth**: pyproject.toml's dependencies decide what gets installed.
- **No duplicate manifest**: the requirements file is derived from what pip actually resolved.
- **Strict mode works**: pip-audit gets a clean list with `==` pins and audits each against the PyPI Advisory Database.
- **No editable distribution confusion**: the project itself is excluded by `pip freeze --exclude-editable`.

## When to Use

Trigger conditions:

- You want to run `pip-audit --strict` in CI.
- Your project uses `pip install -e .` for development AND is not (yet) published on PyPI.
- You see `Dependency not found on PyPI` or `distribution marked as editable` errors in CI.

DO NOT use this pattern when:

- Your project IS published on PyPI — pip-audit will find it and audit it normally.
- You only audit specific dependencies from a hand-maintained requirements file — the editable install isn't in scope.

Related anti-patterns to avoid:

- `--ignore-vuln <synthetic-id>` for the editable error: fragile; the error has no stable ID.
- Maintaining a separate `requirements-runtime.txt` in lock-step with `pyproject.toml`: two sources of truth that drift.
- Skipping pip-audit on PRs that touch dependencies: silently misses CVEs.
