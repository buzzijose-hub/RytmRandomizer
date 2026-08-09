/**
 * E2E: sidecar dies mid-session → visible retries → restart → recovery
 * without a reload (WS-C spec 4).
 *
 * ## Behavior notes
 *
 * 1. **The cockpit stays mounted AND the ReconnectBanner appears.** The
 *    store's `sessionStatus` slice is deliberately never cleared on
 *    disconnect (losing panel context mid-performance is worse than
 *    stale values). The loud reconnect surface is the fixed-position
 *    ReconnectBanner App always renders (it self-gates): mid-session it
 *    carries the advancing retry-attempt counter, the next-dial
 *    countdown, and a Retry-now action — but NOT the pre-session
 *    "Connection help" disclosure — and it disappears on recovery. The
 *    SafetyRail's WebSocket row + operator log remain the quiet,
 *    always-on truth underneath.
 *
 * 2. **A restarted sidecar mints a NEW WS token** (`_provision_token`
 *    always regenerates; the old one is deliberately dead). The browser
 *    client resolves its token lazily on every dial from
 *    `window.__RYTM_RAND_WS_TOKEN__` / localStorage, so a live injection
 *    of the fresh token IS picked up without a reload — this spec does
 *    exactly that (re-read the token file, inject, recover). But nothing
 *    in the product updates that storage: a real operator whose sidecar
 *    restarted (while the webview stayed up) is stuck in an auth-reject
 *    loop until the shell relaunches/reloads and re-injects. That
 *    shell-side re-injection remains a real product question for the
 *    PR body (out of scope here).
 *
 * Console-error allowlist: failed WS dials while the sidecar is down are
 * the reconnect loop working as designed — allowed. Everything else fails.
 */

import { trackConsoleErrors, WS_DIAL_FAILURE } from './fixtures/console_guard';
import { expect, injectTokenLive, primeToken, test } from './fixtures/wizard_fixture';

test.describe('reconnect journey (sidecar killed mid-session)', () => {
  test('cockpit reports the drop truthfully and recovers after restart + fresh token', async ({
    page,
    sidecarControl,
  }) => {
    test.setTimeout(120_000);
    const consoleGuard = trackConsoleErrors(page, [WS_DIAL_FAILURE]);

    // Boot with backend off (deterministic zero-hardware phase) and prime
    // the token before the first navigation.
    const first = await sidecarControl.start({
      env: { RYTM_RAND_MIDI_BACKEND: 'off' },
      onToken: (token) => primeToken(page, token),
    });

    await page.goto('/');
    await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });
    const safetyRail = page.getByTestId('safety-rail');
    await expect(safetyRail.getByText('Connected', { exact: true })).toBeVisible({
      timeout: 10_000,
    });
    // Under the no-gate design, cockpit-root + WS "Connected" no longer
    // imply the session hydrated (the cockpit mounts unconditionally).
    // Wait for a session-dependent surface before killing, or the banner
    // legitimately renders its PRE-session copy and the mid-session
    // assertions below race.
    await expect(page.getByTestId('connection-pill')).toBeVisible({ timeout: 10_000 });

    // Marker to prove recovery happens without a page reload.
    await page.evaluate(() => {
      (window as unknown as { __E2E_NO_RELOAD__?: string }).__E2E_NO_RELOAD__ = 'reconnect';
    });

    // Crash the sidecar (SIGKILL — no graceful close frame).
    await sidecarControl.stop('SIGKILL');

    // DESIGN DECISION (note 1): the cockpit stays mounted — sessionStatus
    // is never cleared — and the ReconnectBanner appears as the loud,
    // actionable reconnect surface over the stale data.
    await expect(safetyRail.getByText('Reconnecting', { exact: true })).toBeVisible({
      timeout: 15_000,
    });
    await expect(page.getByTestId('cockpit-root')).toBeVisible();
    await expect(page.getByTestId('operator-log-list')).toContainText(
      'WebSocket reconnecting',
    );

    // The banner is visible, alert-shaped, and actionable — in its
    // MID-SESSION form (no pre-session connection-help disclosure).
    const banner = page.getByTestId('reconnect-banner');
    await expect(banner).toBeVisible({ timeout: 10_000 });
    await expect(banner.getByRole('alert')).toContainText('Sidecar connection lost');
    await expect(banner.getByTestId('reconnect-banner-retry-now')).toBeVisible();
    await expect(page.getByTestId('reconnect-banner-help')).toHaveCount(0);

    // The retry attempt counter is visible and ADVANCING (backoff loop is
    // really running: 0.5s, 1s, 2s... so attempt ≥ 2 lands within seconds).
    const retryLine = page.getByTestId('reconnect-banner-retry-line');
    await expect(retryLine).toContainText(/Retry attempt \d+/, { timeout: 10_000 });
    const readAttempt = async (): Promise<number> => {
      const text = (await retryLine.textContent().catch(() => '')) ?? '';
      const match = /Retry attempt (\d+)/.exec(text);
      return match === null ? 0 : Number(match[1]);
    };
    await expect.poll(readAttempt, { timeout: 20_000 }).toBeGreaterThanOrEqual(2);

    // Restart on the same port. The new launch overwrites the token file
    // with a FRESH token (finding 2); inject it into the live page the
    // moment it is minted — before the WS port opens — so the client's
    // next dial authenticates without a reload.
    await sidecarControl.start({
      env: { RYTM_RAND_MIDI_BACKEND: 'off' },
      previousToken: first.token,
      onToken: (token) => injectTokenLive(page, token),
    });

    // Autonomous recovery: WebSocket row returns to Connected, the
    // ReconnectBanner disappears, and the session surface is fully alive
    // again (fresh session_status arrived).
    await expect(safetyRail.getByText('Connected', { exact: true })).toBeVisible({
      timeout: 30_000,
    });
    await expect(page.getByTestId('reconnect-banner')).toHaveCount(0, { timeout: 10_000 });
    await expect(page.getByTestId('cockpit-root')).toBeVisible();
    await expect(page.getByTestId('connection-pill')).toHaveText(/searching/, {
      timeout: 15_000,
    });

    // No reload happened.
    expect(
      await page.evaluate(
        () => (window as unknown as { __E2E_NO_RELOAD__?: string }).__E2E_NO_RELOAD__,
      ),
    ).toBe('reconnect');

    // Live-but-Passive rule 8: arming never survives a disconnect. We never
    // armed here (backend off has no ports), and the recovered session is
    // passive: the Arm affordance is present, not an armed/disarm state.
    await expect(page.getByTestId('arm-open-button')).toBeVisible();

    consoleGuard.assertClean();
  });
});
