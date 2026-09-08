/**
 * E2E §8 spec (g): the hardware-revalidation banner renders only when the
 * manifest flags it.
 *
 * `hardware_revalidation: true` marks a release whose diff touched the
 * parity surface, the `mido`/`rtmidi` pins, or the ArmedApply seam (§2.5)
 * — i.e. the repository's hardest invariants, the ones whose regressions
 * the mock-only test suite structurally cannot catch. It is the one place
 * where the update gate is wired to the hardware-safety gate, and the
 * operator's decision genuinely differs: accept before a show, or wait
 * until there is a Rytm on the bench to re-validate against.
 *
 * The banner therefore has a two-sided contract, and both sides are
 * failure modes:
 *
 *  - missing when flagged ⇒ the operator installs a wire-format-affecting
 *    build without knowing, which is exactly the scenario the pinned-
 *    packages rule spends its whole existence preventing;
 *  - present when NOT flagged ⇒ every release looks dangerous, the warning
 *    becomes noise, and the flagged release it was built for gets waved
 *    through with the rest.
 *
 * Hence: one test per side, same panel, same selector.
 *
 * FIXME state: needs PR-B.
 */

import { trackConsoleErrors } from './fixtures/console_guard';
import {
  expect,
  test,
  UPDATE_ENV,
  UPDATE_TESTIDS,
} from './fixtures/update_fixture';
import { journalEvents, readUpdateJournal } from './fixtures/update_manifest';

test.use({ updateEnv: { [UPDATE_ENV.CURRENT_VERSION]: '1.34.0' } });

test.describe('hardware-revalidation banner (§8g)', () => {
  test.fixme(true, 'needs the wired updater in a Tauri shell: a browser e2e run has no shell to emit I2, and the HTTP transport is still unwired (PR-B ships the offline core). Un-fixme when the transport lands AND the harness runs the bundled app.');

  test('renders loudly when the manifest sets hardware_revalidation', async ({
    page,
    manifestServer,
    updateConfigRoot,
  }) => {
    test.setTimeout(60_000);
    const consoleGuard = trackConsoleErrors(page);
    manifestServer.setManifest({
      ...manifestServer.currentManifest(),
      hardware_revalidation: true,
    });

    await page.goto('/');
    await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });
    await expect
      .poll(() => journalEvents(readUpdateJournal(updateConfigRoot)), { timeout: 30_000 })
      .toContain('download_ok');

    await page.getByTestId(UPDATE_TESTIDS.chip).click();
    const banner = page.getByTestId(UPDATE_TESTIDS.hardwareBanner);
    await expect(banner).toBeVisible();
    await expect(banner).toContainText(/hardware/i);

    // Announced, not merely painted: this is the one update message an
    // operator must not miss, so it carries an assertive live region
    // rather than relying on the visual treatment alone (a11y standard).
    await expect(banner).toHaveAttribute('role', /alert|status/);

    // Colorblind-safe: the warning survives without hue (§7 / a11y).
    await expect(banner).toContainText(/⚠|!/);

    // The banner does not pre-empt the choice — consent is still the
    // operator's, just better informed.
    await expect(page.getByTestId(UPDATE_TESTIDS.consentConfirm)).toBeEnabled();

    consoleGuard.assertClean();
  });

  test('is absent for an ordinary release', async ({
    page,
    manifestServer,
    updateConfigRoot,
  }) => {
    test.setTimeout(60_000);
    // The I3 fixture already ships `hardware_revalidation: false`; assert
    // that precondition so this test cannot silently become a duplicate of
    // the one above if the fixture's default ever flips.
    expect(manifestServer.currentManifest().hardware_revalidation).toBe(false);

    await page.goto('/');
    await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });
    await expect
      .poll(() => journalEvents(readUpdateJournal(updateConfigRoot)), { timeout: 30_000 })
      .toContain('download_ok');

    await page.getByTestId(UPDATE_TESTIDS.chip).click();
    await expect(page.getByTestId(UPDATE_TESTIDS.panel)).toBeVisible();
    await expect(page.getByTestId(UPDATE_TESTIDS.hardwareBanner)).toHaveCount(0);
  });
});
