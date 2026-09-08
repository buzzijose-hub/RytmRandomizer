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
  DualMachineStageChangedEvent,
  DualMachineStageState,
  History,
  HistoryUpdatedEvent,
  KitCapturesChangedEvent,
  CockpitSendPlan,
  MutationCandidate,
  MutationPreviewedEvent,
  MutationLocksChangedEvent,
  MutationTargetsChangedEvent,
  PatchGenomeChangedEvent,
  PerformanceConsoleChangedEvent,
  ProfileChangedEvent,
  ProfileCatalogChangedEvent,
  ProfileModel,
  SessionStatusEvent,
  SendPlanChangedEvent,
  Snapshot,
  SnapshotChangedEvent,
} from '../src/ws/protocol';
import { performanceConsoleModel } from './cockpit/performanceConsoleFixture';
import { availableProfiles, connectionFault, patchGenome } from './cockpit/_fixtures';

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
  target_pad_ids: [],
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
  connection_phase: 'armed',
  unsaved_sends: 2,
  capture_enabled: true,
};

const readyStage: DualMachineStageState = {
  revision: 4,
  rytm: {
    device_id: 'analog_rytm_mk2',
    connection_state: 'connected',
    capture_state: 'captured',
    target_ids: [],
    locked_ids: [],
    effective_ids: [1, 2],
    candidate_state: 'ready',
    plan_state: 'ready',
    authority_state: 'armed',
    blocked_reasons: [],
    recovery_actions: ['confirm_exact_plan'],
    last_error: null,
  },
  analog_four: {
    device_id: 'analog_four_mk2',
    connection_state: 'connected',
    capture_state: 'captured',
    target_ids: [],
    locked_ids: [],
    effective_ids: [1, 2, 3, 4],
    candidate_state: 'ready',
    plan_state: 'blocked',
    authority_state: 'blocked',
    blocked_reasons: ['a4_semantic_mapping_unpromoted'],
    recovery_actions: ['run_a4_mapping_gap_procedure'],
    last_error: null,
  },
  oxi_owns_sequencing: true,
  direct_oxi_control: false,
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
    expect(state.profileCatalog).toEqual([]);
    expect(state.patchGenome).toBeNull();
    expect(state.patchGenomeStale).toBe(false);
    expect(state.kitCaptures).toEqual([]);
    expect(state.performanceConsole).toBeNull();
    expect(state.sendPlan).toBeNull();
    expect(state.sessionStatus).toBeNull();
    expect(state.connectionStatus).toBe('closed');
    expect(state.dualMachineStage).toBeNull();
    expect(state.operatorLog).toEqual([]);
    expect(INITIAL_STATE).toEqual({
      snapshot: null,
      previewCandidate: null,
      history: null,
      profile: null,
      profileCatalog: [],
      patchGenome: null,
      patchGenomeStale: false,
      kitCaptures: [],
      rytmPadTargets: [],
      a4TrackTargets: [],
      rytmPadLocks: [],
      a4TrackLocks: [],
      dualMachineStage: null,
      performanceConsole: null,
      sendPlan: null,
      sessionStatus: null,
      // Contract I1 — read-only, populated only by the handshake frame.
      // Full slice behaviour lives in tests/appVersion.test.ts.
      appVersion: null,
      connectionStatus: 'closed',
      operatorLog: [],
      connection: null,
      reconnectNotice: null,
      midiActivityRows: [],
      midiActivityMeta: null,
      midiActivityBatchCount: 0,
      midiActivityPaused: false,
      libraryRecords: null,
      diagnostics: null,
      update: {
        state: null,
        journal: [],
        channel: 'stable',
        frozen: false,
        confirmedChoice: null,
      },
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

  it('setProfileCatalog and setPatchGenome write live catalogue slices', () => {
    const store = createCockpitStore();
    store.getState().setProfileCatalog([...availableProfiles]);
    store.getState().setPatchGenome(patchGenome);
    expect(store.getState().profileCatalog).toEqual(availableProfiles);
    expect(store.getState().patchGenome).toBe(patchGenome);
    expect(store.getState().patchGenomeStale).toBe(false);
  });

  it('optimistic target and lock changes revoke prepared artifacts immediately', () => {
    const store = createCockpitStore();
    store.getState().setPreviewCandidate(candidate);
    store.getState().setSendPlan(sendPlan);
    store.getState().setPatchGenome(patchGenome);

    store.getState().setMutationTargets([], [2]);

    expect(store.getState().previewCandidate).toBeNull();
    expect(store.getState().sendPlan).toBeNull();
    expect(store.getState().patchGenomeStale).toBe(true);

    store.getState().setPatchGenome(patchGenome);
    expect(store.getState().patchGenomeStale).toBe(false);
    store.getState().setA4TrackLocks([3]);
    expect(store.getState().patchGenomeStale).toBe(true);
  });

  it('treats identical targets as a no-op and does not invent stale genome state', () => {
    const store = createCockpitStore();
    store.getState().setPreviewCandidate(candidate);
    store.getState().setSendPlan(sendPlan);

    store.getState().setMutationTargets([], []);
    store.getState().setRytmPadLocks([]);
    store.getState().setA4TrackLocks([]);
    expect(store.getState().previewCandidate).toBe(candidate);
    expect(store.getState().sendPlan).toBe(sendPlan);

    store.getState().setMutationTargets([], [2]);
    expect(store.getState().patchGenomeStale).toBe(false);
  });

  it('marks a genome stale when authoritative whole-lock hydration changes A4 scope', () => {
    const store = createCockpitStore();
    store.getState().setPatchGenome(patchGenome);

    store.getState().setMutationLocks([], [4]);

    expect(store.getState().patchGenomeStale).toBe(true);
  });

  it('tracks stale, blocked, and freshly ready A4 candidates without conflating them', () => {
    const store = createCockpitStore();
    store.getState().setPatchGenome(patchGenome);
    store.getState().setDualMachineStage(readyStage);
    expect(store.getState().patchGenomeStale).toBe(false);

    store.getState().setDualMachineStage({
      ...readyStage,
      analog_four: { ...readyStage.analog_four, candidate_state: 'stale' },
    });
    expect(store.getState().patchGenomeStale).toBe(true);

    store.getState().setDualMachineStage({
      ...readyStage,
      analog_four: { ...readyStage.analog_four, candidate_state: 'blocked' },
    });
    expect(store.getState().patchGenomeStale).toBe(true);

    store.getState().setDualMachineStage(readyStage);
    expect(store.getState().patchGenomeStale).toBe(false);
  });

  it('hydrates whole-stage authority without letting an A4 failure revoke a ready Rytm lane', () => {
    const store = createCockpitStore();
    store.getState().setPreviewCandidate(candidate);
    store.getState().setSendPlan(sendPlan);
    store.getState().setPatchGenome(patchGenome);
    const a4Failed: DualMachineStageState = {
      ...readyStage,
      revision: 5,
      analog_four: {
        ...readyStage.analog_four,
        connection_state: 'disconnected',
        candidate_state: 'stale',
        plan_state: 'stale',
        locked_ids: [3],
        blocked_reasons: ['device_disconnected'],
        recovery_actions: ['reconnect_device', 'capture_current_kit'],
        last_error: 'device disconnected',
      },
    };

    store.getState().setDualMachineStage(a4Failed);

    expect(store.getState().dualMachineStage).toBe(a4Failed);
    expect(store.getState().previewCandidate).toBe(candidate);
    expect(store.getState().sendPlan).toBe(sendPlan);
    expect(store.getState().a4TrackLocks).toEqual([3]);
    expect(store.getState().patchGenomeStale).toBe(true);
  });

  it('authoritative lock hydration revokes artifacts only when the complete lock set changes', () => {
    const store = createCockpitStore();
    store.getState().setPreviewCandidate(candidate);
    store.getState().setSendPlan(sendPlan);

    store.getState().setMutationLocks([], []);
    expect(store.getState().previewCandidate).toBe(candidate);
    expect(store.getState().sendPlan).toBe(sendPlan);

    store.getState().setMutationLocks([2], [4]);
    expect(store.getState().rytmPadLocks).toEqual([2]);
    expect(store.getState().a4TrackLocks).toEqual([4]);
    expect(store.getState().previewCandidate).toBeNull();
    expect(store.getState().sendPlan).toBeNull();
  });

  it('setKitCaptures replaces the complete dual-device anchor set', () => {
    const store = createCockpitStore();
    const captures: KitCapturesChangedEvent['captures'] = [];
    store.getState().setKitCaptures(captures);
    expect(store.getState().kitCaptures).toBe(captures);
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

  it('disconnect revokes candidate and plan, and reconnect does not resurrect them', () => {
    const store = createCockpitStore();
    store.getState().setDualMachineStage(readyStage);
    store.getState().setPreviewCandidate(candidate);
    store.getState().setSendPlan(sendPlan);
    store.getState().setConnectionStatus('connected');

    store.getState().setConnectionStatus('reconnecting');

    expect(store.getState().previewCandidate).toBeNull();
    expect(store.getState().sendPlan).toBeNull();
    expect(store.getState().dualMachineStage?.rytm).toMatchObject({
      connection_state: 'disconnected',
      candidate_state: 'stale',
      plan_state: 'stale',
      authority_state: 'blocked',
    });

    // Repeated loss is idempotent: it exercises the already-stale and
    // already-recorded blocked-reason paths without duplicating authority.
    store.getState().setConnectionStatus('closed');
    expect(store.getState().dualMachineStage?.rytm.blocked_reasons).toEqual([
      'device_disconnected',
    ]);

    store.getState().setConnectionStatus('connected');
    expect(store.getState().previewCandidate).toBeNull();
    expect(store.getState().sendPlan).toBeNull();

    store.getState().setConnection(connectionFault);
    expect(store.getState().dualMachineStage?.rytm.connection_state).toBe('disconnected');
  });

  it('reconnect whole-state hydration replaces retained optimistic locks authoritatively', () => {
    const store = createCockpitStore();
    store.getState().setConnectionStatus('connected');
    store.getState().setMutationLocks([1], [2]);
    store.getState().setConnectionStatus('reconnecting');
    store.getState().setConnectionStatus('connected');

    // Locks remain fail-closed through transport loss, then the first complete
    // server event replaces both device dimensions atomically.
    expect(store.getState().rytmPadLocks).toEqual([1]);
    expect(store.getState().a4TrackLocks).toEqual([2]);
    store.getState().setMutationLocks([3], [4]);
    expect(store.getState().rytmPadLocks).toEqual([3]);
    expect(store.getState().a4TrackLocks).toEqual([4]);
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

  it('selectCanSend requires a connected exact plan for the current candidate, scope, and stage', () => {
    expect(selectSendPlanReady({ ...INITIAL_STATE })).toBe(false);
    expect(selectCanSend({ ...INITIAL_STATE })).toBe(false);
    expect(selectSendPlanReady({ ...INITIAL_STATE, sendPlan })).toBe(true);
    const sendableState = {
      ...INITIAL_STATE,
      connectionStatus: 'connected' as const,
      previewCandidate: candidate,
      sendPlan,
      dualMachineStage: readyStage,
    };
    expect(selectCanSend(sendableState)).toBe(true);
    expect(
      selectCanSend({ ...INITIAL_STATE, connectionStatus: 'connected' }),
    ).toBe(false);
    expect(
      selectCanSend({ ...INITIAL_STATE, connectionStatus: 'connected', sendPlan }),
    ).toBe(false);
    expect(selectCanSend({ ...sendableState, connectionStatus: 'reconnecting' })).toBe(false);
    expect(
      selectCanSend({
        ...sendableState,
        sendPlan: { ...sendPlan, plan_id: '' },
      }),
    ).toBe(false);
    expect(
      selectCanSend({
        ...sendableState,
        sendPlan: { ...sendPlan, candidate_id: 'stale-candidate' },
      }),
    ).toBe(false);
    expect(
      selectCanSend({
        ...sendableState,
        sendPlan: { ...sendPlan, source_snapshot_id: 'stale-snapshot' },
      }),
    ).toBe(false);
    expect(
      selectCanSend({
        ...sendableState,
        sendPlan: { ...sendPlan, profile_id: 'stale-profile' },
      }),
    ).toBe(false);
    expect(
      selectCanSend({
        ...sendableState,
        rytmPadTargets: [1],
      }),
    ).toBe(false);
    expect(
      selectCanSend({
        ...sendableState,
        rytmPadLocks: [2],
      }),
    ).toBe(false);
    expect(selectCanSend({ ...sendableState, dualMachineStage: null })).toBe(false);
    expect(
      selectCanSend({
        ...sendableState,
        dualMachineStage: {
          ...readyStage,
          rytm: { ...readyStage.rytm, candidate_state: 'none' },
        },
      }),
    ).toBe(false);
    expect(
      selectCanSend({
        ...sendableState,
        dualMachineStage: {
          ...readyStage,
          rytm: { ...readyStage.rytm, plan_state: 'stale' },
        },
      }),
    ).toBe(false);
    expect(
      selectCanSend({
        ...sendableState,
        dualMachineStage: {
          ...readyStage,
          rytm: { ...readyStage.rytm, connection_state: 'disconnected' },
        },
      }),
    ).toBe(false);
    expect(
      selectCanSend({
        ...sendableState,
        dualMachineStage: {
          ...readyStage,
          rytm: { ...readyStage.rytm, authority_state: 'blocked' },
        },
      }),
    ).toBe(false);
    expect(
      selectCanSend({
        ...sendableState,
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
  it('routes all nine engine events into the corresponding store slices', () => {
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

    const catalogEvent: ProfileCatalogChangedEvent = {
      type: 'profile_catalog_changed',
      profiles: [...availableProfiles],
    };
    fire('profile_catalog_changed', catalogEvent);
    expect(store.getState().profileCatalog).toEqual(availableProfiles);

    const capturesEvent: KitCapturesChangedEvent = {
      type: 'kit_captures_changed',
      captures: [],
    };
    fire('kit_captures_changed', capturesEvent);
    expect(store.getState().kitCaptures).toEqual([]);

    const targetsEvent: MutationTargetsChangedEvent = {
      type: 'mutation_targets_changed',
      rytm_pad_targets: [1, 4],
      a4_track_targets: [2],
    };
    fire('mutation_targets_changed', targetsEvent);
    expect(store.getState().rytmPadTargets).toEqual([1, 4]);
    expect(store.getState().a4TrackTargets).toEqual([2]);

    const locksEvent: MutationLocksChangedEvent = {
      type: 'mutation_locks_changed',
      rytm_pad_locks: [2],
      a4_track_locks: [3],
    };
    fire('mutation_locks_changed', locksEvent);
    expect(store.getState().rytmPadLocks).toEqual([2]);
    expect(store.getState().a4TrackLocks).toEqual([3]);

    const stageEvent: DualMachineStageChangedEvent = {
      type: 'dual_machine_stage_changed',
      stage: readyStage,
    };
    fire('dual_machine_stage_changed', stageEvent);
    expect(store.getState().dualMachineStage).toBe(readyStage);
    expect(store.getState().rytmPadTargets).toEqual([]);
    expect(store.getState().rytmPadLocks).toEqual([]);

    const genomeEvent: PatchGenomeChangedEvent = {
      type: 'patch_genome_changed',
      patch_genome: patchGenome,
    };
    fire('patch_genome_changed', genomeEvent);
    expect(store.getState().patchGenome).toBe(patchGenome);

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
      connection_phase: 'disconnected',
      unsaved_sends: 0,
      capture_enabled: false,
    };
    fire('session_status', sessionEvent);
    expect(store.getState().sessionStatus).toEqual({
      armed: false,
      midi_port: null,
      mode: 'mock',
      connection_phase: 'disconnected',
      unsaved_sends: 0,
      capture_enabled: false,
    });

    client.fireStatus('connected');
    expect(store.getState().connectionStatus).toBe('connected');
    expect(store.getState().operatorLog.at(-1)).toMatchObject({
      level: 'info',
      message: 'WebSocket connected',
    });

    // Unsubscribe should call client's individual unsubs.
    unbind();
    expect(client.unsubCalls).toBe(17);
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
