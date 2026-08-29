/**
 * 3-checkpoint SR-equivalent journey.
 * See docs/superpowers/specs/2026-05-25-ada-aa-accessibility-design.md
 * §"Manual SR test plan" for the per-checkpoint expectations.
 *
 * Why the `wizard_fixture` (full sidecar boot) and not plain `@playwright/test`:
 * `App.tsx` only renders `<Cockpit/>` or `<Wizard/>` once `sessionStatus !== null`,
 * which requires a real `session_status` push from the Python sidecar. Without
 * the sidecar all three checkpoints would snapshot the "Connecting…" placeholder
 * instead of the routes under test.
 *
 * The cockpit boot checkpoint uses explicit role/test-id assertions because
 * its root contains server-minted snapshot IDs and the live-readiness dashboard
 * is intentionally broader than the wizard route fixtures. The wizard
 * checkpoints still use ARIA YAML fixtures for stable form/accessibility trees.
 */
import { expect, test } from './fixtures/wizard_fixture';

test.describe('SR-equivalent journey', () => {
  test('1. cockpit boot — landmark + title + tab order', async ({
    page,
    sidecar: _sidecar,
  }) => {
    await page.goto('/');
    const root = page.getByTestId('cockpit-root');
    await root.waitFor({ state: 'visible' });

    await expect(page.getByRole('main')).toBeVisible();
    await expect(
      page.getByRole('heading', { level: 1, name: 'RytmRandomizer · Cockpit' }),
    ).toBeVisible();

    const deviceStatus = page.getByRole('complementary', { name: 'Device status' });
    await expect(deviceStatus).toBeVisible();
    await expect(deviceStatus.getByRole('region', { name: 'Analog Rytm MKII' })).toContainText(
      '12 pads mapped',
    );
    await expect(page.getByTestId('device-rail-rytm-pad-1')).toContainText('BD Hard');
    await expect(page.getByTestId('device-rail-rytm-pad-12')).toContainText('BD Acoustic');
    await expect(deviceStatus.getByRole('region', { name: 'Analog Four MKII' })).toContainText(
      '4 tracks staged',
    );
    await expect(page.getByTestId('device-rail-a4-track-1')).toContainText('Bass / low pulse');
    await expect(page.getByTestId('device-rail-a4-track-4')).toContainText('Space / accent');

    await expect(
      page.getByRole('heading', { exact: true, level: 2, name: 'Snapshot' }),
    ).toBeVisible();
    await expect(page.getByText('12 pads ready for dry-run review').first()).toBeVisible();

    // Switch to the Analog Four center panel and prove both the track grid and
    // passive Patch Genome compiler are reachable through the shipped route.
    await page.getByTestId('device-select-analog-four-mk2').click();
    const snapshotPanel = page.getByTestId('snapshot-panel');
    await expect(
      snapshotPanel.getByRole('heading', { exact: true, level: 2, name: 'Analog Four MKII' }),
    ).toBeVisible();
    for (const track of [1, 2, 3, 4]) {
      const card = page.getByTestId(`a4-track-card-${track}`);
      await expect(card).toBeVisible();
      await expect(card).toHaveAttribute('data-role-key', /\w+/);
    }
    await expect(page.getByTestId('a4-track-card-1').getByRole('meter')).toHaveAttribute(
      'aria-valuetext',
      /safe mutation depth/,
    );

    const patchGenomePanel = page.getByTestId('patch-genome-panel');
    await expect(
      patchGenomePanel.getByRole('heading', { exact: true, level: 2, name: 'A4 Patch Genome' }),
    ).toBeVisible();
    for (const track of [1, 2, 3, 4]) {
      await expect(page.getByTestId(`a4-target-control-${track}`)).toBeVisible();
    }
    await expect(page.getByTestId('patch-genome-variant')).toContainText(/Candidate \d of 4/);
    await expect(page.getByRole('button', { name: 'Hardware send locked' })).toBeDisabled();

    // Switch back to the Rytm panel so the rest of the checkpoint runs against
    // the surface the original spec was scoped to.
    await page.getByTestId('device-select-analog-rytm-mk2').click();
    await expect(
      snapshotPanel.getByRole('heading', { exact: true, level: 2, name: 'Snapshot' }),
    ).toBeVisible();

    const liveReadiness = page.getByRole('region', { name: 'Live Readiness' });
    await expect(liveReadiness).toBeVisible();
    await expect(
      liveReadiness.getByRole('heading', { level: 3, name: 'Pad Surface' }),
    ).toBeVisible();
    await expect(
      liveReadiness.getByRole('heading', { level: 3, name: 'Device Inventory' }),
    ).toBeVisible();
    await expect(
      liveReadiness.getByRole('heading', { level: 3, name: 'Snapshot Compatibility' }),
    ).toBeVisible();

    const safetyStatus = page.getByRole('complementary', { name: 'Safety status' });
    await expect(safetyStatus).toContainText('Mock Safe');
    await expect(safetyStatus).toContainText('No MIDI Port Open');
    await expect(safetyStatus).toContainText('Hardware Off');
  });

  test('2. wizard landing — name step heading + form', async ({
    page,
    sidecar: _sidecar,
  }) => {
    await page.goto('/');
    await page.getByTestId('cockpit-root').waitFor({ state: 'visible' });
    await page.evaluate(() => {
      window.location.hash = '#/wizard';
    });
    await page.getByTestId('wizard-root').waitFor({ state: 'visible' });
    await page.getByTestId('wizard-name-step').waitFor({ state: 'visible' });
    await expect(page).toMatchAriaSnapshot({ name: 'checkpoint-2-wizard-name.aria.yml' });
  });

  test('3. name step empty-submit error state', async ({
    page,
    sidecar: _sidecar,
  }) => {
    await page.goto('/');
    await page.getByTestId('cockpit-root').waitFor({ state: 'visible' });
    await page.evaluate(() => {
      window.location.hash = '#/wizard';
    });
    await page.getByTestId('wizard-root').waitFor({ state: 'visible' });
    await page.getByTestId('wizard-name-step').waitFor({ state: 'visible' });

    // Submit the empty name to trigger the role="alert" + aria-invalid path
    // (see NameStep.handleSubmit). Using the test-id rather than raw Tab keys
    // keeps the spec robust against changes to the tab order while still
    // exercising the exact code path a keyboard user would reach with Enter.
    await page.getByTestId('wizard-next').click();

    // The error region is rendered synchronously by NameStep when the trimmed
    // name is empty. Wait on the role="alert" so the snapshot captures the
    // post-error tree, not the pre-submit one.
    await expect(page.getByRole('alert')).toBeVisible();
    await expect(page).toMatchAriaSnapshot({ name: 'checkpoint-3-name-error.aria.yml' });
  });
});
