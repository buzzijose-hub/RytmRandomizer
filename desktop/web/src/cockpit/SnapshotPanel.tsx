/**
 * SnapshotPanel — left panel: pad grid + history strip.
 *
 * Subscribes to the snapshot, preview candidate, and the local "previewOn" flag (lifted
 * to <Cockpit /> so the ActionBar toggle and the snapshot ghost rendering stay in sync).
 */

import { useCockpitStore } from '../state';

import { HistoryStrip } from './HistoryStrip';
import { PadCard } from './PadCard';

export interface SnapshotPanelProps {
  previewOn: boolean;
}

export function SnapshotPanel({ previewOn }: SnapshotPanelProps): JSX.Element {
  const snapshot = useCockpitStore((s) => s.snapshot);
  const previewCandidate = useCockpitStore((s) => s.previewCandidate);

  if (snapshot === null) {
    return (
      <section className="cockpit-panel" data-testid="snapshot-panel">
        <h2>Snapshot</h2>
        <p className="panel-meta">Waiting for snapshot…</p>
      </section>
    );
  }

  return (
    <section className="cockpit-panel" data-testid="snapshot-panel">
      <header>
        <h2>Snapshot</h2>
        <p className="panel-meta">
          {snapshot.device}
          {snapshot.bpm === null ? '' : ` · ${snapshot.bpm} BPM`}
          {snapshot.scene_slot === null ? '' : ` · scene ${snapshot.scene_slot}`}
          {previewOn ? ' · PREVIEW ON' : ''}
        </p>
        <p className="snapshot-readiness">{snapshot.pads.length} pads ready for dry-run review</p>
      </header>
      <div className="pad-grid">
        {snapshot.pads.map((pad) => (
          <PadCard
            key={pad.pad_id}
            pad={pad}
            previewCandidate={previewCandidate}
            previewOn={previewOn}
          />
        ))}
      </div>
      <div>
        <h2>Snapshot history</h2>
        <HistoryStrip />
      </div>
    </section>
  );
}
