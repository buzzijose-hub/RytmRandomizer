/**
 * E2E coverage for the PR #113 handshake contract (CODE_REVIEW.md C1).
 *
 * The cockpit WS endpoint requires:
 *   1. The browser to negotiate the `rytm-rand-cockpit-v1` subprotocol.
 *   2. The client to send `{type:"hello", token:"<urlsafe>"}` as the
 *      first frame, where the token equals the per-launch value the
 *      sidecar minted at boot.
 *
 * An earlier PR #113 push regressed all 5 wizard E2E tests because the
 * frontend was never updated to either pin the subprotocol or send the
 * hello frame. The Python unit tests passed (TestClient bypasses both),
 * the desktop-web unit tests passed (mock WebSocket factory), and only
 * the real-browser → real-sidecar integration failed.
 *
 * These specs codify the contract end-to-end so a future drift on either
 * side trips at the cheapest layer that can catch it (E2E with full
 * browser + full sidecar, not 30 seconds of unit-test mocks).
 *
 * ## Rewritten for the WS-A offline shell (e2e-no-device plan)
 *
 * The old "without a token the cockpit stays on the connecting
 * placeholder" test pinned the DEAD placeholder (`main.cockpit-placeholder`)
 * as correct behavior. WS-A replaced that placeholder with the live
 * OfflineShell, so the auth-failure cases now assert:
 *
 * - **No token at all:** the client deliberately withholds the `hello`
 *   frame (`sendHandshake` refuses to send an empty token). The server
 *   no longer waits forever: `_perform_handshake` enforces a first-frame
 *   deadline (`HANDSHAKE_FIRST_FRAME_TIMEOUT_SECONDS`, 10 s in
 *   production) and then rejects with `{ok:false, code:auth_required}` +
 *   close 1008 — so the shell cycles through a VISIBLE reconnecting
 *   loop instead of parking on a false "connected". The spec shrinks the
 *   deadline to 1 s via the sidecar's test-only
 *   `RYTM_RAND_WS_HANDSHAKE_TIMEOUT_SECONDS` env override so the loop
 *   is observable in seconds, not tens of seconds. The cockpit never
 *   mounts.
 * - **Wrong token:** the server rejects with `{ok:false, code:auth_failed}`
 *   and closes at 1008; the client enters its reconnect loop, so the
 *   shell reaches `reconnecting` with a visibly-advancing retry line.
 *   The cockpit never mounts.
 *
 * See also:
 * - `tests/architecture/test_frontend_matches_handshake_contract.py`
 *   (catches the violation at the Python arch-test layer in <5s)
 * - `desktop/web/tests/ws-client.test.ts` § handshake branches
 *   (catches it at the unit-test layer in <100ms)
 * - `e2e/offline_shell.spec.ts` (the no-sidecar half of the story)
 */

import { test, expect } from './fixtures/wizard_fixture';

test.describe('handshake token (PR #113 / C1)', () => {
  test('with a valid token the cockpit-root mounts (handshake succeeds)', async ({
    page,
    sidecar,
  }) => {
    // Sanity-check the fixture itself: it minted a non-empty token and
    // wrote it to the file the sidecar created.
    expect(sidecar.token.length).toBeGreaterThan(20);

    await page.goto('/');

    // `cockpit-root` only mounts after `sessionStatus` arrives, which
    // requires a successful handshake + the bootstrap-event set from
    // `_perform_handshake` + `emit_initial_events`. If the handshake
    // fails, the offline shell stays on screen instead.
    await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });
  });

  test.describe('without a token (server first-frame deadline)', () => {
    // Test-only override (documented in `ws/server.py`): shrink the 10 s
    // production deadline to 1 s so the reject → close(1008) → redial loop
    // cycles fast enough to observe within the spec budget.
    test.use({ sidecarEnv: { RYTM_RAND_WS_HANDSHAKE_TIMEOUT_SECONDS: '1' } });

    test('without a token the server closes at the deadline and the shell keeps retrying', async ({
      page,
      context,
      sidecar: _sidecar,
    }) => {
      // Three sequential loop observations at a 1 s deadline fit easily in
      // 45 s but not always in the 30 s default when the runner is loaded.
      test.setTimeout(45_000);
      // Override the init script the fixture set up so the browser sees no
      // window.__RYTM_RAND_WS_TOKEN__. The sidecar is still running with
      // its mandatory token — we just refuse to present one client-side.
      // localStorage is also cleared so the resolver falls back to null.
      await context.addInitScript(() => {
        (window as unknown as { __RYTM_RAND_WS_TOKEN__?: undefined }).__RYTM_RAND_WS_TOKEN__ =
          undefined;
        try {
          window.localStorage.removeItem('rytm-rand-ws-token');
        } catch {
          // jsdom-style envs may not expose localStorage; that's fine.
        }
      });

      await page.goto('/');

      // The live OfflineShell renders (WS-A) — no dead placeholder anymore.
      await expect(page.getByTestId('offline-shell')).toBeVisible({ timeout: 5_000 });

      // FIXED behavior: the token-less client withholds its hello frame,
      // and the server now closes the parked socket at the first-frame
      // deadline (auth_required + 1008) instead of waiting forever. The
      // client re-dials, parks again, is closed again — a VISIBLE loop:
      // the shell oscillates through `reconnecting` rather than resting
      // on a false "connected".
      await expect(page.getByTestId('offline-status')).toContainText('reconnecting', {
        timeout: 15_000,
      });

      // Prove it is a LOOP, not a one-off close: the next cycle dials
      // (back to connected while the deadline runs) and is closed again.
      await expect(page.getByTestId('offline-status')).toContainText('connected', {
        timeout: 15_000,
      });
      await expect(page.getByTestId('offline-status')).toContainText('reconnecting', {
        timeout: 15_000,
      });

      // And `cockpit-root` must NOT mount — no session_status can ever
      // arrive without a completed handshake.
      await expect(page.getByTestId('cockpit-root')).not.toBeVisible();
    });
  });

  test('with a WRONG token the server rejects at 1008 and the shell keeps retrying', async ({
    page,
    context,
    sidecar: _sidecar,
  }) => {
    // Present a syntactically-plausible but wrong token: the client DOES
    // send the hello frame, and the server must reject it (auth_failed)
    // and close at 1008 — landing the client in its reconnect loop.
    await context.addInitScript(() => {
      const wrong = 'e2e-definitely-not-the-minted-token';
      (window as unknown as { __RYTM_RAND_WS_TOKEN__?: string }).__RYTM_RAND_WS_TOKEN__ = wrong;
      try {
        window.localStorage.setItem('rytm-rand-ws-token', wrong);
      } catch {
        // jsdom-style envs may not expose localStorage; that's fine.
      }
    });

    await page.goto('/');

    await expect(page.getByTestId('offline-shell')).toBeVisible({ timeout: 5_000 });
    // The reject → close → redial loop is visible: reconnecting status and
    // a retry attempt line.
    await expect(page.getByTestId('offline-status')).toContainText('reconnecting', {
      timeout: 10_000,
    });
    await expect(page.getByTestId('offline-retry-line')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId('cockpit-root')).not.toBeVisible();
  });
});
