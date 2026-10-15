import type { A4NativeTransportPreview, A4PreparationReport } from '../../src/ws/protocol';
import contracts from './a4NativeTransportContract.json' with { type: 'json' };
import { forgeEntry } from './showKitForgeFixture';

export const a4PreparationReport: A4PreparationReport = {
  schema_version: 'a4-preparation-v1', preparation_id: 'review-1', entry_id: forgeEntry.entry_id,
  candidate_id: forgeEntry.selected_candidate_id, device_id: 'analog_four_mk2',
  source_capture_id: 'source-a4', source_fingerprint: 'source', source_frame_sha256: 'source-sha',
  candidate_frame_sha256: 'candidate-sha', current_capture_fingerprint: 'source',
  current_capture_at: '2026-09-07T12:00:00Z', capture_after: '2026-09-07T11:00:00Z',
  checked_at: '2026-09-07T12:01:00Z', target_ids: [1], locked_ids: [], effective_ids: [1],
  output_port_name: 'A4 studio', recovery_slot: 20, source_reloaded: false,
  candidate_is_local: true, candidate_bytes_verified: true, current_source_verified: true,
  changes: [{ track_id: 1, parameter: 'filter1_frequency', before_raw_q8_8: 0,
    after_raw_q8_8: 4096, before_screen_value: '0', after_screen_value: '16', unpacked_offsets: [128, 129] }],
  blocked_reasons: ['source_reload_required', 'a4_hardware_audition_validation_pending',
    'a4_live_transport_mapping_unverified', 'persistent_kit_write_prohibited'],
  ready: false, hardware_send_validated: false, output_authority: 'offline-review-only',
};

export function a4TransportReport(complete: boolean): A4PreparationReport {
  const serialized = contracts[complete ? 'complete' : 'mixed'];
  return {
    ...a4PreparationReport,
    changes: serialized.changes,
    transport_preview: serialized.transport_preview as A4NativeTransportPreview,
  };
}
