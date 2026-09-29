/**
 * The read-only `appVersion` store slice — auto-update contract I1.
 *
 * The sidecar reports its own SemVer on the `session_status` handshake
 * frame; the store surfaces it as a slice PR-B's chip and update panel
 * will read. This file pins the three properties that make it safe to
 * build on:
 *
 * 1. it populates from the handshake frame and nothing else;
 * 2. it is not writable — the store exposes no `setAppVersion`, so no UI
 *    surface can forge a version;
 * 3. nothing about it transmits, and nothing observes it before the
 *    handshake completes (the #238 lesson).
 *
 * Goal: 100% branch coverage on the slice's reducer paths.
 */

import { describe, expect, it } from 'vitest';

import { bindClientToStore, createCockpitStore, INITIAL_STATE } from '../src/state';
import type { CockpitClient, ConnectionStatus, EventHandler, Unsubscribe } from '../src/ws/client';
import type { Event, EventType, SessionStatusEvent } from '../src/ws/protocol';

/** Minimal `CockpitClient` stand-in: records handlers, fires events on demand. */
class FakeClient {
  readonly handlers = new Map<EventType, EventHandler[]>();
  readonly statusHandlers: Array<(status: ConnectionStatus) => void> = [];
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
    return () => {};
  }

  onStatusChange(handler: (status: ConnectionStatus) => void): Unsubscribe {
    this.statusHandlers.push(handler);
    return () => {};
  }

  getStatus(): ConnectionStatus {
    return this.status;
  }

  fireStatus(status: ConnectionStatus): void {
    this.status = status;
    for (const handler of this.statusHandlers) handler(status);
  }

  fire<T extends EventType>(type: T, event: Extract<Event, { type: T }>): void {
    for (const handler of this.handlers.get(type) ?? []) {
      (handler as EventHandler<Extract<Event, { type: T }>>)(event);
    }
  }
}

function handshake(overrides: Partial<SessionStatusEvent> = {}): SessionStatusEvent {
  return {
    type: 'session_status',
    armed: false,
    midi_port: null,
    mode: 'mock',
    connection_phase: 'disconnected',
    unsaved_sends: 0,
    capture_enabled: false,
    app_version: '1.34.0',
    ...overrides,
  };
}

describe('appVersion slice (contract I1)', () => {
  it('is null before the handshake completes', () => {
    const store = createCockpitStore();

    expect(INITIAL_STATE.appVersion).toBeNull();
    expect(store.getState().appVersion).toBeNull();
  });

  it('populates from the session_status handshake frame', () => {
    const store = createCockpitStore();
    const client = new FakeClient();
    bindClientToStore(client as unknown as CockpitClient, store);

    client.fire('session_status', handshake({ app_version: '1.35.0-beta.1' }));

    expect(store.getState().appVersion).toBe('1.35.0-beta.1');
    expect(store.getState().sessionStatus?.app_version).toBe('1.35.0-beta.1');
  });

  it('stays null against a pre-I1 sidecar that omits app_version', () => {
    const store = createCockpitStore();
    const client = new FakeClient();
    bindClientToStore(client as unknown as CockpitClient, store);

    client.fire('session_status', handshake({ app_version: undefined }));

    expect(store.getState().appVersion).toBeNull();
    expect(store.getState().sessionStatus).not.toBeNull();
  });

  it('keeps the known version when a later frame omits it', () => {
    const store = createCockpitStore();
    const client = new FakeClient();
    bindClientToStore(client as unknown as CockpitClient, store);

    client.fire('session_status', handshake({ app_version: '1.34.0' }));
    // A refresh built by an older handler path: everything else updates,
    // but the version must not flicker to null — a running sidecar's
    // version cannot change without a reconnect.
    client.fire('session_status', handshake({ app_version: undefined, unsaved_sends: 3 }));

    expect(store.getState().appVersion).toBe('1.34.0');
    expect(store.getState().sessionStatus?.unsaved_sends).toBe(3);
  });

  it('takes the newest value when a later frame carries a different version', () => {
    const store = createCockpitStore();
    const client = new FakeClient();
    bindClientToStore(client as unknown as CockpitClient, store);

    client.fire('session_status', handshake({ app_version: '1.34.0' }));
    client.fire('session_status', handshake({ app_version: '1.35.0' }));

    expect(store.getState().appVersion).toBe('1.35.0');
  });

  it('clears on reset — a disconnect forgets the peer it was talking to', () => {
    const store = createCockpitStore();
    const client = new FakeClient();
    bindClientToStore(client as unknown as CockpitClient, store);

    client.fire('session_status', handshake({ app_version: '1.34.0' }));
    store.getState().reset();

    expect(store.getState().appVersion).toBeNull();
  });

  it('exposes no writer: there is no setAppVersion action', () => {
    const store = createCockpitStore();

    // The slice is read-only by construction — the handshake reducer is
    // its only writer. A future UI surface must not be able to forge a
    // version, so the absence of a setter is a contract, not an omission.
    expect('setAppVersion' in store.getState()).toBe(false);
    expect(
      Object.keys(store.getState()).filter((key) => key.toLowerCase().includes('appversion')),
    ).toEqual(['appVersion']);
  });

  it('setSessionStatus is the only path that moves the slice', () => {
    const store = createCockpitStore();

    store.getState().setSessionStatus({
      armed: false,
      midi_port: null,
      mode: 'mock',
      connection_phase: 'disconnected',
      unsaved_sends: 0,
      app_version: '2.0.0',
    });

    expect(store.getState().appVersion).toBe('2.0.0');
  });

  it('does not arm, transmit, or change mode when a version arrives', () => {
    const store = createCockpitStore();
    const client = new FakeClient();
    bindClientToStore(client as unknown as CockpitClient, store);

    client.fire('session_status', handshake({ app_version: '1.34.0' }));

    // The #238 guard restated at the slice level: reading a version is
    // inert. The passive defaults of a mock session are untouched.
    expect(store.getState().sessionStatus?.armed).toBe(false);
    expect(store.getState().sessionStatus?.mode).toBe('mock');
    expect(store.getState().sendPlan).toBeNull();
    expect(store.getState().connectionStatus).toBe('closed');
  });
});
