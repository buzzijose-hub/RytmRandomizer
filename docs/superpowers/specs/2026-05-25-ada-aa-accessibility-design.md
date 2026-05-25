# ADA AA Accessibility — Design Spec

**Date:** 2026-05-25
**Status:** Approved (pending spec re-review)
**Branch:** `feat/ada-aa-accessibility`

## Goal

Make the RytmRandomizer desktop UI fully WCAG 2.2 AA compliant, drivable
without a mouse, and usable with NVDA + VoiceOver, with automated tests and
Python architecture guards that prevent slippage. Ships as one bundled PR.

## Non-goals

- WCAG AAA criteria (separate, larger scope).
- JAWS testing (not required per user scope).
- iOS / mobile screen reader testing (no mobile cockpit ships yet).
- Switch-control device testing (different access need; AAA-adjacent).
- A design-token system rewrite (existing palette is mostly fine; targeted
  contrast fixes only).

## Audience

- **Primary:** sighted operators using keyboard + mouse (existing
  behaviour must not regress).
- **Secondary:** sighted operators using keyboard only (no-mouse path —
  goal-explicit user story).
- **Tertiary:** screen-reader users on NVDA (Windows) or VoiceOver
  (macOS), functional-equivalence philosophy: every workflow a sighted
  user can drive, including live mutation previews and SEND, must be
  drivable text-first.

## Standard and SR matrix

- **Target:** WCAG 2.2 AA (current standard, adopted by EU EAA + most
  US gov / enterprise procurement; adds target-size 24px min,
  focus-not-obscured, consistent help, redundant entry).
- **Screen readers validated:** NVDA latest on Windows 10/11 in Tauri's
  WebView2; VoiceOver latest on macOS in Tauri's WKWebView.

## Architecture and approach

Adopt the **ratchet pattern** proven on PR #113's RR4 set, applied to a11y:

1. Every category of violation gets a detector (Vitest test, Playwright
   E2E test, or Python AST architecture test).
2. Each detector starts with a grandfathered allowlist sized to the
   current audit count.
3. Two companion tests per detector: (a) the main rule that fails if a
   NEW violation appears (count exceeds floor), (b) a drain-allowlist
   test that fails if a contributor fixed a grandfathered violation
   but forgot to lower the floor (silently widening the gate).
4. Floors start at audit count, drop monotonically as fix commits land.
   Final state: every floor at 0, every detector active, no allowlist
   entries.

This is the same shape as `tests/architecture/test_no_raw_exception_messages_on_wire.py`
in PR #113 — battle-tested at this codebase scale.

## Library + tooling lineup (2026)

| Layer | Library | Rationale |
|---|---|---|
| Unit a11y scans | `axe-core` (direct, no wrapper) | Vitest direct integration; skip `jest-axe` (wrong runner) and `vitest-axe` (stale, last meaningful release Jan 2025 pre-1.0) |
| Unit keyboard tests | `@testing-library/user-event` v14+ | Already in stack; modern `.tab()` / `.keyboard('{ArrowRight}')` API |
| Unit live-region assertions | `@testing-library/react` `getByRole('status')` | Already in stack |
| E2E a11y scans | `@axe-core/playwright` | Actively maintained, axe-core 4.11.1+, supports WCAG 2.2 |
| E2E SR equivalence | Playwright `page.ariaSnapshot()` (1.59+) | YAML accessibility-tree snapshots; far more robust than text-content matching |
| E2E keyboard journeys | Playwright native `page.keyboard` | No add-on needed |
| Contrast checking | `wcag-contrast` (~3 KB) | Tiny; the formula is 10 lines so inline is also acceptable |
| Architecture tests | Existing Python suite | No new deps; runs alongside RR4 set |

**Explicitly NOT added:**
- `@axe-core/react` — Deque dropped React 18+ support; their guidance
  is to use raw `axe-core` in Vitest + `@axe-core/playwright` for E2E.

## Component remediation clusters

Each cluster maps to a specific WCAG criterion + the test/guard that
makes the fix permanent.

### Cluster 1 — Keyboard interaction completeness

- `ProfileToggle.tsx`: tablist missing arrow-key navigation
  (WCAG 2.1.1; ARIA Authoring Practices tabs pattern). Add `onKeyDown`
  for Left/Right/Home/End plus `tabIndex={selected ? 0 : -1}` (roving
  tabindex).
- `HistoryStrip.tsx`: snapshot dots respond to Left/Right when focused
  to step through history; Home/End jump to first/last. Roving tabindex.
- `DepthSlider.tsx`: native `<input type="range">` already keyboard
  accessible (arrows, Home/End, PageUp/PageDown). Verify via test, no
  code change expected.

