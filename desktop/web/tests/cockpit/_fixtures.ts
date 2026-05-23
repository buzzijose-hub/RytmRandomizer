/**
 * Shared test fixtures + a FakeClient that records sent commands.
 *
 * Imported by every cockpit component test.
 */

import type {
  CockpitClient,
  ConnectionStatus,
  EventHandler,
  Unsubscribe,
} from '../../src/ws/client';
import type {
  Command,
  CommandAck,
  Event as ProtocolEvent,
  EventType,
  History,
  MutationCandidate,
  ProfileModel,
  Snapshot,
} from '../../src/ws/protocol';
import type { SessionStatus } from '../../src/state';

// ---------- Domain fixtures ----------

export const snapshot: Snapshot = {
  snapshot_id: 'snap-1',
  device: 'analog_rytm_mk2',
  captured_at: '2026-05-23T12:00:00Z',
  pads: [
    { pad_id: 1, machine: 'BD Hard', params: { tun: 28, dec: 80, lev: 110, flt: 60 } },
    { pad_id: 2, machine: 'SD Classic', params: { tun: 40, dec: 60, lev: 100, flt: 64 } },
    { pad_id: 3, machine: 'HH Closed', params: { tun: 50, dec: 30, lev: 90 } },
    // pad 4 deliberately omits some params to exercise the "?? 0" fallback.
    { pad_id: 4, machine: 'CY Crash', params: {} },
  ],
  scene_slot: 'A01',
  bpm: 132,
};

export const candidate: MutationCandidate = {
  candidate_id: 'cand-1',
  source_snapshot_id: 'snap-1',
  profile_id: 'user-buzzi',
  depth: 0.45,
  seed: 12345,
  pad_deltas: [
    {
      pad_id: 1,
      proposed_params: { tun: 35, dec: 90, lev: 115, flt: 50 },
      changed_keys: ['tun', 'dec', 'lev', 'flt'],
    },
    {
      pad_id: 3,
      proposed_params: { tun: 55 },
      changed_keys: ['tun'],
    },
  ],
  safety_status: 'safe',
  estimated_midi_msgs: 12,
};

export const highRiskCandidate: MutationCandidate = {
  ...candidate,
  candidate_id: 'cand-risk',
  safety_status: 'high_risk',
};

export const profile: ProfileModel = {
  profile_id: 'user-buzzi',
  name: 'buzzi',
  kind: 'user',
  model_version: '1.2.0',
  traits: [
    { name: 'rolling_low_end', value: 0.85 },
    { name: 'metallic_tension', value: 0.4 },
  ],
  pad_mappings: [{ trait: 'rolling_low_end', pad_id: 1, weight: 0.9 }],
  transition_curve: 'progressive',
  source_summary: '5 sources · 1,243 analyzed signals',
};

export const sceneProfile: ProfileModel = {
  ...profile,
  profile_id: 'scene-industrial',
  name: 'Industrial',
  kind: 'scene',
};

export const history: History = {
  entries: [
    { snapshot, kind: 'auto', parent_id: null, via: null, label: null },
    {
      snapshot: { ...snapshot, snapshot_id: 'snap-2' },
      kind: 'auto',
      parent_id: 'snap-1',
      via: 'send',
      label: null,
    },
    {
      snapshot: { ...snapshot, snapshot_id: 'snap-3' },
      kind: 'saved',
      parent_id: 'snap-2',
      via: 'send',
      label: 'industrial-peak',
    },
  ],
  current_id: 'snap-3',
};

export const sessionLive: SessionStatus = {
  armed: true,
  midi_port: 'IAC Driver Bus 1',
  mode: 'live',
  unsaved_sends: 2,
};

export const sessionMock: SessionStatus = {
  armed: false,
  midi_port: null,
  mode: 'mock',
  unsaved_sends: 0,
};

export const availableProfiles = [
  { profile_id: 'scene-industrial', name: 'Industrial', kind: 'scene' as const },
  { profile_id: 'scene-warehouse', name: 'Warehouse', kind: 'scene' as const },
  { profile_id: 'user-buzzi', name: 'buzzi', kind: 'user' as const },
];

// ---------- FakeClient ----------

export interface SendRecord {
  command: Command;
  ack: { resolve: (ack: CommandAck) => void; reject: (err: Error) => void };
}

export class FakeCockpitClient {
  sent: Command[] = [];
  ackQueue: CommandAck[] = [];
  /** Make the next `send` call reject with this error (consumed once). */
  nextRejection: Error | null = null;
  /** When true, send() returns a never-resolving promise (used to test no-ack paths). */
  hang = false;

  private readonly listeners = new Map<EventType, Set<EventHandler>>();
  private readonly statusListeners = new Set<(s: ConnectionStatus) => void>();
  private status: ConnectionStatus = 'connected';

  send(command: Command): Promise<CommandAck> {
    this.sent.push(command);
    if (this.nextRejection !== null) {
      const err = this.nextRejection;
      this.nextRejection = null;
      return Promise.reject(err);
    }
    if (this.hang) {
      return new Promise(() => {
        /* never resolves */
      });
    }
    const ack: CommandAck =
      this.ackQueue.shift() ?? { request_id: `req-${this.sent.length}`, ok: true };
    return Promise.resolve(ack);
  }

  on<T extends EventType>(
    eventType: T,
    handler: EventHandler<Extract<ProtocolEvent, { type: T }>>,
  ): Unsubscribe {
    let bucket = this.listeners.get(eventType);
    if (bucket === undefined) {
      bucket = new Set();
      this.listeners.set(eventType, bucket);
    }
    bucket.add(handler as EventHandler);
    return () => {
      const b = this.listeners.get(eventType);
      if (b !== undefined) b.delete(handler as EventHandler);
    };
  }

  onStatusChange(handler: (s: ConnectionStatus) => void): Unsubscribe {
    this.statusListeners.add(handler);
    return () => {
      this.statusListeners.delete(handler);
    };
  }

  getStatus(): ConnectionStatus {
    return this.status;
  }

  connect(): void {
    /* no-op for tests */
  }

  close(): void {
    /* no-op for tests */
  }

  /** Cast to the real type when handing to components. */
  asClient(): CockpitClient {
    return this as unknown as CockpitClient;
  }
}

/**
 * Convenience: enqueue an ack with ok=false for the next send().
 */
export function enqueueRejection(client: FakeCockpitClient): void {
  client.ackQueue.push({ request_id: 'rejected', ok: false, error: 'rejected by engine' });
}
