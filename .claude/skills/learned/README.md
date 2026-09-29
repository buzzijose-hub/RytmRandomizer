# Learned skills

Hard-won patterns extracted from real debugging sessions on this repo. Each subdirectory is a Claude Code "skill" that future agents (and human contributors) can consult when they hit the same problem.

These are NOT generic best-practices. Each one solves a *specific* bug or class of bugs we ran into, often after the obvious fix failed. The frontmatter `origin: auto-extracted` marks them as session-derived rather than written from a template.

## Index

| Skill | When it bites you |
|---|---|
| [parallel-agents-need-git-worktrees](parallel-agents-need-git-worktrees/SKILL.md) | You're dispatching 2+ agents in parallel and one reports "the file changed under me" — they're sharing a working tree. Branches alone are not enough isolation. |
| [agent-report-did-not-run](agent-report-did-not-run/SKILL.md) | A parallel agent reports "all green" but its suite errored at collection because a sibling's module was absent — zero tests ran. Parse the runner's summary; DID NOT RUN is a third outcome. |
| [cross-language-seam-drift-guard](cross-language-seam-drift-guard/SKILL.md) | Two sides agree on the payload and disagree on the channel (IPC emit vs DOM listener). Both suites green, nothing crosses. Pin the CALL FORM, or generate one side from the other. |
| [worktree-base-and-lint-traps](worktree-base-and-lint-traps/SKILL.md) | Harness worktrees branch from the ORIGINAL HEAD (agents silently get a stale base), and repo-root lint walks into siblings' half-written files and fails your pre-push on their code. |
| [github-actions-matrix-conditional](github-actions-matrix-conditional/SKILL.md) | After a workflow edit, `gh run list --commit <sha>` is empty even though the YAML parses. Conditional matrix with `exclude: + ternary` silently invalidates the workflow. |
| [pip-audit-editable-install](pip-audit-editable-install/SKILL.md) | `pip-audit --strict` fails with "Dependency not found on PyPI" or "distribution marked as editable" because the project isn't published. `--skip-editable` does NOT help. |
| [branch-protection-with-path-filters](branch-protection-with-path-filters/SKILL.md) | PR stuck on "Some checks are still pending" forever. Path-filtered jobs that skipped are treated as pending by branch protection. |
| [coverage-py-blended-vs-pure-branch](coverage-py-blended-vs-pure-branch/SKILL.md) | `.coveragerc` `fail_under` says 86% passes but a custom ratchet script says branch coverage is 78%. Both are right — they measure different things. |

## How agents use these

Claude Code agents loaded in this repo see the `.claude/skills/learned/` directory automatically. When a triggering condition matches, the agent reads the skill before acting. The skills are short on purpose — they encode the *non-obvious* part, not the whole tutorial.

## How to add a new one

When you spend more than 30 minutes diagnosing something that turns out to be a known-bad pattern, that's a candidate. Use the format from any existing skill:

1. Create `.claude/skills/learned/<kebab-case-name>/SKILL.md`.
2. Frontmatter with `name`, one-line `description`, `user-invocable: false`, `origin: auto-extracted`.
3. Body covers **Problem** (what bites you, including the diagnostic symptoms), **Solution** (the actual fix, with working code), and **When to Use** (trigger conditions + when not to).

Add a row to the index table above.
