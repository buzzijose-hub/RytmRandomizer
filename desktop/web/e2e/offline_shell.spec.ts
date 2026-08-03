/**
 * E2E: the offline shell — NO sidecar at page load (WS-C spec 2).
 *
 * Before WS-A the app showed a dead "Connecting…" placeholder forever when
 * the sidecar was unreachable. Now it must render the OfflineShell: a live
 * status badge, a visibly-advancing retry counter with a next-dial
 * countdown, a "Retry now" action, and the WS target + per-OS help — and
 * when the sidecar comes up mid-session the app must recover to the
 * cockpit WITHOUT a page reload.
 *
 * This spec supersedes the old "placeholder stays forever" assertion in
 * `handshake_token.spec.ts` (rewritten in the same workstream).
 *
 * Console-error allowlist: Chromium logs one error line per failed WS dial
 * while no sidecar is listening. That noise is the feature under test
 * (the client retries forever), so it is explicitly allowed; anything
 * else fails the spec.
 */

import { trackConsoleErrors, WS_DIAL_FAILURE } from './fixtures/console_guard';
import { expect, injectTokenLive, test } from './fixtures/wizard_fixture';

/** Parse the attempt counter out of the retry line ("Retry attempt N — …"). */
function parseAttempt(text: string | null): number {
  const match = /Retry attempt (\d+)/.exec(text ?? '');
  return match === null ? 0 : Number(match[1]);
}

test.describe('offline shell (no sidecar at load)', () => {
  test('shows live retry state and recovers to the cockpit without a reload', async ({
    page,
    sidecarControl,
  }) => {
    test.setTimeout(90_000);
    const consoleGuard = trackConsoleErrors(page, [WS_DIAL_FAILURE]);

    await page.goto('/');

    // The offline shell renders — not a dead placeholder.
    const shell = page.getByTestId('offline-shell');
    await expect(shell).toBeVisible();
    await expect(shell).toContainText('Waiting for the RytmRandomizer sidecar');

    // The first dial fails (nothing listening), so the status must reach
    // 'reconnecting' — proof the retry loop is alive and visible.
    await expect(page.getByTestId('offline-status')).toContainText('reconnecting', {
      timeout: 10_000,
    });

    // The shell names the exact WS target it is dialing.
    await expect(page.getByTestId('offline-ws-target')).toContainText(
      'ws://127.0.0.1:4317/ws',
    );

    // The retry attempt counter appears and ADVANCES over time (backoff
    // starts at 500 ms, so several attempts land inside this window).
    const retryLine = page.getByTestId('offline-retry-line');
    await expect(retryLine).toBeVisible({ timeout: 10_000 });
    const firstObservedAttempt = parseAttempt(await retryLine.textContent());
    expect(firstObservedAttempt).toBeGreaterThan(0);
    await expect(async () => {
      expect(parseAttempt(await retryLine.textContent())).toBeGreaterThan(
        firstObservedAttempt,
      );
    }).toPass({ timeout: 15_000 });

    // "Retry now" is clickable while waiting between dials ('reconnecting'
    // never disables it — only an in-flight first dial does).
    const retryNow = page.getByTestId('offline-retry-now');
    await expect(retryNow).toBeEnabled();
    await retryNow.click();
    // The manual dial also fails (still no sidecar); the loop continues.
    await expect(page.getByTestId('offline-status')).toContainText('reconnecting');

    // Plant a marker to prove the recovery below happens WITHOUT a reload.
    await page.evaluate(() => {
      (window as unknown as { __E2E_NO_RELOAD__?: string }).__E2E_NO_RELOAD__ =
        'offline-shell';
    });

    // Bring the sidecar up mid-session. The token is injected the moment it
    // is minted — BEFORE the WS port opens (see wizard_fixture docstring),
    // so the client's next successful dial always has credentials in hand.
    await sidecarControl.start({
      env: { RYTM_RAND_MIDI_BACKEND: 'off' },
      onToken: (token) => injectTokenLive(page, token),
    });

    // The app recovers to the cockpit on its own (backoff is capped at 10 s).
    await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId('offline-shell')).toHaveCount(0);

    // No reload happened: the marker survived the recovery.
    expect(
      await page.evaluate(
        () => (window as unknown as { __E2E_NO_RELOAD__?: string }).__E2E_NO_RELOAD__,
      ),
    ).toBe('offline-shell');

    consoleGuard.assertClean();
  });
});
