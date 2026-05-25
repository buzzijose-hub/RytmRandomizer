---
name: playwright-strict-mode-selectors
description: "Playwright runs every selector in strict mode. text= and locator(string) MUST resolve to exactly one element. Validate against a running dev server before push or you waste a CI cycle."
user-invocable: false
origin: auto-extracted
---

# Playwright strict-mode selectors require pre-push validation

**Extracted:** 2026-05-25
**Context:** Writing or modifying any Playwright E2E spec in `desktop/web/e2e/`.

## Problem

Playwright runs every selector in strict mode. `page.locator('text=Foo')` MUST resolve to exactly one element. Two matches = `strict mode violation` runtime error in the browser, not a Python type error your IDE can catch.

You will not see this failure until the spec runs against a real browser. Unit tests don't catch it (no DOM), Python tests don't catch it (different layer), TypeScript compile doesn't catch it (the selector is a string). The only catcher is `npm run e2e` against a real dev sidecar + dev server.

In PR #113 wave-2, a `handshake_token.spec.ts` shipped with `page.locator('text=Connecting')`. Locally I never ran the spec. CI failed because the placeholder DOM contains:
```
<p>Connecting…</p>
<small>status: reconnecting</small>
```
Both match `text=Connecting`. The strict-mode check fired in the browser, the test failed all 3 retries, and a full ~10-minute CI cycle was wasted before I could re-push the fix.

## Solution

**Always prefer specific selectors over text=:**

| Bad | Good | Why |
|-----|------|-----|
| `page.locator('text=Connecting')` | `page.locator('main.cockpit-placeholder')` | Targets the container, not whatever text the container happens to render |
| `page.getByText('Save')` | `page.getByRole('button', { name: 'Save' })` | Distinguishes a Save button from "Save:" in a label or breadcrumb |
| `page.locator('.foo')` if `.foo` appears in multiple states | `page.getByTestId('foo-root')` | `data-testid` is intentional contract; class selectors get reused |

**Pre-push validation recipe (do this BEFORE `git push`):**

```bash
# Terminal 1: sidecar
cd <repo-root>
"/c/Program Files/WindowsApps/PythonSoftwareFoundation.Python.3.13_*/python3.13.exe" -m rytm_randomizer.cockpit

# Terminal 2: dev server
cd desktop/web
npm run dev

# Terminal 3: run JUST your new spec
cd desktop/web
npm run e2e -- <new-spec-name>.spec.ts
```

If you cannot run a real browser locally (e.g. headless environment without Chromium), at minimum:
1. Grep for the selector string in the relevant React component to confirm it appears exactly once.
2. Use `data-testid` selectors which the codebase reserves for E2E targeting — you can grep `data-testid=` to confirm uniqueness.

## When to Use

- Writing or editing any `*.spec.ts` file under `desktop/web/e2e/`
- Migrating an existing spec to a new selector (you may now collide with a new element the previous spec was unaware of)
- Adding placeholders/loading states to React components that an existing E2E spec might target by text
- Reviewing a PR that introduces a new E2E spec — always ask "did the author run this against a real browser?"

## Why text= is tempting (and why to resist it)

`text=` is the most natural way to write a "user clicks on the button labeled Save" spec. But the moment your UI has two surfaces showing similar text (a status chip + a placeholder, a heading + a breadcrumb, a tooltip + the trigger), `text=` becomes a strict-mode violation.

The right intuition: **a Playwright selector encodes the contract between the test and the DOM.** Tests should depend on element IDENTITY (`data-testid`, role + accessible name), not on element CONTENT (whatever text the component happens to render). Content drifts; identity is intentional.

## Related

- See memory `feedback_validate_tests_against_real_env_before_push` for the broader rule covering both Playwright AND Python tests that touch global state.
- See `desktop/web/e2e/handshake_token.spec.ts` for the canonical bad-then-good fix:
  - bad: `page.locator('text=Connecting')` (matched `<p>Connecting…</p>` AND `<small>status: reconnecting</small>`)
  - good: `page.locator('main.cockpit-placeholder')` (targets the placeholder container by class)
