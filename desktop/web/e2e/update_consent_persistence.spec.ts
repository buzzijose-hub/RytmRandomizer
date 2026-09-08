/**
 * E2E §8 spec (c): consent persists for this version and does NOT
 * auto-install on reload.
 *
 * This is the update system's direct analogue of "arming never survives a
 * reconnect" (§1). The operator choosing `When I quit the app` is a
 * decision about ONE version at ONE natural exit — it must never become a
 * standing authorization that an unexpected restart cashes in. §5 states
 * it precisely: consent tokens are process-lifetime and version-bound, and
 * a crash after consent does not auto-install on next start.
 *
 * The spec proves the negative the only way a negative can be proven here:
 * by reloading after consent and asserting that `install_started` is
 * absent from the journal while `consent_granted` is present. Asserting on
 * UI state alone could not tell "did not install" from "installed and the
 * chip happened to re-render".
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

test.describe('consent persistence (§8c)', () => {
  test.fixme(true, 'needs the wired updater in a Tauri shell: a browser e2e run has no shell to emit I2, and the HTTP transport is still unwired (PR-B ships the offline core). Un-fixme when the transport lands AND the harness runs the bundled app.');

  test('install-on-quit consent is recorded for this version and never auto-installs', async ({
    page,
    manifestServer,
    updateConfigRoot,
  }) => {
    test.setTimeout(90_000);
    const consoleGuard = trackConsoleErrors(page);
    const stagedVersion = manifestServer.currentManifest().version;

    await page.goto('/');
    await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });
    await expect
      .poll(() => journalEvents(readUpdateJournal(updateConfigRoot)), { timeout: 30_000 })
      .toContain('download_ok');

    // Grant consent for the default affordance.
    await page.getByTestId(UPDATE_TESTIDS.chip).click();
    const panel = page.getByTestId(UPDATE_TESTIDS.panel);
    await panel.getByRole('radio', { name: CONSENT_LABELS.installOnQuit }).check();
    await page.getByTestId(UPDATE_TESTIDS.consentConfirm).click();

    await expect
      .poll(() => journalEvents(readUpdateJournal(updateConfigRoot)), { timeout: 10_000 })
      .toContain('consent_granted');

    // The consent row is version-bound: a token that did not name its
    // version could be replayed against a different one.
    const granted = readUpdateJournal(updateConfigRoot).find(
      (row) => row.event === 'consent_granted',
    );
    expect(granted?.version).toBe(stagedVersion);
    expect(granted?.detail.choice).toBe('install_on_quit');

    // The panel reflects the recorded choice rather than resetting.
    await expect(panel).toContainText(CONSENT_LABELS.installOnQuit);

    // --- the load-bearing half: reload is NOT a natural exit ---------------
    await page.reload();
    await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });

    // Let a full check cycle run after the reload, so "no install" is a
    // conclusion about a settled state and not about an unfinished one.
    await expect
      .poll(
        () =>
          journalEvents(readUpdateJournal(updateConfigRoot)).filter((e) => e === 'check_ok').length,
        { timeout: 20_000 },
      )
      .toBeGreaterThanOrEqual(2);

    const events = journalEvents(readUpdateJournal(updateConfigRoot));
    expect(events, 'consent must never survive into an unattended install').not.toContain(
      'install_started',
    );
    expect(events).not.toContain('install_ok');

    // The chip is still there: the update remains pending, honestly.
    await expect(page.getByTestId(UPDATE_TESTIDS.chip)).toBeVisible();

    expect(journalHygieneViolations(readUpdateJournal(updateConfigRoot))).toEqual([]);
    consoleGuard.assertClean();
  });

  test('consent for one version does not carry to a different version', async ({
    page,
    manifestServer,
    updateConfigRoot,
  }) => {
    test.setTimeout(90_000);

    await page.goto('/');
    await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });
    await expect
      .poll(() => journalEvents(readUpdateJournal(updateConfigRoot)), { timeout: 30_000 })
      .toContain('download_ok');

    await page.getByTestId(UPDATE_TESTIDS.chip).click();
    await page
      .getByTestId(UPDATE_TESTIDS.panel)
      .getByRole('radio', { name: CONSENT_LABELS.installOnQuit })
      .check();
    await page.getByTestId(UPDATE_TESTIDS.consentConfirm).click();
    await expect
      .poll(() => journalEvents(readUpdateJournal(updateConfigRoot)), { timeout: 10_000 })
      .toContain('consent_granted');

    // A newer version supersedes the staged one. The prior consent must not
    // apply to it — otherwise consent silently becomes a standing grant for
    // whatever the manifest serves next, which is the failure mode §5's
    // version-binding rule exists to prevent.
    manifestServer.setManifest({ ...manifestServer.currentManifest(), version: '1.36.0' });
    await page.getByTestId(UPDATE_TESTIDS.checkNow).click();

    await expect(page.getByTestId(UPDATE_TESTIDS.chip)).toContainText('1.36.0', {
      timeout: 20_000,
    });

    // Fresh consent is required: the panel is back to the I9 default.
    await page.getByTestId(UPDATE_TESTIDS.chip).click();
    await expect(
      page.getByTestId(UPDATE_TESTIDS.panel).getByRole('radio', { name: CONSENT_LABELS.installOnQuit }),
    ).toBeChecked();
    const grantedVersions = readUpdateJournal(updateConfigRoot)
      .filter((row) => row.event === 'consent_granted')
      .map((row) => row.version);
    expect(grantedVersions, 'no consent was granted for 1.36.0').not.toContain('1.36.0');
  });
});
