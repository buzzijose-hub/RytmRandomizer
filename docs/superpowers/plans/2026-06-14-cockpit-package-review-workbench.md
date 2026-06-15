# Cockpit Package Review Workbench Implementation Plan

Status: in-flight

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive browser-local cockpit workbench that reviews an imported/exported rehearsal package against the currently loaded Performance Console packet before any operator tries to act on it.

**Architecture:** Keep the feature inside the existing React `PerformanceConsole` package/export surface from PR #181. The workbench derives review rows from `LocalRehearsalPackage`, its embedded `LocalRehearsalSnapshot`, and the current `LiveGuiPerformanceConsoleModelDict`; it records only browser-local operator events and never dispatches WebSocket commands, Tauri invokes, sidecar calls, send-plan actions, hardware arms, MIDI port opens, or MIDI messages.

**Tech Stack:** React 18, TypeScript, Vitest, Testing Library, existing cockpit CSS, existing `LiveGuiPerformanceConsoleModelDict` and local rehearsal package types.

---

## Scope

- Modify `desktop/web/src/cockpit/PerformanceConsole.tsx`
  - Add typed package review rows and summary helpers.
  - Compare package crate, queued move, snapshot, depth, current step, queued count, journal count, blocked actions, and recovery notes against the current cockpit packet and local rehearsal state.
  - Add a local-only "Stage package review locally" action that appends operator-log evidence and updates the local persistence summary.
- Modify `desktop/web/src/cockpit/styles.css`
  - Add compact review table/chip styling within the existing local persistence panel.
- Modify `desktop/web/tests/cockpit/PerformanceConsole.test.tsx`
  - Add RED/GREEN coverage for compatible review rows, missing-reference review rows, local staging, and raw JSON import clearing package review evidence.
- Modify `README.md` and `docs/STATUS.md`
  - Document the local-only package review workbench and its safety boundary.
- Add `docs/superpowers/plans/2026-06-14-cockpit-package-review-workbench-pr-body.md`
  - Single bundled PR body with the 18-gate checklist.

## Task 1: RED Tests

**Files:**
- Modify: `desktop/web/tests/cockpit/PerformanceConsole.test.tsx`

- [ ] **Step 1: Add package review workbench test**

Add a test that exports a local rehearsal package after choosing Peak Time, Rolling Perc Push, `console-snap-01`, and depth `72`. Assert `performance-console-local-package-review` shows:

```ts
expect(review).toHaveTextContent('Package review workbench');
expect(review).toHaveTextContent('review status compatible');
expect(review).toHaveTextContent('Crate');
expect(review).toHaveTextContent('Peak Time');
expect(review).toHaveTextContent('Current packet');
expect(review).toHaveTextContent('Depth');
expect(review).toHaveTextContent('package 72%');
expect(review).toHaveTextContent('current 72%');
```

- [ ] **Step 2: Add missing-reference review test**

Import a package whose rehearsal references `missing-crate`, `missing-queue`, and `missing-snapshot`. Assert the workbench shows `review status needs review`, the missing references, and package recovery/blocker counts.

- [ ] **Step 3: Add local staging test**

Click `Stage package review locally`. Assert the local operator log contains `Staged package review` and the persistence summary says `Staged local package review`. Assert `send to hardware` remains absent and `dry-run send` remains disabled.

- [ ] **Step 4: Add raw snapshot import clearing test**

Import a valid raw local rehearsal JSON snapshot after a package is visible. Assert `performance-console-local-package-review` disappears with the package evidence.

- [ ] **Step 5: Run RED**

```powershell
Set-Location 'C:\Users\Jose Buzzi\Documents\RytmRandomizer\.worktrees\cockpit-package-review-workbench\desktop\web'
npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx
```

Expected: fail because the package review workbench test id and staging button do not exist yet.

## Task 2: Implement Package Review Helpers

**Files:**
- Modify: `desktop/web/src/cockpit/PerformanceConsole.tsx`

- [ ] **Step 1: Add review row types**

Add these component-local types near the existing local package interfaces:

```ts
interface LocalRehearsalPackageReviewRow {
  readonly label: string;
  readonly packageValue: string;
  readonly currentValue: string;
  readonly status: string;
}

interface LocalRehearsalPackageReview {
  readonly status: string;
  readonly summary: string;
  readonly rows: ReadonlyArray<LocalRehearsalPackageReviewRow>;
}
```

