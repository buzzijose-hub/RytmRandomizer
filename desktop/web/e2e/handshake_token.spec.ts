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
 * See also:
 * - `tests/architecture/test_frontend_matches_handshake_contract.py`
 *   (catches the violation at the Python arch-test layer in <5s)
 * - `desktop/web/tests/ws-client.test.ts` § handshake branches
 *   (catches it at the unit-test layer in <100ms)
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
    // fails, the placeholder ("Connecting…") stays on screen forever.
    await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });
  });

  test('without a token the cockpit stays on the connecting placeholder', async ({
    page,
    context,
  }) => {
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

    // The placeholder root container (`<main class="cockpit-placeholder">`)
    // should stay visible — `cockpit-root` must NOT mount because no
    // `session_status` event ever arrives (the WS gets closed at 1008
    // before the bootstrap fires). We target the placeholder by its
    // class to avoid the strict-mode collision with the
    // `status: reconnecting` chip that also contains the word
    // "Connecting" once the client transitions to the reconnect loop.
    const placeholder = page.locator('main.cockpit-placeholder');
    await expect(placeholder).toBeVisible({ timeout: 3_000 });

    // And `cockpit-root` should NOT be visible.
    await expect(page.getByTestId('cockpit-root')).not.toBeVisible();
  });
});
