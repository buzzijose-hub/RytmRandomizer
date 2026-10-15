import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { CockpitClientProvider } from '../../src/cockpit/context';
import { A4StudioAuditionPanel } from '../../src/cockpit/showKitForge/A4StudioAuditionPanel';
import { bindClientToStore, useCockpitStore, type SessionStatus } from '../../src/state';
import type { A4StudioAuditionPlan, CommandAck, ShowBank, ShowBankEntry } from '../../src/ws/protocol';
import { candidate, connectionFault, connectionListening, FakeCockpitClient, sessionMock } from './_fixtures';
import { forgeCaptures, forgeEntry, showBankState } from './showKitForgeFixture';
import { pythonStudioPlan, studioPlan, studioPort } from './a4StudioAuditionFixture';

const bank = showBankState.banks[0]!;
const armSession: SessionStatus = { ...sessionMock, armed: true, armed_device_id: 'analog_four_mk2', midi_port: studioPort };
const prepareLabel = 'Prepare A4 studio plan';
const armLabel = 'Arm A4 studio output';
const sendLabel = 'Send exact A4 studio plan';

function secret(value: string | null): void {
  const target = window as { __RYTM_RAND_ARM_SECRET__?: string };
  delete target.__RYTM_RAND_ARM_SECRET__;
  window.localStorage.removeItem('rytm-rand-arm-secret');
  if (value !== null) target.__RYTM_RAND_ARM_SECRET__ = value;
}

function panel(fake: FakeCockpitClient, selectedBank: ShowBank = bank, entry: ShowBankEntry = forgeEntry, disabled = false) {
  return <CockpitClientProvider client={fake.asClient()}>
    <A4StudioAuditionPanel bank={selectedBank} entry={entry} disabled={disabled} />
  </CockpitClientProvider>;
}

function mount(fake = new FakeCockpitClient()) {
  return { fake, view: render(panel(fake)) };
}

function routing(channels = [2, 4, 6, 8]): void {
  fireEvent.change(screen.getByRole('combobox', { name: 'A4 USB output' }), { target: { value: studioPort } });
  channels.forEach((value, i) => fireEvent.change(screen.getByRole('spinbutton', { name: `A4 track ${i + 1} channel (1-16)` }), { target: { value } }));
}

function attest(): void {
  fireEvent.click(screen.getByRole('checkbox', { name: /I acknowledge this A4 hardware/ }));
  fireEvent.click(screen.getByRole('checkbox', { name: /I manually reloaded/ }));
}

async function click(label: string): Promise<void> {
  await act(async () => { fireEvent.click(screen.getByRole('button', { name: label })); });
}

async function prepare(fake: FakeCockpitClient, plan: A4StudioAuditionPlan = studioPlan): Promise<void> {
  fake.ackQueue.push({ request_id: 'prepare', ok: true, a4_studio_plan: plan });
  routing(); attest(); await click(prepareLabel);
}

beforeEach(() => {
  secret('studio-secret');
  useCockpitStore.setState({
    connectionStatus: 'connected', connection: { ...connectionListening, available_outputs: [studioPort, 'Rytm OUT'] },
    sessionStatus: sessionMock, sessionStatusStale: false, sessionGeneration: 1,
    previewCandidate: candidate, kitCaptures: forgeCaptures,
  });
});
afterEach(() => { secret(null); act(() => useCockpitStore.getState().reset()); });

