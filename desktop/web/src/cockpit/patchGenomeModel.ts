export type PatchGenomeFamilyKey =
  | 'oscillator'
  | 'envelope_lfo'
  | 'filter_fx'
  | 'performance';

export type PatchGenomeGeneStatus = 'ready' | 'review' | 'deferred';

export interface PatchGenomeGene {
  key: string;
  label: string;
  parameterLabel: string;
  laneLabel: string;
  currentValue: number;
  candidateValue: number;
  status: PatchGenomeGeneStatus;
  statusLabel: string;
}

export interface PatchGenomeTrait {
  key: string;
  label: string;
  valuePercent: number;
}

export interface PatchGenomeFamily {
  key: PatchGenomeFamilyKey;
  sectionLabel: string;
  label: string;
  summary: string;
  sendPolicy: string;
  genes: ReadonlyArray<PatchGenomeGene>;
}

export interface PatchGenomeModel {
  targetDeviceLabel: string;
  sourceLabel: string;
  seedLabel: string;
  designStatus: string;
  traits: ReadonlyArray<PatchGenomeTrait>;
  families: ReadonlyArray<PatchGenomeFamily>;
}

export function getPatchGenomeFamily(
  model: PatchGenomeModel,
  key: PatchGenomeFamilyKey,
): PatchGenomeFamily | undefined {
  return model.families.find((family) => family.key === key);
}

export function countReadyGenes(genes: ReadonlyArray<PatchGenomeGene>): number {
  return genes.filter((gene) => gene.status === 'ready').length;
}

export const DEFAULT_PATCH_GENOME_MODEL: PatchGenomeModel = {
  targetDeviceLabel: 'Analog Four MKII',
  sourceLabel: 'Patch-family design reference',
  seedLabel: 'seed 211134509',
  designStatus: 'UI design preview',
  traits: [
    { key: 'energy', label: 'Energy', valuePercent: 72 },
    { key: 'brightness', label: 'Brightness', valuePercent: 58 },
    { key: 'motion', label: 'Motion', valuePercent: 81 },
    { key: 'space', label: 'Space', valuePercent: 64 },
  ],
  families: [
    {
      key: 'oscillator',
      sectionLabel: 'I',
      label: 'Oscillators',
      summary: 'Core tone, oscillator balance, pitch relationship, and noise weight.',
      sendPolicy: 'Preview rows resolve to CC-ready oscillator lanes only.',
      genes: [
        {
          key: 'osc_mix',
          label: 'Oscillator Mix',
          parameterLabel: 'OSC1 / OSC2 Balance',
          laneLabel: 'tone anchor',
          currentValue: 58,
          candidateValue: 71,
          status: 'ready',
          statusLabel: 'CC-ready',
        },
        {
          key: 'pulse_width',
          label: 'Pulse Width',
          parameterLabel: 'OSC1 Pulsewidth',
          laneLabel: 'shape',
          currentValue: 46,
          candidateValue: 53,
          status: 'ready',
          statusLabel: 'CC-ready',
        },
        {
          key: 'noise_level',
          label: 'Noise Level',
          parameterLabel: 'Noise Amount',
          laneLabel: 'edge',
          currentValue: 21,
          candidateValue: 34,
          status: 'review',
          statusLabel: 'Review',
        },
      ],
    },
    {
      key: 'envelope_lfo',
      sectionLabel: 'II',
      label: 'Envelope / LFO',
      summary: 'Contour and rhythmic motion genes that make a patch breathe.',
      sendPolicy: 'Envelope/LFO rows stay dry-run until a candidate send plan is prepared.',
      genes: [
        {
          key: 'amp_decay',
          label: 'Amp Decay',
          parameterLabel: 'Amp Env Decay',
          laneLabel: 'body',
          currentValue: 67,
          candidateValue: 78,
          status: 'ready',
          statusLabel: 'CC-ready',
        },
        {
          key: 'lfo_speed',
          label: 'LFO Speed',
          parameterLabel: 'LFO1 Speed',
          laneLabel: 'motion',
          currentValue: 49,
          candidateValue: 69,
          status: 'ready',
          statusLabel: 'CC-ready',
        },
        {
          key: 'lfo_depth',
          label: 'LFO Depth',
          parameterLabel: 'LFO1 Depth',
          laneLabel: 'motion amount',
          currentValue: 38,
          candidateValue: 44,
          status: 'ready',
          statusLabel: 'CC-ready',
        },
      ],
    },
    {
      key: 'filter_fx',
      sectionLabel: 'III',
      label: 'Filter / FX',
      summary: 'Brightness, resonance, and space genes for the patch surface.',
      sendPolicy: 'Two genes are CC-ready; wide ambience remains review-only.',
      genes: [
        {
          key: 'filter_freq',
          label: 'Filter Frequency',
          parameterLabel: 'Filter 1 Frequency',
          laneLabel: 'brightness',
          currentValue: 62,
          candidateValue: 84,
          status: 'ready',
          statusLabel: 'CC-ready',
        },
        {
          key: 'filter_res',
          label: 'Filter Resonance',
          parameterLabel: 'Filter 1 Resonance',
          laneLabel: 'edge',
          currentValue: 35,
          candidateValue: 48,
          status: 'ready',
          statusLabel: 'CC-ready',
        },
        {
          key: 'reverb_send',
          label: 'Reverb Send',
          parameterLabel: 'Amp Reverb Send',
          laneLabel: 'space',
          currentValue: 28,
          candidateValue: 57,
          status: 'review',
          statusLabel: 'Review',
        },
      ],
    },
    {
      key: 'performance',
      sectionLabel: 'IV',
      label: 'Performance',
      summary: 'Macro-facing genes that describe how the patch should be played.',
      sendPolicy: 'Performance genes are design-preview annotations until mapped upstream.',
      genes: [
        {
          key: 'macro_pressure',
          label: 'Macro Pressure',
          parameterLabel: 'Performance Macro A',
          laneLabel: 'pressure',
          currentValue: 50,
          candidateValue: 73,
          status: 'deferred',
          statusLabel: 'Deferred',
        },
        {
          key: 'space_macro',
          label: 'Space Macro',
          parameterLabel: 'Performance Macro B',
          laneLabel: 'space',
          currentValue: 42,
          candidateValue: 61,
          status: 'deferred',
          statusLabel: 'Deferred',
        },
      ],
    },
  ],
};
