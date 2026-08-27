import { useEffect, useMemo, useState } from 'react';

import { useCockpitStore } from '../state';

import { useCockpitClient } from './context';
import { ANALOG_FOUR_DEVICE_ID } from './devices';
import {
  countReadyGenes,
  genesForFamily,
  getPatchGenomeFamily,
  patchGeneKey,
  patchGeneStatus,
  PATCH_GENOME_FAMILIES,
  transportLabel,
  type PatchGenomeFamilyKey,
} from './patchGenomeModel';
import { useMutationTargets } from './useMutationTargets';
import { usePadLocks } from './usePadLocks';

export interface PatchGenomePanelProps {
  previewOn: boolean;
}

const FIRST_FAMILY: PatchGenomeFamilyKey = 'oscillator';
const DEFAULT_DESCRIPTION = 'Tight warehouse pressure';
const DEFAULT_TRACK = 2;

export function PatchGenomePanel({ previewOn }: PatchGenomePanelProps): JSX.Element {
  const client = useCockpitClient();
  const patchGenome = useCockpitStore((state) => state.patchGenome);
  const patchGenomeStale = useCockpitStore((state) => state.patchGenomeStale);
  const setPatchGenome = useCockpitStore((state) => state.setPatchGenome);
  const appendOperatorLog = useCockpitStore((state) => state.appendOperatorLog);
  const mutationTargets = useMutationTargets(ANALOG_FOUR_DEVICE_ID);
  const trackLocks = usePadLocks(ANALOG_FOUR_DEVICE_ID);
  const [description, setDescription] = useState(
    () => patchGenome?.source.value ?? DEFAULT_DESCRIPTION,
  );
  const [track, setTrack] = useState(() => patchGenome?.selected_track ?? DEFAULT_TRACK);
  const [selectedFamilyKey, setSelectedFamilyKey] =
    useState<PatchGenomeFamilyKey>(FIRST_FAMILY);
  const [selectedCandidateIndex, setSelectedCandidateIndex] = useState(() =>
    Math.max(0, (patchGenome?.selected_candidate ?? 2) - 1),
  );
  const [lockedGeneKeys, setLockedGeneKeys] = useState<ReadonlySet<string>>(() => new Set());
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  useEffect(() => {
    if (patchGenome === null) return;
    setDescription(patchGenome.source.value);
    setTrack(patchGenome.selected_track);
    setSelectedCandidateIndex(Math.max(0, patchGenome.selected_candidate - 1));
  }, [patchGenome]);

  const trackSendable = mutationTargets.isTargeted(track) && !trackLocks.isLocked(track);

  const selectedCandidate = patchGenome?.genome.candidates[selectedCandidateIndex];
  const selectedFamily = getPatchGenomeFamily(selectedFamilyKey);
  const selectedGenes = useMemo(
    () =>
      selectedCandidate === undefined
        ? []
        : genesForFamily(selectedCandidate, selectedFamilyKey),
    [selectedCandidate, selectedFamilyKey],
  );

  const toggleGeneLock = (geneKey: string): void => {
    setLockedGeneKeys((previous) => {
      const next = new Set(previous);
      if (next.has(geneKey)) next.delete(geneKey);
      else next.add(geneKey);
      return next;
    });
  };

  const handleAnalyze = async (): Promise<void> => {
    const normalized = description.trim();
    if (normalized === '') {
      setAnalysisError('Describe the patch before analyzing.');
      return;
    }
    setAnalyzing(true);
    setAnalysisError(null);
    try {
      const ack = await client.send({
        type: 'analyze_patch_genome',
        description: normalized,
        track,
      });
      if (!ack.ok) {
        throw new Error(ack.message ?? ack.error ?? 'Compiler request rejected');
      }
      if (ack.patch_genome !== undefined) setPatchGenome(ack.patch_genome);
      appendOperatorLog({
        level: 'success',
        message: `A4 patch genome compiled for track ${track}`,
      });
    } catch (error) {
      const detail = error instanceof Error ? error.message : String(error);
      setAnalysisError(detail);
      appendOperatorLog({ level: 'error', message: `A4 compiler failed: ${detail}` });
    } finally {
      setAnalyzing(false);
    }
  };

  const growCandidate =
    patchGenome === null
      ? undefined
      : (): void => {
          const count = patchGenome.genome.candidates.length;
          setSelectedCandidateIndex((current) => (current + 1) % count);
        };

  const resetCandidate =
    patchGenome === null
      ? undefined
      : (): void => {
          setSelectedCandidateIndex(Math.max(0, patchGenome.selected_candidate - 1));
          setLockedGeneKeys(new Set());
        };

  return (
    <section
      aria-labelledby="patch-genome-title"
      className="cockpit-panel patch-genome-panel"
      data-testid="patch-genome-panel"
    >
      <header className="patch-genome-header">
        <div>
          <p className="panel-kicker">Passive compiler</p>
          <h2 id="patch-genome-title">A4 Patch Genome</h2>
          <p className="panel-meta">Analog Four MKII · four real candidates · no MIDI I/O</p>
        </div>
        <span className="patch-genome-state">
          {previewOn ? 'Preview overlay active' : 'Dry-run preview'}
        </span>
      </header>

      {patchGenomeStale && patchGenome !== null ? (
        <p className="patch-genome-stale" data-testid="patch-genome-stale" role="status">
          Stale — mutation targets or locks changed. Analyze again before treating this genome as
          current.
        </p>
      ) : null}

      <form
        className="patch-genome-source"
        onSubmit={(event) => {
          event.preventDefault();
          void handleAnalyze();
        }}
      >
        <label htmlFor="patch-genome-description">Source description</label>
        <div className="a4-mutation-targets" aria-label="Analog Four mutation targets">
          <div className="mutation-scope-summary">
            <span>
              {mutationTargets.hasExplicitTargets
                ? `${mutationTargets.targets.size} targeted tracks`
                : 'All tracks in scope by default'}
            </span>
            <button
              disabled={!mutationTargets.hasExplicitTargets}
              onClick={mutationTargets.clearTargets}
              type="button"
            >
              Clear targets
            </button>
          </div>
          <div className="a4-target-grid">
            {[1, 2, 3, 4].map((trackNumber) => {
              const targeted = mutationTargets.isTargeted(trackNumber);
              const locked = trackLocks.isLocked(trackNumber);
              const targetClass = mutationTargets.hasExplicitTargets
                ? targeted
                  ? 'targeted'
                  : 'inactive'
                : '';
              return (
                <div
                  className={`a4-target-control ${targetClass} ${locked ? 'locked' : ''}`.trim()}
                  data-target-state={targeted ? 'targeted' : 'inactive'}
                  data-testid={`a4-target-control-${trackNumber}`}
                  key={trackNumber}
                >
                  <button
                    aria-label={`${targeted && mutationTargets.hasExplicitTargets ? 'Remove' : 'Target'} track ${trackNumber}`}
                    aria-pressed={targeted && mutationTargets.hasExplicitTargets}
                    onClick={() => mutationTargets.toggleTarget(trackNumber)}
                    type="button"
                  >
                    T{trackNumber}
                  </button>
                  <button
                    aria-label={`${locked ? 'Unlock' : 'Lock'} track ${trackNumber}`}
                    aria-pressed={locked}
                    onClick={() => trackLocks.toggleLock(trackNumber)}
                    type="button"
                  >
                    {locked ? 'Locked' : 'Lock'}
                  </button>
                </div>
              );
            })}
          </div>
        </div>
        <div className="patch-genome-source-row">
          <label className="sr-only" htmlFor="patch-genome-description">
            Patch description
          </label>
          <input
            id="patch-genome-description"
            maxLength={240}
            onChange={(event) => setDescription(event.target.value)}
            value={description}
          />
          <label className="patch-genome-track-label" htmlFor="patch-genome-track">
            Track
          </label>
          <select
            id="patch-genome-track"
            onChange={(event) => setTrack(Number(event.target.value))}
            value={track}
          >
            {[1, 2, 3, 4].map((trackNumber) => (
              <option key={trackNumber} value={trackNumber}>
                {trackNumber}
              </option>
            ))}
          </select>
          <button disabled={analyzing || !trackSendable} type="submit">
            {analyzing ? 'Analyzing…' : 'Analyze source'}
          </button>
        </div>
        {analysisError === null ? null : (
          <p className="patch-genome-error" role="alert">
            {analysisError}
          </p>
        )}
        {trackSendable ? null : (
          <p className="patch-genome-target-note" role="status">
            Track {track} is inactive or locked. Select a sendable target before compiling.
          </p>
        )}
      </form>

      {patchGenome === null || selectedCandidate === undefined ? (
        <div className="patch-genome-empty" data-testid="patch-genome-empty" role="status">
          Waiting for the passive sidecar compiler packet…
        </div>
      ) : (
        <>
          <div className="patch-genome-meta-grid" aria-label="Patch genome source metadata">
            <span>Source confidence · {patchGenome.genome.source_confidence}</span>
            <span>Track {patchGenome.selected_track} · {patchGenome.genome.mode}</span>
            <span data-testid="patch-genome-variant">
              Candidate {selectedCandidateIndex + 1} of {patchGenome.genome.candidate_count}
            </span>
            <span>Hash · {patchGenome.genome.source_hash.slice(0, 12)}</span>
          </div>

          <div className="patch-genome-candidates" role="tablist" aria-label="Patch candidates">
            {patchGenome.genome.candidates.map((candidate, index) => (
              <button
                key={candidate.column}
                aria-selected={index === selectedCandidateIndex}
                className={index === selectedCandidateIndex ? 'active' : undefined}
                data-testid={`patch-genome-candidate-${candidate.column}`}
                onClick={() => setSelectedCandidateIndex(index)}
                role="tab"
                type="button"
              >
                <span>V{candidate.column}</span>
                <strong>{candidate.label}</strong>
                <small>{candidate.role}</small>
                <meter min={0} max={100} value={candidate.closeness}>
                  {candidate.closeness}%
                </meter>
                <b>{candidate.closeness}% match</b>
              </button>
            ))}
          </div>

          <div className="patch-genome-family-grid" role="tablist" aria-label="Patch gene families">
            {PATCH_GENOME_FAMILIES.map((family) => {
              const genes = genesForFamily(selectedCandidate, family.key);
              return (
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
                  <small>{countReadyGenes(genes)}/{genes.length} transport ready</small>
                </button>
              );
            })}
          </div>

          <article className="patch-genome-family-detail" data-testid="patch-genome-selected-family">
            <header>
              <div>
                <h3>{selectedFamily.label}</h3>
                <p>{selectedFamily.summary}</p>
              </div>
              <span>{selectedGenes.length} mapped genes</span>
            </header>

            <div className="patch-genome-gene-list">
              {selectedGenes.map((gene) => {
                const geneKey = patchGeneKey(gene);
                const locked = lockedGeneKeys.has(geneKey);
                const status = patchGeneStatus(gene.value.transport_status);
                return (
                  <div
                    key={geneKey}
                    className={`patch-genome-gene ${locked ? 'locked' : status}`}
                    data-testid={`patch-genome-gene-${geneKey}`}
                  >
                    <div className="patch-genome-gene-main">
                      <strong>{gene.value.parameter}</strong>
                      <span>{gene.value.section} · encoder {gene.value.encoder}</span>
                      <small>{gene.rationale}</small>
                    </div>
                    <div className="patch-genome-value-block">
                      <span>Screen</span>
                      <strong>{gene.value.screen_value}</strong>
                    </div>
                    <div className="patch-genome-value-block">
                      <span>MIDI target</span>
                      <strong>{gene.value.midi_value ?? '—'}</strong>
                    </div>
                    <div className="patch-genome-gene-status">
                      <span>{locked ? 'Locked locally' : transportLabel(gene.value.transport_status)}</span>
                      <button
                        aria-label={`${locked ? 'Unlock' : 'Lock'} ${gene.value.parameter.toLowerCase()}`}
                        onClick={() => toggleGeneLock(geneKey)}
                        type="button"
                      >
                        {locked ? 'Unlock' : 'Lock'}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </article>

          <div className="patch-genome-traits" aria-label="Reference trait meters">
            {patchGenome.genome.traits.map((trait) => (
              <div key={trait.key} className="patch-genome-trait">
                <span>{trait.label}</span>
                <meter min={0} max={100} value={trait.intensity}>
                  {trait.intensity}%
                </meter>
                <strong>{trait.intensity}%</strong>
              </div>
            ))}
          </div>
        </>
      )}

      <div className="patch-genome-actions">
        <button disabled={patchGenome === null || patchGenomeStale} onClick={growCandidate} type="button">
          Grow candidate
        </button>
        <button disabled={patchGenome === null || patchGenomeStale} onClick={resetCandidate} type="button">
          Reset selection
        </button>
        <button className="patch-genome-hardware-lock" disabled type="button">
          Hardware send locked
        </button>
      </div>
      <p className="patch-genome-safety">
        Passive compile only. No MIDI port opened, no SysEx requested, and no patch written.
      </p>
    </section>
  );
}
