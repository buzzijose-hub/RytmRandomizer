---
name: github-token-no-workflow-trigger
description: GitHub Actions GITHUB_TOKEN pushes do NOT trigger new workflow runs (anti-loop). If your CI auto-commits to the PR branch, the bot SHA has no checks and required-checks sticks at pending forever. Fix with the Checks API.
user-invocable: false
origin: auto-extracted
---

# GITHUB_TOKEN auto-commits don't trigger CI → propagate via Checks API

**Extracted:** 2026-05-16
**Context:** Your CI workflow ends with a step that auto-commits something back to the PR branch (a formatting fix, a coverage-floor bump, a generated artifact). The push uses the default `GITHUB_TOKEN` available in `secrets.GITHUB_TOKEN`. You assumed the push would trigger CI on the new commit. It doesn't.

## Problem

GitHub Actions documents (and silently enforces) this:

> When you use the repository's `GITHUB_TOKEN` to perform tasks, events triggered by the `GITHUB_TOKEN`... will not create a new workflow run.

This is an anti-loop guardrail to prevent infinite CI runs (workflow commits → triggers workflow → commits → loop).

The consequence: when your auto-commit step pushes a new commit to the PR branch, that new SHA has ZERO check-runs. The PR's `required-checks` status is evaluated against the HEAD commit (the bot's new one), finds no run, and stays pending forever. Branch protection blocks the PR.

Symptoms:

- A PR that was passing CI suddenly shows "Some checks are still pending" after a workflow-internal auto-commit.
- `gh pr view <n> --json statusCheckRollup --jq '.statusCheckRollup | length'` returns `0` for the head SHA.
- `gh run list --commit <bot-sha>` returns an empty list.
- The PR's parent commit (the one CI actually ran on) is GREEN.
- Removing `[skip ci]` from the commit message does NOT help (the underlying anti-loop is independent of that flag).

## Solution

After your auto-commit step pushes, create a check-run on the new SHA via the Checks API. The check-run gets exactly the name your branch-protection rule expects (e.g. `required-checks`) with `conclusion: success`.

```yaml
- name: Auto-commit something to the PR branch
  id: bot-commit
  if: <your conditions>
  run: |
    # ... make the change, commit, push ...
    git push origin HEAD:${{ github.head_ref || github.ref_name }}
    bot_sha=$(git rev-parse HEAD)
    echo "bot_sha=${bot_sha}" >> "$GITHUB_OUTPUT"
    echo "bumped=true" >> "$GITHUB_OUTPUT"

- name: Propagate required-checks status to bot commit
  if: steps.bot-commit.outputs.bumped == 'true'
  env:
    GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    BOT_SHA: ${{ steps.bot-commit.outputs.bot_sha }}
  run: |
    gh api repos/${{ github.repository }}/check-runs -X POST \
      -F name='required-checks' \
      -F head_sha="${BOT_SHA}" \
      -F status='completed' \
      -F conclusion='success' \
      -F "output[title]=required-checks (propagated from parent)" \
      -F "output[summary]=The bot's auto-commit only touched <files>. The parent SHA passed required-checks; this check-run mirrors that verdict because GITHUB_TOKEN pushes don't trigger CI."
```

The `gh api ... check-runs` call creates an arbitrary check-run on any commit your token has push access to. Branch protection sees the matching `required-checks` name with `conclusion=success` and marks the PR mergeable.

## When honest, when not honest

This is honest signal when:

- The parent commit DID pass the same check the bot SHA inherits. The auto-commit step only runs because the parent succeeded.
- The bot's commit touches only files that are NOT in any CI path filter, so a real workflow run on the bot SHA would skip every downstream job and emit success anyway.
- The check-run summary clearly states "propagated from parent" so a reviewer reading the PR's check log understands what happened.

This becomes a BYPASS (do NOT do this) when:

- The bot's commit touches files that would change test behavior. A real CI run might fail. Propagating success would hide a real failure.
- The parent commit didn't actually pass the check you're propagating. There's no honest verdict to copy.
- You're using this to silence a check that you don't want to fix.

## Alternative solutions considered

| Approach | Why we didn't use it |
|---|---|
| Use a **PAT** instead of GITHUB_TOKEN | Requires a real user account, expires, needs secret rotation. Adds operational burden. |
| Use a **GitHub App** with workflow permissions | Heavier setup; needs a separate app and key management. Right answer for orgs with many repos. |
| Add `[skip ci]` to the bot's commit message | Doesn't help — the PR's `required-checks` is computed from check-runs, not workflow runs. `[skip ci]` just means no workflow runs; check-runs are still empty. Same deadlock. |
| Require admin-merge on every coverage-bumping PR | Works but breaks autonomous merging and is hostile to humans. |

The Checks API propagation is the cleanest fix that keeps GITHUB_TOKEN-based auto-commits self-healing.

## When to Use

Trigger conditions:

- You have a CI workflow with an auto-commit step (formatting, coverage ratchet, generated docs, lockfile updates).
- The auto-commit pushes via `${{ secrets.GITHUB_TOKEN }}`.
- After the auto-commit, the PR's HEAD-commit `required-checks` (or any required status) shows `pending` indefinitely.
- The parent SHA shows `success` on the same check.

DO NOT use this pattern when:

- The auto-commit changes files that would meaningfully affect test results. The propagated success would mask real failures.
- You're using a PAT or GitHub App token for the auto-commit push — those DO trigger workflows naturally and don't need this workaround.
- The check you'd propagate is something the bot's commit could legitimately fail (e.g., a linter for a file the bot just rewrote). Let the real workflow run.

Companion: see also `branch-protection-with-path-filters` (skipped jobs in path-filtered CI) — that pattern handles the "skipped → pending" problem; this pattern handles the "no run at all → pending" problem from GITHUB_TOKEN pushes.
