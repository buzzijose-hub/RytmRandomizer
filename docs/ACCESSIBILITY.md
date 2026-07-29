# Accessibility — WCAG 2.2 AA conformance

RytmRandomizer's cockpit is built to **WCAG 2.2 Level AA**. Accessibility is a
first-class, mechanically-enforced invariant of this repo — not a
post-hoc audit. This document is the conformance statement, the enforcement
map, and the per-release manual screen-reader smoke protocol.

The cockpit is a Tauri desktop app whose UI is a Vite + React + TypeScript
web surface (`desktop/web/`) rendered in the platform WebView. All guidance
below targets that surface.

---

## 1. Conformance statement

- **Standard:** Web Content Accessibility Guidelines (WCAG) 2.2.
- **Conformance level:** AA.
- **Scope:** the cockpit (`desktop/web/src/cockpit/**`), the profile wizard
  (`desktop/web/src/wizard/**`), and the shared a11y infrastructure
  (`desktop/web/src/a11y/**`).
- **Evaluation methods:** automated axe-core scans (jsdom component/panel
  audit + real-Chromium route scan), CSS-token contrast analysis, and a
  per-release manual screen-reader pass (§5).
- **Known limitations:** see §6.

Every success criterion below is either enforced by an automated gate (the
table in §3) or covered by the manual protocol (§5).

---

## 2. What "AA" means here, concretely

| Area | Commitment |
|---|---|
| **Perceivable** | 4.5:1 text contrast, 3:1 non-text/large-text contrast, every status conveyed by icon **and** shape/text — never hue alone. |
| **Operable** | Full keyboard reachability + operability; visible focus on every focusable element; interactive targets ≥ 24×24 px (SC 2.5.8); no keyboard trap except the modal arm dialog (which is an intentional, escapable focus trap per APG). |
| **Understandable** | Every form field labelled; errors announced; consistent landmark + heading structure; per-route `document.title`. |
| **Robust** | Name/role/value parity on every custom control (SC 4.1.2); status messages exposed via live regions (SC 4.1.3) — polite for routine updates, `role="alert"` for criticals. |

### Colour is never the only signal

The status palette (`--green` / `--amber` / `--danger` / `--accent`) is
**reinforcement**. Every status also carries a glyph and text: badge tones
pair an icon (`✓ ! ⚠ •`) with a label; the arm state reads "ARMED — Disarm"
with a `▲`/`○` glyph; the MIDI-activity dot is `aria-hidden` decoration on
top of the textual "listening"/"paused" badge. This keeps the UI legible for
deuteranopia / protanopia / tritanopia and in greyscale.

### Custom controls → APG patterns

Two reference shapes, chosen by whether the control is interactive:

- **Read-only value display** (`Knob.tsx`): `role="img"` with an
  `aria-label` of `"<label> value <n>"`. It emits no events and takes no
  keyboard input, so it is a labelled graphic, **not** a `role="slider"`
  (which would promise interaction the control does not have).
- **Interactive value control** (`DepthSlider.tsx`): a native
  `<input type="range">` — which gives Arrow / Home / End / PageUp-Down
  keyboard operation, `aria-valuenow`, and focus for free — plus an
  `aria-valuetext` that speaks the human-facing percentage ("45 percent")
  instead of the raw `0.45` float, satisfying SC 4.1.2. The track is ≥ 24 px
  tall for SC 2.5.8.

New custom controls must follow whichever of these two shapes matches their
interactivity. Do not put `role="slider"` on a non-interactive display.

### Live regions (SC 4.1.3)

There is exactly **one** polite live region for the whole app
(`src/a11y/LiveRegion.tsx` + `announce()` in `src/a11y/announcer.ts`).
Routine status changes (armed/disarmed, saved, refreshed) route through it;
the announcer debounces bursts so a flurry of store updates collapses into a
single spoken message. **Do not add a second polite live region.**

Criticals the operator must not miss — arm rejections, disarm failures,
connection faults, wizard validation errors — use `role="alert"` (an
assertive channel) *in addition to* the polite announcer. `ArmControl.tsx`
is the reference: its rejection message renders as `role="alert"` inside the
modal so a screen reader interrupts to speak it.

### The arm dialog

The arm confirmation is a `role="dialog" aria-modal="true"` with
`aria-labelledby` + `aria-describedby`, an intentional Tab/Shift+Tab focus
trap (APG modal pattern), `autoFocus` on the token input, and Escape-to-close.
Disarm is always one click — safety must never sit behind a dialog.

### Motion & flashing

