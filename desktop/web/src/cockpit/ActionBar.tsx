/**
 * ActionBar — primary controls below the depth slider.
 *
 * Layout (top→bottom):
 *   [ PREVIEW (toggle) ] [ REGEN ]
 *   [          SEND          ]   ← spans 2 cols, primary green
 *   [ UNDO ] [ SAVE ]
 *
 * Disabled states:
 *   - SEND: disabled when no preview candidate is available OR safety_status === "blocked"
 *   - UNDO: disabled when history.entries is empty or current is the first entry
 *
 * The optional EXPORT button is intentionally NOT in this bar — per the v10 mockup it lives
 * inside the active profile card (handled by ProfileChips).
 */

import { selectCanUndo, useCockpitStore } from '../state';

import { useCockpitClient } from './context';

export interface ActionBarProps {
  previewOn: boolean;
  onTogglePreview: (next: boolean) => void;
}

export function ActionBar({ previewOn, onTogglePreview }: ActionBarProps): JSX.Element {
  const client = useCockpitClient();
  const candidate = useCockpitStore((s) => s.previewCandidate);
  const canUndo = useCockpitStore(selectCanUndo);

  const sendDisabled = candidate === null || candidate.safety_status === 'high_risk';
  const previewLabel = previewOn ? '◐ PREVIEW (on)' : '◐ PREVIEW (off)';
  const padsAffected = candidate === null ? 0 : candidate.pad_deltas.length;

  const handleTogglePreview = (): void => {
    const next = !previewOn;
    onTogglePreview(next);
    void client.send({ type: 'toggle_preview', on: next });
  };

  return (
    <div className="action-bar" data-testid="action-bar">
      <button
        type="button"
        className={previewOn ? 'action-button toggle on' : 'action-button toggle'}
        aria-pressed={previewOn}
        data-testid="action-preview"
        onClick={handleTogglePreview}
      >
        {previewLabel}
      </button>
      <button
        type="button"
        className="action-button"
        data-testid="action-regen"
        onClick={() => {
          void client.send({ type: 'regen' });
        }}
      >
        ⟳ REGEN
      </button>
      <button
        type="button"
        className="action-button primary"
        data-testid="action-send"
        disabled={sendDisabled}
        onClick={() => {
          void client.send({ type: 'send' });
        }}
      >
        SEND ▶ {padsAffected === 0 ? '' : `(${padsAffected} pad${padsAffected === 1 ? '' : 's'})`}
      </button>
      <button
        type="button"
        className="action-button"
        data-testid="action-undo"
        disabled={!canUndo}
        onClick={() => {
          void client.send({ type: 'undo' });
        }}
      >
        ↶ UNDO
      </button>
      <button
        type="button"
        className="action-button"
        data-testid="action-save"
        onClick={() => {
          void client.send({ type: 'save' });
        }}
      >
        SAVE ↓
      </button>
    </div>
  );
}
