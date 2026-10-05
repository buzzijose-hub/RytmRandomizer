import type { LibraryRecord, MutationParametersChangedEvent, PerformanceParameterControl } from '../../src/ws/protocol';
import { libraryRecordA } from './_fixtures';

export function scopeControl(patch: Partial<PerformanceParameterControl> = {}): PerformanceParameterControl {
  return {
    device_id: 'analog_rytm_mk2', item_id: 2, machine: 'SD CLASSIC', parameter_key: 'flt',
    page: 'FILTER', name: 'Filter Frequency', value: 64, display_value: '64', minimum: 0, maximum: 127,
    native_precision: 'cc7', mutation_supported: true, send_supported: true, protected: false,
    reasons: [], evidence_level: 'documented_only', ...patch,
  };
}

export const parameterControls: PerformanceParameterControl[] = [
  scopeControl(),
  scopeControl({ parameter_key: 'amp_decay', page: 'AMP', name: 'Amp Decay Time' }),
  scopeControl({ parameter_key: 'overdrive', page: 'AMP', name: 'Amp Overdrive', value: 12, display_value: null }),
  scopeControl({ parameter_key: 'reverb', page: 'AMP', name: 'Amp Reverb Send', value: 0, display_value: '0' }),
  scopeControl({ parameter_key: 'pitch', page: 'SRC', name: 'Tune', protected: true, reasons: ['pitch_protected'] }),
  scopeControl({ parameter_key: 'missing', page: 'SRC', name: 'Missing source', value: null, display_value: null, minimum: null, maximum: null }),
  scopeControl({ parameter_key: 'src_level', page: 'SRC', name: 'Synth Level', mutation_supported: false, reasons: ['src_level_protected'] }),
  scopeControl({ parameter_key: 'lfo_depth', page: 'LFO', name: 'LFO Depth', native_precision: 'paired_cc14', send_supported: false, reasons: ['paired_control_precision_unverified'] }),
  scopeControl({ item_id: 1, machine: 'BD HARD', parameter_key: 'src_bd_hard_decay', page: 'SRC', name: 'BD Decay' }),
  scopeControl({ item_id: 11, machine: 'CY RIDE', parameter_key: 'src_cy_ride_tail', page: 'SRC', name: 'Tail Decay', mutation_supported: false, send_supported: false, reasons: ['src_cy_ride_slot_unverified'] }),
  scopeControl({ device_id: 'analog_four_mk2', item_id: 1, machine: 'A4', parameter_key: 'filter1_frequency', page: 'FILTER', name: 'Filter 1 Frequency', value: 16256, display_value: '63.50', maximum: 32512, native_precision: 'unsigned_q8_8', send_supported: false, evidence_level: 'offline_verified' }),
  scopeControl({ device_id: 'analog_four_mk2', item_id: 1, machine: 'A4', parameter_key: 'osc1_tune', page: 'OSC1', name: 'OSC1 Tune', mutation_supported: false, send_supported: false, reasons: ['saved_offset_unverified'] }),
];

export const parameterEvent: MutationParametersChangedEvent = {
  type: 'mutation_parameters_changed', rytm_parameters: null, a4_parameters: [], controls: parameterControls,
};

export const rehearsalRecord: LibraryRecord = {
  ...libraryRecordA, record_id: 'favorite-1', kit_name: 'Pad 2 rehearsal', record_kind: 'rehearsal_favorite',
  rehearsal: { armed: true, send_plan: { ready: true }, seed: -1, scope: 'untrusted summary' },
};
