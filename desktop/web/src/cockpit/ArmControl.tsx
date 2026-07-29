/**
 * ArmControl — the explicit in-UI arm/disarm affordance (Live-but-Passive).
 *
 * Arming is a two-factor operator decision: an explicit "Arm…" click opens a
 * confirmation dialog demanding the per-launch arm token; only the dialog's
 * "Confirm arm" button sends `{ type: 'arm', arm_token, confirm: true }`.
 * Disarming is always one click — safety must never be behind a dialog.
 *
 * Status changes are announced through the single shared polite live region
 * (`src/a11y/announcer`); the armed state itself is icon + text, never hue
 * alone.
 */

import { useState } from 'react';

import { announce } from '../a11y';
import { useCockpitStore } from '../state';

import { useCockpitClient } from './context';

/** Keep Tab / Shift+Tab focus inside the arm dialog (WCAG 2.4.3 / 2.1.2). */
function trapFocus(container: HTMLElement, event: React.KeyboardEvent): void {
  const focusable = container.querySelectorAll<HTMLElement>(
    'button:not([disabled]), input, [href], [tabindex]:not([tabindex="-1"])',
  );
  if (focusable.length === 0) return;
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

export function ArmControl(): JSX.Element {
  const client = useCockpitClient();
  const armed = useCockpitStore((s) => s.sessionStatus?.armed ?? false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [token, setToken] = useState('');
  const [error, setError] = useState<string | null>(null);

  const closeDialog = (): void => {
    setDialogOpen(false);
    setToken('');
    setError(null);
  };

  const submitArm = (): void => {
    client
      .send({ type: 'arm', arm_token: token, confirm: true })
      .then((ack) => {
        if (ack.ok) {
          closeDialog();
          announce('Hardware output armed');
        } else {
          setError(ack.message ?? 'Arm request rejected');
        }
      })
      .catch(() => setError('Arm request failed to send'));
  };

  const submitDisarm = (): void => {
    client
      .send({ type: 'disarm' })
      .then((ack) => {
        if (ack.ok) {
          announce('Hardware output disarmed — passive');
        } else {
          setError(ack.message ?? 'Disarm request rejected');
        }
      })
      .catch(() => setError('Disarm request failed to send'));
  };

  if (armed) {
    return (
      <div className="arm-control">
        <button
          type="button"
          className="arm-button arm-button-armed"
          onClick={submitDisarm}
          data-testid="disarm-button"
        >
          <span aria-hidden="true">▲</span> ARMED — Disarm
        </button>
        {error !== null && (
          <span className="arm-error" role="alert">
            {error}
          </span>
        )}
      </div>
    );
  }

  return (
    <div className="arm-control">
      <button
        type="button"
        className="arm-button"
        onClick={() => setDialogOpen(true)}
        data-testid="arm-open-button"
      >
        <span aria-hidden="true">○</span> Arm…
      </button>
      {dialogOpen && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="arm-dialog-title"
          aria-describedby="arm-dialog-desc"
          className="arm-dialog"
          data-testid="arm-dialog"
          onKeyDown={(ev) => {
            if (ev.key === 'Escape') {
              closeDialog();
            } else if (ev.key === 'Tab') {
              trapFocus(ev.currentTarget, ev);
            }
          }}
        >
          <h2 id="arm-dialog-title">Arm hardware output</h2>
          <p id="arm-dialog-desc">
            Arming opens a real MIDI output through the guarded seam. Enter the
            per-launch arm token to confirm. A pre-write backup is taken before
            any kit/sound mutation, and arming never survives a disconnect.
          </p>
          <label>
            Arm token
            <input
              value={token}
              onChange={(ev) => setToken(ev.target.value)}
              data-testid="arm-token-input"
              autoFocus
            />
          </label>
          {error !== null && (
            <span className="arm-error" role="alert" data-testid="arm-dialog-error">
              {error}
            </span>
          )}
          <div className="arm-dialog-actions">
            <button type="button" onClick={closeDialog} data-testid="arm-cancel-button">
              Cancel
            </button>
            <button
              type="button"
              onClick={submitArm}
              disabled={token === ''}
              data-testid="arm-confirm-button"
            >
              Confirm arm
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
