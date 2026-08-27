import {
  ANALOG_FOUR_MUTATION_ZONES,
  ANALOG_FOUR_OXI_ACTIONS_BY_ROLE,
  type AnalogFourOxiMacroAction,
  type AnalogFourTrackProfile,
  type AnalogFourZoneState,
} from './devices';
import { LockButton } from './LockButton';
import { usePadLocks } from './usePadLocks';
import { useMutationTargets } from './useMutationTargets';
import { ANALOG_FOUR_DEVICE_ID } from './devices';

export interface AnalogFourTrackCardProps {
  track: AnalogFourTrackProfile;
  previewOn: boolean;
}

export function AnalogFourTrackCard({
  track,
  previewOn,
}: AnalogFourTrackCardProps): JSX.Element {
  const { isLocked, toggleLock } = usePadLocks(ANALOG_FOUR_DEVICE_ID);
  const { hasExplicitTargets, isTargeted, toggleTarget } =
    useMutationTargets(ANALOG_FOUR_DEVICE_ID);
  const locked = isLocked(track.track);
  const targeted = isTargeted(track.track);
  const className = [
    'a4-track-card',
    hasExplicitTargets ? (targeted ? 'targeted' : 'inactive') : '',
    locked ? 'locked' : '',
  ]
    .filter(Boolean)
    .join(' ');
  const oxiActions = ANALOG_FOUR_OXI_ACTIONS_BY_ROLE[track.roleKey];

  return (
    <article
      className={className}
      data-testid={`a4-track-card-${track.track}`}
      data-role-key={track.roleKey}
      data-target-state={targeted ? 'targeted' : 'inactive'}
    >
      <header className="a4-track-header">
        <div>
          <div className="pad-card-title">
            {track.trackLabel} - Track {track.track}
          </div>
          <div className="pad-card-machine">{track.roleLabel}</div>
        </div>
        <div className="mutation-scope-actions">
          <button
            aria-label={`${targeted && hasExplicitTargets ? 'Remove' : 'Target'} track ${track.track}`}
            aria-pressed={targeted && hasExplicitTargets}
            className="target-button"
            onClick={() => toggleTarget(track.track)}
            type="button"
          >
            {targeted && hasExplicitTargets ? 'Targeted' : 'Target'}
          </button>
          <LockButton
            itemLabel="track"
            locked={locked}
            padId={track.track}
            onToggle={() => toggleLock(track.track)}
          />
        </div>
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
      <div
        className="a4-oxi-macro-strip"
        data-testid={`a4-track-${track.track}-oxi-macros`}
        aria-label={`${track.trackLabel} OXI macro actions`}
      >
        <h3>OXI macros</h3>
        <div className="a4-oxi-macro-grid">
          {oxiActions.map((action) => (
            <AnalogFourOxiMacroRow
              key={action.key}
              action={action}
              previewOn={previewOn}
              testId={`a4-track-${track.track}-oxi-macro-${action.key}`}
            />
          ))}
        </div>
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

function AnalogFourOxiMacroRow({
  action,
  previewOn,
  testId,
}: {
  action: AnalogFourOxiMacroAction;
  previewOn: boolean;
  testId: string;
}): JSX.Element {
  const statusLabel =
    action.status === 'cc-ready' ? (previewOn ? 'Preview row' : 'Dry-run row') : 'Deferred';

  return (
    <div className={`a4-oxi-macro ${action.status}`} data-testid={testId}>
      <strong>{action.label}</strong>
      <span>{action.targetParameter}</span>
      <small>{action.scope}</small>
      <em>{statusLabel}</em>
    </div>
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