- [ ] **Step 2: Add review helper**

Add a helper that returns `null` when no package is loaded, otherwise returns a deterministic review:

```ts
function localPackageReviewForCurrentPacket({
  localPackage,
  selectedCrate,
  currentQueueMove,
  selectedSnapshotIdLabel,
  currentDepth,
  currentSetPlanStep,
  localSetPlanEntries,
  localJournalEntries,
}: { ... }): LocalRehearsalPackageReview | null
```

Rows must cover crate, queued move, snapshot, depth, current step, queue count, journal count, blocked actions, and recovery notes. A row status is `match`, `changed`, `missing`, or `review`. Overall status is `needs review` when package compatibility says so or any row is `missing`; otherwise `compatible`.

- [ ] **Step 3: Add memoized review in the component**

Use `useMemo` to compute the review from current local state and `localPackage`.

## Task 3: Render Workbench And Stage Locally

**Files:**
- Modify: `desktop/web/src/cockpit/PerformanceConsole.tsx`
- Modify: `desktop/web/src/cockpit/styles.css`

- [ ] **Step 1: Add staging handler**

Add a handler:

```ts
const stageLocalPackageReview = (): void => {
  if (localPackageReview === null) {
    setLocalPersistenceSummary('No local rehearsal package to review. Local only; no MIDI sent.');
    appendLocalOperatorEvent('Package review skipped', 'No local rehearsal package loaded.');
    return;
  }
  setLocalPersistenceSummary(`Staged local package review: ${localPackageReview.status}. Local only; no MIDI sent.`);
  appendLocalOperatorEvent('Staged package review', localPackageReview.summary);
};
```

- [ ] **Step 2: Render workbench**

Render it inside the existing local package panel:

```tsx
<section data-testid="performance-console-local-package-review" ...>
  <strong>Package review workbench</strong>
  <span>review status {localPackageReview.status}</span>
  <span>{localPackageReview.summary}</span>
  ...
  <button type="button" onClick={stageLocalPackageReview}>Stage package review locally</button>
</section>
```

Each row must visibly show `label`, `packageValue`, `currentValue`, and `status`.

- [ ] **Step 3: Add CSS**

Add styles for `.performance-console-local-package-review`, `.performance-console-local-package-review-row`, and status chips, reusing existing local-panel colors and preserving compact layout.

- [ ] **Step 4: Run GREEN**

```powershell
Set-Location 'C:\Users\Jose Buzzi\Documents\RytmRandomizer\.worktrees\cockpit-package-review-workbench\desktop\web'
npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx
```

Expected: all Performance Console tests pass.

## Task 4: Docs And PR Body

**Files:**
- Modify: `README.md`
- Modify: `docs/STATUS.md`
- Add: `docs/superpowers/plans/2026-06-14-cockpit-package-review-workbench-pr-body.md`

- [ ] **Step 1: Update README**

Add one sentence near the Cockpit/Performance Console docs:

```md
The local rehearsal package flow now includes a browser-local package review workbench that compares the package against the currently loaded packet and stages review evidence without touching the sidecar or MIDI hardware.
```

- [ ] **Step 2: Update STATUS**

Add a 2026-06-14 status entry noting the package review workbench and passive safety boundary.

- [ ] **Step 3: Add PR body**

Create the PR body with summary, test plan, 18-gate checklist, strict-rules block, and plan link.

## Verification

Run:

```powershell
Set-Location 'C:\Users\Jose Buzzi\Documents\RytmRandomizer\.worktrees\cockpit-package-review-workbench\desktop\web'
npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx
npm.cmd run test:coverage
npm.cmd run typecheck
npm.cmd run build
npm.cmd run lint -- --ext .ts,.tsx --max-warnings 0 src/cockpit/PerformanceConsole.tsx tests/cockpit/PerformanceConsole.test.tsx

Set-Location 'C:\Users\Jose Buzzi\Documents\RytmRandomizer\.worktrees\cockpit-package-review-workbench'
python -m pytest tests\architecture\ -q
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
git diff --check
```

## PR Shape

Open one PR against `modularize-v1.34` from `codex/cockpit-package-review-workbench`. Do not stack on any other PR. Do not stage unrelated files from the main checkout (`artifacts/`, `docs/assets/rytmrandomizer-cockpit-cinematic-ui-reference-2026-06-09.png`, or `docs/superpowers/specs/2026-06-01-standalone-commercial-video-mood-board.md`).