**Test:** `desktop/web/tests/a11y/keyboard_navigation.test.tsx` — for each
interactive group, simulate the documented key sequence and assert focus
moves correctly.

### Cluster 2 — Color contrast (small text)

- `.knob-label` (10 px) and `.pad-card-title` (12 px) use `--text-dim`
  on `--panel-2` at ~5.9:1 — marginal for AA at small sizes (1.4.3
  requires 4.5:1 for normal, 3.0:1 for large; small under 14 px reads
  as normal). Swap to `--text` (primary) since these labels carry
  identity, not "secondary" hint text.
- Leave `--text-dim` for genuine secondary content (timestamps,
  hint text), where it remains comfortably above 4.5:1.

**Test:** `tests/architecture/test_a11y_color_palette_aa.py` — parses
CSS custom-property pairs, computes WCAG contrast via inline formula,
fails any small-text pair with ratio < 4.5.

### Cluster 3 — Form error feedback

- `NameStep.tsx` and `AddStep.tsx` validate silently. Add per field:
  - `aria-invalid={hasError}` on the input
  - `aria-describedby="<field>-error"` pointing at a conditionally
    rendered `<div id="<field>-error" role="alert">`
  - `aria-required="true"` on required fields
  - Focus moves to the first invalid field on submit

**Test:** `desktop/web/tests/a11y/form_errors.test.tsx` — submit empty,
assert error message text + focus + ARIA attrs.

### Cluster 4 — Live regions for async state

Cockpit pushes async events over WebSocket: `session_status`,
`snapshot_changed`, `mutation_previewed`, `send_plan_changed`,
profile-save completion, wizard step transitions. Today the UI
re-renders silently.

- Mount a single `<div role="status" aria-live="polite" aria-atomic="true"
  className="sr-only">` at `App.tsx` root.
- New module `desktop/web/src/a11y/announcer.ts` exposes `announce(message)`
  that writes into the live region with a debounce to avoid flooding.
- Zustand store subscribes; specific state changes emit categorical
  announcements:
  - "Mutation preview ready, depth X percent, N pads affected"
  - "Send complete, M parameters sent"
  - "Send failed: <safe categorical reason>"
  - "Profile selected: <name>"
  - "Wizard step <N> of 4: <step name>"
  - "Analyzing source <i> of <N>"
  - "Profile saved as <name>"
- Use `polite` (not `assertive`) so announcements queue rather than
  interrupt the user mid-action.

**Test:** `desktop/web/tests/a11y/live_region.test.tsx` — mount App
with a Zustand store, fire each store event, assert announcer
`textContent` matches the documented announcement.

### Cluster 5 — Focus management on route + state change

- New hook `desktop/web/src/a11y/useFocusOnRouteChange.ts`. On hash
  route change (`#/` ↔ `#/wizard`), move focus to the route's `<h1>`
  via a `ref` + `useEffect`. SR users get the route announcement
  automatically; sighted keyboard users get a visible focus indicator
  on the new heading.
- On form error appearing, focus moves to the first invalid field
  (Cluster 3 already covers this).
- Reserve `desktop/web/src/a11y/useFocusTrap.ts` for future modal use
  — no modals today, but the hook is part of the toolkit.

**Test:** `desktop/web/tests/a11y/focus_management.test.tsx` — change
hash, assert `document.activeElement` is the route's main heading.

### Cluster 6 — Document title + landmarks

- New hook `desktop/web/src/a11y/useDocumentTitle.ts` updates
  `document.title` per route ("RytmRandomizer · Cockpit" vs
  "RytmRandomizer · Profile Wizard · Step <N> <name>").
- `Cockpit.tsx` root container: `<div>` → `<main>` so SR's "jump to
  main" works.
- `Wizard.tsx` already uses `<main>`; verify.
- Add `<h1>` per route (cockpit currently has none).

**Test:** `tests/architecture/test_a11y_every_route_has_main_landmark.py`
— AST-walks each top-level route component; asserts exactly one
`<main>` and exactly one `<h1>` rendered. Also
`desktop/web/tests/a11y/document_title.test.tsx` verifies per-route
title text.

### Cluster 7 — Icon-only buttons + accessible names

Audit found all icon-only buttons already have `aria-label`. Add an
arch test that enforces this going forward.

**Test:** `tests/architecture/test_a11y_every_icon_button_has_aria_label.py`
— AST: any `<button>` whose only children are `<svg>` / `<Icon>` /
`<img>` must have `aria-label` or `aria-labelledby`. Floor 0
immediately.

### Cluster 8 — Reduced motion + forced colors

WCAG 2.2 / 2.3.3 / 1.4.13 / Windows High Contrast support.

