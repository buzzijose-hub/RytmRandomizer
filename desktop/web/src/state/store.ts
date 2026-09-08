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
import {
  UPDATE_JOURNAL_LIMIT,
  isMirroredFailure,
  mirroredFailureMessage,
  type UpdateChannel,
  type UpdateConsentChoice,
  type UpdateJournalRow,
  type UpdateSlice,
  type UpdateStateEvent,
} from '../updateProtocol';
import type { ConnectionStatus } from '../ws/client';
import type {
  AnalogFourPatchGenomePayload,
  CockpitSendPlan,
  ConnectionPhase,
  ConnectionStateDict,
  DiagnosticsPayload,
  DualMachineStageState,
  History,
  KitCaptureResult,
  LibraryRecord,
  MidiActivityBatch,
  MidiActivityRow,
  MutationCandidate,
  ProfileModel,
  ProfileCatalogItem,
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
  /** Additive capability flag; absent on older sidecar/session fixtures. */
  capture_enabled?: boolean;
  /**
   * Auto-update contract I1: the sidecar's running version, strict SemVer.
   *
   * Optional for the same reason `capture_enabled` is: a sidecar predating
   * the version spine simply omits it, and the update panel says "unknown"
   * rather than inventing a number.
   */
  app_version?: string;
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
  profileCatalog: ProfileCatalogItem[];
  patchGenome: AnalogFourPatchGenomePayload | null;
  /** True when the visible A4 genome predates the current target/lock authority. */
  patchGenomeStale: boolean;
  kitCaptures: KitCaptureResult[];
  rytmPadTargets: number[];
  a4TrackTargets: number[];
  rytmPadLocks: number[];
  a4TrackLocks: number[];
  /** Latest whole-state coordinator snapshot; never merged field-by-field. */
  dualMachineStage: DualMachineStageState | null;
  performanceConsole: LiveGuiPerformanceConsoleModelDict | null;
  sendPlan: CockpitSendPlan | null;
  sessionStatus: SessionStatus | null;
  /**
   * Auto-update contract I1 — the sidecar's SemVer, read-only.
   *
   * Populated exclusively by `setSessionStatus` from the `session_status`
   * handshake frame; there is deliberately **no** `setAppVersion` action,
   * so no UI surface can write it. `null` until the handshake completes
   * (or permanently, against a pre-I1 sidecar that omits the field).
   * Nothing renders it yet — the update chip and panel are a later PR.
   */
  appVersion: string | null;
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
  /**
   * Auto-update surface ← the shell's `rytm-update-state` event (I2) and
   * journal tail (I8). Purely a mirror of what the shell pushed plus the
   * operator's own channel/freeze/consent choices — the cockpit never
   * derives update state on its own and never initiates a check on mount.
   */
  update: UpdateSlice;
}

export interface CockpitActions {
  setSnapshot: (snapshot: Snapshot) => void;
  setPreviewCandidate: (candidate: MutationCandidate | null) => void;
  setHistory: (history: History) => void;
  setProfile: (profile: ProfileModel | null) => void;
  setProfileCatalog: (profiles: ProfileCatalogItem[]) => void;
  setPatchGenome: (patchGenome: AnalogFourPatchGenomePayload) => void;
  setKitCaptures: (captures: KitCaptureResult[]) => void;
  setMutationTargets: (rytmPadTargets: number[], a4TrackTargets: number[]) => void;
  setMutationLocks: (rytmPadLocks: number[], a4TrackLocks: number[]) => void;
  setRytmPadLocks: (padIds: number[]) => void;
  setA4TrackLocks: (trackIds: number[]) => void;
  setDualMachineStage: (stage: DualMachineStageState) => void;
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
  /**
   * Apply one I2 payload from the shell. A payload naming a version other
   * than the one the operator consented to voids that consent (§5: consent
   * is per-version and never carries across).
   */
  setUpdateState: (state: UpdateStateEvent) => void;
  /**
   * Replace the journal tail (I8, oldest first). Failure rows the operator
   * must not miss are mirrored into the operator log (§5.1 honesty floor).
   */
  setUpdateJournal: (journal: ReadonlyArray<UpdateJournalRow>) => void;
  setUpdateChannel: (channel: UpdateChannel) => void;
  setUpdateFrozen: (frozen: boolean) => void;
  /** Record the operator's confirmed consent choice for the staged version. */
  confirmUpdateChoice: (choice: UpdateConsentChoice) => void;
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
};

const OPERATOR_LOG_LIMIT = 8;
let nextOperatorLogId = 0;

function makeOperatorLogId(): string {
  nextOperatorLogId += 1;
  return `operator-log-${nextOperatorLogId}`;
}

/**
 * Identity of a journal row for de-duplication when the shell re-sends an
 * overlapping tail. The shell assigns no row ids, so the tuple the row
 * already carries is the key.
 */
