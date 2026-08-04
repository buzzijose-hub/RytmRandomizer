/**
 * E2E: the cockpit with NO sidecar at page load (WS-C spec 2, no-gate design).
 *
 * Operator directive: "it can do retries in the background but it should
 * load up the UI. there are plenty of buttons and functionality on the ui
 * to use without being connected."
 *
 * Earlier iterations gated the cockpit behind a session (first a dead
 * "Connecting…" placeholder, then the OfflineShell). Both are gone: the
 * cockpit mounts IMMEDIATELY, degraded surfaces render honest empty states,
 * sidecar-requiring buttons are present-but-disabled, and the
 * ReconnectBanner carries the live retry state (advancing attempt counter,
 * next-dial countdown, Retry now) plus a "Connection help" disclosure with
 * the WS target and per-OS hints. When the sidecar comes up mid-session the
 * app hydrates in place WITHOUT a page reload.
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

test.describe('offline cockpit (no sidecar at load)', () => {
  test('cockpit mounts with no sidecar, banner shows live retry state, and hydrates in place when the sidecar starts', async ({
    page,
    sidecarControl,
  }) => {
    test.setTimeout(90_000);
    const consoleGuard = trackConsoleErrors(page, [WS_DIAL_FAILURE]);

    await page.goto('/');

    // NO GATE: the cockpit mounts immediately, sidecar or not.
    await expect(page.getByTestId('cockpit-root')).toBeVisible();
    await expect(page.getByTestId('header-bar')).toContainText('disconnected');
    await expect(page.getByTestId('snapshot-panel')).toContainText('Waiting for snapshot…');

    // The ReconnectBanner appears over the mounted cockpit (the first dial
    // fails instantly — nothing is listening — so no grace delay applies).
    const banner = page.getByTestId('reconnect-banner');
    await expect(banner).toBeVisible({ timeout: 10_000 });
    await expect(banner.getByRole('alert')).toContainText(/[Ss]idecar/);

    // The retry attempt counter appears and ADVANCES over time (backoff
    // starts at 500 ms, so several attempts land inside this window).
    const retryLine = page.getByTestId('reconnect-banner-retry-line');
    await expect(retryLine).toBeVisible({ timeout: 10_000 });
    const firstObservedAttempt = parseAttempt(await retryLine.textContent());
    expect(firstObservedAttempt).toBeGreaterThan(0);
    await expect(async () => {
      expect(parseAttempt(await retryLine.textContent())).toBeGreaterThan(
        firstObservedAttempt,
      );
    }).toPass({ timeout: 15_000 });

    // "Retry now" is clickable while waiting between dials ('reconnecting'
    // never disables it — only the initial in-flight dial does).
    const retryNow = page.getByTestId('reconnect-banner-retry-now');
    await expect(retryNow).toBeEnabled();
    await retryNow.click();
    // The manual dial also fails (still no sidecar); the loop continues.
    await expect(page.getByTestId('reconnect-banner-status')).toContainText('reconnecting');

    // The pre-session help disclosure names the exact WS target + per-OS hints.
    const help = page.getByTestId('reconnect-banner-help');
    await help.getByText('Connection help').click();
    await expect(page.getByTestId('reconnect-banner-ws-target')).toContainText(
      'ws://127.0.0.1:4317/ws',
    );
    await expect(help).toContainText('python -m rytm_randomizer.cockpit');
    await expect(help).toContainText('lsof -i :4317');
    await expect(help).toContainText('RYTM_RAND_WS_PORT');

    // Plenty of UI is alive offline: the library panel renders its empty
    // state with its buttons PRESENT, and a sidecar-requiring dispatch
    // degrades to an in-panel note (never a crash).
    const library = page.getByTestId('library-panel');
    await expect(library).toContainText('Library not loaded yet — press Load library.');
    await expect(library.getByTestId('library-load')).toBeEnabled();
    await expect(library.getByTestId('library-import')).toBeEnabled();
    await expect(library.getByTestId('library-search-submit')).toBeEnabled();
    await library.getByTestId('library-load').click();
    await expect(library).toContainText('library request failed to send');

    // Sidecar-requiring primary actions are disabled WITH a reason — not hidden.
    await expect(page.getByTestId('arm-open-button')).toBeDisabled();
    await expect(page.getByTestId('arm-open-button')).toHaveAttribute(
      'title',
      'Requires sidecar connection',
    );
    await expect(page.getByTestId('action-regen')).toBeDisabled();
    await expect(page.getByTestId('action-save')).toBeDisabled();

    // Local-only surfaces stay fully interactive (patch genome variants).
    await expect(page.getByTestId('patch-genome-variant')).toHaveText('Variant 1');
    await page.getByRole('button', { name: 'Grow variant' }).click();
    await expect(page.getByTestId('patch-genome-variant')).toHaveText('Variant 2');

    // Plant a marker to prove the hydration below happens WITHOUT a reload.
    await page.evaluate(() => {
      (window as unknown as { __E2E_NO_RELOAD__?: string }).__E2E_NO_RELOAD__ =
        'offline-cockpit';
    });

    // Bring the sidecar up mid-session. The token is injected the moment it
    // is minted — BEFORE the WS port opens (see wizard_fixture docstring),
    // so the client's next successful dial always has credentials in hand.
    await sidecarControl.start({
      env: { RYTM_RAND_MIDI_BACKEND: 'off' },
      onToken: (token) => injectTokenLive(page, token),
    });

    // The app hydrates IN PLACE (backoff is capped at 10 s): the banner
    // clears and the session data replaces the degraded placeholders.
    await expect(page.getByTestId('reconnect-banner')).toHaveCount(0, { timeout: 30_000 });
    await expect(page.getByTestId('cockpit-root')).toBeVisible();
    await expect(page.getByTestId('connection-pill')).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId('header-bar')).not.toContainText('disconnected');
    const safetyRail = page.getByTestId('safety-rail');
    await expect(safetyRail.getByText('Connected', { exact: true })).toBeVisible({
      timeout: 10_000,
    });
    // The previously-gated affordances come alive.
    await expect(page.getByTestId('arm-open-button')).toBeEnabled();
    await expect(page.getByTestId('action-regen')).toBeEnabled();

    // No reload happened: the marker survived the hydration.
    expect(
      await page.evaluate(
        () => (window as unknown as { __E2E_NO_RELOAD__?: string }).__E2E_NO_RELOAD__,
      ),
    ).toBe('offline-cockpit');

    consoleGuard.assertClean();
  });
});
