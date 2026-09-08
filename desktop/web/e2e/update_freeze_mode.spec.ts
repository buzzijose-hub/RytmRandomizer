/**
 * E2E §8 spec (e): freeze mode produces PROVABLE network silence.
 *
 * Freeze mode is the "machine that goes to the gig" escape hatch (§1) —
 * the update analogue of `RYTM_RAND_MIDI_BACKEND=off`. Its promise is
 * absolute: "no check, no download, no chip" (§4.4), and §5 places the
 * short-circuit *before* `checking`, so freeze means zero network I/O of
 * any kind.
 *
 * ## Why this spec asserts request counts rather than chip absence
 *
 * A hidden chip is compatible with a client that checks every four hours,
 * downloads a 40 MB artifact, and merely declines to render. On a laptop
 * tethered to a phone in a venue, that is precisely the failure the
 * operator turned freeze mode ON to avoid — and it would look perfect from
 * the UI. The only assertion that distinguishes real silence from a quiet
 * facade is a server-side request count of exactly zero, which is what the
 * mock server's request log exists to provide.
 *
 * Both counters are checked: the manifest (§4) and the ping asset (§6).
 * Freeze disables both; `RYTM_RAND_UPDATE_BEACON=off` disables only the
 * second, and the last test pins that distinction so the two opt-outs
 * cannot be collapsed into one.
 *
 * FIXME state: needs PR-B for the chip/journal assertions. Marked at the
 * describe level for consistency with the other client-flow specs.
 */

import { trackConsoleErrors } from './fixtures/console_guard';
import {
  expect,
  PANEL_BODY_VARIANTS,
  test,
  UPDATE_ENV,
  UPDATE_TESTIDS,
} from './fixtures/update_fixture';
import {
  journalEvents,
  journalHygieneViolations,
  readUpdateJournal,
} from './fixtures/update_manifest';

/** Long enough for a launch check (+ its retry) to have fired if it were going to. */
const SILENCE_OBSERVATION_MS = 8_000;

test.describe('freeze mode (§8e)', () => {
  test.fixme(true, 'needs the wired updater in a Tauri shell: a browser e2e run has no shell to emit I2, and the HTTP transport is still unwired (PR-B ships the offline core). Un-fixme when the transport lands AND the harness runs the bundled app.');

  test.describe('with updates frozen', () => {
    test.use({
      updateEnv: {
        [UPDATE_ENV.UPDATES]: 'off',
        [UPDATE_ENV.CURRENT_VERSION]: '1.34.0',
      },
    });

    test('issues zero update requests and renders no chip', async ({
      page,
      manifestServer,
      updateConfigRoot,
    }) => {
      test.setTimeout(60_000);
      const consoleGuard = trackConsoleErrors(page);

      await page.goto('/');
      await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });

      // Sit for longer than a launch check would take. An immediate
      // assertion would pass even against a client that checks on a short
      // delay, so the wait is the assertion's whole substance.
      await page.waitForTimeout(SILENCE_OBSERVATION_MS);

      // THE assertion of this spec: provable silence, both channels.
      expect(manifestServer.manifestRequests(), 'freeze mode must not fetch the manifest').toEqual(
        [],
      );
      expect(manifestServer.pingRequests(), 'freeze mode must not fire the §6 ping').toEqual([]);
      expect(manifestServer.requests, 'freeze mode must issue no update traffic at all').toEqual(
        [],
      );

      // ...and only then the UI consequence: chip hidden, and the §7.1
      // frozen body saying so. "No chip" alone is ambiguous — it is also
      // what up-to-date looks like — so the panel must state that traffic
      // is stopped, or an operator cannot tell freeze took effect.
      await expect(page.getByTestId(UPDATE_TESTIDS.chip)).toHaveCount(0);
      await expect(page.getByTestId(UPDATE_TESTIDS.panel)).toContainText(
        PANEL_BODY_VARIANTS.frozen,
      );

      // §5.1: freeze is journaled, not silent. "Nothing happened" and
      // "the updater is broken" must be distinguishable after the fact —
      // that is the difference between a working escape hatch and a
      // hatch nobody can verify was engaged.
      const events = journalEvents(readUpdateJournal(updateConfigRoot));
      expect(events).toContain('freeze_suppressed');
      expect(events, 'a frozen client never starts a check').not.toContain('check_started');
      expect(events).not.toContain('download_started');
      expect(journalHygieneViolations(readUpdateJournal(updateConfigRoot))).toEqual([]);

      consoleGuard.assertClean();
    });

    test('manual "Check now" stays inert while frozen', async ({ page, manifestServer }) => {
      test.setTimeout(60_000);
      await page.goto('/');
      await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });

      // If the panel exposes a check control at all while frozen, it must
      // not be a backdoor around the freeze — an operator mid-set who taps
      // it should not discover that freeze only governed the timer.
      const checkNow = page.getByTestId(UPDATE_TESTIDS.checkNow);
      if ((await checkNow.count()) > 0) {
        await expect(checkNow).toBeDisabled();
      }
      await page.waitForTimeout(SILENCE_OBSERVATION_MS);
      expect(manifestServer.requests).toEqual([]);
    });
  });

  test.describe('with only the beacon disabled', () => {
    test.use({
      updateEnv: {
        [UPDATE_ENV.BEACON]: 'off',
        [UPDATE_ENV.CURRENT_VERSION]: '1.34.0',
      },
    });

    test('checks continue but the §6 ping never fires', async ({
      page,
      manifestServer,
      updateConfigRoot,
    }) => {
      test.setTimeout(60_000);
      await page.goto('/');
      await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });

      await expect
        .poll(() => journalEvents(readUpdateJournal(updateConfigRoot)), { timeout: 20_000 })
        .toContain('check_ok');

      // The two opt-outs are genuinely separate (§6 privacy section): this
      // one keeps the operator updatable while sending nothing.
      expect(manifestServer.manifestRequests().length).toBeGreaterThanOrEqual(1);
      expect(manifestServer.pingRequests(), 'BEACON=off must suppress the ping').toEqual([]);

      const events = journalEvents(readUpdateJournal(updateConfigRoot));
      expect(events).not.toContain('ping_ok');
      expect(events, 'a suppressed ping is not a failed ping').not.toContain('ping_failed');
    });
  });
});
