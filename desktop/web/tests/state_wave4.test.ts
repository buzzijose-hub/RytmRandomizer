/**
 * Wave-4 store slices + client→store bindings: passive connection state,
 * the reconnect notice, the bounded MIDI-activity ring, library records,
 * and diagnostics.
 */

import { describe, expect, it } from 'vitest';

import {
  bindClientToStore,
  createCockpitStore,
  MIDI_ACTIVITY_RING_LIMIT,
  RECONNECT_NOTICE,
  selectConnectionPhase,
  INITIAL_STATE,
} from '../src/state';
import type { CockpitClient, EventHandler, Unsubscribe } from '../src/ws/client';
import type {
  ConnectionChangedEvent,
  Event,
  EventType,
  LibraryChangedEvent,
  MidiActivityEvent,
} from '../src/ws/protocol';

import {
  connectionFault,
  connectionListening,
  diagnosticsHealthy,
  libraryRecordA,
  libraryRecordB,
  midiBatch,
} from './cockpit/_fixtures';

// Minimal handler-recording fake (mirrors the FakeClient in store.test.ts).
class FakeClient {
  handlers = new Map<EventType, Set<EventHandler>>();
  on<T extends EventType>(
    eventType: T,
    handler: EventHandler<Extract<Event, { type: T }>>,
  ): Unsubscribe {
    let bucket = this.handlers.get(eventType);
    if (bucket === undefined) {
      bucket = new Set();
      this.handlers.set(eventType, bucket);
    }
    bucket.add(handler as EventHandler);
    return () => undefined;
  }
  onStatusChange(): Unsubscribe {
    return () => undefined;
  }
}

function fire(client: FakeClient, type: EventType, event: Event): void {
  const bucket = client.handlers.get(type);
  expect(bucket).toBeDefined();
  for (const handler of bucket as Set<EventHandler>) handler(event);
}

describe('wave-4 store slices', () => {
  it('setConnection stores the observation and flags fault → listening recoveries', () => {
    const store = createCockpitStore();
    store.getState().setConnection(connectionListening);
    expect(store.getState().connection).toBe(connectionListening);
    // listening → listening keeps the (null) notice.
    expect(store.getState().reconnectNotice).toBeNull();

    store.getState().setConnection(connectionFault);
    expect(store.getState().reconnectNotice).toBeNull();

    store.getState().setConnection(connectionListening);
    expect(store.getState().reconnectNotice).toBe(RECONNECT_NOTICE);

    // A later fault does not clear an undismissed notice.
    store.getState().setConnection(connectionFault);
    expect(store.getState().reconnectNotice).toBe(RECONNECT_NOTICE);

    store.getState().clearReconnectNotice();
    expect(store.getState().reconnectNotice).toBeNull();
  });

  it('appendMidiActivity appends rows with ids, tracks meta, and honors pause', () => {
    const store = createCockpitStore();
    store.getState().appendMidiActivity(midiBatch);
    const state = store.getState();
    expect(state.midiActivityRows).toHaveLength(2);
    expect(state.midiActivityRows[0]).toMatchObject({ control: 16, value: 90 });
    expect(state.midiActivityRows[0]!.id).not.toBe(state.midiActivityRows[1]!.id);
    expect(state.midiActivityMeta).toEqual({
      port: 'Analog Rytm MK2 IN',
      dropped: 0,
      ignored: 2,
      read_errors: 0,
    });
    expect(state.midiActivityBatchCount).toBe(1);

    store.getState().setMidiActivityPaused(true);
    store.getState().appendMidiActivity(midiBatch);
    expect(store.getState().midiActivityRows).toHaveLength(2);
    expect(store.getState().midiActivityBatchCount).toBe(1);

    store.getState().setMidiActivityPaused(false);
    store.getState().appendMidiActivity(midiBatch);
    expect(store.getState().midiActivityRows).toHaveLength(4);
    expect(store.getState().midiActivityBatchCount).toBe(2);

    store.getState().clearMidiActivity();
    expect(store.getState().midiActivityRows).toEqual([]);
    expect(store.getState().midiActivityMeta).toBeNull();
    expect(store.getState().midiActivityBatchCount).toBe(0);
  });

  it('the monitor ring is bounded client-side (drop-oldest)', () => {
    const store = createCockpitStore();
    const bigBatch = {
      ...midiBatch,
      batch: Array.from({ length: MIDI_ACTIVITY_RING_LIMIT + 5 }, (_, i) => ({
        channel: 0,
        pad: 1,
        control: i,
        value: i,
        repeat_count: 1,
        observed_at: i,
        labels: [],
      })),
    };
    store.getState().appendMidiActivity(bigBatch);
    const rows = store.getState().midiActivityRows;
    expect(rows).toHaveLength(MIDI_ACTIVITY_RING_LIMIT);
    // Oldest 5 rows were dropped.
    expect(rows[0]).toMatchObject({ control: 5 });
  });

  it('setLibraryRecords and setDiagnostics write their slices; reset clears them', () => {
    const store = createCockpitStore();
    store.getState().setLibraryRecords([libraryRecordA, libraryRecordB]);
    store.getState().setDiagnostics(diagnosticsHealthy);
    store.getState().setConnection(connectionListening);
    expect(store.getState().libraryRecords).toHaveLength(2);
    expect(store.getState().diagnostics).toBe(diagnosticsHealthy);

    store.getState().reset();
    expect(store.getState().libraryRecords).toBeNull();
    expect(store.getState().diagnostics).toBeNull();
    expect(store.getState().connection).toBeNull();
  });

  it('selectConnectionPhase prefers connection, then session_status, then disconnected', () => {
    expect(selectConnectionPhase(INITIAL_STATE)).toBe('disconnected');
    expect(
      selectConnectionPhase({
        ...INITIAL_STATE,
        sessionStatus: {
          armed: false,
          midi_port: null,
          mode: 'mock',
          connection_phase: 'searching',
          unsaved_sends: 0,
        },
      }),
    ).toBe('searching');
    expect(
      selectConnectionPhase({ ...INITIAL_STATE, connection: connectionListening }),
    ).toBe('listening');
  });
});

describe('wave-4 client→store bindings', () => {
  it('routes connection_changed, midi_activity, and library_changed into the store', () => {
    const client = new FakeClient();
    const store = createCockpitStore();
    const unbind = bindClientToStore(client as unknown as CockpitClient, store);

    const connectionEvent: ConnectionChangedEvent = {
      type: 'connection_changed',
      connection: connectionListening,
    };
    fire(client, 'connection_changed', connectionEvent);
    expect(store.getState().connection).toBe(connectionListening);

    const activityEvent: MidiActivityEvent = {
      type: 'midi_activity',
      midi_activity: midiBatch,
    };
    fire(client, 'midi_activity', activityEvent);
    expect(store.getState().midiActivityRows).toHaveLength(2);

    const libraryEvent: LibraryChangedEvent = {
      type: 'library_changed',
      library: { records: [libraryRecordA] },
    };
    fire(client, 'library_changed', libraryEvent);
    expect(store.getState().libraryRecords).toEqual([libraryRecordA]);

    // session_status carries the phase + the armed announcement branch.
    fire(client, 'session_status', {
      type: 'session_status',
      armed: true,
      midi_port: 'Analog Rytm MK2 OUT',
      mode: 'live',
      connection_phase: 'armed',
      unsaved_sends: 1,
    });
    expect(store.getState().sessionStatus).toEqual({
      armed: true,
      midi_port: 'Analog Rytm MK2 OUT',
      mode: 'live',
      connection_phase: 'armed',
      unsaved_sends: 1,
    });

    unbind();
  });
});
