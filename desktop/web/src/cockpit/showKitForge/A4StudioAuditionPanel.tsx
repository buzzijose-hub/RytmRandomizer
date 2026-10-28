import { useEffect, useRef, useState } from 'react';

import { useCockpitStore } from '../../state';
import { resolveArmSecret } from '../../ws/client';
import type { A4StudioAuditionOutcome, A4StudioAuditionPlan, Command, ShowBank, ShowBankEntry, ShowBankSendA4StudioAuditionCommand } from '../../ws/protocol';
import { useCockpitClient } from '../context';
import { ANALOG_FOUR_DEVICE_ID, ANALOG_FOUR_TRACKS } from '../devices';

interface Props { bank: ShowBank; entry: ShowBankEntry; disabled: boolean }
type Channels = [number, number, number, number];

/** Routing is transient operator input, never a default or a persisted grant. */
export function A4StudioAuditionPanel(props: Props): JSX.Element {
  const client = useCockpitClient();
  const [portName, setPortName] = useState('');
  const [channelInputs, setChannelInputs] = useState(() => ANALOG_FOUR_TRACKS.map(() => ''));
  const [sending, setSending] = useState(false);
  const [lastAttempt, setLastAttempt] = useState<{ planId: string; outcome?: A4StudioAuditionOutcome; error?: string } | null>(null);
  const sendGeneration = useRef(0);
  useEffect(() => () => { sendGeneration.current += 1; }, []);
  const connection = useCockpitStore((state) => state.connection);
  const status = useCockpitStore((state) => state.connectionStatus);
  const session = useCockpitStore((state) => state.sessionStatus);
  const sessionStale = useCockpitStore((state) => state.sessionStatusStale);
  const generation = useCockpitStore((state) => state.sessionGeneration);
  const mutationRevision = useCockpitStore((state) => state.mutationContextRevision);
  const captures = useCockpitStore((state) => state.kitCaptures);
  const targets = useCockpitStore((state) => state.a4TrackTargets);
  const locks = useCockpitStore((state) => state.a4TrackLocks);
  const candidate = useCockpitStore((state) => state.previewCandidate);
  const stage = useCockpitStore((state) => state.dualMachineStage);
  const outputs = connection?.available_outputs ?? [];
  const uniqueOutput = portName !== '' && outputs.filter((name) => name === portName).length === 1;
  const numbers = channelInputs.map(Number);
  const channelsValid = channelInputs.every((value) => /^\d+$/.test(value)) &&
    numbers.every((value) => Number.isInteger(value) && value >= 1 && value <= 16);
  const distinct = new Set(numbers).size === ANALOG_FOUR_TRACKS.length;
  const routingValid = uniqueOutput && channelsValid && distinct;
  const connected = status === 'connected' && session !== null && !sessionStale;
  // Remount only the authority-bearing request state, including pending promises.
  const key = JSON.stringify([
    props.bank, props.entry, props.disabled, portName, channelInputs, connection, status,
    sessionStale, generation, session?.armed, session?.armed_device_id, session?.midi_port,
    mutationRevision, captures, targets, locks, candidate, stage,
  ]);

  // A send result is historical, not authority. Preserve interruption counts when
  // the sidecar revokes readiness or disarms before delivering the final ACK.
  async function sendTrial(command: ShowBankSendA4StudioAuditionCommand): Promise<void> {
    const generation = ++sendGeneration.current;
    setSending(true);
    setLastAttempt(null);
    try {
      const ack = await client.send(command);
      if (sendGeneration.current !== generation) return;
      if (!ack.ok) {
        setLastAttempt({ planId: command.send_plan_id, outcome: ack.a4_studio_outcome,
          error: ack.error ?? ack.message ?? 'A4 studio SEND refused. Hardware state is unknown.' });
      } else if (ack.a4_studio_outcome === undefined) {
        setLastAttempt({ planId: command.send_plan_id, error: 'A4 studio outcome unavailable. Hardware state is unknown.' });
      } else {
        setLastAttempt({ planId: command.send_plan_id, outcome: ack.a4_studio_outcome });
      }
    } catch (failure) {
      if (sendGeneration.current === generation) setLastAttempt({ planId: command.send_plan_id,
        error: failure instanceof Error ? failure.message : String(failure) });
    } finally {
      if (sendGeneration.current === generation) setSending(false);
    }
  }

  return <section className="show-kit-forge-section a4-studio-audition-panel" aria-label="A4 studio audition">
    <h4>A4 studio audition</h4>
    <p><strong>Operator-present, unqualified, working RAM only.</strong> No persistent KIT write, hardware qualification or show-readiness grant. General A4/BOTH stage output remains blocked.</p>
    <p>Manual recovery: A4 saved source slot <strong>{props.entry.analog_four_source.hardware_slot ?? 'not recorded'}</strong> ({props.entry.analog_four_source.kit_name}). A capture alone does not prove unsaved RAM was restored.</p>
    <div className="a4-studio-routing">
      <label>A4 USB output
        <select value={portName} disabled={props.disabled || !connected || sending}
          onChange={(event) => setPortName(event.currentTarget.value)}>
          <option value="">Select an exact output port</option>
          {[...new Set(outputs)].map((name) => <option key={name} value={name}
            disabled={outputs.filter((item) => item === name).length !== 1}>{name}</option>)}
        </select>
      </label>
      {ANALOG_FOUR_TRACKS.map(({ track }, index) => <label key={track}>A4 track {track} channel (1-16)
        <input type="number" min={1} max={16} step={1} value={channelInputs[index]}
          disabled={props.disabled || !connected || sending} onChange={(event) => {
            const value = event.currentTarget.value;
            setChannelInputs((previous) => previous.map((old, i) => i === index ? value : old));
          }} />
      </label>)}
    </div>
    <p>Only an explicitly Analog Four-named USB output is permitted. A port name is not physical device identity proof; generic DIN interfaces and Rytm outputs are refused.</p>
    {outputs.length === 0 && <p>No enumerated MIDI outputs available.</p>}
    {portName !== '' && !uniqueOutput && <p role="alert">Select an output name occurring exactly once in the current enumeration.</p>}
    {channelInputs.some((value) => value !== '') && !channelsValid && <p>Enter four integer channels from 1 to 16.</p>}
    {channelsValid && !distinct && <p role="alert">The four track channels must be distinct.</p>}
    <StudioTrial key={key} {...props} portName={portName} channels={numbers as Channels}
      routingValid={routingValid} connected={connected} sending={sending} onSend={(command) => void sendTrial(command)} />
    {sending && <p role="status">A4 studio send pending. Disarm remains available.</p>}
    {lastAttempt !== null && <div className="a4-studio-last-attempt">
      <p>Last A4 studio attempt: <code>{lastAttempt.planId}</code></p>
      {lastAttempt.error !== undefined && <p role="alert">{lastAttempt.error}</p>}
      {lastAttempt.outcome !== undefined && <p role="status">A4 studio outcome: {lastAttempt.outcome.status}. Sent {lastAttempt.outcome.sent_count} of {lastAttempt.outcome.expected_count}. {lastAttempt.outcome.reason}</p>}
      <p>No hardware qualification or show readiness granted. Manually reload the saved source and capture again before another attempt.</p>
    </div>}
  </section>;
}

