# README freshness — mandatory rule

**Authority:** This file + `tests/architecture/test_readme_freshness.py` (mechanical enforcement) + `docs/PLAN_REQUIREMENTS.md` Gate 5 (documentation update) + `.github/PULL_REQUEST_TEMPLATE.md`.
**Scope:** Any PR that changes the user-facing surface of RytmRandomizer — a new device family, a new CLI command, a new install path, a changed default, a renamed doc.

## The rule

`README.md` is the front door. It must stay accurate with respect to the
user-facing surface. Specifically, **a PR is not done until `README.md`
reflects the change it made**, and the README must always satisfy these
mechanically-checked invariants:

1. **Every registered device is named in the README.** If
   `rytm_randomizer.devices.all_devices()` returns a device, the README
   mentions it (by `device_id`, family name, or `display_name` — the
   `MKII`/`MK2` spelling is normalized).
2. **Every internal README link resolves.** A Markdown link to a
   repo-relative path (`docs/X.md`, `CONTRIBUTING.md`, `./AGENTS.md`) must
   point at a file that exists on disk.
3. **No stale placeholder tokens.** `<owner>`, `TODO`, `FIXME`, `TKTK`,
   `XXX`, and the "will land in a follow-up wave" phrasing are forbidden
   in README prose (fenced code blocks are exempt for template tokens
   like an installer-artifact filename).
4. **The README references `docs/ARCHITECTURE.md`.** A contributor reading
   only the README must be able to find the architecture standard.

This is enforced by `tests/architecture/test_readme_freshness.py`, which
runs in the `architecture` CI job — a **required check**. A PR that adds a
device or command without updating the README fails CI on the PR itself.

## What you MUST do

1. **When a PR adds a device family** (a new `Device` registered through
   `devices/registry.py`): add a paragraph or section to `README.md`
   naming the device and its operator-facing behavior. The PR #44 worked
   example — adding `AnalogFourDevice` — required:
   - The intro paragraph to say "Rytm + Analog Four", not "Rytm".
   - A "Dual-machine target commands" subsection documenting the new CLI command.
   - A safety-rules line for the new device's gating.
2. **When a PR adds or renames a CLI command:** document it in the README's
   command reference.
3. **When a PR adds a new install path / changes a default / changes the
   minimum Python:** update the relevant README section.
4. **When a PR renames or moves a doc:** update every `README.md` link
   that pointed at the old path.
5. **Run the freshness test locally before pushing:**
   ```bash
   python -m pytest tests/architecture/test_readme_freshness.py -q
   ```
6. **Tick the Gate 5 box in the PR body** only after the README is
   genuinely current — not just `docs/STATUS.md`.

## What you MUST NOT do

- **Do not** ship a device-family or CLI-surface PR with `README.md`
  unchanged. The freshness test will fail; if it somehow doesn't, a
  reviewer rejects the PR.
- **Do not** leave placeholder tokens (`<owner>`, `TODO`, ...) in the
  README "to fill in later". Resolve them in the same PR.
- **Do not** link a doc from the README before that doc exists on the
  branch. (PR #44 initially linked `docs/CODEX_CONTRIBUTING.md`, which
  lives on a different unmerged branch — the freshness test caught it.)
- **Do not** add a line to `_KNOWN_PLACEHOLDER_ALLOWLIST` in the test
  without explicit reviewer approval stated in the PR body. The allowlist
  is for genuinely-intentional placeholder-shaped lines (e.g. a fenced
  installer-filename template) and its long-term state is empty.
- **Do not** silently let the test-count / device-count / file-count
  numbers in the README drift. If a number is wrong, fix it.

## Why this is a rule and not just guidance

`README.md` is the single most-read file in the repo — it is what a new
user sees on the GitHub landing page and what a new contributor opens
first. A stale README is worse than no README: it actively misinforms.

PR #44 is the worked example. It added Analog Four as a fully registered
second device, added a `dual-machine-target-report` CLI command, and added
three new subpackages — and shipped with `README.md` describing a
single-machine Rytm-only tool, a wrong GitHub URL (`misteredr` instead of
`buzzijose-hub`), an un-substituted `<owner>` placeholder, a "~1280 tests
in 5-6 minutes" claim that was off by ~2× / ~10×, and a "the architecture
map will land in a follow-up wave" sentence written two waves after the
architecture doc had already landed.

Gate 5 already says "docs updated". But "docs" was being read as
`docs/STATUS.md` only. This rule + the mechanical test make `README.md`
freshness non-optional and self-enforcing.

## When this rule applies

- Any PR adding / removing / renaming a registered `Device`.
- Any PR adding / removing / renaming a CLI command or subcommand.
- Any PR changing the install flow, the launch flags, or the minimum
  Python version.
- Any PR renaming or moving a doc the README links.
- Any PR that changes a count the README quotes (test count, file count,
  device count).

## When this rule does NOT apply

- Pure-internal refactors with no user-facing surface change (the README
  has nothing to update — and the freshness test still passes because the
  invariants still hold).
- A PR whose only doc change IS the README (e.g. a typo fix) — the rule is
  satisfied trivially.
- The freshness test's invariants are always checked regardless; this
  "does not apply" only means there's no *additional* README content to
  write.

## Cross-references

- `tests/architecture/test_readme_freshness.py` — the 4 mechanical checks.
- `docs/PLAN_REQUIREMENTS.md` Gate 5 — documentation update.
- `.github/PULL_REQUEST_TEMPLATE.md` — the Gate 5 checkbox.
- `.claude/rules/device-protocol-strategy.md` — adding a device family (which always triggers this rule).
- `.claude/rules/codex-contribution-guide.md` — the codex pre-flight checklist (README freshness is on it).
- `.claude/skills/docs-update-with-pr/SKILL.md` — the docs-update workflow.
- `CONTRIBUTING.md` § Strict rules — the contributor-facing list (rule 14).
