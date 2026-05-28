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

import {
  selectCanSend,
  selectCanUndo,
  selectPreparedPadCount,
  useCockpitStore,
} from '../state';

import { useLoggedCommand } from './useLoggedCommand';

export interface ActionBarProps {
  previewOn: boolean;
  onTogglePreview: (next: boolean) => void;
}

export function ActionBar({ previewOn, onTogglePreview }: ActionBarProps): JSX.Element {
  const sendCommand = useLoggedCommand();
  const candidate = useCockpitStore((s) => s.previewCandidate);
  const canSend = useCockpitStore(selectCanSend);
  const canUndo = useCockpitStore(selectCanUndo);
  const preparedPadCount = useCockpitStore(selectPreparedPadCount);
  const session = useCockpitStore((s) => s.sessionStatus);

  const prepareDisabled = candidate === null;
  const sendDisabled = !canSend;
  const previewLabel = previewOn ? '◐ PREVIEW (on)' : '◐ PREVIEW (off)';
  const padsAffected = preparedPadCount;
  const isLiveHardware = session?.mode === 'live' && session.armed;
  const sendLabel = isLiveHardware ? 'SEND' : 'DRY-RUN SEND';

  const handleTogglePreview = (): void => {
    const next = !previewOn;
    onTogglePreview(next);
    sendCommand({ type: 'toggle_preview', on: next });
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
          sendCommand({ type: 'regen' });
        }}
      >
        ⟳ REGEN
      </button>
      <button
        type="button"
        className="action-button"
        data-testid="action-prepare-send-plan"
        disabled={prepareDisabled}
        onClick={() => {
          sendCommand({ type: 'prepare_send_plan' });
        }}
      >
        PREPARE
      </button>
      <button
        type="button"
        className="action-button primary"
        data-testid="action-send"
        disabled={sendDisabled}
        onClick={() => {
          sendCommand({ type: 'send' });
        }}
      >
        {sendLabel} ▶ {padsAffected === 0 ? '' : `(${padsAffected} pad${padsAffected === 1 ? '' : 's'})`}
      </button>
      <button
        type="button"
        className="action-button"
        data-testid="action-undo"
        disabled={!canUndo}
        onClick={() => {
          sendCommand({ type: 'undo' });
        }}
      >
        ↶ UNDO
      </button>
      <button
        type="button"
        className="action-button"
        data-testid="action-save"
        onClick={() => {
          sendCommand({ type: 'save' });
        }}
      >
        SAVE ↓
      </button>
    </div>
  );
}