describe('bounded A4 studio audition', () => {
  it('starts with empty nonpersistent routing, passive commands and visible recovery/authority limits', () => {
    const { fake } = mount();
    expect(screen.getByRole('region', { name: 'A4 studio audition' })).toHaveTextContent('source slot 22');
    expect(screen.getByRole('region', { name: 'A4 studio audition' })).toHaveTextContent('General A4/BOTH stage output remains blocked');
    expect(screen.getByRole('combobox')).toHaveValue('');
    screen.getAllByRole('spinbutton').forEach((input) => expect(input).toHaveValue(null));
    expect(screen.getByRole('button', { name: armLabel })).toBeDisabled();
    expect(screen.getByRole('button', { name: prepareLabel })).toBeDisabled();
    expect(screen.queryByRole('button', { name: sendLabel })).not.toBeInTheDocument();
    expect(fake.sent).toEqual([]);
  });

  it.each([[2, 2, 6, 8], [0, 4, 6, 8], [17, 4, 6, 8], [1.5, 4, 6, 8]])('refuses duplicate or invalid channels %j', (...channels) => {
    mount(); routing(channels); attest();
    expect(screen.getByRole('button', { name: armLabel })).toBeDisabled();
    expect(screen.getByRole('button', { name: prepareLabel })).toBeDisabled();
    if (channels[0] === 2) expect(screen.getByRole('alert')).toHaveTextContent('must be distinct');
    else expect(screen.getByText('Enter four integer channels from 1 to 16.')).toBeInTheDocument();
  });

  it('rejects duplicate exact outputs and removed selected ports without auto-selecting another', () => {
    mount(); routing(); attest();
    act(() => useCockpitStore.setState({ connection: { ...connectionListening, available_outputs: [studioPort, studioPort] } }));
    expect(screen.getByRole('alert')).toHaveTextContent('exactly once');
    expect(screen.getByRole('option', { name: studioPort })).toBeDisabled();
    expect(screen.getByRole('button', { name: prepareLabel })).toBeDisabled();
    act(() => useCockpitStore.setState({ connection: { ...connectionListening, available_outputs: ['Rytm OUT'] } }));
    expect(screen.getByRole('alert')).toHaveTextContent('exactly once');
    expect(screen.getByRole('button', { name: armLabel })).toBeDisabled();
  });

  it.each(['disconnected', 'no-session', 'stale', 'no-connection', 'disabled', 'no-candidate'] as const)('cannot act with %s context', async (context) => {
    const fake = new FakeCockpitClient();
    if (context === 'disconnected') useCockpitStore.setState({ connectionStatus: 'closed' });
    if (context === 'no-session') useCockpitStore.setState({ sessionStatus: null });
    if (context === 'stale') useCockpitStore.setState({ sessionStatusStale: true });
    if (context === 'no-connection') useCockpitStore.setState({ connection: null });
    render(panel(fake, bank, context === 'no-candidate' ? { ...forgeEntry, selected_candidate_id: null } : forgeEntry, context === 'disabled'));
    routing(); attest(); await click(prepareLabel);
    expect(fake.sent).toEqual([]);
    if (context === 'no-connection') expect(screen.getByText('No enumerated MIDI outputs available.')).toBeInTheDocument();
  });

  it('keeps a missing recovery slot honest', () => {
    render(panel(new FakeCockpitClient(), bank, { ...forgeEntry, analog_four_source: { ...forgeEntry.analog_four_source, hardware_slot: null } }));
    expect(screen.getByRole('region', { name: 'A4 studio audition' })).toHaveTextContent('source slot not recorded');
  });

  it('prepares offline without ARM, exposing exact packets without touching the generic send plan', async () => {
    const { fake } = mount(); await prepare(fake);
    expect(fake.sent).toEqual([{
      type: 'show_bank_prepare_a4_studio_audition', bank_id: bank.bank_id, entry_id: forgeEntry.entry_id,
      expected_revision: bank.revision, output_port_name: studioPort, track_channels: [2, 4, 6, 8],
      source_reloaded: true, acknowledge_unvalidated_hardware: true,
    }]);
    expect(screen.getByText(studioPlan.plan_id)).toBeInTheDocument();
    const cells = within(screen.getByRole('table', { name: 'Prepared A4 studio send plan' })).getAllByRole('cell');
    expect(cells.map((cell) => cell.textContent)).toEqual(['1', 'osc1_level', '69', '1', '100']);
    expect(screen.getByRole('button', { name: sendLabel })).toBeDisabled();
    expect(useCockpitStore.getState().sendPlan).toBeNull();
  });

  it('consumes the unchanged Python-produced DTO through client.send and renders its exact CC7 wire packet', async () => {
    const fake = new FakeCockpitClient();
    render(panel(fake, { ...bank, bank_id: pythonStudioPlan.bank_id, revision: pythonStudioPlan.bank_revision },
      { ...forgeEntry, entry_id: pythonStudioPlan.entry_id, selected_candidate_id: pythonStudioPlan.candidate_id }));
    await prepare(fake, pythonStudioPlan);
    expect(fake.sent[0]).toMatchObject({ type: 'show_bank_prepare_a4_studio_audition',
      bank_id: 'bank-boundary', entry_id: 'cue-source', expected_revision: 5,
      output_port_name: pythonStudioPlan.routing.output_port_name, track_channels: pythonStudioPlan.routing.track_channels });
    expect(screen.getByText(pythonStudioPlan.plan_id)).toBeInTheDocument();
    const table = screen.getByRole('table', { name: 'Prepared A4 studio send plan' });
    expect(within(table).getAllByRole('cell').map((cell) => cell.textContent)).toEqual(['1', 'osc1_level', '69', '1', '100']);
    expect(pythonStudioPlan.hardware_send_validated).toBe(false);
    expect(pythonStudioPlan.output_authority).toBe('studio-ram-only-unqualified');
    expect(screen.getByRole('button', { name: sendLabel })).toBeDisabled();
  });

  it('requires both attestations before prepare and the per-action checkbox after prepare', async () => {
    useCockpitStore.setState({ sessionStatus: armSession });
    const { fake } = mount(); routing();
    fireEvent.click(screen.getByRole('checkbox', { name: /I acknowledge/ }));
    expect(screen.getByRole('button', { name: prepareLabel })).toBeDisabled();
    fireEvent.click(screen.getByRole('checkbox', { name: /I manually reloaded/ }));
    fake.ackQueue.push({ request_id: 'prepare', ok: true, a4_studio_plan: studioPlan });
    await click(prepareLabel);
    expect(screen.getByRole('button', { name: sendLabel })).toBeDisabled();
    fireEvent.click(screen.getByRole('checkbox', { name: /I confirm sending/ }));
    expect(screen.getByRole('button', { name: sendLabel })).toBeEnabled();
    fireEvent.click(screen.getByRole('checkbox', { name: /I confirm sending/ }));
    expect(screen.getByRole('button', { name: sendLabel })).toBeDisabled();
  });

  it('arms only explicitly acknowledged A4 with the exact output and delivered secret', async () => {
    const { fake } = mount(); routing(); attest();
    await click(armLabel);
    expect(fake.sent).toEqual([{ type: 'arm', device_id: 'analog_four_mk2', acknowledge_unvalidated_hardware: true,
      arm_token: 'studio-secret', port_name: studioPort, confirm: true }]);
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });

  it('refuses ARM without a secret, including loss between rendering and clicking', async () => {
    const { fake, view } = mount(); routing(); attest();
    secret(null); await click(armLabel);
    expect(screen.getByRole('alert')).toHaveTextContent('Arm secret unavailable');
    expect(fake.sent).toEqual([]);
    view.unmount(); mount();
    expect(screen.getByRole('button', { name: armLabel })).toBeDisabled();
    expect(screen.getByText(/Arm secret unavailable. Relaunch the desktop app to arm output/)).toBeInTheDocument();
  });

  it.each([
    { ...armSession, armed_device_id: undefined },
    { ...armSession, midi_port: 'Rytm OUT' },
    { ...armSession, armed: false },
  ])('never treats another device, port or passive session as A4 output authority: %j', async (session) => {
    useCockpitStore.setState({ sessionStatus: session });
    const { fake } = mount(); await prepare(fake);
    fireEvent.click(screen.getByRole('checkbox', { name: /I confirm sending/ }));
    expect(screen.getByRole('button', { name: sendLabel })).toBeDisabled();
    await click(sendLabel); expect(fake.sent).toHaveLength(1);
  });

  it.each(['sent', 'partial', 'refused'])('reports %s counts, consumes the plan and requires another reload without promoting readiness', async (status) => {
    useCockpitStore.setState({ sessionStatus: armSession });
    const { fake } = mount(); await prepare(fake);
    fireEvent.click(screen.getByRole('checkbox', { name: /I confirm sending/ }));
    fake.ackQueue.push({ request_id: 'send', ok: true, a4_studio_outcome: { status, sent_count: status === 'refused' ? 0 : 1, expected_count: 1, reason: 'Software result only.' } });
    await click(sendLabel);
    expect(fake.sent[1]).toEqual({ type: 'show_bank_send_a4_studio_audition', send_plan_id: studioPlan.plan_id,
      confirm: true, source_reloaded: true, acknowledge_unvalidated_hardware: true });
    expect(screen.getByRole('status')).toHaveTextContent(`A4 studio outcome: ${status}`);
    expect(screen.getByText(/No hardware qualification or show readiness granted/)).toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: /I manually reloaded/ })).not.toBeChecked();
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: prepareLabel })).toBeDisabled();
    expect(useCockpitStore.getState().showBank).toBeNull();
    expect(useCockpitStore.getState().sendPlan).toBeNull();
  });

  it('displays missing outcomes as unknown hardware state and consumes a failed send attempt', async () => {
    useCockpitStore.setState({ sessionStatus: armSession });
    const { fake } = mount(); await prepare(fake);
    fireEvent.click(screen.getByRole('checkbox', { name: /I confirm sending/ }));
    await click(sendLabel);
    expect(screen.getByRole('alert')).toHaveTextContent('Hardware state is unknown');
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: /I manually reloaded/ })).not.toBeChecked();
  });

  it('retains reported partial counts even when SEND is refused and never offers retry without a fresh reload', async () => {
    useCockpitStore.setState({ sessionStatus: armSession });
    const { fake } = mount(); await prepare(fake);
    fireEvent.click(screen.getByRole('checkbox', { name: /I confirm sending/ }));
    fake.ackQueue.push({ request_id: 'partial', ok: false, message: 'Output auto-disarmed.',
      a4_studio_outcome: { status: 'partial', sent_count: 1, expected_count: 2, reason: 'Output failed.' } });
    await click(sendLabel);
    expect(screen.getByRole('status')).toHaveTextContent('partial. Sent 1 of 2');
    expect(screen.getByRole('alert')).toHaveTextContent('Output auto-disarmed');
    expect(screen.getByRole('button', { name: prepareLabel })).toBeDisabled();
    expect(screen.queryByRole('button', { name: sendLabel })).not.toBeInTheDocument();
  });

  it('retains interruption counts across readiness revocation, disarm and disconnect while never restoring authority', async () => {
    useCockpitStore.setState({ sessionStatus: armSession });
    const { fake, view } = mount(); await prepare(fake);
    let settle!: (ack: CommandAck) => void;
    fake.responseQueue.push(new Promise((resolve) => { settle = resolve; }));
    fireEvent.click(screen.getByRole('checkbox', { name: /I confirm sending/ }));
    await click(sendLabel);
    expect(screen.getByRole('status')).toHaveTextContent('send pending');
    expect(screen.getByRole('combobox')).toBeDisabled();
    expect(screen.getByRole('button', { name: prepareLabel })).toBeDisabled();
    await click('Disarm output');
    expect(fake.sent.at(-1)).toEqual({ type: 'disarm' });
    act(() => useCockpitStore.setState({ sessionStatus: sessionMock, connectionStatus: 'closed', sessionStatusStale: true }));
    view.rerender(panel(fake, { ...bank, revision: bank.revision + 1 }));
    await act(async () => settle({ request_id: 'interrupted', ok: true,
      a4_studio_outcome: { status: 'interrupted', sent_count: 1, expected_count: 3, reason: 'disarmed' } }));
    expect(screen.getByRole('status')).toHaveTextContent('interrupted. Sent 1 of 3');
    expect(screen.getByText(studioPlan.plan_id)).toBeInTheDocument();
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: /I manually reloaded/ })).not.toBeChecked();
  });

  it.each([
    { request_id: 'send', ok: false, error: 'studio_send_refused', message: 'other' },
    { request_id: 'send', ok: false, message: 'Send refused' },
    { request_id: 'send', ok: false },
    new Error('Send transport failure'),
    'Send transport unavailable',
  ])('retains SEND refusal/transport errors without granting retry (%#)', async (response) => {
    useCockpitStore.setState({ sessionStatus: armSession });
    const { fake } = mount(); await prepare(fake);
    fireEvent.click(screen.getByRole('checkbox', { name: /I confirm sending/ }));
    if (typeof response === 'string' || response instanceof Error) fake.nextRejection = response;
    else fake.ackQueue.push(response);
    await click(sendLabel);
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: prepareLabel })).toBeDisabled();
  });

  it.each([true, false])('ignores SEND outcome/rejection after the whole panel unmounts (reject=%s)', async (reject) => {
    useCockpitStore.setState({ sessionStatus: armSession });
    const { fake, view } = mount(); await prepare(fake);
    let settle!: (ack: CommandAck) => void; let fail!: (reason: Error) => void;
    fake.responseQueue.push(new Promise((resolve, refused) => { settle = resolve; fail = refused; }));
    fireEvent.click(screen.getByRole('checkbox', { name: /I confirm sending/ }));
    await click(sendLabel); view.unmount();
    await act(async () => {
      if (reject) fail(new Error('unmounted'));
      else settle({ request_id: 'old-send', ok: true, a4_studio_outcome: { status: 'complete', sent_count: 1, expected_count: 1, reason: '' } });
    });
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('retains blocked whole-plan reasons with no executable subset', async () => {
    const { fake } = mount(); await prepare(fake, { ...studioPlan, ready: false, blocked_reasons: ['fractional_conversion_unverified'],
      send_plan: { ...studioPlan.send_plan, ready: false, packets: [], blocked_reasons: ['unsupported_control_changed'] } });
    expect(screen.getByText('A4 studio trial blocked')).toBeInTheDocument();
    expect(screen.getByText('fractional_conversion_unverified')).toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: /I confirm sending/ })).toBeDisabled();
    expect(screen.getByRole('button', { name: sendLabel })).toBeDisabled();
  });

  it.each([
    undefined,
    { ...studioPlan, bank_id: 'other' },
    { ...studioPlan, bank_revision: 999 },
    { ...studioPlan, entry_id: 'other' },
    { ...studioPlan, candidate_id: 'other' },
    { ...studioPlan, routing: { ...studioPlan.routing, output_port_name: 'other' } },
    { ...studioPlan, routing: { ...studioPlan.routing, track_channels: [1, 2, 3, 4] } },
    { ...studioPlan, hardware_send_validated: true },
    { ...studioPlan, persistent_write: true },
    { ...studioPlan, output_authority: 'offline-review-only' },
    { ...studioPlan, plan_id: '' },
    { ...studioPlan, send_plan: { ...studioPlan.send_plan, plan_id: 'other' } },
    { ...studioPlan, send_plan: { ...studioPlan.send_plan, candidate_id: 'other' } },
    { ...studioPlan, send_plan: { ...studioPlan.send_plan, ready: false } },
    { ...studioPlan, blocked_reasons: ['blocked'] },
    { ...studioPlan, ready: false, blocked_reasons: ['blocked'], send_plan: { ...studioPlan.send_plan, ready: false } },
  ])('rejects mismatched plan/authority rather than displaying executable evidence (%#)', async (value) => {
    const { fake } = mount(); routing(); attest();
    fake.ackQueue.push({ request_id: 'bad', ok: true, a4_studio_plan: value as A4StudioAuditionPlan });
    await click(prepareLabel);
    expect(screen.getByRole('alert')).toHaveTextContent('did not match');
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });

  it.each([
    { request_id: 'refuse', ok: false, error: 'studio_refused', message: 'other' },
    { request_id: 'refuse', ok: false, message: 'Refused studio request' },
    { request_id: 'refuse', ok: false },
    new Error('Request unavailable'),
    'Request transport unavailable',
  ])('shows categorical command errors and transport failures (%#)', async (response) => {
    const { fake } = mount(); routing(); attest();
    if (typeof response === 'string' || response instanceof Error) fake.nextRejection = response;
    else fake.ackQueue.push(response);
    await click(prepareLabel);
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: prepareLabel })).toBeEnabled();
  });

  it.each(['port', 'channel', 'acknowledgment', 'reload'] as const)('clears a displayed plan immediately when %s changes', async (change) => {
    const { fake } = mount(); await prepare(fake);
    if (change === 'port') fireEvent.change(screen.getByRole('combobox'), { target: { value: 'Rytm OUT' } });
    if (change === 'channel') fireEvent.change(screen.getAllByRole('spinbutton')[0]!, { target: { value: 3 } });
    if (change === 'acknowledgment') fireEvent.click(screen.getByRole('checkbox', { name: /I acknowledge/ }));
    if (change === 'reload') fireEvent.click(screen.getByRole('checkbox', { name: /I manually reloaded/ }));
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
    expect(fake.sent).toHaveLength(1);
  });

  it.each(['bank', 'revision', 'entry', 'selection', 'disabled'] as const)('revokes prepared evidence on %s prop changes', async (change) => {
    const { fake, view } = mount(); await prepare(fake);
    view.rerender(panel(fake,
      { ...bank, bank_id: change === 'bank' ? 'other-bank' : bank.bank_id, revision: bank.revision + (change === 'revision' ? 1 : 0) },
      { ...forgeEntry, entry_id: change === 'entry' ? 'other-entry' : forgeEntry.entry_id, selected_candidate_id: change === 'selection' ? null : forgeEntry.selected_candidate_id },
      change === 'disabled'));
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });

  it.each(['capture', 'target', 'lock', 'parameters', 'generation', 'status', 'session', 'stale', 'connection', 'candidate', 'stage'] as const)('revokes displayed evidence after %s changes', async (change) => {
    const { fake } = mount(); await prepare(fake);
    act(() => {
      if (change === 'capture') useCockpitStore.setState({ kitCaptures: [] });
      if (change === 'target') useCockpitStore.setState({ a4TrackTargets: [2] });
      if (change === 'lock') useCockpitStore.setState({ a4TrackLocks: [1] });
      if (change === 'parameters') useCockpitStore.setState({ mutationContextRevision: 3 });
      if (change === 'generation') useCockpitStore.setState({ sessionGeneration: 8 });
      if (change === 'status') useCockpitStore.setState({ connectionStatus: 'closed' });
      if (change === 'session') useCockpitStore.setState({ sessionStatus: armSession });
      if (change === 'stale') useCockpitStore.setState({ sessionStatusStale: true });
      if (change === 'connection') useCockpitStore.setState({ connection: connectionFault });
      if (change === 'candidate') useCockpitStore.setState({ previewCandidate: null });
      if (change === 'stage') useCockpitStore.setState({ dualMachineStage: { ...useCockpitStore.getState().dualMachineStage!, revision: 5 } });
    });
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: /I manually reloaded/ })).not.toBeChecked();
  });

  it.each(['accept', 'refuse', 'throw'] as const)('ignores late obsolete %s ACKs after routing changes, preserving a newer plan', async (outcome) => {
    const { fake } = mount(); routing(); attest();
    let settle!: (ack: CommandAck) => void; let fail!: (reason: Error) => void;
    fake.responseQueue.push(new Promise((resolve, reject) => { settle = resolve; fail = reject; }));
    await click(prepareLabel);
    expect(screen.getByRole('status')).toHaveTextContent('pending');
    fireEvent.change(screen.getAllByRole('spinbutton')[0]!, { target: { value: 3 } });
    fireEvent.change(screen.getAllByRole('spinbutton')[0]!, { target: { value: 2 } });
    attest(); fake.ackQueue.push({ request_id: 'new', ok: true, a4_studio_plan: studioPlan });
    await click(prepareLabel);
    await act(async () => {
      if (outcome === 'throw') fail(new Error('obsolete rejection'));
      else settle({ request_id: 'old', ok: outcome === 'accept', a4_studio_plan: { ...studioPlan, plan_id: 'obsolete' } });
    });
    expect(screen.getByText(studioPlan.plan_id)).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it.each([true, false])('ignores late ACK or rejection after unmount (reject=%s)', async (reject) => {
    const { fake, view } = mount(); routing(); attest();
    let settle!: (ack: CommandAck) => void; let fail!: (reason: Error) => void;
    fake.responseQueue.push(new Promise((resolve, refused) => { settle = resolve; fail = refused; }));
    await click(prepareLabel); view.unmount();
    await act(async () => {
      if (reject) fail(new Error('unmounted'));
      else settle({ request_id: 'old', ok: true, a4_studio_plan: studioPlan });
    });
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });

  it('keeps disarm one click away even during a pending action and rejects its obsolete ACK', async () => {
    const { fake } = mount(); routing(); attest();
    let settle!: (ack: CommandAck) => void;
    fake.responseQueue.push(new Promise((resolve) => { settle = resolve; }));
    await click(prepareLabel); await click('Disarm output');
    expect(fake.sent.at(-1)).toEqual({ type: 'disarm' });
    expect(screen.getByRole('checkbox', { name: /I manually reloaded/ })).not.toBeChecked();
    await act(async () => settle({ request_id: 'obsolete', ok: true, a4_studio_plan: studioPlan }));
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });

  it('forwards A4 armed identity through the actual client binding and removes it for ordinary Rytm/passive events', () => {
    const fake = new FakeCockpitClient();
    const unbind = bindClientToStore(fake.asClient());
    act(() => fake.emitEvent({ type: 'session_status', ...armSession }));
    expect(useCockpitStore.getState().sessionStatus?.armed_device_id).toBe('analog_four_mk2');
    act(() => fake.emitEvent({ type: 'session_status', ...sessionMock }));
    expect(useCockpitStore.getState().sessionStatus).not.toHaveProperty('armed_device_id');
    unbind();
  });
});