function journalRowKey(row: UpdateJournalRow): string {
  return `${row.ts}|${row.event}|${row.version}|${row.detail}`;
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

function sameNumberSet(left: readonly number[], right: readonly number[]): boolean {
  if (left.length !== right.length) return false;
  const rightSet = new Set(right);
  return left.every((value) => rightSet.has(value));
}

function appendUnique(values: readonly string[], value: string): string[] {
  return values.includes(value) ? [...values] : [...values, value];
}

function revokeMachineForDisconnect(
  machine: DualMachineStageState['rytm'],
): DualMachineStageState['rytm'] {
  return {
    ...machine,
    connection_state: 'disconnected',
    candidate_state: machine.candidate_state === 'ready' ? 'stale' : machine.candidate_state,
    plan_state: machine.plan_state === 'ready' ? 'stale' : machine.plan_state,
    authority_state: 'blocked',
    blocked_reasons: appendUnique(machine.blocked_reasons, 'device_disconnected'),
    recovery_actions: ['reconnect_device', 'capture_current_kit', 'prepare_again'],
    last_error: 'device disconnected',
  };
}

function revokeStageForTransportDisconnect(
  stage: DualMachineStageState | null,
): DualMachineStageState | null {
  if (stage === null) return null;
  return {
    ...stage,
    rytm: revokeMachineForDisconnect(stage.rytm),
    analog_four: revokeMachineForDisconnect(stage.analog_four),
  };
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
    setProfileCatalog: (profileCatalog) => set({ profileCatalog }),
    setPatchGenome: (patchGenome) => set({ patchGenome, patchGenomeStale: false }),
    setKitCaptures: (kitCaptures) => set({ kitCaptures }),
    setMutationTargets: (rytmPadTargets, a4TrackTargets) =>
      set((state) => {
        const rytmChanged = !sameNumberSet(state.rytmPadTargets, rytmPadTargets);
        const a4Changed = !sameNumberSet(state.a4TrackTargets, a4TrackTargets);
        if (!rytmChanged && !a4Changed) return {};
        return {
          rytmPadTargets,
          a4TrackTargets,
          previewCandidate: null,
          sendPlan: null,
          patchGenomeStale:
            a4Changed && state.patchGenome !== null ? true : state.patchGenomeStale,
        };
      }),
    setMutationLocks: (rytmPadLocks, a4TrackLocks) =>
      set((state) => {
        const rytmChanged = !sameNumberSet(state.rytmPadLocks, rytmPadLocks);
        const a4Changed = !sameNumberSet(state.a4TrackLocks, a4TrackLocks);
        if (!rytmChanged && !a4Changed) return {};
        return {
          rytmPadLocks,
          a4TrackLocks,
          previewCandidate: null,
          sendPlan: null,
          patchGenomeStale:
            a4Changed && state.patchGenome !== null ? true : state.patchGenomeStale,
        };
      }),
    setRytmPadLocks: (rytmPadLocks) =>
      set((state) => {
        if (sameNumberSet(state.rytmPadLocks, rytmPadLocks)) return {};
        return { rytmPadLocks, previewCandidate: null, sendPlan: null };
      }),
    setA4TrackLocks: (a4TrackLocks) =>
      set((state) => {
        if (sameNumberSet(state.a4TrackLocks, a4TrackLocks)) return {};
        return {
          a4TrackLocks,
          previewCandidate: null,
          sendPlan: null,
          patchGenomeStale: state.patchGenome !== null ? true : state.patchGenomeStale,
        };
      }),
    setDualMachineStage: (dualMachineStage) =>
      set((state) => {
        const rytmScopeChanged =
          !sameNumberSet(state.rytmPadTargets, dualMachineStage.rytm.target_ids) ||
          !sameNumberSet(state.rytmPadLocks, dualMachineStage.rytm.locked_ids);
        const a4ScopeChanged =
          !sameNumberSet(state.a4TrackTargets, dualMachineStage.analog_four.target_ids) ||
          !sameNumberSet(state.a4TrackLocks, dualMachineStage.analog_four.locked_ids);
        const rytmCandidateReady = dualMachineStage.rytm.candidate_state === 'ready';
        const rytmPlanReady = dualMachineStage.rytm.plan_state === 'ready';
        const a4CandidateReady = dualMachineStage.analog_four.candidate_state === 'ready';
        return {
          dualMachineStage,
          rytmPadTargets: dualMachineStage.rytm.target_ids,
          a4TrackTargets: dualMachineStage.analog_four.target_ids,
          rytmPadLocks: dualMachineStage.rytm.locked_ids,
          a4TrackLocks: dualMachineStage.analog_four.locked_ids,
          previewCandidate:
            rytmScopeChanged || !rytmCandidateReady ? null : state.previewCandidate,
          sendPlan: rytmScopeChanged || !rytmPlanReady ? null : state.sendPlan,
          patchGenomeStale:
            state.patchGenome === null
              ? false
              : a4ScopeChanged || dualMachineStage.analog_four.candidate_state === 'stale'
                ? true
                : a4CandidateReady
                  ? false
                  : state.patchGenomeStale,
        };
      }),
    setPerformanceConsole: (model) => set({ performanceConsole: model }),
    setSendPlan: (sendPlan) => set({ sendPlan }),
    // Contract I1: `appVersion` is derived here and nowhere else — the
    // store exposes no `setAppVersion`, so the handshake frame is the
    // slice's only writer. A later `session_status` refresh that omits
    // `app_version` (pre-I1 sidecar, or a frame built by an older
    // handler) leaves the last known value in place rather than
    // flickering it to null; the version of a running sidecar cannot
    // change without a reconnect, and `reset()` clears it on disconnect.
    setSessionStatus: (status) =>
      set((state) => ({
        sessionStatus: status,
        appVersion: status.app_version ?? state.appVersion,
      })),
    setConnectionStatus: (status) =>
      set((state) =>
        status === 'connected'
          ? { connectionStatus: status }
          : {
              connectionStatus: status,
              previewCandidate: null,
              sendPlan: null,
              patchGenomeStale: state.patchGenome !== null || state.patchGenomeStale,
              dualMachineStage: revokeStageForTransportDisconnect(state.dualMachineStage),
            },
      ),
    setConnection: (connection) =>
      set((state) => {
        const disconnected = connection.phase === 'disconnected' || connection.phase === 'fault';
        const stage = state.dualMachineStage;
        return {
          connection,
          reconnectNotice:
            state.connection?.phase === 'fault' && connection.phase === 'listening'
              ? RECONNECT_NOTICE
              : state.reconnectNotice,
          previewCandidate: disconnected ? null : state.previewCandidate,
          sendPlan: disconnected ? null : state.sendPlan,
          dualMachineStage:
            disconnected && stage !== null
              ? { ...stage, rytm: revokeMachineForDisconnect(stage.rytm) }
              : stage,
        };
      }),
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
    setUpdateState: (updateState) =>
      set((state) => {
        // Consent is per-version (§5). A payload naming a different version
        // than the one the operator confirmed voids that confirmation, so a
        // superseding release always re-asks rather than inheriting a yes.
        const previous = state.update.state;
        const versionChanged = previous !== null && previous.version !== updateState.version;
        return {
          update: {
            ...state.update,
            state: updateState,
            confirmedChoice: versionChanged ? null : state.update.confirmedChoice,
          },
        };
      }),
    setUpdateJournal: (journal) =>
      set((state) => {
        const bounded = journal.slice(-UPDATE_JOURNAL_LIMIT);
        // §5.1 failure-honesty floor: check_failed / signature_rejected also
        // surface in the operator log so a failing updater is never silent.
        // Only rows new to this batch are mirrored — re-sending the same tail
        // must not duplicate log entries.
        const known = new Set(state.update.journal.map(journalRowKey));
        const mirrored = bounded
          .filter((row) => isMirroredFailure(row) && !known.has(journalRowKey(row)))
          .map((row) => ({
            id: makeOperatorLogId(),
            level: 'error' as const,
            message: mirroredFailureMessage(row),
          }));
        return {
          update: { ...state.update, journal: bounded },
          operatorLog:
            mirrored.length > 0
              ? [...state.operatorLog, ...mirrored].slice(-OPERATOR_LOG_LIMIT)
              : state.operatorLog,
        };
      }),
    setUpdateChannel: (channel) =>
      set((state) => ({ update: { ...state.update, channel } })),
    setUpdateFrozen: (frozen) => set((state) => ({ update: { ...state.update, frozen } })),
    confirmUpdateChoice: (choice) =>
      set((state) => ({ update: { ...state.update, confirmedChoice: choice } })),
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

/** Fail closed unless the prepared plan is exact for the current authoritative scope. */
export const selectCanSend = (s: CockpitState): boolean => {
  const plan = s.sendPlan;
  const candidate = s.previewCandidate;
  const stage = s.dualMachineStage?.rytm;
  if (s.connectionStatus !== 'connected' || plan === null || candidate === null) return false;
  if (!plan.ready || plan.plan_id.trim() === '') return false;
  if (plan.candidate_id !== candidate.candidate_id) return false;
  if (plan.source_snapshot_id !== candidate.source_snapshot_id) return false;
  if (plan.profile_id !== candidate.profile_id) return false;
  if (!sameNumberSet(plan.target_pad_ids, s.rytmPadTargets)) return false;
  if (!sameNumberSet(plan.locked_pad_ids, s.rytmPadLocks)) return false;
  if (stage === undefined) return false;
  return (
    stage.candidate_state === 'ready' &&
    stage.plan_state === 'ready' &&
    stage.connection_state !== 'disconnected' &&
    stage.authority_state !== 'blocked'
  );
};

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
