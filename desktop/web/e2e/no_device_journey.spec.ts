/**
 * E2E: the full no-device operator journey (WS-C spec 1).
 *
 * Sidecar up with `RYTM_RAND_MIDI_BACKEND=off` → the enumerator sees zero
 * ports, so the passive ConnectionManager parks the phase at `searching`.
 * The operator report that drove this plan was "I can't even use the app
 * without a device" — this spec pins the fixed behavior:
 *
 *  - the cockpit mounts AND the session hydrates (session status arrives
 *    even with zero hardware) — no ReconnectBanner in sight;
 *  - the header pill + device rail reach the honest `searching`
 *    presentation ("No hardware detected — still scanning (every 2 s)")
 *    with the "Preview — mock data" badges;
 *  - the library panel works against the empty store (list + search);
 *  - the Connection Doctor reports the honest empty enumeration and the
 *    per-OS driver hint after Refresh;
 *  - the arm dialog opens but CANNOT complete (no ports → confirm stays
 *    disabled) — Live-but-Passive gating unchanged;
 *  - the whole journey produces zero browser console errors (no
 *    allowlist: with the sidecar up throughout, even WS noise is a bug).
 */

import { trackConsoleErrors } from './fixtures/console_guard';
import { expect, test } from './fixtures/wizard_fixture';

test.use({ sidecarEnv: { RYTM_RAND_MIDI_BACKEND: 'off' } });

test.describe('no-device journey (backend off)', () => {
  test('cockpit mounts, reports searching honestly, library/doctor work, arm cannot complete', async ({
    page,
    sidecar,
  }) => {
    test.setTimeout(60_000);
    expect(sidecar.token.length).toBeGreaterThan(20);
    const consoleGuard = trackConsoleErrors(page);

    await page.goto('/');

    // The cockpit mounts and the session hydrates: no device ≠ no session.
    // With the sidecar up throughout, the ReconnectBanner never appears
    // (the initial-connect grace absorbs the fast healthy dial).
    await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId('reconnect-banner')).toHaveCount(0);

    // Header pill reaches the searching phase (first poll lands within 2 s).
    await expect(page.getByTestId('connection-pill')).toHaveText(/searching/, {
      timeout: 10_000,
    });

    // Device rail: honest no-hardware banner on the Rytm card + preview
    // badges on both cards (the rail renders mock data, and says so).
    await expect(
      page.getByTestId('device-card-analog-rytm-mk2-hardware-banner'),
    ).toContainText('No hardware detected — still scanning (every 2 s)');
    await expect(page.getByText('Preview — mock data')).toHaveCount(2);

    // Library panel against the empty store: load + search, no crash.
    const library = page.getByTestId('library-panel');
    await library.getByTestId('library-load').click();
    await expect(library).toContainText('library loaded');
    await expect(library.getByText('0 record(s)')).toBeVisible();
    await library.getByTestId('library-search-input').fill('warehouse');
    await library.getByTestId('library-search-submit').click();
    await expect(library).toContainText('search complete: warehouse');
    await expect(library.getByText('0 record(s)')).toBeVisible();

    // Connection Doctor: refresh → honest empty enumeration + driver hint.
    const doctor = page.getByTestId('connection-doctor');
    await doctor.getByTestId('doctor-refresh').click();
    await expect(doctor).toContainText('diagnostics refreshed');
    await expect(doctor).toContainText('no MIDI inputs visible — check cable and driver');
    await expect(doctor).toContainText('no MIDI outputs visible — check cable and driver');
    await expect(doctor).toContainText('no Elektron output matched');
    await expect(doctor).toContainText('Driver hint');
    // The phase badge inside the Doctor mirrors the searching phase.
    await expect(doctor.getByText('searching', { exact: false }).first()).toBeVisible();

    // Arm dialog: reachable, but arming cannot complete without a port.
    await page.getByTestId('arm-open-button').click();
    await expect(page.getByTestId('arm-dialog')).toBeVisible();
    await expect(page.getByTestId('arm-no-ports')).toBeVisible();
    // Only the "Select a port…" placeholder — zero real ports offered.
    await expect(page.getByTestId('arm-port-select').locator('option')).toHaveCount(1);
    await expect(page.getByTestId('arm-confirm-button')).toBeDisabled();
    await page.getByTestId('arm-cancel-button').click();
    await expect(page.getByTestId('arm-dialog')).toHaveCount(0);
    await expect(page.getByTestId('arm-open-button')).toBeVisible();

    // Crash net: the whole journey must be console-error-free. No allowlist —
    // with the sidecar alive throughout, any WS failure line is a regression.
    consoleGuard.assertClean();
  });
});
