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
# These context names must match the job names produced by .github/workflows/test.yml.
# NOTE: this list gates every merge to main. The three required checks below:
#   - "architecture" (WS-T): the gated architecture-conformance suite
#       (tests/architecture/) — fast, ubuntu-only, must stay green.
#   - "test (<os>, py3.11)" (WS-E): full pytest suite on each of the 3 OSs.
#   - "e2e (<os>, py3.11)" (WS-R): the V1.34 canonical operator-command flow
#       against MockMidiSender, deterministic, must stay green on each OS.
# When the WS-I coverage job lands, add "coverage" here so it also gates.
# Do NOT remove the 3-OS matrix entries — the canonical operator-command
# flow gates every merge to main on every supported platform.
read -r -d '' PAYLOAD <<'JSON' || true
{
  "required_status_checks": {
    "strict": true,
    "checks": [
      { "context": "architecture" },
      { "context": "test (windows-latest, py3.11)" },
      { "context": "test (macos-latest, py3.11)" },
      { "context": "test (ubuntu-latest, py3.11)" },
      { "context": "e2e (windows-latest, py3.11)" },
      { "context": "e2e (macos-latest, py3.11)" },
      { "context": "e2e (ubuntu-latest, py3.11)" }
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
