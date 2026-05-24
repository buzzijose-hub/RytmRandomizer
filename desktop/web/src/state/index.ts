/**
 * Public surface of the state module.
 *
 * Re-exports the store + selectors and provides `bindClientToStore`, the canonical
 * wiring that subscribes a CockpitClient's events into a store instance. Kept here
 * (not in `store.ts`) so the store stays transport-agnostic.
 */

import type { CockpitClient, Unsubscribe } from '../ws/client';

import { useCockpitStore, type CockpitStore } from './store';

export {
  createCockpitStore,
  useCockpitStore,
  INITIAL_STATE,
  selectIsConnected,
  selectIsArmed,
  selectUnsavedSends,
  selectPadCount,
  selectHasHistory,
  selectCanUndo,
} from './store';

export type { CockpitState, CockpitActions, CockpitStore, SessionStatus } from './store';

/**
 * Wire a CockpitClient's event stream into the given store. Returns an unsubscribe
 * function that detaches every handler. The default store is the module singleton.
 */
export function bindClientToStore(
  client: CockpitClient,
  store: { getState: () => CockpitStore } = useCockpitStore,
): Unsubscribe {
  const unsubs: Unsubscribe[] = [
    client.on('snapshot_changed', (ev) => store.getState().setSnapshot(ev.snapshot)),
    client.on('mutation_previewed', (ev) =>
      store.getState().setPreviewCandidate(ev.candidate),
    ),
    client.on('history_updated', (ev) => store.getState().setHistory(ev.history)),
    client.on('profile_changed', (ev) => store.getState().setProfile(ev.profile)),
    client.on('session_status', (ev) =>
      store.getState().setSessionStatus({
        armed: ev.armed,
        midi_port: ev.midi_port,
        mode: ev.mode,
        unsaved_sends: ev.unsaved_sends,
      }),
    ),
  ];
  return () => {
    for (const off of unsubs) off();
  };
}
