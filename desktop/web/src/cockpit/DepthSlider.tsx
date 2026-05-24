/**
 * DepthSlider — DJ-style horizontal mutation amount slider.
 *
 * Range: 0.10..0.90 in 0.01 steps (per spec § "MutationCandidate.depth").
 * On change → emits `set_depth { depth }` and re-renders the value chip.
 *
 * Local state mirrors the engine's last-applied depth; if the engine acks with a different
 * value (e.g. clamped) we'll see it via the next `mutation_previewed` event. For v10 we
 * don't surface that round-trip — the slider trusts the operator.
 */

import { useState, type ChangeEvent } from 'react';

import { useCockpitClient } from './context';

const MIN = 0.1;
const MAX = 0.9;
const STEP = 0.01;
const DEFAULT_DEPTH = 0.45;

export interface DepthSliderProps {
  initial?: number;
}

export function DepthSlider({ initial = DEFAULT_DEPTH }: DepthSliderProps): JSX.Element {
  const [depth, setDepth] = useState<number>(initial);
  const [active, setActive] = useState<boolean>(false);
  const client = useCockpitClient();

  const handleChange = (ev: ChangeEvent<HTMLInputElement>): void => {
    const next = Number.parseFloat(ev.target.value);
    setDepth(next);
    void client.send({ type: 'set_depth', depth: next });
  };

  return (
    <div className="depth-slider" data-testid="depth-slider">
      <div className="depth-slider-header">
        <span>Mutation amount</span>
        <span className="depth-slider-value" data-testid="depth-slider-value">
          {Math.round(depth * 100)}%
        </span>
      </div>
      <div className="depth-slider-track-wrap">
        <input
          type="range"
          min={MIN}
          max={MAX}
          step={STEP}
          value={depth}
          aria-label="Mutation amount"
          className={active ? 'depth-slider-range active' : 'depth-slider-range'}
          onChange={handleChange}
          onPointerDown={() => setActive(true)}
          onPointerUp={() => setActive(false)}
          onBlur={() => setActive(false)}
        />
      </div>
      <div className="depth-slider-ticks">
        <span>10</span>
        <span>30</span>
        <span>50</span>
        <span>70</span>
        <span>90</span>
      </div>
    </div>
  );
}
