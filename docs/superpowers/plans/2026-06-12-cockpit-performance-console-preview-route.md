# Cockpit Performance Console Preview Route Implementation Plan

> Status: in-flight

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the passive Cockpit performance console packet from PR #162 reachable in the desktop web app through a mock-safe preview route.

**Architecture:** The Python report and `PerformanceConsole` renderer already exist. This slice only teaches the App hash router to render an injected `LiveGuiPerformanceConsoleModelDict` at a dedicated preview route while preserving the existing Cockpit and Profile Wizard routes. No WebSocket command, sidecar launch, port enumeration, MIDI send, or hardware arm behavior changes.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, existing `desktop/web/src/cockpit/PerformanceConsole.tsx`, existing `desktop/web/src/types/live_gui_protocol.ts`.

---

## File Structure

- Modify: `desktop/web/src/App.tsx`
  - Add a preview-route predicate for `#/performance-console` and `#/console`.
  - Accept an optional `performanceConsole` model prop for tests/storybook/preview hosts.
  - Render `<PerformanceConsole model={performanceConsole} />` before the session-status gate when the preview route has a model.
  - Preserve current connecting placeholder, Profile Wizard route, and Cockpit route behavior.
- Create: `desktop/web/tests/cockpit/performanceConsoleFixture.ts`
  - Move the existing performance console fixture into a shared test helper so router tests and component tests use one model.
- Modify: `desktop/web/tests/cockpit/PerformanceConsole.test.tsx`
  - Import the shared fixture instead of keeping a second inline copy.
- Modify: `desktop/web/tests/router.test.tsx`
  - Add route tests proving the preview route renders without a session, swaps back to Cockpit/Wizard, and falls back to the connecting placeholder when no preview model is injected.
- Modify: `docs/STATUS.md`
  - Add a concise status entry describing the mock-safe frontend preview route after tests pass.

## Workstream Graph

| Workstream | Owns | Depends on | Parallel with |
|---|---|---|---|
| WS1 - Frontend preview route | `desktop/web/src/App.tsx`, `desktop/web/tests/router.test.tsx`, `desktop/web/tests/cockpit/*` | PR #162 merged on `origin/modularize-v1.34` | None; this is a small single-workstream slice |
| WS2 - Docs/status | `docs/STATUS.md`, this plan | WS1 tests passing | None |

## Per-WS Worktree Assignment

- Worktree: `.worktrees/cockpit-performance-console-preview-route`
- Branch: `codex/cockpit-performance-console-preview-route`
- Base: `origin/modularize-v1.34`

## Disjoint File Ownership

This plan is one workstream. It owns only the files listed above and does not touch Python runtime, MIDI adapters, V1.34 parity fixtures, installer workflow files, or unrelated local assets.

## Agent Crew

- Planner: write this plan and verify it matches the existing App router and PerformanceConsole contracts.
- TDD implementer: write failing Vitest route tests first, then implement the smallest App router changes.
- Refactor pass: extract the shared fixture only after the route test is red.
- Verification: run targeted Vitest, frontend typecheck/lint, and Python architecture tests if docs/source scope requires them.
- PR closer: commit, push, open one PR against `modularize-v1.34` with the 18-gate checklist.

## Self-Driving Decision Rules

- If the preview route test passes before implementation, rewrite the test because it did not prove missing behavior.
- If the router implementation would require opening the sidecar or sending a WebSocket command, stop and reduce the slice back to injected-model rendering.
- If frontend dependency setup is missing, run `npm.cmd install` inside `desktop/web` and keep dependency lockfile changes only if npm actually modifies the lockfile.
- If `docs/STATUS.md` conflicts with current base, preserve the current base entry and add this entry at the top of Recent Cleanup.
- If a test fails outside touched frontend routing/console behavior, inspect before editing and avoid sweeping unrelated fixes into this PR.

## Auto-Merge Cascade

This plan opens one PR only. It does not create stacked PRs. If the base advances before merge, fetch `origin`, merge or rebase onto `origin/modularize-v1.34`, resolve only conflicts in owned files, rerun verification, and force-push only this feature branch.

## Auto-Rebase Rules

- Source branch can be updated with `git merge origin/modularize-v1.34` or `git rebase origin/modularize-v1.34`.
- Do not reset or rewrite unrelated local worktrees.
- Do not regenerate V1.34 parity fixtures.
- Do not use `--no-verify`.

