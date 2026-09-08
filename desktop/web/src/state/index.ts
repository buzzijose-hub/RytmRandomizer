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
  MIDI_ACTIVITY_RING_LIMIT,
  RECONNECT_NOTICE,
  selectIsConnected,
  selectIsArmed,
  selectUnsavedSends,
  selectPadCount,
  selectPreparedPadCount,
  selectSendPlanReady,
  selectCanSend,
  selectHasHistory,
  selectCanUndo,
  selectConnectionPhase,
} from './store';

export type {
  CockpitState,
  CockpitActions,
  CockpitStore,
  MidiActivityMeta,
  MonitorRow,
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
    client.on('profile_catalog_changed', (ev) => {
      store.getState().setProfileCatalog(ev.profiles);
      announce(`Profile catalogue updated, ${ev.profiles.length} profiles available`);
    }),
    client.on('kit_captures_changed', (ev) => {
      store.getState().setKitCaptures(ev.captures);
      announce(
        ev.captures.length > 0
          ? `Current kit anchors updated, ${ev.captures.length} machines captured`
          : 'No current kit anchors captured',
      );
    }),
    client.on('mutation_targets_changed', (ev) => {
      store.getState().setMutationTargets(ev.rytm_pad_targets, ev.a4_track_targets);
      announce(
        `Mutation targets updated, ${ev.rytm_pad_targets.length || 12} Rytm pads and ${ev.a4_track_targets.length || 4} Analog Four tracks in scope`,
      );
    }),
    client.on('mutation_locks_changed', (ev) => {
      store.getState().setMutationLocks(ev.rytm_pad_locks, ev.a4_track_locks);
      announce(
        `Mutation locks updated, ${ev.rytm_pad_locks.length} Rytm pads and ${ev.a4_track_locks.length} Analog Four tracks protected`,
      );
    }),
    client.on('dual_machine_stage_changed', (ev) => {
      store.getState().setDualMachineStage(ev.stage);
      announce(
        `Dual-machine stage revision ${ev.stage.revision}, Rytm plan ${ev.stage.rytm.plan_state}, Analog Four plan ${ev.stage.analog_four.plan_state}`,
      );
    }),
    client.on('patch_genome_changed', (ev) => {
      store.getState().setPatchGenome(ev.patch_genome);
      announce(
        `Analog Four patch genome ready, ${ev.patch_genome.genome.candidate_count} candidates`,
      );
    }),
    client.on('performance_console_changed', (ev) => {
      store.getState().setPerformanceConsole(ev.performance_console);
      announce(
        ev.performance_console !== null
          ? 'Performance console packet ready'
          : 'Performance console packet cleared',
      );
    }),
    client.on('session_status', (ev) => {
      store.getState().setSessionStatus({
        armed: ev.armed,
        midi_port: ev.midi_port,
        mode: ev.mode,
        connection_phase: ev.connection_phase,
        unsaved_sends: ev.unsaved_sends,
        capture_enabled: ev.capture_enabled,
      });
      announce(
        `Session status updated, mode ${ev.mode}, ${ev.armed ? 'armed' : 'passive'}`,
      );
    }),
    client.on('connection_changed', (ev) => {
      store.getState().setConnection(ev.connection);
      // Single coalesced live region: the announcer debounces bursts so a
      // reconnect (fault → searching → listening) reads as one message.
      announce(`Connection ${ev.connection.phase}`);
    }),
    client.on('midi_activity', (ev) => {
      // Deliberately silent for screen readers: activity batches arrive up
      // to ~16×/s and would flood the polite region.
      store.getState().appendMidiActivity(ev.midi_activity);
    }),
    client.on('library_changed', (ev) => {
      store.getState().setLibraryRecords(ev.library.records);
      announce(`Library updated, ${ev.library.records.length} records`);
    }),
    client.on('show_bank_changed', (ev) => {
      store.getState().setShowBank(ev.show_bank);
      announce(
        ev.show_bank === null
          ? 'Show Kit Forge bank state cleared'
          : `Show Kit Forge updated, ${ev.show_bank.banks.length} banks available`,
      );
    }),
  ];
  return () => {
    for (const off of unsubs) off();
  };
}
