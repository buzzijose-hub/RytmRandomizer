import type { A4StudioAuditionPlan } from '../../src/ws/protocol';
import { forgeEntry, showBankState } from './showKitForgeFixture';
import pythonDto from './a4StudioAudition.python.json';

// Producer 646e0044: studio_case.__wrapped__(tmp).with_mutations((
// AnalogFourNativeMutation('osc1_level', 1, 100),)).prepare().to_dict(),
// with explicit routing below and matching context.output_port_name.
export const pythonStudioPlan = pythonDto as unknown as A4StudioAuditionPlan;

export const studioPort = 'Elektron Analog Four MKII Out';
export const studioPlan: A4StudioAuditionPlan = {
  plan_id: 'a4-studio-exact-plan',
  ready: true,
  blocked_reasons: [],
  bank_id: showBankState.banks[0]!.bank_id,
  bank_revision: showBankState.banks[0]!.revision,
  entry_id: forgeEntry.entry_id,
  candidate_id: forgeEntry.selected_candidate_id,
  session_generation: 19,
  routing: { output_port_name: studioPort, track_channels: [2, 4, 6, 8] },
  send_plan: {
    plan_id: 'a4-studio-exact-plan', candidate_id: forgeEntry.selected_candidate_id!,
    source_snapshot_id: forgeEntry.analog_four_source.capture_id, profile_id: 'profile-show',
    ready: true, readiness_reason: 'ready', safety_status: 'armed', estimated_midi_msgs: 1,
    pad_count: 1, locked_pad_ids: [], target_pad_ids: [1], blocked_reasons: [],
    packets: [{ pad_id: 1, parameter: 'osc1_level', channel: 1, control: 69, value: 100 }],
  },
  hardware_send_validated: false,
  persistent_write: false,
  output_authority: 'studio-ram-only-unqualified',
};