## Persistent State On Disk

- Plan file: `docs/superpowers/plans/2026-06-12-cockpit-performance-console-preview-route.md`
- Git state: branch `codex/cockpit-performance-console-preview-route`
- PR state: the eventual GitHub PR against `modularize-v1.34`

## Kickoff Trigger

Manual Codex continuation in this thread. No cron or automation is required.

## Termination Condition

The work is done when the route tests, component tests, frontend typecheck/lint, relevant architecture checks, commit, push, and one PR are complete. No hardware validation is needed because this is injected passive UI rendering only.

## Hard Time Budget

Target: same working session. Stop only for repeated verification failure, unavailable local tooling, or conflicting user instruction.

## Recovery Procedure

On resume:

1. Run `git status --short --branch`.
2. Run `git log --oneline -5`.
3. Run `gh pr list --state open --json number,title,headRefName,baseRefName`.
4. Continue from the first unchecked task below.

## Permission Profile

Local file edits, local tests, git branch/commit/push, and GitHub PR creation are allowed. Refuse hardware sends, MIDI port opening, V1.34 parity regeneration, dependency pin changes, or destructive cleanup of old worktrees unless explicitly requested.

## Stop Signals

If the user says `stop`, `pause`, or redirects to hardware testing, leave the worktree state intact and report current status. If a reviewer requests changes on an existing open PR, address that before broadening scope.

---

### Task 1: Router Test And Fixture Extraction

**Files:**
- Create: `desktop/web/tests/cockpit/performanceConsoleFixture.ts`
- Modify: `desktop/web/tests/cockpit/PerformanceConsole.test.tsx`
- Modify: `desktop/web/tests/router.test.tsx`

- [ ] **Step 1: Write the failing route test**

Add a router test that sets `window.location.hash` to `#/performance-console`, renders `<App client={fake.asClient()} performanceConsole={performanceConsoleModel} />` without seeding `sessionStatus`, and expects `screen.getByTestId('performance-console')` to be present while the connecting placeholder, Cockpit, and Wizard are absent.

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
npm.cmd run test:run -- tests/router.test.tsx
```

Expected: TypeScript/Vitest fails because `App` does not accept `performanceConsole` and the route still renders the connecting placeholder.

- [ ] **Step 3: Extract the shared fixture**

Move the existing `model` object from `desktop/web/tests/cockpit/PerformanceConsole.test.tsx` to `desktop/web/tests/cockpit/performanceConsoleFixture.ts`:

```ts
import type { LiveGuiPerformanceConsoleModelDict } from '../../src/types/live_gui_protocol';

export const performanceConsoleModel: LiveGuiPerformanceConsoleModelDict = {
  console_version: 'live-gui-performance-console-v1',
  // keep the existing fixture fields byte-for-byte where practical
};
```

Then import `performanceConsoleModel` in both tests.

- [ ] **Step 4: Run fixture refactor test**

Run:

```powershell
npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx
```

Expected: component test still passes.

### Task 2: App Preview Route

**Files:**
- Modify: `desktop/web/src/App.tsx`
- Modify: `desktop/web/tests/router.test.tsx`

- [ ] **Step 1: Implement minimal route support**

In `App.tsx`, import `PerformanceConsole` and `LiveGuiPerformanceConsoleModelDict`, extend `AppProps`, add:

```ts
function isPerformanceConsoleRoute(hash: string): boolean {
  return hash === '#/performance-console' || hash === '#/console';
}
```

Then render the console before the `sessionStatus === null` branch only when `performanceConsole` is provided:

```tsx
if (isPerformanceConsoleRoute(route) && performanceConsole) {
  return (
    <>
      <LiveRegion />
      <div ref={routeRootRef} tabIndex={-1}>
        <PerformanceConsole model={performanceConsole} />
      </div>
    </>
  );
}
```

- [ ] **Step 2: Update document title logic**

Set the title to `RytmRandomizer · Performance Console` when the preview route has a model. Preserve `Connecting`, `Profile Wizard`, and `Cockpit` titles elsewhere.

- [ ] **Step 3: Add fallback and swap tests**

Add tests that prove:

- `#/performance-console` without `performanceConsole` still shows the connecting placeholder if no session exists.
- Changing hash from `#/performance-console` to `#/wizard` with a seeded session swaps to the wizard.
- Changing hash from `#/performance-console` to `#/` with a seeded session swaps to Cockpit.

