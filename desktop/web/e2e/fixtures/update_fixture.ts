/**
 * Playwright fixture for the auto-update E2E specs (agent C-e2e).
 *
 * Layers three things onto the existing `wizard_fixture` sidecar fixture:
 *
 *  1. `manifestServer` — the ephemeral-port mock manifest server
 *     (`update_manifest.ts`), pointed at by `RYTM_RAND_UPDATE_MANIFEST_URL`.
 *  2. `updateConfigRoot` — an isolated config dir so the I8 journal, the
 *     skip-version record, and the install id are per-test state.
 *  3. `updateEnv` — the §7 env-var block handed to the sidecar spawn, so a
 *     spec declares intent (`RYTM_RAND_UPDATES: 'off'`) rather than
 *     assembling paths itself.
 *
 * ## Why this composes with `wizard_fixture` instead of replacing it
 *
 * The update chip and panel live in the cockpit, which does not render
 * meaningfully without a hydrated session — every existing spec's first
 * assertion is `cockpit-root` visible after the sidecar handshake. Forking
 * a second sidecar-spawning fixture would duplicate the token hand-off,
 * the CoreMIDI retry policy, and the per-test profile isolation, i.e.
 * exactly the R-contract fork the plan forbids. Extending is the only
 * option that keeps one sidecar lifecycle in the suite.
 *
 * The env vars are passed via the sidecar spawn because the sidecar is the
 * process this suite can actually configure. When PR-B lands the Rust
 * shell, the same variable names reach the shell unchanged (they are I4,
 * fixed by the spec, not by either implementation) — which is why the
 * specs address them by name here rather than through a shell-only seam.
 */

import { test as wizardTest, expect } from './wizard_fixture';
import {
  makeUpdateConfigRoot,
  startMockManifestServer,
  type MockManifestServer,
  type UpdateManifest,
} from './update_manifest';

/**
 * I4 — env vars exactly as spec §7. Centralized so a spec never spells a
 * variable name inline: a rename lands in one place, and a typo becomes a
 * compile error rather than a silently-ignored variable (the worst
 * possible failure for a freeze-mode test, which would pass vacuously).
 */
export const UPDATE_ENV = {
  /** `off` disables checks entirely — no network of any kind (§1, §5). */
  UPDATES: 'RYTM_RAND_UPDATES',
  /** `off` keeps checks but never fires the §6 ping. */
  BEACON: 'RYTM_RAND_UPDATE_BEACON',
  /** Points the client at the mock manifest instead of the real CDN. */
  MANIFEST_URL: 'RYTM_RAND_UPDATE_MANIFEST_URL',
  /** Test-only forced install id — the §5 bucketing input (see below). */
  FORCED_INSTALL_ID: 'RYTM_RAND_UPDATE_FORCED_INSTALL_ID',
  /** Test-only override for the running version the client compares against. */
  CURRENT_VERSION: 'RYTM_RAND_UPDATE_CURRENT_VERSION',
} as const;

/**
 * I9 — the §7.1 consent-prompt labels, verbatim.
 *
 * Spec §7.1 ("Consent prompt — normative mockup") fixes these strings, their
 * order, and the default selection, with a pixel render at
 * `docs/design/update-consent-prompt.html`. Both are in the tree, and
 * `update_consent_labels.spec.ts` pins these constants against BOTH of them
 * unconditionally — so a drift in either direction is a red test rather than
 * a stale comment.
 *
 * Centralized so a §7.1 revision is one edit rather than a sweep through
 * seven spec files, and so a typo becomes a compile error instead of a
 * `getByRole('radio', {name: '…'})` that silently matches nothing and lets
 * an assertion pass against an element that was never rendered.
 */
export const CONSENT_LABELS = {
  /** Default (D3): install at the next natural exit — the I9 default radio. */
  installOnQuit: 'When I quit the app',
  /** Install immediately, restarting the app now. */
  installNow: 'Now — restart RytmRandomizer immediately',
  /** Suppress this version's chip until a newer version appears. */
  skipVersion: 'Skip this version',
} as const;

/**
 * I9 — the radio order as §7.1 renders it, top to bottom.
 *
 * Order is normative, not incidental: the pre-selected option sits first, so
 * the calm default is where the eye lands. A build that reorders the list
 * puts "restart immediately" under the cursor of an operator skimming
 * mid-set — precisely the interruption §1's safety model exists to forbid.
 */
export const CONSENT_LABEL_ORDER: readonly string[] = [
  CONSENT_LABELS.installOnQuit,
  CONSENT_LABELS.installNow,
  CONSENT_LABELS.skipVersion,
];

/** The label of the radio that must be pre-selected (I9 / D3). */
export const DEFAULT_CONSENT_LABEL: string = CONSENT_LABELS.installOnQuit;

/**
 * I9 — the §7.1 panel's static chrome copy (staged state).
 *
 * Asserted so the panel is recognisably the mockup rather than a set of
 * controls that merely carry the right radio labels. The section captions
 * are what make the prompt legible: an operator scanning for "what changed"
 * needs "What's new" to exist, and the phone-home honesty line
 * ("Last checked …") is a §7.1 contract element, not decoration.
 */
