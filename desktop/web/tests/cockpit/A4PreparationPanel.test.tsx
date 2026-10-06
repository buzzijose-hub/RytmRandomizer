import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { CockpitClientProvider } from '../../src/cockpit/context';
import { A4PreparationPanel } from '../../src/cockpit/showKitForge/A4PreparationPanel';
import { useCockpitStore } from '../../src/state';
import type { A4PreparationReport, CommandAck, ShowBank, ShowBankEntry } from '../../src/ws/protocol';
import { candidate, connectionFault, connectionListening, FakeCockpitClient, readyDualMachineStage } from './_fixtures';
import { forgeCaptures, forgeEntry, showBankState } from './showKitForgeFixture';

const bank = showBankState.banks[0] as ShowBank;
const report: A4PreparationReport = {
  schema_version: 'a4-preparation-v1', preparation_id: 'review-1', entry_id: forgeEntry.entry_id,
  candidate_id: forgeEntry.selected_candidate_id, device_id: 'analog_four_mk2',
  source_capture_id: 'source-a4', source_fingerprint: 'source', source_frame_sha256: 'source-sha',
  candidate_frame_sha256: 'candidate-sha', current_capture_fingerprint: 'source',
  current_capture_at: '2026-09-07T12:00:00Z', capture_after: '2026-09-07T11:00:00Z',
  checked_at: '2026-09-07T12:01:00Z', target_ids: [1], locked_ids: [], effective_ids: [1],
  output_port_name: 'A4 studio', recovery_slot: 20, source_reloaded: false,
  candidate_is_local: true, candidate_bytes_verified: true, current_source_verified: true,
  changes: [{ track_id: 1, parameter: 'filter1_frequency', before_raw_q8_8: 0,
    after_raw_q8_8: 4096, before_screen_value: '0', after_screen_value: '16', unpacked_offsets: [128, 129] }],
  blocked_reasons: ['source_reload_required', 'a4_hardware_audition_validation_pending',
    'a4_live_transport_mapping_unverified', 'persistent_kit_write_prohibited'],
  ready: false, hardware_send_validated: false, output_authority: 'offline-review-only',
};

function mount(fake: FakeCockpitClient, entry: ShowBankEntry = forgeEntry, disabled = false) {
  useCockpitStore.setState({ previewCandidate: candidate, connection: connectionListening, dualMachineStage: readyDualMachineStage });
  return render(<CockpitClientProvider client={fake.asClient()}>
    <A4PreparationPanel bank={bank} entry={entry} disabled={disabled} />
  </CockpitClientProvider>);
}

async function requestReview(): Promise<void> {
  await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Review A4 preparation' })); });
}

afterEach(() => act(() => useCockpitStore.getState().reset()));

