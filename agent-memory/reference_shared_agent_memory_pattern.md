---
name: reference-shared-agent-memory-pattern
description: "How to make agent memory shareable across Claude Code + Codex + any other tool — put it in agent-memory/ at the repo root, wire via CLAUDE.md import + AGENTS.md include"
metadata: 
  node_type: memory
  type: reference
  originSessionId: b2a9f27a-6737-437c-b063-6015a588d52d
---

# Shared-memory pattern for multi-tool agentic repos

User asked (2026-05-25): "i want you to make sure the memory is shareable across claude and codex. how can we add it to the repo so its reusable?"

## The pattern

Mirrors the **existing skills-sharing pattern** in this repo (`.claude/skills/learned/` is canonical, `.agents/skills` is a symlink so Codex discovers them too). For memory, the canonical store is `agent-memory/` at the repo root with these moving parts:

```
<repo-root>/
├── CLAUDE.md                    # Claude Code reads automatically
├── AGENTS.md                    # Codex CLI reads automatically (per AGENTS.md convention)
├── agent-memory/
│   ├── INDEX.md                 # Human + agent index; mirrors ~/.claude/.../MEMORY.md shape
│   ├── feedback_no_cascade_prs.md
│   ├── feedback_maximum_parallelization_worktrees.md
│   ├── ... (one .md per memory, frontmatter as below)
```

Per-memory file frontmatter (identical to local `~/.claude/projects/<id>/memory/` shape):

```yaml
---
name: <short-kebab-slug>
description: <one-line summary, under 130 chars>
metadata:
  type: user | feedback | project | reference
---
```

## Wiring up

**Claude Code** — add to `CLAUDE.md` at the repo root:

```markdown
## Shared agent memory

This repo's project-scoped agent memory lives in [`agent-memory/`](agent-memory/). Read [`agent-memory/INDEX.md`](agent-memory/INDEX.md) at session start; individual memories are referenced inline by relative link and read on demand when relevant. Same shape as Claude Code's local memory (`~/.claude/projects/<id>/memory/`) so memories can migrate between the two stores freely.
```

(Claude Code respects `@<path>` import directives in `CLAUDE.md` automatically; the `[INDEX.md](...)` link inside CLAUDE.md is enough — Claude reads it as part of session bootstrap.)

**Codex CLI** — add to `AGENTS.md` at the repo root:

```markdown
## Shared agent memory

Per the [AGENTS.md convention](https://agents.md), this repo ships project-scoped agent memory in [`agent-memory/`](agent-memory/). Start with [`agent-memory/INDEX.md`](agent-memory/INDEX.md). Memories are plain markdown with YAML frontmatter; the same files Claude Code reads from `~/.claude/projects/<id>/memory/` locally are also kept in the repo here so the loadout travels with the source.
```

**Any other tool** — point its context-loading config at `agent-memory/`.

## What to put in `agent-memory/` (project-scoped)

- Workflow feedback ("no cascade PRs", "max parallelization", "cleanup worktrees")
- Project facts (the kit-first sysex workflow, the hardware target)
- Reference (where the pre-push hook lives, which Python on this Windows box)
- Code-review-derived lessons (every staff-engineer review finding pattern that should not recur)

## What to keep in `~/.claude/...` (user-personal)

- "User owns an Analog Rytm MK2" — personal hardware, not project fact
- "User prefers single-tab terminal" — personal workflow, not project standard
- Cross-project preferences ("Eddie prefers tight commit messages") — applicable across many repos

## What stays out of both

- API keys, tokens, credentials — never in memory, never in repo
- In-flight PR speculation that may not land — that's a plan/tracker file, not memory

## Sync helper (optional, future)

A small script `scripts/sync_agent_memory.py` (not yet authored) could:
1. Diff `~/.claude/projects/<projectId>/memory/*.md` against `<repo>/agent-memory/*.md`
2. Prompt for each file: "new local memory `<name>` — promote to repo? [y/N]"
3. Copy + commit on confirmation

Skipped for the initial version because manual `cp` is one command and the volume is small (~7 memories at adoption time).

## Real-world origin

Implemented in PR for CODE_REVIEW.md execution sweep (2026-05-25). 7 project-scoped memories migrated from `<local-agent-memory>/` into `agent-memory/`. CLAUDE.md + AGENTS.md updated with import sections. User-personal memories (`hardware_elektron.md`) kept local.
