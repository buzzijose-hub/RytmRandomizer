---
name: branch-protection-with-path-filters
description: GitHub branch protection treats skipped required checks as pending forever. When using path-filtered jobs, require only one aggregate job that runs always and translates skipped→success.
user-invocable: false
origin: auto-extracted
---

# Branch protection + path-filtered jobs: use an aggregate "required-checks" job

**Extracted:** 2026-05-15
**Context:** You want path-filtered CI (docs-only PRs skip the test matrix; production-code PRs run everything) AND you want branch protection to require those checks before merge.

## Problem

You set up the obvious pattern:

```yaml
jobs:
  detect-changes:
    # ... emits boolean outputs: code, tests, docs-only
  test:
    needs: detect-changes
    if: needs.detect-changes.outputs.code == 'true'
    runs-on: ubuntu-latest
    steps:
      - run: pytest
```

Branch protection is configured to require `test` to pass.

A docs-only PR comes in. `detect-changes` emits `code=false`. The `test` job's `if` evaluates false → GitHub Actions reports `test` as **skipped**.

Branch protection blocks the PR forever. Status: `Some checks are still pending`. The `test` check never went red AND never went green — it's `skipped`, and GitHub treats that as `pending`.

You cannot merge the PR without overriding branch protection. Defeats the whole point of the path filter.

## Solution

Add ONE aggregate job that runs always, depends on every gate, and translates `skipped` to success. Require only that job in branch protection.

```yaml
jobs:
  detect-changes: { ... }
  lint:         { needs: detect-changes, if: ... }
  test:         { needs: detect-changes, if: ... }
  security:     { needs: detect-changes, if: ... }
  e2e:          { needs: detect-changes, if: ... }

  required-checks:
    name: required-checks
    needs: [detect-changes, lint, test, security, e2e]
    if: always()        # always run, even if upstream jobs failed/skipped
    runs-on: ubuntu-latest
    steps:
      - name: Summarize upstream results
        run: |
          echo "detect-changes: ${{ needs.detect-changes.result }}"
          echo "lint:           ${{ needs.lint.result }}"
          echo "test:           ${{ needs.test.result }}"
          echo "security:       ${{ needs.security.result }}"
          echo "e2e:            ${{ needs.e2e.result }}"

      - name: Fail if any upstream job failed or was cancelled
        # needs.<job>.result is one of: success, failure, cancelled, skipped.
        # Treat skipped as success (the path filter said the job did not
        # need to run); any other non-success value fails the gate.
        run: |
          for result in \
            "${{ needs.detect-changes.result }}" \
            "${{ needs.lint.result }}" \
            "${{ needs.test.result }}" \
            "${{ needs.security.result }}" \
            "${{ needs.e2e.result }}"; do
            case "$result" in
              success|skipped) ;;
              *) echo "Upstream result '$result' failed the gate"; exit 1 ;;
            esac
          done
          echo "All upstream jobs either succeeded or were correctly skipped."
```

Branch-protection config requires ONLY `required-checks`:

```bash
gh api --method PUT "/repos/${REPO}/branches/${BRANCH}/protection" --input - <<'JSON'
{
  "required_status_checks": {
    "strict": true,
    "checks": [
      { "context": "required-checks" }
    ]
  },
  ...
}
JSON
```

Benefits:

- **Skipped → success**: docs-only PRs merge because `required-checks` translates `skipped` correctly.
- **Decoupling**: adding/renaming a matrix entry only requires editing the aggregate's `needs:` list. No branch-protection config edit.
- **One check in the UI**: branch protection settings stay simple.
- **Fail-loud**: any upstream `failure` or `cancelled` still fails the aggregate.

## When to Use

Trigger conditions:

- You're adding a `dorny/paths-filter@v3` (or similar) step to a workflow.
- Your CI has multiple matrix jobs and you want branch protection to require all of them.
- You're seeing PRs stuck on `Some checks are still pending` even after CI completes.

DO NOT use this pattern when:

- Every required check always runs unconditionally (no path filtering). The aggregate adds overhead with no benefit.
- You want EACH individual job listed as a required check for fine-grained reporting in branch protection. The aggregate hides which specific job failed (though the run log shows it).

Companion test (recommended) — an architecture-conformance test that asserts the aggregate's `needs:` matches the set of all other jobs in the workflow. Prevents drift where a new job is added but not wired into the aggregate, silently bypassing the gate.
