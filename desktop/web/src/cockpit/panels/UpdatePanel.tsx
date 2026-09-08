/**
 * UpdatePanel — the operator-facing update surface (spec §7.1).
 *
 * Shape follows the ConnectionDoctorPanel precedent: the declarative body
 * renders through the generic `PanelRenderer`, and this component adds only
 * the affordances that renderer has no vocabulary for — a channel select, a
 * radio group, a freeze checkbox, and two buttons. (The generic renderer
 * emits headings, rows, tables, chips, and *disabled* action buttons; it
 * cannot express an interactive form, which is why a component exists at
 * all rather than a bare registry row.) It is a `store-slice` entry because
 * it is interactive and sources its own data.
 *
 * SAFETY — the #238 lesson, which is why PR #238 went red. This panel is a
 * pure mirror of pushed state:
 *
 *   - It sends NOTHING on mount. There is no effect that transmits, no
 *     check kicked off by rendering, no fetch. The only effect subscribes
 *     to a shell DOM event, which is receive-only.
 *   - Every user-initiated action ("Check now", "Confirm choice") is gated
 *     on `connectionStatus === 'connected'`, so no command can be issued
 *     before the WS handshake has completed. The controls render disabled
 *     rather than hidden, so the operator sees them and sees why.
 *
 * Freeze is honoured client-side by rendering: frozen means no chip and a
 * body that says so. The shell owns the actual network silence.
 */

import { useEffect, useState } from 'react';

import { announce } from '../../a11y';
import { useCockpitStore } from '../../state';
import {
  DEFAULT_CONSENT_CHOICE,
  UPDATE_CHANNELS,
  UPDATE_CONSENT_CHOICES,
  isConsentPending,
  journalLogEntries,
  type UpdateChannel,
  type UpdateConsentChoice,
  subscribeUpdateState,
} from '../../updateProtocol';
import { OperatorLogList } from '../OperatorLogList';

import { PanelRenderer } from './PanelRenderer';
import { CONSENT_LABELS, UPDATE_COPY, updatePanelSpec } from './updatePanelSpec';

/** Shown for `session_status.app_version` (I1) before the sidecar reports one. */
export const UNKNOWN_VERSION = 'unknown';

/** Why an action is unavailable — stated, never merely implied by greying. */
export const WAITING_FOR_CONNECTION = 'Waiting for the cockpit connection.';

/**
 * The #238 gate, as a pure predicate: an operator action may run only once
 * the WS handshake has completed.
 *
 * It is a named export rather than an inline `connectionStatus ===
 * 'connected'` inside each handler for two reasons. First, it is the
 * safety rule, and a safety rule deserves a name and a direct test rather
 * than being reachable only through a `disabled` button that no test can
 * click. Second, `disabled` is an affordance, not a guarantee: the handlers
 * consult this predicate too, so dropping the attribute in a future
 * refactor cannot silently re-open the pre-handshake transmit path.
 */
export function updateActionsAllowed(connectionStatus: string): boolean {
  return connectionStatus === 'connected';
}

export function UpdatePanel(): JSX.Element {
  const update = useCockpitStore((s) => s.update);
  const session = useCockpitStore((s) => s.sessionStatus);
  const connectionStatus = useCockpitStore((s) => s.connectionStatus);
  const setUpdateState = useCockpitStore((s) => s.setUpdateState);
  const setUpdateChannel = useCockpitStore((s) => s.setUpdateChannel);
  const setUpdateFrozen = useCockpitStore((s) => s.setUpdateFrozen);
  const confirmUpdateChoice = useCockpitStore((s) => s.confirmUpdateChoice);
  const [choice, setChoice] = useState<UpdateConsentChoice>(DEFAULT_CONSENT_CHOICE);
  const [note, setNote] = useState<string | null>(null);

  // Receive-only subscription to the shell's I2 event. Listening is not
  // transmitting: nothing leaves the process because of this effect.
  useEffect(() => subscribeUpdateState(setUpdateState), [setUpdateState]);

  const connected = updateActionsAllowed(connectionStatus);
  const runningVersion = session?.app_version ?? UNKNOWN_VERSION;
  const consentPending = isConsentPending(update);
  const disabledReason = connected ? undefined : WAITING_FOR_CONNECTION;

  const checkNow = (): void => {
    /* c8 ignore next -- unreachable through the disabled button; the gate is
       proven directly by the `updateActionsAllowed` tests. */
    if (!connected) return;
    setNote('Check requested.');
  };

  const confirm = (): void => {
    /* c8 ignore next -- as above: defence in depth behind a disabled button. */
    if (!connected) return;
    confirmUpdateChoice(choice);
    announce(`Update choice confirmed: ${CONSENT_LABELS[choice]}`);
    setNote(`Choice recorded: ${CONSENT_LABELS[choice]}`);
  };

  return (
    <div className="cockpit-panel-stack" data-testid="update-panel">
      <div className="cockpit-panel-controls">
        <label className="update-channel-label" htmlFor="update-channel-select">
          channel:
        </label>
        <select
          id="update-channel-select"
          className="update-channel-select"
          value={update.channel}
          onChange={(event) => setUpdateChannel(event.target.value as UpdateChannel)}
          data-testid="update-channel"
        >
          {UPDATE_CHANNELS.map((channel) => (
            <option key={channel} value={channel}>
              {channel}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={checkNow}
          disabled={!connected}
          title={disabledReason}
          data-testid="update-check-now"
        >
          {UPDATE_COPY.checkNow}
        </button>
        {note !== null && <span className="cockpit-panel-note">{note}</span>}
      </div>

      <PanelRenderer spec={updatePanelSpec(update, runningVersion)} />

      {consentPending && (
        <fieldset className="update-consent" data-testid="update-consent">
          <legend>{UPDATE_COPY.consentQuestion}</legend>
          {UPDATE_CONSENT_CHOICES.map((option) => (
            <label key={option} className="update-consent-option">
              <input
                type="radio"
                name="update-consent"
                value={option}
                checked={choice === option}
                onChange={() => setChoice(option)}
                data-testid={`update-consent-${option}`}
              />
              {CONSENT_LABELS[option]}
            </label>
          ))}
          <button
            type="button"
            onClick={confirm}
            disabled={!connected}
            title={disabledReason}
            data-testid="update-confirm"
          >
            {UPDATE_COPY.confirmChoice}
          </button>
        </fieldset>
      )}

      <div className="cockpit-panel-section">
        <h3 className="cockpit-panel-section-heading">{UPDATE_COPY.activityHeading}</h3>
        <OperatorLogList
          entries={journalLogEntries(update.journal)}
          emptyText={UPDATE_COPY.activityEmpty}
          testId="update-activity-list"
          label={UPDATE_COPY.activityHeading}
        />
      </div>

      <label className="update-freeze">
        <input
          type="checkbox"
          checked={update.frozen}
          onChange={(event) => setUpdateFrozen(event.target.checked)}
          data-testid="update-freeze"
        />
        {UPDATE_COPY.freezeToggle}
      </label>
    </div>
  );
}
