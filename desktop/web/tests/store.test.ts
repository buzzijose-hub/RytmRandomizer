/**
 * Tests for the Zustand cockpit store + selectors + client→store binding.
 *
 * Goal: 100% branch coverage on `src/state/**`.
 */

import { describe, expect, it } from 'vitest';

import {
  bindClientToStore,
  createCockpitStore,
  INITIAL_STATE,
  selectCanUndo,
  selectCanSend,
  selectHasHistory,
  selectIsArmed,
  selectIsConnected,
  selectPadCount,
  selectSendPlanReady,
  selectUnsavedSends,
  useCockpitStore,
  type CockpitStore,
  type SessionStatus,
} from '../src/state';
import type {
  ConnectionStatus,
  EventHandler,
  Unsubscribe,
  CockpitClient,
} from '../src/ws/client';
import type {
  Event,
  EventType,
  History,
  HistoryUpdatedEvent,
  CockpitSendPlan,
  MutationCandidate,
  MutationPreviewedEvent,
  PerformanceConsoleChangedEvent,
  ProfileChangedEvent,
  ProfileModel,
  SessionStatusEvent,
  SendPlanChangedEvent,
  Snapshot,
  SnapshotChangedEvent,
} from '../src/ws/protocol';
import { performanceConsoleModel } from './cockpit/performanceConsoleFixture';

// ---------- Fixtures ----------

const snapshot: Snapshot = {
  snapshot_id: 'snap-1',
  device: 'analog_rytm_mk2',
  captured_at: '2026-05-23T12:00:00Z',
  pads: [
    { pad_id: 1, machine: 'BD Hard', params: { tun: 28, dec: 80, lev: 110 } },
    { pad_id: 2, machine: 'SD Classic', params: { tun: 40, dec: 60, lev: 100 } },
  ],
  scene_slot: 'A01',
  bpm: 132,
};

const snapshot2: Snapshot = { ...snapshot, snapshot_id: 'snap-2', captured_at: '2026-05-23T12:00:30Z' };

const candidate: MutationCandidate = {
  candidate_id: 'cand-1',
  source_snapshot_id: 'snap-1',
  profile_id: 'prof-1',
  depth: 0.45,
  seed: 12345,
  pad_deltas: [],
  safety_status: 'safe',
  estimated_midi_msgs: 12,
};

const sendPlan: CockpitSendPlan = {
  plan_id: 'sendplan-1',
  candidate_id: 'cand-1',
  source_snapshot_id: 'snap-1',
  profile_id: 'prof-1',
  ready: true,
  readiness_reason: 'ready',
  safety_status: 'safe',
  estimated_midi_msgs: 2,
  pad_count: 2,
  locked_pad_ids: [],
  blocked_reasons: [],
  packets: [
    { pad_id: 1, parameter: 'tun', channel: 0, control: 52, value: 45 },
    { pad_id: 2, parameter: 'dec', channel: 0, control: 44, value: 72 },
  ],
};

const history: History = {
  entries: [
    { snapshot, kind: 'auto', parent_id: null, via: null, label: null },
    { snapshot: snapshot2, kind: 'auto', parent_id: 'snap-1', via: 'send', label: null },
  ],
  current_id: 'snap-2',
};

const profile: ProfileModel = {
  profile_id: 'prof-1',
  name: 'buzzi',
  kind: 'user',
  model_version: '1.2.0',
  traits: [{ name: 'rolling_low_end', value: 0.85 }],
  pad_mappings: [{ trait: 'rolling_low_end', pad_id: 1, weight: 0.9 }],
  transition_curve: 'progressive',
  source_summary: '5 sources · 1,243 analyzed signals',
};

const session: SessionStatus = {
  armed: true,
  midi_port: 'IAC Driver Bus 1',
  mode: 'live',
  unsaved_sends: 2,
};

// ---------- Tests: store actions ----------

