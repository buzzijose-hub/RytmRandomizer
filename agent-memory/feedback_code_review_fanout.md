---
name: code-review-fanout-per-dimension
description: "Code reviews must fan out to one agent per dimension, not one wide agent doing all dimensions"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4c24068c-92ab-45c0-bd43-7201536e4825
---

Code reviews must be done as **one targeted agent per review dimension**, dispatched in parallel — not a single wide agent covering every dimension.

**Why:** The user observed that targeted reviews outperform wide reviews — a single agent asked to check architecture + maintainability + observability + docs + abstraction + parity + security at once does each one shallowly. One agent per dimension goes deep on its dimension.

**How to apply:** When asked to review a PR / diff / changes (including the post-push `code-review` skill and the codex hook handoff), spawn parallel `Agent` calls — e.g. one for maintainability, one for observability, one for docs/diagram freshness, one for abstraction reuse, one for architecture/import-direction compliance, one for parity + test hygiene, one for security. Each agent gets a prompt scoped to ONLY its dimension. Then synthesize the per-dimension verdicts into the single Critical/Important/Minor/Abstraction/Docs report and post one consolidated PR comment. The 18 plan-requirement gates (`docs/PLAN_REQUIREMENTS.md`) still define the dimensions; the change is one-agent-per-dimension instead of one-agent-all-dimensions.

Repo: RytmRandomizer (`C:\Users\Edward.Rosado\Desktop\MusicProduction\RytmRandomizer`).