interface TrialProps extends Props {
  portName: string;
  channels: Channels;
  routingValid: boolean;
  connected: boolean;
  sending: boolean;
  onSend: (command: ShowBankSendA4StudioAuditionCommand) => void;
}

function StudioTrial({ bank, entry, disabled, portName, channels, routingValid, connected, sending, onSend }: TrialProps): JSX.Element {
  const client = useCockpitClient();
  const session = useCockpitStore((state) => state.sessionStatus);
  const [acknowledged, setAcknowledged] = useState(false);
  const [reloaded, setReloaded] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const [plan, setPlan] = useState<A4StudioAuditionPlan | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<Command['type'] | null>(null);
  const serial = useRef(0);
  useEffect(() => () => { serial.current += 1; }, []);

  const available = connected && !disabled && busy === null && !sending;
  const canPrepare = available && routingValid && acknowledged && reloaded && entry.selected_candidate_id !== null;
  const sameArmedOutput = session?.armed === true && session.armed_device_id === ANALOG_FOUR_DEVICE_ID && session.midi_port === portName;
  const canSend = canPrepare && confirmed && sameArmedOutput && plan?.ready === true;
  const secret = resolveArmSecret();

  function clearPlan(): void {
    serial.current += 1;
    setPlan(null);
    setConfirmed(false);
    setError(null);
    setBusy(null);
  }

  async function issue(command: Command): Promise<void> {
    const request = ++serial.current;
    setBusy(command.type);
    setPlan(null);
    setConfirmed(false);
    setError(null);
    try {
      const ack = await client.send(command);
      if (serial.current !== request) return;
      if (!ack.ok) throw new Error(ack.error ?? ack.message ?? 'A4 studio action refused.');
      if (command.type === 'show_bank_prepare_a4_studio_audition') {
        const result = ack.a4_studio_plan;
        if (result === undefined || result.bank_id !== bank.bank_id || result.bank_revision !== bank.revision ||
          result.entry_id !== entry.entry_id || result.candidate_id !== entry.selected_candidate_id ||
          result.routing.output_port_name !== portName || JSON.stringify(result.routing.track_channels) !== JSON.stringify(channels) ||
          result.hardware_send_validated !== false || result.persistent_write !== false ||
          result.output_authority !== 'studio-ram-only-unqualified' || result.plan_id === '' ||
          result.plan_id !== result.send_plan.plan_id || result.send_plan.candidate_id !== result.candidate_id ||
          result.ready !== result.send_plan.ready || result.ready === (result.blocked_reasons.length > 0) ||
          (!result.ready && result.send_plan.packets.length > 0)) {
          throw new Error('A4 studio plan did not match this exact candidate and routing.');
        }
        setPlan(result);
      }
    } catch (failure) {
      if (serial.current === request) setError(failure instanceof Error ? failure.message : String(failure));
    } finally {
      if (serial.current === request) setBusy(null);
    }
  }

  function arm(): void {
    const currentSecret = resolveArmSecret();
    if (currentSecret === null) {
      setError('Arm secret unavailable. Relaunch the desktop app.');
      return;
    }
    void issue({ type: 'arm', device_id: ANALOG_FOUR_DEVICE_ID, arm_token: currentSecret,
      port_name: portName, confirm: true, acknowledge_unvalidated_hardware: true });
  }

  return <>
    <label className="a4-studio-attestation"><input type="checkbox" checked={acknowledged} disabled={!connected || disabled}
      onChange={(event) => { clearPlan(); setAcknowledged(event.currentTarget.checked); }} />
      I acknowledge this A4 hardware path is unqualified; this is an operator-present RAM-only trial.
    </label>
    <label className="a4-studio-attestation"><input type="checkbox" checked={reloaded} disabled={!connected || disabled}
      onChange={(event) => { clearPlan(); setReloaded(event.currentTarget.checked); }} />
      I manually reloaded the saved A4 source slot and captured its current KIT before this attempt.
    </label>
    <div className="show-kit-forge-actions">
      <button type="button" disabled={!available || !routingValid || !acknowledged || session?.armed === true || secret === null}
        onClick={arm}>Arm A4 studio output</button>
      <button type="button" disabled={!connected} onClick={() => {
        clearPlan(); setReloaded(false); void issue({ type: 'disarm' });
      }}>Disarm output</button>
      <button type="button" disabled={!canPrepare} onClick={() => void issue({
        type: 'show_bank_prepare_a4_studio_audition', bank_id: bank.bank_id, entry_id: entry.entry_id,
        expected_revision: bank.revision, output_port_name: portName, track_channels: channels,
        source_reloaded: true, acknowledge_unvalidated_hardware: true,
      })}>Prepare A4 studio plan</button>
    </div>
    {secret === null && <p>Arm secret unavailable. Relaunch the desktop app to arm output.</p>}
    <p>{sameArmedOutput ? `A4 studio output armed on ${portName}.` : 'SEND requires A4 explicitly armed on this exact output port.'}</p>
    {busy !== null && <p role="status">A4 studio action pending.</p>}
    {error !== null && <p role="alert">{error}</p>}
    {plan !== null && <div className="a4-studio-plan">
      <p><strong>{plan.ready ? 'Prepared for unqualified studio trial only' : 'A4 studio trial blocked'}</strong></p>
      <p>Plan ID: <code>{plan.plan_id}</code></p>
      {plan.blocked_reasons.length > 0 && <ul>{plan.blocked_reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul>}
      <div className="show-kit-forge-table-scroll" tabIndex={0} role="region" aria-label="Exact A4 studio packets">
        <table className="show-kit-forge-cue-table a4-studio-table" aria-label="Prepared A4 studio send plan">
          <thead><tr><th>Track</th><th>Parameter</th><th>Control (CC)</th><th>Channel (wire 0-15)</th><th>Value</th></tr></thead>
          <tbody>{plan.send_plan.packets.map((packet, index) => <tr key={index}>
            <td>{packet.pad_id}</td><td>{packet.parameter}</td><td>{packet.control}</td><td>{packet.channel}</td><td>{packet.value}</td>
          </tr>)}</tbody>
        </table>
      </div>
      <label className="a4-studio-attestation"><input type="checkbox" checked={confirmed} disabled={!plan.ready || !available}
        onChange={(event) => setConfirmed(event.currentTarget.checked)} />
        I confirm sending only this exact A4 studio plan to {portName} now.
      </label>
      <button type="button" disabled={!canSend} onClick={() => {
        clearPlan();
        setReloaded(false);
        onSend({ type: 'show_bank_send_a4_studio_audition', send_plan_id: plan.plan_id,
          confirm: true, source_reloaded: true, acknowledge_unvalidated_hardware: true });
      }}>Send exact A4 studio plan</button>
    </div>}
  </>;
}
