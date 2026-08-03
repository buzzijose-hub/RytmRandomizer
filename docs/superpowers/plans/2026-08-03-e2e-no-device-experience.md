# E2E platform expansion + no-device experience

Date: 2026-08-03
Status: in-flight
**Base:** `modularize-v1.34` @ `a7898be`
**Branch:** `feat/e2e-no-device`
**Driver:** operator report — "I don't have any devices with me and I can't even
use the app. There are lots of functions I can do without a device.
Connectivity retries should be on-going, managing my sound library, etc."

## Findings that shape this plan

A full source investigation (connection lifecycle, UI gating, library store,
e2e fixtures) established:

1. **The retry story is already correct — but invisible.** The WS client
   retries forever with exponential backoff capped at 10 s
   (`desktop/web/src/ws/client.ts` — `maxReconnectAttempts` defaults to
   `Infinity`), and the sidecar's `ConnectionManager.run()` re-enumerates
   ports every 2 s unconditionally (`rytm_randomizer/cockpit/device/connection.py`).
   Neither loop ever gives up. The operator simply cannot see any of it.
2. **One line blocks the whole app.** `App.tsx` returns a dead
   "Connecting…" placeholder while `sessionStatus === null` — which happens
   when the *sidecar* is unreachable, not when *devices* are absent. Every
   device-independent feature (library, profiles, wizard, reports, exports,
   history) sits behind that gate. The README's promise ("an honest empty
   state + the Connection Doctor") is broken exactly when it matters: the
   Doctor is behind the gate too.
3. **The sound library never needed hardware.** `LibraryPanel` (list,
   search, tag, import-captures) is backed by on-disk JSON; the only
   device-requiring operation is capture-from-device.
4. **`DeviceRail` lies by omission.** It renders hardcoded mock states and
   `available_ports: []`; it never reflects `connection.phase` or real
   enumeration, so it cannot say "no hardware detected."
5. **The e2e platform already exists** (Playwright + Chromium, 10 specs,
   per-test sidecar spawn with isolated config dirs, CI job with report
   upload) — but **zero specs cover no-device behavior**, and
   `handshake_token.spec.ts` pins the dead-end placeholder as *correct*.
6. **There is no fake-device seam.** `_build_port_enumerator()` is a closed
   three-way switch (real / null / null-on-missing-mido). Nothing can make
   the sidecar present a fake Rytm, so `listening`-phase behavior is
   untestable without hardware. The `PortEnumerator` Protocol (two methods,
   list-only, no transmit) is already the right shape for one.

## Workstreams

### WS-A — offline shell + visible retries + honest DeviceRail (product)

- Replace the `App.tsx` dead placeholder with an **offline shell**: the
  header, a client-side Connection Doctor view (WS target, attempt count,
  next-retry countdown, per-OS hints), and a manual "Retry now" button.
  Auto-retry continues regardless (unchanged client behavior — just made
  visible).
- Drive `DeviceRail` from `connection.phase` + `available_inputs` /
  `available_outputs`: `searching` renders "no hardware detected — still
  scanning (every 2 s)" instead of mock labels; `listening` names the real
  port(s).
- Keep arming exactly as gated as today (no port → unreachable). No change
  to the Live-but-Passive model; inputs/enumeration stay free, transmit
  stays behind ArmedApply.

### WS-B — fake-device enumerator seam (test enabler)

- `RYTM_RAND_MIDI_BACKEND=fake` → a `FakePortEnumerator` returning
  Elektron-shaped port names (override via `RYTM_RAND_FAKE_PORTS`, comma
  separated). List-only: the Protocol has no open/send surface, so this
  cannot create a transmit path; architecture enforcement modules must stay
  green with no allowlist growth.
- This deliberately makes `listening` phase reachable in CI with zero
  hardware, which un-blocks device-present e2e (device rail rendering,
  arm-flow reachability) and phase-transition tests (fake ports appear /
  disappear between polls).

### WS-C — e2e specs (the feature)

New specs under `desktop/web/e2e/`:

1. `no_device_journey.spec.ts` — sidecar up, zero ports (backend `off`):
   phase reaches `searching` and is *announced* in the UI; library
   list/search/tag/import works; wizard completes; Connection Doctor shows
   honest enumeration (`[]`) + driver hint; arm flow is unreachable.
2. `offline_shell.spec.ts` — **no sidecar**: offline shell renders (not a
   dead placeholder), retry counter visibly advances, "Retry now" fires,
   and when the sidecar comes up mid-test the app recovers without reload.
   Supersedes the "placeholder forever" assertion in
   `handshake_token.spec.ts` (auth-failure case remains).
3. `fake_device_listening.spec.ts` — backend `fake`: phase reaches
   `listening`, DeviceRail names the fake port, arm modal lists it.
4. `reconnect_journey.spec.ts` — kill sidecar mid-session → UI shows
   `reconnecting` with ongoing retries → restart sidecar → session
   recovers; arming never survives the drop (Live-but-Passive rule 8).
5. `library_management.spec.ts` — no device: seed capture files into the
   isolated config dir, import, search, tag; assert persistence across a
   sidecar restart.

### WS-D — pipeline + local ergonomics

- CI: new specs run in the existing `desktop-web-e2e` job (workers: 1
  constraint respected — specs stay per-test-sidecar isolated). Budget
  check: suite must stay under ~10 min.
- Local: document `npm run e2e` / `npx playwright test --ui` in
  `docs/COCKPIT_QUICKSTART.md`; the suite must pass on macOS with only
  `.venv` + `npm ci` + `npx playwright install chromium`.
- Playwright MCP is optional authoring tooling, not a dependency:
  `claude mcp add playwright -- npx @playwright/mcp@latest` gives agent
  sessions an interactive browser for debugging specs. The suite itself
  never requires MCP.

## Sequencing

WS-B (small, unblocks C3/C4) and WS-A (independent React work) run in
parallel with disjoint file scopes; WS-C lands after both; WS-D closes.
One bundled PR per the cascade-merge rule.

## Gates

Standard 18-gate conformance. Notables: Gate 1 (100 % branch on touched
Python; vitest 100 % thresholds on touched TS), Gate 2 untouched (no
engines/runners/parity surface), live-but-passive enforcement modules green
with no allowlist growth (WS-B is list-only), README/diagram freshness for
the new operator-visible states, `handshake_token.spec.ts` rewrite is a
deliberate behavior change documented in the PR body.
