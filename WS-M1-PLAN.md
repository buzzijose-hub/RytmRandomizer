# WS-M1 — Docs Curation Pass

**Worktree:** `RytmRandomizer-worktrees/ws-m1-docs-curation`
**Branch:** `refactor/docs-curation`
**Base:** `modularize-v1.34 @ 0bd46aa`
**Per:** `docs/PLAN_REQUIREMENTS.md` (16 gates; Gates 1/3/4/6/7/9/10/11/12/13 N/A — docs-only).

## Overview

Reorganize `docs/` from 33 markdown files into a contributor-oriented active set (≤12 onboarding files) + `docs/archive/` keep-pile. Add `docs/README.md` index + small `CONTRIBUTING.md` addition pointing at `ARCHITECTURE.md` §6. Zero behavior change; pure doc reorg.

## Variance vs. brief

| Brief | Reality at 0bd46aa | Resolution |
|---|---|---|
| "35 .md files" | 33 .md files | Inventory below has 33. |
| `docs/SIMPLIFICATION_STATE.json` exists | Created by orchestrator on first wake-up | Listed as in-flight; not blocking. |
| `docs/SIMPLIFICATION_RUN_LOG.md` exists | Created by orchestrator on first wake-up | Same. |

## Inventory (33 .md files, classified)

| Classification | Count |
|---|---|
| KEEP-active (onboarding) | 11 |
| KEEP-active (ops references, exempt from 12-cap) | 4 |
| ARCHIVE (incl. 2 PROMOTE-then-ARCHIVE) | 19 |
| **Total** | 33 |

**KEEP-active (11 onboarding):** ARCHITECTURE.md, ARCHITECTURE_DIAGRAMS.md, STATUS.md, SIMPLIFICATION_PLAN.md, PLAN_REQUIREMENTS.md, V134_OPERATOR_COMMAND_SURFACE_REFERENCE.md, COVERAGE_POLICY.md, MODULARIZATION_RULES.md, OBSERVABILITY.md, STYLE_ANALYSIS.md, + new docs/README.md.

**KEEP-active (4 ops references, exempt from 12-cap):** BRANCH_PROTECTION.md, BUILDING_INSTALLERS.md, MANUAL_HARDWARE_VALIDATION.md, LOCAL_DEV_TOOLING_NOTES.md. Each is referenced from CI workflows / pyproject.toml / Scripts/ and archiving requires cross-WS edits.

**ARCHIVE (19):**
- Codex briefs (2): CODEX_MODULARIZATION_PROTOCOL.md, CODEX_REFACTOR_PROMPT.md
- Collaborator-review intake/triage (8): COLLABORATOR_QUICKSTART.md (PROMOTE), COLLABORATOR_REVIEW_BRANCH_INTAKE.md, _INTAKE_REVIEW.md, _INTAKE_CHECKPOINT.md, _STATUS_VISIBILITY_CHECKPOINT.md, _STATUS_VISIBILITY_CHECKPOINT_REVIEW.md, COLLABORATOR_REVIEW_TRIAGE_TEMPLATE.md, _REVIEW.md, COLLABORATOR_TRIAGE_TEMPLATE_STATUS_VISIBILITY_CHECKPOINT.md
- Project identity (2): PROJECT_IDENTITY_NAME_SHORTLIST.md, PROJECT_IDENTITY_RENAME_PLAN.md
- Checkpoints (3): PROJECT_STATUS_API_HARDENING_VISIBILITY_CHECKPOINT.md, PUBLIC_API_HARDENING_PROGRESS_CHECKPOINT.md, RUNTIME_PLAN_PUBLIC_API_EXPORTS_CHECKPOINT.md
- Reference/historical (3): HARDWARE_MANUAL_REFERENCE_INVENTORY.md, PASSIVE_CLI_OPERATOR_QUICKSTART.md (PROMOTE), TRIAGE_REPORT.md

## Critical reference-rot fix

