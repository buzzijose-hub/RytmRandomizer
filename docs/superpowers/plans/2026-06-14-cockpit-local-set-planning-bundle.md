# Cockpit Local Set Planning Bundle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> Status: in-flight

**Goal:** Extend the cinematic Performance Console from local single-move rehearsal into passive local set planning: the operator can stage multiple crate/queue/snapshot/depth choices, promote or skip the next staged move, clear the local plan, and keep all real hardware actions blocked.

**Architecture:** Keep the feature inside `PerformanceConsole` as component-local state derived from the existing `LiveGuiPerformanceConsoleModelDict`. This remains frontend/passive only: no WebSocket command dispatch, no Tauri or sidecar command execution, no MIDI port opening, no hardware arm path, no queued command execution, no snapshot mutation, and no MIDI send.

**Tech Stack:** React 18, TypeScript, Vitest, Testing Library, existing cockpit CSS and `LiveGuiPerformanceConsoleModelDict` protocol types.

---

## File Structure

- Modify `desktop/web/src/cockpit/PerformanceConsole.tsx`
  - Add component-local set-plan entries for crate, queued move, snapshot, depth, and local-only status.
  - Add local-only actions to stage the selected rehearsal state, promote the next staged step, skip it, and clear the plan.
  - Preserve disabled real send, arm, queue dispatch, sidecar, and hardware controls.
- Modify `desktop/web/src/cockpit/styles.css`
  - Add compact list/action styling for local set-plan entries without changing the passive HUD layout.
- Modify `desktop/web/tests/cockpit/PerformanceConsole.test.tsx`
  - Add red tests for staging multiple local set-plan steps and promoting/skipping/clearing them without enabling hardware sends.
- Modify `docs/STATUS.md`
  - Update the top status snapshot in place after implementation.
- Modify `README.md`
  - Add a short note to the Cockpit/Performance Console section describing the local set-plan queue.

## Task 1: Red Tests For Local Set Planning

**Files:**
- Modify: `desktop/web/tests/cockpit/PerformanceConsole.test.tsx`

- [x] **Step 1: Write the failing local set-plan test**

Add a test named `supports local-only set planning without enabling hardware sends`.
The test should render `performanceConsoleModelWithSelectableHistory()`, select a crate, queued move, snapshot, and depth, stage the selection into a local set plan, stage a second selection, then promote, skip, and clear local-only plan steps. Assert:

```ts
expect(screen.getByTestId('performance-console-local-set-plan')).toHaveTextContent('local-step-01');
expect(screen.getByTestId('performance-console-local-set-plan')).toHaveTextContent('Peak Time');
expect(screen.getByTestId('performance-console-local-set-plan')).toHaveTextContent('Rolling Perc Push');
expect(screen.getByTestId('performance-console-local-set-plan')).toHaveTextContent('console-snap-01');
expect(screen.getByTestId('performance-console-local-set-plan')).toHaveTextContent('72%');
expect(screen.getByTestId('performance-console-local-set-plan-summary')).toHaveTextContent('Promoted local-step-01');
expect(screen.queryByRole('button', { name: /send to hardware/i })).not.toBeInTheDocument();
expect(screen.getByRole('button', { name: /dry-run send/i })).toBeDisabled();
```

- [x] **Step 2: Run the focused test and verify red**

Run:

```powershell
Set-Location 'C:\Users\Jose Buzzi\Documents\RytmRandomizer\desktop\web'
npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx
```

Expected: fail because the local set-plan panel and controls do not exist.

## Task 2: Implement Local-Only Set Planning

**Files:**
- Modify: `desktop/web/src/cockpit/PerformanceConsole.tsx`
- Modify: `desktop/web/src/cockpit/styles.css`

- [x] **Step 1: Add local set-plan types and state**

Add a `LocalSetPlanEntry` interface and state for staged entries plus a last-action summary. Entries should include deterministic ids, crate name, move name, snapshot id, depth, and local-only status text.

- [x] **Step 2: Add local-only action handlers**

Add handlers for:

- `stageLocalSetPlanEntry`
- `promoteNextLocalSetStep`
- `skipNextLocalSetStep`
- `clearLocalSetPlan`

Each handler must update component-local state only and use copy-on-write array updates.

- [x] **Step 3: Render local set-plan controls and evidence**

Render a deterministic panel:

```tsx
data-testid="performance-console-local-set-plan"
data-testid="performance-console-local-set-plan-summary"
```

The panel should show staged entries, empty state, local-only safety text, and buttons for staging, promoting, skipping, and clearing local plan steps.

- [x] **Step 4: Run focused test and verify green**

Run the same focused Vitest command and expect the full `PerformanceConsole.test.tsx` file to pass.

## Task 3: Documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/STATUS.md`

- [x] **Step 1: Update README**

Add one sentence near the cockpit Performance Console documentation explaining that local set-plan staging/promote/skip/clear is component-local and never dispatches hardware or sidecar actions.

- [x] **Step 2: Update STATUS**

Edit the top `Recent Cleanup` section in place with the new bundle status and safety boundary.

## Task 4: Verification, Review, And PR

**Files:**
- No new production files beyond the focused cockpit surface.

- [x] **Step 1: Run focused frontend checks**

```powershell
Set-Location 'C:\Users\Jose Buzzi\Documents\RytmRandomizer\desktop\web'
npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx
npm.cmd run test:coverage
npm.cmd run typecheck
npm.cmd run build
npm.cmd run lint -- --ext .ts,.tsx --max-warnings 0 src/cockpit/PerformanceConsole.tsx tests/cockpit/PerformanceConsole.test.tsx
```

- [x] **Step 2: Run repo gates**

```powershell
Set-Location 'C:\Users\Jose Buzzi\Documents\RytmRandomizer'
python -m pytest tests\architecture\ -q
python -m pytest
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
git diff --check
```

- [ ] **Step 3: Commit and open one PR**

Create a single bundled PR against `modularize-v1.34`; do not stack it on another open PR. The PR body must include the 18-gate checklist and explicitly state the controls are passive/local-only with no MIDI behavior changes.
