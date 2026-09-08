/**
 * `src/updateProtocol.ts` — the single TS home for the I2 event shape and
 * the I8 journal row shape (reuse contract R4).
 *
 * These tests pin the contract itself: the closed state / event / consent
 * vocabularies, the default consent choice (spec §7.1 + decision D3), the
 * untrusted-payload parsers, the chip predicate, and the adapter that lets
 * the journal render through the SHARED operator-log list rather than a
 * forked second list component.
 */

import { describe, expect, it } from 'vitest';

import {
  DEFAULT_CONSENT_CHOICE,
  MIRRORED_FAILURE_EVENTS,
  UPDATE_CHANNELS,
  UPDATE_CONSENT_CHOICES,
  UPDATE_JOURNAL_EVENTS,
  UPDATE_JOURNAL_LIMIT,
  UPDATE_STATES,
  UPDATE_STATE_EVENT_NAME,
  chipLabel,
  isConsentPending,
  isMirroredFailure,
  isUpdateJournalEvent,
  isUpdateState,
  journalLogEntries,
  journalRowLevel,
  journalRowText,
  mirroredFailureMessage,
  parseUpdateJournalRow,
  parseUpdateStateEvent,
  recentJournal,
  shouldShowChip,
  type UpdateJournalRow,
  type UpdateSlice,
  confirmUpdateChoiceOnShell,
  requestUpdateCheck,
} from '../src/updateProtocol';

