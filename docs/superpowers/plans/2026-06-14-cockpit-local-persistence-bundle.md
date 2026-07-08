# Cockpit Local Persistence Bundle Implementation Plan

Status: in-flight

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the passive Cockpit Performance Console preserve, export, and import local rehearsal state without touching any hardware path.

**Architecture:** Keep persistence entirely inside the existing React `PerformanceConsole`: browser `localStorage` for auto-save, copy-ready JSON for export/import, and existing component-local rehearsal state for journal, set-plan, and operator log data. The bundle must not add WebSocket commands, Tauri invokes, sidecar execution, MIDI port opening, snapshot mutation, command queue execution, hardware arm behavior, or MIDI sends.

**Tech Stack:** TypeScript React, browser `localStorage`, Vitest + Testing Library, existing cockpit CSS, Markdown docs.

---

## File Structure

- Modify `desktop/web/tests/cockpit/PerformanceConsole.test.tsx` for RED/GREEN coverage of local auto-save restore, JSON import/export, local storage clearing, and unchanged hardware-send safety.
- Modify `desktop/web/src/cockpit/PerformanceConsole.tsx` to add a typed local rehearsal snapshot schema, safe parser/serializer helpers, auto-save effect, JSON import/export controls, and clear-storage control.
- Modify `desktop/web/src/cockpit/styles.css` for compact persistence controls and JSON text areas.
- Modify `README.md` and `docs/STATUS.md` to document the passive persistence behavior.
- Add `docs/superpowers/plans/2026-06-14-cockpit-local-persistence-bundle-pr-body.md` for the PR body.

## Task 1: TDD Red For Local Auto-Save Restore

**Files:**
- Modify: `desktop/web/tests/cockpit/PerformanceConsole.test.tsx`
- Later modify: `desktop/web/src/cockpit/PerformanceConsole.tsx`

- [x] **Step 1: Write the failing test**

Add a test that clears `window.localStorage`, selects a crate, queued move, snapshot, and depth, runs a local dry-run, saves a local journal take, stages and promotes a local set-plan step, then asserts the browser-local storage key contains `local-step-01` and `local-take-01`. Unmount and render the component again, then assert the local preview, journal, and current set-plan state are restored.

- [x] **Step 2: Run the focused test and verify RED**

Run:

```powershell
Set-Location '<repo-root>\desktop\web'
npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx
```

Observed: the new test failed because the storage key was `null` and the persistence summary did not exist.

- [x] **Step 3: Implement minimal persistence support**

Add `LOCAL_REHEARSAL_STORAGE_KEY`, `LOCAL_REHEARSAL_STORAGE_VERSION`, `LocalRehearsalSnapshot`, safe `unknown` parsers, `readLocalRehearsalSnapshot`, `writeLocalRehearsalSnapshot`, and `removeLocalRehearsalSnapshot`. Initialize component-local state from the saved snapshot, then auto-save when the local snapshot changes and local auto-save is enabled.

- [x] **Step 4: Verify GREEN**

Run the same focused Vitest command and confirm the auto-save restore test passes.

## Task 2: TDD Red For JSON Import / Export

**Files:**
- Modify: `desktop/web/tests/cockpit/PerformanceConsole.test.tsx`
- Later modify: `desktop/web/src/cockpit/PerformanceConsole.tsx`
- Later modify: `desktop/web/src/cockpit/styles.css`

- [x] **Step 1: Write the failing test**

Add a test that types a versioned local rehearsal JSON payload into a new import textarea, clicks `Import local rehearsal JSON`, and asserts selected crate, queued move, snapshot, depth, local journal, current set-plan step, queued set-plan step, and local operator log all reflect the imported payload. Then click `Export local rehearsal JSON`, assert the exported payload contains the imported journal and set-plan IDs, click `Clear saved local rehearsal`, and assert the browser-local storage key is removed while hardware-send controls remain absent or disabled.

- [x] **Step 2: Run the focused test and verify RED**

Run:

```powershell
Set-Location '<repo-root>\desktop\web'
npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx
```

Observed: the test failed because `performance-console-local-import-input` did not exist.

- [x] **Step 3: Implement import/export controls**

Add component-local state for the import textarea, export payload, local auto-save flag, and persistence summary. Implement `exportLocalRehearsalJson`, `importLocalRehearsalJson`, `clearSavedLocalRehearsal`, and `toggleLocalAutosave`; each handler updates React state and local operator log entries only.

- [x] **Step 4: Style the persistence panel**

Add compact CSS for the local auto-save checkbox, import textarea, and exported JSON preview. Keep the panel inside the existing local rehearsal surface and avoid modal/file-picker behavior.

- [x] **Step 5: Verify GREEN**

Run the same focused Vitest command and confirm all cockpit tests pass.

## Task 3: Docs And PR Body

**Files:**
- Modify: `README.md`
- Modify: `docs/STATUS.md`
- Add: `docs/superpowers/plans/2026-06-14-cockpit-local-persistence-bundle-pr-body.md`

- [x] **Step 1: Update README**

Document that the passive Performance Console now supports browser-local auto-save, copy-ready JSON export/import, and clear-storage controls for local rehearsal state.

- [x] **Step 2: Update STATUS**

Add a 2026-06-14 Recent Cleanup entry describing the local persistence bundle and its safety boundary.

- [x] **Step 3: Add PR body**

Create a PR body with summary, changed files, safety notes, verification, the 18-gate checklist, strict rules confirmation, and this plan link.

## Task 4: Verification, Push, PR

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
python -m pytest tests\architecture\ -q
python -m pytest
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
git diff --check
```

- [ ] **Step 3: Stage only intended files**

Stage:

```powershell
git add desktop/web/src/cockpit/PerformanceConsole.tsx `
  desktop/web/src/cockpit/styles.css `
  desktop/web/tests/cockpit/PerformanceConsole.test.tsx `
  README.md `
  docs/STATUS.md `
  docs/superpowers/plans/2026-06-14-cockpit-local-persistence-bundle.md `
  docs/superpowers/plans/2026-06-14-cockpit-local-persistence-bundle-pr-body.md
```

Do not stage unrelated untracked `artifacts/`, `docs/assets/rytmrandomizer-cockpit-cinematic-ui-reference-2026-06-09.png`, or `docs/superpowers/specs/2026-06-01-standalone-commercial-video-mood-board.md`.

- [ ] **Step 4: Commit, push, open one PR**

Run:

```powershell
git commit -m "feat: add cockpit local rehearsal persistence"
git push -u origin codex/cockpit-local-persistence-bundle
python scripts\create_pr.py --title "feat: add cockpit local rehearsal persistence" --body-file docs\superpowers\plans\2026-06-14-cockpit-local-persistence-bundle-pr-body.md
```

Expected: one PR against `modularize-v1.34`, no stacked PRs.
