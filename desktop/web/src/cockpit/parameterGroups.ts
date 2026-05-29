export interface ParameterDefinition {
  key: string;
  code: string;
  label: string;
}

export interface ParameterGroup {
  title: string;
  params: ReadonlyArray<ParameterDefinition>;
}

export const RYTM_PARAMETER_GROUPS: ReadonlyArray<ParameterGroup> = [
  {
    title: 'Synth',
    params: [
      { key: 'tun', code: 'TUN', label: 'Tune' },
      { key: 'swt', code: 'SWT', label: 'Sweep Time' },
      { key: 'snap', code: 'SNP', label: 'Snap Amount' },
      { key: 'dec', code: 'DEC', label: 'Decay Time' },
      { key: 'wave', code: 'WAV', label: 'Waveform' },
      { key: 'hold', code: 'HLD', label: 'Hold Time' },
      { key: 'tick', code: 'TCK', label: 'Tick' },
      { key: 'lev', code: 'LEV', label: 'Level' },
    ],
  },
  {
    title: 'Sample',
    params: [
      { key: 'sample_tune', code: 'SMT', label: 'Sample Tune' },
      { key: 'sample_fine', code: 'FIN', label: 'Fine Tune' },
      { key: 'sample_bit', code: 'BIT', label: 'Bit Reduction' },
      { key: 'sample_slot', code: 'SLT', label: 'Sample Slot' },
      { key: 'sample_start', code: 'STA', label: 'Start' },
      { key: 'sample_end', code: 'END', label: 'End' },
      { key: 'sample_loop', code: 'LOP', label: 'Loop' },
      { key: 'sample_level', code: 'SML', label: 'Sample Level' },
    ],
  },
  {
    title: 'Filter Envelope',
    params: [
      { key: 'filter_attack', code: 'FAT', label: 'Filter Attack' },
      { key: 'filter_decay', code: 'FDC', label: 'Filter Decay' },
      { key: 'filter_sustain', code: 'FSU', label: 'Filter Sustain' },
      { key: 'filter_release', code: 'FRL', label: 'Filter Release' },
      { key: 'flt', code: 'FLT', label: 'Filter Frequency' },
      { key: 'filter_resonance', code: 'RES', label: 'Resonance' },
      { key: 'filter_env', code: 'ENV', label: 'Env Depth' },
    ],
  },
  {
    title: 'Amp Envelope',
    params: [
      { key: 'amp_attack', code: 'AAT', label: 'Amp Attack' },
      { key: 'amp_hold', code: 'AHD', label: 'Amp Hold' },
      { key: 'amp_decay', code: 'ADC', label: 'Amp Decay' },
      { key: 'pan', code: 'PAN', label: 'Pan' },
      { key: 'accent', code: 'ACC', label: 'Accent' },
      { key: 'overdrive', code: 'DRV', label: 'Overdrive' },
      { key: 'delay', code: 'DLY', label: 'Delay' },
      { key: 'reverb', code: 'REV', label: 'Reverb' },
    ],
  },
  {
    title: 'LFO',
    params: [
      { key: 'lfo_destination', code: 'LDS', label: 'Destination' },
      { key: 'lfo_depth', code: 'LDP', label: 'LFO Depth' },
      { key: 'lfo_phase', code: 'LPH', label: 'Start Phase' },
      { key: 'lfo_fade', code: 'LFD', label: 'Fade' },
      { key: 'lfo_mult', code: 'LML', label: 'Multiplier' },
      { key: 'lfo_speed', code: 'LSP', label: 'LFO Speed' },
    ],
  },
];
