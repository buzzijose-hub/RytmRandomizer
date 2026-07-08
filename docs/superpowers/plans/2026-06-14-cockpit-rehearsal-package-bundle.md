# Cockpit Rehearsal Package Bundle Implementation Plan

Status: in-flight

Verification is complete; PR #181 is open and awaiting review/merge.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the Cockpit Performance Console's browser-local rehearsal state into a portable, validated rehearsal package without adding any hardware behavior.

**Architecture:** Keep the bundle inside the existing passive React `PerformanceConsole`. A package wraps the already-versioned local rehearsal snapshot with a manifest, device/safety summary, blocked-action evidence, compatibility checks, recovery notes, and the source packet identity; imports continue to accept the previous raw local snapshot shape for backward compatibility. No WebSocket command, Tauri invoke, sidecar call, MIDI adapter, send planner, queue executor, hardware arm path, file write, snapshot mutation, or MIDI send is introduced.

**Tech Stack:** TypeScript React, existing `LiveGuiPerformanceConsoleModelDict`, browser-local JSON, Vitest + Testing Library, existing cockpit CSS, Markdown docs.

---

## File Structure

- Modify `desktop/web/tests/cockpit/PerformanceConsole.test.tsx` for RED/GREEN tests around package export/import, compatibility warnings, old raw snapshot import compatibility, and unchanged hardware-send safety.
- Modify `desktop/web/src/cockpit/PerformanceConsole.tsx` to add package manifest types, safe package parsers, package builder helpers, package import/export handlers, and visible package evidence.
- Modify `desktop/web/src/cockpit/styles.css` for compact package manifest/checklist styling inside the existing local persistence panel.
- Modify `README.md` and `docs/STATUS.md` to document the passive rehearsal-package boundary.
- Add `docs/superpowers/plans/2026-06-14-cockpit-rehearsal-package-bundle-pr-body.md` for the PR body.

## Task 1: TDD Red For Package Export

**Files:**
- Modify: `desktop/web/tests/cockpit/PerformanceConsole.test.tsx`
- Later modify: `desktop/web/src/cockpit/PerformanceConsole.tsx`

- [x] **Step 1: Write the failing test**

Add a focused test that selects a crate, queued move, snapshot, and preview depth, stages/promotes a local set-plan step, clicks `Export local rehearsal package`, and asserts the rendered JSON contains:

```json
{
  "kind": "rytmrandomizer.cockpit.local-rehearsal-package",
  "version": 1,
  "manifest": {
    "sessionLabel": "Warehouse arc",
    "packetSource": "passive packet",
    "selectedCrateName": "Peak Time",
    "selectedMoveName": "Rolling Perc Push",
    "selectedSnapshotId": "console-snap-01",
    "queuedStepCount": 0,
    "currentStepId": "local-step-01",
    "journalTakeCount": 0,
    "hardwareMode": "passive"
  },
  "compatibility": {
    "status": "compatible",
    "checks": [
      "selected crate exists in current packet",
      "selected queued move exists in current packet",
      "selected snapshot exists in current packet"
    ]
  }
}
```

The same test must assert the package panel shows device names, blocked actions, recovery notes, and no `send to hardware` button.

- [x] **Step 2: Run the focused test and verify RED**

Run:

```powershell
Set-Location '<repo-root>\desktop\web'
npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx
```

Expected RED: Testing Library cannot find the `Export local rehearsal package` button or the package manifest panel.

- [x] **Step 3: Implement package export**

Add `LOCAL_REHEARSAL_PACKAGE_KIND`, `LOCAL_REHEARSAL_PACKAGE_VERSION`, `LocalRehearsalPackageManifest`, `LocalRehearsalPackageCompatibility`, and `LocalRehearsalPackage` types. Add a `buildLocalRehearsalPackage(...)` helper that wraps `localRehearsalSnapshot` with:

```ts
{
  kind: LOCAL_REHEARSAL_PACKAGE_KIND,
  version: LOCAL_REHEARSAL_PACKAGE_VERSION,
  manifest,
  compatibility,
  safety,
  blockedActions,
  recoveryNotes,
  rehearsal: localRehearsalSnapshot,
}
```

The manifest is derived from the visible model and local state only. Export updates React state and local operator events only.

- [x] **Step 4: Verify GREEN for package export**

Run the same focused Vitest command and confirm the package export assertions pass.

## Task 2: TDD Red For Package Import And Compatibility

**Files:**
- Modify: `desktop/web/tests/cockpit/PerformanceConsole.test.tsx`
- Later modify: `desktop/web/src/cockpit/PerformanceConsole.tsx`

- [x] **Step 1: Write the failing import test**

