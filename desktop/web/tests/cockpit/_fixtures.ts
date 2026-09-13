/**
 * Shared test fixtures + a FakeClient that records sent commands.
 *
 * Imported by every cockpit component test.
 */

import type {
  CockpitClient,
  ConnectionStatus,
  EventHandler,
  ReconnectState,
  Unsubscribe,
} from '../../src/ws/client';
import type {
  Command,
  CommandAck,
  ConnectionStateDict,
  DiagnosticsPayload,
  DualMachineStageState,
  Event as ProtocolEvent,
  EventType,
  History,
  CockpitSendPlan,
  LibraryRecord,
  MidiActivityBatch,
  MutationCandidate,
  AnalogFourPatchGenomePayload,
  AnalogFourPatchGene,
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
    { pad_id: 3, machine: 'CH Closed', params: { tun: 50, dec: 30, lev: 90, flt: 58 } },
    // pad 4 deliberately omits some params to exercise the "?? 0" fallback.
    { pad_id: 4, machine: 'OH Open', params: {} },
    { pad_id: 5, machine: 'BT Rim', params: { tun: 42, dec: 70, lev: 95, flt: 52 } },
    { pad_id: 6, machine: 'LT Low', params: { tun: 38, dec: 68, lev: 92, flt: 50 } },
    { pad_id: 7, machine: 'MT Mid', params: { tun: 48, dec: 66, lev: 93, flt: 55 } },
    { pad_id: 8, machine: 'HT High', params: { tun: 56, dec: 58, lev: 88, flt: 62 } },
    { pad_id: 9, machine: 'CP Clap', params: { tun: 52, dec: 44, lev: 96, flt: 70 } },
    { pad_id: 10, machine: 'RS Riser', params: { tun: 60, dec: 76, lev: 86, flt: 74 } },
    { pad_id: 11, machine: 'SY Raw', params: { tun: 64, dec: 80, lev: 110, flt: 64 } },
    { pad_id: 12, machine: 'BD Acoustic', params: { tun: 34, dec: 84, lev: 105, flt: 48 } },
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

export const sendPlan: CockpitSendPlan = {
  plan_id: 'sendplan-1',
  candidate_id: 'cand-1',
  source_snapshot_id: 'snap-1',
  profile_id: 'user-buzzi',
  ready: true,
  readiness_reason: 'ready',
  safety_status: 'safe',
  estimated_midi_msgs: 2,
  pad_count: 2,
  locked_pad_ids: [2],
  target_pad_ids: [],
  blocked_reasons: [],
  packets: [
    { pad_id: 1, parameter: 'tun', channel: 0, control: 52, value: 35 },
    { pad_id: 3, parameter: 'tun', channel: 0, control: 52, value: 55 },
  ],
};

export const blockedSendPlan: CockpitSendPlan = {
  ...sendPlan,
  plan_id: 'sendplan-blocked',
  ready: false,
  readiness_reason: 'candidate_high_risk',
  safety_status: 'high_risk',
  estimated_midi_msgs: 0,
  pad_count: 0,
  packets: [],
  blocked_reasons: ['candidate_high_risk'],
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
  connection_phase: 'armed',
  unsaved_sends: 2,
  capture_enabled: true,
};

export const sessionMock: SessionStatus = {
  armed: false,
  midi_port: null,
  mode: 'mock',
  connection_phase: 'disconnected',
  unsaved_sends: 0,
  capture_enabled: false,
};

export const readyDualMachineStage: DualMachineStageState = {
  revision: 8,
  rytm: {
    device_id: 'analog_rytm_mk2',
    connection_state: 'connected',
    capture_state: 'captured',
    target_ids: [],
    locked_ids: [2],
    effective_ids: [1, 3],
    candidate_state: 'ready',
    plan_state: 'ready',
    authority_state: 'not_armed',
    blocked_reasons: [],
    recovery_actions: ['confirm_exact_plan'],
    last_error: null,
  },
  analog_four: {
    device_id: 'analog_four_mk2',
    connection_state: 'unknown',
    capture_state: 'not_captured',
    target_ids: [],
    locked_ids: [],
    effective_ids: [],
    candidate_state: 'none',
    plan_state: 'blocked',
    authority_state: 'blocked',
    blocked_reasons: ['a4_hardware_audition_validation_pending'],
    recovery_actions: ['capture_current_kit', 'run_a4_mapping_gap_procedure'],
    last_error: null,
  },
  oxi_owns_sequencing: true,
  direct_oxi_control: false,
};

// ---------- Wave-4 fixtures (connection / monitor / doctor / library) ----------

export const connectionListening: ConnectionStateDict = {
  phase: 'listening',
  available_inputs: ['Analog Rytm MK2 IN'],
  available_outputs: ['Analog Rytm MK2 OUT'],
  selected_input: 'Analog Rytm MK2 IN',
  selected_output: 'Analog Rytm MK2 OUT',
  last_error_fingerprint: null,
  changed_at: 1000.0,
};

export const connectionFault: ConnectionStateDict = {
  phase: 'fault',
  available_inputs: [],
  available_outputs: [],
  selected_input: null,
  selected_output: null,
  last_error_fingerprint: 'cockpit.connection.enumeration_failed.oserror',
  changed_at: 999.0,
};

export const midiBatch: MidiActivityBatch = {
  port: 'Analog Rytm MK2 IN',
  batch: [
    {
      channel: 0,
      pad: 1,
      control: 16,
      value: 90,
      repeat_count: 3,
      observed_at: 12.5,
      labels: ['BD Tune'],
    },
    {
      channel: 1,
      pad: 2,
      control: 24,
      value: 64,
      repeat_count: 1,
      observed_at: 12.6,
      labels: [],
    },
  ],
  dropped: 0,
  ignored: 2,
  read_errors: 0,
};

export const libraryRecordA: LibraryRecord = {
  record_id: 'abc123',
  device_id: 'analog_rytm_mk2',
  kit_name: 'INDUSTRIAL KIT',
  fingerprint: 'abc123',
  captured_at: '2026-07-01T10:00:00+00:00',
  tags: ['techno'],
  payload_hex: 'f0f7',
};

export const libraryRecordB: LibraryRecord = {
  record_id: 'def456',
  device_id: 'analog_four_mk2',
  kit_name: 'ACID BANK',
  fingerprint: 'def456',
  captured_at: '2026-07-02T11:00:00+00:00',
  tags: [],
  payload_hex: 'f0f7',
};

export const diagnosticsHealthy: DiagnosticsPayload = {
  journal: [],
  errors_by_kind: {},
  connection: connectionListening,
  available_inputs: ['Analog Rytm MK2 IN'],
  available_outputs: ['Analog Rytm MK2 OUT'],
  platform: 'darwin',
  driver_hint: 'macOS CoreMIDI: check Audio MIDI Setup > MIDI Studio.',
};

export const diagnosticsFaulty: DiagnosticsPayload = {
  journal: [
    {
      fingerprint: 'cockpit.connection.enumeration_failed.oserror',
      message: 'MIDI port enumeration failed',
      context: { exception_type: 'OSError' },
      ts: 1721900000.0,
    },
  ],
  errors_by_kind: { midi_port: 2 },
  connection: connectionFault,
  available_inputs: [],
  available_outputs: [],
  platform: 'linux',
  driver_hint: 'Linux ALSA: run `amidi -l` to confirm the kernel sees the device.',
};

export const availableProfiles = [
  {
    profile_id: 'scene-industrial',
    name: 'Industrial',
    kind: 'scene' as const,
    model_version: '1.0.0',
    source_summary: 'Built-in scene · metallic and harsh',
  },
  {
    profile_id: 'scene-warehouse',
    name: 'Warehouse',
    kind: 'scene' as const,
    model_version: '1.0.0',
    source_summary: 'Built-in scene · rolling warehouse pressure',
  },
  {
    profile_id: 'user-buzzi',
    name: 'buzzi',
    kind: 'user' as const,
    model_version: '1.2.0',
    source_summary: '5 sources · 1,243 analyzed signals',
  },
];

const patchGenes: AnalogFourPatchGene[] = [
  {
    track: 2,
    family: 'Oscillators',
    rationale: 'Keep the first oscillator tight and centered.',
    confidence: 'high',
    value: {
      parameter: 'OSC1 TUN',
      section: 'OSC1',
      encoder: 'A',
      screen_value: '+7.00',
      midi_value: 71,
      cc_msb: 16,
      cc_lsb: null,
      nrpn_address: null,
      transport_status: 'cc-ready',
      dial_direction: 'clockwise',
    },
  },
  {
    track: 2,
    family: 'Envelope and LFO',
    rationale: 'Short motion reinforces the pressure pulse.',
    confidence: 'medium',
    value: {
      parameter: 'LFO1 SPD',
      section: 'LFO1',
      encoder: 'B',
      screen_value: '64',
      midi_value: 64,
      cc_msb: null,
      cc_lsb: null,
      nrpn_address: [1, 32],
      transport_status: 'nrpn-ready',
      dial_direction: 'clockwise',
    },
  },
  {
    track: 2,
    family: 'Filter and effects',
    rationale: 'Open the filter without losing the low-end anchor.',
    confidence: 'high',
    value: {
      parameter: 'FILT1 FRQ',
      section: 'FILTER',
      encoder: 'A',
      screen_value: '88',
      midi_value: null,
      cc_msb: null,
      cc_lsb: null,
      nrpn_address: [2, 10],
      transport_status: 'screen-only-nrpn',
      dial_direction: 'clockwise',
    },
  },
];

function patchCandidate(column: number, label: string, role: string, closeness: number) {
  return { column, label, role, closeness, genes: patchGenes };
}

export const patchGenome: AnalogFourPatchGenomePayload = {
  source: { type: 'description', value: 'Tight warehouse pressure' },
  selected_candidate: 2,
  selected_track: 2,
  selected: patchCandidate(2, 'Brighter sync', 'Sharper sync-led variation', 86),
  genome: {
    version: 'analog-four-patch-genome-v1',
    device_id: 'analog_four',
    mode: 'passive',
    selected_track: 2,
    source_hash: '0123456789abcdef',
    source_confidence: 'high',
    candidate_count: 4,
    traits: [
      { key: 'energy', label: 'Energy', intensity: 78, evidence: ['pressure'] },
      { key: 'brightness', label: 'Brightness', intensity: 61, evidence: ['tight'] },
    ],
    candidates: [
      patchCandidate(1, 'Closest match', 'Reference-nearest patch', 92),
      patchCandidate(2, 'Brighter sync', 'Sharper sync-led variation', 86),
      patchCandidate(3, 'Darker drive', 'Driven low-mid variation', 80),
      patchCandidate(4, 'Wider motion', 'Motion-rich spatial variation', 76),
    ],
    safety: ['passive read-only patch genome'],
  },
  safety: ['passive read-only patch genome'],
};

// ---------- FakeClient ----------

export class FakeCockpitClient {
  sent: Command[] = [];
  ackQueue: CommandAck[] = [];
  /** Explicit promises consumed before the synchronous ack helpers. */
  responseQueue: Promise<CommandAck>[] = [];
  /** Make the next `send` call reject with this value (consumed once). */
  nextRejection: unknown | null = null;
  /** When true, send() returns a never-resolving promise (used to test no-ack paths). */
  hang = false;

  /** retryNow() invocations (asserted by ReconnectBanner tests). */
  retryCalls = 0;
  /** URL reported by getUrl(). */
  url = 'ws://127.0.0.1:4317/ws';
  /** Reconnect snapshot returned by getReconnectState(). */
  reconnectState: ReconnectState = { attempt: 0, nextDelayMs: null };

  private readonly listeners = new Map<EventType, Set<EventHandler>>();
  private readonly statusListeners = new Set<(s: ConnectionStatus) => void>();
  private readonly reconnectListeners = new Set<(state: ReconnectState) => void>();
  private status: ConnectionStatus = 'connected';

  send(command: Command): Promise<CommandAck> {
    this.sent.push(command);
    const queuedResponse = this.responseQueue.shift();
    if (queuedResponse !== undefined) return queuedResponse;
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

  /** Test helper: change the reported connection status and notify subscribers. */
  setStatus(status: ConnectionStatus): void {
    this.status = status;
    for (const handler of this.statusListeners) handler(status);
  }

  getStatus(): ConnectionStatus {
    return this.status;
  }

  getUrl(): string {
    return this.url;
  }

  getReconnectState(): ReconnectState {
    return this.reconnectState;
  }

  onReconnectStateChange(handler: (state: ReconnectState) => void): Unsubscribe {
    this.reconnectListeners.add(handler);
    return () => {
      this.reconnectListeners.delete(handler);
    };
  }

  /** Test helper: update the reconnect snapshot and notify subscribers. */
  emitReconnectState(state: ReconnectState): void {
    this.reconnectState = state;
    for (const handler of this.reconnectListeners) handler(state);
  }

  retryNow(): void {
    this.retryCalls += 1;
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
