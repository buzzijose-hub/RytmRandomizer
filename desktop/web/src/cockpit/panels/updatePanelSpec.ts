/**
 * Updates panel — pure `PanelSpec` selector over the update slice
 * (no React, no fetch, no state, and above all no transmit).
 *
 * Renders the normative spec §7.1 mockup: the running version + channel
 * line, the staged block with the update version and "What's new", the
 * hardware-revalidation warning when and only when the manifest flags it,
 * and the honesty line naming the last check and the last check-in ping.
 *
 * The five §7.1 body variants are ONE selector with a swapped body section,
 * not five components: `bodySections()` is the single switch.
 *
 * The "Recent update activity" list is deliberately NOT a section here — it
 * renders through the shared `OperatorLogList` component (reuse contract
 * R4), so there is exactly one log-list implementation in the cockpit.
 *
 * Labels here are the UX contract (plan I9) — the e2e suite asserts these
 * exact strings, so they are copied from §7.1 character for character and
 * must not be reworded without changing the spec first.
 */

import type { BadgeDict, PanelSectionDict, PanelSpecDict } from '../../types/live_gui_protocol';
import type { UpdateJournalRow, UpdateSlice } from '../../updateProtocol';

/** Spec §7.1 body copy. Exported so unit tests and e2e assert one source. */
export const UPDATE_COPY = {
  panelTitle: 'UPDATES',
  whatsNew: "What's new",
  hardwareWarning:
    'This update changes hardware send paths. Re-run the manual hardware ' +
    'validation checklist after installing.',
  hardwareDoc: 'docs/MANUAL_HARDWARE_VALIDATION.md',
  consentQuestion: 'How do you want to install it?',
  activityHeading: 'Recent update activity',
  activityEmpty: 'No update activity recorded yet.',
  freezeToggle: 'Freeze updates (stops all update network traffic)',
  frozenBody: 'Updates are frozen. No update network traffic will occur until you unfreeze.',
  devLoopBody: 'Updates run in the installed app.',
  checkNow: 'Check now',
  confirmChoice: 'Confirm choice',
  noNotes: 'No release notes provided.',
} as const;

/** Radio labels, in the normative §7.1 order (first is pre-selected). */
export const CONSENT_LABELS = {
  install_on_quit: 'When I quit the app',
  install_now: 'Now — restart RytmRandomizer immediately',
  skip_this_version: 'Skip this version',
} as const;

/** `You're on the latest version (v1.35.0). Next automatic check in about 4 hours.` */
export function upToDateLine(runningVersion: string): string {
  return `You're on the latest version (v${runningVersion}). Next automatic check in about 4 hours.`;
}

/** `Couldn't check for updates (manifest_unreachable). Will retry automatically.` */
export function checkFailedLine(reasonCode: string): string {
  return `Couldn't check for updates (${reasonCode}). Will retry automatically.`;
}

/** `⬆ Update ready: v1.35.1` */
export function stagedHeadline(version: string): string {
  return `⬆ Update ready: v${version}`;
}

/** `Running v1.35.0 · channel: stable` */
export function runningLine(runningVersion: string, channel: string): string {
  return `Running v${runningVersion} · channel: ${channel}`;
}

function lastTimestampFor(
  journal: ReadonlyArray<UpdateJournalRow>,
  events: ReadonlyArray<string>,
): string {
  for (let index = journal.length - 1; index >= 0; index -= 1) {
    const row = journal[index];
    if (row !== undefined && events.includes(row.event) && row.ts !== '') {
      return row.ts;
    }
  }
  return 'never';
}

/**
 * The honesty line: what phoned home, and when. Sourced from the journal's
 * `check_*` / `ping_*` rows only — never from a clock the panel reads
 * itself, because the panel must not claim a check it cannot evidence.
 */
export function honestyLine(journal: ReadonlyArray<UpdateJournalRow>): string {
  const lastCheck = lastTimestampFor(journal, ['check_ok', 'check_failed']);
  const lastPing = lastTimestampFor(journal, ['ping_ok', 'ping_failed']);
  return `Last checked ${lastCheck} · Last check-in ping ${lastPing}`;
}

function rowsSection(heading: string, rows: ReadonlyArray<string>): PanelSectionDict {
  return { heading, kind: 'rows', rows: [...rows], table: null, chips: [] };
}

/** Status badge — icon + text, never hue alone. */
function updateBadge(slice: UpdateSlice): BadgeDict {
  if (slice.frozen) return { label: 'frozen', tone: 'neutral', icon: '❄' };
  const state = slice.state;
  if (state === null) return { label: 'dev loop', tone: 'neutral', icon: '•' };
  if (state.state === 'staged') return { label: 'update ready', tone: 'ok', icon: '⬆' };
  if (state.state === 'check_failed' || state.state === 'stage_failed') {
    return { label: state.state, tone: 'warn', icon: '!' };
  }
  if (state.state === 'up_to_date') return { label: 'up to date', tone: 'ok', icon: '✓' };
  return { label: state.state, tone: 'neutral', icon: '◌' };
}

/** Manifest notes split into list lines; blank lines dropped. */
function notesLines(notes: string): ReadonlyArray<string> {
  return notes
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line !== '');
}

/**
 * The five §7.1 body variants — one switch, one component.
 *
 * Precedence is deliberate: freeze wins over everything (it is the
 * performance-mode guarantee), then the absence of a shell (dev loop),
 * then whatever the shell last reported. `rollout-excluded` has no branch
 * of its own by design — the shell reports it as `up_to_date` and the only
 * trace is the journal's `bucket_excluded` row (§5).
 */
export function bodySections(
  slice: UpdateSlice,
  runningVersion: string,
): ReadonlyArray<PanelSectionDict> {
  if (slice.frozen) {
    return [rowsSection('Status', [UPDATE_COPY.frozenBody])];
  }
  const state = slice.state;
  if (state === null) {
    return [rowsSection('Status', [UPDATE_COPY.devLoopBody])];
  }
  if (state.state === 'check_failed') {
    return [rowsSection('Status', [checkFailedLine(state.error_code ?? 'unknown_reason')])];
  }
  if (state.state === 'staged') {
    const staged: PanelSectionDict[] = [
      rowsSection('Status', [stagedHeadline(state.version)]),
      rowsSection(
        UPDATE_COPY.whatsNew,
        state.notes === '' ? [UPDATE_COPY.noNotes] : notesLines(state.notes),
      ),
    ];
    if (state.hardware_revalidation) {
      staged.push(
        rowsSection('Hardware revalidation', [
          `⚠ ${UPDATE_COPY.hardwareWarning}`,
          `→ ${UPDATE_COPY.hardwareDoc}`,
        ]),
      );
    }
    return staged;
  }
  return [rowsSection('Status', [upToDateLine(runningVersion)])];
}

/**
 * Build the passive PanelSpec for the update surface.
 *
 * `runningVersion` is `session_status.app_version` (plan I1); callers pass
 * `'unknown'` when the sidecar has not reported one rather than guessing.
 */
export function updatePanelSpec(slice: UpdateSlice, runningVersion: string): PanelSpecDict {
  return {
    panel_id: 'updates',
    title: UPDATE_COPY.panelTitle,
    status_badges: [updateBadge(slice)],
    sections: [
      rowsSection('Running', [runningLine(runningVersion, slice.channel)]),
      ...bodySections(slice, runningVersion),
      rowsSection('Phone-home honesty', [honestyLine(slice.journal)]),
    ],
    required_actions: [],
    blocked_actions: [],
    safety_lines: ['checks are passive; installing always asks first'],
  };
}
