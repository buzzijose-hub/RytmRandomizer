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
 * SEND has two distinct shapes, and the difference is load-bearing:
 *
 *   - **Unarmed / mock (DRY-RUN SEND).** One click with the exact prepared
 *     `send_plan_id` and no `confirm`. Nothing reaches hardware, so an extra
 *     gesture would be safety theatre.
 *   - **Live + armed (SEND).** Opens an explicit per-action confirmation
 *     dialog showing the exact output, plan, pads, and message count; only
 *     "Confirm send" emits both `confirm: true` and the current plan id.
 *     The sidecar's ArmedApply seam *refuses* an armed send without
 *     `confirm: true` (`cockpit/ws/handlers.py::_armed_send_over_seam`), so
 *     without this affordance the live SEND button could not succeed at all.
 *     "Armed" is a session state; each individual write is still its own
 *     operator decision (Live-but-Passive rule).
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

import { SIDECAR_REQUIRED_REASON } from './ReconnectBanner';
import { ExactRytmSendDialog, useExactRytmSend } from './ExactRytmSend';
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
  const sendPlan = useCockpitStore((s) => s.sendPlan);
  const session = useCockpitStore((s) => s.sessionStatus);

  // Never-connected (no session ever arrived): the sidecar-requiring
  // actions are disabled WITH a reason — present, never hidden. Data-driven
  // buttons (PREPARE/SEND/UNDO) are already disabled by their empty slices.
  // Mid-session loss deliberately keeps them enabled: failures surface in
  // the operator log and the ReconnectBanner owns the connection truth.
  const offline = session === null;
  const offlineTitle = offline ? SIDECAR_REQUIRED_REASON : undefined;
  const prepareDisabled = candidate === null;
  const previewLabel = previewOn ? '◐ PREVIEW (on)' : '◐ PREVIEW (off)';
  const padsAffected = preparedPadCount;
  const padSuffix = padsAffected === 0 ? '' : `(${padsAffected} pad${padsAffected === 1 ? '' : 's'})`;
  const exactSend = useExactRytmSend({
    canSend,
    onSend: sendCommand,
    sendPlan,
    session,
  });

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
        disabled={offline}
        title={offlineTitle}
        onClick={handleTogglePreview}
      >
        {previewLabel}
      </button>
      <button
        type="button"
        className="action-button"
        data-testid="action-regen"
        disabled={offline}
        title={offlineTitle}
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
        ref={exactSend.triggerRef}
        type="button"
        className="action-button primary"
        data-testid="action-send"
        disabled={exactSend.disabled}
        onClick={exactSend.request}
      >
        {exactSend.label} ▶ {padSuffix}
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
        disabled={offline}
        title={offlineTitle}
        onClick={() => {
          sendCommand({ type: 'save' });
        }}
      >
        SAVE ↓
      </button>
      <ExactRytmSendDialog controller={exactSend} sendPlan={sendPlan} session={session} />
    </div>
  );
}
