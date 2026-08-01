/**
 * ArmControl — the explicit in-UI arm/disarm affordance (Live-but-Passive).
 *
 * Arming is an explicit operator decision: an "Arm…" click opens a
 * confirmation dialog demanding the exact MIDI output port, chosen from the
 * live enumeration; only then does the "Confirm arm" button send
 * `{ type: 'arm', arm_token, port_name, confirm: true }`.
 *
 * The `arm_token` is the per-launch ARM secret, which is DELIVERED rather
 * than typed: the sidecar mints it and writes it 0600, and the Tauri shell
 * injects it into this window before any app code runs
 * (`resolveArmSecret`). Requiring transcription made arming impossible in a
 * packaged double-click build — there is no terminal there to read it from.
 * When no secret was injected the dialog says so and refuses, rather than
 * sending an empty token that the server would reject opaquely.
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

import { resolveArmSecret } from '../ws/client';
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
  const [portName, setPortName] = useState('');
  const [error, setError] = useState<string | null>(null);

  // The ARM secret is DELIVERED, never typed. The sidecar mints it and
  // writes it 0600; the Tauri shell reads that file and injects it before
  // any app code runs. Requiring the operator to transcribe it made arming
  // impossible in a packaged double-click build (no terminal to read it
  // from), so the deliberate operator gesture is choosing the exact output
  // port and confirming — not copying a secret.
  const armSecret = resolveArmSecret();

  // No default port selection on purpose: pre-selecting an output would
  // reintroduce the auto-pick the server-side fix removed, one layer up.
  const canConfirm = armSecret !== null && portName !== '';

  const closeDialog = (): void => {
    setDialogOpen(false);
    setPortName('');
    setError(null);
  };

  // Reached from the confirm button, which stays `disabled` until
  // `canConfirm` (exact port chosen AND a secret was injected). The
  // null-secret re-check below is NOT redundant with that: `resolveArmSecret`
  // reads live browser state, so a secret can disappear between render and
  // click (webview reload clearing storage, a shell restart). Failing closed
  // there is the difference between a clear message and an opaque server
  // refusal.
  const submitArm = (): void => {
    // Re-read at CLICK time, not the render-time closure value: a webview
    // reload or shell restart can clear the injection after the button was
    // enabled, and sending a stale/absent secret would surface as an opaque
    // server refusal instead of an actionable message.
    const secretNow = resolveArmSecret();
    if (secretNow === null) {
      // Fail closed. Sending an empty token would just surface as an opaque
      // server refusal; naming the real cause is actionable.
      setError(
        'Arm secret unavailable — the cockpit sidecar did not hand one to this ' +
          'window. Relaunch the desktop app, or see docs/COCKPIT_QUICKSTART.md ' +
          'for the two-terminal dev flow.',
      );
      return;
    }
    client
      .send({ type: 'arm', arm_token: secretNow, port_name: portName, confirm: true })
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
            exact instrument to arm, then confirm. Only live-dial CC changes are
            sent — writes to saved kits and sounds are disabled because they
            cannot yet be undone. Arming never survives a disconnect.
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
          {armSecret === null && (
            <p data-testid="arm-no-secret">
              Arm secret unavailable — this window was not handed one by the
              cockpit sidecar. Relaunch the desktop app to arm.
            </p>
          )}
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
