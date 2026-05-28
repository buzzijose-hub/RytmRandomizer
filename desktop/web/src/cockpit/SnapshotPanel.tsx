/**
 * SnapshotPanel — left panel: pad grid + history strip.
 *
 * Subscribes to the snapshot, preview candidate, and the local "previewOn" flag (lifted
 * to <Cockpit /> so the ActionBar toggle and the snapshot ghost rendering stay in sync).
 */

import { useCockpitStore } from '../state';

import { AnalogFourTrackCard } from './AnalogFourTrackCard';
import { ANALOG_FOUR_DEVICE_ID, ANALOG_FOUR_TRACKS, type CockpitDeviceId } from './devices';
import { HistoryStrip } from './HistoryStrip';
import { PadCard } from './PadCard';

export interface SnapshotPanelProps {
  activeDeviceId: CockpitDeviceId;
  previewOn: boolean;
}

export function SnapshotPanel({ activeDeviceId, previewOn }: SnapshotPanelProps): JSX.Element {
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

  if (activeDeviceId === ANALOG_FOUR_DEVICE_ID) {
    return (
      <section
        className="cockpit-panel"
        data-active-device={ANALOG_FOUR_DEVICE_ID}
        data-testid="snapshot-panel"
      >
        <header>
          <h2>Analog Four MKII</h2>
          <p className="panel-meta">
            4 synth tracks - OSC / filters / amp / envelopes / LFO / FX
            {snapshot.bpm === null ? '' : ` - ${snapshot.bpm} BPM`}
            {previewOn ? ' - PREVIEW ON' : ''}
          </p>
          <p className="snapshot-readiness">4 tracks ready for dry-run review</p>
          <p className="a4-source-note">
            Manual-backed mutation zones are shown from the current A4 capability map. Hardware
            remains locked; deferred zones stay mock-only until separately validated.
          </p>
        </header>
        <div className="a4-track-grid">
          {ANALOG_FOUR_TRACKS.map((track) => (
            <AnalogFourTrackCard key={track.track} track={track} previewOn={previewOn} />
          ))}
        </div>
        <div>
          <h2>Snapshot history</h2>
          <HistoryStrip />
        </div>
      </section>
    );
  }

  return (
    <section
      className="cockpit-panel"
      data-active-device={snapshot.device}
      data-testid="snapshot-panel"
    >
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