- Wrap any animations in `@media (prefers-reduced-motion: no-preference)`.
- Add `@media (forced-colors: active)` overrides so Windows High
  Contrast mode renders cleanly (focus indicators visible, button
  borders preserved).

**Test:** `tests/architecture/test_a11y_reduced_motion_respected.py`
— any CSS file containing `@keyframes`, `animation:`, or `transition:`
(other than instant) must also contain `@media (prefers-reduced-motion`.

## Test + arch-guard inventory

### A11y unit tests (Vitest, `desktop/web/tests/a11y/`)

| File | Coverage |
|---|---|
| `axe_smoke.test.tsx` | `axe-core` direct-call scan per top-level component (Cockpit, Wizard.NameStep, AddStep, AnalyzeStep, ReviewStep) against a per-component grandfathered violation list |
| `keyboard_navigation.test.tsx` | userEvent flows for ProfileToggle tablist arrows, HistoryStrip arrows, slider Home/End, form Tab order |
| `live_region.test.tsx` | Store event → announcer `textContent` assertion for each documented announcement |
| `focus_management.test.tsx` | Route transition focus, form-error focus, future dialog-open focus restoration |
| `document_title.test.tsx` | Each route mount → assert `document.title` matches the route-specific pattern |
| `contrast.test.ts` | Parses `cockpit/styles.css` and `wizard/styles.css` for CSS custom properties, computes WCAG ratio for documented pairs, fails on AA misses |
| `form_errors.test.tsx` | Cluster 3 behavioural coverage — empty submit, assert error text + focus + ARIA |

### E2E (Playwright, `desktop/web/e2e/`)

| File | Coverage |
|---|---|
| `a11y_keyboard_journey.spec.ts` | Cockpit + wizard journeys driven entirely via `page.keyboard`; asserts every UI surface a sighted user reaches is reachable |
| `a11y_axe_scan.spec.ts` | `@axe-core/playwright` scan per top-level route, same per-route grandfathered list as the Vitest scans (so they cannot drift) |
| `a11y_screen_reader_journey.spec.ts` | Drives the wizard happy path; asserts `page.ariaSnapshot()` matches committed YAML fixtures at each of 8 checkpoints (see §"Manual SR test plan") |

### Python architecture tests (`tests/architecture/`)

All 8 use the RR4 ratchet shape; each gets two companion tests
(main rule + drain-allowlist).

| File | What it forbids |
|---|---|
| `test_a11y_no_div_onclick.py` | `<div onClick>` / `<span onClick>` in `desktop/web/src/` — forces semantic `<button>` / `<a>` |
| `test_a11y_every_icon_button_has_aria_label.py` | `<button>` with icon-only children must have `aria-label` / `aria-labelledby` |
| `test_a11y_every_form_field_has_label.py` | `<input>` / `<textarea>` / `<select>` must have associated `<label htmlFor>` OR `aria-label` OR `aria-labelledby` |
| `test_a11y_every_route_has_main_landmark.py` | Top-level route components render exactly one `<main>` and exactly one `<h1>` |
| `test_a11y_color_palette_aa.py` | Documented CSS custom-property pairings meet AA contrast |
| `test_a11y_no_aria_hidden_focusable.py` | `aria-hidden="true"` elements cannot be focusable (no `tabIndex >= 0`, no focusable tag) |
| `test_a11y_no_role_attribute_redundancy.py` | `role="button"` on `<button>`, `role="link"` on `<a>`, etc. forbidden (semantic-HTML smell) |
| `test_a11y_announcer_is_wired.py` | `App.tsx` must mount the live-region `<div role="status" aria-live="polite">` |
| `test_a11y_reduced_motion_respected.py` | CSS files with animations must also have `@media (prefers-reduced-motion)` overrides |

## Manual SR test plan (release-cycle ritual)

Run once per SR (NVDA + VoiceOver) before merging the PR and before
each release. Not part of CI gate — the Playwright `ariaSnapshot`
fixtures bridge automation and manual once these pass.

1. **Cockpit boot** — title + H1 + landmark announce; Tab order
   header → mutation panel → snapshot panel → action bar.
