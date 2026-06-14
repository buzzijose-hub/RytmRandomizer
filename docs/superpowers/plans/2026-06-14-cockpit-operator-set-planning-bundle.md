# Cockpit Operator Set Planning Bundle Implementation Plan

Status: in-flight

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the passive cockpit local set-plan queue into an operator-grade rehearsal surface with current/up-next state, operator handoff notes, and a local activity log, without touching hardware paths.

**Architecture:** Keep the work inside the existing React `PerformanceConsole` because the behavior is component-local rehearsal state derived from the already-merged `LiveGuiPerformanceConsoleModelDict`. The bundle must not add WebSocket commands, Tauri invocations, sidecar execution, MIDI port opening, snapshot mutation, or hardware send behavior.

**Tech Stack:** TypeScript React, Vitest + Testing Library, existing CSS in `desktop/web/src/cockpit/styles.css`, Markdown docs.

---

## File Structure

- Modify `desktop/web/tests/cockpit/PerformanceConsole.test.tsx` to add failing coverage for promoted current set-plan step, up-next queue state, and local operator activity log.
- Modify `desktop/web/src/cockpit/PerformanceConsole.tsx` to extend local-only state and render the operator plan surface.
- Modify `desktop/web/src/cockpit/styles.css` to keep the new operator plan layout compact and readable.
- Modify `README.md` and `docs/STATUS.md` to document the passive operator-planning behavior.
- Create `docs/superpowers/plans/2026-06-14-cockpit-operator-set-planning-bundle-pr-body.md` for the final PR body.

## Task 1: Red Test For Current / Up-Next Set Plan State

**Files:**
- Modify: `desktop/web/tests/cockpit/PerformanceConsole.test.tsx`
- Later modify: `desktop/web/src/cockpit/PerformanceConsole.tsx`

- [ ] **Step 1: Write the failing test**

Add a Vitest case that stages two local set-plan steps, promotes the first, and asserts:

```ts
expect(screen.getByTestId('performance-console-current-set-plan-step')).toHaveTextContent(
  'local-step-01',
);
expect(screen.getByTestId('performance-console-current-set-plan-step')).toHaveTextContent(
  'Rolling Perc Push',
);
expect(screen.getByTestId('performance-console-local-set-plan')).toHaveTextContent(
  'local-step-02',
);
expect(screen.getByTestId('performance-console-local-set-plan')).toHaveTextContent('Up next');
expect(screen.queryByTestId('local-set-plan-step-local-step-01')).not.toBeInTheDocument();
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```powershell
Set-Location 'C:\Users\Jose Buzzi\Documents\RytmRandomizer\desktop\web'
npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx
```

Expected: the new test fails because `performance-console-current-set-plan-step` and the `Up next` label do not exist yet.

- [ ] **Step 3: Implement minimal current/up-next state**

In `PerformanceConsole.tsx`, add:

```ts
const [currentSetPlanStep, setCurrentSetPlanStep] = useState<LocalSetPlanEntry | null>(null);
```

Update `promoteNextLocalSetStep()` so it sets `currentSetPlanStep` to the promoted entry before removing it from `localSetPlanEntries`.

- [ ] **Step 4: Render current and up-next state**

Render a current-step article with `data-testid="performance-console-current-set-plan-step"` and label queued entries as `Up next` based on their array index.

- [ ] **Step 5: Verify GREEN**

Run the same focused Vitest command and confirm the new test passes.

## Task 2: Red Test For Local Operator Activity Log

**Files:**
- Modify: `desktop/web/tests/cockpit/PerformanceConsole.test.tsx`
- Later modify: `desktop/web/src/cockpit/PerformanceConsole.tsx`
- Later modify: `desktop/web/src/cockpit/styles.css`

- [ ] **Step 1: Write the failing test**

Extend the new test or add a second test that performs local actions and asserts:

```ts
const operatorLog = screen.getByTestId('performance-console-local-operator-log');
expect(operatorLog).toHaveTextContent('Staged local-step-01');
expect(operatorLog).toHaveTextContent('Staged local-step-02');
expect(operatorLog).toHaveTextContent('Promoted local-step-01');
expect(operatorLog).toHaveTextContent('Local only');
expect(screen.queryByRole('button', { name: /send to hardware/i })).not.toBeInTheDocument();
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```powershell
Set-Location 'C:\Users\Jose Buzzi\Documents\RytmRandomizer\desktop\web'
npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx
```

Expected: the test fails because the local operator log does not exist.

- [ ] **Step 3: Implement the local activity log**

In `PerformanceConsole.tsx`, add a frozen local shape:

```ts
interface LocalOperatorEvent {
  readonly id: string;
  readonly label: string;
  readonly detail: string;
  readonly status: string;
}
```

Add a `localOperatorEvents` state array and a helper that appends log entries for local dry-run, journal save, stage, promote, skip, and clear actions.

- [ ] **Step 4: Render the log**

Add a compact section with `data-testid="performance-console-local-operator-log"` that shows the newest local activity in memory. Empty state text must be `No local operator activity recorded.`

