#!/usr/bin/env bash
#
# apply-branch-protection.sh
#
# Applies branch protection to the `main` branch of the RytmRandomizer repo.
# An admin runs this ONCE after `main` is created as the integration branch.
# It is NOT run from CI or from a worktree.
#
# Requires: gh CLI authenticated as a repo admin.
# See docs/BRANCH_PROTECTION.md for the human-readable description.

set -euo pipefail

REPO="${REPO:-buzzijose-hub/RytmRandomizer}"
BRANCH="${BRANCH:-main}"

# Required status checks.
# This list intentionally requires ONLY the `required-checks` aggregate
# job from .github/workflows/test.yml. That job depends on every actual
# gate (lint, security, architecture, test x3, e2e x3) and enforces:
#   "every upstream job either succeeded or was correctly skipped".
#
# Why one aggregate instead of seven individual checks:
#   * Path-filtered jobs (e.g. test matrix skipping on docs-only PRs)
#     report status `skipped` to GitHub. By default branch protection
#     treats `skipped` as pending and blocks the PR forever. The
#     aggregate job always runs and translates `skipped` to `success`.
#   * Adding/removing a matrix entry no longer requires editing this
#     payload — only the aggregate job's needs: list.
#   * Branch protection UI is simpler (one check, one source of truth).
#
# The aggregate job is the contract; the individual jobs are the
# implementation detail. Do not add the individual job names back here.
read -r -d '' PAYLOAD <<'JSON' || true
{
  "required_status_checks": {
    "strict": true,
    "checks": [
      { "context": "required-checks" }
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "required_approving_review_count": 1
  },
  "required_conversation_resolution": true,
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON

echo "Applying branch protection to ${REPO}@${BRANCH} ..."
gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  "/repos/${REPO}/branches/${BRANCH}/protection" \
  --input - <<<"${PAYLOAD}"

echo "Branch protection applied to ${REPO}@${BRANCH}."
