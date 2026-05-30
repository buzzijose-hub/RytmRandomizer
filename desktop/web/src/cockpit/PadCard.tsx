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
