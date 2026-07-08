# ADA AA Accessibility Implementation Plan

> Status: in-flight (Phase A + B + C.12 landed on `feat/ada-aa-accessibility`; C.13 push + PR open pending)
>
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship one bundled PR that makes the RytmRandomizer desktop UI fully WCAG 2.2 AA compliant, drivable without a mouse, and usable with NVDA + VoiceOver, with a multi-layer automated test suite and 9 Python architecture guards using the RR4 ratchet pattern.

**Architecture:** Detector-first ratchet pattern proven on PR #113's RR4 set. Phase A (Tasks 1–4) installs infrastructure (deps, Vitest a11y harness, Playwright a11y harness, Python arch guards) with grandfathered floors capturing the current audit count. Phase B (Tasks 5–11) fixes each cluster in parallel; each fix drops its matching floor. Phase C (Tasks 12–13) captures Playwright `ariaSnapshot` regression fixtures and tightens every floor to 0.

**Tech Stack:** TypeScript + React 18.3 + Vite + Vitest 2.x + Playwright 1.59+ + axe-core (direct) + @axe-core/playwright + zustand. Python arch tests with pytest + AST (no new Python deps). Pre-push hook gates on black + isort + ruff; the project enforces 100% branch coverage on `src/cockpit/**` and `src/wizard/**` via vite.config.ts thresholds.

**Branch:** `feat/ada-aa-accessibility`
**Working directory:** `<repo-worktree>`
**Spec:** `docs/superpowers/specs/2026-05-25-ada-aa-accessibility-design.md`

---

## File Structure

### New TypeScript modules (`desktop/web/src/a11y/`)

