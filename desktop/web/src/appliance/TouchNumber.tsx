import { useState } from 'react';

import { TouchDialog } from './TouchDialog';

interface TouchNumberProps {
  label: string;
  value: number;
  disabled?: boolean;
  onChange: (value: number) => void;
}

/** Depth is a next-roll rule. Touch adjustment stages a value before publication. */
export function TouchNumber({ label, value, disabled = false, onChange }: TouchNumberProps): JSX.Element {
  const [draft, setDraft] = useState<number | null>(null);
  const adjust = (amount: number): void => setDraft((current) => Math.max(0, Math.min(100, (current ?? value) + amount)));
  return (
    <>
      <button
        type="button"
        className="appliance-depth"
        aria-label={`${label} ${value} percent. Adjust`}
        disabled={disabled}
        onClick={() => setDraft(value)}
      >
        <span>{label}</span><strong>{value}<small>%</small></strong>
        <span className="appliance-meter" aria-hidden="true"><i style={{ width: `${value}%` }} /></span>
      </button>
      {draft !== null && (
        <TouchDialog title={`${label} DEPTH`} onClose={() => setDraft(null)}>
          <output className="appliance-number">{draft}%</output>
          <div className="appliance-adjust"><button type="button" onClick={() => adjust(-10)}>-10</button><button type="button" onClick={() => adjust(-1)}>-1</button><button type="button" onClick={() => adjust(1)}>+1</button><button type="button" onClick={() => adjust(10)}>+10</button></div>
          <div className="appliance-presets">{[0, 25, 50, 75, 100].map((preset) => <button type="button" key={preset} aria-pressed={draft === preset} onClick={() => setDraft(preset)}>{preset}%</button>)}</div>
          <p>Applies to the next roll. Changing depth does not reverse earlier rolls. Zero performs no mutation.</p>
          <div className="appliance-dialog-actions"><button type="button" onClick={() => setDraft(null)}>CANCEL</button><button type="button" className="appliance-primary" onClick={() => { onChange(draft); setDraft(null); }}>SET {draft}%</button></div>
        </TouchDialog>
      )}
    </>
  );
}