- [ ] **Step 5: Verify GREEN**

Run the same focused Vitest command and confirm the operator-log assertions pass.

## Task 3: Operator Summary And Safety Copy

**Files:**
- Modify: `desktop/web/src/cockpit/PerformanceConsole.tsx`
- Modify: `desktop/web/src/cockpit/styles.css`

- [ ] **Step 1: Add summary helpers**

Add component-local helpers for:

```ts
function localSetPlanSummary(
  current: LocalSetPlanEntry | null,
  queued: ReadonlyArray<LocalSetPlanEntry>,
): string {
  if (current === null && queued.length === 0) {
    return 'No active local set plan. Local only; no MIDI sent.';
  }
  const currentLabel = current === null ? 'no current step' : `current ${current.id}`;
  return `${currentLabel}; ${queued.length} queued. Local only; no MIDI sent.`;
}
```

- [ ] **Step 2: Surface the summary**

Use the helper in `performance-console-local-set-plan-summary` so the operator can see current + queued state after every action. Also render a local operator handoff with the current step, next step, recent local action, recovery note, and explicit no-send safety copy.

- [ ] **Step 3: Style without layout churn**

Add compact CSS classes for the current step, handoff card, and operator log. Use stable dimensions, grid gaps, and no nested cards beyond the existing panel pattern.

## Task 3A: Local Completion And Reset Controls

**Files:**
- Modify: `desktop/web/tests/cockpit/PerformanceConsole.test.tsx`
- Modify: `desktop/web/src/cockpit/PerformanceConsole.tsx`
- Modify: `desktop/web/src/cockpit/styles.css`

- [x] **Step 1: Write the failing test**

Extend the local set-plan test so it promotes a staged move, completes the
current step, verifies the up-next step remains queued, then resets the local
plan and verifies both current and queued local state are empty.

- [x] **Step 2: Run the focused test and verify RED**

Run:

```powershell
Set-Location 'C:\Users\Jose Buzzi\Documents\RytmRandomizer\desktop\web'
npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx
```

Observed: the focused test failed because the
`Complete current local set-plan step` button did not exist.

- [x] **Step 3: Implement local-only complete/reset actions**

Add component-local handlers that complete the current local set-plan step or
reset current plus queued local plan state. Both actions only update React
state and local operator log entries; they do not dispatch WebSocket commands,
Tauri invokes, sidecar actions, MIDI adapter calls, hardware arm paths, or MIDI
sends.

- [x] **Step 4: Verify GREEN**

Run the same focused Vitest command and confirm the complete/reset assertions pass.

## Task 4: Docs And PR Body

**Files:**
- Modify: `README.md`
- Modify: `docs/STATUS.md`
- Add: `docs/superpowers/plans/2026-06-14-cockpit-operator-set-planning-bundle-pr-body.md`

- [ ] **Step 1: Update README**

Document that the cockpit can rehearse a local set plan with current/up-next state and local activity logs, and that this remains passive.

- [ ] **Step 2: Update STATUS**

Add a dated entry at the top of Recent Cleanup describing this bundle.

- [ ] **Step 3: Add PR body**

Create a PR body with:

- Summary
- What changed
- Safety notes
- Test plan
- All 18 plan gates
- Strict rules confirmation
- Link to this plan

## Task 5: Verification, Push, PR

**Files:** none expected beyond previous tasks.

- [ ] **Step 1: Focused frontend tests**

Run:

```powershell
Set-Location 'C:\Users\Jose Buzzi\Documents\RytmRandomizer\desktop\web'
npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx
npm.cmd run typecheck
npm.cmd run build
npm.cmd run lint -- --ext .ts,.tsx --max-warnings 0 src/cockpit/PerformanceConsole.tsx tests/cockpit/PerformanceConsole.test.tsx
```

- [ ] **Step 2: Coverage and repo gates**

Run:

```powershell
Set-Location 'C:\Users\Jose Buzzi\Documents\RytmRandomizer\desktop\web'
npm.cmd run test:coverage
Set-Location 'C:\Users\Jose Buzzi\Documents\RytmRandomizer'
python -m pytest tests\architecture\ -q
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
python -m pytest
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
  docs/superpowers/plans/2026-06-14-cockpit-operator-set-planning-bundle.md `
  docs/superpowers/plans/2026-06-14-cockpit-operator-set-planning-bundle-pr-body.md
```

Do not stage unrelated untracked `artifacts/`, `docs/assets/rytmrandomizer-cockpit-cinematic-ui-reference-2026-06-09.png`, or `docs/superpowers/specs/2026-06-01-standalone-commercial-video-mood-board.md`.

- [ ] **Step 4: Commit, push, open one PR**

Run:

```powershell
git commit -m "feat: deepen cockpit operator set planning"
git push -u origin codex/cockpit-operator-set-planning-bundle
python scripts\create_pr.py --title "feat: deepen cockpit operator set planning" --body-file docs\superpowers\plans\2026-06-14-cockpit-operator-set-planning-bundle-pr-body.md
```

Expected: one PR against `modularize-v1.34`, no stacked PRs.