- The MIDI-activity indicator flashes by class toggle, rate-capped to
  **< 3 flashes/second** (`FLASH_MIN_INTERVAL_MS = 350` ms → ~2.8/s max),
  clearing SC 2.3.1 (three-flash threshold).
- Every CSS file that declares an animation or non-instant transition ships a
  `@media (prefers-reduced-motion: reduce)` override
  (`test_a11y_reduced_motion_respected.py`).

---

## 3. Enforcement map — which gate covers which criterion

Accessibility is enforced on **every push** by PR-blocking checks. Two axe
lanes plus a set of static architecture tests:

### Automated axe scans

| Gate | Runner | Where | What it catches |
|---|---|---|---|
| **Component/panel audit** | axe-core in jsdom | `desktop/web/tests/a11y/cockpit_axe_audit.test.tsx` (run by `npm run test:a11y`, a named step in the `desktop-web` CI job) | Structural WCAG 2.0/2.1/2.2 A+AA violations on every cockpit component + panel, in isolation. Floor 0 for every surface. |
| **Per-control assertions** | axe-core in jsdom | `tests/cockpit/DepthSlider.test.tsx` (+ per-panel cases) | Control-level name/role/value + slider-pattern regressions. |
| **Route scan** | @axe-core/playwright in real Chromium | `desktop/web/e2e/a11y_axe_scan.spec.ts` (`desktop-web-e2e` CI job) | Full-route violations **including colour-contrast** (which jsdom cannot compute — see §6). |
| **Keyboard / SR journeys** | Playwright | `e2e/a11y_keyboard_journey.spec.ts`, `e2e/a11y_screen_reader_journey.spec.ts` | Tab order, focus movement, accessible-name snapshots. |

> **jsdom caveat:** jsdom has no canvas, so axe-core's colour-contrast rule
> cannot run there and is silently skipped in the component audit. Contrast is
> therefore enforced by the Chromium route scan **and** the CSS-token
> architecture test below — the two overlap so neither lane is the sole
> guardian of contrast.

### Static architecture tests (`tests/architecture/test_a11y_*.py`)

| Test | Criterion |
|---|---|
| `test_a11y_color_palette_aa.py` | 1.4.3 / 1.4.11 — every documented token pair (text 4.5:1, non-text 3:1) including the `--accent` focus ring on `--bg`/`--panel`. |
| `test_a11y_reduced_motion_respected.py` | 2.3.3 — animated CSS honours `prefers-reduced-motion`. |
| `test_a11y_every_form_field_has_label.py` | 1.3.1 / 3.3.2 — labelled inputs. |
| `test_a11y_every_icon_button_has_aria_label.py` | 4.1.2 — icon-only buttons have accessible names. |
| `test_a11y_every_route_has_main_landmark.py` | 1.3.1 / 2.4.1 — one `<main>` per route. |
| `test_a11y_no_aria_hidden_focusable.py` | 4.1.2 — no focusable element hidden from AT. |
| `test_a11y_no_div_onclick.py` | 2.1.1 — no `div`+`onClick`; use real controls. |
| `test_a11y_no_role_attribute_redundancy.py` | 4.1.2 — no redundant ARIA roles. |
| `test_a11y_announcer_is_wired.py` | 4.1.3 — the single polite live region is mounted + wired. |

The global `:focus-visible` ring (`src/cockpit/styles.css`) provides SC 2.4.7
focus visibility for every focusable element that does not supply its own
bespoke indicator.

### Running the gates locally

```bash
# Frontend a11y (fast, jsdom) + full suite + build:
cd desktop/web
npm run test:a11y          # the PR-blocking axe gate, on its own
npm run typecheck && npm run lint && npx vitest run --coverage

# Real-browser route scan + keyboard/SR journeys:
npm run e2e                # requires Playwright browsers + Python sidecar

# Static a11y architecture tests:
.venv/bin/python -m pytest tests/architecture/test_a11y_*.py -q
```

---

## 4. Adding a new panel or control — the a11y contract

New cockpit surfaces go through the schema-driven PanelSpec platform, which
gives you labelled landmarks, icon+text badges, and disabled-not-hidden
blocked actions **for free** — see `.claude/skills/add-cockpit-panel`
("Per-panel accessibility acceptance checklist"). The non-negotiables:

1. Add a floor-0 case to `cockpit_axe_audit.test.tsx`.
2. Keep colour as reinforcement only (icon + shape + text).
3. Route routine status through the shared polite announcer; use
   `role="alert"` for criticals; never add a second polite live region.
4. Custom controls follow the read-only (`role="img"`) or interactive
   (native range / `role="slider"` + `aria-valuetext`, ≥24px, arrow keys)
   shape.
5. Keep the global focus ring, or supply a visible replacement.

