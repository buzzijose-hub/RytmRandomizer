/**
 * `updatePanelSpec` — the pure §7.1 selector.
 *
 * Every assertion here is against a string copied character-for-character
 * from spec §7.1 (plan contract I9). The e2e suite asserts the same strings
 * through the DOM; if these two ever disagree, the spec section wins.
 */

import { describe, expect, it } from 'vitest';

import {
  CONSENT_LABELS,
  UPDATE_COPY,
  bodySections,
  checkFailedLine,
  honestyLine,
  runningLine,
  stagedHeadline,
  updatePanelSpec,
  upToDateLine,
} from '../../../src/cockpit/panels/updatePanelSpec';
import type { UpdateJournalRow, UpdateSlice, UpdateStateEvent } from '../../../src/updateProtocol';

function state(over: Partial<UpdateStateEvent> = {}): UpdateStateEvent {
  return {
    state: 'staged',
    version: '1.35.1',
    notes: '',
    hardware_revalidation: false,
    error_code: null,
    ...over,
  };
}

function slice(over: Partial<UpdateSlice> = {}): UpdateSlice {
  return {
    state: null,
    journal: [],
    channel: 'stable',
    frozen: false,
    confirmedChoice: null,
    ...over,
  };
}

function row(over: Partial<UpdateJournalRow> = {}): UpdateJournalRow {
  return { ts: '12:04', event: 'check_ok', version: '1.35.1', detail: '', ...over };
}

describe('§7.1 normative copy', () => {
  it('pins the three consent labels in order', () => {
    expect(CONSENT_LABELS.install_on_quit).toBe('When I quit the app');
    expect(CONSENT_LABELS.install_now).toBe('Now — restart RytmRandomizer immediately');
    expect(CONSENT_LABELS.skip_this_version).toBe('Skip this version');
  });

  it('pins the fixed panel strings', () => {
    expect(UPDATE_COPY.panelTitle).toBe('UPDATES');
    expect(UPDATE_COPY.whatsNew).toBe("What's new");
    expect(UPDATE_COPY.consentQuestion).toBe('How do you want to install it?');
    expect(UPDATE_COPY.activityHeading).toBe('Recent update activity');
    expect(UPDATE_COPY.checkNow).toBe('Check now');
    expect(UPDATE_COPY.confirmChoice).toBe('Confirm choice');
    expect(UPDATE_COPY.freezeToggle).toBe('Freeze updates (stops all update network traffic)');
    expect(UPDATE_COPY.hardwareWarning).toBe(
      'This update changes hardware send paths. Re-run the manual hardware ' +
        'validation checklist after installing.',
    );
    expect(UPDATE_COPY.hardwareDoc).toBe('docs/MANUAL_HARDWARE_VALIDATION.md');
  });

  it('pins the variant body sentences', () => {
    expect(upToDateLine('1.35.0')).toBe(
      "You're on the latest version (v1.35.0). Next automatic check in about 4 hours.",
    );
    expect(checkFailedLine('manifest_unreachable')).toBe(
      "Couldn't check for updates (manifest_unreachable). Will retry automatically.",
    );
    expect(stagedHeadline('1.35.1')).toBe('⬆ Update ready: v1.35.1');
    expect(runningLine('1.35.0', 'stable')).toBe('Running v1.35.0 · channel: stable');
    expect(UPDATE_COPY.frozenBody).toBe(
      'Updates are frozen. No update network traffic will occur until you unfreeze.',
    );
    expect(UPDATE_COPY.devLoopBody).toBe('Updates run in the installed app.');
  });
});

