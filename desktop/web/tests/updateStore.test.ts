/**
 * The additive `update` store slice.
 *
 * The slice is a mirror: it holds the last I2 payload the shell pushed, the
 * I8 journal tail, and the operator's own channel / freeze / consent
 * choices. It derives nothing and initiates nothing. What it DOES enforce is
 * §5's per-version consent rule and §5.1's failure-honesty floor.
 */

import { beforeEach, describe, expect, it } from 'vitest';

import { INITIAL_STATE, createCockpitStore } from '../src/state';
import { UPDATE_JOURNAL_LIMIT, type UpdateJournalRow, type UpdateStateEvent } from '../src/updateProtocol';

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

function row(over: Partial<UpdateJournalRow> = {}): UpdateJournalRow {
  return { ts: '12:04', event: 'check_ok', version: '1.35.1', detail: 'ok', ...over };
}

let store: ReturnType<typeof createCockpitStore>;

beforeEach(() => {
  store = createCockpitStore();
});

describe('initial state', () => {
  it('starts silent: no shell state, no journal, stable, unfrozen', () => {
    expect(INITIAL_STATE.update).toEqual({
      state: null,
      journal: [],
      channel: 'stable',
      frozen: false,
      confirmedChoice: null,
    });
  });

  it('resets the update slice with the rest of the store', () => {
    store.getState().setUpdateFrozen(true);
    store.getState().reset();
    expect(store.getState().update.frozen).toBe(false);
  });
});

describe('setUpdateState — consent is per-version (§5)', () => {
  it('stores the payload the shell pushed', () => {
    store.getState().setUpdateState(state());
    expect(store.getState().update.state).toEqual(state());
  });

  it('keeps a confirmed choice when the same version is re-reported', () => {
    store.getState().setUpdateState(state());
    store.getState().confirmUpdateChoice('install_on_quit');
    store.getState().setUpdateState(state({ notes: 'refreshed' }));
    expect(store.getState().update.confirmedChoice).toBe('install_on_quit');
  });

  it('voids a confirmed choice when a NEWER version supersedes it', () => {
    store.getState().setUpdateState(state());
    store.getState().confirmUpdateChoice('install_on_quit');
    store.getState().setUpdateState(state({ version: '1.36.0' }));
    expect(store.getState().update.confirmedChoice).toBeNull();
  });

  it('keeps a choice made before any state arrived (nothing to supersede)', () => {
    store.getState().confirmUpdateChoice('skip_this_version');
    store.getState().setUpdateState(state());
    expect(store.getState().update.confirmedChoice).toBe('skip_this_version');
  });
});

describe('setUpdateJournal — bounded tail + §5.1 honesty floor', () => {
  it('keeps only the tail, oldest first, at the protocol limit', () => {
    const journal = Array.from({ length: UPDATE_JOURNAL_LIMIT + 4 }, (_u, i) => row({ ts: `t${i}` }));
    store.getState().setUpdateJournal(journal);
    const kept = store.getState().update.journal;
    expect(kept).toHaveLength(UPDATE_JOURNAL_LIMIT);
    expect(kept[0]!.ts).toBe('t4');
  });

  it('mirrors check_failed and signature_rejected into the operator log', () => {
    store.getState().setUpdateJournal([
      row({ event: 'check_failed', detail: 'manifest_unreachable' }),
      row({ event: 'signature_rejected', detail: 'bad_signature' }),
    ]);
    expect(store.getState().operatorLog.map((e) => e.message)).toEqual([
      'Update check_failed: manifest_unreachable',
      'Update signature_rejected: bad_signature',
    ]);
    expect(store.getState().operatorLog.every((e) => e.level === 'error')).toBe(true);
  });

  it('does not mirror non-failure rows', () => {
    store.getState().setUpdateJournal([row(), row({ event: 'stage_failed' })]);
    expect(store.getState().operatorLog).toEqual([]);
  });

  it('does not duplicate a mirrored row when the shell re-sends the same tail', () => {
    const tail = [row({ event: 'check_failed', detail: 'manifest_unreachable' })];
    store.getState().setUpdateJournal(tail);
    store.getState().setUpdateJournal([...tail, row({ event: 'download_ok' })]);
    expect(store.getState().operatorLog).toHaveLength(1);
  });

  it('mirrors a second, genuinely new failure', () => {
    store.getState().setUpdateJournal([row({ event: 'check_failed', ts: 'a' })]);
    store.getState().setUpdateJournal([
      row({ event: 'check_failed', ts: 'a' }),
      row({ event: 'check_failed', ts: 'b' }),
    ]);
    expect(store.getState().operatorLog).toHaveLength(2);
  });

  it('never leaks an absolute path — it renders only what the shell sent', () => {
    store.getState().setUpdateJournal([row({ event: 'check_failed', detail: 'io_timeout' })]);
    for (const entry of store.getState().operatorLog) {
      expect(entry.message).not.toMatch(/(^|\s)\/[^\s]/);
      expect(entry.message).not.toMatch(/[A-Za-z]:\\/);
    }
  });
});

describe('operator-owned toggles', () => {
  it('records the channel selection', () => {
    store.getState().setUpdateChannel('beta');
    expect(store.getState().update.channel).toBe('beta');
  });

  it('records the freeze toggle in both directions', () => {
    store.getState().setUpdateFrozen(true);
    expect(store.getState().update.frozen).toBe(true);
    store.getState().setUpdateFrozen(false);
    expect(store.getState().update.frozen).toBe(false);
  });

  it('records the confirmed consent choice', () => {
    store.getState().confirmUpdateChoice('install_now');
    expect(store.getState().update.confirmedChoice).toBe('install_now');
  });
});

describe('session_status.app_version (I1)', () => {
  it('is carried through the session slice when the sidecar reports it', () => {
    store.getState().setSessionStatus({
      armed: false,
      midi_port: null,
      mode: 'mock',
      connection_phase: 'listening',
      unsaved_sends: 0,
      app_version: '1.35.0',
    });
    expect(store.getState().sessionStatus?.app_version).toBe('1.35.0');
  });

  it('is simply absent on a sidecar predating the version spine', () => {
    store.getState().setSessionStatus({
      armed: false,
      midi_port: null,
      mode: 'mock',
      connection_phase: 'listening',
      unsaved_sends: 0,
    });
    expect(store.getState().sessionStatus?.app_version).toBeUndefined();
  });
});
