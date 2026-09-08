/**
 * E2E §8 spec (f): staged-rollout bucket boundary, both sides.
 *
 * §5 fixes the bucketing exactly:
 *
 *     bucket = first 4 bytes of SHA-256(install_id) as big-endian u32, mod 100
 *     take the update iff bucket < rollout_percent
 *
 * The strictness of `<` is the whole contract. An implementation using
 * `<=` shifts every rollout by one percent — which is invisible in
 * production (nobody notices 11% instead of 10%) and corrupts the one
 * property the design promises: that each rollout step is a strict
 * superset of the last, so nobody flaps in and out as the percentage
 * rises. A boundary bug here silently degrades staged rollout into
 * "roughly staged", and the fleet dashboard would show a plausible curve
 * the entire time.
 *
 * So this spec asserts BOTH sides of one real boundary with install ids
 * whose buckets were computed from the §5 formula itself (see
 * `BUCKET_VECTORS` — the values are checked in-spec, not trusted), plus
 * the superset property across a rollout step.
 *
 * `RYTM_RAND_UPDATE_FORCED_INSTALL_ID` is a test-only seam: the real
 * `install_id` is minted once at first launch and never regenerated, so
 * without an override there is no way to place a client in a chosen
 * bucket, and boundary behavior would be untestable.
 *
 * FIXME state: needs PR-B.
 */

import { createHash } from 'node:crypto';

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

/** The §5 bucketing function, implemented here as the spec states it. */
function bucketOf(installId: string): number {
  return createHash('sha256').update(installId).digest().readUInt32BE(0) % 100;
}

/**
 * Install ids chosen so their §5 buckets straddle the 10% boundary.
 * The buckets are asserted below rather than assumed — if the formula
 * above and these ids ever disagree, the vector test fails loudly instead
 * of the boundary tests passing for the wrong reason.
 */
const BUCKET_VECTORS = {
  /** bucket 9 — included at rollout_percent = 10 (9 < 10). */
  included: '00000000-0000-4000-8000-000000000015',
  /** bucket 10 — excluded at rollout_percent = 10 (10 < 10 is false). */
  excluded: '00000000-0000-4000-8000-000000000119',
  /** bucket 11 — still excluded at 10, included once the step reaches 50. */
  laterWave: '00000000-0000-4000-8000-000000000016',
} as const;

const ROLLOUT_PERCENT = 10;

test.describe('rollout bucketing (§8f)', () => {
  test('the vectors really do straddle the boundary', () => {
    // Not fixme'd: this pins the test data itself and needs no client.
    expect(bucketOf(BUCKET_VECTORS.included)).toBe(9);
    expect(bucketOf(BUCKET_VECTORS.excluded)).toBe(10);
    expect(bucketOf(BUCKET_VECTORS.laterWave)).toBe(11);
    expect(bucketOf(BUCKET_VECTORS.included)).toBeLessThan(ROLLOUT_PERCENT);
    expect(bucketOf(BUCKET_VECTORS.excluded)).toBeGreaterThanOrEqual(ROLLOUT_PERCENT);
  });

  test.describe('inside the rollout (bucket 9 < 10)', () => {
    test.fixme(true, 'needs the wired updater in a Tauri shell: a browser e2e run has no shell to emit I2, and the HTTP transport is still unwired (PR-B ships the offline core). Un-fixme when the transport lands AND the harness runs the bundled app.');
    test.use({
      updateEnv: {
        [UPDATE_ENV.CURRENT_VERSION]: '1.34.0',
        [UPDATE_ENV.FORCED_INSTALL_ID]: BUCKET_VECTORS.included,
      },
      initialManifest: null,
    });

    test('takes the update and shows the chip', async ({
      page,
      manifestServer,
      updateConfigRoot,
    }) => {
      test.setTimeout(60_000);
      manifestServer.setManifest({
        ...manifestServer.currentManifest(),
        rollout_percent: ROLLOUT_PERCENT,
      });

      await page.goto('/');
      await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });

      await expect(page.getByTestId(UPDATE_TESTIDS.chip)).toBeVisible({ timeout: 20_000 });

      const events = journalEvents(readUpdateJournal(updateConfigRoot));
      expect(events).toContain('check_ok');
      expect(events, 'a client inside the rollout is not excluded').not.toContain(
        'bucket_excluded',
      );
      expect(journalHygieneViolations(readUpdateJournal(updateConfigRoot))).toEqual([]);
    });
  });

  test.describe('outside the rollout (bucket 10, not < 10)', () => {
    test.fixme(true, 'needs the wired updater in a Tauri shell: a browser e2e run has no shell to emit I2, and the HTTP transport is still unwired (PR-B ships the offline core). Un-fixme when the transport lands AND the harness runs the bundled app.');
    test.use({
      updateEnv: {
        [UPDATE_ENV.CURRENT_VERSION]: '1.34.0',
        [UPDATE_ENV.FORCED_INSTALL_ID]: BUCKET_VECTORS.excluded,
      },
    });

    test('is treated as up-to-date this cycle, and journals why', async ({
      page,
      manifestServer,
      updateConfigRoot,
    }) => {
      test.setTimeout(60_000);
      manifestServer.setManifest({
        ...manifestServer.currentManifest(),
        rollout_percent: ROLLOUT_PERCENT,
      });

      await page.goto('/');
      await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });

      await expect
        .poll(() => journalEvents(readUpdateJournal(updateConfigRoot)), { timeout: 20_000 })
        .toContain('bucket_excluded');

      // §5: "treated as up_to_date this cycle" — no chip, and crucially no
      // download either. Staging an artifact the client is not allowed to
      // offer would waste the bandwidth the rollout gate exists to control.
      await expect(page.getByTestId(UPDATE_TESTIDS.chip)).toHaveCount(0);
      expect(journalEvents(readUpdateJournal(updateConfigRoot))).not.toContain('download_started');

      // The exclusion row explains itself without leaking the install id
      // (which is local-only by §6) — bucket and threshold, nothing more.
      const row = readUpdateJournal(updateConfigRoot).find((r) => r.event === 'bucket_excluded');
      expect(row?.detail.bucket).toBe(10);
      expect(row?.detail.rollout_percent).toBe(ROLLOUT_PERCENT);
      expect(
        JSON.stringify(row?.detail ?? {}),
        'the install id never appears in the journal',
      ).not.toContain(BUCKET_VECTORS.excluded);
    });

    test('a later rollout step includes it — every step is a superset', async ({
      page,
      manifestServer,
      updateConfigRoot,
    }) => {
      test.setTimeout(90_000);
      manifestServer.setManifest({
        ...manifestServer.currentManifest(),
        rollout_percent: ROLLOUT_PERCENT,
      });

      await page.goto('/');
      await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });
      await expect
        .poll(() => journalEvents(readUpdateJournal(updateConfigRoot)), { timeout: 20_000 })
        .toContain('bucket_excluded');
      await expect(page.getByTestId(UPDATE_TESTIDS.chip)).toHaveCount(0);

      // Promote 10 → 50 (one manifest commit in production, §3).
      manifestServer.setManifest({ ...manifestServer.currentManifest(), rollout_percent: 50 });
      await page.reload();
      await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });

      // Same install id, same hash, now inside the window: the client is
      // pulled in and never pushed back out. That monotonicity is what
      // makes a staged rollout observable on the dashboard.
      await expect(page.getByTestId(UPDATE_TESTIDS.chip)).toBeVisible({ timeout: 20_000 });
    });
  });
});
