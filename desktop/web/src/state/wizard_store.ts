/**
 * Wizard state store (Zustand) — mirrors the WS-D Python `WizardState`.
 *
 * The store owns:
 *   - `state`             — the latest WizardState pushed by the sidecar (null until start)
 *   - `lastCreatedProfile` — populated when a `profile_created` event arrives
 *
 * Action surface:
 *   - `handleEvent(event)`   — reducer over the three wizard event types
 *   - `sendCommand(cmd)`     — typed pass-through to the injected `CockpitClient`
 *   - `bindClient(client)`   — subscribe to wizard_state_changed / analysis_progress /
 *                              profile_created and route them through `handleEvent`
 *
 * The store does NOT own a WebSocket; the binding helper is called from the wizard route
 * mount so the binding lifetime tracks the wizard surface lifetime.
 */

import { create } from 'zustand';

import type { CockpitClient, Unsubscribe } from '../ws/client';
import type {
  AnalysisJob,
  AnalysisProgressEvent,
  CandidateProfileModel,
  ProfileCreatedEvent,
  WizardCommand,
  WizardEvent,
  WizardState,
  WizardStateChangedEvent,
} from '../types/wizard_protocol';

// ---------- Slice + actions ----------

export interface WizardSlice {
  state: WizardState | null;
  lastCreatedProfile: CandidateProfileModel | null;
}

export interface WizardActions {
  handleEvent: (event: WizardEvent) => void;
  reset: () => void;
}

export type WizardStore = WizardSlice & WizardActions;

export const INITIAL_WIZARD_STATE: WizardSlice = {
  state: null,
  lastCreatedProfile: null,
};

// ---------- Store factory + singleton ----------

/** Create a fresh, isolated store instance (used by tests for hermetic state). */
export function createWizardStore() {
  return create<WizardStore>((set, get) => ({
    ...INITIAL_WIZARD_STATE,
    handleEvent: (event) => {
      if (event.type === 'wizard_state_changed') {
        set({ state: applyStateChanged(event) });
        return;
      }
      if (event.type === 'analysis_progress') {
        const current = get().state;
        if (current === null) return;
        set({ state: applyAnalysisProgress(current, event) });
        return;
      }
      // Exhaustive: only `profile_created` remains.
      set({ lastCreatedProfile: applyProfileCreated(event) });
    },
    reset: () => set({ ...INITIAL_WIZARD_STATE }),
  }));
}

/** Module-level singleton consumed by the React wizard route. */
export const useWizardStore = createWizardStore();

// ---------- Event reducers (pure, branch-coverable) ----------

function applyStateChanged(event: WizardStateChangedEvent): WizardState {
  return event.state;
}

function applyAnalysisProgress(
  current: WizardState,
  event: AnalysisProgressEvent,
): WizardState {
  // The Python sidecar emits the full job dict (`{type, job}`), so we replace the
  // matching job wholesale — this propagates `extracted_traits` + `error` in
  // addition to `status`/`progress`, which a field-level merge would drop.
  const updatedJobs: AnalysisJob[] = current.jobs.map((job) =>
    job.source_id === event.job.source_id ? event.job : job,
  );
  return { ...current, jobs: updatedJobs };
}

function applyProfileCreated(event: ProfileCreatedEvent): CandidateProfileModel {
  return event.profile;
}

// ---------- Client binding ----------

/**
 * Subscribe the given store to a CockpitClient's wizard event stream. Returns an
 * unsubscribe that detaches every handler. Default target is the module singleton.
 */
export function bindWizardClient(
  client: CockpitClient,
  store: { getState: () => WizardStore } = useWizardStore,
): Unsubscribe {
  const unsubs: Unsubscribe[] = [
    client.on('wizard_state_changed' as never, ((ev: WizardStateChangedEvent) => {
      store.getState().handleEvent(ev);
    }) as never),
    client.on('analysis_progress' as never, ((ev: AnalysisProgressEvent) => {
      store.getState().handleEvent(ev);
    }) as never),
    client.on('profile_created' as never, ((ev: ProfileCreatedEvent) => {
      store.getState().handleEvent(ev);
    }) as never),
  ];
  return () => {
    for (const off of unsubs) off();
  };
}

/**
 * Typed `send` wrapper. Returns the underlying ack promise; callers await for the
 * "ok" + payload. The cast widens the wizard command into the cockpit `Command` union;
 * at runtime the cockpit client dispatches on `type` so any string-keyed object is fine.
 */
export function sendWizardCommand(
  client: CockpitClient,
  command: WizardCommand,
): ReturnType<CockpitClient['send']> {
  return client.send(command as never);
}

// ---------- Selectors ----------

export const selectStep = (s: WizardSlice): WizardState['step'] | null => s.state?.step ?? null;

export const selectSources = (s: WizardSlice): WizardState['sources'] =>
  s.state?.sources ?? [];

export const selectJobs = (s: WizardSlice): WizardState['jobs'] => s.state?.jobs ?? [];

export const selectCandidateProfile = (
  s: WizardSlice,
): CandidateProfileModel | null => s.state?.candidate_profile ?? null;

export const selectIsWizardActive = (s: WizardSlice): boolean => s.state !== null;

export const selectAnalysisComplete = (s: WizardSlice): boolean => {
  const jobs = s.state?.jobs ?? [];
  if (jobs.length === 0) return false;
  return jobs.every((j) => j.status === 'ok' || j.status === 'failed');
};
