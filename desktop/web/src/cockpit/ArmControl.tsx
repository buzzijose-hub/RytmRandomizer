/**
 * ArmControl — the explicit in-UI arm/disarm affordance (Live-but-Passive).
 *
 * Arming is a three-factor operator decision: an explicit "Arm…" click opens
 * a confirmation dialog demanding (1) the exact MIDI output port, chosen from
 * the live enumeration, and (2) the per-launch arm token; only then does
 * (3) the "Confirm arm" button send
 * `{ type: 'arm', arm_token, port_name, confirm: true }`.
 *
 * The port selector is not a convenience — it is a safety control. With a
 * Rytm and an Analog Four both connected, a server-side "first Elektron-
 * looking output" guess can arm the wrong instrument, so the operator names
 * the target explicitly and the server fails closed on anything that does not
 * match exactly one enumerated output.
 *
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
    'button:not([disabled]), input, select, [href], [tabindex]:not([tabindex="-1"])',
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
  const availableOutputs = useCockpitStore((s) => s.connection?.available_outputs);
  const outputs = availableOutputs ?? [];
  const [dialogOpen, setDialogOpen] = useState(false);
  const [token, setToken] = useState('');
  const [portName, setPortName] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Both factors are required. There is deliberately no default selection:
  // pre-selecting an output would reintroduce the auto-pick the server-side
  // fix removed, just one layer up.
  const canConfirm = token !== '' && portName !== '';

  const closeDialog = (): void => {
    setDialogOpen(false);
    setToken('');
    setPortName('');
    setError(null);
  };

  // Reachable only from the confirm button, which stays `disabled` until
  // `canConfirm` — so this never runs without an exact port AND a token.
  // (A redundant in-handler re-check was removed: it was unreachable, and an
  // unreachable guard is exactly the kind of dead safety code this change set
  // is eliminating elsewhere.)
  const submitArm = (): void => {
    client
      .send({ type: 'arm', arm_token: token, port_name: portName, confirm: true })
      .then((ack) => {
        if (ack.ok) {
          const armedPort = portName;
          closeDialog();
          announce(`Hardware output armed on ${armedPort}`);
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
            Arming opens a real MIDI output through the guarded seam. Choose the
            exact instrument to arm, then enter the per-launch arm token. Only
            live-dial CC changes are sent — writes to saved kits and sounds are
            disabled because they cannot yet be undone. Arming never survives a
            disconnect.
          </p>
          <label htmlFor="arm-port-select">MIDI output port</label>
          <select
            id="arm-port-select"
            value={portName}
            onChange={(ev) => setPortName(ev.target.value)}
            data-testid="arm-port-select"
            autoFocus
          >
            <option value="">Select a port…</option>
            {outputs.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
          {outputs.length === 0 && (
            <p data-testid="arm-no-ports">
              No MIDI outputs detected. Connect the instrument and wait for the
              connection status to report it.
            </p>
          )}
          <label htmlFor="arm-token-input">Arm token</label>
          <input
            id="arm-token-input"
            value={token}
            onChange={(ev) => setToken(ev.target.value)}
            data-testid="arm-token-input"
          />
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
              disabled={!canConfirm}
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
