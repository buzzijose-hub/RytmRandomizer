import { useEffect, useRef, useState } from 'react';

import { useCockpitStore } from '../../state';
import type { A4PreparationBlocker, A4PreparationReport, ShowBank, ShowBankEntry } from '../../ws/protocol';
import { useCockpitClient } from '../context';

const BLOCKER_LABELS: Readonly<Record<A4PreparationBlocker, string>> = {
  session_unavailable: 'Reconnect and refresh the current session.',
  candidate_not_selected: 'Select this candidate again in the active cue.',
  candidate_not_local: 'Imported evidence is catalog-only. Capture fresh sources in this session.',
  source_bytes_unavailable: 'Retain or recapture the exact A4 source bytes.',
  source_bytes_invalid: 'The retained source failed verification. Preserve it and recapture the source.',
  candidate_bytes_unavailable: 'Regenerate and retain the selected A4 candidate.',
  candidate_bytes_invalid: 'The candidate failed canonical byte verification. Regenerate it from the source.',
  scope_changed: 'Track targets or locks changed. Generate and select a candidate for the current scope.',
  no_a4_changes: 'This candidate contains no A4 changes.',
  source_reload_required: 'A future live audition must require an explicit manual source reload.',
  current_capture_required: 'Capture the current A4 source kit.',
  current_capture_invalid: 'The current capture failed verification. Capture it again.',
  current_capture_stale: 'Capture the source again after the latest session change.',
  current_source_mismatch: 'The current A4 kit differs from the immutable source.',
  output_port_intent_required: 'Record the exact intended A4 output name for review.',
  recovery_slot_required: 'Record a saved source slot for manual recovery.',
  a4_hardware_audition_validation_pending: 'The generated scratch kit still needs physical load, listening, save and recapture evidence.',
  a4_live_transport_mapping_unverified: 'The live MIDI value mapping still needs separate validation.',
  persistent_kit_write_prohibited: 'Cockpit cannot perform a persistent KIT write or restore.',
};

interface Props { bank: ShowBank; entry: ShowBankEntry; disabled: boolean }

/** Changing any relevant source/session/scope invalidates even an in-flight review. */
export function A4PreparationPanel(props: Props): JSX.Element {
  const captures = useCockpitStore((state) => state.kitCaptures);
  const targets = useCockpitStore((state) => state.a4TrackTargets);
  const locks = useCockpitStore((state) => state.a4TrackLocks);
  const generation = useCockpitStore((state) => state.sessionGeneration);
  const currentCandidate = useCockpitStore((state) => state.previewCandidate);
  const connection = useCockpitStore((state) => state.connection);
  const stage = useCockpitStore((state) => state.dualMachineStage);
  const key = JSON.stringify([
    props.bank.bank_id, props.bank.revision, props.entry.entry_id,
    props.entry.selected_candidate_id, props.disabled, captures, targets, locks, generation,
    currentCandidate?.candidate_id, connection, stage,
  ]);
  return <PreparationRequest key={key} {...props} />;
}

function PreparationRequest({ bank, entry, disabled }: Props): JSX.Element {
  const client = useCockpitClient();
  const [portName, setPortName] = useState('');
  const [report, setReport] = useState<A4PreparationReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const request = useRef(0);
  useEffect(() => () => { request.current += 1; }, []);

  async function review(): Promise<void> {
    const serial = ++request.current;
    setBusy(true);
    setReport(null);
    setError(null);
    try {
      const ack = await client.send({
        type: 'show_bank_list',
        a4_preparation: {
          bank_id: bank.bank_id, entry_id: entry.entry_id,
          expected_revision: bank.revision, output_port_name: portName === '' ? null : portName,
        },
      });
      if (request.current !== serial) return;
      if (!ack.ok) throw new Error(ack.error ?? ack.message ?? 'A4 preparation review was refused.');
      const result = ack.a4_preparation;
      if (result === undefined || result.entry_id !== entry.entry_id ||
          result.candidate_id !== entry.selected_candidate_id || result.ready !== false ||
          result.hardware_send_validated !== false || result.output_authority !== 'offline-review-only') {
        throw new Error('A4 preparation response did not match this blocked candidate review.');
      }
      setReport(result);
    } catch (failure) {
      if (request.current === serial) setError(failure instanceof Error ? failure.message : String(failure));
    } finally {
      if (request.current === serial) setBusy(false);
    }
  }

  return (
    <section className="show-kit-forge-section" aria-label="A4 audition preparation">
      <h4>A4 audition preparation — output blocked</h4>
      <p>Review the selected candidate and recovery evidence. This action does not open a port or send MIDI.</p>
      <label>Intended A4 output name (review only)
        <input value={portName} maxLength={256} disabled={disabled || busy}
          onChange={(event) => { setPortName(event.currentTarget.value); setReport(null); setError(null); }} />
      </label>
      <button type="button" disabled={disabled || busy || entry.selected_candidate_id === null}
        onClick={() => void review()}>{busy ? 'Reviewing A4 candidate…' : 'Review A4 preparation'}</button>
      {error !== null && <p role="alert">{error}</p>}
      {report !== null && <div role="status">
        <p>{report.candidate_bytes_verified ? 'Candidate bytes verified against the immutable source.' : 'Candidate bytes are not verified.'} A4 SEND remains blocked.</p>
        <ul>{report.blocked_reasons.map((reason) => <li key={reason}>{BLOCKER_LABELS[reason]}</li>)}</ul>
        <p>Manual recovery: A4 source slot {report.recovery_slot ?? 'not recorded'}.</p>
        <ul>{report.changes.map((change) => <li key={change.track_id}>
          Track {change.track_id} Filter 1 Frequency: {change.before_screen_value} → {change.after_screen_value}
        </li>)}</ul>
        <details><summary>Candidate verification details</summary>
          <dl>
            <dt>Review ID</dt><dd><code>{report.preparation_id}</code></dd>
            <dt>Source frame SHA256</dt><dd><code>{report.source_frame_sha256}</code></dd>
            <dt>Candidate frame SHA256</dt><dd><code>{report.candidate_frame_sha256 ?? 'Unavailable'}</code></dd>
            <dt>Checked at</dt><dd>{report.checked_at}</dd>
          </dl>
        </details>
      </div>}
    </section>
  );
}