- [ ] **Step 4: Run router tests**

Run:

```powershell
npm.cmd run test:run -- tests/router.test.tsx
```

Expected: router tests pass.

### Task 3: Docs And Verification

**Files:**
- Modify: `docs/STATUS.md`

- [ ] **Step 1: Update status**

Add one Recent Cleanup entry dated 2026-06-12 describing the passive frontend route and explicitly saying it opens no port and sends no MIDI.

- [ ] **Step 2: Run focused verification**

Run:

```powershell
npm.cmd run test:run -- tests/router.test.tsx tests/cockpit/PerformanceConsole.test.tsx
npm.cmd run typecheck
npm.cmd run lint
python -m pytest tests/architecture/ -q
```

Expected: all commands pass.

- [ ] **Step 3: Inspect diff**

Run:

```powershell
git diff --stat
git diff -- desktop/web/src/App.tsx desktop/web/tests/router.test.tsx desktop/web/tests/cockpit/PerformanceConsole.test.tsx desktop/web/tests/cockpit/performanceConsoleFixture.ts docs/STATUS.md docs/superpowers/plans/2026-06-12-cockpit-performance-console-preview-route.md
```

Expected: only planned files changed.

- [ ] **Step 4: Commit, push, and open PR**

Run:

```powershell
git add desktop/web/src/App.tsx desktop/web/tests/router.test.tsx desktop/web/tests/cockpit/PerformanceConsole.test.tsx desktop/web/tests/cockpit/performanceConsoleFixture.ts docs/STATUS.md docs/superpowers/plans/2026-06-12-cockpit-performance-console-preview-route.md
git commit -m "feat: add Cockpit performance console preview route"
git push -u origin codex/cockpit-performance-console-preview-route
```

Then create one PR against `modularize-v1.34` using the repo template and include the plan link.

## Plan-Requirements Conformance

Per docs/PLAN_REQUIREMENTS.md, this plan commits to:

- [x] Gate 1 (100% branch coverage on touched files) - frontend-only TypeScript changes; covered by route/component tests and typecheck.
- [x] Gate 2 (V1.34 parity fixtures byte-identical) - no parity fixtures touched.
- [x] Gate 3 (lint/format/type clean) - run frontend lint/typecheck and relevant Python architecture checks.
- [x] Gate 4 (dead-code purge) - no new dead Python code; TypeScript imports verified by lint.
- [x] Gate 5 (docs updated before PR open) - update `docs/STATUS.md` and commit this plan.
- [x] Gate 6 (type-system hygiene) - use generated protocol type, no `Any`.
- [x] Gate 7 (observability adoption) - no hot-path state transition, guardrail decision, or MIDI send added.
- [x] Gate 8 (test hygiene) - intent-named route/component tests with shared fixture.
- [x] Gate 9 (module-organization hygiene) - no new Python modules or top-level package additions.
- [x] Gate 10 (string-literal dispatch hygiene) - only UI hash route strings, no Python mode/page dispatch.
- [x] Gate 11 (shared test fixtures) - console model extracted for reuse.
- [x] Gate 12 (module-level constants use Final) - no new Python constants.
- [x] Gate 13 (env vars: docs + safe default) - no env vars added.
- [x] Gate 14 (maintainability review) - this small plan scopes file ownership and future extension path.
- [x] Gate 15 (learning phase) - no new reusable project lesson discovered yet; status doc captures result.
- [x] Gate 16 (execution shape) - one isolated worktree, one PR, self-driving verification.
- [x] Gate 17 (abstraction reuse and genericization) - reuse existing `PerformanceConsole` and generated protocol instead of creating a second renderer/model.
- [x] Gate 18 (architecture-doc and diagram freshness) - no new architecture surface; existing Cockpit architecture remains unchanged.

Exceptions:

- None.

## Self-Review

- Spec coverage: the plan covers route access, injected passive model rendering, fallback behavior, docs, and verification.
- Placeholder scan: no TBD/TODO placeholders remain; the copied fixture instruction preserves the existing object rather than inventing a partial test model.
- Type consistency: `performanceConsole` is consistently typed as `LiveGuiPerformanceConsoleModelDict`; route names are consistently `#/performance-console` and `#/console`.
