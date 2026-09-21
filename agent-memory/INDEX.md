# Shared agent memory — RytmRandomizer

This directory ships **project-scoped agent memory** that travels with the repo so every AI agent (Claude Code, Codex CLI, any other) reads the same observations. The pattern mirrors the existing `.agents/skills` symlink: one source of truth, both tools discover it.

## Why a repo-level memory directory

- Claude Code's default memory lives at `~/.claude/projects/<projectId>/memory/` — local to a single machine, not in version control
- Codex CLI doesn't read that location at all
- Without a shared store, every machine + every agent starts fresh and re-learns the same patterns
- This dir gives both tools a stable file path they can read via their respective context-injection mechanisms (Claude: `@agent-memory/INDEX.md` from `CLAUDE.md`; Codex: include from `AGENTS.md`)

## How agents discover this

**Claude Code:** [`CLAUDE.md`](../CLAUDE.md) at the repo root contains a `@agent-memory/INDEX.md` import directive. Claude loads `CLAUDE.md` automatically at session start; the import directive pulls this index in. Individual memories are referenced inline below via relative links — Claude reads them on demand when relevant.

**Codex CLI:** [`AGENTS.md`](../AGENTS.md) at the repo root contains a "Shared memory" section that points here. Codex reads `AGENTS.md` automatically per the AGENTS.md convention.

**Any other tool:** add this directory to your tool's context-loading config; the files are plain markdown with YAML frontmatter (`name` / `description` / `metadata.type` fields).

## How to add a new memory

1. Create a new `.md` file here. Follow the existing frontmatter shape (`name`, `description`, `metadata.type` = `user` / `feedback` / `project` / `reference`).
2. Add a one-line entry to this INDEX with a link.
3. Commit + push as part of whatever PR makes the memory relevant. The next agent on the next machine sees it without configuration.

## How to update an existing memory

Edit the file in place. The frontmatter `description` and the body should always reflect current truth. Memories that turn out to be wrong should be **removed** (not appended with "edit: this is wrong now") — a stale memory is worse than no memory.

## User-private memories stay out

Memories about the human's hardware setup, personal preferences across multiple projects, etc. **stay in `~/.claude/projects/<id>/memory/`** — they're not project facts. Only put memory here if it would be useful to another contributor / agent working on this repo.

---

## Index

### Workflow feedback (how this team operates)

- [No cascade PRs](feedback_no_cascade_prs.md) — ship multi-finding sweeps as ONE bundled PR (per wizard/Phase-3 precedent), not a cascade. Sub-branches are intermediate worktrees only.
- [Maximum parallelization + worktrees](feedback_maximum_parallelization_worktrees.md) — DEFAULT mode: fan out implementer agents one-per-worktree, in parallel, single message. Sequential is the exception.
- [Cleanup worktrees as you go](feedback_cleanup_worktrees_as_you_go.md) — `git worktree remove` immediately after each branch merges into the bundle; don't batch cleanup to the end.
- [Code review fan-out](feedback_code_review_fanout.md) — code reviews: spawn one targeted agent per dimension in parallel, synthesize into one PR comment.
- [Verify composition, not agents](feedback_verify_composition_not_agents.md) — parallel agents each verifying themselves produce individually-green work that does not compose; a green report that DID NOT RUN is a red report. Parse the runner's summary, take one integration checkpoint.

### Project facts (load-bearing context about this codebase)

- [Analog Rytm SysEx project](project_rytm_sysex.md) — kit-first generator, offline-only, file-drop loading workflow.
- [Python tooling pitfalls](python_tooling_pitfalls.md) — black target-version must match CI py3.11; don't suppress xdist with `-o addopts=''` for normal runs (3× slowdown); only suppress for `PARITY_CAPTURE_MODE=1`.
- [Armed entry-point seam](project_armed_entry_point_seam.md) — Live-but-Passive MIDI boundary: inputs open freely, all transmit routes through the `senders` ArmedApply seam; enforced by `test_armed_entry_points.py` + `test_repo_root_perimeter.py`.
- [Cockpit live Patch Genome and targeted live KIT state](project_cockpit_live_patch_genome.md) — current dual-device capture, Rytm target/lock/send authority, blocked A4 saved-KIT mapping, installer launch, and studio continuation truth.
- [Security-cap mirroring](project_security_cap_mirroring.md) — every pyproject security upper-cap needs a dependabot ignore twin + a tie-test, or dependabot opens PRs that defeat the cap (PR #211 / MAL-2026-4750).

### Reference (where to look up things)

- [Pre-push hook Windows shim](reference_pre_push_hook_windows_shim.md) — `.githooks/pre-push` Windows Store python detection was fixed in PR #110; pre-PR-110 worktrees need `--no-verify` for non-code pushes.
- [Shared agent memory pattern](reference_shared_agent_memory_pattern.md) — how to make memory shareable across Claude Code + Codex + any agent (the very pattern this directory implements). Read this when extending the system.
