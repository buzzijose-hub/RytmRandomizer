# Cockpit Performance Console Interaction Bundle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> Status: in-flight

**Goal:** Make the cinematic Performance Console rehearse operator intent locally by supporting passive selections, preview depth changes, local dry-run summaries, and journal saves without sending MIDI.

**Architecture:** Keep `PerformanceConsole` as the typed packet consumer and add only component-local rehearsal state derived from `LiveGuiPerformanceConsoleModelDict`. All controls remain mock-safe: clicks update visible local preview state only, do not call WebSocket/Tauri/sidecar command dispatch, do not open MIDI ports, and do not send MIDI.

**Tech Stack:** React 18, TypeScript, Vitest, Testing Library, existing cockpit CSS and `LiveGuiPerformanceConsoleModelDict` protocol types.

---

## File Structure

- Modify `desktop/web/src/cockpit/PerformanceConsole.tsx`
  - Add local state for selected style crate, selected queue move, selected snapshot, preview depth, local dry-run result, and local journal entries.
  - Convert safe passive controls from disabled placeholders into local-only buttons/input where useful.
  - Preserve disabled real hardware controls and blocked action messaging.
- Modify `desktop/web/src/cockpit/styles.css`
  - Add visible selected/pressed/focus styling for local rehearsal controls and summaries.
- Modify `desktop/web/tests/cockpit/PerformanceConsole.test.tsx`
  - Add red tests for crate selection, queue selection, snapshot selection, depth update, local dry-run summary, and local journal save.
- Modify `docs/STATUS.md`
  - Update the latest status snapshot in place after implementation.
- Modify `README.md`
  - Add a short note to the Cockpit/Performance Console section describing local-only passive interactions.

## Task 1: Red Tests For Local Rehearsal Interactions

**Files:**
- Modify: `desktop/web/tests/cockpit/PerformanceConsole.test.tsx`

- [x] **Step 1: Write the failing interaction test**

Add a test named `supports local-only rehearsal interactions without enabling hardware sends`.
The test should render `PerformanceConsole`, click a non-current crate, click a queued move, click an older snapshot, change the preview depth, run local dry-run, save to journal, and assert:

```ts
expect(screen.getByTestId('performance-console-local-preview')).toHaveTextContent('Selected crate Peak Time');
expect(screen.getByTestId('performance-console-local-preview')).toHaveTextContent('Selected move Pressure Rattle');
expect(screen.getByTestId('performance-console-local-preview')).toHaveTextContent('Selected snapshot console-snap-01');
expect(screen.getByTestId('performance-console-local-preview')).toHaveTextContent('Depth 72%');
expect(screen.getByTestId('performance-console-last-dry-run')).toHaveTextContent('Local dry-run');
expect(screen.getByTestId('performance-console-local-journal')).toHaveTextContent('local-take-01');
expect(screen.queryByRole('button', { name: /send to hardware/i })).not.toBeInTheDocument();
```

- [x] **Step 2: Run the focused test and verify red**

Run:

```powershell
Set-Location '<repo-root>\desktop\web'
npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx
```

Expected: fail because the new test ids and active local controls do not exist.

## Task 2: Implement Local-Only Interaction State

**Files:**
- Modify: `desktop/web/src/cockpit/PerformanceConsole.tsx`

- [x] **Step 1: Add local state**

Use `useMemo` for sorted packet-derived lists and `useState` for:

```ts
const [selectedCrateKey, setSelectedCrateKey] = useState<string | null>(null);
const [selectedQueueKey, setSelectedQueueKey] = useState<string | null>(null);
const [selectedSnapshotId, setSelectedSnapshotId] = useState<string | null>(null);
const [previewDepth, setPreviewDepth] = useState<number | null>(null);
const [lastDryRunSummary, setLastDryRunSummary] = useState<string>('No local dry-run performed.');
const [localJournalEntries, setLocalJournalEntries] = useState<ReadonlyArray<string>>([]);
```

- [x] **Step 2: Derive selected packet rows**

Derive active crate, move, snapshot, and depth from selected state first, falling back to the packet defaults. Clamp preview depth to 10-90.

- [x] **Step 3: Make passive controls local-only**

Convert crate cards, queue cards, snapshot history cards, depth input, local dry-run, and save journal buttons to active local controls. Each button must have a `title` explaining it is local/passive only. Hardware send / arm controls remain disabled.

- [x] **Step 4: Render local preview, dry-run, and journal evidence**

Add three deterministic panels/test ids:

```tsx
data-testid="performance-console-local-preview"
data-testid="performance-console-last-dry-run"
data-testid="performance-console-local-journal"
```

The text must show selected crate, selected move, selected snapshot, depth, dry-run summary, and saved local take names.

- [x] **Step 5: Run focused test and verify green**

Run the same focused Vitest command and expect the full `PerformanceConsole.test.tsx` file to pass.

## Task 3: Styling And Documentation

**Files:**
- Modify: `desktop/web/src/cockpit/styles.css`
- Modify: `README.md`
- Modify: `docs/STATUS.md`

- [x] **Step 1: Style active local controls**

Add styles for `.performance-console-local-control`, `.performance-console-local-control[aria-pressed='true']`, and local preview panels. Keep text compact and avoid shifting the existing grid.

- [x] **Step 2: Update README**

Add one sentence near the cockpit Performance Console documentation:

```md
The cinematic Performance Console also supports local-only rehearsal interactions for selecting crates, queued moves, snapshots, preview depth, dry-run summary, and journal saves; these controls do not dispatch sidecar commands, open MIDI ports, arm hardware, or send MIDI.
```

- [x] **Step 3: Update STATUS**

Edit the top `Recent Cleanup` section in place with the new bundle status and safety boundary.

## Task 4: Verification, Review, And PR

**Files:**
- No new production files.

- [x] **Step 1: Run focused frontend checks**

```powershell
Set-Location '<repo-root>\desktop\web'
npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx
npm.cmd run typecheck
npm.cmd run lint -- --ext .ts,.tsx --max-warnings 0 src/cockpit/PerformanceConsole.tsx tests/cockpit/PerformanceConsole.test.tsx
npm.cmd run build
```

- [x] **Step 2: Run repo gates**

```powershell
Set-Location '<repo-root>'
python -m pytest tests\architecture\ -q
git diff --check
```

- [ ] **Step 3: Commit and open one PR**

Create a single bundled PR against `modularize-v1.34`; do not stack it on another open PR. The PR body must include the 18-gate checklist and explicitly state the controls are passive/local-only with no MIDI behavior changes.