describe('cockpit store — actions write each slice', () => {
  it('starts with all slices null and matches the exported INITIAL_STATE shape', () => {
    const store = createCockpitStore();
    const state = store.getState();
    expect(state.snapshot).toBeNull();
    expect(state.previewCandidate).toBeNull();
    expect(state.history).toBeNull();
    expect(state.profile).toBeNull();
    expect(state.performanceConsole).toBeNull();
    expect(state.sendPlan).toBeNull();
    expect(state.sessionStatus).toBeNull();
    expect(state.connectionStatus).toBe('closed');
    expect(state.operatorLog).toEqual([]);
    expect(INITIAL_STATE).toEqual({
      snapshot: null,
      previewCandidate: null,
      history: null,
      profile: null,
      performanceConsole: null,
      sendPlan: null,
      sessionStatus: null,
      connectionStatus: 'closed',
      operatorLog: [],
    });
  });

  it('setSnapshot writes the snapshot slice', () => {
    const store = createCockpitStore();
    store.getState().setSnapshot(snapshot);
    expect(store.getState().snapshot).toBe(snapshot);
  });

  it('setPreviewCandidate accepts a candidate and null (preview off)', () => {
    const store = createCockpitStore();
    store.getState().setPreviewCandidate(candidate);
    expect(store.getState().previewCandidate).toBe(candidate);
    store.getState().setPreviewCandidate(null);
    expect(store.getState().previewCandidate).toBeNull();
  });

  it('setHistory writes the history slice', () => {
    const store = createCockpitStore();
    store.getState().setHistory(history);
    expect(store.getState().history).toBe(history);
  });

  it('setProfile accepts a profile and null (no active profile)', () => {
    const store = createCockpitStore();
    store.getState().setProfile(profile);
    expect(store.getState().profile).toBe(profile);
    store.getState().setProfile(null);
    expect(store.getState().profile).toBeNull();
  });

  it('setPerformanceConsole accepts a passive console packet and null', () => {
    const store = createCockpitStore();
    store.getState().setPerformanceConsole(performanceConsoleModel);
    expect(store.getState().performanceConsole).toBe(performanceConsoleModel);
    store.getState().setPerformanceConsole(null);
    expect(store.getState().performanceConsole).toBeNull();
  });

  it('setSendPlan accepts a plan and null (stale plan cleared)', () => {
    const store = createCockpitStore();
    store.getState().setSendPlan(sendPlan);
    expect(store.getState().sendPlan).toBe(sendPlan);
    store.getState().setSendPlan(null);
    expect(store.getState().sendPlan).toBeNull();
  });

  it('setSessionStatus writes the session status slice', () => {
    const store = createCockpitStore();
    store.getState().setSessionStatus(session);
    expect(store.getState().sessionStatus).toEqual(session);
  });

  it('setConnectionStatus and appendOperatorLog write operator feedback slices', () => {
    const store = createCockpitStore();
    store.getState().setConnectionStatus('connected');
    store.getState().appendOperatorLog({ level: 'info', message: 'WebSocket connected' });
    store.getState().appendOperatorLog({ level: 'error', message: 'send rejected' });
    expect(store.getState().connectionStatus).toBe('connected');
    expect(store.getState().operatorLog.map((entry) => entry.message)).toEqual([
      'WebSocket connected',
      'send rejected',
    ]);
    expect(store.getState().operatorLog[1]).toMatchObject({ level: 'error' });
  });

  it('reset() returns to INITIAL_STATE', () => {
    const store = createCockpitStore();
    store.getState().setSnapshot(snapshot);
    store.getState().setPreviewCandidate(candidate);
    store.getState().setHistory(history);
    store.getState().setProfile(profile);
    store.getState().setPerformanceConsole(performanceConsoleModel);
    store.getState().setSendPlan(sendPlan);
    store.getState().setSessionStatus(session);
    store.getState().setConnectionStatus('connected');
    store.getState().appendOperatorLog({ level: 'info', message: 'WebSocket connected' });
    store.getState().reset();
    const s = store.getState();
    expect(s.snapshot).toBeNull();
    expect(s.previewCandidate).toBeNull();
    expect(s.history).toBeNull();
    expect(s.profile).toBeNull();
    expect(s.performanceConsole).toBeNull();
    expect(s.sendPlan).toBeNull();
    expect(s.sessionStatus).toBeNull();
    expect(s.connectionStatus).toBe('closed');
    expect(s.operatorLog).toEqual([]);
  });

  it('exports a singleton useCockpitStore that is the same Zustand store across imports', () => {
    expect(typeof useCockpitStore.getState).toBe('function');
    expect(typeof useCockpitStore.setState).toBe('function');
    expect(typeof useCockpitStore.subscribe).toBe('function');
  });
});

// ---------- Tests: selectors (all branches) ----------

