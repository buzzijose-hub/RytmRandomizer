---
name: github-actions-matrix-conditional
description: Conditionally include matrix entries in GitHub Actions using fromJSON, not exclude+ternary. The ternary form silently invalidates the entire workflow when it expands to an empty value.
user-invocable: false
origin: auto-extracted
---

# GitHub Actions: use fromJSON for conditional matrices

**Extracted:** 2026-05-15
**Context:** You want a CI matrix that includes macOS on pushes to main but skips it on pull_request events (to keep PR turnaround fast when the macOS runner queue is long).

## Problem

The intuitive approach is to put a template ternary inside `strategy.matrix.exclude`:

```yaml
strategy:
  matrix:
    os: [windows-latest, macos-latest, ubuntu-latest]
    exclude:
      - os: ${{ github.event_name == 'pull_request' && 'macos-latest' || '' }}
```

This LOOKS like it conditionally excludes macOS only on PRs. On push events the template evaluates to `os: ''` (empty string), which the exclude list "should" treat as a no-op exclude rule.

**It does not.** GitHub Actions silently rejects the workflow entirely. You get:

- The workflow does not appear in the **Actions** tab for new runs.
- No `workflow_run` events.
- `gh run list` returns no rows for new commits.
- Branch-protection PRs sit pending forever because the required-check status never lands.
- The workflow file still validates as YAML (`python -c "import yaml; yaml.safe_load(open('.github/workflows/test.yml'))"`) so local validation passes.
- The GitHub web UI Actions tab also shows nothing helpful — the failure is silent.

Cause: GitHub Actions evaluates the template at workflow-parse time, and an empty-string `os` value in an exclude entry is rejected by the matrix parser. The whole workflow is then invalid and never starts.

## Solution

Build the `os:` list ITSELF from a JSON string that is conditional on the event:

```yaml
strategy:
  matrix:
    os: ${{ fromJSON(github.event_name == 'pull_request' && '["windows-latest", "ubuntu-latest"]' || '["windows-latest", "macos-latest", "ubuntu-latest"]') }}
    python-version: ["3.11"]
```

This is the GitHub-documented pattern for variable-shape matrices and parses cleanly. The template evaluates BEFORE matrix expansion to a literal array of strings.

Verify after editing:

```bash
# Local YAML parse:
python -c "import yaml; data=yaml.safe_load(open('.github/workflows/test.yml')); print('YAML ok, jobs:', list(data['jobs'].keys()))"

# After pushing, confirm GitHub started a run:
gh run list --commit "$(git rev-parse HEAD)" --limit 5
```

If `gh run list --commit <sha>` returns an empty list for your push, the workflow is invalid even when YAML parses locally — the most likely cause is a malformed conditional matrix.

## When to Use

Trigger conditions:

- You want a matrix entry (OS, Python version, etc.) to appear on some event types but not others.
- You want macOS / Windows runners only on `main` pushes and the weekly schedule, not on every PR.

Symptom that tells you you have this bug:

- `gh run list --commit <sha>` is empty for a commit you just pushed.
- The workflow ran on the PREVIOUS commit but not this one.
- The workflow file YAML-parses locally.
- No error in the Actions tab — workflow simply does not start.

Recovery:

1. Diff `.github/workflows/*.yml` against the last commit whose CI ran successfully.
2. If the only change is in `matrix.exclude` with a template, that's almost certainly the cause.
3. Rewrite as `matrix.os: ${{ fromJSON(...) }}` per the pattern above.
4. Force-push or amend; new commit triggers a clean run.
