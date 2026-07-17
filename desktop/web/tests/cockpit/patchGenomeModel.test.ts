import { describe, expect, it } from 'vitest';

import {
  DEFAULT_PATCH_GENOME_MODEL,
  countReadyGenes,
  getPatchGenomeFamily,
} from '../../src/cockpit/patchGenomeModel';

describe('patchGenomeModel', () => {
  it('ships four named gene families for the cockpit design surface', () => {
    expect(DEFAULT_PATCH_GENOME_MODEL.families.map((family) => family.label)).toEqual([
      'Oscillators',
      'Envelope / LFO',
      'Filter / FX',
      'Performance',
    ]);
  });

  it('resolves a selected family by key', () => {
    expect(getPatchGenomeFamily(DEFAULT_PATCH_GENOME_MODEL, 'filter_fx')?.label).toBe(
      'Filter / FX',
    );
  });

  it('counts only ready genes as dry-run-ready', () => {
    const family = getPatchGenomeFamily(DEFAULT_PATCH_GENOME_MODEL, 'filter_fx');
    expect(family).toBeDefined();
    if (family === undefined) throw new Error('missing filter_fx family');
    expect(countReadyGenes(family.genes)).toBe(2);
  });
});
