/**
 * E2E §8 spec (b): the staged state renders the §7.1 consent panel with the
 * normative labels and `When I quit the app` pre-selected (I9).
 *
 * "Download eagerly, install consensually" (§1) means by the time the
 * operator is asked, the artifact is already on disk and verified. This
 * spec pins both halves: the panel only offers consent from the `staged`
 * state (never from `downloading`), and the default affordance is the one
 * D3 chose — the fastest fleet convergence that never forces a restart.
 *
 * ## Label provenance
 *
 * Every string asserted here comes from `CONSENT_LABELS` / `PANEL_COPY` in
 * the fixture, which `update_consent_labels.spec.ts` pins against spec §7.1
 * and the pixel render at `docs/design/update-consent-prompt.html`. So this
 * spec checks "the panel renders the contract", and that spec checks "the
 * contract is what §7.1 says" — neither can drift alone.
 *
 * FIXME state: needs PR-B (panel + I2 state bridge).
 */

import { trackConsoleErrors } from './fixtures/console_guard';
import {
  CONSENT_LABEL_ORDER,
  CONSENT_LABELS,
  DEFAULT_CONSENT_LABEL,
  expect,
  PANEL_BODY_VARIANTS,
  PANEL_COPY,
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

test.describe('staged consent panel (§8b / §7.1 / I9)', () => {
  test.fixme(true, 'needs the wired updater in a Tauri shell: a browser e2e run has no shell to emit I2, and the HTTP transport is still unwired (PR-B ships the offline core). Un-fixme when the transport lands AND the harness runs the bundled app.');

  test('staged state renders the three consent actions with the quit default', async ({
    page,
    manifestServer,
    updateConfigRoot,
  }) => {
    test.setTimeout(60_000);
    const consoleGuard = trackConsoleErrors(page);

    await page.goto('/');
    await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });

    // Wait for the eager download to finish staging — consent must not be
    // offered before the artifact is verified on disk (§5).
    await expect
      .poll(() => journalEvents(readUpdateJournal(updateConfigRoot)), { timeout: 30_000 })
      .toContain('download_ok');

    const panel = page.getByTestId(UPDATE_TESTIDS.panel);
    await page.getByTestId(UPDATE_TESTIDS.chip).click();
    await expect(panel).toBeVisible();

    // §7.1 header row: the running version and the channel selector. The
    // operator is choosing between two NAMED versions, not accepting an
    // opaque "update", so both numbers must be on screen at once.
    await expect(panel).toContainText(`${PANEL_COPY.runningPrefix} v1.34.0`);
    await expect(panel).toContainText(PANEL_COPY.channel);
    await expect(panel).toContainText(manifestServer.currentManifest().version);
    await expect(panel.getByTestId(UPDATE_TESTIDS.checkNow)).toBeVisible();

    // §7.1 body chrome: the captions that make the prompt legible. Release
    // notes reach the panel from the manifest under the "What's new" cap.
    await expect(panel).toContainText(PANEL_COPY.whatsNew);
    await expect(panel).toContainText(manifestServer.currentManifest().notes);
    await expect(panel).toContainText(PANEL_COPY.question);
    await expect(panel).toContainText(PANEL_COPY.activity);
    // The phone-home honesty line: §7.1 requires the panel to always state
    // what was sent and when, not merely that a check happened.
    await expect(panel).toContainText(PANEL_COPY.lastChecked);
    await expect(panel.getByTestId(UPDATE_TESTIDS.freezeToggle)).toBeVisible();
    await expect(panel).toContainText(PANEL_COPY.freeze);

    // I9 — the three labels, verbatim.
    const installNow = page.getByTestId(UPDATE_TESTIDS.consentInstallNow);
    const installOnQuit = page.getByTestId(UPDATE_TESTIDS.consentInstallOnQuit);
    const skipVersion = page.getByTestId(UPDATE_TESTIDS.consentSkipVersion);
    await expect(installNow).toHaveText(CONSENT_LABELS.installNow);
    await expect(installOnQuit).toHaveText(CONSENT_LABELS.installOnQuit);
    await expect(skipVersion).toHaveText(CONSENT_LABELS.skipVersion);

    // I9 — element order is normative, not incidental: §7.1 puts the calm
    // default first so it is where a skimming operator's eye lands.
    const renderedOrder = await panel
      .getByRole('radio')
      .evaluateAll((nodes) =>
        nodes.map((node) => (node.closest('label')?.textContent ?? '').trim()),
      );
    expect(renderedOrder).toEqual([...CONSENT_LABEL_ORDER]);

    // Confirm is the only control that mints a consent token (§7.1).
    await expect(page.getByTestId(UPDATE_TESTIDS.consentConfirm)).toHaveText(PANEL_COPY.confirm);

    // I9 — the default radio. This is the D3 decision made mechanical: if a
    // future change flips the default to "Now — restart RytmRandomizer
    // immediately", the fleet gets restarted mid-set, and this is the line
    // that catches it before a stage machine does.
    await expect(panel.getByRole('radio', { name: DEFAULT_CONSENT_LABEL })).toBeChecked();
    await expect(panel.getByRole('radio', { name: CONSENT_LABELS.installNow })).not.toBeChecked();
    await expect(panel.getByRole('radio', { name: CONSENT_LABELS.skipVersion })).not.toBeChecked();

    // Nothing has been consented to yet — merely opening the panel must not
    // record consent (the never-auto-arm analogue).
    expect(journalEvents(readUpdateJournal(updateConfigRoot))).not.toContain('consent_granted');

    // The staged transition is journaled with bounded detail.
    expect(journalHygieneViolations(readUpdateJournal(updateConfigRoot))).toEqual([]);

    consoleGuard.assertClean();
  });

  test('the activity list renders the journal, not a parallel event stream', async ({
    page,
    updateConfigRoot,
  }) => {
    test.setTimeout(60_000);
    await page.goto('/');
    await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });
    await expect
      .poll(() => journalEvents(readUpdateJournal(updateConfigRoot)), { timeout: 30_000 })
      .toContain('download_ok');

    await page.getByTestId(UPDATE_TESTIDS.chip).click();
    const activity = page.getByTestId(UPDATE_TESTIDS.activityList);
    await expect(activity).toBeVisible();

    // R4/§5.1: the journal is the single source of truth for the activity
    // list. Every event on disk must be represented in the UI — a second
    // in-memory event stream that merely resembles the journal is the fork
    // this assertion exists to prevent.
    for (const event of journalEvents(readUpdateJournal(updateConfigRoot))) {
      await expect(activity).toContainText(event);
    }
  });
});