---

## 5. Per-release manual screen-reader smoke protocol

Automated tools catch ~40–50% of AA issues. Before each release, an operator
runs this ~15-minute pass on **at least one** screen reader per desktop OS the
release ships to.

### Screen readers by platform

| OS | Screen reader | Notes |
|---|---|---|
| Windows | **NVDA** (free) | Primary. Test with Chromium-based WebView2. |
| macOS | **VoiceOver** (built in, ⌘F5) | Test in the WKWebView Tauri shell. |
| Linux | **Orca** | Best-effort; WebKitGTK support varies. |

> **Tauri WebView caveat:** the app runs in the OS WebView (WebView2 on
> Windows, WKWebView on macOS, WebKitGTK on Linux), **not** a standalone
> browser. Accessibility-tree exposure can differ subtly from Chrome/Firefox
> — VoiceOver + WKWebView in particular sometimes lags a live-region update by
> a beat and occasionally double-speaks `aria-atomic` regions. Always do the
> final manual pass in the real Tauri build (`npm run build` + the shell), not
> just `npm run dev` in a browser tab.

### Smoke checklist (run per screen reader)

1. **Launch & landmark.** App opens → SR announces the page title
   ("RytmRandomizer · Cockpit") and finds one `main` landmark. Navigate by
   landmark/heading; confirm the `<h1>` and each panel `<h2>` are reachable.
2. **Tab order.** Tab through the whole cockpit. Focus is always **visible**
   (accent ring) and lands only on real controls, in a sensible order. No
   focus lands on a decorative glyph or a hidden element.
3. **Depth slider.** Tab to "Mutation amount". SR speaks the label and a
   **percentage** (e.g. "45 percent"), not "0.45". Arrow keys change the value
   and the announced percentage updates; Home/End jump to 10%/90%.
4. **Read-only knobs.** Navigate to a Knob. SR announces "<param> value <n>"
   as a graphic. It is not operable (correct — it is a display).
5. **Arm dialog (critical path).**
   - Activate "Arm…". A modal opens; focus moves into the token field; SR
     announces the dialog name + description.
   - Tab cycles **within** the dialog (does not escape to the page behind).
   - Enter a wrong token, confirm. SR **interrupts** to speak the rejection
     (`role="alert"`). Escape closes the dialog and returns focus sensibly.
   - When armed, "ARMED — Disarm" is announced; one-click disarm announces
     "Hardware output disarmed — passive".
6. **Live MIDI monitor.** With activity flowing, the "listening"/"paused"
   badge is announced textually; the flashing dot is silent (decorative).
   Toggle Pause → the badge flips to "paused"; the feed stops. Confirm the
   flash never feels faster than ~3/second.
7. **Connection fault.** Trigger (or simulate) a fault. The fault state is
   announced with text + `⚠`, and a `role="alert"` critical fires — not hue
   alone.
8. **Wizard errors.** Submit an empty required field. The error is announced
   immediately (`role="alert"`), the field is marked invalid, and focus
   handling lets the operator correct it.
9. **Reduced motion.** Enable the OS "reduce motion" setting, reload. No
   non-essential animation plays; transitions are effectively instant.

Log the pass (OS + SR + version + date + any findings) in the release notes.
Any AA failure blocks the release until fixed or explicitly waived with a
tracked follow-up.

---

## 6. Known limitations

- **jsdom cannot compute colour-contrast.** The component-level axe audit
  runs in jsdom, which has no canvas, so axe skips its colour-contrast rule
  there. Contrast is covered instead by the Chromium route scan
  (`a11y_axe_scan.spec.ts`) and the CSS-token architecture test
  (`test_a11y_color_palette_aa.py`).
- **Automated tools are necessary, not sufficient.** They catch structural
  and contrast issues but not "does this actually make sense to a blind
  operator." The manual protocol (§5) exists to close that gap.
- **Tauri WebView parity.** Behaviour verified in Chrome/Firefox may differ
  in the OS WebView; the manual pass is done in the real build for that
  reason.

---

## Cross-references

- `.claude/skills/add-cockpit-panel/SKILL.md` — per-panel a11y acceptance
  checklist (the contract new panels must satisfy).
- `tests/architecture/test_a11y_*.py` — the static enforcement suite.
- `desktop/web/tests/a11y/` — the axe-core component/panel audit + helpers.
- `desktop/web/e2e/a11y_*.spec.ts` — the real-browser route + journey scans.
- `desktop/web/src/a11y/` — the shared live-region / announcer / focus infra.
- `docs/COCKPIT_QUICKSTART.md` — operator-facing cockpit walkthrough.
