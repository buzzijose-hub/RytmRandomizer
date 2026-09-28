/**
 * UpdatePanel — the operator-facing update surface (spec §7.1).
 *
 * Shape follows the ConnectionDoctorPanel precedent: the declarative body
 * renders through the generic `PanelRenderer`, and this component adds only
 * the affordances that renderer has no vocabulary for — a consent radio
 * group and two buttons. (The generic renderer
 * emits headings, rows, tables, chips, and *disabled* action buttons; it
 * cannot express an interactive form, which is why a component exists at
 * all rather than a bare registry row.) It is a `store-slice` entry because
 * it is interactive and sources its own data.
 *
 * SAFETY — the #238 lesson, which is why PR #238 went red. This panel is a
 * pure mirror of pushed state:
 *
 *   - Mount subscribes to shell IPC and reads a local snapshot. It never
 *     sends a backend WebSocket command or starts a network update check.
 *   - Every user-initiated action ("Check now", "Confirm choice") is gated
 *     on an established cockpit connection and session. The controls render disabled
 *     rather than hidden, so the operator sees them and sees why.
 *
 * Channel and freeze are read-only launch settings reported by the shell.
 */

import { useEffect, useState } from 'react';

import { announce } from '../../a11y';
import { useCockpitStore } from '../../state';
import {
  DEFAULT_CONSENT_CHOICE,
  UPDATE_CONSENT_CHOICES,
  isConsentPending,
  journalLogEntries,
  type UpdateConsentChoice,
  confirmUpdateChoiceOnShell,
  requestUpdateCheck,
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
 * Connection portion of the action gate; the panel also requires session data.
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
  const setUpdateJournal = useCockpitStore((s) => s.setUpdateJournal);
  const setUpdateChannel = useCockpitStore((s) => s.setUpdateChannel);
  const setUpdateFrozen = useCockpitStore((s) => s.setUpdateFrozen);
  const confirmUpdateChoice = useCockpitStore((s) => s.confirmUpdateChoice);
  const [choice, setChoice] = useState<UpdateConsentChoice>(DEFAULT_CONSENT_CHOICE);
  const [note, setNote] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    setChoice(DEFAULT_CONSENT_CHOICE);
    setNote(null);
  }, [update.state?.version]);

  // Receive-only subscription to the shell's I2 event. Listening is not
  // transmitting: nothing leaves the process because of this effect.
  useEffect(
    () => subscribeUpdateState(setUpdateState, (snapshot) => {
      setUpdateState(snapshot.state);
      setUpdateJournal(snapshot.journal);
      setUpdateChannel(snapshot.channel);
      setUpdateFrozen(snapshot.frozen);
    }),
    [setUpdateState, setUpdateJournal, setUpdateChannel, setUpdateFrozen],
  );

  const connected = updateActionsAllowed(connectionStatus) && session !== null;
  const runningVersion = session?.app_version ?? UNKNOWN_VERSION;
  const consentPending = isConsentPending(update);
  const disabledReason = connected ? undefined : WAITING_FOR_CONNECTION;

  const checkNow = async (): Promise<void> => {
    /* c8 ignore next -- unreachable through the disabled button; the gate is
       proven directly by the `updateActionsAllowed` tests. */
    if (!connected) return;
    // Reaches the shell's driver. Before this the button only set a note.
    const accepted = await requestUpdateCheck();
    setNote(accepted ? 'Check requested.' : 'The shell did not accept that check.');
  };

  const confirm = async (): Promise<void> => {
    /* c8 ignore next -- as above: defence in depth behind a disabled button. */
    if (!connected) return;
    /* c8 ignore next -- the confirm button only renders inside the staged
       consent block, so a version is always present here; the fallback exists
       so a future refactor that moves the button cannot send `undefined`. */
    const version = update.state?.version ?? UNKNOWN_VERSION;
    setSubmitting(true);
    const accepted = await confirmUpdateChoiceOnShell(version, choice);
    setSubmitting(false);
    // An answer for an older release cannot hide a newly staged prompt.
    if (useCockpitStore.getState().update.state?.version !== version) return;
    if (!accepted) {
      setNote('The shell did not accept that choice.');
      return;
    }
    confirmUpdateChoice(choice);
    announce(`Update choice confirmed: ${CONSENT_LABELS[choice]}`);
    setNote(`Choice recorded: ${CONSENT_LABELS[choice]}`);
  };

  return (
    <div className="cockpit-panel-stack" data-testid="update-panel">
      <div className="cockpit-panel-controls">
        <span data-testid="update-channel">
          Shell channel: {update.state === null ? 'unavailable' : update.channel}
        </span>
        <button
          type="button"
          onClick={() => { void checkNow(); }}
          disabled={!connected || update.frozen}
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
                disabled={submitting}
                onChange={() => setChoice(option)}
                data-testid={`update-consent-${option}`}
              />
              {CONSENT_LABELS[option]}
            </label>
          ))}
          <button
            type="button"
            onClick={() => { void confirm(); }}
            disabled={!connected || submitting}
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

      <p data-testid="update-freeze">
        {update.state === null ? 'Waiting for shell settings.' :
          update.frozen ? 'Shell updates: frozen' : 'Shell updates: enabled'}
      </p>
      <p>{UPDATE_COPY.settingsInstruction}</p>
    </div>
  );
}