`rytm_randomizer/project_status_report.py:108-109` hardcodes `"docs/COLLABORATOR_REVIEW_TRIAGE_TEMPLATE.md"` + `_REVIEW.md`. Both files move to `docs/archive/`. **Update constants + test fixture + golden text in lockstep:**
- `rytm_randomizer/project_status_report.py:108-109` → `"docs/archive/..."`
- `tests/test_project_status_report.py:177-178, 472-473` mirror.
- `tests/fixtures/cli_project_status_report_expected.txt:71-72` golden text update.

Also update `docs/STATUS.md:53-57` cross-links pointing at to-be-archived files.

## Migration phases

1. **Create `docs/archive/` + README** (one commit).
2. **`git mv` 19 files** to `docs/archive/` (one commit; history preserved).
3. **Reference-rot fixes** (project_status_report.py + test + fixture + STATUS.md links).
4. **Write `docs/README.md`** index (~100 LOC) classifying Active vs Archive.
5. **Edit `CONTRIBUTING.md`** "Common contributor tasks" section after "Data vs code".
6. **STATUS.md "Recent Cleanup" entry** for 2026-05-18.
7. **doc-updater** + acceptance + `gh pr create`.

## Coordination with WS-M4

Both edit CONTRIBUTING.md. **Resolution:**
- Whoever opens PR first wins.
- WS-M1 inserts "Common contributor tasks" after "Data vs code" H2.
- WS-M4 appends `pytest -m fast` paragraph to existing "Verification gate" H2.
- Sections are textually disjoint; cascade auto-rebase keeps both.

## Acceptance commands

```powershell
# Narrowed onboarding-only check (the contractual cap)
$onboarding = @('README.md','ARCHITECTURE.md','ARCHITECTURE_DIAGRAMS.md','STATUS.md','SIMPLIFICATION_PLAN.md','PLAN_REQUIREMENTS.md','V134_OPERATOR_COMMAND_SURFACE_REFERENCE.md','COVERAGE_POLICY.md','MODULARIZATION_RULES.md','OBSERVABILITY.md','STYLE_ANALYSIS.md')
if ($onboarding.Count -gt 12) { Write-Error "Onboarding count > 12"; exit 1 }

# Broken-link grep
$links = Select-String -Path docs/*.md, docs/archive/*.md, CONTRIBUTING.md, README.md -Pattern '\]\(([^)]+)\)' -AllMatches | ForEach-Object { $_.Matches } | ForEach-Object { $_.Groups[1].Value } | Where-Object { $_ -notmatch '^https?://' -and $_ -notmatch '^#' }
$broken = @()
foreach ($link in $links) {
  $path = $link -replace '#.*$',''
  if (-not (Test-Path $path) -and -not (Test-Path "docs/$path") -and -not (Test-Path "docs/archive/$path")) { $broken += $link }
}
if ($broken) { Write-Error "Broken links: $broken"; exit 1 }

# git mv history preserved
foreach ($name in (Get-ChildItem docs/archive/*.md | Select-Object -ExpandProperty Name)) {
  if ((git log --follow --oneline "docs/archive/$name" | Measure-Object -Line).Lines -lt 1) {
    Write-Error "History lost on docs/archive/$name"; exit 1
  }
}

# Reference-rot fix verified
$report = python -m rytm_randomizer.cli report 2>$null
if ($report -notmatch 'docs/archive/COLLABORATOR_REVIEW_TRIAGE_TEMPLATE\.md') {
  Write-Error "project_status_report still points at old docs/ path"; exit 1
}

# Test fixture pass
pytest tests/test_project_status_report.py -q

# Parity paranoia (no .py touched, but run anyway per Gate 2)
pytest tests/test_engines_pad*.py tests/test_group_runner.py tests/test_scene_runner.py -q
```

## Risks

| Risk | Mitigation |
|---|---|
| Reference-rot in project_status_report.py forgotten | Phase 3 ordered explicitly; pytest test_project_status_report.py is the gate. |
| Broken cross-link missed | Phase 7 grep at acceptance time. |
| Onboarding-count cap interpretation (15 vs 12) | docs/README.md documents narrowed-list interpretation; reviewers see rationale. |
| CONTRIBUTING.md conflict with WS-M4 | Disjoint sections; cascade keep-both. |