describe('bodySections — one switch, five variants', () => {
  it('freeze wins over every other state', () => {
    const sections = bodySections(slice({ frozen: true, state: state() }), '1.35.0');
    expect(sections).toHaveLength(1);
    expect(sections[0]!.rows).toEqual([UPDATE_COPY.frozenBody]);
  });

  it('renders the dev-loop sentence when the shell never spoke', () => {
    expect(bodySections(slice(), '1.35.0')[0]!.rows).toEqual([UPDATE_COPY.devLoopBody]);
  });

  it('renders check_failed with the reason code verbatim', () => {
    const sections = bodySections(
      slice({ state: state({ state: 'check_failed', error_code: 'manifest_unreachable' }) }),
      '1.35.0',
    );
    expect(sections[0]!.rows).toEqual([
      "Couldn't check for updates (manifest_unreachable). Will retry automatically.",
    ]);
  });

  it('substitutes a placeholder reason when the shell sent none', () => {
    const sections = bodySections(
      slice({ state: state({ state: 'check_failed', error_code: null }) }),
      '1.35.0',
    );
    expect(sections[0]!.rows[0]).toContain('(unknown_reason)');
  });

  it('renders the staged block with notes split into lines', () => {
    const sections = bodySections(
      slice({ state: state({ notes: 'first\n\n  second  \n' }) }),
      '1.35.0',
    );
    expect(sections[0]!.rows).toEqual(['⬆ Update ready: v1.35.1']);
    expect(sections[1]!.heading).toBe("What's new");
    expect(sections[1]!.rows).toEqual(['first', 'second']);
    expect(sections).toHaveLength(2);
  });

  it('says so honestly when the manifest carried no notes', () => {
    const sections = bodySections(slice({ state: state({ notes: '' }) }), '1.35.0');
    expect(sections[1]!.rows).toEqual([UPDATE_COPY.noNotes]);
  });

  it('adds the hardware banner ONLY when I2 flags it', () => {
    const flagged = bodySections(
      slice({ state: state({ hardware_revalidation: true }) }),
      '1.35.0',
    );
    expect(flagged).toHaveLength(3);
    expect(flagged[2]!.rows).toEqual([
      `⚠ ${UPDATE_COPY.hardwareWarning}`,
      `→ ${UPDATE_COPY.hardwareDoc}`,
    ]);
  });

  it('falls through to up_to_date for every remaining state', () => {
    for (const s of ['idle', 'checking', 'up_to_date', 'downloading', 'installing'] as const) {
      const sections = bodySections(slice({ state: state({ state: s }) }), '1.35.0');
      expect(sections[0]!.rows).toEqual([upToDateLine('1.35.0')]);
    }
  });
});

describe('honestyLine — evidenced, never invented', () => {
  it('says "never" with an empty journal', () => {
    expect(honestyLine([])).toBe('Last checked never · Last check-in ping never');
  });

  it('reads the latest check_* and ping_* timestamps', () => {
    expect(
      honestyLine([
        row({ ts: '11:00', event: 'check_ok' }),
        row({ ts: '11:30', event: 'ping_failed' }),
        row({ ts: '12:04', event: 'check_failed' }),
        row({ ts: '12:05', event: 'ping_ok' }),
      ]),
    ).toBe('Last checked 12:04 · Last check-in ping 12:05');
  });

  it('ignores rows with no timestamp and unrelated events', () => {
    expect(honestyLine([row({ ts: '', event: 'check_ok' }), row({ event: 'download_ok' })])).toBe(
      'Last checked never · Last check-in ping never',
    );
  });
});

describe('updatePanelSpec', () => {
  it('leads with the running-version line and ends with the honesty line', () => {
    const spec = updatePanelSpec(slice({ channel: 'beta' }), '1.35.0');
    expect(spec.panel_id).toBe('updates');
    expect(spec.title).toBe('UPDATES');
    expect(spec.sections[0]!.rows).toEqual(['Running v1.35.0 · channel: beta']);
    const last = spec.sections[spec.sections.length - 1]!;
    expect(last.heading).toBe('Phone-home honesty');
    expect(last.rows[0]).toContain('Last checked');
  });

  it('carries no interactive actions — the panel is passive', () => {
    const spec = updatePanelSpec(slice(), '1.35.0');
    expect(spec.required_actions).toEqual([]);
    expect(spec.blocked_actions).toEqual([]);
    expect(spec.safety_lines).toEqual(['checks are passive; installing always asks first']);
  });

  it('does NOT carry the activity list as a section (it reuses the shared log list)', () => {
    const spec = updatePanelSpec(slice({ journal: [row()] }), '1.35.0');
    expect(spec.sections.map((s) => s.heading)).not.toContain(UPDATE_COPY.activityHeading);
  });

  it('badges every state with an icon + text pair', () => {
    const cases: ReadonlyArray<[UpdateSlice, string, string]> = [
      [slice({ frozen: true }), 'frozen', '❄'],
      [slice(), 'dev loop', '•'],
      [slice({ state: state() }), 'update ready', '⬆'],
      [slice({ state: state({ state: 'check_failed' }) }), 'check_failed', '!'],
      [slice({ state: state({ state: 'stage_failed' }) }), 'stage_failed', '!'],
      [slice({ state: state({ state: 'up_to_date' }) }), 'up to date', '✓'],
      [slice({ state: state({ state: 'downloading' }) }), 'downloading', '◌'],
    ];
    for (const [input, label, icon] of cases) {
      const badge = updatePanelSpec(input, '1.35.0').status_badges[0]!;
      expect(badge.label).toBe(label);
      expect(badge.icon).toBe(icon);
    }
  });
});
