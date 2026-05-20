# PR-body conformance checklist — mandatory rule

**Authority:** This file + [`.github/PULL_REQUEST_TEMPLATE.md`](../../.github/PULL_REQUEST_TEMPLATE.md) (the binding form) + [`docs/PLAN_REQUIREMENTS.md`](../../docs/PLAN_REQUIREMENTS.md) (the 18 gates' source-of-truth definitions).
**Scope:** Every non-trivial PR opened against this repository — not only "plan" PRs. Applies equally to AI-agent contributors (Claude Code, codex, etc.) and human contributors.

## The rule

Every PR body opened against this repo **must** include, verbatim and in order, the two checklist blocks defined in `.github/PULL_REQUEST_TEMPLATE.md`:

1. The **18-gate plan-requirements conformance checklist** (Gate 1 through Gate 18), each rendered as either `[x]` (satisfied) or `[ ] Gate N — N/A: <reason>` (explicitly not applicable, with a one-line justification).
2. The **Strict rules — non-negotiables confirmation block** (the 6 hard rules confirming no hardware in tests, lazy MIDI imports, pinned hardware packages, passive default, no stacked PRs, no `--no-verify`).

These two blocks are not decoration. They are the binding interface between the PR author and the review gate. The 18 gates are defined in [`docs/PLAN_REQUIREMENTS.md`](../../docs/PLAN_REQUIREMENTS.md); the strict rules are defined in [`CONTRIBUTING.md` § Strict rules — non-negotiables](../../CONTRIBUTING.md#strict-rules--non-negotiables) (15 hard rules in the full canon; the PR template surfaces the 6 highest-risk ones for per-PR confirmation).

## What you MUST do

1. **Open the PR using the GitHub template.** `gh pr create` without `--body` will populate from `.github/PULL_REQUEST_TEMPLATE.md`; if you pass `--body` or `--body-file`, the body you pass **must** still contain both blocks. Do not bypass the template by passing a custom body that omits them.
2. **Check every one of the 18 gates.** Each Gate 1–18 line gets exactly one of:
   - `[x] **Gate N** — <gate title>.` (satisfied; nothing more required, though a brief note is welcome)
   - `[ ] Gate N — N/A: <one-line reason>` (explicitly not applicable; the reason is mandatory and reviewer-readable)
3. **Confirm every strict-rule line.** The 6 lines under "Strict rules — non-negotiables" are all `[x]` for a normal PR. If any of them genuinely cannot be `[x]`, the PR is out of scope for this repo's standard review path — escalate before opening.
4. **AI-agent contributors:** treat the template as a strict schema. If your tooling generates the PR body, the generator must emit both blocks. Silently dropping gates (because "this is a small PR") is the failure mode this rule exists to prevent.
5. **Reviewers:** reject PRs missing either block with a one-line comment pointing here. Do not start substantive review until the checklist is present.

## What you MUST NOT do

- **Do not omit any of the 18 gate checkmarks.** A PR body that lists "Gate 1, Gate 3, Gate 7" and skips the rest is non-conforming, even if the skipped gates are obviously N/A — the reader cannot tell the difference between "deliberately N/A" and "the author forgot."
- **Do not replace the checklist with prose** ("all 18 gates pass — see commit messages"). The checklist is machine- and reviewer-scannable; prose is not. The whole point of the form is that a reviewer can vertically scan 18 lines in 10 seconds.
- **Do not use `~~strikethrough~~`** to mark a gate non-applicable. The canonical form is `[ ] Gate N — N/A: <reason>`. Strikethrough hides the gate from a quick scan and loses the reason.
- **Do not collapse multiple gates onto one line** ("Gates 1–4: ✅"). Each gate gets its own line.
- **Do not remove or reorder the template's section headings** (`## Plan-requirements conformance`, `## Strict rules — non-negotiables`). Tooling and reviewer muscle-memory both rely on stable anchors.
- **Do not edit the template inline** (e.g. delete a gate from the rendered body because "it doesn't apply to this repo path"). The 18 gates are repo-wide invariants; per-PR applicability is expressed via `N/A: <reason>`, not by deletion.
- **Do not open stacked PRs to dodge the checklist.** If you're tempted to open three small PRs to avoid filling out the form three times, you're hitting the cascade-merge anti-pattern instead — see `.claude/rules/cascade-merge-pattern.md`.

## Why this is a rule and not just a skill

A skill (e.g. `open-pr`) covers *how* to open a PR. This rule defines *what the PR body must contain to be reviewable*. Three forces make it a rule rather than a guideline:

1. **AI agents will silently drop sections** unless the requirement is hard. The template's footer comment alone is insufficient — agents have demonstrated a tendency to "summarize" the checklist into prose. This file is the authority an agent's review feedback can cite.
2. **The 18 gates encode hard project invariants** (parity, coverage, lint, no-hardware-in-tests, etc.) that are not negotiable per-PR. Surfacing them on every PR forces every contributor — human or AI — to confront each invariant explicitly.
3. **Reviewer time is the bottleneck.** A uniform, scannable checklist lets a reviewer triage 10 PRs in the time an irregular freeform body would take for 2.

## When this rule applies

- Every PR opened against `main`, `modularize-v1.34`, or any integration branch in this repo.
- Every PR opened by an AI-agent contributor, regardless of size.
- Every PR that touches `rytm_randomizer/`, `tests/`, `docs/`, `.github/`, `.claude/`, or the repo root.
- Bundle PRs (cascade-merge) — the checklist covers the bundle as a whole; per-WS notes go in the body's "What changed" section.

## When this rule does NOT apply

- **Trivial typo / comment-only PRs** that touch a single Markdown file and change no behavior, no tests, no CI, and no public docs may use a shorter body with a one-line summary. "Trivial" here means: the diff is ≤10 lines, only `.md` or comments, no semantic change. Any uncertainty → use the full template.
- **Draft PRs explicitly marked `[WIP]`** may temporarily omit gate checkmarks while the work is in flight, but must complete the checklist before marking "Ready for review." Reviewers will not start substantive review on a `[WIP]` PR with an incomplete checklist.
- **Bot-authored PRs** (Dependabot, etc.) are exempt — the rule binds human and human-agent authored PRs.

## Cross-references

- [`.github/PULL_REQUEST_TEMPLATE.md`](../../.github/PULL_REQUEST_TEMPLATE.md) — the binding template; the source of the two checklist blocks this rule enforces.
- [`docs/PLAN_REQUIREMENTS.md`](../../docs/PLAN_REQUIREMENTS.md) — the canonical definitions of Gates 1–18 (titles, what satisfies them, how they map to CI). Gate 17 (abstraction reuse and genericization) and Gate 18 (architecture-doc and diagram freshness) are the two newest gates.
- [`CONTRIBUTING.md` § Strict rules — non-negotiables](../../CONTRIBUTING.md#strict-rules--non-negotiables) — the 15 hard rules; the PR template surfaces the 6 highest-risk for per-PR confirmation.
- [`.claude/rules/cascade-merge-pattern.md`](./cascade-merge-pattern.md) — bundle WSes into one PR rather than opening stacked PRs (Strict Rule "No stacked PRs" on the template).
- [`.claude/rules/device-protocol-strategy.md`](./device-protocol-strategy.md) — the cross-machine seam contract; PRs touching `devices/` must satisfy Gate 9 + Gate 6 against this rule.
- [`.claude/rules/parity-fixture-discipline.md`](./parity-fixture-discipline.md) — Gate 2 (V1.34 parity) is binding; fixture regeneration requires explicit approval linked from the PR body.
- [`.claude/rules/coverage-gate-100pct.md`](./coverage-gate-100pct.md) — Gate 1 (100% branch on touched files) is binding; this rule defines the mechanical check.
- `.claude/skills/open-pr/SKILL.md` (and the user-level `open-pr` skill) — operational details for creating PRs; this rule constrains what those skills emit.
