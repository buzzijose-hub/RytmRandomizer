---
name: project-security-cap-mirroring
description: "Every pyproject security upper-cap needs a dependabot ignore twin + a tie-test, or dependabot opens PRs that defeat the cap (PR #211 / MAL-2026-4750 lesson)"
metadata:
  node_type: memory
  type: project
---

# Security-cap mirroring: pyproject cap ⇔ dependabot ignore ⇔ tie-test

Lesson from PR #211 (dependabot, 2026-07): `pyproject.toml` caps FastAPI at
`<0.136.3` specifically to exclude the release pip-audit flags as
**MAL-2026-4750**. Dependabot does not read the intent behind an upper cap —
it opened a PR to "update the requirements to permit the latest version",
i.e. a PR whose entire purpose was to remove the security cap.

## The rule

Every security-motivated upper bound in `pyproject.toml` must have:

1. **A dependabot ignore twin** in `.github/dependabot.yml` — an
   `ignore:` entry (dependency-name + the blocked version range) so
   dependabot stops proposing the capped upgrade.
2. **A tie-test** (architecture test) that parses both files and fails if a
   security cap exists without its ignore twin (or vice versa), so the two
   files cannot drift apart silently.
3. **A comment at the cap** naming the advisory (e.g. MAL-2026-4750) so a
   future bump is a deliberate, informed decision.

This mirrors the existing `mido` / `python-rtmidi` pattern: those hardware
pins already have dependabot ignore entries. Never merge a dependabot PR that
widens a capped range — close it and fix the mirroring instead.
