/**
 * E2E: the §6 ping is structurally unable to gate an update.
 *
 * §6 makes an unusually strong claim: the fleet-awareness ping "is
 * fire-and-forget and entirely separate from the manifest fetch: its
 * failure, absence, or removal cannot delay or block an update check
 * (pinned by a §8 test)". This is that test.
 *
 * The claim matters because it is the design's whole answer to the
 * question "what happens when your telemetry breaks". The rejected
 * edge-worker design failed exactly here — a beacon in the request path
 * is an availability dependency wearing a metrics costume, and the day it
 * 500s, nobody in the fleet can update. Making the ping a separate
 * fire-and-forget GET of a public asset removes that coupling by
 * construction, but "by construction" is a claim about code that has to
 * be checked against the code.
 *
 * Three failure shapes are exercised, because they fail differently:
 *  - the ping 500s (server up, asset broken);
 *  - the ping 404s (asset never uploaded — the real state of every
 *    release before the first one that ships beacon assets, §6);
 *  - the ping hangs (the nastiest: a naive `await` blocks the check
 *    behind a socket timeout, which is a delay rather than an error and
 *    so passes both of the tests above).
 *
 * In all three the update must complete normally, and the failure must be
 * journaled rather than swallowed.
 *
 * FIXME state: needs PR-B for the client behavior.
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

test.use({ updateEnv: { [UPDATE_ENV.CURRENT_VERSION]: '1.34.0' } });

test.describe('ping independence (§6)', () => {
  test.fixme(true, 'needs the wired updater in a Tauri shell: a browser e2e run has no shell to emit I2, and the HTTP transport is still unwired (PR-B ships the offline core). Un-fixme when the transport lands AND the harness runs the bundled app.');

  test('a failing ping does not block, delay, or hide the update', async ({
    page,
    manifestServer,
    updateConfigRoot,
  }) => {
    test.setTimeout(60_000);
    const consoleGuard = trackConsoleErrors(page);
    manifestServer.setPingOverride({ status: 500, body: 'boom' });

    const startedAt = Date.now();
    await page.goto('/');
    await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });

    // The update path completes exactly as it would with a healthy ping.
    await expect(page.getByTestId(UPDATE_TESTIDS.chip)).toBeVisible({ timeout: 20_000 });
    const events = journalEvents(readUpdateJournal(updateConfigRoot));
    expect(events).toContain('check_ok');

    // The ping was attempted and its failure recorded — "cannot block" is
    // not the same as "is not tried", and a silently dropped ping would
    // leave the fleet histogram wrong with no local evidence why.
    expect(manifestServer.pingRequests().length).toBeGreaterThanOrEqual(1);
    expect(events).toContain('ping_failed');

    // Typed reason code, not a transport error string (§5.1 hygiene).
    const pingRow = readUpdateJournal(updateConfigRoot).find((r) => r.event === 'ping_failed');
    expect(typeof pingRow?.detail.reason).toBe('string');
    expect(journalHygieneViolations(readUpdateJournal(updateConfigRoot))).toEqual([]);

    // And it did not cost the operator any waiting: a fire-and-forget GET
    // that is actually awaited would show up here as multi-second drag.
    expect(Date.now() - startedAt).toBeLessThan(25_000);

    consoleGuard.assertClean();
  });

  test('an absent ping asset (404) is equally harmless', async ({
    page,
    manifestServer,
    updateConfigRoot,
  }) => {
    test.setTimeout(60_000);
    // 404 is the honest state for every version released before ping
    // assets existed (§6 "honest limits") — the common case, not an edge.
    manifestServer.setPingOverride({ status: 404, body: 'not found' });

    await page.goto('/');
    await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId(UPDATE_TESTIDS.chip)).toBeVisible({ timeout: 20_000 });
    expect(journalEvents(readUpdateJournal(updateConfigRoot))).toContain('check_ok');
  });

  test('a hanging ping does not stall the check', async ({
    page,
    manifestServer,
    updateConfigRoot,
  }) => {
    test.setTimeout(60_000);
    // The mock server answers the manifest promptly but accepts the ping
    // connection and never responds — a black-holed asset. If the client
    // awaits the ping anywhere in the check path, the chip misses its
    // deadline below and this test fails: the only way to catch an ordering
    // bug that the 500 and 404 cases sail straight past, because those two
    // return promptly and a naive `await` on them costs nothing.
    //
    // The hang lives in the SERVER, not in `page.route(...)`. Playwright's
    // route interception only sees browser-issued requests, and the §6 ping
    // is fired by the Rust shell — a browser-scoped hang would leave the
    // shell's real GET answered instantly, and this test would pass while
    // testing nothing. See `ResponseOverride.hang`.
    manifestServer.setPingOverride({ hang: true });

    await page.goto('/');
    await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId(UPDATE_TESTIDS.chip)).toBeVisible({ timeout: 20_000 });
    expect(journalEvents(readUpdateJournal(updateConfigRoot))).toContain('check_ok');

    // The ping was attempted (and is still hanging) — proof the stall was
    // real and the client simply did not wait on it.
    expect(manifestServer.pingRequests().length).toBeGreaterThanOrEqual(1);
  });
});