2. **Pad navigation** — each pad announces identity + lock state +
   parameter values (e.g. "Pad 1, BD Hard, unlocked, LEV 110, TUN 30,
   DEC 80").
3. **Profile select** — ProfileToggle tablist announces "tab list, 2
   tabs"; arrow keys move; selected tab announces "selected"; chips
   announce with `aria-current="true"` on selected.
4. **Depth slider** — slider announces value, min, max; arrow keys
   move; Home/End jump.
5. **Mutation preview** — REGEN triggers live-region announce
   "Mutation preview ready, depth 50%, 3 pads affected".
6. **Send** — disabled state uses `aria-disabled="true"` (announces
   *why*); SEND triggers "Send complete, M parameters sent" or
   categorical failure.
7. **Wizard journey** — hash-route, title changes, focus on wizard
   H1, step indicator announces; per-step transitions announce;
   final save announces.
8. **Error path** — submit empty Name; live region announces "Name is
   required"; focus to the field; field announces "Name, edit,
   required, invalid, Name is required".

Each checkpoint above gets a committed `ariaSnapshot` YAML fixture in
`desktop/web/tests/a11y/__snapshots__/`. Snapshot diffs fail the build
on unconscious SR-experience drift.

## Commit sequence (one bundled PR)

| # | Commit | Files |
|---|---|---|
| 1 | Install + wire deps (`axe-core`, `@axe-core/playwright`, bump Playwright if < 1.59) | `desktop/web/package.json`, `desktop/web/tests/setup.ts` |
| 2 | Vitest a11y test suite with grandfathered per-component violation lists | `desktop/web/tests/a11y/*.test.tsx` |
| 3 | Playwright a11y E2E with grandfathered per-route violation lists | `desktop/web/e2e/a11y_*.spec.ts` |
| 4 | Python arch guards (8 tests, parallel to RR4) with grandfathered floors | `tests/architecture/test_a11y_*.py` |
| 5 | Cluster 1 — Keyboard interaction completeness | `cockpit/ProfileToggle.tsx`, `HistoryStrip.tsx` |
| 6 | Cluster 2 — Color contrast (small text) | `cockpit/styles.css` |
| 7 | Cluster 3 — Form error feedback | `wizard/NameStep.tsx`, `AddStep.tsx` |
| 8 | Cluster 4 — Live region + announcer module | new `a11y/announcer.ts`, `App.tsx`, state subscriptions |
| 9 | Cluster 5 — Focus management on route change | new `a11y/useFocusOnRouteChange.ts`, `App.tsx` |
| 10 | Cluster 6 — Document title + `<main>` + `<h1>` | new `a11y/useDocumentTitle.ts`, `Cockpit.tsx`, `App.tsx` |
| 11 | Cluster 8 — Reduced-motion + forced-colors CSS | `cockpit/styles.css`, `wizard/styles.css` |
| 12 | Capture committed `ariaSnapshot` fixtures (after fixes are in) | `desktop/web/tests/a11y/__snapshots__/*.yml` |
| 13 | All ratchet floors at 0 + drain-allowlist test active | various |

Clusters 5-11 land in parallel — each touches an isolated file set
and can be done by independent subagents. Commits 1-4 must land first
(infrastructure dependencies), then 5-11 in parallel, then 12 (snapshot
capture must happen after fixes are in place), then 13 (the final
ratchet tightening confirms zero violations remain).

## Acceptance criteria

1. All 9 Python a11y arch tests pass with floors at 0.
2. All Vitest a11y tests pass (zero axe violations on every
   component).
3. All Playwright a11y E2E pass; every `ariaSnapshot` fixture
   matches.
4. Full fast suite (currently 4326 tests) still passes.
5. Manual SR walkthrough (the 8 journeys above) signed off against
   NVDA + VoiceOver.
6. Lint clean: `black` + `isort` + `ruff` (Python); `eslint` +
   `prettier` (TypeScript).

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Tauri's WebView2 (Edge) and WKWebView (Safari) render ARIA differently | Snapshot fixtures captured per platform; CI runs E2E on both Ubuntu + Windows + macOS runners |
| `axe-core` only catches ~57% of WCAG issues | Multi-layer suite + manual SR ritual covers the rest; arch tests catch structural anti-patterns axe doesn't surface |
| Live-region flooding from rapid state changes | Announcer module debounces with a configurable interval (default 200 ms); rate-limit tests pin the behaviour |
| Contrast pairs that pass automated check fail in dark mode (or vice versa) | Cockpit is dark-only today; arch test is single-theme. Future theme work must extend the matrix |
| Roving tabindex misimplementation desyncs `tabIndex` and `aria-selected` | Test asserts both move in lockstep on every key press |

## References

- WCAG 2.2 AA quickref: <https://www.w3.org/WAI/WCAG22/quickref/>
- ARIA Authoring Practices Tabs pattern: <https://www.w3.org/WAI/ARIA/apg/patterns/tabs/>
- axe-core rules + WCAG mapping: <https://www.npmjs.com/package/axe-core>
- `@axe-core/playwright`: <https://playwright.dev/docs/accessibility-testing>
- Playwright `ariaSnapshot`: <https://playwright.dev/docs/aria-snapshots>
- RR4 ratchet shape precedent: this repo's
  `tests/architecture/test_no_raw_exception_messages_on_wire.py`