function row(over: Partial<UpdateJournalRow> = {}): UpdateJournalRow {
  return { ts: '12:04', event: 'check_ok', version: '1.35.1', detail: 'ok', ...over };
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

describe('closed vocabularies', () => {
  it('pins the §5 client state vocabulary', () => {
    expect([...UPDATE_STATES]).toEqual([
      'idle',
      'checking',
      'up_to_date',
      'check_failed',
      'update_available',
      'downloading',
      'staged',
      'stage_failed',
      'installing',
      'frozen',
      'dev_loop',
    ]);
  });

  it('pins the §5.1 journal event vocabulary exactly (17 events)', () => {
    expect([...UPDATE_JOURNAL_EVENTS]).toEqual([
      'check_started',
      'check_ok',
      'check_failed',
      'manifest_rejected',
      'bucket_excluded',
      'download_started',
      'download_ok',
      'stage_failed',
      'signature_rejected',
      'consent_granted',
      'install_started',
      'install_ok',
      'install_failed',
      'skip_recorded',
      'freeze_suppressed',
      'ping_ok',
      'ping_failed',
    ]);
  });

  it('orders the consent choices per the normative §7.1 mockup', () => {
    expect([...UPDATE_CONSENT_CHOICES]).toEqual([
      'install_on_quit',
      'install_now',
      'skip_this_version',
    ]);
  });

  it('pre-selects "install on quit" (decision D3)', () => {
    expect(DEFAULT_CONSENT_CHOICE).toBe('install_on_quit');
    expect(UPDATE_CONSENT_CHOICES[0]).toBe(DEFAULT_CONSENT_CHOICE);
  });

  it('exposes the two channels and the shell event name', () => {
    expect([...UPDATE_CHANNELS]).toEqual(['stable', 'beta']);
    expect(UPDATE_STATE_EVENT_NAME).toBe('rytm-update-state');
  });
});

describe('type guards', () => {
  it('accepts known states and refuses everything else', () => {
    expect(isUpdateState('staged')).toBe(true);
    expect(isUpdateState('exploded')).toBe(false);
    expect(isUpdateState(7)).toBe(false);
  });

  it('accepts known journal events and refuses everything else', () => {
    expect(isUpdateJournalEvent('signature_rejected')).toBe(true);
    expect(isUpdateJournalEvent('whatever')).toBe(false);
    expect(isUpdateJournalEvent(null)).toBe(false);
  });
});

describe('parseUpdateStateEvent (I2, untrusted)', () => {
  it('narrows a well-formed payload', () => {
    expect(
      parseUpdateStateEvent({
        state: 'staged',
        version: '1.35.1',
        notes: 'line',
        hardware_revalidation: true,
        error_code: 'ignored',
      }),
    ).toEqual({
      state: 'staged',
      version: '1.35.1',
      notes: 'line',
      hardware_revalidation: true,
      error_code: 'ignored',
    });
  });

  it('fills missing / wrongly-typed optional fields rather than throwing', () => {
    expect(
      parseUpdateStateEvent({ state: 'up_to_date', version: 3, notes: null, error_code: '' }),
    ).toEqual({
      state: 'up_to_date',
      version: '',
      notes: '',
      hardware_revalidation: false,
      error_code: null,
    });
  });

  it('refuses a non-object, null, or unknown-state payload', () => {
    expect(parseUpdateStateEvent(null)).toBeNull();
    expect(parseUpdateStateEvent('staged')).toBeNull();
    expect(parseUpdateStateEvent({ state: 'nope' })).toBeNull();
  });
});

describe('parseUpdateJournalRow (I8, untrusted)', () => {
  it('narrows a well-formed row', () => {
    expect(
      parseUpdateJournalRow({ ts: 't', event: 'ping_ok', version: '1', detail: 'd' }),
    ).toEqual({ ts: 't', event: 'ping_ok', version: '1', detail: 'd' });
  });

  it('defaults non-string fields to the empty string', () => {
    expect(parseUpdateJournalRow({ event: 'ping_ok' })).toEqual({
      ts: '',
      event: 'ping_ok',
      version: '',
      detail: '',
    });
  });

  it('refuses a non-object or unknown-event row', () => {
    expect(parseUpdateJournalRow(null)).toBeNull();
    expect(parseUpdateJournalRow(42)).toBeNull();
    expect(parseUpdateJournalRow({ event: 'not_in_vocabulary' })).toBeNull();
  });
});

describe('chip visibility (§7: staged and unfrozen only)', () => {
  const staged = { state: 'staged' as const, version: '1.35.1', notes: '', hardware_revalidation: false, error_code: null };

  it('shows for a staged, unfrozen, unconfirmed update', () => {
    const s = slice({ state: staged });
    expect(isConsentPending(s)).toBe(true);
    expect(shouldShowChip(s)).toBe(true);
  });

  it('hides in freeze mode', () => {
    expect(shouldShowChip(slice({ state: staged, frozen: true }))).toBe(false);
  });

  it('hides once the operator has confirmed a choice', () => {
    expect(shouldShowChip(slice({ state: staged, confirmedChoice: 'install_now' }))).toBe(false);
  });

  it('hides with no shell state at all (dev loop)', () => {
    expect(shouldShowChip(slice())).toBe(false);
  });

  it('hides for every non-staged state (rollout-excluded looks up-to-date)', () => {
    expect(
      shouldShowChip(
        slice({
          state: { ...staged, state: 'up_to_date' },
        }),
      ),
    ).toBe(false);
  });

  it('renders icon + text, never colour alone', () => {
    expect(chipLabel('1.35.1')).toBe('⬆ 1.35.1 ready');
  });
});

describe('journal tail rendering', () => {
  it('returns newest first, bounded by the limit (spec §7.1 table)', () => {
    const journal = Array.from({ length: UPDATE_JOURNAL_LIMIT + 3 }, (_unused, i) =>
      row({ ts: `t${i}` }),
    );
    const recent = recentJournal(journal);
    expect(recent).toHaveLength(UPDATE_JOURNAL_LIMIT);
    expect(recent[0]!.ts).toBe(`t${UPDATE_JOURNAL_LIMIT + 2}`);
    expect(recent[recent.length - 1]!.ts).toBe('t3');
  });

  it('honours an explicit limit', () => {
    expect(recentJournal([row({ ts: 'a' }), row({ ts: 'b' })], 1)).toEqual([row({ ts: 'b' })]);
  });

  it('grades severity from the event code alone', () => {
    expect(journalRowLevel('signature_rejected')).toBe('error');
    expect(journalRowLevel('install_failed')).toBe('error');
    expect(journalRowLevel('download_ok')).toBe('success');
    expect(journalRowLevel('check_started')).toBe('info');
    expect(journalRowLevel('bucket_excluded')).toBe('info');
  });

  it('flattens a row to the §7.1 reading order and drops empty fields', () => {
    expect(journalRowText(row({ ts: '12:04', event: 'download_ok', detail: '42 MB · 6 s' }))).toBe(
      '12:04  download_ok  42 MB · 6 s',
    );
    expect(journalRowText(row({ ts: '', detail: '' }))).toBe('check_ok');
  });

  it('adapts rows into shared operator-log-list entries with stable ids', () => {
    const entries = journalLogEntries([row({ ts: 'a' }), row({ ts: 'b', event: 'ping_failed' })]);
    expect(entries).toHaveLength(2);
    expect(entries[0]).toEqual({
      id: 'update-journal-0-b-ping_failed',
      level: 'error',
      message: 'b  ping_failed  ok',
    });
    expect(entries[1]!.level).toBe('success');
  });

  it('respects an explicit limit when adapting', () => {
    expect(journalLogEntries([row({ ts: 'a' }), row({ ts: 'b' })], 1)).toHaveLength(1);
  });
});

describe('failure mirroring (§5.1 honesty floor)', () => {
  it('mirrors exactly check_failed and signature_rejected', () => {
    expect([...MIRRORED_FAILURE_EVENTS]).toEqual(['check_failed', 'signature_rejected']);
    expect(isMirroredFailure(row({ event: 'check_failed' }))).toBe(true);
    expect(isMirroredFailure(row({ event: 'signature_rejected' }))).toBe(true);
    expect(isMirroredFailure(row({ event: 'stage_failed' }))).toBe(false);
  });

  it('builds a bounded message, substituting for a missing detail', () => {
    expect(mirroredFailureMessage(row({ event: 'check_failed', detail: 'manifest_unreachable' }))).toBe(
      'Update check_failed: manifest_unreachable',
    );
    expect(mirroredFailureMessage(row({ event: 'check_failed', detail: '' }))).toBe(
      'Update check_failed: no detail',
    );
  });
});

describe('shell command bindings', () => {
  // These are the ONLY two ways the panel reaches the updater. Before they
  // existed the buttons were decorative — "Check now" set a note and "Confirm
  // choice" updated React state, and neither reached the driver.

  it('requestUpdateCheck resolves without a shell rather than throwing', async () => {
    // The dev loop and a plain browser have no Tauri bridge. A throw here
    // would propagate out of the click handler and blank the cockpit over a
    // check that simply cannot happen.
    await expect(requestUpdateCheck()).resolves.toBeUndefined();
  });

  it('confirmUpdateChoiceOnShell reports failure rather than claiming success', async () => {
    // Without a shell the consent cannot be delivered. Returning `false` is
    // what lets the panel tell the operator; returning `true` would show
    // "choice recorded" for a decision that reached nothing.
    await expect(
      confirmUpdateChoiceOnShell('1.35.1', 'install_on_quit'),
    ).resolves.toBe(false);
  });
});
