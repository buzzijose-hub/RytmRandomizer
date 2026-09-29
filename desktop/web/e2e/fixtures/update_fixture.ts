/**
 * Static I9 copy references for the specification/design consistency test.
 * Actual updater acceptance uses native_update_fixture and the real Tauri shell.
 * This file owns no process fixture or update environment overrides.
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
 * row as its only trace (covered by the native acceptance target).
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
