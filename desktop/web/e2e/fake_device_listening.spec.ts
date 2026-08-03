/**
 * E2E: the fake-device seam drives the LISTENING presentation (WS-C spec 3).
 *
 * `RYTM_RAND_MIDI_BACKEND=fake` selects the list-only FakePortEnumerator, so
 * the passive ConnectionManager reaches the `listening` phase with zero real
 * hardware — exactly what WS-B built the seam for. This spec pins:
 *
 *  - the device rail's listening presentation names the fake port and drops
 *    the "No hardware detected" banner + preview badge;
 *  - the arm dialog's port select offers the enumerated fake port (we open
 *    the dialog, assert the option, and CANCEL — never arm, never send);
 *  - `RYTM_RAND_FAKE_PORTS` overrides the enumeration (both custom names
 *    appear in the arm select and in the Connection Doctor's counts).
 *
 * No console-error allowlist: the sidecar is up for the whole journey.
 */

import type { Page } from '@playwright/test';

import { trackConsoleErrors } from './fixtures/console_guard';
import { expect, test } from './fixtures/wizard_fixture';

const FAKE_RYTM_PORT = 'Elektron Analog Rytm MKII';
const CUSTOM_PORT = 'Custom Port X';

/** Real (non-placeholder) option values currently offered by the arm select. */
async function armSelectPortOptions(page: Page): Promise<string[]> {
  return page
    .getByTestId('arm-port-select')
    .locator('option')
    .evaluateAll((options) =>
      options.map((option) => (option as HTMLOptionElement).value).filter((value) => value !== ''),
    );
}

test.describe('fake device — default Elektron-shaped port', () => {
  test.use({ sidecarEnv: { RYTM_RAND_MIDI_BACKEND: 'fake' } });

  test('rail reaches listening with the fake Rytm named; arm select offers it', async ({
    page,
    sidecar: _sidecar,
  }) => {
    test.setTimeout(60_000);
    const consoleGuard = trackConsoleErrors(page);

    await page.goto('/');
    await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });

    // Phase reaches listening (fake enumeration matches the Elektron stems).
    await expect(page.getByTestId('connection-pill')).toHaveText(/listening/, {
      timeout: 15_000,
    });

    // Listening presentation: no "No hardware detected" banner, no preview
    // badge — the rail names the real (fake-enumerated) port instead.
    await expect(
      page.getByTestId('device-card-analog-rytm-mk2-hardware-banner'),
    ).toHaveCount(0);
    await expect(page.getByText('Preview — mock data')).toHaveCount(0);
    await expect(page.getByTestId('device-rail-rytm-port-state')).toContainText(
      FAKE_RYTM_PORT,
    );

    // Arm dialog: the enumerated fake port is offered. Open → assert → CANCEL.
    // Deliberately no arm/confirm here — the seam is list-only and this spec
    // must never exercise a transmit path.
    await page.getByTestId('arm-open-button').click();
    await expect(page.getByTestId('arm-dialog')).toBeVisible();
    await expect(page.getByTestId('arm-no-ports')).toHaveCount(0);
    expect(await armSelectPortOptions(page)).toEqual([FAKE_RYTM_PORT]);
    await page.getByTestId('arm-cancel-button').click();
    await expect(page.getByTestId('arm-dialog')).toHaveCount(0);
    // Still passive after the cancel.
    await expect(page.getByTestId('arm-open-button')).toBeVisible();

    consoleGuard.assertClean();
  });
});

test.describe('fake device — RYTM_RAND_FAKE_PORTS override', () => {
  test.use({
    sidecarEnv: {
      RYTM_RAND_MIDI_BACKEND: 'fake',
      RYTM_RAND_FAKE_PORTS: `${FAKE_RYTM_PORT},${CUSTOM_PORT}`,
    },
  });

  test('both overridden ports appear in enumeration (arm select + doctor)', async ({
    page,
    sidecar: _sidecar,
  }) => {
    test.setTimeout(60_000);
    const consoleGuard = trackConsoleErrors(page);

    await page.goto('/');
    await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId('connection-pill')).toHaveText(/listening/, {
      timeout: 15_000,
    });

    // Both fake ports are offered to the operator in the arm select.
    await page.getByTestId('arm-open-button').click();
    await expect(page.getByTestId('arm-dialog')).toBeVisible();
    expect(await armSelectPortOptions(page)).toEqual([FAKE_RYTM_PORT, CUSTOM_PORT]);
    await page.getByTestId('arm-cancel-button').click();
    await expect(page.getByTestId('arm-dialog')).toHaveCount(0);

    // The Doctor's honest enumeration counts both, and matches the Elektron one.
    const doctor = page.getByTestId('connection-doctor');
    await doctor.getByTestId('doctor-refresh').click();
    await expect(doctor).toContainText('2 MIDI input(s) visible');
    await expect(doctor).toContainText('2 MIDI output(s) visible');
    await expect(doctor).toContainText(`Elektron output matched: ${FAKE_RYTM_PORT}`);

    consoleGuard.assertClean();
  });
});
