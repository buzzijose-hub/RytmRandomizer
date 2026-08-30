import type {
  AnalogFourPatchCandidate,
  AnalogFourPatchGene,
  AnalogFourPatchTransportStatus,
} from '../ws/protocol';

export type PatchGenomeFamilyKey = 'oscillator' | 'envelope_lfo' | 'filter_fx';
export type PatchGenomeGeneStatus = 'ready' | 'review';

export interface PatchGenomeFamilyDefinition {
  key: PatchGenomeFamilyKey;
  backendName: string;
  sectionLabel: string;
  label: string;
  summary: string;
}

export const PATCH_GENOME_FAMILIES: ReadonlyArray<PatchGenomeFamilyDefinition> = [
  {
    key: 'oscillator',
    backendName: 'Oscillators',
    sectionLabel: 'I',
    label: 'Oscillators',
    summary: 'Core tone, pitch relationship, oscillator balance, and noise weight.',
  },
  {
    key: 'envelope_lfo',
    backendName: 'Envelope and LFO',
    sectionLabel: 'II',
    label: 'Envelope / LFO',
    summary: 'Contour and rhythmic motion genes that make a patch breathe.',
  },
  {
    key: 'filter_fx',
    backendName: 'Filter and effects',
    sectionLabel: 'III',
    label: 'Filter / FX',
    summary: 'Brightness, resonance, drive, and space genes for the patch surface.',
  },
];

export function getPatchGenomeFamily(
  key: PatchGenomeFamilyKey,
): PatchGenomeFamilyDefinition {
  return PATCH_GENOME_FAMILIES.find((family) => family.key === key) ?? PATCH_GENOME_FAMILIES[0]!;
}

export function genesForFamily(
  candidate: AnalogFourPatchCandidate,
  familyKey: PatchGenomeFamilyKey,
): AnalogFourPatchGene[] {
  const family = getPatchGenomeFamily(familyKey);
  return candidate.genes.filter((gene) => gene.family === family.backendName);
}

export function patchGeneKey(gene: AnalogFourPatchGene): string {
  return [gene.track, gene.value.section, gene.value.encoder, gene.value.parameter]
    .join('-')
    .replace(/[^A-Za-z0-9_-]+/g, '-')
    .toLowerCase();
}

export function patchGeneStatus(
  transportStatus: AnalogFourPatchTransportStatus,
): PatchGenomeGeneStatus {
  return transportStatus === 'cc-ready' || transportStatus === 'nrpn-ready'
    ? 'ready'
    : 'review';
}

export function countReadyGenes(genes: ReadonlyArray<AnalogFourPatchGene>): number {
  return genes.filter((gene) => patchGeneStatus(gene.value.transport_status) === 'ready').length;
}

export function transportLabel(status: AnalogFourPatchTransportStatus): string {
  switch (status) {
    case 'cc-ready':
      return 'CC ready';
    case 'nrpn-ready':
      return 'NRPN ready';
    case 'screen-only':
    case 'screen-only-nrpn':
      return 'Screen review';
  }
}
