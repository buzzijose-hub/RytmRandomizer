# Cascade-merge pattern (bundle WSes into one PR)

**Authority:** This file + `.claude/skills/learned/cascade-merge-pattern/SKILL.md` (the operational details).
**Scope:** Any autonomous multi-WS refactor in this repo when the base branch's protection requires per-PR human approval.

## The rule

When the base branch requires per-PR human approval (`gh pr merge --squash` would block waiting for review), do **not** open N PRs in a stalled cascade. Instead:

1. Run each WS's implementation phase in parallel on disjoint files (see `.claude/skills/learned/parallel-agent-bundle/`).
2. Bundle all WS branches into one integration branch via `git merge --no-ff`.
3. Resolve the shared-file conflicts deterministically (keep both entries on `docs/STATUS.md` "Recent Cleanup"; merge-by-WS-id on `docs/SIMPLIFICATION_STATE.json`).
4. Open one PR for the bundle.

This collapses N human approvals into 1.

## Why this is a rule and not just a skill

The skill (`.claude/skills/learned/cascade-merge-pattern/SKILL.md`) explains *how*. This rule mandates *when* — if an autonomous orchestrator is wired for one-PR-per-WS under approval gates, the orchestrator is broken. Future plans inherit this rule and structure their kickoff accordingly.

## When the per-PR cascade still applies

If the base branch is unprotected or allows agent auto-merge (the PRs #22-#28 setup), the per-PR cascade is preferred — it gives independent revert capability and finer-grained reviewer attention.

## Cross-references

- `.claude/skills/learned/cascade-merge-pattern/SKILL.md` — operational details + keep-both rule mechanics.
- `.claude/skills/learned/parallel-agent-bundle/SKILL.md` — how to dispatch the WSes themselves.
- `docs/SIMPLIFICATION_RUN_REPORT.md` — the concrete run (PR #35) this rule was derived from.
- `docs/PLAN_REQUIREMENTS.md` Gate 16 #6 ("Auto-merge cascade") — the parent requirement.
