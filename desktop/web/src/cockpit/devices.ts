export const RYTM_DEVICE_ID = 'analog_rytm_mk2';
export const ANALOG_FOUR_DEVICE_ID = 'analog_four_mk2';

export type CockpitDeviceId = typeof RYTM_DEVICE_ID | typeof ANALOG_FOUR_DEVICE_ID;

export type AnalogFourZoneState = 'cc-ready' | 'deferred';

export interface AnalogFourMutationZone {
  key: string;
  label: string;
  manualSection: string;
  target: string;
  status: AnalogFourZoneState;
  note: string;
}

export interface AnalogFourTrackProfile {
  track: number;
  trackLabel: string;
  roleKey: string;
  roleLabel: string;
  safeDepth: number;
}

export const ANALOG_FOUR_TRACKS: ReadonlyArray<AnalogFourTrackProfile> = [
  {
    track: 1,
    trackLabel: 'T1',
    roleKey: 'bass_foundation',
    roleLabel: 'Bass / low pulse',
    safeDepth: 76,
  },
  {
    track: 2,
    trackLabel: 'T2',
    roleKey: 'stab_pulse',
    roleLabel: 'Stab / pulse',
    safeDepth: 69,
  },
  {
    track: 3,
    trackLabel: 'T3',
    roleKey: 'texture_motion',
    roleLabel: 'Texture / motion',
    safeDepth: 63,
  },
  {
    track: 4,
    trackLabel: 'T4',
    roleKey: 'space_accent',
    roleLabel: 'Space / accent',
    safeDepth: 58,
  },
];

export const ANALOG_FOUR_MUTATION_ZONES: ReadonlyArray<AnalogFourMutationZone> = [
  {
    key: 'oscillator',
    label: 'Oscillators',
    manualSection: 'OSC1 / OSC2 / COMMON',
    target: 'OSC1 Level',
    status: 'cc-ready',
    note: 'Tone, waveform, pitch, and oscillator balance shaping.',
  },
  {
    key: 'filter',
    label: 'Filters',
    manualSection: 'FILTERS',
    target: 'Filter 1 Frequency',
    status: 'cc-ready',
    note: 'Ladder and multimode filter movement for dark/bright pressure.',
  },
  {
    key: 'envelope',
    label: 'Envelopes',
    manualSection: 'AMP / ENVF / ENV2',
    target: 'Amp Env Decay',
    status: 'cc-ready',
    note: 'Attack, decay, sustain, release, and contour shaping.',
  },
  {
    key: 'modulation',
    label: 'LFO / Modulators',
    manualSection: 'LFO1 / LFO2 / MOD',
    target: 'LFO1 Speed',
    status: 'cc-ready',
    note: 'Rhythmic motion and assignable modulation movement.',
  },
  {
    key: 'effects',
    label: 'Effects Sends',
    manualSection: 'AMP SENDS / FX',
    target: 'Amp Delay Send',
    status: 'cc-ready',
    note: 'Chorus, delay, and reverb send motion from the synth track.',
  },
  {
    key: 'drive',
    label: 'Drive',
    manualSection: 'OVERDRIVE / DRIVE PRESSURE',
    target: 'NRPN-only / deferred',
    status: 'deferred',
    note: 'Tracked as a style intent, but not rendered as a mock CC row yet.',
  },
];