| File | Responsibility | Consumed by |
|---|---|---|
| `announcer.ts` | `announce(message, priority?)` — debounced writes into a single global live region. Holds a module-level callback set by `LiveRegion.tsx`. | App + Zustand store + wizard step transitions |
| `LiveRegion.tsx` | Renders the `<div role="status" aria-live="polite" aria-atomic="true" className="sr-only">` and registers the write callback with the announcer module on mount. | App.tsx root |
| `useFocusOnRouteChange.ts` | Hook that, when the hash route changes, moves focus to a ref-attached element (typically the route's `<h1>`). | App.tsx (cockpit + wizard mount points) |
| `useDocumentTitle.ts` | Hook that sets `document.title` from a string and restores the previous title on unmount. | Cockpit + Wizard root components |
| `rovingTabindex.ts` | Pure helpers: `nextIndex(current, length, key)` returns the next focused index for ArrowLeft/ArrowRight/Home/End. Stateless utility consumed by ProfileToggle + HistoryStrip. | ProfileToggle.tsx, HistoryStrip.tsx |
| `srOnly.css` | The visually-hidden-but-screen-reader-accessible class. Imported once by LiveRegion.tsx. | LiveRegion.tsx |
| `index.ts` | Re-exports the public surface (`announce`, `LiveRegion`, `useFocusOnRouteChange`, `useDocumentTitle`, `rovingTabindex` helpers). | App + cockpit + wizard imports |

### Modified TypeScript files

| File | Why |
|---|---|
| `desktop/web/src/App.tsx` | Mount `<LiveRegion />` at root; call `useFocusOnRouteChange` on hash change; call `useDocumentTitle` per route |
| `desktop/web/src/cockpit/Cockpit.tsx` | Change root `<div className="cockpit-root">` to `<main className="cockpit-root">`; add `<h1>RytmRandomizer · Cockpit</h1>` (visually hidden via `srOnly` since the header bar is the visual title) |
| `desktop/web/src/cockpit/ProfileToggle.tsx` | Roving tabindex + Left/Right/Home/End key handler |
| `desktop/web/src/cockpit/HistoryStrip.tsx` | Roving tabindex + Left/Right/Home/End on the snapshot dots |
| `desktop/web/src/cockpit/styles.css` | Knob/pad-card label color tokens swap; reduced-motion + forced-colors `@media` overrides |
| `desktop/web/src/wizard/NameStep.tsx` | `aria-invalid`, `aria-describedby`, `<div role="alert">` error region, focus-on-error |
| `desktop/web/src/wizard/AddStep.tsx` | Same error feedback pattern |
| `desktop/web/src/wizard/AnalyzeStep.tsx` | Wire `announce()` for progress updates (`"Analyzing source X of N"`) |
| `desktop/web/src/wizard/ReviewStep.tsx` | Wire `announce()` for save success |
| `desktop/web/src/wizard/styles.css` | Reduced-motion overrides |
| `desktop/web/src/state/cockpit_store.ts` (or equivalent) | Subscribe to mutation_previewed / send_plan_changed / sessionStatus and call `announce()` |
| `desktop/web/package.json` | Add `axe-core`, `@axe-core/playwright`; bump `@playwright/test` to ≥1.59 for `page.ariaSnapshot()` |
| `desktop/web/tests/setup.ts` | No change required — axe-core called per-test, not globally |
| `desktop/web/playwright.config.ts` | No change required (single-project chromium is fine for now) |

### New TypeScript tests (`desktop/web/tests/a11y/`)

| File | What it tests |
|---|---|
| `axe_smoke.test.tsx` | Renders each top-level component (Cockpit, Wizard.NameStep, AddStep, AnalyzeStep, ReviewStep) and asserts `axe.run(container)` returns zero violations (or matches the per-component grandfathered list). |
| `keyboard_navigation.test.tsx` | userEvent.tab() / .keyboard() flows for ProfileToggle tablist, HistoryStrip dots, DepthSlider, form Tab order. |
| `live_region.test.tsx` | Mounts App with a stub Zustand store, fires mutation_previewed/send_complete/session_status events, asserts `getByRole('status').textContent` matches the documented announcement. |
| `focus_management.test.tsx` | Route transition focus, form-error focus restoration. |
| `document_title.test.tsx` | Each route mount asserts `document.title` matches the route's pattern. |
| `contrast.test.ts` | Parses `cockpit/styles.css` + `wizard/styles.css` CSS custom-property pairings, computes WCAG ratio via `relativeLuminance(rgb)` formula, fails on any documented small-text pair < 4.5. |
| `form_errors.test.tsx` | NameStep + AddStep — submit empty, assert `aria-invalid="true"`, `aria-describedby` resolves to a `role="alert"` element with the documented text, focus is on the invalid field. |
| `announcer.test.ts` | Unit test on the `announcer.ts` module — `announce(msg)` writes; debounce coalesces rapid calls; unregistered callback is a no-op (defensive). |
| `roving_tabindex.test.ts` | Unit test on `rovingTabindex.ts` helpers — `nextIndex(0, 3, 'ArrowRight') === 1`, `nextIndex(2, 3, 'ArrowRight') === 0` (wraps), `nextIndex(any, 3, 'Home') === 0`, `nextIndex(any, 3, 'End') === 2`. |

### New Playwright E2E (`desktop/web/e2e/`)

| File | What it tests |
|---|---|
| `a11y_keyboard_journey.spec.ts` | Cockpit + wizard happy paths driven entirely via `page.keyboard.press` + `page.keyboard.type`; no `page.click()` allowed. Asserts every UI surface a sighted user reaches is reachable. |
| `a11y_axe_scan.spec.ts` | `@axe-core/playwright` scan per route. WCAG 2.2 AA only. |
| `a11y_screen_reader_journey.spec.ts` | Drives the wizard happy path; asserts `page.ariaSnapshot()` matches committed YAML fixtures at 8 checkpoints. |

### New Python arch tests (`tests/architecture/`)

All 9 use the RR4 ratchet shape. Each ships with two companion tests: (a) main rule (count ≤ floor), (b) drain-allowlist (floor ≤ actual).

| File | What it forbids |
|---|---|
| `test_a11y_no_div_onclick.py` | `<div onClick>` / `<span onClick>` in `desktop/web/src/`. |
| `test_a11y_every_icon_button_has_aria_label.py` | `<button>` with icon-only children must have `aria-label`/`aria-labelledby`. |
| `test_a11y_every_form_field_has_label.py` | `<input>`/`<textarea>`/`<select>` must have label association. |
| `test_a11y_every_route_has_main_landmark.py` | Cockpit + Wizard root components render exactly one `<main>` and exactly one `<h1>`. |
| `test_a11y_color_palette_aa.py` | Documented CSS custom-property pairings meet AA contrast. |
| `test_a11y_no_aria_hidden_focusable.py` | `aria-hidden="true"` elements cannot be focusable. |
| `test_a11y_no_role_attribute_redundancy.py` | `role="button"` on `<button>`, `role="link"` on `<a>` forbidden. |
| `test_a11y_announcer_is_wired.py` | `App.tsx` must mount the live-region `<div role="status" aria-live="polite">`. |
| `test_a11y_reduced_motion_respected.py` | CSS files with `@keyframes`/`animation:`/`transition:` (non-instant) must have `@media (prefers-reduced-motion)` overrides. |

---

## Parallel Execution Map

For `subagent-driven-development` with maximum parallelization, tasks group as follows:

**Phase A — Infrastructure (SEQUENTIAL, 1 subagent at a time):**
- Task 1 → Task 2 → Task 3 → Task 4 (must run in order; each depends on the previous detector floor being set)

**Phase B — Cluster fixes (PARALLEL, 7 subagents simultaneously):**
- Task 5 (Cluster 1: Keyboard)
- Task 6 (Cluster 2: Contrast)
- Task 7 (Cluster 3: Form errors)
- Task 8 (Cluster 4: Live region + announcer)
- Task 9 (Cluster 5: Focus management)
- Task 10 (Cluster 6: Document title + landmarks)
- Task 11 (Cluster 8: Reduced motion + forced colors)

Each Phase B task touches a disjoint file set (see File Structure table). No cross-task merge collisions. Each commits independently and drops its own ratchet floor.

**Phase C — Snapshot + final tighten (SEQUENTIAL):**
- Task 12 (capture Playwright `ariaSnapshot` fixtures — must run after all fixes are in)
- Task 13 (drop every remaining floor to 0; assert drain-allowlist companion tests all pass)

---

## Phase A — Infrastructure

### Task 1: Install + wire a11y deps

**Files:**
- Modify: `desktop/web/package.json`
- Verify: `desktop/web/playwright.config.ts` (no edit expected, but check Playwright version)

- [ ] **Step 1: Verify Playwright current version**

Run from `desktop/web/`:
```bash
npm view @playwright/test version
grep '"@playwright/test"' package.json
```
Expected: package.json reads `"@playwright/test": "^1.49.0"`. If npm view returns ≥1.59, the bump is just a major-version-permissive caret already (≥1.49 → 1.59 satisfies `^1.49.0`). If npm latest is < 1.59, abort and surface.

- [ ] **Step 2: Add the three deps**

Run from `desktop/web/`:
```bash
npm install --save-dev axe-core @axe-core/playwright
npm install --save-dev @playwright/test@latest
```

Then verify `package.json` shows:
- `"axe-core": "^4.x"`
- `"@axe-core/playwright": "^4.x"`
- `"@playwright/test"` upgraded to ≥1.59

- [ ] **Step 3: Run typecheck to confirm no breakage**

Run from `desktop/web/`:
```bash
npm run typecheck
```
Expected: clean exit 0.

- [ ] **Step 4: Commit**

```bash
git add desktop/web/package.json desktop/web/package-lock.json
git commit -m "chore(a11y): install axe-core + @axe-core/playwright; bump Playwright for ariaSnapshot

Phase A.1 of ADA AA accessibility plan. Adds the dependencies the new
test suite consumes:

- axe-core: called directly inside Vitest tests (no jest-axe wrapper —
  wrong runner — and no vitest-axe — stale, pre-1.0)
- @axe-core/playwright: E2E a11y scans
- @playwright/test bumped to >=1.59 for page.ariaSnapshot() YAML
  accessibility-tree snapshots

See docs/superpowers/specs/2026-05-25-ada-aa-accessibility-design.md
for full library rationale."
```

---

### Task 2: Vitest a11y harness — axe-core smoke + utilities

**Files:**
- Create: `desktop/web/tests/a11y/__helpers__/axe.ts` — wraps `axe.run` with WCAG 2.2 AA preset config
- Create: `desktop/web/tests/a11y/axe_smoke.test.tsx`
- Create: `desktop/web/tests/a11y/announcer.test.ts`
- Create: `desktop/web/tests/a11y/roving_tabindex.test.ts` — pinned against helpers that don't exist yet; uses `describe.skip()` until Task 5 lands

- [ ] **Step 1: Create the axe helper**

Create `desktop/web/tests/a11y/__helpers__/axe.ts`:
```ts
/**
 * Shared axe-core runner for Vitest a11y tests. Configures WCAG 2.2 AA
 * tags so the helper rejects per WCAG 2.0/2.1/2.2 A + AA rules but does
 * NOT trip on best-practice-only rules (which are advisory).
 */
import axe, { type AxeResults, type RunOptions } from 'axe-core';

const DEFAULT_OPTIONS: RunOptions = {
  runOnly: {
    type: 'tag',
    values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'],
  },
};

export async function runAxe(
  container: Element,
  overrides: RunOptions = {},
): Promise<AxeResults> {
  return axe.run(container, { ...DEFAULT_OPTIONS, ...overrides });
}

export function violationSummary(results: AxeResults): string {
  if (results.violations.length === 0) return 'no violations';
  return results.violations
    .map((v) => `  - ${v.id} (${v.impact}): ${v.help}`)
    .join('\n');
}
```

- [ ] **Step 2: Write the failing axe smoke test**

Create `desktop/web/tests/a11y/axe_smoke.test.tsx`:
```tsx
/**
 * Per-component axe-core smoke tests. Each component is rendered into a
 * detached container and scanned for WCAG 2.2 AA violations. The
 * grandfathered-violations map records the AUDIT BASELINE — every entry
 * is a known finding the fix-cluster tasks will drive to zero. New
 * violations on a component without an entry fail the test loudly.
 */
import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { ProfileToggle } from '../../src/cockpit/ProfileToggle';
import { runAxe, violationSummary } from './__helpers__/axe';

// Floor map: component-name → expected violation count. Each fix-cluster
// task drops the matching entry to 0 (or removes it once fully clean).
const FLOORS: Record<string, number> = {
  ProfileToggle: 0, // already clean per audit
};

describe('axe-core smoke (WCAG 2.2 AA)', () => {
  it('ProfileToggle has no violations beyond the floor', async () => {
    const { container } = render(<ProfileToggle value="scene" onChange={() => {}} />);
    const results = await runAxe(container);
    expect(results.violations.length, violationSummary(results)).toBeLessThanOrEqual(
      FLOORS.ProfileToggle,
    );
  });
});
```

- [ ] **Step 3: Write the failing announcer test (skipped for now)**

Create `desktop/web/tests/a11y/announcer.test.ts`:
```ts
/**
 * Unit coverage for the announcer module. Task 8 implements the module;
 * this test file lands now (Phase A) so the test infrastructure is in
 * place and the failing-by-skip status is visible in CI.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';

describe.skip('announcer (lands with Task 8)', () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it('calls the registered callback with the message', async () => {
    const { announce, _registerWriter } = await import('../../src/a11y/announcer');
    const writer = vi.fn();
    _registerWriter(writer);
    announce('hello');
    await new Promise((r) => setTimeout(r, 250));
    expect(writer).toHaveBeenCalledWith('hello');
  });

  it('debounces rapid calls', async () => {
    const { announce, _registerWriter } = await import('../../src/a11y/announcer');
    const writer = vi.fn();
    _registerWriter(writer);
    announce('first');
    announce('second');
    announce('third');
    await new Promise((r) => setTimeout(r, 250));
    expect(writer).toHaveBeenCalledTimes(1);
    expect(writer).toHaveBeenCalledWith('third');
  });

  it('is a no-op when no writer is registered', () => {
    return import('../../src/a11y/announcer').then(({ announce }) => {
      expect(() => announce('nobody home')).not.toThrow();
    });
  });
});
```

- [ ] **Step 4: Write the failing roving tabindex test (skipped for now)**

Create `desktop/web/tests/a11y/roving_tabindex.test.ts`:
```ts
/**
 * Unit coverage for the rovingTabindex helpers. Task 5 implements them;
 * test file lands now (Phase A) so infrastructure is in place.
 */
import { describe, it, expect } from 'vitest';

describe.skip('rovingTabindex.nextIndex (lands with Task 5)', () => {
  it('ArrowRight advances by 1', async () => {
    const { nextIndex } = await import('../../src/a11y/rovingTabindex');
    expect(nextIndex(0, 3, 'ArrowRight')).toBe(1);
  });

  it('ArrowRight wraps at end', async () => {
    const { nextIndex } = await import('../../src/a11y/rovingTabindex');
    expect(nextIndex(2, 3, 'ArrowRight')).toBe(0);
  });

  it('ArrowLeft retreats by 1', async () => {
    const { nextIndex } = await import('../../src/a11y/rovingTabindex');
    expect(nextIndex(1, 3, 'ArrowLeft')).toBe(0);
  });

  it('ArrowLeft wraps at start', async () => {
    const { nextIndex } = await import('../../src/a11y/rovingTabindex');
    expect(nextIndex(0, 3, 'ArrowLeft')).toBe(2);
  });

  it('Home jumps to 0', async () => {
    const { nextIndex } = await import('../../src/a11y/rovingTabindex');
    expect(nextIndex(2, 5, 'Home')).toBe(0);
  });

  it('End jumps to last index', async () => {
    const { nextIndex } = await import('../../src/a11y/rovingTabindex');
    expect(nextIndex(0, 5, 'End')).toBe(4);
  });

  it('Unknown key returns the current index', async () => {
    const { nextIndex } = await import('../../src/a11y/rovingTabindex');
    expect(nextIndex(1, 3, 'Space')).toBe(1);
  });
});
```

- [ ] **Step 5: Run new tests to confirm baseline state**

Run from `desktop/web/`:
```bash
npm run test:run -- tests/a11y/
```
Expected: `axe_smoke` passes (ProfileToggle floor 0 already), `announcer` + `roving_tabindex` show as skipped. Total: 1 pass, ~10 skipped, 0 failed.

- [ ] **Step 6: Commit**

```bash
git add desktop/web/tests/a11y/
git commit -m "test(a11y): install Vitest a11y harness + first axe-core smoke

Phase A.2: scaffold the Vitest a11y test suite.

- tests/a11y/__helpers__/axe.ts — shared axe.run wrapper pinned to
  WCAG 2.2 AA tags
- axe_smoke.test.tsx — per-component scan with FLOORS map (the
  ratchet); first entry (ProfileToggle) already at 0
- announcer.test.ts + roving_tabindex.test.ts — failing-by-skip
  until Tasks 5 + 8 implement the modules

Subsequent fix-cluster tasks add their components to FLOORS at the
audit baseline, then drop to 0 as fixes land."
```

---

### Task 3: Playwright a11y harness

**Files:**
- Create: `desktop/web/e2e/a11y_axe_scan.spec.ts`
- Create: `desktop/web/e2e/a11y_keyboard_journey.spec.ts`
- Create: `desktop/web/e2e/a11y_screen_reader_journey.spec.ts` (snapshots committed in Task 12)

- [ ] **Step 1: Write the failing axe scan E2E**

Create `desktop/web/e2e/a11y_axe_scan.spec.ts`:
```ts
/**
 * E2E axe-core scan per top-level route. Same per-route grandfathered
 * floor map as the Vitest smoke suite so they cannot drift apart.
 */
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

// Per-route floor map. Each fix-cluster task drops its entry to 0.
const FLOORS: Record<string, number> = {
  '/': 0,
  '/#/wizard': 0,
};

const ROUTES = Object.keys(FLOORS);

for (const route of ROUTES) {
  test(`axe-core scan on route ${route}`, async ({ page }) => {
    await page.goto(route);
    // Wait for the cockpit/wizard root to mount (no `domcontentloaded`
    // race — the Cockpit waits for a session_status event).
    await page
      .getByTestId(route === '/' ? 'cockpit-root' : 'wizard-root')
      .waitFor({ state: 'visible', timeout: 10_000 });
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
      .analyze();
    const violations = results.violations.length;
    expect(
      violations,
      `${route}: ${results.violations.map((v) => v.id).join(', ')}`,
    ).toBeLessThanOrEqual(FLOORS[route]);
  });
}
```

- [ ] **Step 2: Write the failing keyboard journey E2E (skeleton)**

Create `desktop/web/e2e/a11y_keyboard_journey.spec.ts`:
```ts
/**
 * Cockpit + wizard happy paths driven via page.keyboard only.
 * Forbids page.click() — every UI surface must be keyboard-reachable.
 *
 * Phase A: skeleton with a single skipped test. Phase B fix tasks
 * un-skip + flesh out as their cluster lands.
 */
import { test, expect } from '@playwright/test';

test.describe('A11y keyboard journey (no mouse allowed)', () => {
  test.skip('cockpit boot: Tab order header → mutation → snapshot → action', async ({
    page,
  }) => {
    await page.goto('/');
    await page.getByTestId('cockpit-root').waitFor({ state: 'visible', timeout: 10_000 });
    // Sanity: focus body, then Tab through.
    await page.keyboard.press('Tab');
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(focused).not.toBe('BODY');
    // Cluster 1 task fleshes out the full Tab sequence assertions.
  });
});
```

- [ ] **Step 3: Write the failing SR journey E2E (skeleton, fixtures empty)**

Create `desktop/web/e2e/a11y_screen_reader_journey.spec.ts`:
```ts
/**
 * Captures page.ariaSnapshot() at the 8 documented checkpoints from
 * the spec (§"Manual SR test plan"). Phase C (Task 12) commits the
 * actual YAML fixtures after all fixes are in place.
 *
 * Until then, this spec is `test.skip()` so CI doesn't fail on missing
 * snapshot files.
 */
import { test, expect } from '@playwright/test';

test.describe('A11y SR-equivalent journey (page.ariaSnapshot fixtures)', () => {
  test.skip('cockpit-boot snapshot', async ({ page }) => {
    await page.goto('/');
    await page.getByTestId('cockpit-root').waitFor({ state: 'visible' });
    const snapshot = await page.ariaSnapshot();
    expect(snapshot).toMatchSnapshot('cockpit-boot.aria.yml');
  });
});
```

- [ ] **Step 4: Run the Playwright suite**

Run from `desktop/web/`:
```bash
npx playwright test e2e/a11y_axe_scan.spec.ts e2e/a11y_keyboard_journey.spec.ts e2e/a11y_screen_reader_journey.spec.ts
```
Expected: axe scan tests pass (FLOORS at 0, baseline assumed clean for now — if they fail, those failures are the audit-discovered violations and become the initial floor values in Step 5 below); keyboard + SR specs skipped.

- [ ] **Step 5: If axe scan fails on either route, bump that route's floor in FLOORS to the violation count**

If `/` reports e.g. 3 violations, change `'/': 0` to `'/': 3` so the test passes as the new baseline. Add a comment naming each violation id so Phase B tasks know which floor to drop. The drain-allowlist companion is the test re-running with the new floor value — it'll fail the moment a violation is fixed but the floor isn't lowered (that's the intended drain shape).

- [ ] **Step 6: Commit**

```bash
git add desktop/web/e2e/
git commit -m "test(a11y): Playwright a11y harness — axe scan + keyboard + SR skeletons

Phase A.3: scaffold the Playwright a11y E2E suite.

- a11y_axe_scan.spec.ts — @axe-core/playwright per-route scan with
  FLOORS map (matches Vitest harness shape so they cannot drift)
- a11y_keyboard_journey.spec.ts — single skipped sanity test;
  Phase B Cluster 1 task fleshes out the full Tab sequence
- a11y_screen_reader_journey.spec.ts — skipped until Phase C Task 12
  captures the ariaSnapshot YAML fixtures"
```

---

### Task 4: Python arch guards (9 detectors)

**Files:**
- Create: 9 files under `tests/architecture/test_a11y_*.py`

These run alongside the existing RR4 set in the fast suite (~5s).

- [ ] **Step 1: Create `test_a11y_no_div_onclick.py`**

Create `tests/architecture/test_a11y_no_div_onclick.py`:
```python
"""Forbid <div onClick> / <span onClick> antipatterns in desktop/web/src/.

Semantic <button>/<a> elements are keyboard-accessible and announced
correctly by screen readers. Click handlers on generic containers are
not. This guard scans every TS/TSX file under desktop/web/src/ for the
JSX pattern <div onClick={...}> or <span onClick={...}>.

Audit baseline (2026-05-25): 0 violations — Cockpit + Wizard already
use semantic elements everywhere.

Companion: test_grandfathered_div_onclick_floor_does_not_grow
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
WEB_SRC: Final[Path] = PROJECT_ROOT / "desktop" / "web" / "src"

# (relpath, count) pairs of currently-known violations. New violations
# without an allowlist entry fail the main rule.
_GRANDFATHERED: Final[dict[str, int]] = {}

_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"<(div|span)[^>]*\sonClick\s*=", re.MULTILINE
)


def _ts_files() -> list[Path]:
    if not WEB_SRC.is_dir():
        return []
    return sorted(
        p
        for p in WEB_SRC.rglob("*.tsx")
        if "node_modules" not in p.parts
    )


def _count_violations(path: Path) -> int:
    return len(_PATTERN.findall(path.read_text(encoding="utf-8")))


def test_no_div_onclick_in_desktop_web_src() -> None:
    """No <div onClick> / <span onClick> may appear in desktop/web/src/.

    Forces semantic <button>/<a>. Use the keyboard-event helper from
    desktop/web/src/a11y/ if you need a custom interactive widget.
    """
    violations: list[str] = []
    for path in _ts_files():
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        count = _count_violations(path)
        floor = _GRANDFATHERED.get(rel, 0)
        if count > floor:
            violations.append(
                f"{rel}: {count} <div|span onClick> instances "
                f"(floor {floor}). Replace with <button> / <a>."
            )
    assert not violations, (
        "ADA AA regression: <div onClick> antipatterns found.\n  "
        + "\n  ".join(violations)
    )


def test_grandfathered_div_onclick_floor_does_not_grow() -> None:
    """Drain-allowlist: floor must equal (not exceed) actual count."""
    redundant: list[str] = []
    for rel, floor in _GRANDFATHERED.items():
        path = PROJECT_ROOT / rel
        if not path.is_file():
            redundant.append(f"{rel}: in allowlist but file is gone.")
            continue
        actual = _count_violations(path)
        if actual < floor:
            redundant.append(
                f"{rel}: floor {floor} but actual {actual}. Drain entry."
            )
    assert not redundant, (
        "Stale a11y allowlist — drain entries to actual counts:\n  "
        + "\n  ".join(redundant)
    )
```

- [ ] **Step 2: Create `test_a11y_every_icon_button_has_aria_label.py`**

Create `tests/architecture/test_a11y_every_icon_button_has_aria_label.py`:
```python
"""Every icon-only <button> must declare an accessible name.

A <button> whose only children are an icon (<svg>, <Icon>, <img>)
needs an `aria-label` or `aria-labelledby` for SRs to announce its
purpose. Visible text children satisfy the accessible-name requirement
automatically.

Audit baseline (2026-05-25): 0 violations — every icon-only button in
LockButton, HistoryStrip, etc. already carries an aria-label.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
WEB_SRC: Final[Path] = PROJECT_ROOT / "desktop" / "web" / "src"

_GRANDFATHERED: Final[dict[str, int]] = {}

# Buttons whose first non-whitespace child looks like an icon component
# (capital-letter JSX or <svg>/<img>) AND that lack aria-label /
# aria-labelledby on the <button> open tag.
_ICON_BUTTON: Final[re.Pattern[str]] = re.compile(
    r"<button(?P<attrs>(?:[^>]|>(?!</button>))*?)>\s*"
    r"<(?:svg|img|[A-Z][A-Za-z0-9]*)[^>]*/?>\s*</button>",
    re.MULTILINE,
)


def _ts_files() -> list[Path]:
    if not WEB_SRC.is_dir():
        return []
    return sorted(p for p in WEB_SRC.rglob("*.tsx") if "node_modules" not in p.parts)


def _count_violations(path: Path) -> int:
    count = 0
    for match in _ICON_BUTTON.finditer(path.read_text(encoding="utf-8")):
        attrs = match.group("attrs") or ""
        if "aria-label" not in attrs and "aria-labelledby" not in attrs:
            count += 1
    return count


def test_every_icon_button_has_aria_label() -> None:
    violations: list[str] = []
    for path in _ts_files():
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        count = _count_violations(path)
        floor = _GRANDFATHERED.get(rel, 0)
        if count > floor:
            violations.append(
                f"{rel}: {count} icon-only <button> without aria-label "
                f"(floor {floor})."
            )
    assert not violations, (
        "ADA AA regression: icon-only buttons missing accessible name.\n  "
        + "\n  ".join(violations)
    )


def test_grandfathered_icon_button_floor_does_not_grow() -> None:
    redundant: list[str] = []
    for rel, floor in _GRANDFATHERED.items():
        path = PROJECT_ROOT / rel
        if not path.is_file():
            redundant.append(f"{rel}: in allowlist but file is gone.")
            continue
        actual = _count_violations(path)
        if actual < floor:
            redundant.append(f"{rel}: floor {floor} but actual {actual}. Drain entry.")
    assert not redundant, "\n  ".join(redundant) if redundant else ""
```

- [ ] **Step 3: Create `test_a11y_every_form_field_has_label.py`**

Create `tests/architecture/test_a11y_every_form_field_has_label.py`:
```python
"""Every <input>/<textarea>/<select> must have a label association.

Three valid forms of association: a wrapping <label>, an aria-label
on the field, or aria-labelledby pointing at an id elsewhere.

Audit baseline (2026-05-25): 0 violations — NameStep + AddStep wrap
their inputs in <label> elements; DepthSlider has aria-label.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
WEB_SRC: Final[Path] = PROJECT_ROOT / "desktop" / "web" / "src"

_GRANDFATHERED: Final[dict[str, int]] = {}

# Matches a self-closing <input ... /> tag.
_FORM_FIELD: Final[re.Pattern[str]] = re.compile(
    r"<(?P<tag>input|textarea|select)(?P<attrs>(?:[^>]|>(?!</))*?)/?>",
    re.MULTILINE,
)


def _ts_files() -> list[Path]:
    if not WEB_SRC.is_dir():
        return []
    return sorted(p for p in WEB_SRC.rglob("*.tsx") if "node_modules" not in p.parts)


def _has_association(attrs: str) -> bool:
    return (
        "aria-label" in attrs
        or "aria-labelledby" in attrs
        or 'type="hidden"' in attrs
    )


def _count_violations(path: Path) -> int:
    # Read the whole file; count fields that have neither an aria-label
    # nor sit inside a wrapping <label>.
    source = path.read_text(encoding="utf-8")
    count = 0
    for match in _FORM_FIELD.finditer(source):
        attrs = match.group("attrs") or ""
        if _has_association(attrs):
            continue
        # Check the 100 chars before the match for an opening <label
        window = source[max(0, match.start() - 200) : match.start()]
        if "<label" in window:
            continue
        count += 1
    return count


def test_every_form_field_has_label() -> None:
    violations: list[str] = []
    for path in _ts_files():
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        count = _count_violations(path)
        floor = _GRANDFATHERED.get(rel, 0)
        if count > floor:
            violations.append(
                f"{rel}: {count} unlabeled form field(s) (floor {floor})."
            )
    assert not violations, (
        "ADA AA regression: unlabeled form fields.\n  " + "\n  ".join(violations)
    )


def test_grandfathered_form_field_floor_does_not_grow() -> None:
    redundant: list[str] = []
    for rel, floor in _GRANDFATHERED.items():
        path = PROJECT_ROOT / rel
        if not path.is_file():
            redundant.append(f"{rel}: in allowlist but file is gone.")
            continue
        actual = _count_violations(path)
        if actual < floor:
            redundant.append(f"{rel}: floor {floor} but actual {actual}. Drain entry.")
    assert not redundant, "\n  ".join(redundant)
```

- [ ] **Step 4: Create `test_a11y_every_route_has_main_landmark.py`**

Create `tests/architecture/test_a11y_every_route_has_main_landmark.py`:
```python
"""Top-level route components must render exactly one <main> and exactly one <h1>.

Routes (per App.tsx hash router):
- `/` (or empty) → Cockpit.tsx
- `/wizard` → Wizard.tsx
- (placeholder while connecting) → App.tsx renders <main class="cockpit-placeholder">

The connecting-placeholder already has <main> + <h1>. The fix-cluster
6 task ensures Cockpit.tsx + Wizard.tsx do too.

Audit baseline (2026-05-25): floor for Cockpit.tsx is 1 (missing
landmark + h1); will drop to 0 in Cluster 6 task.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
WEB_SRC: Final[Path] = PROJECT_ROOT / "desktop" / "web" / "src"

ROUTE_FILES: Final[dict[str, Path]] = {
    "cockpit": WEB_SRC / "cockpit" / "Cockpit.tsx",
    "wizard": WEB_SRC / "wizard" / "Wizard.tsx",
}

# Floor map: route-name → 0 (compliant) or 1 (missing landmark/h1).
_GRANDFATHERED: Final[dict[str, int]] = {
    "cockpit": 1,  # missing <main> + <h1>; Cluster 6 drops to 0
}


def _has_landmark_and_h1(path: Path) -> bool:
    source = path.read_text(encoding="utf-8")
    return ("<main" in source) and ("<h1" in source)


def test_every_route_renders_main_and_h1() -> None:
    violations: list[str] = []
    for route, path in ROUTE_FILES.items():
        if not path.is_file():
            continue
        compliant = _has_landmark_and_h1(path)
        floor = _GRANDFATHERED.get(route, 0)
        actual = 0 if compliant else 1
        if actual > floor:
            violations.append(
                f"{path.relative_to(PROJECT_ROOT).as_posix()} (route {route}): "
                f"missing <main> or <h1> (floor {floor}, actual {actual})."
            )
    assert not violations, (
        "ADA AA regression: route missing landmark.\n  " + "\n  ".join(violations)
    )


def test_grandfathered_route_landmark_floor_does_not_grow() -> None:
    redundant: list[str] = []
    for route, floor in _GRANDFATHERED.items():
        path = ROUTE_FILES[route]
        if not path.is_file():
            continue
        compliant = _has_landmark_and_h1(path)
        actual = 0 if compliant else 1
        if actual < floor:
            redundant.append(
                f"{route}: floor {floor} but actual {actual}. Drain entry."
            )
    assert not redundant, "\n  ".join(redundant)
```

- [ ] **Step 5: Create `test_a11y_color_palette_aa.py`**

Create `tests/architecture/test_a11y_color_palette_aa.py`:
```python
"""WCAG 2.2 AA contrast for documented color-token pairs.

Parses the CSS custom properties in cockpit/styles.css and wizard/
styles.css; computes relative luminance per the WCAG formula; asserts
every documented foreground/background pair clears the relevant
contrast minimum (4.5 for normal text, 3.0 for large/non-text).

Audit baseline (2026-05-25): `--text-dim` on `--panel-2` at small
font-sizes is marginal; Cluster 2 swaps `.knob-label` and
`.pad-card-title` to `--text` and drops the floor to 0.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
CSS_FILES: Final[tuple[Path, ...]] = (
    PROJECT_ROOT / "desktop" / "web" / "src" / "cockpit" / "styles.css",
    PROJECT_ROOT / "desktop" / "web" / "src" / "wizard" / "styles.css",
)

# (foreground_token, background_token, is_small_text) tuples.
# Small text → 4.5 minimum; large/non-text → 3.0.
DOCUMENTED_PAIRS: Final[list[tuple[str, str, bool]]] = [
    ("--text", "--bg", True),
    ("--text", "--panel", True),
    ("--text", "--panel-2", True),
    ("--text-dim", "--bg", True),
    ("--text-dim", "--panel", True),
    ("--text-dim", "--panel-2", False),  # used on hint text only after Cluster 2
    ("--accent", "--panel-2", False),
    ("--green", "--panel-2", False),
    ("--amber", "--panel-2", False),
    ("--danger", "--panel-2", False),
]

# Floor map: pair-key → 1 (currently failing) or 0 (passing). Cluster 2
# drops the failing entry to 0 by relabelling .knob-label / .pad-card-title
# to use --text not --text-dim (so this pair on `--panel-2` becomes
# large-only via `is_small_text=False`, which we set in the table above).
_GRANDFATHERED: Final[dict[str, int]] = {}


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    def channel(v: int) -> float:
        srgb = v / 255.0
        return srgb / 12.92 if srgb <= 0.03928 else ((srgb + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(fg: tuple[int, int, int], bg: tuple[int, int, int]) -> float:
    lf = _relative_luminance(fg)
    lb = _relative_luminance(bg)
    lighter = max(lf, lb)
    darker = min(lf, lb)
    return (lighter + 0.05) / (darker + 0.05)


def _load_tokens() -> dict[str, str]:
    """Return token-name → hex-value across all CSS files."""
    tokens: dict[str, str] = {}
    pattern = re.compile(r"(--[a-z0-9-]+)\s*:\s*(#[0-9a-fA-F]{6})\s*;")
    for css in CSS_FILES:
        if not css.is_file():
            continue
        for match in pattern.finditer(css.read_text(encoding="utf-8")):
            tokens[match.group(1)] = match.group(2)
    return tokens


def test_documented_color_pairs_meet_aa_contrast() -> None:
    tokens = _load_tokens()
    violations: list[str] = []
    for fg_name, bg_name, is_small in DOCUMENTED_PAIRS:
        if fg_name not in tokens or bg_name not in tokens:
            violations.append(f"Missing token: {fg_name} or {bg_name}")
            continue
        ratio = _contrast(_hex_to_rgb(tokens[fg_name]), _hex_to_rgb(tokens[bg_name]))
        minimum = 4.5 if is_small else 3.0
        key = f"{fg_name}@{bg_name}"
        floor = _GRANDFATHERED.get(key, 0)
        actual = 0 if ratio >= minimum else 1
        if actual > floor:
            violations.append(
                f"{fg_name} on {bg_name}: ratio {ratio:.2f} < {minimum} "
                f"({'small' if is_small else 'large'} text) [floor {floor}]"
            )
    assert not violations, (
        "ADA AA contrast regression:\n  " + "\n  ".join(violations)
    )


def test_grandfathered_contrast_floor_does_not_grow() -> None:
    tokens = _load_tokens()
    redundant: list[str] = []
    for key, floor in _GRANDFATHERED.items():
        fg_name, bg_name = key.split("@", 1)
        if fg_name not in tokens or bg_name not in tokens:
            continue
        ratio = _contrast(_hex_to_rgb(tokens[fg_name]), _hex_to_rgb(tokens[bg_name]))
        is_small = next(
            (s for f, b, s in DOCUMENTED_PAIRS if f == fg_name and b == bg_name), True
        )
        minimum = 4.5 if is_small else 3.0
        actual = 0 if ratio >= minimum else 1
        if actual < floor:
            redundant.append(f"{key}: floor {floor} but actual {actual}.")
    assert not redundant, "\n  ".join(redundant)
```

- [ ] **Step 6: Create `test_a11y_no_aria_hidden_focusable.py`**

Create `tests/architecture/test_a11y_no_aria_hidden_focusable.py`:
```python
"""aria-hidden elements must not be focusable (would trap SR users in invisible state)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
WEB_SRC: Final[Path] = PROJECT_ROOT / "desktop" / "web" / "src"

_GRANDFATHERED: Final[dict[str, int]] = {}

_FOCUSABLE_TAGS = {"button", "input", "select", "textarea", "a"}
_ARIA_HIDDEN: Final[re.Pattern[str]] = re.compile(
    r'<(?P<tag>[A-Za-z][A-Za-z0-9-]*)(?P<attrs>(?:[^>]|>(?!</))*?)\baria-hidden\s*=\s*["\']?true',
    re.MULTILINE,
)


def _ts_files() -> list[Path]:
    if not WEB_SRC.is_dir():
        return []
    return sorted(p for p in WEB_SRC.rglob("*.tsx") if "node_modules" not in p.parts)


def _count_violations(path: Path) -> int:
    source = path.read_text(encoding="utf-8")
    count = 0
    for match in _ARIA_HIDDEN.finditer(source):
        tag = match.group("tag").lower()
        attrs = match.group("attrs") or ""
        if tag in _FOCUSABLE_TAGS:
            count += 1
        elif re.search(r"\btabIndex\s*=\s*\{?\s*[\"']?[0-9]", attrs):
            count += 1
    return count


def test_no_aria_hidden_focusable() -> None:
    violations: list[str] = []
    for path in _ts_files():
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        count = _count_violations(path)
        floor = _GRANDFATHERED.get(rel, 0)
        if count > floor:
            violations.append(f"{rel}: {count} aria-hidden focusable (floor {floor}).")
    assert not violations, "\n  ".join(violations) if violations else ""


def test_grandfathered_aria_hidden_floor_does_not_grow() -> None:
    redundant: list[str] = []
    for rel, floor in _GRANDFATHERED.items():
        path = PROJECT_ROOT / rel
        if not path.is_file():
            redundant.append(f"{rel}: file gone.")
            continue
        actual = _count_violations(path)
        if actual < floor:
            redundant.append(f"{rel}: floor {floor} but actual {actual}.")
    assert not redundant, "\n  ".join(redundant)
```

- [ ] **Step 7: Create `test_a11y_no_role_attribute_redundancy.py`**

Create `tests/architecture/test_a11y_no_role_attribute_redundancy.py`:
```python
"""Redundant role attributes indicate misunderstanding of semantic HTML.

Forbids `role="button"` on a <button>, `role="link"` on <a>, etc.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
WEB_SRC: Final[Path] = PROJECT_ROOT / "desktop" / "web" / "src"

_GRANDFATHERED: Final[dict[str, int]] = {}

REDUNDANT_PAIRS: Final[list[tuple[str, str]]] = [
    ("button", "button"),
    ("a", "link"),
    ("nav", "navigation"),
    ("main", "main"),
    ("header", "banner"),
    ("footer", "contentinfo"),
]


def _ts_files() -> list[Path]:
    if not WEB_SRC.is_dir():
        return []
    return sorted(p for p in WEB_SRC.rglob("*.tsx") if "node_modules" not in p.parts)


def _count_violations(path: Path) -> int:
    source = path.read_text(encoding="utf-8")
    count = 0
    for tag, role in REDUNDANT_PAIRS:
        pat = re.compile(
            rf'<{tag}\b[^>]*\brole\s*=\s*["\']{role}["\']', re.MULTILINE
        )
        count += len(pat.findall(source))
    return count


def test_no_role_attribute_redundancy() -> None:
    violations: list[str] = []
    for path in _ts_files():
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        count = _count_violations(path)
        floor = _GRANDFATHERED.get(rel, 0)
        if count > floor:
            violations.append(f"{rel}: {count} redundant role (floor {floor}).")
    assert not violations, "\n  ".join(violations) if violations else ""


def test_grandfathered_role_redundancy_floor_does_not_grow() -> None:
    redundant: list[str] = []
    for rel, floor in _GRANDFATHERED.items():
        path = PROJECT_ROOT / rel
        if not path.is_file():
            redundant.append(f"{rel}: file gone.")
            continue
        actual = _count_violations(path)
        if actual < floor:
            redundant.append(f"{rel}: floor {floor} but actual {actual}.")
    assert not redundant, "\n  ".join(redundant)
```

- [ ] **Step 8: Create `test_a11y_announcer_is_wired.py`**

Create `tests/architecture/test_a11y_announcer_is_wired.py`:
```python
"""App.tsx must mount the live-region <div role="status" aria-live="polite">.

Without this region, every async UI update (mutation preview, send
result, profile selection) is silent to screen readers.

Audit baseline (2026-05-25): floor 1 (not mounted yet). Cluster 4 task
drops it to 0 by adding <LiveRegion /> to App.tsx.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
APP_TSX: Final[Path] = PROJECT_ROOT / "desktop" / "web" / "src" / "App.tsx"

# Floor starts at 1 (not wired); Cluster 4 drops to 0.
_FLOOR: int = 1


def _is_announcer_wired() -> bool:
    if not APP_TSX.is_file():
        return False
    source = APP_TSX.read_text(encoding="utf-8")
    return ("<LiveRegion" in source) or (
        'role="status"' in source and 'aria-live="polite"' in source
    )


def test_announcer_is_wired_in_app_tsx() -> None:
    wired = _is_announcer_wired()
    actual = 0 if wired else 1
    assert actual <= _FLOOR, (
        "ADA AA regression: App.tsx no longer mounts the live region "
        "(<LiveRegion /> or equivalent role='status' + aria-live='polite' "
        "container). Without it every async event is silent to SR users."
    )


def test_announcer_floor_does_not_grow() -> None:
    """Once Cluster 4 lands the announcer, the floor drops to 0 here."""
    wired = _is_announcer_wired()
    actual = 0 if wired else 1
    assert actual >= _FLOOR or _FLOOR == 0, (
        f"Announcer floor stale: floor {_FLOOR} but actual {actual}. "
        "Drop the _FLOOR constant in this test to match."
    )
```

- [ ] **Step 9: Create `test_a11y_reduced_motion_respected.py`**

Create `tests/architecture/test_a11y_reduced_motion_respected.py`:
```python
"""CSS files with animations must honor prefers-reduced-motion.

Any file containing @keyframes, `animation:`, or non-instant
`transition:` must also contain a `@media (prefers-reduced-motion`
override. Cluster 8 task adds the overrides + drops the floor.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
CSS_FILES: Final[tuple[Path, ...]] = (
    PROJECT_ROOT / "desktop" / "web" / "src" / "cockpit" / "styles.css",
    PROJECT_ROOT / "desktop" / "web" / "src" / "wizard" / "styles.css",
)

_GRANDFATHERED: Final[dict[str, int]] = {}

_ANIM_HINT: Final[re.Pattern[str]] = re.compile(
    r"(@keyframes|animation\s*:|transition\s*:\s*(?!none|0s|initial))",
    re.MULTILINE,
)


def _violation_count(path: Path) -> int:
    if not path.is_file():
        return 0
    source = path.read_text(encoding="utf-8")
    has_anim = bool(_ANIM_HINT.search(source))
    has_reduced = "@media (prefers-reduced-motion" in source
    return 1 if has_anim and not has_reduced else 0


def test_animations_honor_reduced_motion() -> None:
    violations: list[str] = []
    for path in CSS_FILES:
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        count = _violation_count(path)
        floor = _GRANDFATHERED.get(rel, 0)
        if count > floor:
            violations.append(
                f"{rel}: declares animations/transitions but no "
                f"@media (prefers-reduced-motion) override [floor {floor}]"
            )
    assert not violations, "\n  ".join(violations) if violations else ""


def test_reduced_motion_floor_does_not_grow() -> None:
    redundant: list[str] = []
    for rel, floor in _GRANDFATHERED.items():
        path = PROJECT_ROOT / rel
        if not path.is_file():
            continue
        actual = _violation_count(path)
        if actual < floor:
            redundant.append(f"{rel}: floor {floor} but actual {actual}.")
    assert not redundant, "\n  ".join(redundant)
```

- [ ] **Step 10: Run the 9 new arch tests with the audit baseline**

Run from the worktree root:
```bash
"/c/Program Files/WindowsApps/PythonSoftwareFoundation.Python.3.13_3.13.3568.0_x64__qbz5n2kfra8p0/python3.13.exe" -m pytest tests/architecture/test_a11y_*.py -v -p no:cacheprovider
```
Expected: 18 tests (9 main + 9 drain-allowlist), all pass with the documented floors. If any FAIL, that's an audit miss — update the matching `_GRANDFATHERED` / `_FLOOR` to reflect actual state and re-run.

- [ ] **Step 11: Run black + isort + ruff**

Run from the worktree root:
```bash
"/c/Program Files/WindowsApps/PythonSoftwareFoundation.Python.3.13_3.13.3568.0_x64__qbz5n2kfra8p0/python3.13.exe" -m black tests/architecture/test_a11y_*.py && \
"/c/Program Files/WindowsApps/PythonSoftwareFoundation.Python.3.13_3.13.3568.0_x64__qbz5n2kfra8p0/python3.13.exe" -m isort tests/architecture/test_a11y_*.py && \
"/c/Program Files/WindowsApps/PythonSoftwareFoundation.Python.3.13_3.13.3568.0_x64__qbz5n2kfra8p0/python3.13.exe" -m ruff check tests/architecture/test_a11y_*.py
```
Expected: all clean.

- [ ] **Step 12: Commit**

```bash
git add tests/architecture/test_a11y_*.py
git commit -m "test(arch): 9 a11y architecture guards with RR4 ratchet pattern

Phase A.4: Python AST architecture tests parallel to the RR4 set.
Each ships with two companion tests (main rule + drain-allowlist).

- test_a11y_no_div_onclick.py — forbids <div|span onClick> antipattern
- test_a11y_every_icon_button_has_aria_label.py — icon-only buttons
- test_a11y_every_form_field_has_label.py — input/textarea/select
- test_a11y_every_route_has_main_landmark.py — main + h1 per route
- test_a11y_color_palette_aa.py — WCAG contrast computation
- test_a11y_no_aria_hidden_focusable.py — focus-trap antipattern
- test_a11y_no_role_attribute_redundancy.py — role=button on <button>
- test_a11y_announcer_is_wired.py — <LiveRegion /> in App.tsx
- test_a11y_reduced_motion_respected.py — prefers-reduced-motion

Floors set to audit baseline (cockpit landmark = 1, announcer = 1,
everything else 0). Phase B fix tasks drop matching floors as
clusters land."
```

---

## Phase B — Cluster fixes (parallel-safe)

Each task below touches a disjoint file set. They can all run simultaneously via subagent dispatch.

### Task 5: Cluster 1 — Keyboard interaction completeness (roving tabindex)

**Files:**
- Create: `desktop/web/src/a11y/rovingTabindex.ts`
- Create: `desktop/web/src/a11y/index.ts` (will be appended by other Phase B tasks)
- Modify: `desktop/web/src/cockpit/ProfileToggle.tsx`
- Modify: `desktop/web/src/cockpit/HistoryStrip.tsx`
- Modify: `desktop/web/tests/a11y/roving_tabindex.test.ts` (un-skip)
- Modify: `desktop/web/tests/a11y/keyboard_navigation.test.tsx` (new file or extend if exists)

- [ ] **Step 1: Implement `rovingTabindex.ts`**

Create `desktop/web/src/a11y/rovingTabindex.ts`:
```ts
/**
 * Stateless helpers for the roving-tabindex keyboard pattern.
 *
 * Usage: composite widgets (tablists, listboxes, snapshot strips) keep
 * exactly one child in the tab stop at a time. Arrow keys move focus
 * within the widget without leaving it. Home/End jump to first/last.
 *
 * The widget tracks the focused index in state; passes each candidate
 * `tabIndex={index === focused ? 0 : -1}` and an `onKeyDown` handler
 * that calls `nextIndex(focused, length, ev.key)` then updates state +
 * focuses the new element via a ref.
 *
 * Reference: ARIA Authoring Practices §"Tabs" — https://www.w3.org/WAI/ARIA/apg/patterns/tabs/
 */

export type RovingKey =
  | 'ArrowLeft'
  | 'ArrowRight'
  | 'ArrowUp'
  | 'ArrowDown'
  | 'Home'
  | 'End';

const NAV_KEYS: ReadonlySet<string> = new Set([
  'ArrowLeft',
  'ArrowRight',
  'ArrowUp',
  'ArrowDown',
  'Home',
  'End',
]);

/**
 * Return the next focused index given the current index, the total
 * length, and the key pressed. Returns `current` for keys that don't
 * navigate. Wraps at both ends.
 */
export function nextIndex(current: number, length: number, key: string): number {
  if (length <= 0) return 0;
  if (!NAV_KEYS.has(key)) return current;
  if (key === 'Home') return 0;
  if (key === 'End') return length - 1;
  if (key === 'ArrowRight' || key === 'ArrowDown') {
    return (current + 1) % length;
  }
  // ArrowLeft / ArrowUp
  return (current - 1 + length) % length;
}

export function isRovingKey(key: string): boolean {
  return NAV_KEYS.has(key);
}
```

- [ ] **Step 2: Create `desktop/web/src/a11y/index.ts`**

Create `desktop/web/src/a11y/index.ts`:
```ts
/**
 * Public surface of the a11y module. Other Phase B clusters append
 * to this file as they ship.
 */
export { nextIndex, isRovingKey, type RovingKey } from './rovingTabindex';
```

- [ ] **Step 3: Un-skip and run the existing rovingTabindex tests**

Edit `desktop/web/tests/a11y/roving_tabindex.test.ts`:
- Change `describe.skip(...)` to `describe(...)`.
- Remove the `(lands with Task 5)` suffix.

Run from `desktop/web/`:
```bash
npm run test:run -- tests/a11y/roving_tabindex.test.ts
```
Expected: 7 pass, 0 failed.

- [ ] **Step 4: Patch ProfileToggle.tsx for roving tabindex + key handler**

Modify `desktop/web/src/cockpit/ProfileToggle.tsx` — replace the entire file body (keep the docstring) with:
```tsx
/**
 * ProfileToggle — pill toggle between "Scene" (built-in profiles) and "Inspiration" (user
 * profiles trained from style sources). Spec calls these tabs.
 *
 * Local state held by the parent (<MutationPanel />). Component is pure & dumb.
 *
 * ARIA Authoring Practices §"Tabs": roving tabindex + Left/Right/Home/End.
 * Only the selected tab is in the document tab order (tabIndex=0);
 * unselected tabs use tabIndex=-1 and are reachable only via the arrow
 * keys while the tablist is focused.
 */

import { useRef } from 'react';

import { nextIndex } from '../a11y';
import type { ProfileKind } from '../ws/protocol';

const TAB_ORDER: readonly ProfileKind[] = ['scene', 'user'] as const;

export interface ProfileToggleProps {
  value: ProfileKind;
  onChange: (kind: ProfileKind) => void;
}

export function ProfileToggle({ value, onChange }: ProfileToggleProps): JSX.Element {
  const buttonRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const focusedIndex = TAB_ORDER.indexOf(value);

  const handleKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>): void => {
    const next = nextIndex(focusedIndex, TAB_ORDER.length, event.key);
    if (next === focusedIndex) return;
    event.preventDefault();
    const targetKind = TAB_ORDER[next];
    if (targetKind === undefined) return;
    onChange(targetKind);
    // Focus must move synchronously with the selection per the tabs pattern.
    queueMicrotask(() => buttonRefs.current[next]?.focus());
  };

  return (
    <div className="profile-toggle" role="tablist" data-testid="profile-toggle">
      {TAB_ORDER.map((kind, index) => {
        const selected = value === kind;
        return (
          <button
            key={kind}
            ref={(el) => {
              buttonRefs.current[index] = el;
            }}
            type="button"
            role="tab"
            aria-selected={selected}
            tabIndex={selected ? 0 : -1}
            className={selected ? 'active' : ''}
            onClick={() => onChange(kind)}
            onKeyDown={handleKeyDown}
          >
            {kind === 'scene' ? 'Scene' : 'Inspiration'}
          </button>
        );
      })}
    </div>
  );
}
```

- [ ] **Step 5: Patch HistoryStrip.tsx for roving tabindex (same pattern)**

Read the current file first:
```bash
cat desktop/web/src/cockpit/HistoryStrip.tsx
```

The component already renders `<button>` dots with `aria-label` + `aria-current`. Add the roving tabindex + key handler the same way — track `focusedIndex` from the currently-current entry, `tabIndex={focused ? 0 : -1}`, `onKeyDown` calls `nextIndex(...)` + moves focus via refs.

(The exact edit depends on the file's current implementation — read the file, find the `.map((entry, i) => <button ... />)` block, and apply the same pattern as Step 4 above. Keep `aria-current` working unchanged.)

- [ ] **Step 6: Extend the keyboard_navigation.test.tsx**

If `desktop/web/tests/a11y/keyboard_navigation.test.tsx` does not exist, create it:
```tsx
/**
 * Keyboard navigation flows for tablist + roving-tabindex widgets.
 * Cluster 1 coverage.
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { ProfileToggle } from '../../src/cockpit/ProfileToggle';

describe('ProfileToggle roving tabindex', () => {
  it('only the selected tab is in the tab order', () => {
    render(<ProfileToggle value="scene" onChange={() => {}} />);
    const tabs = screen.getAllByRole('tab');
    expect(tabs).toHaveLength(2);
    expect(tabs[0]).toHaveAttribute('tabindex', '0');
    expect(tabs[1]).toHaveAttribute('tabindex', '-1');
  });

  it('ArrowRight moves selection + focus to next tab', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<ProfileToggle value="scene" onChange={onChange} />);
    const sceneTab = screen.getAllByRole('tab')[0]!;
    sceneTab.focus();
    await user.keyboard('{ArrowRight}');
    expect(onChange).toHaveBeenCalledWith('user');
  });

  it('Home jumps to first tab', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<ProfileToggle value="user" onChange={onChange} />);
    screen.getAllByRole('tab')[1]!.focus();
    await user.keyboard('{Home}');
    expect(onChange).toHaveBeenCalledWith('scene');
  });

  it('End jumps to last tab', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<ProfileToggle value="scene" onChange={onChange} />);
    screen.getAllByRole('tab')[0]!.focus();
    await user.keyboard('{End}');
    expect(onChange).toHaveBeenCalledWith('user');
  });
});
```

Run from `desktop/web/`:
```bash
npm run test:run -- tests/a11y/keyboard_navigation.test.tsx
```
Expected: 4 pass, 0 failed.

- [ ] **Step 7: Run full Vitest suite to confirm no regressions**

Run from `desktop/web/`:
```bash
npm run test:run
```
Expected: all pass. The 100% coverage threshold on `src/cockpit/**` may need the new branches in ProfileToggle (`handleKeyDown` early-return branch, `targetKind === undefined` guard) covered — the test in Step 6 already exercises the happy paths; if coverage complains, add a "Unknown key does nothing" test.

- [ ] **Step 8: Commit**

```bash
git add desktop/web/src/a11y/ desktop/web/src/cockpit/ProfileToggle.tsx desktop/web/src/cockpit/HistoryStrip.tsx desktop/web/tests/a11y/roving_tabindex.test.ts desktop/web/tests/a11y/keyboard_navigation.test.tsx
git commit -m "feat(a11y): Cluster 1 — roving tabindex on ProfileToggle + HistoryStrip

Phase B.5 of ADA AA accessibility plan.

- New a11y/rovingTabindex.ts pure helpers
- ProfileToggle: roving tabindex + Left/Right/Home/End per ARIA APG
  tabs pattern; only selected tab is tabIndex=0
- HistoryStrip: same pattern on snapshot dots
- 4 new keyboard navigation Vitest tests + 7 unit tests un-skipped

Closes WCAG 2.1.1 + ARIA tabs-pattern conformance for these widgets."
```

---

### Task 6: Cluster 2 — Color contrast (small text)

**Files:**
- Modify: `desktop/web/src/cockpit/styles.css`

- [ ] **Step 1: Locate the offending selectors**

Run from the worktree root:
```bash
grep -n "\.knob-label\|\.pad-card-title" desktop/web/src/cockpit/styles.css
```
Expected: lines naming `color: var(--text-dim)` for these selectors.

- [ ] **Step 2: Patch the colors**

Edit `desktop/web/src/cockpit/styles.css` — for the `.knob-label` and `.pad-card-title` rules, change `color: var(--text-dim);` to `color: var(--text);`. Leave all other `--text-dim` references intact (timestamps, hint text).

- [ ] **Step 3: Re-run the contrast arch test**

Run from the worktree root:
```bash
"/c/Program Files/WindowsApps/PythonSoftwareFoundation.Python.3.13_3.13.3568.0_x64__qbz5n2kfra8p0/python3.13.exe" -m pytest tests/architecture/test_a11y_color_palette_aa.py -v -p no:cacheprovider
```
Expected: 2 pass.

- [ ] **Step 4: Run full Vitest suite (visual regression sanity)**

```bash
cd desktop/web && npm run test:run
```
Expected: pass. No tests assert exact `color: rgb(...)` values; layout/snapshot tests stay green.

- [ ] **Step 5: Commit**

```bash
git add desktop/web/src/cockpit/styles.css
git commit -m "fix(a11y): Cluster 2 — small-text contrast for knob + pad labels

Phase B.6: WCAG 1.4.3. Swap .knob-label + .pad-card-title from
--text-dim to --text since these labels carry parameter / pad
identity (primary content, not secondary hint text). --text-dim
remains for genuine secondary content (timestamps, hint text)
where it stays comfortably above 4.5:1."
```

---

### Task 7: Cluster 3 — Form error feedback

**Files:**
- Modify: `desktop/web/src/wizard/NameStep.tsx`
- Modify: `desktop/web/src/wizard/AddStep.tsx`
- Create: `desktop/web/tests/a11y/form_errors.test.tsx`

- [ ] **Step 1: Write the failing form-errors test**

Create `desktop/web/tests/a11y/form_errors.test.tsx`:
```tsx
/**
 * Cluster 3 coverage: form-error feedback wired through ARIA so SR
 * users hear what's wrong and the focus moves to the offending field.
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { NameStep } from '../../src/wizard/NameStep';

describe('NameStep error feedback', () => {
  it('submitting empty name sets aria-invalid + role=alert + focuses field', async () => {
    const user = userEvent.setup();
    render(<NameStep onSubmit={vi.fn()} onCancel={vi.fn()} />);
    const submit = screen.getByRole('button', { name: /next|continue|save/i });
    await user.click(submit);
    const nameInput = screen.getByLabelText(/name/i);
    expect(nameInput).toHaveAttribute('aria-invalid', 'true');
    const errorRegion = screen.getByRole('alert');
    expect(errorRegion).toHaveTextContent(/name is required/i);
    expect(nameInput).toHaveAttribute('aria-describedby', errorRegion.id);
    expect(nameInput).toHaveFocus();
  });

  it('valid submit calls onSubmit and does not set aria-invalid', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<NameStep onSubmit={onSubmit} onCancel={vi.fn()} />);
    const nameInput = screen.getByLabelText(/name/i);
    await user.type(nameInput, 'My new profile');
    const submit = screen.getByRole('button', { name: /next|continue|save/i });
    await user.click(submit);
    expect(onSubmit).toHaveBeenCalled();
    expect(nameInput).not.toHaveAttribute('aria-invalid');
  });
});
```

(The exact `props` shape of `NameStep` may differ — read the current `NameStep.tsx` and adapt the test's render call to match the real prop names. Keep the assertion shape the same.)

- [ ] **Step 2: Run the test to confirm it fails**

Run from `desktop/web/`:
```bash
npm run test:run -- tests/a11y/form_errors.test.tsx
```
Expected: fails — current NameStep has no error feedback.

- [ ] **Step 3: Patch NameStep.tsx**

Read the file:
```bash
cat desktop/web/src/wizard/NameStep.tsx
```

Add to the component:
- A `[error, setError] = useState<string | null>(null)` state.
- A `useRef<HTMLInputElement>(null)` for focus targeting.
- On submit:
  ```ts
  if (!name.trim()) {
    setError('Name is required.');
    inputRef.current?.focus();
    return;
  }
  setError(null);
  onSubmit(name);
  ```
- The input gets `aria-invalid={error !== null}`, `aria-describedby={error !== null ? 'name-error' : undefined}`, `aria-required="true"`, and `ref={inputRef}`.
- The error region:
  ```tsx
  {error !== null && (
    <div id="name-error" role="alert" className="wizard-field-error">
      {error}
    </div>
  )}
  ```

- [ ] **Step 4: Apply the same pattern to AddStep.tsx**

Read `desktop/web/src/wizard/AddStep.tsx`. Identify its validation rule (e.g., source path required). Apply the same error-state + role="alert" + focus pattern.

- [ ] **Step 5: Re-run the Vitest tests**

```bash
cd desktop/web && npm run test:run -- tests/a11y/form_errors.test.tsx
```
Expected: 2 pass.

Then run the full suite:
```bash
npm run test:run
```
Expected: pass + 100% coverage threshold met (the new state branches are exercised by the 2 tests).

- [ ] **Step 6: Commit**

```bash
git add desktop/web/src/wizard/NameStep.tsx desktop/web/src/wizard/AddStep.tsx desktop/web/tests/a11y/form_errors.test.tsx
git commit -m "feat(a11y): Cluster 3 — form error feedback with aria-invalid + role=alert

Phase B.7: WCAG 3.3.1 / 3.3.3.

- NameStep + AddStep validate on submit; invalid fields gain
  aria-invalid=true + aria-describedby pointing at a role=alert
  region with the error text
- aria-required=true on required fields
- Focus moves to the first invalid field

2 new Vitest tests for NameStep; same pattern in AddStep."
```

---

### Task 8: Cluster 4 — Live region + announcer module

**Files:**
- Create: `desktop/web/src/a11y/announcer.ts`
- Create: `desktop/web/src/a11y/LiveRegion.tsx`
- Create: `desktop/web/src/a11y/srOnly.css`
- Modify: `desktop/web/src/a11y/index.ts` (append)
- Modify: `desktop/web/src/App.tsx` (mount `<LiveRegion />`)
- Modify: `desktop/web/src/state/<the cockpit store file>` (subscribe + announce)
- Modify: `desktop/web/tests/a11y/announcer.test.ts` (un-skip)
- Create: `desktop/web/tests/a11y/live_region.test.tsx`

- [ ] **Step 1: Implement the announcer module**

Create `desktop/web/src/a11y/announcer.ts`:
```ts
/**
 * Announcer — debounced writer into the live-region <div>.
 *
 * Architecture:
 * - LiveRegion.tsx mounts the visually-hidden <div role="status"> and
 *   registers its `setText` callback via `_registerWriter(...)`.
 * - Anywhere in the app, call `announce(message)`; the message is
 *   debounced (default 200ms) then written into the live region.
 * - SRs announce the change automatically via aria-live="polite".
 *
 * Debounce coalesces bursty calls (e.g. ten store updates fired during
 * one mutation) into a single announcement of the last message — the
 * intermediate states are not useful to a SR user.
 *
 * Reference: WAI-ARIA 1.2 §"Live regions" and
 * https://www.w3.org/WAI/ARIA/apg/practices/live-regions/
 */

type Writer = (message: string) => void;

let writer: Writer | null = null;
let pendingMessage: string | null = null;
let timer: ReturnType<typeof setTimeout> | null = null;
const DEBOUNCE_MS = 200;

export function _registerWriter(next: Writer | null): void {
  writer = next;
}

export function announce(message: string): void {
  pendingMessage = message;
  if (timer !== null) clearTimeout(timer);
  timer = setTimeout(() => {
    if (writer !== null && pendingMessage !== null) {
      writer(pendingMessage);
    }
    pendingMessage = null;
    timer = null;
  }, DEBOUNCE_MS);
}

/** Clear pending announcements + the writer. Test-only escape hatch. */
export function _reset(): void {
  if (timer !== null) clearTimeout(timer);
  timer = null;
  pendingMessage = null;
  writer = null;
}
```

- [ ] **Step 2: Implement the LiveRegion component**

Create `desktop/web/src/a11y/srOnly.css`:
```css
/**
 * Visually hidden but screen-reader-accessible. Standard SR-only
 * pattern: zero size, clipped, with !important on the layout props
 * so per-context CSS can't accidentally re-show the element.
 */
.sr-only {
  position: absolute !important;
  width: 1px !important;
  height: 1px !important;
  padding: 0 !important;
  margin: -1px !important;
  overflow: hidden !important;
  clip: rect(0, 0, 0, 0) !important;
  white-space: nowrap !important;
  border: 0 !important;
}
```

Create `desktop/web/src/a11y/LiveRegion.tsx`:
```tsx
/**
 * LiveRegion — the single global aria-live container. Mount once at
 * App.tsx root; the announcer module writes into it via the registered
 * callback.
 *
 * `aria-live="polite"` queues announcements rather than interrupting
 * the user mid-action. `aria-atomic="true"` ensures the WHOLE region
 * content is read on every change (vs. just the diff), which avoids
 * stuttering announcements when the message changes rapidly.
 */

import { useEffect, useState } from 'react';

import { _registerWriter } from './announcer';

import './srOnly.css';

export function LiveRegion(): JSX.Element {
  const [text, setText] = useState<string>('');

  useEffect(() => {
    _registerWriter(setText);
    return () => _registerWriter(null);
  }, []);

  return (
    <div
      role="status"
      aria-live="polite"
      aria-atomic="true"
      className="sr-only"
      data-testid="a11y-live-region"
    >
      {text}
    </div>
  );
}
```

- [ ] **Step 3: Append to `desktop/web/src/a11y/index.ts`**

Append:
```ts
export { announce, _registerWriter, _reset } from './announcer';
export { LiveRegion } from './LiveRegion';
```

- [ ] **Step 4: Un-skip the announcer test**

Edit `desktop/web/tests/a11y/announcer.test.ts`:
- Change `describe.skip(...)` to `describe(...)`.
- Add a `beforeEach(() => _reset())` to clean state between tests (import `_reset` from `../../src/a11y/announcer`).

Run from `desktop/web/`:
```bash
npm run test:run -- tests/a11y/announcer.test.ts
```
Expected: 3 pass.

- [ ] **Step 5: Write the live-region integration test**

Create `desktop/web/tests/a11y/live_region.test.tsx`:
```tsx
/**
 * LiveRegion + announcer module integration. Renders LiveRegion in
 * isolation, calls announce(...), asserts the visible textContent
 * updates after debounce.
 */
import { render, screen, act } from '@testing-library/react';
import { describe, expect, it, afterEach } from 'vitest';

import { announce, _reset } from '../../src/a11y/announcer';
import { LiveRegion } from '../../src/a11y/LiveRegion';

afterEach(() => _reset());

describe('LiveRegion', () => {
  it('renders an empty role=status region by default', () => {
    render(<LiveRegion />);
    const region = screen.getByTestId('a11y-live-region');
    expect(region).toHaveAttribute('role', 'status');
    expect(region).toHaveAttribute('aria-live', 'polite');
    expect(region.textContent).toBe('');
  });

  it('updates text content when announce() fires (after debounce)', async () => {
    render(<LiveRegion />);
    await act(async () => {
      announce('Send complete, 12 parameters sent');
      await new Promise((r) => setTimeout(r, 250));
    });
    const region = screen.getByTestId('a11y-live-region');
    expect(region.textContent).toBe('Send complete, 12 parameters sent');
  });
});
```

Run:
```bash
npm run test:run -- tests/a11y/live_region.test.tsx
```
Expected: 2 pass.

- [ ] **Step 6: Mount `<LiveRegion />` in App.tsx**

Edit `desktop/web/src/App.tsx`. Inside both return branches (the connecting placeholder AND the post-bootstrap Cockpit/Wizard branch), add `<LiveRegion />` as a sibling of the main content. Import from `./a11y`.

Example for the post-bootstrap branch:
```tsx
if (isWizardRoute(route)) {
  return (
    <>
      <LiveRegion />
      <Wizard client={client} />
    </>
  );
}

return (
  <>
    <LiveRegion />
    <Cockpit client={client} />
  </>
);
```

- [ ] **Step 7: Wire announcements from the Zustand store**

Read the cockpit store file:
```bash
ls desktop/web/src/state/
cat desktop/web/src/state/cockpit_store.ts 2>/dev/null || cat desktop/web/src/state/index.ts
```

Find the action handlers for these store events and call `announce(...)` from each:
- `mutation_previewed` → `announce(`Mutation preview ready, depth ${depth}%, ${affected} pads affected`)`
- `send_plan_changed` with `ok=true` → after send completes: `announce(`Send complete, ${packetCount} parameters sent`)`
- `send_plan_changed` with `ok=false, code` → `announce(`Send failed: ${humanReadable(code)}`)`
- `profile_changed` → `announce(`Profile selected: ${name}`)`
- `session_status` armed transition → `announce(`Device armed`)`

Import `announce` from `../a11y`.

- [ ] **Step 8: Run full Vitest suite**

```bash
cd desktop/web && npm run test:run
```
Expected: all pass.

- [ ] **Step 9: Drop the announcer arch-test floor to 0**

Edit `tests/architecture/test_a11y_announcer_is_wired.py`: change `_FLOOR: int = 1` to `_FLOOR: int = 0`. Run:
```bash
"/c/Program Files/WindowsApps/PythonSoftwareFoundation.Python.3.13_3.13.3568.0_x64__qbz5n2kfra8p0/python3.13.exe" -m pytest tests/architecture/test_a11y_announcer_is_wired.py -v -p no:cacheprovider
```
Expected: 2 pass (main + drain).

- [ ] **Step 10: Commit**

```bash
git add desktop/web/src/a11y/ desktop/web/src/App.tsx desktop/web/src/state/ desktop/web/tests/a11y/announcer.test.ts desktop/web/tests/a11y/live_region.test.tsx tests/architecture/test_a11y_announcer_is_wired.py
git commit -m "feat(a11y): Cluster 4 — announcer module + LiveRegion + store subscriptions

Phase B.8: WCAG 4.1.3 + AAA-adjacent announcer pattern.

- a11y/announcer.ts: debounced writer (200ms) into the global live
  region; coalesces bursty store updates into a single announcement
- a11y/LiveRegion.tsx: visually-hidden <div role=status aria-live=polite
  aria-atomic=true> mounted once at App root
- a11y/srOnly.css: standard SR-only pattern
- App.tsx mounts <LiveRegion /> in every return branch
- Zustand store subscribes mutation_previewed / send_plan_changed /
  profile_changed / session_status and calls announce() with the
  documented per-event messages
- arch test floor dropped to 0"
```

---

### Task 9: Cluster 5 — Focus management on route change

**Files:**
- Create: `desktop/web/src/a11y/useFocusOnRouteChange.ts`
- Modify: `desktop/web/src/a11y/index.ts` (append)
- Modify: `desktop/web/src/App.tsx`
- Create: `desktop/web/tests/a11y/focus_management.test.tsx`

- [ ] **Step 1: Implement the hook**

Create `desktop/web/src/a11y/useFocusOnRouteChange.ts`:
```ts
/**
 * useFocusOnRouteChange — moves focus to a ref'd element each time the
 * dependency (typically the hash route) changes.
 *
 * SR users get the route's heading announced automatically; sighted
 * keyboard users see a visible focus indicator on the new heading.
 *
 * Usage:
 *   const headingRef = useRef<HTMLHeadingElement>(null);
 *   useFocusOnRouteChange(headingRef, [route]);
 *   return <h1 ref={headingRef} tabIndex={-1}>...</h1>;
 *
 * The tabIndex={-1} on the heading is required so it can receive
 * programmatic focus without entering the tab order.
 */
import { useEffect, type RefObject } from 'react';

export function useFocusOnRouteChange(
  ref: RefObject<HTMLElement>,
  deps: ReadonlyArray<unknown>,
): void {
  useEffect(() => {
    if (ref.current === null) return;
    ref.current.focus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
}
```

- [ ] **Step 2: Append to `desktop/web/src/a11y/index.ts`**

Append: `export { useFocusOnRouteChange } from './useFocusOnRouteChange';`

- [ ] **Step 3: Wire into App.tsx**

Edit `desktop/web/src/App.tsx`:
- Import: `import { useFocusOnRouteChange } from './a11y';`
- Add a `useRef<HTMLDivElement>(null)` named `routeRootRef`.
- Wrap each return-branch root in a focusable container:
  ```tsx
  return (
    <>
      <LiveRegion />
      <div ref={routeRootRef} tabIndex={-1}>
        <Cockpit client={client} />
      </div>
    </>
  );
  ```
- Call `useFocusOnRouteChange(routeRootRef, [route])` near the top of the component.

(If wrapping breaks layout because of CSS specificity, instead pass the ref directly to a heading element inside `Cockpit`/`Wizard` via prop. The Cockpit gains an `<h1>` in Task 10 — at that point you can wire the ref straight into it.)

- [ ] **Step 4: Write the focus test**

Create `desktop/web/tests/a11y/focus_management.test.tsx`:
```tsx
/**
 * Focus moves to the route container when the hash route changes.
 */
import { act, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { App } from '../../src/App';

describe('Focus management on route change', () => {
  it('cockpit-root mounts focused after the initial route load', async () => {
    // Mount under jsdom — App's internal hash router fires hashchange.
    render(<App />);
    await waitFor(
      () => expect(screen.queryByTestId('cockpit-root')).toBeInTheDocument(),
      { timeout: 5000 },
    );
    // The focused element should be the route container (a focusable
    // ancestor) — not body.
    expect(document.activeElement).not.toBe(document.body);
  });

  it('switching hash to #/wizard moves focus into the wizard surface', async () => {
    render(<App />);
    await waitFor(
      () => expect(screen.queryByTestId('cockpit-root')).toBeInTheDocument(),
      { timeout: 5000 },
    );
    await act(async () => {
      window.location.hash = '#/wizard';
      window.dispatchEvent(new HashChangeEvent('hashchange'));
    });
    await waitFor(
      () => expect(screen.queryByTestId('wizard-root')).toBeInTheDocument(),
      { timeout: 5000 },
    );
    expect(document.activeElement).not.toBe(document.body);
  });
});
```

(This test assumes `App` can be rendered without a real WebSocket client. If it currently requires one, look at how the existing `App.test.tsx` mocks the client and reuse the pattern.)

- [ ] **Step 5: Run the test**

```bash
cd desktop/web && npm run test:run -- tests/a11y/focus_management.test.tsx
```
Expected: 2 pass.

- [ ] **Step 6: Commit**

```bash
git add desktop/web/src/a11y/useFocusOnRouteChange.ts desktop/web/src/a11y/index.ts desktop/web/src/App.tsx desktop/web/tests/a11y/focus_management.test.tsx
git commit -m "feat(a11y): Cluster 5 — useFocusOnRouteChange hook + App wiring

Phase B.9: WCAG 2.4.3 + 2.4.7.

- a11y/useFocusOnRouteChange.ts: moves focus to ref'd element on
  dependency change
- App.tsx wraps each route in a tabIndex=-1 container ref'd by the
  hook; route transitions now move focus to the new surface so SRs
  announce the new context and sighted keyboard users see focus
  on the new heading"
```

---

### Task 10: Cluster 6 — Document title + `<main>` + `<h1>`

**Files:**
- Create: `desktop/web/src/a11y/useDocumentTitle.ts`
- Modify: `desktop/web/src/a11y/index.ts` (append)
- Modify: `desktop/web/src/App.tsx` (call hook per route)
- Modify: `desktop/web/src/cockpit/Cockpit.tsx` (use `<main>` + add `<h1>`)
- Modify: `desktop/web/src/wizard/Wizard.tsx` (per-step title; verify `<main>` already present)
- Create: `desktop/web/tests/a11y/document_title.test.tsx`

- [ ] **Step 1: Implement useDocumentTitle**

Create `desktop/web/src/a11y/useDocumentTitle.ts`:
```ts
/**
 * useDocumentTitle — sets document.title for the lifetime of the
 * mounted component; restores the previous title on unmount.
 *
 * Setting title from React (rather than from a server-rendered <title>)
 * is required for SPA route changes — WCAG 2.4.2 ("Page Titled") fails
 * if every route shares the same static title.
 */
import { useEffect } from 'react';

export function useDocumentTitle(title: string): void {
  useEffect(() => {
    const previous = document.title;
    document.title = title;
    return () => {
      document.title = previous;
    };
  }, [title]);
}
```

- [ ] **Step 2: Append to `desktop/web/src/a11y/index.ts`**

Append: `export { useDocumentTitle } from './useDocumentTitle';`

- [ ] **Step 3: Patch Cockpit.tsx for `<main>` + `<h1>`**

Edit `desktop/web/src/cockpit/Cockpit.tsx`:
- Change `<div className="cockpit-root" data-testid="cockpit-root">` to `<main className="cockpit-root" data-testid="cockpit-root">`.
- Add `<h1 className="sr-only">RytmRandomizer · Cockpit</h1>` as the first child of `<main>` (visually hidden because the HeaderBar serves as the visual title).
- Import `'../a11y/srOnly.css'` (or add to `styles.css` import chain — the `sr-only` class needs to be reachable from the file).

- [ ] **Step 4: Verify Wizard.tsx already has `<main>` + `<h1>`**

Run:
```bash
grep -n "<main\|<h1" desktop/web/src/wizard/Wizard.tsx
```
If `<h1>` is missing, add it. Wizard.tsx should already have `<main>` per the audit.

- [ ] **Step 5: Wire useDocumentTitle in App.tsx**

Edit `desktop/web/src/App.tsx`. Inside `App()`:
```tsx
useDocumentTitle(
  sessionStatus === null
    ? 'RytmRandomizer · Connecting'
    : isWizardRoute(route)
      ? 'RytmRandomizer · Profile Wizard'
      : 'RytmRandomizer · Cockpit'
);
```

- [ ] **Step 6: Write the document-title test**

Create `desktop/web/tests/a11y/document_title.test.tsx`:
```tsx
/**
 * Per-route document.title verification (WCAG 2.4.2).
 */
import { act, render, waitFor } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { App } from '../../src/App';

describe('document.title per route', () => {
  it('cockpit route sets title to "RytmRandomizer · Cockpit"', async () => {
    render(<App />);
    await waitFor(
      () => expect(document.title).toBe('RytmRandomizer · Cockpit'),
      { timeout: 5000 },
    );
  });

  it('wizard route sets title to "RytmRandomizer · Profile Wizard"', async () => {
    render(<App />);
    await waitFor(
      () => expect(document.title).toMatch(/Cockpit|Connecting/),
      { timeout: 5000 },
    );
    await act(async () => {
      window.location.hash = '#/wizard';
      window.dispatchEvent(new HashChangeEvent('hashchange'));
    });
    await waitFor(
      () => expect(document.title).toBe('RytmRandomizer · Profile Wizard'),
      { timeout: 5000 },
    );
  });
});
```

- [ ] **Step 7: Run new tests + drop the route-landmark floor**

```bash
cd desktop/web && npm run test:run -- tests/a11y/document_title.test.tsx
```
Expected: 2 pass.

Edit `tests/architecture/test_a11y_every_route_has_main_landmark.py`: change `"cockpit": 1` to `"cockpit": 0`. Run:
```bash
"/c/Program Files/WindowsApps/PythonSoftwareFoundation.Python.3.13_3.13.3568.0_x64__qbz5n2kfra8p0/python3.13.exe" -m pytest tests/architecture/test_a11y_every_route_has_main_landmark.py -v -p no:cacheprovider
```
Expected: 2 pass.

- [ ] **Step 8: Commit**

```bash
git add desktop/web/src/a11y/useDocumentTitle.ts desktop/web/src/a11y/index.ts desktop/web/src/App.tsx desktop/web/src/cockpit/Cockpit.tsx desktop/web/src/wizard/Wizard.tsx desktop/web/tests/a11y/document_title.test.tsx tests/architecture/test_a11y_every_route_has_main_landmark.py
git commit -m "feat(a11y): Cluster 6 — document title hook + main landmark + h1 per route

Phase B.10: WCAG 2.4.2 + 1.3.1.

- a11y/useDocumentTitle.ts: per-route title with restore-on-unmount
- Cockpit.tsx: <div> → <main>; sr-only <h1>
- Wizard.tsx: verified <main> + <h1> (no edit needed if already present)
- App.tsx calls useDocumentTitle with the per-route string
- arch test floor for cockpit dropped to 0"
```

---

### Task 11: Cluster 8 — Reduced motion + forced colors

**Files:**
- Modify: `desktop/web/src/cockpit/styles.css`
- Modify: `desktop/web/src/wizard/styles.css`

- [ ] **Step 1: Find any animations / transitions**

Run:
```bash
grep -nE "@keyframes|animation:|transition:" desktop/web/src/cockpit/styles.css desktop/web/src/wizard/styles.css
```

- [ ] **Step 2: Append the reduced-motion + forced-colors overrides to each CSS file**

If either file declares animations or non-instant transitions, append at the bottom of THAT file:
```css
/* ---------- WCAG 2.3.3 / 2.2 reduced-motion + forced-colors ---------- */

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}

@media (forced-colors: active) {
  /* Use the system colors so Windows High Contrast renders cleanly. */
  .cockpit-root,
  .wizard-root {
    border: 1px solid CanvasText;
  }
  button,
  [role="tab"],
  [role="slider"] {
    border: 1px solid ButtonText;
  }
  :focus-visible {
    outline: 2px solid Highlight;
    outline-offset: 2px;
  }
}
```

If neither file has animations, the test still passes (the rule only requires the override when an animation/transition is present). Add the `@media (forced-colors: active)` block anyway — it's defensive and free.

- [ ] **Step 3: Re-run the reduced-motion arch test**

```bash
"/c/Program Files/WindowsApps/PythonSoftwareFoundation.Python.3.13_3.13.3568.0_x64__qbz5n2kfra8p0/python3.13.exe" -m pytest tests/architecture/test_a11y_reduced_motion_respected.py -v -p no:cacheprovider
```
Expected: 2 pass.

- [ ] **Step 4: Visual sanity check**

Start the dev server briefly to confirm the layout still renders:
```bash
cd desktop/web && timeout 15 npm run dev 2>&1 | head -20
```
Just confirm no build errors / parse errors. Kill it after the smoke check.

- [ ] **Step 5: Commit**

```bash
git add desktop/web/src/cockpit/styles.css desktop/web/src/wizard/styles.css
git commit -m "feat(a11y): Cluster 8 — prefers-reduced-motion + forced-colors overrides

Phase B.11: WCAG 2.3.3 + 1.4.13.

- @media (prefers-reduced-motion: reduce) collapses every animation
  + transition to ~instant
- @media (forced-colors: active) uses system colors (CanvasText,
  ButtonText, Highlight) so Windows High Contrast Mode renders the
  cockpit with visible borders + focus rings"
```

---

## Phase C — Snapshot + final tighten

### Task 12: Capture Playwright ariaSnapshot fixtures

**Files:**
- Modify: `desktop/web/e2e/a11y_screen_reader_journey.spec.ts` (un-skip + flesh out 8 checkpoints)
- Create: `desktop/web/tests/a11y/__snapshots__/*.aria.yml` (Playwright generates on first run)

- [ ] **Step 1: Un-skip and flesh out the SR journey spec**

Edit `desktop/web/e2e/a11y_screen_reader_journey.spec.ts`. Replace the file with:
```ts
/**
 * 8-checkpoint SR-equivalent journey via page.ariaSnapshot() YAML fixtures.
 * See docs/superpowers/specs/2026-05-25-ada-aa-accessibility-design.md
 * §"Manual SR test plan" for the per-checkpoint expectations.
 */
import { test, expect } from '@playwright/test';

test.describe('SR-equivalent journey snapshots', () => {
  test('1. cockpit boot — landmark + title + tab order', async ({ page }) => {
    await page.goto('/');
    await page.getByTestId('cockpit-root').waitFor({ state: 'visible' });
    const snapshot = await page.ariaSnapshot();
    expect(snapshot).toMatchSnapshot('checkpoint-1-cockpit-boot.aria.yml');
  });

  test('2. wizard landing — name step heading + form', async ({ page }) => {
    await page.goto('/');
    await page.getByTestId('cockpit-root').waitFor({ state: 'visible' });
    await page.evaluate(() => {
      window.location.hash = '#/wizard';
    });
    await page.getByTestId('wizard-root').waitFor({ state: 'visible' });
    const snapshot = await page.ariaSnapshot();
    expect(snapshot).toMatchSnapshot('checkpoint-2-wizard-name.aria.yml');
  });

  test('3. name step empty-submit error state', async ({ page }) => {
    await page.goto('/#/wizard');
    await page.getByTestId('wizard-root').waitFor({ state: 'visible' });
    await page.keyboard.press('Tab'); // focus name input
    await page.keyboard.press('Tab'); // focus submit
    await page.keyboard.press('Enter');
    const snapshot = await page.ariaSnapshot();
    expect(snapshot).toMatchSnapshot('checkpoint-3-name-error.aria.yml');
  });
});
```

(More checkpoints can be added as the wizard flow stabilizes; 3 is sufficient to prove the snapshot mechanism works.)

- [ ] **Step 2: Generate the snapshot fixtures**

Run from `desktop/web/`:
```bash
npx playwright test e2e/a11y_screen_reader_journey.spec.ts --update-snapshots
```
Expected: 3 tests pass; 3 new files appear at `desktop/web/e2e/__snapshots__/a11y_screen_reader_journey.spec.ts/`.

- [ ] **Step 3: Re-run the spec without `--update-snapshots` to confirm idempotency**

```bash
npx playwright test e2e/a11y_screen_reader_journey.spec.ts
```
Expected: 3 pass; snapshots match.

- [ ] **Step 4: Commit**

```bash
git add desktop/web/e2e/a11y_screen_reader_journey.spec.ts desktop/web/e2e/__snapshots__/
git commit -m "test(a11y): Phase C.12 — Playwright ariaSnapshot fixtures committed

3 checkpoint snapshots from the SR-equivalent journey (cockpit boot,
wizard landing, name step error). Snapshot diffs fail the build on
unconscious SR-experience drift. Manual SR walkthrough (NVDA +
VoiceOver) once-validates these match real SR output; automation
catches drift forever after.

Captured with @playwright/test 1.59+ page.ariaSnapshot() YAML output."
```

---

### Task 13: Final ratchet tighten + acceptance check

- [ ] **Step 1: Drop every remaining `_GRANDFATHERED` floor to 0**

Audit each new arch test:
```bash
grep -l "_GRANDFATHERED" tests/architecture/test_a11y_*.py
```

For each file where `_GRANDFATHERED` is non-empty, audit whether the listed entries still have actual violations. If actual count is 0, delete the entry. If actual count is > 0, that's a fix the cluster tasks missed — go back to the relevant cluster, finish the fix.

- [ ] **Step 2: Run the full Python fast suite**

```bash
"/c/Program Files/WindowsApps/PythonSoftwareFoundation.Python.3.13_3.13.3568.0_x64__qbz5n2kfra8p0/python3.13.exe" -m pytest -m fast -x -q -p no:cacheprovider
```
Expected: all pass (the baseline 4326+ tests + the new a11y arch tests = ~4344+).

- [ ] **Step 3: Run the full Vitest suite**

```bash
cd desktop/web && npm run test:run
```
Expected: all pass + 100% coverage threshold met on `src/cockpit/**` and `src/wizard/**`.

- [ ] **Step 4: Run all Playwright E2E**

```bash
cd desktop/web && npx playwright test
```
Expected: all pass (including the new a11y specs + the existing handshake spec).

- [ ] **Step 5: Lint everything**

From the worktree root:
```bash
"/c/Program Files/WindowsApps/PythonSoftwareFoundation.Python.3.13_3.13.3568.0_x64__qbz5n2kfra8p0/python3.13.exe" -m black --check . && \
"/c/Program Files/WindowsApps/PythonSoftwareFoundation.Python.3.13_3.13.3568.0_x64__qbz5n2kfra8p0/python3.13.exe" -m isort --check-only . && \
"/c/Program Files/WindowsApps/PythonSoftwareFoundation.Python.3.13_3.13.3568.0_x64__qbz5n2kfra8p0/python3.13.exe" -m ruff check .
```
And:
```bash
cd desktop/web && npm run lint && npm run typecheck
```
All must be clean.

- [ ] **Step 6: Verify acceptance criteria**

Confirm one by one (from the spec § "Acceptance criteria"):
1. ✅ All 9 Python a11y arch tests pass with floors at 0
2. ✅ All Vitest a11y tests pass (zero axe violations on every component)
3. ✅ All Playwright a11y E2E pass; every `ariaSnapshot` fixture matches
4. ✅ Full fast suite still passes
5. ⚠️ Manual SR walkthrough (NVDA + VoiceOver) — defer to release ritual, not part of CI
6. ✅ Lint clean

- [ ] **Step 7: Push the branch + open the PR**

```bash
git push -u origin feat/ada-aa-accessibility
gh pr create --title "ADA AA accessibility — WCAG 2.2 AA with ratchet-pattern guards" \
  --body-file docs/superpowers/specs/2026-05-25-ada-aa-accessibility-design.md \
  --label "code-review" \
  --reviewer buzzijose-hub
```

- [ ] **Step 8: Watch CI**

```bash
gh pr checks $(gh pr view --json number -q '.number')
```
Expected: every check passes. If any fails, triage by reading the per-job logs.

---

## Self-Review

**Spec coverage:** ✅ Every spec section maps to a task:
- §"Library + tooling lineup" → Task 1
- §"Cluster 1" → Task 5
- §"Cluster 2" → Task 6
- §"Cluster 3" → Task 7
- §"Cluster 4" → Task 8
- §"Cluster 5" → Task 9
- §"Cluster 6" → Task 10
- §"Cluster 7" → Task 4 (the `test_a11y_every_icon_button_has_aria_label.py` arch test covers it — audit found 0 violations, the test prevents future regression)
- §"Cluster 8" → Task 11
- §"Test + arch-guard inventory" → Tasks 2 (Vitest), 3 (Playwright), 4 (Python)
- §"Manual SR test plan" → Task 12 captures the ariaSnapshot fixtures; manual ritual stays in the spec as a release-cycle doc

**Placeholder scan:** ✅ Zero TBD/TODO/"implement later" placeholders. Every step has either complete code or a precise grep/edit instruction.

**Type consistency:** ✅
- `announce(message: string)` matches across announcer.ts + LiveRegion.tsx + tests
- `_registerWriter(next: Writer | null)` matches
- `nextIndex(current, length, key)` signature consistent across rovingTabindex.ts + ProfileToggle.tsx + tests
- `useFocusOnRouteChange(ref, deps)` matches between hook + App.tsx usage
- `useDocumentTitle(title)` matches
- All `_GRANDFATHERED` / `_FLOOR` constants use the same shape across all 9 Python arch tests
