/**
 * Circular Knob with a rotation indicator + optional ghost overlay.
 *
 * Inputs:
 *   - `label`: display name (e.g. "TUN")
 *   - `value`: 0..127 current value (MIDI CC range)
 *   - `ghostValue`: optional 0..127 candidate value; renders a faint cyan indicator
 *
 * Purely presentational; no events emitted (per spec, knob positions render only).
 */

export interface KnobProps {
  label: string;
  value: number;
  ghostValue?: number | null;
}

const MIN_VALUE = 0;
const MAX_VALUE = 127;
const MIN_ANGLE = -135;
const MAX_ANGLE = 135;

function clamp(n: number, lo: number, hi: number): number {
  if (n < lo) return lo;
  if (n > hi) return hi;
  return n;
}

export function valueToAngle(value: number): number {
  const clamped = clamp(value, MIN_VALUE, MAX_VALUE);
  const ratio = (clamped - MIN_VALUE) / (MAX_VALUE - MIN_VALUE);
  return MIN_ANGLE + ratio * (MAX_ANGLE - MIN_ANGLE);
}

export function Knob({ label, value, ghostValue = null }: KnobProps): JSX.Element {
  const angle = valueToAngle(value);
  const showGhost = ghostValue !== null && ghostValue !== undefined && ghostValue !== value;
  // `ghostValue ?? value` here is for type-narrowing only; `showGhost === true` guarantees
  // ghostValue is a number. The fallback is just defensive against TypeScript losing
  // the narrowing inside the JSX expression.
  const ghostAngle = valueToAngle(ghostValue ?? value);
  return (
    <div className="knob" data-testid={`knob-${label}`}>
      <div
        className="knob-dial"
        role="img"
        aria-label={`${label} value ${value}`}
      >
        <div
          className="knob-indicator"
          data-testid={`knob-indicator-${label}`}
          style={{ transform: `translateX(-50%) rotate(${angle}deg)` }}
        />
        {showGhost ? (
          <div
            className="knob-ghost-indicator"
            data-testid={`knob-ghost-${label}`}
            style={{ transform: `translateX(-50%) rotate(${ghostAngle}deg)` }}
          />
        ) : null}
      </div>
      <span className="knob-label">{label}</span>
      <span className="knob-value">{value}</span>
    </div>
  );
}
