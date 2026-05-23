/**
 * PadCard — one card per pad. Renders the machine name, a LockButton, and a 4-knob row.
 *
 * Per spec the knob set is taken from the pad's `params` map. We render up to 4 stable knobs
 * (tun, dec, lev, flt) when present; any other params present in the snapshot are skipped from
 * the v10 layout but visible in tooltips on hover (future). The ghost overlay uses the
 * candidate's `proposed_params` for this pad if a preview candidate is available.
 */

import type { MutationCandidate, PadState } from '../ws/protocol';

import { Knob } from './Knob';
import { LockButton } from './LockButton';
import { usePadLocks } from './usePadLocks';

export interface PadCardProps {
  pad: PadState;
  previewCandidate: MutationCandidate | null;
  previewOn: boolean;
}

const PRIMARY_KNOBS: ReadonlyArray<string> = ['tun', 'dec', 'lev', 'flt'];

function selectGhostParams(
  padId: number,
  candidate: MutationCandidate | null,
  previewOn: boolean,
): Record<string, number> | null {
  if (!previewOn) return null;
  if (candidate === null) return null;
  const delta = candidate.pad_deltas.find((d) => d.pad_id === padId);
  if (delta === undefined) return null;
  return delta.proposed_params;
}

export function PadCard({ pad, previewCandidate, previewOn }: PadCardProps): JSX.Element {
  const { isLocked, toggleLock } = usePadLocks();
  const locked = isLocked(pad.pad_id);
  const ghostParams = selectGhostParams(pad.pad_id, previewCandidate, previewOn);
  const className = locked ? 'pad-card locked' : 'pad-card';

  return (
    <div className={className} data-testid={`pad-card-${pad.pad_id}`}>
      <div className="pad-card-header">
        <div>
          <div className="pad-card-title">Pad {pad.pad_id}</div>
          <div className="pad-card-machine">{pad.machine}</div>
        </div>
        <LockButton locked={locked} padId={pad.pad_id} onToggle={() => toggleLock(pad.pad_id)} />
      </div>
      <div className="pad-card-knobs">
        {PRIMARY_KNOBS.map((knobKey) => {
          const value = pad.params[knobKey] ?? 0;
          const ghostValue = ghostParams === null ? null : ghostParams[knobKey] ?? null;
          return (
            <Knob
              key={knobKey}
              label={knobKey.toUpperCase()}
              value={value}
              ghostValue={ghostValue}
            />
          );
        })}
      </div>
    </div>
  );
}
