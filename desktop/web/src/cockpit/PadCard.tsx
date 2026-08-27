/**
 * PadCard - one card per Rytm pad.
 *
 * The cockpit should expose the same broad control groups an operator sees in
 * Overbridge/manual workflows: synth, sample, filter envelope, amp envelope, and
 * LFO. Individual machine engines may not map every parameter yet, so absent
 * values render as "not mapped" instead of hiding the control surface shape.
 */

import type { MutationCandidate, PadState } from '../ws/protocol';

import { Knob } from './Knob';
import { LockButton } from './LockButton';
import { RYTM_PARAMETER_GROUPS, type ParameterDefinition } from './parameterGroups';
import { usePadLocks } from './usePadLocks';
import { useMutationTargets } from './useMutationTargets';
import { RYTM_DEVICE_ID } from './devices';

export interface PadCardProps {
  pad: PadState;
  previewCandidate: MutationCandidate | null;
  previewOn: boolean;
}

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
  const { hasExplicitTargets, isTargeted, toggleTarget } =
    useMutationTargets(RYTM_DEVICE_ID);
  const locked = isLocked(pad.pad_id);
  const targeted = isTargeted(pad.pad_id);
  // A lock is authoritative protection, so a pre-lock candidate must not keep
  // drawing proposed values while the replacement whole-state event arrives.
  const ghostParams = locked
    ? null
    : selectGhostParams(pad.pad_id, previewCandidate, previewOn);
  const className = [
    'pad-card',
    hasExplicitTargets ? (targeted ? 'targeted' : 'inactive') : '',
    locked ? 'locked' : '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div
      className={className}
      data-target-state={targeted ? 'targeted' : 'inactive'}
      data-testid={`pad-card-${pad.pad_id}`}
    >
      <div className="pad-card-header">
        <div>
          <div className="pad-card-title">Pad {pad.pad_id}</div>
          <div className="pad-card-machine">{pad.machine}</div>
        </div>
        <div className="mutation-scope-actions">
          <button
            aria-label={`${targeted && hasExplicitTargets ? 'Remove' : 'Target'} pad ${pad.pad_id}`}
            aria-pressed={targeted && hasExplicitTargets}
            className="target-button"
            onClick={() => toggleTarget(pad.pad_id)}
            type="button"
          >
            {targeted && hasExplicitTargets ? 'Targeted' : 'Target'}
          </button>
          <LockButton locked={locked} padId={pad.pad_id} onToggle={() => toggleLock(pad.pad_id)} />
        </div>
      </div>
      <div className="pad-card-parameter-groups">
        {RYTM_PARAMETER_GROUPS.map((group) => (
          <section className="pad-parameter-group" key={group.title}>
            <h3>{group.title}</h3>
            <div className="pad-card-knobs">
              {group.params.map((definition) => (
                <ParameterSlot
                  definition={definition}
                  ghostParams={ghostParams}
                  key={definition.key}
                  padParams={pad.params}
                />
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}

function ParameterSlot({
  definition,
  ghostParams,
  padParams,
}: {
  definition: ParameterDefinition;
  ghostParams: Record<string, number> | null;
  padParams: Record<string, number>;
}): JSX.Element {
  const value = padParams[definition.key];
  const ghostValue = ghostParams === null ? null : ghostParams[definition.key] ?? null;
  if (value === undefined) {
    return (
      <div className="parameter-slot missing">
        <span className="parameter-label">{definition.label}</span>
        <span className="parameter-missing">not mapped</span>
      </div>
    );
  }
  return (
    <div className="parameter-slot">
      <span className="parameter-label">{definition.label}</span>
      <Knob label={definition.code} value={value} ghostValue={ghostValue} />
    </div>
  );
}
