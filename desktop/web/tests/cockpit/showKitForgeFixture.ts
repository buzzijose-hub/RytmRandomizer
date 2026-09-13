import type {
  KitCaptureResult,
  ShowBankEntry,
  ShowBankState,
  ShowCandidatePair,
  ShowCaptureReference,
} from '../../src/ws/protocol';
import { ANALOG_FOUR_TRACKS } from '../../src/cockpit/devices';
import { snapshot } from './_fixtures';

const when = '2026-09-04T12:00:00+00:00';

function captureReference(
  device_id: ShowCaptureReference['device_id'],
  fingerprint: string,
  hardware_slot: number,
  retained = false,
): ShowCaptureReference {
  const sha = `${fingerprint}${'0'.repeat(64)}`.slice(0, 64);
  return {
    capture_id: `${device_id}-capture`,
    device_id,
    kit_name: device_id === 'analog_rytm_mk2' ? 'RYTM SOURCE' : 'A4 SOURCE',
    hardware_slot,
    fingerprint,
    snapshot_id: device_id === 'analog_rytm_mk2' ? 'snapshot-source' : null,
    captured_at: when,
    round_trip_verified: true,
    sysex: {
      artifact_id: `${device_id}-artifact`,
      frame_sha256: sha,
      frame_bytes: 4096,
      retained: retained ? { artifact_name: `${sha}.syx`, sha256: sha, byte_count: 4096 } : null,
    },
    evidence: [
      {
        evidence_id: `${device_id}-evidence`,
        status: 'round-trip-verified',
        source: 'fixture',
        observed_at: when,
        notes: [],
      },
    ],
  };
}

const rytmSource = captureReference('analog_rytm_mk2', '11111111', 11);
const a4Source = captureReference('analog_four_mk2', '22222222', 22);

function candidate(candidate_id: string, seed: number, retained = false): ShowCandidatePair {
  return {
    candidate_id,
    source_rytm_fingerprint: rytmSource.fingerprint,
    source_a4_fingerprint: a4Source.fingerprint,
    rytm_semantic_fingerprint: `${seed}3333333`,
    recipe: {
      profile_id: 'profile-show',
      depth_preset: seed === 1 ? 'small' : 'large',
      depth: seed === 1 ? 0.25 : 0.75,
      seed,
      rytm_scope: { device_id: 'analog_rytm_mk2', target_ids: [1, 2], locked_ids: [2] },
      analog_four_scope: { device_id: 'analog_four_mk2', target_ids: [1], locked_ids: [] },
    },
    rytm_candidate: {
      candidate_id: `rytm-${candidate_id}`,
      source_snapshot_id: 'snapshot-source',
      profile_id: 'profile-show',
      depth: seed === 1 ? 0.25 : 0.75,
      seed,
      pad_deltas: [{ pad_id: 1, proposed_params: { tun: 64 }, changed_keys: ['tun'] }],
      safety_status: 'safe',
      estimated_midi_msgs: 1,
    },
    analog_four_candidate: {
      artifact_fingerprint: `${seed}4444444`,
      semantic_fingerprint: `${seed}5555555`,
      source_fingerprint: a4Source.fingerprint,
      sysex: {
        artifact_id: `a4-${candidate_id}`,
        frame_sha256: `${seed}${'4'.repeat(63)}`,
        frame_bytes: 4096,
        retained: retained
          ? {
              artifact_name: `${seed}${'4'.repeat(63)}.syx`,
              sha256: `${seed}${'4'.repeat(63)}`,
              byte_count: 4096,
            }
          : null,
      },
      values: [
        {
          track_id: 1,
          parameter: 'filter1_frequency',
          screen_value: '63.50',
          encoded_unsigned_8_8: 16256,
          unpacked_offset: 128,
        },
      ],
      evidence_status: 'offline-captured-kit-mutation-validated',
    },
    created_at: when,
    evidence: [],
  };
}

const candidates = [candidate('candidate-one', 1), candidate('candidate-two', 2, true)];

export const forgeEntry: ShowBankEntry = {
  entry_id: 'entry-one',
  cue_index: 1,
  name: 'Opening Pressure',
  description: 'Controlled opening pair',
  rytm_source: rytmSource,
  analog_four_source: a4Source,
  candidates,
  selected_candidate_id: 'candidate-one',
  rytm_live_auditioned_candidate_id: 'candidate-one',
  rytm_live_auditioned_at: when,
  favorite: { candidate_id: 'candidate-two', selected_at: when, notes: [] },
  rytm_hardware_save: {
    device_id: 'analog_rytm_mk2',
    hardware_slot: 31,
    attested_at: when,
    note: 'Saved manually',
  },
  analog_four_hardware_save: {
    device_id: 'analog_four_mk2',
    hardware_slot: 32,
    attested_at: when,
    note: 'Saved manually',
  },
  rytm_recapture: {
    device_id: 'analog_rytm_mk2',
    expected_semantic_fingerprint: '23333333',
    source_semantic_fingerprint: '11111111',
    observed_semantic_fingerprint: '23333333',
    matches_candidate: true,
    matches_source: false,
    comparison_reason: 'Rytm semantic fingerprint matches favorite',
    recorded_at: when,
    capture: captureReference('analog_rytm_mk2', '23333333', 31, true),
  },
  analog_four_recapture: {
    device_id: 'analog_four_mk2',
    expected_semantic_fingerprint: '25555555',
    source_semantic_fingerprint: '99999999',
    observed_semantic_fingerprint: '99999999',
    matches_candidate: false,
    matches_source: true,
    comparison_reason: 'Analog Four semantic fingerprint differs from favorite',
    recorded_at: when,
    capture: captureReference('analog_four_mk2', '99999999', 32),
  },
  show_time_preflight: null,
  show_ready_at: null,
  oxi: { project: 'Buzzi Live', pattern: 'A01', chapter: 'Opening', direct_oxi_control: false },
  audition_notes: ['Rytm low end checked'],
  energy_level: 3,
  energy_notes: ['medium build'],
  transition_notes: ['filter out over eight bars'],
  recovery_notes: ['reload source slots'],
  created_at: when,
  updated_at: when,
  status: 'hardware-saved',
  rytm_audition_status: 'live_unsaved_hardware',
  readiness: {
    status: 'hardware-saved',
    show_ready: false,
    blocked_reasons: ['a4_recapture_mismatch'],
    recovery_actions: ['recapture_intended_a4_slot'],
  },
};

