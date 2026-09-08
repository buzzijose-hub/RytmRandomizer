/**
 * E2E §8 spec (a): the chip appears when an update is available.
 *
 * The passive half of the safety model (§1): checking and downloading are
 * free and ongoing, so a client whose manifest advertises a newer version
 * must surface the chip WITHOUT any operator action — and must journal the
 * check it performed while doing so.
 *
 * Asserted at two layers deliberately:
 *  - the chip renders with the staged version (what the operator sees);
 *  - the I8 journal carries `check_started` → `check_ok` (what actually
 *    happened). UI alone cannot distinguish "checked and found 1.35.1"
 *    from "rendered a stale cached chip"; the journal can.
 *
 * FIXME state: needs PR-B (B-rust emits I8 + I2; B-web renders the chip).
 * The body is complete — un-fixme is the only change required.
 */

import { trackConsoleErrors } from './fixtures/console_guard';
import {
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

// The running version must be OLDER than the manifest's 1.35.1, or §4's
// "act only when newer" rule correctly suppresses everything.
test.use({ updateEnv: { [UPDATE_ENV.CURRENT_VERSION]: '1.34.0' } });

test.describe('update chip (§8a)', () => {
  test.fixme(
    true,
    'needs the wired updater in a Tauri shell: a browser e2e run has no shell to emit I2, and the HTTP transport is still unwired (PR-B ships the offline core). Un-fixme when the transport lands AND the harness runs the bundled app.',
  );

  test('an available update raises the chip and journals a successful check', async ({
    page,
    sidecar,
    manifestServer,
    updateConfigRoot,
  }) => {
    test.setTimeout(60_000);
    expect(sidecar.token.length).toBeGreaterThan(20);
    const consoleGuard = trackConsoleErrors(page);

    await page.goto('/');
    await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });

    // Passive check happens on launch (§5, D2 cadence) — no click required.
    const chip = page.getByTestId(UPDATE_TESTIDS.chip);
    await expect(chip).toBeVisible({ timeout: 15_000 });

    // §7.1's chip is `⬆ <version> ready` — icon + shape + text, never hue
    // alone (the colorblind-safe a11y standard). Asserted as one string
    // rather than three `toContainText` calls so a chip reading
    // "⬆ update ready" without the version cannot pass: knowing WHICH
    // version is staged is the whole informational content of the chip.
    await expect(chip).toHaveText(`⬆ ${manifestServer.currentManifest().version} ready`);

    // Announced once via the global announcer, not on every poll (§7: no
    // live-region spam — the OfflineShell precedent).
    await expect(page.getByTestId(UPDATE_TESTIDS.liveRegion)).toContainText(
      manifestServer.currentManifest().version,
    );

    // The check really hit the network — a rendered chip is not proof.
    expect(manifestServer.manifestRequests().length).toBeGreaterThanOrEqual(1);

    // I8: the transition sequence, not merely the end state.
    const rows = readUpdateJournal(updateConfigRoot);
    const events = journalEvents(rows);
    expect(events).toContain('check_started');
    expect(events).toContain('check_ok');
    expect(events, 'a healthy check must not journal a failure').not.toContain('check_failed');

    // The check_ok row names the version it found, so the journal alone
    // explains the chip without cross-referencing the manifest.
    const checkOk = rows.find((row) => row.event === 'check_ok');
    expect(checkOk?.version).toBe(manifestServer.currentManifest().version);

    // §5.1 hygiene floor: bounded, path-free details on every row.
    expect(journalHygieneViolations(rows)).toEqual([]);

    consoleGuard.assertClean();
  });

  test('no chip when the manifest advertises the running version', async ({
    page,
    manifestServer,
    updateConfigRoot,
  }) => {
    test.setTimeout(60_000);
    // Serve a manifest matching what we claim to be running: §4 says the
    // client acts only when the manifest version is strictly NEWER.
    manifestServer.setManifest({ ...manifestServer.currentManifest(), version: '1.34.0' });

    await page.goto('/');
    await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });

    // Give the launch check time to complete before asserting absence —
    // asserting "not visible" too early would pass for the wrong reason.
    await expect
      .poll(() => journalEvents(readUpdateJournal(updateConfigRoot)), { timeout: 15_000 })
      .toContain('check_ok');

    await expect(page.getByTestId(UPDATE_TESTIDS.chip)).toHaveCount(0);
  });
});