describe('A4 preparation review', () => {
  it('dispatches only an explicit read-only review and displays blocked verified evidence', async () => {
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({ request_id: 'review', ok: true, a4_preparation: report });
    mount(fake);
    expect(fake.sent).toEqual([]);
    fireEvent.change(screen.getByLabelText('Intended A4 output name (review only)'), { target: { value: 'A4 studio' } });
    await requestReview();
    expect(fake.sent).toEqual([{ type: 'show_bank_list', a4_preparation: {
      bank_id: bank.bank_id, entry_id: forgeEntry.entry_id, expected_revision: bank.revision,
      output_port_name: 'A4 studio',
    } }]);
    expect(screen.getByRole('status')).toHaveTextContent('Candidate bytes verified against the immutable source. A4 SEND remains blocked.');
    expect(screen.getByRole('status')).toHaveTextContent('Track 1 filter1_frequency: 0 → 16');
    expect(screen.getByRole('status')).toHaveTextContent('source-sha');
    expect(screen.getByRole('status')).toHaveTextContent('live MIDI value mapping still needs separate validation');
    fireEvent.change(screen.getByLabelText('Intended A4 output name (review only)'), { target: { value: 'Different A4' } });
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('keeps incomplete evidence visibly blocked', async () => {
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({ request_id: 'review', ok: true, a4_preparation: {
      ...report, candidate_bytes_verified: false, candidate_frame_sha256: null, recovery_slot: null,
      changes: [], blocked_reasons: ['source_bytes_unavailable'],
    } });
    mount(fake);
    await requestReview();
    expect(fake.sent[0]).toMatchObject({ a4_preparation: { output_port_name: null } });
    expect(screen.getByRole('status')).toHaveTextContent('Candidate bytes are not verified.');
    expect(screen.getByRole('status')).toHaveTextContent('source slot not recorded');
    expect(screen.getByRole('status')).toHaveTextContent('Unavailable');
  });

  it('preserves native signed and fractional before/after values without granting live output authority', async () => {
    const nativeReport: A4PreparationReport = { ...report, changes: [
      { track_id: 2, parameter: 'filter2_frequency', before_encoded_native: 0, after_encoded_native: 1,
        native_encoding: 'unsigned-big-endian-q8.8', before_screen_value: '0', after_screen_value: '0.00390625', unpacked_offsets: [510, 511] },
      { track_id: 3, parameter: 'osc1_tune', before_encoded_native: 1, after_encoded_native: 257,
        native_encoding: 'centered-16384-pitch-preserve-fine', before_screen_value: '-64', after_screen_value: '-63', unpacked_offsets: [760, 761] },
    ] };
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({ request_id: 'native', ok: true, a4_preparation: nativeReport });
    mount(fake);
    await requestReview();
    const status = screen.getByRole('status');
    expect(status).toHaveTextContent('Track 2 filter2_frequency: 0 \u2192 0.00390625 Native 0 \u2192 1');
    expect(status).toHaveTextContent('Track 3 osc1_tune: -64 \u2192 -63 Native 1 \u2192 257');
    expect(status).toHaveTextContent('A4 SEND remains blocked.');
    expect(status).toHaveTextContent('still needs physical load, listening, save and recapture evidence');
    expect(fake.sent).toEqual([{ type: 'show_bank_list', a4_preparation: {
      bank_id: bank.bank_id, entry_id: forgeEntry.entry_id, expected_revision: bank.revision, output_port_name: null,
    } }]);
    expect(useCockpitStore.getState().sendPlan).toBeNull();
  });

  it('cannot review a selected candidate while its parent context is disabled', async () => {
    const fake = new FakeCockpitClient();
    mount(fake, forgeEntry, true);
    expect(screen.getByLabelText('Intended A4 output name (review only)')).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Review A4 preparation' })).toBeDisabled();
    await requestReview();
    expect(fake.sent).toEqual([]);
  });

  it.each(['bank', 'revision', 'cue', 'selection', 'disabled'] as const)(
    'revokes an existing preparation report after its %s prop changes', async (change) => {
      const fake = new FakeCockpitClient();
      fake.ackQueue.push({ request_id: 'review', ok: true, a4_preparation: report });
      const view = mount(fake);
      await requestReview();
      expect(screen.getByRole('status')).toBeInTheDocument();
      view.rerender(<CockpitClientProvider client={fake.asClient()}><A4PreparationPanel
        bank={{ ...bank, bank_id: change === 'bank' ? 'other-bank' : bank.bank_id,
          revision: change === 'revision' ? bank.revision + 1 : bank.revision }}
        entry={{ ...forgeEntry, entry_id: change === 'cue' ? 'other-cue' : forgeEntry.entry_id,
          selected_candidate_id: change === 'selection' ? 'candidate-two' : forgeEntry.selected_candidate_id }}
        disabled={change === 'disabled'}
      /></CockpitClientProvider>);
      expect(screen.queryByRole('status')).not.toBeInTheDocument();
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
      expect(fake.sent).toHaveLength(1);
    },
  );

  it.each(['accept', 'refuse', 'throw'] as const)(
    'keeps a newer review intact when an obsolete request later %s', async (outcome) => {
      const fake = new FakeCockpitClient();
      let settle!: (ack: CommandAck) => void;
      let fail!: (error: Error) => void;
      fake.responseQueue.push(new Promise((resolve, reject) => { settle = resolve; fail = reject; }));
      mount(fake);
      await requestReview();
      act(() => useCockpitStore.setState({ sessionGeneration: 2 }));
      fake.ackQueue.push({ request_id: 'current', ok: true, a4_preparation: { ...report, preparation_id: 'current-review' } });
      await requestReview();
      expect(screen.getByRole('status')).toHaveTextContent('current-review');
      await act(async () => {
        if (outcome === 'throw') fail(new Error('obsolete failure'));
        else settle({ request_id: 'old', ok: outcome === 'accept', message: 'obsolete failure', a4_preparation: report });
      });
      expect(screen.getByRole('status')).toHaveTextContent('current-review');
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Review A4 preparation' })).toBeEnabled();
      expect(fake.sent.every((command) => command.type === 'show_bank_list' && 'a4_preparation' in command)).toBe(true);
    },
  );

  it.each([false, true])('discards response after panel unmount (reject=%s)', async (reject) => {
    const fake = new FakeCockpitClient();
    let settle!: (ack: CommandAck) => void;
    let fail!: (error: Error) => void;
    fake.responseQueue.push(new Promise((resolve, refused) => { settle = resolve; fail = refused; }));
    const view = mount(fake);
    await requestReview();
    view.unmount();
    await act(async () => {
      if (reject) fail(new Error('obsolete failure'));
      else settle({ request_id: 'old', ok: true, a4_preparation: report });
    });
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(fake.sent).toHaveLength(1);
  });

  it('clears a refused review when the operator edits output intent', async () => {
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({ request_id: 'refused', ok: false });
    mount(fake);
    await requestReview();
    expect(screen.getByRole('alert')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Intended A4 output name (review only)'), { target: { value: 'A4 replacement intent' } });
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
    expect(fake.sent).toHaveLength(1);
  });

  it.each([true, false])('cannot review with disabled=%s and no selected candidate', async (disabled) => {
    const fake = new FakeCockpitClient();
    mount(fake, { ...forgeEntry, selected_candidate_id: null }, disabled);
    await requestReview();
    expect(fake.sent).toEqual([]);
  });

  it.each([
    undefined,
    { ...report, entry_id: 'other' },
    { ...report, candidate_id: 'other' },
    { ...report, ready: true },
    { ...report, hardware_send_validated: true },
    { ...report, output_authority: 'live' },
  ])('refuses mismatched or authority-claiming response %#', async (value) => {
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({ request_id: 'review', ok: true, a4_preparation: value as A4PreparationReport });
    mount(fake);
    await requestReview();
    expect(screen.getByRole('alert')).toHaveTextContent('did not match this blocked candidate review');
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it.each([undefined, 'Stale bank revision'])('shows a refused review: %s', async (error) => {
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({ request_id: 'review', ok: false, error });
    mount(fake);
    await requestReview();
    expect(screen.getByRole('alert')).toHaveTextContent(error ?? 'A4 preparation review was refused.');
  });

  it.each([new Error('Connection lost'), 'Connection lost'])('shows transport errors without output', async (error) => {
    const fake = new FakeCockpitClient();
    fake.nextRejection = error;
    mount(fake);
    await requestReview();
    expect(screen.getByRole('alert')).toHaveTextContent('Connection lost');
    expect(fake.sent).toHaveLength(1);
  });

  it('shows the server validation message for a rejected revision', async () => {
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({ request_id: 'review', ok: false, code: 'validation_error', message: 'show bank changed; refresh before retrying' });
    mount(fake);
    await requestReview();
    expect(screen.getByRole('alert')).toHaveTextContent('show bank changed; refresh before retrying');
  });

  it.each(['capture', 'scope', 'parameter_scope', 'session', 'candidate_reset', 'candidate_replaced', 'connection', 'capture_failed'] as const)('invalidates displayed evidence after a %s change', async (change) => {
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({ request_id: 'review', ok: true, a4_preparation: report });
    mount(fake);
    await requestReview();
    expect(screen.getByRole('status')).toBeInTheDocument();
    act(() => {
      if (change === 'capture') useCockpitStore.setState({ kitCaptures: forgeCaptures });
      if (change === 'scope') useCockpitStore.setState({ a4TrackLocks: [1] });
      if (change === 'parameter_scope') useCockpitStore.getState().replaceMutationParameters(null, []);
      if (change === 'session') useCockpitStore.setState({ sessionGeneration: 2 });
      if (change === 'candidate_reset') useCockpitStore.getState().setPreviewCandidate(null);
      if (change === 'candidate_replaced') useCockpitStore.getState().setPreviewCandidate({ ...candidate, candidate_id: 'other' });
      if (change === 'connection') useCockpitStore.getState().setConnection(connectionFault);
      if (change === 'capture_failed') useCockpitStore.setState({ dualMachineStage: {
        ...readyDualMachineStage, analog_four: { ...readyDualMachineStage.analog_four, last_error: "mock_a4_capture_failed" },
      } });
    });
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it.each([
    ['scope', false], ['parameter_scope', false], ['candidate', false], ['connection', false], ['stage', false], ['candidate', true],
  ] as const)('discards a stale in-flight response after %s changes (reject=%s)', async (change, reject) => {
    const fake = new FakeCockpitClient();
    let resolve!: (ack: CommandAck) => void;
    let fail!: (error: Error) => void;
    fake.responseQueue.push(new Promise((success, failure) => { resolve = success; fail = failure; }));
    mount(fake);
    await requestReview();
    expect(screen.getByRole('button', { name: 'Reviewing A4 candidate…' })).toBeDisabled();
    act(() => {
      if (change === 'scope') useCockpitStore.setState({ a4TrackTargets: [2] });
      if (change === 'parameter_scope') useCockpitStore.getState().replaceMutationParameters(null, []);
      if (change === 'candidate') useCockpitStore.getState().setPreviewCandidate(null);
      if (change === 'connection') useCockpitStore.getState().setConnection(connectionFault);
      if (change === 'stage') useCockpitStore.setState({ dualMachineStage: null });
    });
    await act(async () => {
      if (reject) fail(new Error('Old response'));
      else resolve({ request_id: 'review', ok: true, a4_preparation: report });
    });
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Review A4 preparation' })).toBeEnabled();
  });
});
