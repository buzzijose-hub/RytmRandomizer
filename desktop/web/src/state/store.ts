/**
 * Cockpit state store (Zustand).
 *
 * The store is a thin reducer over the latest event payloads. Per spec, events carry the
 * WHOLE state per kind (not deltas), so a slice's value is simply the most recent event
 * payload of that kind.
 *
 * Slices:
 *   - snapshot         ← snapshot_changed.snapshot
 *   - previewCandidate ← mutation_previewed.candidate (null when preview is off)
 *   - history          ← history_updated.history
 *   - profile          ← profile_changed.profile (active profile, null when none)
 *   - performanceConsole ← performance_console_changed.performance_console
 *   - sessionStatus    ← session_status (full payload sans `type`)
 *
 * The store does NOT own a WebSocket; bindings to a `CockpitClient` live in the
 * `bindClientToStore` helper, kept in `src/state/index.ts` for tree-shake friendliness.
 */

import { create } from 'zustand';

import type { LiveGuiPerformanceConsoleModelDict } from '../types/live_gui_protocol';
import type { ConnectionStatus } from '../ws/client';
import type {
  CockpitSendPlan,
  ConnectionPhase,
  ConnectionStateDict,
  DiagnosticsPayload,
  History,
  LibraryRecord,
  MidiActivityBatch,
  MidiActivityRow,
  MutationCandidate,
  ProfileModel,
  SessionMode,
  Snapshot,
} from '../ws/protocol';

// ---------- Slice types ----------

export interface SessionStatus {
  armed: boolean;
  midi_port: string | null;
  mode: SessionMode;
  connection_phase: ConnectionPhase;
  unsaved_sends: number;
}

/** One monitor row with a client-side id (React key for the bounded ring). */
export interface MonitorRow extends MidiActivityRow {
  id: string;
}

/** Latest batch counters from the passive input monitor. */
export interface MidiActivityMeta {
  port: string;
  dropped: number;
  ignored: number;
  read_errors: number;
}

export interface OperatorLogEntry {
  id: string;
  level: 'info' | 'success' | 'error';
  message: string;
}

export interface CockpitState {
  snapshot: Snapshot | null;
  previewCandidate: MutationCandidate | null;
  history: History | null;
  profile: ProfileModel | null;
  performanceConsole: LiveGuiPerformanceConsoleModelDict | null;
  sendPlan: CockpitSendPlan | null;
  sessionStatus: SessionStatus | null;
  connectionStatus: ConnectionStatus;
  operatorLog: OperatorLogEntry[];
  /** Latest passive connection observation ← connection_changed.connection. */
  connection: ConnectionStateDict | null;
  /** Visual notice set when the device recovers from fault → listening. */
  reconnectNotice: string | null;
  /** Bounded client-side ring of decoded input rows ← midi_activity batches. */
  midiActivityRows: MonitorRow[];
  midiActivityMeta: MidiActivityMeta | null;
  /** Count of batches applied — the monitor's flash indicator trigger. */
  midiActivityBatchCount: number;
  /** When true, incoming midi_activity batches are dropped client-side. */
  midiActivityPaused: boolean;
  /** Library records ← library_changed / library_list / library_search. */
  libraryRecords: LibraryRecord[] | null;
  /** Latest read-only diagnostics packet ← the diagnostics command ack. */
  diagnostics: DiagnosticsPayload | null;
}

export interface CockpitActions {
  setSnapshot: (snapshot: Snapshot) => void;
  setPreviewCandidate: (candidate: MutationCandidate | null) => void;
  setHistory: (history: History) => void;
  setProfile: (profile: ProfileModel | null) => void;
  setPerformanceConsole: (model: LiveGuiPerformanceConsoleModelDict | null) => void;
  setSendPlan: (sendPlan: CockpitSendPlan | null) => void;
  setSessionStatus: (status: SessionStatus) => void;
  setConnectionStatus: (status: ConnectionStatus) => void;
  appendOperatorLog: (entry: Omit<OperatorLogEntry, 'id'>) => void;
  setConnection: (connection: ConnectionStateDict) => void;
  clearReconnectNotice: () => void;
  appendMidiActivity: (activity: MidiActivityBatch) => void;
  setMidiActivityPaused: (paused: boolean) => void;
  clearMidiActivity: () => void;
  setLibraryRecords: (records: LibraryRecord[]) => void;
  setDiagnostics: (diagnostics: DiagnosticsPayload) => void;
  /** Reset all slices back to null (used on disconnect / shutdown). */
  reset: () => void;
}

export type CockpitStore = CockpitState & CockpitActions;

// ---------- Initial state ----------

export const INITIAL_STATE: CockpitState = {
  snapshot: null,
  previewCandidate: null,
  history: null,
  profile: null,
  performanceConsole: null,
  sendPlan: null,
  sessionStatus: null,
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
};

