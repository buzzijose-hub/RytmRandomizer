/**
 * Public surface of the state module.
 *
 * Re-exports the store + selectors and provides `bindClientToStore`, the canonical
 * wiring that subscribes a CockpitClient's events into a store instance. Kept here
 * (not in `store.ts`) so the store stays transport-agnostic.
 */

import { announce } from '../a11y';
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
  selectPreparedPadCount,
  selectSendPlanReady,
  selectCanSend,
  selectHasHistory,
  selectCanUndo,
} from './store';

export type {
  CockpitState,
  CockpitActions,
  CockpitStore,
  OperatorLogEntry,
  SessionStatus,
} from './store';

/**
 * Wire a CockpitClient's event stream into the given store. Returns an unsubscribe
 * function that detaches every handler. The default store is the module singleton.
 */
export function bindClientToStore(
  client: CockpitClient,
  store: { getState: () => CockpitStore } = useCockpitStore,
): Unsubscribe {
  const unsubs: Unsubscribe[] = [
    client.onStatusChange((status) => {
      store.getState().setConnectionStatus(status);
      store.getState().appendOperatorLog({
        level: status === 'connected' ? 'info' : 'error',
        message: `WebSocket ${status}`,
      });
    }),
    client.on('snapshot_changed', (ev) => store.getState().setSnapshot(ev.snapshot)),
    client.on('mutation_previewed', (ev) => {
      store.getState().setPreviewCandidate(ev.candidate);
      announce(
        ev.candidate !== null
          ? `Mutation preview ready, depth ${Math.round(ev.candidate.depth * 100)}%, ${ev.candidate.pad_deltas.length} pads affected`
          : 'Mutation preview cleared',
      );
    }),
    client.on('send_plan_changed', (ev) => {
      store.getState().setSendPlan(ev.send_plan);
      announce(
        ev.send_plan !== null
          ? `Send plan ready, ${ev.send_plan.pad_count} pads, ${ev.send_plan.estimated_midi_msgs} parameters`
          : 'Send plan cleared',
      );
    }),
    client.on('history_updated', (ev) => store.getState().setHistory(ev.history)),
    client.on('profile_changed', (ev) => {
      store.getState().setProfile(ev.profile);
      announce(
        ev.profile !== null ? `Profile selected: ${ev.profile.name}` : 'Profile cleared',
      );
    }),
    client.on('session_status', (ev) => {
      store.getState().setSessionStatus({
        armed: ev.armed,
        midi_port: ev.midi_port,
        mode: ev.mode,
        unsaved_sends: ev.unsaved_sends,
      });
      announce(`Session status updated, mode ${ev.mode}`);
    }),
  ];
  return () => {
    for (const off of unsubs) off();
  };
}
