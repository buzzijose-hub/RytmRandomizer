import { useMemo, useState } from 'react';

import {
  DEFAULT_PATCH_GENOME_MODEL,
  countReadyGenes,
  getPatchGenomeFamily,
  type PatchGenomeFamily,
  type PatchGenomeFamilyKey,
  type PatchGenomeGene,
  type PatchGenomeModel,
} from './patchGenomeModel';

export interface PatchGenomePanelProps {
  model?: PatchGenomeModel;
  previewOn: boolean;
}

const FIRST_FAMILY: PatchGenomeFamilyKey = 'oscillator';
const MIDI_MAX = 127;

function clampValue(value: number): number {
  if (value < 0) return 0;
  if (value > MIDI_MAX) return MIDI_MAX;
  return value;
}

function variantCandidateValue(gene: PatchGenomeGene, variantIndex: number): number {
  return clampValue(gene.candidateValue + variantIndex * 3);
}

function deltaPercent(gene: PatchGenomeGene, variantIndex: number): number {
  const delta = Math.abs(variantCandidateValue(gene, variantIndex) - gene.currentValue);
  return Math.round((delta / MIDI_MAX) * 100);
}

function geneStatusClass(gene: PatchGenomeGene, locked: boolean): string {
  if (locked) return 'locked';
  return gene.status;
}

export function PatchGenomePanel({
  model = DEFAULT_PATCH_GENOME_MODEL,
  previewOn,
}: PatchGenomePanelProps): JSX.Element {
  const [selectedFamilyKey, setSelectedFamilyKey] =
    useState<PatchGenomeFamilyKey>(FIRST_FAMILY);
  const [lockedGeneKeys, setLockedGeneKeys] = useState<ReadonlySet<string>>(() => new Set());
  const [variantIndex, setVariantIndex] = useState<number>(0);
  const selectedFamily = useMemo<PatchGenomeFamily>(() => {
    return (
      getPatchGenomeFamily(model, selectedFamilyKey) ??
      model.families[0] ??
      DEFAULT_PATCH_GENOME_MODEL.families[0]!
    );
  }, [model, selectedFamilyKey]);

  const toggleGeneLock = (geneKey: string): void => {
    setLockedGeneKeys((previous) => {
      const next = new Set(previous);
      if (next.has(geneKey)) {
        next.delete(geneKey);
      } else {
        next.add(geneKey);
      }
      return next;
    });
  };

  return (
    <section
      aria-labelledby="patch-genome-title"
      className="cockpit-panel patch-genome-panel"
      data-testid="patch-genome-panel"
    >
      <header className="patch-genome-header">
        <div>
          <h2 id="patch-genome-title">Patch Genome</h2>
          <p className="panel-meta">{model.targetDeviceLabel}</p>
        </div>
        <span className="patch-genome-state">
          {previewOn ? 'Preview overlay active' : 'Dry-run preview'}
        </span>
      </header>

      <div className="patch-genome-meta-grid" aria-label="Patch genome source metadata">
        <span>{model.sourceLabel}</span>
        <span>{model.seedLabel}</span>
        <span data-testid="patch-genome-variant">Variant {variantIndex + 1}</span>
        <span>{model.designStatus}</span>
      </div>

      <div className="patch-genome-family-grid" role="tablist" aria-label="Patch gene families">
        {model.families.map((family) => (
          <button
            key={family.key}
            aria-selected={family.key === selectedFamily.key}
            className={family.key === selectedFamily.key ? 'active' : undefined}
            data-testid={`patch-genome-family-${family.key}`}
            onClick={() => setSelectedFamilyKey(family.key)}
            role="tab"
            type="button"
          >
            <span>{family.sectionLabel}</span>
            <strong>{family.label}</strong>
            <small>
              {countReadyGenes(family.genes)}/{family.genes.length} ready
            </small>
          </button>
        ))}
      </div>

      <article
        className="patch-genome-family-detail"
        data-testid="patch-genome-selected-family"
      >
        <header>
          <div>
            <h3>{selectedFamily.label}</h3>
            <p>{selectedFamily.summary}</p>
          </div>
          <span>{selectedFamily.sendPolicy}</span>
        </header>

        <div className="patch-genome-gene-list">
          {selectedFamily.genes.map((gene) => {
            const locked = lockedGeneKeys.has(gene.key);
            const candidate = variantCandidateValue(gene, variantIndex);
            const statusClass = geneStatusClass(gene, locked);
            const lockLabel = `${locked ? 'Unlock' : 'Lock'} ${gene.label.toLowerCase()}`;

            return (
              <div
                key={gene.key}
                className={`patch-genome-gene ${statusClass}`}
                data-testid={`patch-genome-gene-${gene.key}`}
              >
                <div className="patch-genome-gene-main">
                  <strong>{gene.label}</strong>
                  <span>{gene.parameterLabel}</span>
                  <small>{gene.laneLabel}</small>
                </div>
                <div className="patch-genome-delta" aria-hidden="true">
                  <span style={{ width: `${deltaPercent(gene, variantIndex)}%` }} />
                </div>
                <div className="patch-genome-values">
                  <span>{gene.currentValue}</span>
                  <strong>{candidate}</strong>
                </div>
                <div className="patch-genome-gene-status">
                  <span>{locked ? 'Locked locally' : gene.statusLabel}</span>
                  <button type="button" aria-label={lockLabel} onClick={() => toggleGeneLock(gene.key)}>
                    {locked ? 'Unlock' : 'Lock'}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </article>

      <div className="patch-genome-traits" aria-label="Patch genome trait meters">
        {model.traits.map((trait) => (
          <div key={trait.key} className="patch-genome-trait">
            <span>{trait.label}</span>
            <meter min={0} max={100} value={trait.valuePercent}>
              {trait.valuePercent}%
            </meter>
            <strong>{trait.valuePercent}%</strong>
          </div>
        ))}
      </div>

      <div className="patch-genome-actions">
        <button type="button" onClick={() => setVariantIndex((current) => (current + 1) % 4)}>
          Grow variant
        </button>
        <button type="button" onClick={() => setVariantIndex(0)}>
          Reset seed
        </button>
      </div>
    </section>
  );
}