export const PANEL_COPY = {
  /** Header row: `Running vX · channel:` precedes the channel selector. */
  runningPrefix: 'Running',
  /** Header row: the channel-selector caption. */
  channel: 'channel:',
  /** Manual check control in the panel header row. */
  checkNow: 'Check now',
  /** Section caption above the manifest `notes` excerpt. */
  whatsNew: "What's new",
  /** The question above the three radios. */
  question: 'How do you want to install it?',
  /** Button that mints the per-version consent token. */
  confirm: 'Confirm choice',
  /** Caption above the I8 journal-tail list. */
  activity: 'Recent update activity',
  /** Footer: the phone-home honesty line prefix. */
  lastChecked: 'Last checked',
  /** Freeze toggle label (§7 env surface, in-UI half). */
  freeze: 'Freeze updates (stops all update network traffic)',
} as const;

/**
 * I9 — the five body variants of §7.1 ("same frame, body swapped — one
 * component, not five").
 *
 * Only what §7.1 fixes verbatim is pinned as a whole string; the
 * `up_to_date` and `check_failed` bodies interpolate a version and a reason
 * code respectively, so they are matched as prefixes. The fifth variant,
 * `rollout-excluded`, has no copy of its own — §5 makes it deliberately
 * indistinguishable from `up_to_date`, with the `bucket_excluded` journal
 * row as its only trace (asserted in `update_rollout_bucket.spec.ts`).
 */
export const PANEL_BODY_VARIANTS = {
  /** `You're on the latest version (vX). Next automatic check in about 4 hours.` */
  upToDatePrefix: "You're on the latest version",
  /** `Couldn't check for updates (<reason_code>). Will retry automatically.` */
  checkFailedPrefix: "Couldn't check for updates",
  /** Verbatim: the frozen body replaces everything but the toggle. */
  frozen: 'Updates are frozen. No update network traffic will occur until you unfreeze.',
  /** Verbatim: the dev-loop fallback is a sentence, not a broken control. */
  devLoop: 'Updates run in the installed app.',
} as const;

/** Test-ids the update UI is expected to expose (PR-B owns the markup). */
export const UPDATE_TESTIDS = {
  chip: 'update-chip',
  panel: 'update-panel',
  consentInstallNow: 'update-consent-install-now',
  consentInstallOnQuit: 'update-consent-install-on-quit',
  consentSkipVersion: 'update-consent-skip-version',
  consentConfirm: 'update-consent-confirm',
  hardwareBanner: 'update-hardware-revalidation-banner',
  activityList: 'update-activity-list',
  checkNow: 'update-check-now',
  freezeToggle: 'update-freeze-toggle',
  /**
   * The PRE-EXISTING SafetyRail operator log (`SafetyRail.tsx`), reused for
   * the §5.1 failure-honesty mirror. Named here — rather than inlined in the
   * one spec that needs it — to make the reuse explicit: §5.1 asks for
   * `check_failed` / `signature_rejected` to appear as operator-log entries
   * in the cockpit, i.e. in THIS list, not in an update-specific second log.
   * A new `update-operator-log` testid appearing in PR-B would be the R4
   * fork the plan forbids.
   */
  operatorLog: 'operator-log-list',
  /**
   * The PRE-EXISTING single global aria-live region (`a11y/LiveRegion.tsx`).
   * §7 requires the chip to be "announced once via the global announcer" —
   * this one, shared with the arm control and the reconnect banner. A
   * second live region for updates would double-announce every state change
   * on a screen reader, which is the "live-region countdown spam" §7 names.
   */
  liveRegion: 'a11y-live-region',
} as const;

interface UpdateFixtures {
  /** Manifest served at fixture setup; override with `test.use()`. */
  initialManifest: UpdateManifest | null;
  /** Extra env layered onto the sidecar spawn for update behavior. */
  updateEnv: Record<string, string>;
  /** Isolated config dir holding the journal / skip record / install id. */
  updateConfigRoot: string;
  /** The running mock manifest server. */
  manifestServer: MockManifestServer;
}

/**
 * The update-suite `test`. Fixture ordering matters: `manifestServer` and
 * `updateConfigRoot` must resolve BEFORE `sidecarEnv`, because the sidecar
 * spawn needs the server's ephemeral URL and the config root path in its
 * environment. Playwright resolves fixtures by dependency, so declaring
 * `sidecarEnv` in terms of the other two is what enforces that order —
 * there is deliberately no manual sequencing here to get wrong.
 */
export const test = wizardTest.extend<UpdateFixtures>({
  initialManifest: [null, { option: true }],
  updateEnv: [{}, { option: true }],

  // eslint-disable-next-line no-empty-pattern -- Playwright fixtures require destructuring
  updateConfigRoot: async ({}, use) => {
    const { root, cleanup } = makeUpdateConfigRoot();
    try {
      await use(root);
    } finally {
      cleanup();
    }
  },

  manifestServer: async ({ initialManifest }, use) => {
    const server =
      initialManifest === null
        ? await startMockManifestServer()
        : await startMockManifestServer(initialManifest);
    try {
      await use(server);
    } finally {
      await server.close();
    }
  },

  // Override the inherited `sidecarEnv` option so the sidecar spawn carries
  // the update configuration. Depending on the two fixtures above is what
  // guarantees they are constructed first (see the docstring).
  sidecarEnv: async ({ manifestServer, updateConfigRoot, updateEnv }, use) => {
    await use({
      [UPDATE_ENV.MANIFEST_URL]: manifestServer.manifestUrl,
      // The updater writes its journal into the config dir; the sidecar
      // fixture already isolates XDG_CONFIG_HOME/APPDATA per test, but the
      // updater is a different process in the bundled build, so it gets an
      // explicit root rather than inheriting one by luck.
      RYTM_RAND_UPDATE_CONFIG_DIR: updateConfigRoot,
      ...updateEnv,
    });
  },
});

export { expect };