Add a test that pastes a package JSON into the existing import textarea, clicks `Import local rehearsal package`, and asserts the selected crate, queued move, snapshot, depth, current set-plan step, queued set-plan step, and operator log are restored from `package.rehearsal`.

Add a second test that imports a package with unknown `selectedCrateKey`, `selectedQueueKey`, and `selectedSnapshotId`, then asserts the package panel reports:

```text
needs review
selected crate missing from current packet
selected queued move missing from current packet
selected snapshot missing from current packet
```

The UI may fall back to current packet defaults for display, but the warnings must remain visible.

- [x] **Step 2: Run focused tests and verify RED**

Run:

```powershell
Set-Location '<repo-root>\desktop\web'
npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx
```

Expected RED: package import is unsupported and no package compatibility panel exists.

- [x] **Step 3: Implement package parsing and import**

Add `localRehearsalPackageFromUnknown`, `localRehearsalImportFromUnknown`, and `applyLocalRehearsalSnapshot`. `localRehearsalImportFromUnknown` accepts either the new package envelope or the previous raw `LocalRehearsalSnapshot` shape. Package import sets package evidence state, applies `package.rehearsal`, records a local operator event, and never dispatches commands.

- [x] **Step 4: Verify GREEN for package import**

Run the same focused Vitest command and confirm package import, warning, and raw snapshot compatibility tests pass.

## Task 3: Package Panel Styling And Docs

**Files:**
- Modify: `desktop/web/src/cockpit/styles.css`
- Modify: `README.md`
- Modify: `docs/STATUS.md`
- Add: `docs/superpowers/plans/2026-06-14-cockpit-rehearsal-package-bundle-pr-body.md`

- [x] **Step 1: Style package evidence**

Add compact CSS for package manifest rows, compatibility chips, device/safety evidence, and JSON preview. Use existing local panel tokens and keep the panel within the current local persistence surface.

- [x] **Step 2: Update README**

Document that the Performance Console can export/import a portable local rehearsal package containing local rehearsal state, manifest, compatibility checks, blocked-action evidence, and recovery notes while staying browser-local and hardware-safe.

- [x] **Step 3: Update STATUS**

Add a dated 2026-06-14 Recent Cleanup entry for the rehearsal-package bundle and explicitly state that it adds no hardware behavior.

- [x] **Step 4: Add PR body**

Create the PR body with summary, changed files, safety notes, verification, the 18-gate checklist, strict rules confirmation, and this plan link.

## Task 4: Verification, Commit, Push, PR

**Files:** none expected beyond previous tasks.

- [x] **Step 1: Focused frontend verification**

Run:

```powershell
Set-Location '<repo-root>\desktop\web'
npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx
npm.cmd run typecheck
npm.cmd run build
npm.cmd run lint -- --ext .ts,.tsx --max-warnings 0 src/cockpit/PerformanceConsole.tsx tests/cockpit/PerformanceConsole.test.tsx
```

- [x] **Step 2: Coverage and repo gates**

Run:

```powershell
Set-Location '<repo-root>\desktop\web'
npm.cmd run test:coverage
Set-Location '<repo-root>'
python -m pytest tests\architecture\ -q -n 0
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
git diff --check
```

Notes: `npm.cmd run test:coverage` passed at 100% statements/branches/functions/lines.
The full architecture gate passed with `-n 0` on local Windows/Python 3.13
(608 passed, 1 existing warn-only abstraction warning). A prior local full-suite
xdist attempt hit worker crashes in `test_no_unreferenced_top_level_symbols.py`;
that file passes with `-n 0`, and this bundle does not touch Python runtime code.

- [x] **Step 3: Stage only intended files**

Stage:

```powershell
git add desktop/web/src/cockpit/PerformanceConsole.tsx `
  desktop/web/src/cockpit/styles.css `
  desktop/web/tests/cockpit/PerformanceConsole.test.tsx `
  README.md `
  docs/STATUS.md `
  docs/superpowers/plans/2026-06-14-cockpit-rehearsal-package-bundle.md `
  docs/superpowers/plans/2026-06-14-cockpit-rehearsal-package-bundle-pr-body.md
```

Do not stage unrelated untracked `artifacts/`, `docs/assets/rytmrandomizer-cockpit-cinematic-ui-reference-2026-06-09.png`, or `docs/superpowers/specs/2026-06-01-standalone-commercial-video-mood-board.md`.

- [x] **Step 4: Commit, push, open one PR**

Run:

```powershell
git commit -m "feat: add cockpit rehearsal package export"
git push -u origin codex/cockpit-rehearsal-package-bundle
python scripts\create_pr.py --title "feat: add cockpit rehearsal package export" --body-file docs\superpowers\plans\2026-06-14-cockpit-rehearsal-package-bundle-pr-body.md
```

Expected: one large PR against `modularize-v1.34`, no stacked PRs.
