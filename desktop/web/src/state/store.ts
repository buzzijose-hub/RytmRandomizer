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
 *   - sessionStatus    ← session_status (full payload sans `type`)
 *
 * The store does NOT own a WebSocket; bindings to a `CockpitClient` live in the
 * `bindClientToStore` helper, kept in `src/state/index.ts` for tree-shake friendliness.
 */

import { create } from 'zustand';

import type {
  CockpitSendPlan,
  History,
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
  unsaved_sends: number;
}

export interface CockpitState {
  snapshot: Snapshot | null;
  previewCandidate: MutationCandidate | null;
  history: History | null;
  profile: ProfileModel | null;
  sendPlan: CockpitSendPlan | null;
  sessionStatus: SessionStatus | null;
}

export interface CockpitActions {
  setSnapshot: (snapshot: Snapshot) => void;
  setPreviewCandidate: (candidate: MutationCandidate | null) => void;
  setHistory: (history: History) => void;
  setProfile: (profile: ProfileModel | null) => void;
  setSendPlan: (sendPlan: CockpitSendPlan | null) => void;
  setSessionStatus: (status: SessionStatus) => void;
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
  sendPlan: null,
  sessionStatus: null,
};

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
    setSendPlan: (sendPlan) => set({ sendPlan }),
    setSessionStatus: (status) => set({ sessionStatus: status }),
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

export const selectCanUndo = (s: CockpitState): boolean => {
  const h = s.history;
  if (h === null) return false;
  if (h.entries.length === 0) return false;
  // Cannot undo if current is the first entry.
  return h.entries[0]?.snapshot.snapshot_id !== h.current_id;
};
