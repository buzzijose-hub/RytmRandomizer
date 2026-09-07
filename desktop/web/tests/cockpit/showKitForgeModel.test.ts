import { describe, expect, it } from 'vitest';

import {
  applyEntryMove,
  findActiveBank,
  findEntry,
  fingerprintMatchLabel,
  mismatchMessages,
  moveEntryIds,
  normalizePackId,
  showReadinessPanelSpec,
  shouldAdoptServerDraft,
} from '../../src/cockpit/showKitForge/showKitForgeModel';
import type { ShowBank, ShowBankEntry } from '../../src/ws/protocol';

import { forgeEntry, readyEntry, showBankState } from './showKitForgeFixture';

const bank = showBankState.banks[0] as ShowBank;

describe('Show Kit Forge model selectors', () => {
  it('preserves unsaved metadata through unrelated authoritative revisions', () => {
    expect(shouldAdoptServerDraft(false, true, false)).toBe(false);
    expect(shouldAdoptServerDraft(true, true, false)).toBe(true);
    expect(shouldAdoptServerDraft(false, false, false)).toBe(true);
    expect(shouldAdoptServerDraft(false, true, true)).toBe(true);
  });

  it('dispatches only valid cue moves', () => {
    const moves: string[][] = [];
    expect(applyEntryMove(bank.entries, 'entry-one', -1, (ids) => moves.push(ids))).toBe(false);
    expect(moves).toEqual([]);
    expect(applyEntryMove(bank.entries, 'entry-one', 1, (ids) => moves.push(ids))).toBe(true);
    expect(moves).toEqual([['entry-two', 'entry-one']]);
  });

  it('withholds current readiness while cached state waits for a fresh connection packet', () => {
    const spec = showReadinessPanelSpec(bank, readyEntry, true);
    expect(spec.status_badges).toEqual([{ label: 'Readiness unavailable — refresh required', tone: 'warn', icon: '•' }]);
    expect(spec.required_actions).toContain('Refresh from server.');
  });

  it('normalizes bank titles to lowercase filename-safe package IDs', () => {
    expect(normalizePackId('  Friday @ Warehouse!  ')).toBe('friday-warehouse');
    expect(normalizePackId('___')).toBe('show-bank');
    expect(normalizePackId(`A${'B'.repeat(120)}`)).toHaveLength(96);
  });

  it('labels fingerprint comparisons without hiding mismatches in color', () => {
    expect(fingerprintMatchLabel(true)).toBe('Match');
    expect(fingerprintMatchLabel(false)).toBe('Mismatch');
  });

  it('finds only the explicitly active server bank', () => {
    expect(findActiveBank(null)).toBeNull();
    expect(findActiveBank({ ...showBankState, active_bank_id: null })).toBeNull();
    expect(findActiveBank({ ...showBankState, active_bank_id: 'missing' })).toBeNull();
    expect(findActiveBank(showBankState)).toBe(bank);
  });

  it('selects an explicit entry, server-active fallback, then cue-order fallback', () => {
    expect(findEntry(null, null)).toBeNull();
    expect(findEntry({ ...bank, entries: [] }, null)).toBeNull();
    expect(findEntry(bank, 'entry-two')).toBe(readyEntry);
    expect(findEntry(bank, 'missing')).toBe(forgeEntry);
    expect(findEntry({ ...bank, active_entry_id: 'missing' }, null)).toBe(forgeEntry);
    expect(
      findEntry({ ...bank, active_entry_id: null, entries: [readyEntry, forgeEntry] }, null),
    ).toBe(forgeEntry);
  });

  it('moves entries in canonical cue order and refuses invalid/boundary moves', () => {
    expect(moveEntryIds(bank.entries, 'missing', 1)).toBeNull();
    expect(moveEntryIds(bank.entries, 'entry-one', -1)).toBeNull();
    expect(moveEntryIds(bank.entries, 'entry-two', 1)).toBeNull();
    expect(moveEntryIds(bank.entries, 'entry-one', 1)).toEqual(['entry-two', 'entry-one']);
    expect(moveEntryIds(bank.entries, 'entry-two', -1)).toEqual(['entry-two', 'entry-one']);
  });

  it('returns only explicit server mismatch explanations', () => {
    expect(mismatchMessages(null)).toEqual([]);
    expect(mismatchMessages({ ...forgeEntry, rytm_recapture: null, analog_four_recapture: null })).toEqual([]);
    expect(mismatchMessages(forgeEntry)).toEqual([
      'Analog Four semantic fingerprint mismatch: expected 25555555; observed 99999999. ' +
        'Immutable source 99999999: observed capture matches source. ' +
        'Analog Four semantic fingerprint differs from favorite',
    ]);
    const unavailable: ShowBankEntry = {
      ...forgeEntry,
      analog_four_recapture: {
        ...(forgeEntry.analog_four_recapture as NonNullable<typeof forgeEntry.analog_four_recapture>),
        observed_semantic_fingerprint: null,
        comparison_reason: 'Semantic decode unavailable',
      },
    };
    expect(mismatchMessages(unavailable)[0]).toContain('observed unavailable');
    expect(mismatchMessages({
      ...unavailable,
      analog_four_recapture: { ...unavailable.analog_four_recapture!, matches_source: false },
    })[0]).toContain('observed capture does not match source');

    const preflightMismatch: ShowBankEntry = {
      ...readyEntry,
      show_ready_at: null,
      status: 'verified',
      show_time_preflight: {
        ...(readyEntry.show_time_preflight as NonNullable<typeof readyEntry.show_time_preflight>),
        observed_rytm_fingerprint: 'deadbeef',
        rytm_matches: false,
        observed_a4_fingerprint: 'bad4face',
        a4_matches: false,
        reason: 'Fresh current captures differ',
      },
    };
    expect(mismatchMessages(preflightMismatch)).toEqual([
      'Rytm show-time full fingerprint mismatch: expected 23333333; observed deadbeef. ' +
        'Fresh current captures differ',
      'Analog Four show-time full fingerprint mismatch: expected 14444444; observed bad4face. ' +
        'Fresh current captures differ',
    ]);
    expect(mismatchMessages(readyEntry)).toEqual([]);
  });

  it('formats empty, blocked, neutral, and ready authoritative readiness packets', () => {
    const empty = showReadinessPanelSpec(null, null);
    expect(empty.status_badges[0]).toMatchObject({ label: 'Waiting for a bank', tone: 'neutral' });
    expect(empty.safety_lines).toContain('No demo fallback');

    const blocked = showReadinessPanelSpec(bank, forgeEntry);
    expect(blocked.status_badges).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          label: 'Bank: Manually saved — attested/unverified',
          tone: 'warn',
        }),
        expect.objectContaining({
          label: 'Active cue: Manually saved — attested/unverified',
          tone: 'warn',
        }),
      ]),
    );
    expect(blocked.sections[0]?.rows).toEqual(['One or more cues still need a fresh show-time preflight.']);
    expect(blocked.sections[1]?.rows).toEqual(['The Analog Four recapture does not match the candidate.']);
    expect(blocked.required_actions).toEqual([
      'Bank: verify_entry_one',
      'Active cue: recapture_intended_a4_slot',
    ]);

    const bankReadiness = showReadinessPanelSpec(bank, null);
    expect(bankReadiness.status_badges[0]).toMatchObject({
      label: 'Bank: Manually saved — attested/unverified',
    });

    const neutralEntry: ShowBankEntry = {
      ...forgeEntry,
      readiness: { status: 'candidate', show_ready: false, blocked_reasons: [], recovery_actions: [] },
    };
    const neutralBank = {
      ...bank,
      readiness: {
        status: 'candidate' as const,
        show_ready: false,
        show_ready_entry_ids: [],
        blocked_reasons: [],
        recovery_actions: [],
      },
    };
    expect(showReadinessPanelSpec(neutralBank, neutralEntry).status_badges[0]).toMatchObject({
      tone: 'neutral',
    });

    const readyBank = {
      ...bank,
      readiness: {
        status: 'show-ready' as const,
        show_ready: true,
        show_ready_entry_ids: ['entry-one', 'entry-two'],
        blocked_reasons: [],
        recovery_actions: [],
      },
    };
    const ready = showReadinessPanelSpec(readyBank, readyEntry);
    expect(ready.status_badges[0]).toMatchObject({
      label: 'Bank: Show-ready',
      tone: 'ok',
      icon: '✓',
    });
  });
});