export const readyEntry: ShowBankEntry = {
  ...forgeEntry,
  entry_id: 'entry-two',
  cue_index: 2,
  name: 'Peak Release',
  favorite: { candidate_id: 'candidate-one', selected_at: when, notes: [] },
  rytm_live_auditioned_candidate_id: null,
  rytm_live_auditioned_at: null,
  rytm_recapture: {
    ...(forgeEntry.rytm_recapture as NonNullable<typeof forgeEntry.rytm_recapture>),
    expected_semantic_fingerprint: '13333333',
    observed_semantic_fingerprint: '13333333',
    comparison_reason: 'Rytm semantic fingerprint matches favorite',
  },
  analog_four_recapture: {
    device_id: 'analog_four_mk2',
    expected_semantic_fingerprint: '15555555',
    source_semantic_fingerprint: '22222222',
    observed_semantic_fingerprint: '15555555',
    matches_candidate: true,
    matches_source: false,
    comparison_reason: 'Analog Four semantic fingerprint matches favorite',
    recorded_at: when,
    capture: captureReference('analog_four_mk2', '14444444', 32, true),
  },
  show_time_preflight: {
    expected_rytm_fingerprint: '23333333',
    observed_rytm_fingerprint: '23333333',
    observed_rytm_capture_id: 'analog_rytm_mk2-capture',
    observed_rytm_captured_at: when,
    rytm_matches: true,
    expected_a4_fingerprint: '14444444',
    observed_a4_fingerprint: '14444444',
    observed_a4_capture_id: 'analog_four_mk2-capture',
    observed_a4_captured_at: when,
    a4_matches: true,
    checked_at: when,
    reason: 'Fresh current captures match retained favorite recaptures',
  },
  show_ready_at: when,
  status: 'show-ready',
  rytm_audition_status: 'not_auditioned',
  readiness: { status: 'show-ready', show_ready: true, blocked_reasons: [], recovery_actions: [] },
};

export const showBankState: ShowBankState = {
  schema_version: 'show-bank-workspace-v1',
  revision: 9,
  active_bank_id: 'bank-one',
  depth_presets: { small: 0.25, medium: 0.5, large: 0.75 },
  banks: [
    {
      schema_version: 'show-bank-v1',
      bank_id: 'bank-one',
      name: 'Warehouse Set',
      description: 'Paired favorites for Friday',
      revision: 7,
      active_entry_id: 'entry-one',
      entries: [forgeEntry, readyEntry],
      notes: ['Keep source kits untouched'],
      evidence: [],
      created_at: when,
      updated_at: when,
      status: 'hardware-saved',
      readiness: {
        status: 'hardware-saved',
        show_ready: false,
        show_ready_entry_ids: ['entry-two'],
        blocked_reasons: ['cue_not_show_ready'],
        recovery_actions: ['verify_entry_one'],
      },
    },
  ],
};

export const forgeCaptures: KitCaptureResult[] = [
  {
    device_id: 'analog_rytm_mk2',
    kit_name: 'CURRENT RYTM',
    slot: 41,
    fingerprint: 'aaaaaaaa',
    frame_bytes: 4096,
    captured_at: when,
    snapshot_layout: 'saved_kit',
    parameter_readiness: 'rytm_anchor_ready',
    round_trip_verified: true,
    input_only: true,
    sent_midi: false,
    layout_items: snapshot.pads.map((pad) => ({
      index: pad.pad_id,
      label: pad.machine,
      status: 'mutation_ready',
      detail: 'Captured Rytm machine fields are available for mutation.',
    })),
  },
  {
    device_id: 'analog_four_mk2',
    kit_name: 'CURRENT A4',
    slot: 42,
    fingerprint: 'bbbbbbbb',
    frame_bytes: 4096,
    captured_at: when,
    snapshot_layout: 'saved_kit',
    parameter_readiness: 'filter1_frequency_offline_ready',
    round_trip_verified: true,
    input_only: true,
    sent_midi: false,
    layout_items: ANALOG_FOUR_TRACKS.map((track) => ({
      index: track.track,
      label: track.trackLabel,
      status: 'mutation_ready',
      detail: 'Filter 1 Frequency is verified for offline captured-kit mutation; every other parameter remains mapping-blocked',
    })),
  },
];
