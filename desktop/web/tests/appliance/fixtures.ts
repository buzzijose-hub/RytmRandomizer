import type { EventHandler, Unsubscribe } from '../../src/ws/client';
import type { ApplianceLane, ApplianceState, Event, EventType } from '../../src/ws/protocol';
import { FakeCockpitClient } from '../cockpit/_fixtures';

function lane(device_id: ApplianceLane['device_id']): ApplianceLane {
  return {
    device_id,
    reference_track_id: 1,
    scope: { target_ids: [1, 2], locked_ids: [2], page_ids: ['FILTER'], track_depths: {}, page_depths: {}, parameter_locks: ['pitch'] },
    provenance: { source_type: 'simulation', fingerprint: `fixture-${device_id}`, captured_at: '2026-09-30T14:00:00Z', kit_name: 'TOUCH REHEARSAL', working_state_verified: false },
    parameters: [
      { parameter_id: 'cutoff', page: 'FILTER', parameter: 'CUTOFF', cockpit_key: 'flt', value: 64, machine_key: null, values_by_track: { '1': 64, '2': 72 }, default_protected: false, categorical: false, protection_reasons: [], blockers: [] },
      { parameter_id: 'pitch', page: 'FILTER', parameter: 'TUNING', cockpit_key: 'tun', value: 64, machine_key: null, values_by_track: { '1': 64, '2': 72 }, default_protected: true, categorical: false, protection_reasons: ['tuning'], blockers: [] },
      { parameter_id: 'route', page: 'FILTER', parameter: 'ROUTING', cockpit_key: null, value: null, machine_key: null, values_by_track: {}, default_protected: true, categorical: true, protection_reasons: ['routing'], blockers: ['offset_unknown'] },
      { parameter_id: 'decay', page: 'AMP', parameter: 'DECAY', cockpit_key: 'dec', value: 70, machine_key: null, values_by_track: { '1': 70, '2': 80 }, default_protected: false, categorical: false, protection_reasons: [], blockers: ['capture_mapping_pending'] },
    ], blocked_reasons: [],
  };
}

export function applianceState(patch: Partial<ApplianceState> = {}): ApplianceState {
  return {
    schema_version: 1, revision: 3, mode: 'simulation', target: 'rytm', master_depth: .25, armed: false,
    lanes: { analog_rytm_mk2: lane('analog_rytm_mk2'), analog_four_mk2: lane('analog_four_mk2') }, candidate: null,
    history: { can_undo: true, can_redo: true, count: 3, anchor_captured: true, hardware_restore_supported: false },
    profiles: [{ name: 'SAFE', association: { device_ids: ['analog_rytm_mk2'], fingerprints: { analog_rytm_mk2: 'fixture-analog_rytm_mk2' } } }],
    last_receipt: null, blocked_reasons: [], ...patch,
  };
}

export function candidateState(): ApplianceState {
  return applianceState({ candidate: { candidate_id: 'candidate-3', revision: 3, changes: [{ device_id: 'analog_rytm_mk2', track_id: 1, parameter_id: 'cutoff', parameter: 'CUTOFF', page: 'FILTER', before: 64, after: 68 }], send_plan_id: null, live_ready: false, blocked_reasons: [] } });
}

export class ApplianceFakeClient extends FakeCockpitClient {
  private readonly eventBuckets = new Map<EventType, Set<EventHandler>>();
  override on<T extends EventType>(type: T, callback: EventHandler<Extract<Event, { type: T }>>): Unsubscribe {
    let bucket = this.eventBuckets.get(type);
    if (bucket === undefined) { bucket = new Set(); this.eventBuckets.set(type, bucket); }
    const listener = callback as EventHandler;
    bucket.add(listener);
    return () => { bucket.delete(listener); };
  }
  emit(event: Event): void { for (const listener of this.eventBuckets.get(event.type) ?? []) listener(event); }
}
