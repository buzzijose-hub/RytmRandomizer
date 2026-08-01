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
 *   - **Unarmed / mock (DRY-RUN SEND).** One click, `{ type: 'send' }` with no
 *     `confirm`. Nothing reaches hardware, so an extra gesture would be
 *     safety theatre — and the sidecar does not ask for one.
 *   - **Live + armed (SEND).** Opens an explicit per-action confirmation
 *     dialog; only "Confirm send" emits `{ type: 'send', confirm: true }`.
 *     The sidecar's ArmedApply seam *refuses* an armed send without
 *     `confirm: true` (`cockpit/ws/handlers.py::_armed_send_over_seam`), so
 *     without this affordance the live SEND button could not succeed at all.
 *     "Armed" is a session state; each individual write is still its own
 *     operator decision (Live-but-Passive rule).
 *
 * The optional EXPORT button is intentionally NOT in this bar — per the v10 mockup it lives
 * inside the active profile card (handled by ProfileChips).
 */

import { useState } from 'react';

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

/**
 * Keep Tab / Shift+Tab focus inside the send-confirm dialog (WCAG 2.4.3 / 2.1.2).
 *
 * The dialog's focusable set is statically two always-enabled buttons
 * (Cancel, Confirm send), so there is deliberately no "empty set" guard here:
 * it would be unreachable defensive code. If a future revision adds a
 * conditionally-disabled control, re-introduce the guard *with* a test.
 */
function trapFocus(container: HTMLElement, event: React.KeyboardEvent): void {
  const focusable = container.querySelectorAll<HTMLElement>('button:not([disabled])');
  const first = focusable[0]!;
  const last = focusable[focusable.length - 1]!;
  const active = container.ownerDocument.activeElement;
  if (event.shiftKey && active === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && active === last) {
    event.preventDefault();
    first.focus();
  }
}

export function ActionBar({ previewOn, onTogglePreview }: ActionBarProps): JSX.Element {
  const sendCommand = useLoggedCommand();
  const candidate = useCockpitStore((s) => s.previewCandidate);
  const canSend = useCockpitStore(selectCanSend);
  const canUndo = useCockpitStore(selectCanUndo);
  const preparedPadCount = useCockpitStore(selectPreparedPadCount);
  const session = useCockpitStore((s) => s.sessionStatus);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const prepareDisabled = candidate === null;
  const sendDisabled = !canSend;
  const previewLabel = previewOn ? '◐ PREVIEW (on)' : '◐ PREVIEW (off)';
  const padsAffected = preparedPadCount;
  const isLiveHardware = session?.mode === 'live' && session.armed;
  const sendLabel = isLiveHardware ? 'SEND' : 'DRY-RUN SEND';
  const padSuffix = padsAffected === 0 ? '' : `(${padsAffected} pad${padsAffected === 1 ? '' : 's'})`;

  const handleTogglePreview = (): void => {
    const next = !previewOn;
    onTogglePreview(next);
    sendCommand({ type: 'toggle_preview', on: next });
  };

  // Armed: gather the per-action confirmation first. Unarmed: send straight
  // through, exactly as before — no confirm field, no extra click.
  const handleSendClick = (): void => {
    if (isLiveHardware) {
      setConfirmOpen(true);
      return;
    }
    sendCommand({ type: 'send' });
  };

  const handleConfirmSend = (): void => {
    setConfirmOpen(false);
    sendCommand({ type: 'send', confirm: true });
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
        onClick={handleSendClick}
      >
        {sendLabel} ▶ {padSuffix}
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
      {/*
        Gated on `isLiveHardware`, not just `confirmOpen`: if the session
        disarms while the dialog is open (cable pull, explicit disarm), the
        dialog's "the session is armed on X" text is instantly false and its
        confirm would be a per-action confirmation for a session that no
        longer has one. Dropping it on the same render keeps the UI from
        outliving the state it describes.
      */}
      {confirmOpen && isLiveHardware && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="send-confirm-title"
          aria-describedby="send-confirm-desc"
          className="arm-dialog"
          data-testid="send-confirm-dialog"
          onKeyDown={(ev) => {
            if (ev.key === 'Escape') {
              setConfirmOpen(false);
            } else if (ev.key === 'Tab') {
              trapFocus(ev.currentTarget, ev);
            }
          }}
        >
          <h2 id="send-confirm-title">Confirm send to hardware</h2>
          <p id="send-confirm-desc">
            The session is armed on {session?.midi_port ?? 'the selected output'}. Confirming
            transmits this prepared plan {padSuffix === '' ? '' : `${padSuffix} `}as live-dial CC
            changes to the instrument&apos;s working memory. Saved kits and sounds are not
            written. Each send is confirmed separately.
          </p>
          <div className="arm-dialog-actions">
            <button
              type="button"
              onClick={() => setConfirmOpen(false)}
              data-testid="send-cancel-button"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleConfirmSend}
              data-testid="send-confirm-button"
              autoFocus
            >
              Confirm send
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
