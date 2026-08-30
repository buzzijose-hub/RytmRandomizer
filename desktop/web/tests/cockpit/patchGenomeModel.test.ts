import { describe, expect, it } from 'vitest';

import {
  countReadyGenes,
  genesForFamily,
  getPatchGenomeFamily,
  patchGeneKey,
  patchGeneStatus,
  PATCH_GENOME_FAMILIES,
  transportLabel,
} from '../../src/cockpit/patchGenomeModel';

import { patchGenome } from './_fixtures';

const candidate = patchGenome.genome.candidates[1]!;

describe('patchGenomeModel', () => {
  it('maps the three compiler-owned families without inventing performance genes', () => {
    expect(PATCH_GENOME_FAMILIES.map((family) => family.label)).toEqual([
      'Oscillators',
      'Envelope / LFO',
      'Filter / FX',
    ]);
    expect(getPatchGenomeFamily('filter_fx').backendName).toBe('Filter and effects');
    expect(getPatchGenomeFamily('unknown' as never).key).toBe('oscillator');
  });

  it('filters a real candidate by the backend family name', () => {
    const genes = genesForFamily(candidate, 'filter_fx');
    expect(genes).toHaveLength(1);
    expect(genes[0]?.value.parameter).toBe('FILT1 FRQ');
  });

  it('derives stable keys and transport readiness from real gene metadata', () => {
    const oscillator = genesForFamily(candidate, 'oscillator')[0]!;
    const filter = genesForFamily(candidate, 'filter_fx')[0]!;

    expect(patchGeneKey(oscillator)).toBe('2-osc1-a-osc1-tun');
    expect(patchGeneStatus(oscillator.value.transport_status)).toBe('ready');
    expect(patchGeneStatus(filter.value.transport_status)).toBe('review');
    expect(countReadyGenes(candidate.genes)).toBe(2);
    expect(transportLabel(filter.value.transport_status)).toBe('Screen review');
    expect(transportLabel('screen-only')).toBe('Screen review');
    expect(transportLabel('nrpn-ready')).toBe('NRPN ready');
  });
});