const OPERATOR_LOG_LIMIT = 8;
let nextOperatorLogId = 0;

function makeOperatorLogId(): string {
  nextOperatorLogId += 1;
  return `operator-log-${nextOperatorLogId}`;
}

/** Client-side bound on the monitor ring (the server ring is 256/batch). */
export const MIDI_ACTIVITY_RING_LIMIT = 200;

/** Operator-facing notice shown when a fault recovers to passive listening. */
export const RECONNECT_NOTICE = 'Reconnected — passive listening restored';

let nextMonitorRowId = 0;

function makeMonitorRowId(): string {
  nextMonitorRowId += 1;
  return `midi-row-${nextMonitorRowId}`;
}

// ---------- Store ----------

/**
 * Create a fresh store instance. Most consumers use the module-level `useCockpitStore`
 * singleton; tests get isolation by creating their own instance.
 */
export function createCockpitStore() {
  return create<CockpitStore>((set) => ({
    ...INITIAL_STATE,
    setSnapshot: (snapshot) => set({ snapshot }),
    setPreviewCandidate: (candidate) => set({ previewCandidate: candidate }),
    setHistory: (history) => set({ history }),
    setProfile: (profile) => set({ profile }),
    setPerformanceConsole: (model) => set({ performanceConsole: model }),
    setSendPlan: (sendPlan) => set({ sendPlan }),
    setSessionStatus: (status) => set({ sessionStatus: status }),
    setConnectionStatus: (status) => set({ connectionStatus: status }),
    setConnection: (connection) =>
      set((state) => ({
        connection,
        reconnectNotice:
          state.connection?.phase === 'fault' && connection.phase === 'listening'
            ? RECONNECT_NOTICE
            : state.reconnectNotice,
      })),
    clearReconnectNotice: () => set({ reconnectNotice: null }),
    appendMidiActivity: (activity) =>
      set((state) => {
        if (state.midiActivityPaused) return {};
        const appended = [
          ...state.midiActivityRows,
          ...activity.batch.map((row) => ({ ...row, id: makeMonitorRowId() })),
        ];
        return {
          midiActivityRows: appended.slice(-MIDI_ACTIVITY_RING_LIMIT),
          midiActivityMeta: {
            port: activity.port,
            dropped: activity.dropped,
            ignored: activity.ignored,
            read_errors: activity.read_errors,
          },
          midiActivityBatchCount: state.midiActivityBatchCount + 1,
        };
      }),
    setMidiActivityPaused: (paused) => set({ midiActivityPaused: paused }),
    clearMidiActivity: () =>
      set({ midiActivityRows: [], midiActivityMeta: null, midiActivityBatchCount: 0 }),
    setLibraryRecords: (records) => set({ libraryRecords: records }),
    setDiagnostics: (diagnostics) => set({ diagnostics }),
    appendOperatorLog: (entry) =>
      set((state) => ({
        operatorLog: [
          ...state.operatorLog,
          {
            ...entry,
            id: makeOperatorLogId(),
          },
        ].slice(-OPERATOR_LOG_LIMIT),
      })),
    reset: () => set({ ...INITIAL_STATE }),
  }));
}

/** Module-level singleton store consumed by the React tree. */
export const useCockpitStore = createCockpitStore();

// ---------- Selectors ----------

export const selectIsConnected = (s: CockpitState): boolean => s.sessionStatus !== null;

export const selectIsArmed = (s: CockpitState): boolean => s.sessionStatus?.armed ?? false;

export const selectUnsavedSends = (s: CockpitState): number =>
  s.sessionStatus?.unsaved_sends ?? 0;

export const selectPadCount = (s: CockpitState): number => s.snapshot?.pads.length ?? 0;

export const selectSendPlanReady = (s: CockpitState): boolean => s.sendPlan?.ready ?? false;

export const selectCanSend = (s: CockpitState): boolean => selectSendPlanReady(s);

export const selectPreparedPadCount = (s: CockpitState): number => s.sendPlan?.pad_count ?? 0;

export const selectHasHistory = (s: CockpitState): boolean =>
  (s.history?.entries.length ?? 0) > 0;

/**
 * The operator-facing connection phase: the passive ConnectionManager's
 * latest observation wins; the session_status fallback covers sessions
 * booted before the first connection_changed event; 'disconnected' covers
 * the pre-session placeholder.
 */
export const selectConnectionPhase = (s: CockpitState): ConnectionPhase =>
  s.connection?.phase ?? s.sessionStatus?.connection_phase ?? 'disconnected';

export const selectCanUndo = (s: CockpitState): boolean => {
  const h = s.history;
  if (h === null) return false;
  if (h.entries.length === 0) return false;
  // Cannot undo if current is the first entry.
  return h.entries[0]?.snapshot.snapshot_id !== h.current_id;
};