/**
 * §7.1 state variants — "same frame, body swapped — one component, not five".
 *
 * The staged state above is the interesting one, but it is only one of five
 * bodies the same panel must render. They are asserted here rather than
 * scattered because the contract is about the SET: five distinguishable
 * bodies from one component. Two of the five have no test in this block by
 * design — `staged` is the whole describe above, and `rollout-excluded` is
 * required by §5 to be indistinguishable from `up_to_date`, so asserting it
 * separately here would be asserting a difference the spec forbids (its
 * `bucket_excluded` journal row is checked in `update_rollout_bucket.spec.ts`).
 */
test.describe('panel state variants (§7.1)', () => {
  test.fixme(true, 'needs the wired updater in a Tauri shell: a browser e2e run has no shell to emit I2, and the HTTP transport is still unwired (PR-B ships the offline core). Un-fixme when the transport lands AND the harness runs the bundled app.');

  test.describe('up to date', () => {
    test.use({ updateEnv: { [UPDATE_ENV.CURRENT_VERSION]: '1.35.1' } });

    test('states the running version and the next check, with no chip', async ({
      page,
      updateConfigRoot,
    }) => {
      test.setTimeout(60_000);
      // The manifest's 1.35.1 equals what we claim to run, so §4's
      // newer-than rule leaves the client up to date.
      await page.goto('/');
      await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });
      await expect
        .poll(() => journalEvents(readUpdateJournal(updateConfigRoot)), { timeout: 20_000 })
        .toContain('check_ok');

      await expect(page.getByTestId(UPDATE_TESTIDS.chip)).toHaveCount(0);
      const panel = page.getByTestId(UPDATE_TESTIDS.panel);
      await expect(panel).toContainText(PANEL_BODY_VARIANTS.upToDatePrefix);
      // No consent controls exist in this state — there is nothing to consent
      // to, and a disabled radio group would imply otherwise.
      await expect(page.getByTestId(UPDATE_TESTIDS.consentConfirm)).toHaveCount(0);
    });
  });

  test.describe('check failed', () => {
    test.use({ updateEnv: { [UPDATE_ENV.CURRENT_VERSION]: '1.34.0' } });

    test('names the reason code verbatim and promises a retry', async ({
      page,
      manifestServer,
      updateConfigRoot,
    }) => {
      test.setTimeout(60_000);
      // §5.1's failure-honesty floor: an updater that cannot reach its
      // manifest must SAY so. A silent chip-less panel is indistinguishable
      // from "up to date", which is the one lie the floor exists to prevent.
      manifestServer.setManifestOverride({ status: 500, body: '' });

      await page.goto('/');
      await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });
      await expect
        .poll(() => journalEvents(readUpdateJournal(updateConfigRoot)), { timeout: 20_000 })
        .toContain('check_failed');

      const panel = page.getByTestId(UPDATE_TESTIDS.panel);
      await expect(panel).toContainText(PANEL_BODY_VARIANTS.checkFailedPrefix);

      // The panel shows the journal's typed reason code verbatim — not a
      // paraphrase, so an operator can quote it into a bug report and a
      // maintainer can grep the closed vocabulary for it.
      const failure = readUpdateJournal(updateConfigRoot).find((r) => r.event === 'check_failed');
      const reason = failure?.detail.reason;
      expect(typeof reason, 'check_failed carries a typed reason code').toBe('string');
      await expect(panel).toContainText(String(reason));

      // §5.1 floor: also mirrored into the EXISTING SafetyRail operator log
      // (not a second update-only log — that is the R4 fork the plan
      // forbids), so the failure is visible without opening the panel.
      await expect(page.getByTestId(UPDATE_TESTIDS.operatorLog)).toContainText(String(reason));
    });
  });

  test.describe('frozen', () => {
    test.use({
      updateEnv: {
        [UPDATE_ENV.UPDATES]: 'off',
        [UPDATE_ENV.CURRENT_VERSION]: '1.34.0',
      },
    });

    test('replaces the body and keeps only the toggle', async ({ page }) => {
      test.setTimeout(60_000);
      await page.goto('/');
      await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });

      const panel = page.getByTestId(UPDATE_TESTIDS.panel);
      await expect(panel).toContainText(PANEL_BODY_VARIANTS.frozen);
      await expect(panel.getByTestId(UPDATE_TESTIDS.freezeToggle)).toBeVisible();
      // Chip hidden (§7.1) and no consent surface: a frozen client has
      // nothing staged, so offering "install now" would be a dead control.
      await expect(page.getByTestId(UPDATE_TESTIDS.chip)).toHaveCount(0);
      await expect(page.getByTestId(UPDATE_TESTIDS.consentConfirm)).toHaveCount(0);
    });
  });
});