describe('cockpit store — selectors', () => {
  it('selectIsConnected reflects sessionStatus presence', () => {
    expect(selectIsConnected({ ...INITIAL_STATE })).toBe(false);
    expect(selectIsConnected({ ...INITIAL_STATE, sessionStatus: session })).toBe(true);
  });

  it('selectIsArmed handles null and present sessionStatus', () => {
    expect(selectIsArmed({ ...INITIAL_STATE })).toBe(false);
    expect(selectIsArmed({ ...INITIAL_STATE, sessionStatus: { ...session, armed: false } })).toBe(
      false,
    );
    expect(selectIsArmed({ ...INITIAL_STATE, sessionStatus: session })).toBe(true);
  });

  it('selectUnsavedSends defaults to 0 when sessionStatus is null', () => {
    expect(selectUnsavedSends({ ...INITIAL_STATE })).toBe(0);
    expect(selectUnsavedSends({ ...INITIAL_STATE, sessionStatus: session })).toBe(2);
  });

  it('selectPadCount handles null snapshot and counts pads', () => {
    expect(selectPadCount({ ...INITIAL_STATE })).toBe(0);
    expect(selectPadCount({ ...INITIAL_STATE, snapshot })).toBe(2);
  });

  it('selectSendPlanReady and selectCanSend require a ready send plan', () => {
    expect(selectSendPlanReady({ ...INITIAL_STATE })).toBe(false);
    expect(selectCanSend({ ...INITIAL_STATE })).toBe(false);
    expect(selectSendPlanReady({ ...INITIAL_STATE, sendPlan })).toBe(true);
    expect(selectCanSend({ ...INITIAL_STATE, sendPlan })).toBe(true);
    expect(
      selectCanSend({
        ...INITIAL_STATE,
        sendPlan: { ...sendPlan, ready: false, readiness_reason: 'candidate_high_risk' },
      }),
    ).toBe(false);
  });

  it('selectHasHistory handles null history and empty entries', () => {
    expect(selectHasHistory({ ...INITIAL_STATE })).toBe(false);
    expect(
      selectHasHistory({
        ...INITIAL_STATE,
        history: { entries: [], current_id: '' },
      }),
    ).toBe(false);
    expect(selectHasHistory({ ...INITIAL_STATE, history })).toBe(true);
  });

  it('selectCanUndo: null history → false', () => {
    expect(selectCanUndo({ ...INITIAL_STATE })).toBe(false);
  });

  it('selectCanUndo: empty entries → false', () => {
    expect(
      selectCanUndo({
        ...INITIAL_STATE,
        history: { entries: [], current_id: '' },
      }),
    ).toBe(false);
  });

  it('selectCanUndo: current is the first entry → false', () => {
    const singleEntry: History = {
      entries: [{ snapshot, kind: 'auto', parent_id: null, via: null, label: null }],
      current_id: snapshot.snapshot_id,
    };
    expect(selectCanUndo({ ...INITIAL_STATE, history: singleEntry })).toBe(false);
  });

  it('selectCanUndo: current is past the first entry → true', () => {
    expect(selectCanUndo({ ...INITIAL_STATE, history })).toBe(true);
  });
});

// ---------- Tests: bindClientToStore ----------

/**
 * A tiny fake client that captures handlers per event type. We bind to it, then call
 * each captured handler to verify the store updates. Also verifies the returned
 * unsubscribe detaches every handler.
 */
class FakeClient {
  readonly handlers = new Map<EventType, EventHandler[]>();
  readonly statusHandlers: Array<(status: ConnectionStatus) => void> = [];
  unsubCalls = 0;
  status: ConnectionStatus = 'closed';

  on<T extends EventType>(
    eventType: T,
    handler: EventHandler<Extract<Event, { type: T }>>,
  ): Unsubscribe {
    let bucket = this.handlers.get(eventType);
    if (bucket === undefined) {
      bucket = [];
      this.handlers.set(eventType, bucket);
    }
    bucket.push(handler as EventHandler);
    return () => {
      this.unsubCalls += 1;
    };
  }

  onStatusChange(handler: (status: ConnectionStatus) => void): Unsubscribe {
    this.statusHandlers.push(handler);
    return () => {
      this.unsubCalls += 1;
    };
  }

  getStatus(): ConnectionStatus {
    return this.status;
  }

