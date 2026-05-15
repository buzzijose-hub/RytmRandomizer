---
name: docs-update-with-pr
description: PRs that touch `rytm_randomizer/` or `pyproject.toml` MUST also touch at least one of `docs/`, `README.md`, or `CONTRIBUTING.md`. This is enforced by the CI `docs-gate` job. Use this skill before opening a PR that modifies code or dependencies, when CI fails with a "docs-gate" failure, or when a contributor asks "do I really need to update docs for a pure refactor?" The answer is yes — even a one-line `docs/STATUS.md` bump counts. Docs rot is the dominant onboarding problem in this repo; tying doc touches to code changes is how we prevent drift.
---

# Update docs with every code-touching PR

If your PR touches `rytm_randomizer/` or `pyproject.toml`, it MUST also touch at least one of:

* `docs/` (any file under `docs/`)
* `README.md`
* `CONTRIBUTING.md`

Otherwise the CI `docs-gate` job fails the PR.

## Why this exists

Docs rot is the dominant onboarding problem in this repo. New contributors clone, read `README.md` and `docs/ARCHITECTURE.md`, and find them describing a system that doesn't quite exist anymore. Every PR that ships code without touching docs makes the gap bigger.

The fix is a forcing function: you cannot merge a code change without touching docs. Most of the time this is a 30-second edit. It is never a real burden, and the cumulative effect is that docs stay roughly in sync with the code.

## What counts as "touching docs"

Anything that genuinely updates documentation:

* Updating `docs/ARCHITECTURE.md` to reflect a new module or moved responsibility.
* Adding a section to `README.md` about a new CLI flag.
* Bumping `docs/STATUS.md` to record what's now done / in-progress / next.
* Adding an example to `docs/EXAMPLES.md`.
* Clarifying setup in `CONTRIBUTING.md`.
* Adding/updating a docstring file that lives under `docs/`.

## "But mine is a pure refactor — there's nothing to document"

Common objection. Three answers:

1. **A rename is documentation-relevant.** If you renamed `KitBuilder` to `KitAssembler`, the architecture doc that mentions `KitBuilder` is now wrong. Update it.
2. **An internal reshape changes the mental model.** If you split a module, the diagram or module list in `docs/ARCHITECTURE.md` is now slightly stale. Update it.
3. **If genuinely nothing else changed, bump `docs/STATUS.md`.** Add a one-line entry: `- 2026-05-15: refactored guardrails internals (no public API change).` That's enough. The point is to keep the docs alive — to leave fingerprints — not to write an essay.

There is always a one-line update available. The bar is "leave a fingerprint", not "write a chapter."

## When CI fails with "docs-gate"

You'll see something like:

```
docs-gate: PR touched rytm_randomizer/ but no files under docs/, README.md, or CONTRIBUTING.md.
```

The fix is one line in `docs/STATUS.md`, or whichever doc is most relevant to your change. Commit, push, CI passes.

Do not "fix" this by reverting your code change. Do not "fix" this by editing the workflow to skip the check. Do not "fix" this by touching `docs/STATUS.md` with a trailing-whitespace-only change — at code-review time we'll flag that as cheating the gate.

## When `pyproject.toml` is the only thing that changed

Bumping a dependency version is also a docs-worthy event. At minimum, note it in `docs/STATUS.md`:

```
- 2026-05-15: bumped ruff to 0.5.0 (no behavioral change expected).
```

Two minutes. Future you, debugging a weird lint behavior, will thank past you for the breadcrumb.

## When to invoke this skill

- Before opening any PR that touches `rytm_randomizer/` or `pyproject.toml`.
- When CI fails with a `docs-gate` failure.
- When a contributor argues a refactor "doesn't need docs."
- When a code-review reveals stale docs — likely a previous PR slipped through before this gate existed.
