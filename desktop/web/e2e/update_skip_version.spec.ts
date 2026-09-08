/**
 * E2E §8 spec (d): skip-version suppresses the chip; a newer version
 * clears the skip.
 *
 * Skip is the pressure-release valve that makes the consent gate humane
 * (§5): it stops the nagging without freezing the machine out of the
 * fleet. Both halves of that sentence are load-bearing, and a bug in
 * either direction is invisible to the operator until it matters:
 *
 *  - skip that does not persist ⇒ the chip returns, the operator learns
 *    the control is a lie, and starts ignoring update UI generally;
 *  - skip that persists too broadly ⇒ the machine silently stops
 *    surfacing every future update, which looks identical to a working
 *    installation right up until it is many versions behind.
 *
 * §5 resolves it: the suppression is per-version and "cleared by any
 * newer version". This spec asserts exactly that boundary.
 *
 * FIXME state: needs PR-B.
 */

import { trackConsoleErrors } from './fixtures/console_guard';
import {
  CONSENT_LABELS,
  expect,
  test,
  UPDATE_ENV,
  UPDATE_TESTIDS,
} from './fixtures/update_fixture';
import {
  journalEvents,
  journalHygieneViolations,
  readUpdateJournal,
} from './fixtures/update_manifest';

test.use({ updateEnv: { [UPDATE_ENV.CURRENT_VERSION]: '1.34.0' } });

test.describe('skip this version (§8d)', () => {
  test.fixme(true, 'needs the wired updater in a Tauri shell: a browser e2e run has no shell to emit I2, and the HTTP transport is still unwired (PR-B ships the offline core). Un-fixme when the transport lands AND the harness runs the bundled app.');

  test('skipping suppresses the chip across a reload, and a newer version clears it', async ({
    page,
    manifestServer,
    updateConfigRoot,
  }) => {
    test.setTimeout(120_000);
    const consoleGuard = trackConsoleErrors(page);
    const skipped = manifestServer.currentManifest().version; // 1.35.1

    await page.goto('/');
    await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId(UPDATE_TESTIDS.chip)).toBeVisible({ timeout: 20_000 });

    // Skip it.
    await page.getByTestId(UPDATE_TESTIDS.chip).click();
    await page
      .getByTestId(UPDATE_TESTIDS.panel)
      .getByRole('radio', { name: CONSENT_LABELS.skipVersion })
      .check();
    await page.getByTestId(UPDATE_TESTIDS.consentConfirm).click();

    await expect
      .poll(() => journalEvents(readUpdateJournal(updateConfigRoot)), { timeout: 10_000 })
      .toContain('skip_recorded');
    const skipRow = readUpdateJournal(updateConfigRoot).find((r) => r.event === 'skip_recorded');
    expect(skipRow?.version, 'the skip names the version it suppresses').toBe(skipped);

    await expect(page.getByTestId(UPDATE_TESTIDS.chip)).toHaveCount(0);

    // --- persistence across a restart of the page ------------------------
    await page.reload();
    await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });
    await expect
      .poll(
        () =>
          journalEvents(readUpdateJournal(updateConfigRoot)).filter((e) => e === 'check_ok').length,
        { timeout: 20_000 },
      )
      .toBeGreaterThanOrEqual(2);
    await expect(
      page.getByTestId(UPDATE_TESTIDS.chip),
      'a skipped version must stay skipped after a reload',
    ).toHaveCount(0);

    // Skipping suppresses the CHIP, not the CHECK: the client keeps polling
    // so the moment a newer version ships it is noticed. A skip that also
    // stopped checking would be an accidental freeze mode.
    expect(manifestServer.manifestRequests().length).toBeGreaterThanOrEqual(2);

    // --- the boundary: a newer version clears the skip -------------------
    manifestServer.setManifest({ ...manifestServer.currentManifest(), version: '1.36.0' });
    await page.reload();
    await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });

    const chip = page.getByTestId(UPDATE_TESTIDS.chip);
    await expect(chip, 'a newer version clears the skip').toBeVisible({ timeout: 20_000 });
    await expect(chip).toContainText('1.36.0');

    expect(journalHygieneViolations(readUpdateJournal(updateConfigRoot))).toEqual([]);
    consoleGuard.assertClean();
  });

  test('an OLDER manifest version does not resurrect a skipped chip', async ({
    page,
    manifestServer,
    updateConfigRoot,
  }) => {
    test.setTimeout(90_000);

    await page.goto('/');
    await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId(UPDATE_TESTIDS.chip)).toBeVisible({ timeout: 20_000 });
    await page.getByTestId(UPDATE_TESTIDS.chip).click();
    await page
      .getByTestId(UPDATE_TESTIDS.panel)
      .getByRole('radio', { name: CONSENT_LABELS.skipVersion })
      .check();
    await page.getByTestId(UPDATE_TESTIDS.consentConfirm).click();
    await expect
      .poll(() => journalEvents(readUpdateJournal(updateConfigRoot)), { timeout: 10_000 })
      .toContain('skip_recorded');

    // §5 says "cleared by any NEWER version". A rollback (the manifest
    // re-pointed at an older release, §3) must therefore leave the skip
    // intact — and is separately refused by §4's newer-than rule. A naive
    // "version != skipped_version" implementation passes the previous test
    // and fails this one, which is why both exist.
    manifestServer.setManifest({ ...manifestServer.currentManifest(), version: '1.35.0' });
    await page.reload();
    await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });
    await expect
      .poll(
        () =>
          journalEvents(readUpdateJournal(updateConfigRoot)).filter((e) => e === 'check_ok').length,
        { timeout: 20_000 },
      )
      .toBeGreaterThanOrEqual(2);

    await expect(page.getByTestId(UPDATE_TESTIDS.chip)).toHaveCount(0);
  });
});