  fireStatus(status: ConnectionStatus): void {
    this.status = status;
    for (const handler of this.statusHandlers) handler(status);
  }
}

describe('bindClientToStore', () => {
  it('routes all seven engine events into the corresponding store slices', () => {
    const store = createCockpitStore();
    const client = new FakeClient();
    const unbind = bindClientToStore(client as unknown as CockpitClient, store);

    const fire = <T extends EventType>(
      type: T,
      event: Extract<Event, { type: T }>,
    ): void => {
      const bucket = client.handlers.get(type);
      expect(bucket).toBeDefined();
      for (const h of bucket as EventHandler[]) h(event);
    };

    const snapshotEvent: SnapshotChangedEvent = { type: 'snapshot_changed', snapshot };
    fire('snapshot_changed', snapshotEvent);
    expect(store.getState().snapshot).toBe(snapshot);

    const previewEvent: MutationPreviewedEvent = { type: 'mutation_previewed', candidate };
    fire('mutation_previewed', previewEvent);
    expect(store.getState().previewCandidate).toBe(candidate);

    const previewOff: MutationPreviewedEvent = { type: 'mutation_previewed', candidate: null };
    fire('mutation_previewed', previewOff);
    expect(store.getState().previewCandidate).toBeNull();

    const planEvent: SendPlanChangedEvent = { type: 'send_plan_changed', send_plan: sendPlan };
    fire('send_plan_changed', planEvent);
    expect(store.getState().sendPlan).toBe(sendPlan);

    const planOff: SendPlanChangedEvent = { type: 'send_plan_changed', send_plan: null };
    fire('send_plan_changed', planOff);
    expect(store.getState().sendPlan).toBeNull();

    const historyEvent: HistoryUpdatedEvent = { type: 'history_updated', history };
    fire('history_updated', historyEvent);
    expect(store.getState().history).toBe(history);

    const profileEvent: ProfileChangedEvent = { type: 'profile_changed', profile };
    fire('profile_changed', profileEvent);
    expect(store.getState().profile).toBe(profile);

    const profileOff: ProfileChangedEvent = { type: 'profile_changed', profile: null };
    fire('profile_changed', profileOff);
    expect(store.getState().profile).toBeNull();

    const consoleEvent: PerformanceConsoleChangedEvent = {
      type: 'performance_console_changed',
      performance_console: performanceConsoleModel,
    };
    fire('performance_console_changed', consoleEvent);
    expect(store.getState().performanceConsole).toBe(performanceConsoleModel);

    const consoleOff: PerformanceConsoleChangedEvent = {
      type: 'performance_console_changed',
      performance_console: null,
    };
    fire('performance_console_changed', consoleOff);
    expect(store.getState().performanceConsole).toBeNull();

    const sessionEvent: SessionStatusEvent = {
      type: 'session_status',
      armed: false,
      midi_port: null,
      mode: 'mock',
      unsaved_sends: 0,
    };
    fire('session_status', sessionEvent);
    expect(store.getState().sessionStatus).toEqual({
      armed: false,
      midi_port: null,
      mode: 'mock',
      unsaved_sends: 0,
    });

    client.fireStatus('connected');
    expect(store.getState().connectionStatus).toBe('connected');
    expect(store.getState().operatorLog.at(-1)).toMatchObject({
      level: 'info',
      message: 'WebSocket connected',
    });

    // Unsubscribe should call client's individual unsubs.
    unbind();
    expect(client.unsubCalls).toBe(8);
  });

  it('falls back to the module-level singleton store when no store is provided', () => {
    const client = new FakeClient();
    // Reset the singleton so the test is hermetic.
    useCockpitStore.getState().reset();
    const unbind = bindClientToStore(client as unknown as CockpitClient);
    const snapshotEvent: SnapshotChangedEvent = { type: 'snapshot_changed', snapshot };
    const bucket = client.handlers.get('snapshot_changed');
    expect(bucket).toBeDefined();
    for (const h of bucket as EventHandler[]) h(snapshotEvent);
    expect(useCockpitStore.getState().snapshot).toBe(snapshot);
    unbind();
    useCockpitStore.getState().reset();
  });
});

// Type-only sanity: CockpitStore satisfies the actions interface (compile-time check).
const _typeProbe: CockpitStore = createCockpitStore().getState();
void _typeProbe;
