import {
  ANALOG_FOUR_MUTATION_ZONES,
  type AnalogFourTrackProfile,
  type AnalogFourZoneState,
} from './devices';
import { LockButton } from './LockButton';
import { usePadLocks } from './usePadLocks';

export interface AnalogFourTrackCardProps {
  track: AnalogFourTrackProfile;
  previewOn: boolean;
}

export function AnalogFourTrackCard({
  track,
  previewOn,
}: AnalogFourTrackCardProps): JSX.Element {
  const { isLocked, toggleLock } = usePadLocks();
  const locked = isLocked(track.track);
  const className = locked ? 'a4-track-card locked' : 'a4-track-card';

  return (
    <article
      className={className}
      data-testid={`a4-track-card-${track.track}`}
      data-role-key={track.roleKey}
    >
      <header className="a4-track-header">
        <div>
          <div className="pad-card-title">
            {track.trackLabel} - Track {track.track}
          </div>
          <div className="pad-card-machine">{track.roleLabel}</div>
        </div>
        <LockButton
          locked={locked}
          padId={track.track}
          onToggle={() => toggleLock(track.track)}
        />
      </header>
      <div className="a4-depth-row">
        <span id={`a4-track-${track.track}-safe-depth-label`}>Safe Depth</span>
        <meter
          min={0}
          max={100}
          value={track.safeDepth}
          aria-labelledby={`a4-track-${track.track}-safe-depth-label`}
          aria-valuetext={`${track.safeDepth} percent safe mutation depth for ${track.trackLabel}`}
        >
          {track.safeDepth}%
        </meter>
        <strong>{track.safeDepth}%</strong>
      </div>
      <div className="a4-zone-grid" aria-label={`${track.trackLabel} mutation zones`}>
        {ANALOG_FOUR_MUTATION_ZONES.map((zone) => (
          <AnalogFourZonePill
            key={zone.key}
            previewOn={previewOn}
            status={zone.status}
            testId={`a4-track-${track.track}-zone-${zone.key}`}
            title={zone.label}
            subtitle={zone.target}
            detail={zone.manualSection}
          />
        ))}
      </div>
    </article>
  );
}

function AnalogFourZonePill({
  previewOn,
  status,
  testId,
  title,
  subtitle,
  detail,
}: {
  previewOn: boolean;
  status: AnalogFourZoneState;
  testId: string;
  title: string;
  subtitle: string;
  detail: string;
}): JSX.Element {
  const statusLabel =
    status === 'cc-ready' ? (previewOn ? 'Preview row' : 'Dry-run row') : 'Deferred';

  return (
    <div className={`a4-zone-pill ${status}`} data-testid={testId}>
      <strong>{title}</strong>
      <span>{subtitle}</span>
      <small>{detail}</small>
      <em>{statusLabel}</em>
    </div>
  );
}
