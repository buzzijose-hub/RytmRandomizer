export const RYTM_DEVICE_ID = 'analog_rytm_mk2';
export const ANALOG_FOUR_DEVICE_ID = 'analog_four_mk2';

export type CockpitDeviceId = typeof RYTM_DEVICE_ID | typeof ANALOG_FOUR_DEVICE_ID;

export type AnalogFourZoneState = 'cc-ready' | 'deferred';
export type AnalogFourTrackRoleKey =
  | 'bass_foundation'
  | 'stab_pulse'
  | 'texture_motion'
  | 'space_accent';
export type AnalogFourMutationZoneKey =
  | 'oscillator'
  | 'filter'
  | 'envelope'
  | 'modulation'
  | 'effects'
  | 'drive';

export interface AnalogFourOxiMacroAction {
  key: 'anchor' | 'shape' | 'pressure' | 'space';
  label: string;
  targetZoneKey: AnalogFourMutationZoneKey;
  targetParameter: string;
  scope: string;
  status: AnalogFourZoneState;
  performerNote: string;
}

export interface AnalogFourMutationZone {
  key: AnalogFourMutationZoneKey;
  label: string;
  manualSection: string;
  target: string;
  status: AnalogFourZoneState;
  note: string;
}

export interface AnalogFourTrackProfile {
  track: number;
  trackLabel: string;
  roleKey: AnalogFourTrackRoleKey;
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

export const ANALOG_FOUR_OXI_ACTIONS_BY_ROLE: Readonly<
  Record<AnalogFourTrackRoleKey, ReadonlyArray<AnalogFourOxiMacroAction>>
> = {
  bass_foundation: [
    {
      key: 'anchor',
      label: 'Anchor',
      targetZoneKey: 'oscillator',
      targetParameter: 'OSC1 Level',
      scope: 'Keep the low pulse centered.',
      status: 'cc-ready',
      performerNote: 'Use as the stable bass reset before wider movement.',
    },
    {
      key: 'shape',
      label: 'Shape',
      targetZoneKey: 'filter',
      targetParameter: 'Filter 1 Frequency',
      scope: 'Open or darken the bass lane.',
      status: 'cc-ready',
      performerNote: 'Small sweeps keep the kick relationship intact.',
    },
    {
      key: 'pressure',
      label: 'Pressure',
      targetZoneKey: 'envelope',
      targetParameter: 'Amp Env Decay',
      scope: 'Tighten or lengthen the body.',
      status: 'cc-ready',
      performerNote: 'Good for OXI-style build pressure without changing notes.',
    },
    {
      key: 'space',
      label: 'Space',
      targetZoneKey: 'drive',
      targetParameter: 'NRPN-only / deferred',
      scope: 'Drive pressure remains parked.',
      status: 'deferred',
      performerNote: 'Held until the A4 drive path is separately validated.',
    },
  ],
  stab_pulse: [
    {
      key: 'anchor',
      label: 'Anchor',
      targetZoneKey: 'oscillator',
      targetParameter: 'OSC1 Pulsewidth',
      scope: 'Keep the stab tone coherent.',
      status: 'cc-ready',
      performerNote: 'Pulse width movement reads clearly on short synth hits.',
    },
    {
      key: 'shape',
      label: 'Shape',
      targetZoneKey: 'filter',
      targetParameter: 'Filter 1 Frequency',
      scope: 'Make the pulse brighter or tighter.',
      status: 'cc-ready',
      performerNote: 'Use modest range for rhythmic call-and-response parts.',
    },
    {
      key: 'pressure',
      label: 'Pressure',
      targetZoneKey: 'modulation',
      targetParameter: 'LFO1 Speed',
      scope: 'Add tempo-feeling motion.',
      status: 'cc-ready',
      performerNote: 'Keeps the action in dry-run territory until armed later.',
    },
    {
      key: 'space',
      label: 'Space',
      targetZoneKey: 'effects',
      targetParameter: 'Amp Delay Send',
      scope: 'Add repeat energy around the stab.',
      status: 'cc-ready',
      performerNote: 'Good for breakdowns and short fills.',
    },
  ],
  texture_motion: [
    {
      key: 'anchor',
      label: 'Anchor',
      targetZoneKey: 'oscillator',
      targetParameter: 'OSC2 Level',
      scope: 'Set the texture weight.',
      status: 'cc-ready',
      performerNote: 'Keeps the layer present without stealing the low end.',
    },
    {
      key: 'shape',
      label: 'Shape',
      targetZoneKey: 'modulation',
      targetParameter: 'LFO1 Speed',
      scope: 'Change the motion rate.',
      status: 'cc-ready',
      performerNote: 'Primary movement lane for atmosphere and motion.',
    },
    {
      key: 'pressure',
      label: 'Pressure',
      targetZoneKey: 'filter',
      targetParameter: 'Filter 1 Resonance',
      scope: 'Push the edge of the texture.',
      status: 'cc-ready',
      performerNote: 'Use restrained values for hypnotic pressure.',
    },
    {
      key: 'space',
      label: 'Space',
      targetZoneKey: 'effects',
      targetParameter: 'Amp Reverb Send',
      scope: 'Move the texture backward or forward.',
      status: 'cc-ready',
      performerNote: 'Useful for long transitions without changing patterns.',
    },
  ],
  space_accent: [
    {
      key: 'anchor',
      label: 'Anchor',
      targetZoneKey: 'effects',
      targetParameter: 'Amp Delay Send',
      scope: 'Pin the accent space.',
      status: 'cc-ready',
      performerNote: 'A predictable return point for space accents.',
    },
    {
      key: 'shape',
      label: 'Shape',
      targetZoneKey: 'effects',
      targetParameter: 'Amp Reverb Send',
      scope: 'Widen the tail.',
      status: 'cc-ready',
      performerNote: 'Lets the A4 breathe around the Rytm without pattern edits.',
    },
    {
      key: 'pressure',
      label: 'Pressure',
      targetZoneKey: 'modulation',
      targetParameter: 'LFO1 Speed',
      scope: 'Add evolving accent motion.',
      status: 'cc-ready',
      performerNote: 'Keeps movement visible and reversible in the cockpit.',
    },
    {
      key: 'space',
      label: 'Space',
      targetZoneKey: 'drive',
      targetParameter: 'NRPN-only / deferred',
      scope: 'Drive pressure remains parked.',
      status: 'deferred',
      performerNote: 'Held until the A4 drive path is separately validated.',
    },
  ],
};

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
