import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { StrictMode } from 'react';
import { afterEach, describe, expect, it } from 'vitest';

import { CockpitClientProvider } from '../../src/cockpit/context';
import { ShowKitForgePanel } from '../../src/cockpit/showKitForge/ShowKitForgePanel';
import { useCockpitStore } from '../../src/state';
import type { Command, CommandAck, ShowBankEntry, ShowBankState, ShowDepthPresets } from '../../src/ws/protocol';

import {
  candidate,
  FakeCockpitClient,
  profile,
  readyDualMachineStage,
  sendPlan,
  sessionLive,
  sessionMock,
} from './_fixtures';
import { forgeCaptures, forgeEntry, readyEntry, showBankState } from './showKitForgeFixture';

function mount(fake: FakeCockpitClient, state: ShowBankState | null = showBankState): ReturnType<typeof render> {
  useCockpitStore.setState({
    showBank: state,
    showBankStale: false,
    kitCaptures: forgeCaptures,
    profile,
    connectionStatus: 'connected',
  });
  useCockpitStore.getState().setSessionStatus(sessionLive);
  return render(
    <CockpitClientProvider client={fake.asClient()}>
      <ShowKitForgePanel />
    </CockpitClientProvider>,
  );
}

async function waitForCommand(fake: FakeCockpitClient, type: Command['type']): Promise<Command> {
  await waitFor(() => expect(fake.sent.some((command) => command.type === type)).toBe(true));
  const matches = fake.sent.filter((command) => command.type === type);
  return matches[matches.length - 1] as Command;
}

afterEach(() => {
  useCockpitStore.getState().reset();
});

describe('ShowKitForgePanel', () => {
  it('waits for authenticated session hydration before loading and creating a bank', async () => {
    const fake = new FakeCockpitClient();
    useCockpitStore.setState({ connectionStatus: 'closed', showBank: null, kitCaptures: [] });
    render(
      <CockpitClientProvider client={fake.asClient()}>
        <ShowKitForgePanel />
      </CockpitClientProvider>,
    );

    expect(fake.sent).toEqual([]);
    expect(screen.getByText(/Last known server state is read-only/)).toBeInTheDocument();
    expect(screen.getByText('Waiting for a bank')).toBeInTheDocument();
    expect(screen.queryByText('Warehouse Set')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Create show bank' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Refresh from server' })).toBeDisabled();

    act(() => useCockpitStore.getState().setConnectionStatus('connecting'));
    expect(fake.sent).toEqual([]);
    act(() => useCockpitStore.getState().setConnectionStatus('connected'));
    expect(fake.sent).toEqual([]);
    expect(screen.getByRole('button', { name: 'Refresh from server' })).toBeDisabled();
    act(() => useCockpitStore.getState().setSessionStatus(sessionLive));
    await waitForCommand(fake, 'show_bank_list');
    expect(fake.sent.filter((command) => command.type === 'show_bank_list')).toHaveLength(1);
    act(() => useCockpitStore.getState().setSessionStatus({ ...sessionLive, armed: false }));
    expect(fake.sent.filter((command) => command.type === 'show_bank_list')).toHaveLength(1);
    act(() => useCockpitStore.getState().setShowBank({ ...showBankState, banks: [], active_bank_id: null }));

    fireEvent.change(screen.getByLabelText('Bank name'), { target: { value: '  New Set  ' } });
    fireEvent.change(screen.getByLabelText('Description'), { target: { value: '  Friday  ' } });
    fireEvent.change(screen.getByLabelText('Notes'), { target: { value: ' first\n\n second ' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create show bank' }));
    expect(await waitForCommand(fake, 'show_bank_create')).toEqual({
      type: 'show_bank_create',
      name: 'New Set',
      description: 'Friday',
      notes: ['first', 'second'],
    });
  });

  it('leaves tokenless sockets silent through repeated first-frame deadline reconnects', () => {
    const fake = new FakeCockpitClient();
    useCockpitStore.setState({ connectionStatus: 'connecting', sessionStatus: null });
    render(
      <CockpitClientProvider client={fake.asClient()}>
        <ShowKitForgePanel />
      </CockpitClientProvider>,
    );

    for (let attempt = 0; attempt < 3; attempt += 1) {
      act(() => useCockpitStore.getState().setConnectionStatus('connected'));
      fireEvent.click(screen.getByRole('button', { name: 'Refresh from server' }));
      expect(fake.sent).toEqual([]);
      act(() => useCockpitStore.getState().setConnectionStatus('reconnecting'));
    }
    expect(useCockpitStore.getState().sessionStatus).toBeNull();
  });

  it('requires fresh authentication when remounted over a connected socket with a cached session', async () => {
    const fake = new FakeCockpitClient();
    const view = mount(fake);
    await waitForCommand(fake, 'show_bank_list');
    view.unmount();
    act(() => {
      useCockpitStore.getState().setConnectionStatus('reconnecting');
      useCockpitStore.getState().setConnectionStatus('connected');
    });
    render(<CockpitClientProvider client={fake.asClient()}><ShowKitForgePanel /></CockpitClientProvider>);

    expect(useCockpitStore.getState().sessionStatus).toEqual(sessionLive);
    expect(fake.sent.filter((command) => command.type === 'show_bank_list')).toHaveLength(1);
    expect(screen.getByRole('button', { name: 'Refresh from server' })).toBeDisabled();
    act(() => useCockpitStore.getState().setSessionStatus({ ...sessionLive }));
    await waitFor(() => expect(fake.sent.filter((command) => command.type === 'show_bank_list')).toHaveLength(2));
  });

  it('refreshes once when remounted under StrictMode in an authenticated connection', async () => {
    const fake = new FakeCockpitClient();
    const view = mount(fake);
    await waitForCommand(fake, 'show_bank_list');
    view.unmount();
    render(<StrictMode><CockpitClientProvider client={fake.asClient()}><ShowKitForgePanel /></CockpitClientProvider></StrictMode>);
    await waitFor(() => expect(fake.sent.filter((command) => command.type === 'show_bank_list')).toHaveLength(2));
    expect(screen.getByRole('button', { name: 'Refresh from server' })).toBeEnabled();
  });

  it('refreshes after disconnect and fresh hydration are batched into one render', async () => {
    const fake = new FakeCockpitClient();
    mount(fake);
    await waitForCommand(fake, 'show_bank_list');
    act(() => {
      useCockpitStore.getState().setConnectionStatus('closed');
      useCockpitStore.getState().setConnectionStatus('connected');
      useCockpitStore.getState().setSessionStatus({ ...sessionLive });
    });
    await waitFor(() => expect(fake.sent.filter((command) => command.type === 'show_bank_list')).toHaveLength(2));
    act(() => useCockpitStore.getState().setSessionStatus({ ...sessionLive, armed: false }));
    expect(fake.sent.filter((command) => command.type === 'show_bank_list')).toHaveLength(2);
  });

  it('reports rejected and thrown commands without changing authoritative bank state', async () => {
    const fake = new FakeCockpitClient();
    fake.ackQueue.push(
      { request_id: 'list', ok: true },
      { request_id: 'reject', ok: false, message: 'revision conflict' },
    );
    mount(fake, null);
    await waitForCommand(fake, 'show_bank_list');

    fireEvent.click(screen.getByRole('button', { name: 'Refresh from server' }));
    expect(await screen.findByText(/Show bank refresh failed: revision conflict/)).toBeInTheDocument();
    expect(useCockpitStore.getState().showBank).toBeNull();

    fake.nextRejection = new Error('socket lost');
    fireEvent.click(screen.getByRole('button', { name: 'Refresh from server' }));
    expect(await screen.findByText(/Show bank refresh failed: socket lost/)).toBeInTheDocument();

    fake.nextRejection = 'offline';
    fireEvent.click(screen.getByRole('button', { name: 'Refresh from server' }));
    expect(await screen.findByText(/Show bank refresh failed: offline/)).toBeInTheDocument();

    fake.ackQueue.push({ request_id: 'reject-default', ok: false });
    fireEvent.click(screen.getByRole('button', { name: 'Refresh from server' }));
    expect(await screen.findByText(/command rejected/)).toBeInTheDocument();
  });

  it('keeps reconnect actions and scope disabled until a fresh bank packet arrives', async () => {
    const fake = new FakeCockpitClient();
    mount(fake);
    await waitForCommand(fake, 'show_bank_list');
    fireEvent.change(screen.getByLabelText('Bank name'), { target: { value: 'Next set' } });
    act(() => useCockpitStore.getState().setConnectionStatus('closed'));
    fireEvent.click(screen.getByRole('button', { name: /2\. Peak Release/ }));
    expect(screen.getByText('Readiness unavailable — refresh required')).toBeInTheDocument();
    expect(screen.getByText(/Historical result only/)).toBeInTheDocument();
    expect(screen.queryByText(/currently grants show readiness/)).toBeNull();
    expect(screen.getByLabelText('P1')).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Lock pad 1' })).toBeDisabled();
    act(() => useCockpitStore.getState().setConnectionStatus('connected'));
    expect(fake.sent.filter((command) => command.type === 'show_bank_list')).toHaveLength(1);
    expect(screen.getByRole('button', { name: 'Refresh from server' })).toBeDisabled();
    act(() => useCockpitStore.getState().setSessionStatus({ ...sessionLive }));
    await waitFor(() => expect(fake.sent.filter((command) => command.type === 'show_bank_list')).toHaveLength(2));
    expect(screen.getByRole('button', { name: 'Create show bank' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Run show-time preflight' })).toBeDisabled();
    act(() => useCockpitStore.getState().setShowBank(showBankState));
    expect(screen.getByRole('button', { name: 'Create show bank' })).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Run show-time preflight' })).toBeEnabled();
  });

  it.each(['reject', 'throw'] as const)('ignores a stale refresh %s after a newer reconnect request', async (outcome) => {
    const fake = new FakeCockpitClient();
    let settleOld: (ack: CommandAck) => void = () => undefined;
    let rejectOld: (error: Error) => void = () => undefined;
    let settleNew: (ack: CommandAck) => void = () => undefined;
    fake.responseQueue.push(new Promise((resolve, reject) => { settleOld = resolve; rejectOld = reject; }));
    fake.responseQueue.push(new Promise((resolve) => { settleNew = resolve; }));
    mount(fake);
    await waitForCommand(fake, 'show_bank_list');
    act(() => useCockpitStore.getState().setConnectionStatus('closed'));
    act(() => useCockpitStore.getState().setConnectionStatus('connected'));
    act(() => useCockpitStore.getState().setSessionStatus({ ...sessionLive }));
    await act(async () => {
      if (outcome === 'reject') settleOld({ request_id: 'old', ok: false, message: 'Old refresh failed' });
      else rejectOld(new Error('Old refresh failed'));
    });
    expect(screen.queryByText(/Old refresh failed/)).toBeNull();
    expect(screen.getByRole('button', { name: 'Refresh from server' })).toBeDisabled();
    await act(async () => settleNew({ request_id: 'new', ok: true }));
    expect(screen.getByRole('button', { name: 'Refresh from server' })).toBeEnabled();
  });

  it('preserves unfinished cue and bank metadata through unrelated bank packets', async () => {
    const fake = new FakeCockpitClient();
    mount(fake);
    await waitForCommand(fake, 'show_bank_list');
    const bankEditor = screen.getByRole('heading', { name: 'Bank details' }).closest('form');
    if (bankEditor === null) throw new Error('bank editor missing');
    fireEvent.change(within(bankEditor).getByLabelText('Name'), { target: { value: 'Unfinished set title' } });
    fireEvent.change(screen.getByLabelText('Audition notes'), { target: { value: 'Do not lose these notes' } });
    const next = { ...showBankState, revision: 99 };
    act(() => useCockpitStore.getState().setShowBank(next));
    expect(within(bankEditor).getByLabelText('Name')).toHaveValue('Unfinished set title');
    expect(screen.getByLabelText('Audition notes')).toHaveValue('Do not lose these notes');
    fireEvent.click(screen.getByRole('button', { name: /2\. Peak Release/ }));
    expect(screen.getByLabelText('Audition notes')).toHaveValue(readyEntry.audition_notes.join('\n'));
  });

  it('requires reselecting the displayed cue before preparing or sending a global plan', async () => {
    const fake = new FakeCockpitClient();
    mount(fake);
    await waitForCommand(fake, 'show_bank_list');
    act(() => useCockpitStore.setState({
      dualMachineStage: readyDualMachineStage,
      previewCandidate: candidate,
      sendPlan,
      rytmPadLocks: [2],
    }));
    expect(screen.getByRole('button', { name: 'Send exact Rytm plan' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Prepare exact plan' })).toBeDisabled();
    act(() => useCockpitStore.setState({
      previewCandidate: { ...candidate, candidate_id: 'rytm-candidate-one' },
      sendPlan: { ...sendPlan, candidate_id: 'rytm-candidate-one' },
    }));
    expect(screen.getByRole('button', { name: 'Send exact Rytm plan' })).toBeEnabled();
    fireEvent.click(screen.getByRole('button', { name: 'Send exact Rytm plan' }));
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /2\. Peak Release/ }));
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(screen.getByRole('button', { name: 'Send exact Rytm plan' })).toBeDisabled();
    const first = screen.getByRole('article', { name: 'Candidate 1' });
    expect(within(first).getByRole('button', { name: 'Select for audition' })).toBeEnabled();
    fireEvent.click(within(first).getByRole('button', { name: 'Select for audition' }));
    expect(await waitForCommand(fake, 'show_bank_select_candidate')).toMatchObject({ entry_id: 'entry-two' });
    expect(fake.sent.filter((command) => command.type === 'send')).toEqual([]);
  });

  it('reports background refresh failures without promoting local state', async () => {
    const rejected = new FakeCockpitClient();
    rejected.ackQueue.push({ request_id: 'background-reject', ok: false, error: 'not ready' });
    mount(rejected, null);
    expect(await screen.findByText(/Show bank refresh failed: not ready/)).toBeInTheDocument();
    expect(useCockpitStore.getState().showBank).toBeNull();
  });

  it('reports a thrown background refresh without promoting local state', async () => {
    const thrown = new FakeCockpitClient();
    thrown.nextRejection = new Error('background socket lost');
    mount(thrown, null);
    expect(
      await screen.findByText(/Show bank refresh failed: background socket lost/),
    ).toBeInTheDocument();
    expect(useCockpitStore.getState().showBank).toBeNull();
  });

  it.each(['rytm', 'a4'] as const)('explains the remaining save when only %s has been attested', async (saved) => {
    const entry: ShowBankEntry = {
      ...forgeEntry,
      rytm_hardware_save: saved === 'rytm' ? forgeEntry.rytm_hardware_save : null,
      analog_four_hardware_save: saved === 'a4' ? forgeEntry.analog_four_hardware_save : null,
      rytm_recapture: null,
      analog_four_recapture: null,
    };
    const fake = new FakeCockpitClient();
    mount(fake, { ...showBankState, banks: [{ ...showBankState.banks[0]!, entries: [entry] }] });
    await waitForCommand(fake, 'show_bank_list');
    const message = saved === 'rytm' ? /Rytm is attested\/unverified\. Save the favorite manually on Analog Four/ : /Analog Four is attested\/unverified\. Save the favorite manually on Rytm/;
    expect(screen.getByText(message)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Verify current paired recapture' })).toBeDisabled();
  });

  it('handles no-op candidates, missing semantic evidence, first favorites, and local retention', async () => {
    const entry: ShowBankEntry = {
      ...forgeEntry,
      favorite: null,
      selected_candidate_id: null,
      rytm_live_auditioned_at: null,
      energy_level: null,
      energy_notes: [],
      transition_notes: [],
      candidates: forgeEntry.candidates.map((pair, index) => ({
        ...pair,
        recipe: {
          ...pair.recipe,
          rytm_scope: { ...pair.recipe.rytm_scope, target_ids: [], locked_ids: [] },
          analog_four_scope: { ...pair.recipe.analog_four_scope, target_ids: [], locked_ids: [1] },
        },
        rytm_candidate: {
          ...pair.rytm_candidate,
          pad_deltas: index === 0 ? [] : [{ pad_id: 1, proposed_params: {}, changed_keys: ['tun'] }],
        },
        analog_four_candidate: {
          ...pair.analog_four_candidate,
          values: index === 0 ? [] : pair.analog_four_candidate.values,
        },
      })),
      rytm_recapture: {
        ...forgeEntry.rytm_recapture!,
        observed_semantic_fingerprint: null,
        capture: { ...forgeEntry.rytm_recapture!.capture, sysex: { ...forgeEntry.rytm_recapture!.capture.sysex, retained: null } },
      },
      analog_four_recapture: {
        ...forgeEntry.analog_four_recapture!,
        capture: { ...forgeEntry.analog_four_recapture!.capture, sysex: { ...forgeEntry.analog_four_recapture!.capture.sysex, retained: null } },
      },
    };
    const fake = new FakeCockpitClient();
    mount(fake, { ...showBankState, banks: [{ ...showBankState.banks[0]!, entries: [entry] }] });
    await waitForCommand(fake, 'show_bank_list');
    expect(screen.getByText('No mapped Rytm parameter changes.')).toBeInTheDocument();
    expect(screen.getByText('No mapped A4 parameter changes. Source bytes preserved.')).toBeInTheDocument();
    expect(screen.getByText('Pad 1: tun —')).toBeInTheDocument();
    expect(screen.getAllByText(/Rytm scope: All pads; locks: none/)).toHaveLength(2);
    expect(screen.getAllByText(/A4 scope: All tracks; locks: T1/)).toHaveLength(2);
    expect(screen.getByText('Unavailable')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Energy level'), { target: { value: '3' } });
    fireEvent.change(screen.getByLabelText('Energy level'), { target: { value: '' } });
    const first = screen.getByRole('article', { name: 'Candidate 1' });
    expect(within(first).getByRole('button', { name: 'Retain selected A4 offline artifact' })).toBeDisabled();
    fireEvent.click(within(first).getByRole('button', { name: 'Mark favorite' }));
    expect(await waitForCommand(fake, 'show_bank_mark_favorite')).not.toHaveProperty('replace_existing');
    fireEvent.click(screen.getByRole('button', { name: 'Retain Rytm recapture evidence' }));
    expect(await waitForCommand(fake, 'show_bank_retain_capture')).toMatchObject({ capture_kind: 'favorite', device_id: 'analog_rytm_mk2' });
    fireEvent.click(screen.getByRole('button', { name: 'Retain Analog Four recapture evidence' }));
    expect(await waitForCommand(fake, 'show_bank_retain_capture')).toMatchObject({ capture_kind: 'favorite', device_id: 'analog_four_mk2' });
  });

  it('keeps absent server depth presets unavailable, including keyboard shortcuts', async () => {
    const fake = new FakeCockpitClient();
    mount(fake, { ...showBankState, depth_presets: {} as ShowDepthPresets });
    await waitForCommand(fake, 'show_bank_list');
    expect(screen.getByRole('button', { name: 'Small · Unavailable' })).toBeDisabled();
    fireEvent.keyDown(screen.getByTestId('show-kit-forge'), { key: '1' });
    expect(screen.getByLabelText(/Custom depth/)).toHaveValue('0.25');
  });

  it('supports source recovery and ready exports with older acknowledgement metadata', async () => {
    const fake = new FakeCockpitClient();
    const readyBank = { ...showBankState.banks[0]!, status: 'show-ready' as const, entries: [readyEntry], active_entry_id: readyEntry.entry_id, readiness: { ...showBankState.banks[0]!.readiness, status: 'show-ready' as const, show_ready: true } };
    mount(fake, { ...showBankState, banks: [readyBank] });
    await waitForCommand(fake, 'show_bank_list');
    fireEvent.click(screen.getByRole('button', { name: 'Reset Cockpit audition to source' }));
    await waitForCommand(fake, 'show_bank_return_source');
    expect(screen.getByText(/Cockpit reset its in-memory audition only/)).toHaveTextContent('Source slots: Rytm 11, Analog Four 22');
    fireEvent.click(screen.getByRole('button', { name: 'Export show-ready local pack' }));
    await waitForCommand(fake, 'show_bank_export');
    expect(screen.getByText('Show-pack export completed beneath the configured server export root.')).toBeInTheDocument();
  });

  it('corrects an attested hardware slot through a new explicit save attestation', async () => {
    const fake = new FakeCockpitClient();
    mount(fake);
    await waitForCommand(fake, 'show_bank_list');
    fireEvent.click(screen.getAllByText('Correct a recorded hardware slot')[0]!);
    const correct = screen.getByRole('button', { name: 'Re-attest Rytm saved slot' });
    expect(correct).toBeDisabled();
    fireEvent.change(screen.getByLabelText('Corrected Rytm slot (1–128)'), { target: { value: '45' } });
    fireEvent.click(correct);
    expect(await waitForCommand(fake, 'show_bank_attest_hardware_saved')).toMatchObject({ device_id: 'analog_rytm_mk2', slot: 45, expected_revision: 7 });
    expect(screen.getAllByText(/A new attestation clears this instrument’s recapture/)).toHaveLength(2);
  });

  it('revokes favorite replacement confirmation when its authoritative bank revision changes', async () => {
    const fake = new FakeCockpitClient();
    mount(fake);
    await waitForCommand(fake, 'show_bank_list');
    fireEvent.change(screen.getByLabelText('Audition notes'), { target: { value: 'Draft still open' } });
    const first = screen.getByRole('article', { name: 'Candidate 1' });
    fireEvent.click(within(first).getByRole('button', { name: 'Mark favorite' }));
    expect(screen.getByText(/Replace the existing favorite/)).toBeInTheDocument();
    fireEvent.click(within(screen.getByRole('row', { name: /Opening Pressure/ })).getByRole('button', { name: 'Remove' }));
    expect(screen.getByRole('button', { name: 'Confirm remove' })).toBeInTheDocument();
    act(() => useCockpitStore.getState().setShowBank({
      ...showBankState,
      revision: 99,
      banks: [{ ...showBankState.banks[0]!, revision: 8 }],
    }));
    expect(screen.queryByText(/Replace the existing favorite/)).toBeNull();
    expect(screen.queryByRole('button', { name: 'Confirm remove' })).toBeNull();
    expect(screen.getByLabelText('Audition notes')).toHaveValue('Draft still open');
  });

  it('renders captured subset IDs and sends their exact target and lock identities', async () => {
    const fake = new FakeCockpitClient();
    mount(fake);
    await waitForCommand(fake, 'show_bank_list');
    act(() => useCockpitStore.setState({
      kitCaptures: forgeCaptures.map((capture) => ({
        ...capture,
        layout_items: capture.layout_items.filter((item) =>
          (capture.device_id === 'analog_rytm_mk2' ? [3, 8] : [2, 4]).includes(item.index),
        ),
      })),
      rytmPadTargets: [], a4TrackTargets: [], rytmPadLocks: [], a4TrackLocks: [],
    }));

    const rytm = within(screen.getByRole('group', { name: 'Rytm pads' }));
    const a4 = within(screen.getByRole('group', { name: 'Analog Four tracks' }));
    expect(rytm.getAllByRole('checkbox')).toHaveLength(2);
    expect(a4.getAllByRole('checkbox')).toHaveLength(2);
    expect(rytm.queryByLabelText('P1')).not.toBeInTheDocument();
    expect(a4.queryByLabelText('T1')).not.toBeInTheDocument();
    fireEvent.click(rytm.getByLabelText('P8'));
    fireEvent.click(a4.getByLabelText('T4'));
    fireEvent.click(rytm.getByRole('button', { name: 'Lock pad 3' }));
    fireEvent.click(a4.getByRole('button', { name: 'Lock track 2' }));
    expect(fake.sent).toEqual(expect.arrayContaining([
      { type: 'set_mutation_targets', device_id: 'analog_rytm_mk2', target_ids: [8] },
      { type: 'set_mutation_targets', device_id: 'analog_four_mk2', target_ids: [4] },
      { type: 'set_pad_lock', pad_id: 3, locked: true },
      { type: 'set_a4_track_lock', track: 2, locked: true },
    ]));
    fireEvent.click(screen.getByRole('button', { name: 'Forge 3 candidate pairs' }));
    expect(await waitForCommand(fake, 'show_bank_generate_candidates')).toMatchObject({
      rytm_targets: [8], rytm_locks: [3], a4_targets: [4], a4_locks: [2],
    });
  });

  it.each(['missing', 'empty'] as const)(
    'keeps %s captured layouts inert while retained-bank generation preserves the server scope',
    async (layout) => {
      const retainedState = {
        ...showBankState,
        banks: showBankState.banks.map((bank) => ({
          ...bank,
          entries: bank.entries.map((entry) => ({
            ...entry,
            rytm_source: {
              ...entry.rytm_source,
              sysex: {
                ...entry.rytm_source.sysex,
                retained: {
                  artifact_name: `${entry.rytm_source.sysex.frame_sha256}.syx`,
                  sha256: entry.rytm_source.sysex.frame_sha256,
                  byte_count: entry.rytm_source.sysex.frame_bytes,
                },
              },
            },
            analog_four_source: {
              ...entry.analog_four_source,
              sysex: {
                ...entry.analog_four_source.sysex,
                retained: {
                  artifact_name: `${entry.analog_four_source.sysex.frame_sha256}.syx`,
                  sha256: entry.analog_four_source.sysex.frame_sha256,
                  byte_count: entry.analog_four_source.sysex.frame_bytes,
                },
              },
            },
          })),
        })),
      };
      const fake = new FakeCockpitClient();
      mount(fake, retainedState);
      await waitForCommand(fake, 'show_bank_list');
      act(() => useCockpitStore.setState({
        kitCaptures: layout === 'missing' ? [] : forgeCaptures.map((capture) => ({ ...capture, layout_items: [] })),
        rytmPadTargets: [3], a4TrackTargets: [2], rytmPadLocks: [8], a4TrackLocks: [4],
      }));
      for (const name of ['Rytm pads', 'Analog Four tracks']) {
        const group = screen.getByRole('group', { name });
        expect(group).toBeDisabled();
        expect(within(group).queryByRole('checkbox')).not.toBeInTheDocument();
        expect(within(group).queryByRole('button')).not.toBeInTheDocument();
        expect(within(group).getByText(/Capture this device’s KIT to load its available/)).toBeInTheDocument();
      }
      const forge = screen.getByRole('button', { name: 'Forge 3 candidate pairs' });
      expect(forge).toBeEnabled();
      fireEvent.click(forge);
      expect(await waitForCommand(fake, 'show_bank_generate_candidates')).toMatchObject({
        rytm_targets: [3], rytm_locks: [8], a4_targets: [2], a4_locks: [4],
      });
      expect(fake.sent.filter((command) =>
        ['set_mutation_targets', 'clear_mutation_targets', 'set_pad_lock', 'set_a4_track_lock'].includes(command.type),
      )).toEqual([]);

      act(() => useCockpitStore.setState({
        kitCaptures: forgeCaptures.filter((capture) => capture.device_id === 'analog_rytm_mk2'),
      }));
      expect(screen.getByRole('group', { name: 'Rytm pads' })).toBeEnabled();
      expect(screen.getByRole('group', { name: 'Analog Four tracks' })).toBeDisabled();
      expect(screen.getByLabelText('P3')).toBeChecked();
      expect(screen.queryByLabelText('T2')).not.toBeInTheDocument();
    },
  );

  it('edits metadata, scope, depth, and deterministic multi-candidate controls', async () => {
    const fake = new FakeCockpitClient();
    mount(fake);
    await waitForCommand(fake, 'show_bank_list');
    await waitFor(() => expect(screen.getAllByDisplayValue('Warehouse Set')).toHaveLength(2));

    fireEvent.change(screen.getByLabelText('Server banks'), { target: { value: 'bank-one' } });
    await waitForCommand(fake, 'show_bank_select');

    expect(screen.getAllByText('OXI owns sequencing')).toHaveLength(2);
    expect(screen.getByText('Direct OXI control: disabled')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent('Fingerprint mismatch');
    expect(screen.getAllByText(/11111111/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/22222222/).length).toBeGreaterThan(0);

    const bankEditor = screen.getByRole('heading', { name: 'Bank details' }).closest('form');
    if (bankEditor === null) throw new Error('bank editor missing');
    fireEvent.change(within(bankEditor).getByLabelText('Name'), { target: { value: ' Updated Set ' } });
    fireEvent.change(within(bankEditor).getByLabelText('Description'), { target: { value: ' New description ' } });
    fireEvent.change(within(bankEditor).getByLabelText('Notes'), { target: { value: 'line one\nline two' } });
    fireEvent.click(within(bankEditor).getByRole('button', { name: 'Save bank details' }));
    expect(await waitForCommand(fake, 'show_bank_update')).toMatchObject({
      type: 'show_bank_update',
      name: 'Updated Set',
      description: 'New description',
      notes: ['line one', 'line two'],
      expected_revision: 7,
    });

    fireEvent.change(screen.getByLabelText('Audition notes'), { target: { value: 'listen on PA\ncheck kick' } });
    const cueEditor = screen.getByRole('heading', { name: 'Shape the show moment' }).closest('form');
    if (cueEditor === null) throw new Error('cue editor missing');
    fireEvent.change(within(cueEditor).getByLabelText('Name'), { target: { value: ' New cue ' } });
    fireEvent.change(within(cueEditor).getByLabelText('Description'), {
      target: { value: ' New cue description ' },
    });
    fireEvent.change(screen.getByLabelText('Energy notes'), { target: { value: 'peak after bar 16' } });
    fireEvent.change(screen.getByLabelText('Energy level'), { target: { value: '4' } });
    fireEvent.change(screen.getByLabelText('Transition notes'), { target: { value: 'fade slowly' } });
    fireEvent.change(screen.getByLabelText('Recovery notes'), { target: { value: 'reload source' } });
    fireEvent.change(screen.getByLabelText('OXI project'), { target: { value: ' Live Brain ' } });
    fireEvent.change(screen.getByLabelText('OXI pattern'), { target: { value: ' B04 ' } });
    fireEvent.change(screen.getByLabelText('OXI chapter'), { target: { value: ' Peak ' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save cue metadata' }));
    expect(await waitForCommand(fake, 'show_bank_update_entry')).toMatchObject({
      name: 'New cue',
      description: 'New cue description',
      audition_notes: ['listen on PA', 'check kick'],
      energy_level: 4,
      energy_notes: ['peak after bar 16'],
      transition_notes: ['fade slowly'],
      recovery_notes: ['reload source'],
      oxi: { project: 'Live Brain', pattern: 'B04', chapter: 'Peak', direct_oxi_control: false },
    });

    const root = screen.getByTestId('show-kit-forge');
    fireEvent.keyDown(root, { key: '1' });
    expect(screen.getByRole('button', { name: /Small · 25%/ })).toHaveAttribute('aria-pressed', 'true');
    fireEvent.keyDown(root, { key: '2' });
    fireEvent.keyDown(root, { key: '3' });
    expect(screen.getByRole('button', { name: /Large · 75%/ })).toHaveAttribute('aria-pressed', 'true');
    fireEvent.keyDown(root, { key: 'x' });
    fireEvent.keyDown(screen.getByLabelText('Starting seed'), { key: '1' });

    fireEvent.change(screen.getByLabelText(/Custom depth/), { target: { value: '0.63' } });
    expect(screen.getByLabelText(/Custom depth/)).toHaveAttribute('aria-valuetext', '63 percent');
    fireEvent.click(screen.getByRole('button', { name: /Small · 25%/ }));
    fireEvent.change(screen.getByLabelText('Starting seed'), { target: { value: '77' } });
    fireEvent.change(screen.getByLabelText('Candidate count'), { target: { value: '4' } });
    fireEvent.click(screen.getByLabelText('P1'));
    fireEvent.click(screen.getByRole('button', { name: 'Lock pad 1' }));
    fireEvent.click(screen.getByLabelText('T1'));
    fireEvent.click(screen.getByRole('button', { name: 'Lock track 1' }));
    await waitFor(() => expect(useCockpitStore.getState().rytmPadTargets).toEqual([1]));
    fireEvent.click(screen.getByRole('button', { name: 'Forge 4 candidate pairs' }));
    expect(await waitForCommand(fake, 'show_bank_generate_candidates')).toMatchObject({
      depth_preset: 'small',
      depth: 0.25,
      candidate_count: 4,
      seed: 77,
      profile_id: profile.profile_id,
      rytm_targets: [1],
      rytm_locks: [1],
      a4_targets: [1],
      a4_locks: [1],
    });

    const first = screen.getByRole('article', { name: 'Candidate 1' });
    const second = screen.getByRole('article', { name: 'Candidate 2' });
    expect(within(first).getByText('A4 offline saved-KIT-format artifact')).toBeInTheDocument();
    expect(within(first).getByText(/Track 1 filter1_frequency: 63\.50/)).toBeInTheDocument();
    expect(within(first).getByText(/Local file only\. Cockpit cannot SEND/)).toBeInTheDocument();
    expect(within(second).getByText(/Retained as/)).toHaveTextContent('4096 bytes');
    fireEvent.click(
      within(first).getByRole('button', { name: 'Retain selected A4 offline artifact' }),
    );
    expect(await waitForCommand(fake, 'show_bank_retain_capture')).toMatchObject({
      capture_kind: 'candidate',
      device_id: 'analog_four_mk2',
      entry_id: 'entry-one',
    });
    fireEvent.click(within(second).getByRole('button', { name: 'Select for audition' }));
    expect(await waitForCommand(fake, 'show_bank_select_candidate')).toMatchObject({ candidate_id: 'candidate-two' });
    fireEvent.click(within(first).getByRole('button', { name: 'Mark favorite' }));
    expect(screen.getByText(/Replace the existing favorite/)).toBeInTheDocument();
    expect(fake.sent.filter((command) => command.type === 'show_bank_mark_favorite')).toEqual([]);
    fireEvent.click(within(first).getByRole('button', { name: 'Keep current favorite' }));
    expect(screen.queryByText(/Replace the existing favorite/)).toBeNull();
    fireEvent.click(within(first).getByRole('button', { name: 'Mark favorite' }));
    fireEvent.click(within(first).getByRole('button', { name: 'Replace favorite' }));
    expect(await waitForCommand(fake, 'show_bank_mark_favorite')).toMatchObject({
      candidate_id: 'candidate-one',
      replace_existing: true,
    });
  });

  it('adopts and retains sources with operator-facing slots', async () => {
    const fake = new FakeCockpitClient();
    mount(fake);
    await waitForCommand(fake, 'show_bank_list');
    await waitFor(() => expect(screen.getAllByDisplayValue('Warehouse Set')).toHaveLength(2));

    const sourceSlots = screen.getAllByLabelText('Source hardware slot (1–128)');
    fireEvent.change(sourceSlots[0] as HTMLElement, { target: { value: '150' } });
    fireEvent.change(sourceSlots[1] as HTMLElement, { target: { value: '0' } });
    fireEvent.click(screen.getByRole('button', { name: 'Adopt current captures as a new source pair' }));
    expect(await waitForCommand(fake, 'show_bank_adopt_sources')).toMatchObject({
      rytm_fingerprint: 'aaaaaaaa',
      a4_fingerprint: 'bbbbbbbb',
      rytm_slot: 128,
      a4_slot: 1,
    });

    fireEvent.click(screen.getByRole('button', { name: 'Retain Rytm source' }));
    expect(await waitForCommand(fake, 'show_bank_retain_capture')).toMatchObject({
      capture_kind: 'source',
      device_id: 'analog_rytm_mk2',
    });
    fireEvent.click(screen.getByRole('button', { name: 'Retain A4 source' }));
    expect(await waitForCommand(fake, 'show_bank_retain_capture')).toMatchObject({
      capture_kind: 'source',
      device_id: 'analog_four_mk2',
    });
  });

  it('replaces source retain controls with exact server-owned artifact evidence', async () => {
    const sourceSha = forgeEntry.rytm_source.sysex.frame_sha256;
    const retainedEntry = {
      ...forgeEntry,
      rytm_source: {
        ...forgeEntry.rytm_source,
        sysex: {
          ...forgeEntry.rytm_source.sysex,
          retained: {
            artifact_name: `${sourceSha}.syx`,
            sha256: sourceSha,
            byte_count: forgeEntry.rytm_source.sysex.frame_bytes,
          },
        },
      },
    };
    const fake = new FakeCockpitClient();
    mount(fake, {
      ...showBankState,
      banks: [
        {
          ...(showBankState.banks[0] as NonNullable<(typeof showBankState.banks)[number]>),
          active_entry_id: retainedEntry.entry_id,
          entries: [retainedEntry],
        },
      ],
    });
    await waitForCommand(fake, 'show_bank_list');

    expect(screen.queryByRole('button', { name: 'Retain Rytm source' })).toBeNull();
    expect(screen.getByText(new RegExp(`${sourceSha}\\.syx`)).parentElement).toHaveTextContent(
      '4096 bytes',
    );
    expect(screen.getByRole('button', { name: 'Retain A4 source' })).toBeEnabled();
  });

  it('keeps favorite, hardware-save, recapture, preflight, and SEND states distinct', async () => {
    const favoriteEntry = {
      ...forgeEntry,
      status: 'favorite' as const,
      rytm_hardware_save: null,
      analog_four_hardware_save: null,
      rytm_recapture: null,
      analog_four_recapture: null,
      readiness: { status: 'favorite' as const, show_ready: false, blocked_reasons: ['rytm_hardware_save_missing' as const], recovery_actions: ['save_then_recapture'] },
    };
    const favoriteState: ShowBankState = {
      ...showBankState,
      banks: [{ ...(showBankState.banks[0] as NonNullable<(typeof showBankState.banks)[number]>), entries: [favoriteEntry], active_entry_id: favoriteEntry.entry_id }],
    };
    const fake = new FakeCockpitClient();
    mount(fake, favoriteState);
    await waitForCommand(fake, 'show_bank_list');
    expect(screen.getByText('Save on instrument, then recapture')).toBeInTheDocument();
    expect(screen.getByText(/Marked favorite in Cockpit/)).toBeInTheDocument();

    const savedSlots = screen.getAllByLabelText('Saved hardware slot (1–128)');
    fireEvent.change(savedSlots[0] as HTMLElement, { target: { value: '999' } });
    fireEvent.change(savedSlots[1] as HTMLElement, { target: { value: '-1' } });
    fireEvent.click(
      screen.getByRole('button', { name: 'Attest: I manually saved this on Rytm' }),
    );
    expect(await waitForCommand(fake, 'show_bank_attest_hardware_saved')).toMatchObject({
      device_id: 'analog_rytm_mk2',
      slot: 128,
    });
    fireEvent.click(
      screen.getByRole('button', { name: 'Attest: I manually saved this on Analog Four' }),
    );
    expect(await waitForCommand(fake, 'show_bank_attest_hardware_saved')).toMatchObject({
      device_id: 'analog_four_mk2',
      slot: 1,
    });
    expect(screen.getByRole('button', { name: 'Verify current paired recapture' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Run show-time preflight' })).toBeDisabled();

    expect(screen.queryByRole('button', { name: /Retain .* recapture evidence/ })).toBeNull();
    fake.ackQueue.push({
      request_id: 'reset-source',
      ok: true,
      hardware_changed: false,
      source_slots: { rytm: 11, analog_four: 22 },
      instruction:
        'Cockpit reset its in-memory audition only; no instrument changed. Manually load the immutable Rytm and Analog Four source slots to return hardware.',
    });
    fireEvent.click(screen.getByRole('button', { name: 'Reset Cockpit audition to source' }));
    await waitForCommand(fake, 'show_bank_return_source');
    expect(await screen.findByText(/no instrument changed/)).toHaveTextContent(
      'Source slots: Rytm 11, Analog Four 22',
    );

    act(() => {
      useCockpitStore.setState({
        showBank: showBankState,
        connectionStatus: 'connected',
        dualMachineStage: readyDualMachineStage,
        rytmPadLocks: [2],
        a4TrackLocks: [],
        rytmPadTargets: [],
        a4TrackTargets: [],
        previewCandidate: { ...candidate, candidate_id: 'rytm-candidate-one' },
        sendPlan: { ...sendPlan, candidate_id: 'rytm-candidate-one' },
      });
    });
    fireEvent.click(screen.getByRole('button', { name: 'Verify current paired recapture' }));
    await waitForCommand(fake, 'show_bank_verify_recapture');

    fireEvent.click(screen.getByRole('button', { name: 'Preview Rytm' }));
    await waitForCommand(fake, 'toggle_preview');
    fireEvent.click(screen.getByRole('button', { name: 'Prepare exact plan' }));
    await waitForCommand(fake, 'prepare_send_plan');
    fireEvent.click(screen.getByRole('button', { name: 'Send exact Rytm plan' }));
    const dialog = screen.getByRole('dialog', { name: 'Confirm send to hardware' });
    expect(dialog).toHaveTextContent('IAC Driver Bus 1');
    expect(dialog).toHaveTextContent('sendplan-1');
    expect(dialog).toHaveTextContent('1, 3');
    expect(dialog).toHaveTextContent('Messages');
    expect(dialog).toHaveTextContent('2');
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(screen.getByRole('button', { name: 'Send exact Rytm plan' })).toHaveFocus();
    fireEvent.click(screen.getByRole('button', { name: 'Send exact Rytm plan' }));
    fireEvent.keyDown(screen.getByRole('dialog', { name: 'Confirm send to hardware' }), {
      key: 'Escape',
    });
    expect(screen.queryByRole('dialog', { name: 'Confirm send to hardware' })).toBeNull();
    expect(screen.getByRole('button', { name: 'Send exact Rytm plan' })).toHaveFocus();
    fireEvent.click(screen.getByRole('button', { name: 'Send exact Rytm plan' }));
    act(() => useCockpitStore.getState().setSessionStatus(sessionMock));
    expect(screen.queryByRole('dialog', { name: 'Confirm send to hardware' })).toBeNull();
    expect(screen.getByRole('button', { name: 'Dry-run exact Rytm plan' })).toHaveFocus();
    act(() => useCockpitStore.getState().setSessionStatus(sessionLive));
    fireEvent.click(screen.getByRole('button', { name: 'Send exact Rytm plan' }));
    expect(screen.getByRole('button', { name: 'Confirm send' })).toBeDisabled();
    fireEvent.click(screen.getByRole('checkbox', { name: /I manually reloaded Rytm source/ }));
    fireEvent.click(screen.getByRole('button', { name: 'Confirm send' }));
    expect(await waitForCommand(fake, 'send')).toMatchObject({
      confirm: true,
      send_plan_id: 'sendplan-1',
      show_bank_source_reloaded: true,
    });
    expect(screen.getByRole('button', { name: 'A4 SEND blocked — offline only' })).toBeDisabled();

    fireEvent.click(screen.getByRole('button', { name: /2\. Peak Release/ }));
    await screen.findByDisplayValue('Peak Release');
    fireEvent.click(screen.getByRole('button', { name: 'Run show-time preflight' }));
    await waitForCommand(fake, 'show_bank_run_preflight');
  });

  it('uses a one-click exact-plan dry run in mock mode without implying hardware output', async () => {
    const fake = new FakeCockpitClient();
    mount(fake);
    await waitForCommand(fake, 'show_bank_list');
    act(() => {
      useCockpitStore.setState({
        dualMachineStage: readyDualMachineStage,
        previewCandidate: { ...candidate, candidate_id: 'rytm-candidate-one' },
        rytmPadLocks: [2],
        rytmPadTargets: [],
        sendPlan: { ...sendPlan, candidate_id: 'rytm-candidate-one' },
        sessionStatus: sessionMock,
      });
    });

    const send = screen.getByRole('button', { name: 'Dry-run exact Rytm plan' });
    fireEvent.click(send);
    expect(await waitForCommand(fake, 'send')).toEqual({
      type: 'send',
      send_plan_id: 'sendplan-1',
    });
    expect(screen.queryByRole('dialog', { name: 'Confirm send to hardware' })).toBeNull();
  });

  it('shows authoritative saved slots, recapture comparisons, and cue-sheet source/favorite truth', async () => {
    const fake = new FakeCockpitClient();
    mount(fake);
    await waitForCommand(fake, 'show_bank_list');

    expect(screen.getByText('Save on instrument, then recapture')).toBeInTheDocument();
    expect(screen.getAllByText('Manually saved — attested/unverified').length).toBeGreaterThan(1);
    expect(screen.getAllByText('31').length).toBeGreaterThan(0);
    expect(screen.getAllByText('32').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Immutable source semantic fingerprint')).toHaveLength(2);
    expect(screen.getByText('Rytm semantic fingerprint matches favorite')).toBeInTheDocument();
    expect(
      screen.getByText('Analog Four semantic fingerprint differs from favorite'),
    ).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent(
      'Immutable source 99999999: observed capture matches source',
    );

    const firstRow = screen.getByRole('row', { name: /Opening Pressure/ });
    expect(firstRow).toHaveTextContent('R 11 · A4 22');
    expect(firstRow).toHaveTextContent('R 31 · A4 32');
    expect(firstRow).toHaveTextContent('23333333');
    expect(firstRow).toHaveTextContent('99999999');
    expect(firstRow).toHaveTextContent('Level 3 / 5');
    expect(firstRow).toHaveTextContent('recapture_intended_a4_slot');
    expect(firstRow).toHaveTextContent('reload source slots');

    const secondRow = screen.getByRole('row', { name: /Peak Release/ });
    expect(secondRow).toHaveTextContent('R 11 · A4 22');
    expect(secondRow).toHaveTextContent('R 31 · A4 32');
    expect(secondRow).toHaveTextContent('14444444');
  });

  it('supports keyboard cue ordering, duplicate/remove confirmation, and safe-name packs', async () => {
    const fake = new FakeCockpitClient();
    mount(fake);
    await waitForCommand(fake, 'show_bank_list');
    await waitFor(() => expect(screen.getAllByDisplayValue('Warehouse Set')).toHaveLength(2));

    expect(screen.getByRole('button', { name: 'Move Opening Pressure earlier' })).toBeDisabled();
    fireEvent.click(screen.getByRole('button', { name: 'Move Opening Pressure later' }));
    expect(await waitForCommand(fake, 'show_bank_reorder_entries')).toMatchObject({
      entry_ids: ['entry-two', 'entry-one'],
    });
    fireEvent.click(screen.getByRole('button', { name: 'Move Peak Release earlier' }));
    await waitForCommand(fake, 'show_bank_reorder_entries');

    const firstRow = screen.getByRole('row', { name: /Opening Pressure/ });
    fireEvent.click(within(firstRow).getByRole('button', { name: 'Opening Pressure' }));
    fireEvent.click(within(firstRow).getByRole('button', { name: 'Duplicate' }));
    expect(await waitForCommand(fake, 'show_bank_duplicate_entry')).toMatchObject({ entry_id: 'entry-one' });
    fireEvent.click(within(firstRow).getByRole('button', { name: 'Remove' }));
    fireEvent.click(within(firstRow).getByRole('button', { name: 'Cancel' }));
    fireEvent.click(within(firstRow).getByRole('button', { name: 'Remove' }));
    fireEvent.click(within(firstRow).getByRole('button', { name: 'Confirm remove' }));
    expect(await waitForCommand(fake, 'show_bank_remove_entry')).toMatchObject({ entry_id: 'entry-one' });

    const importName = screen.getByLabelText('Import package ID');
    fireEvent.change(importName, { target: { value: '../unsafe' } });
    expect(screen.getByRole('button', { name: 'Import local pack' })).toBeDisabled();
    fireEvent.change(importName, { target: { value: 'Friday-Show' } });
    fake.ackQueue.push({
      request_id: 'import-pack',
      ok: true,
      show_pack_import: {
        package_id: 'friday-show',
        bank_id: 'imported-bank',
        artifact_count: 6,
        write_count: 6,
      },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Import local pack' }));
    expect(await waitForCommand(fake, 'show_bank_import')).toEqual({
      type: 'show_bank_import',
      pack_name: 'friday-show',
    });
    expect(await screen.findByText(/Imported friday-show/)).toHaveTextContent(
      '6 artifacts verified and 6 files retained',
    );

    const exportName = screen.getByLabelText('Export package ID');
    fireEvent.change(exportName, { target: { value: 'Friday-Export' } });
    fake.ackQueue.push({
      request_id: 'export-pack',
      ok: true,
      show_pack_export: {
        package_id: 'friday-export',
        directory_name: 'friday-export.show-pack',
        artifact_count: 8,
      },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Export draft local pack' }));
    const exportCommand = await waitForCommand(fake, 'show_bank_export');
    expect(exportCommand).toMatchObject({ artifact_name: 'friday-export' });
    expect(exportCommand).not.toHaveProperty('destination_path');
    expect(fake.sent.find((command) => command.type === 'show_bank_import')).not.toHaveProperty('source_path');
    expect(await screen.findByText(/Exported friday-export/)).toHaveTextContent(
      'friday-export.show-pack: 8 files',
    );
  });

  it('keeps safe-name import usable when the server has no active bank', async () => {
    const fake = new FakeCockpitClient();
    mount(fake, {
      ...showBankState,
      revision: 0,
      active_bank_id: null,
      banks: [],
    });
    await waitForCommand(fake, 'show_bank_list');

    expect(screen.getByText(/Import available · select a bank to export/)).toBeInTheDocument();
    expect(screen.queryByLabelText('Export package ID')).toBeNull();
    fireEvent.change(screen.getByLabelText('Import package ID'), {
      target: { value: 'recovery_pack' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Import local pack' }));
    expect(await waitForCommand(fake, 'show_bank_import')).toEqual({
      type: 'show_bank_import',
      pack_name: 'recovery_pack',
    });
  });

  it('uses only projected server depth presets for buttons and keyboard shortcuts', async () => {
    const fake = new FakeCockpitClient();
    mount(fake, {
      ...showBankState,
      depth_presets: { small: 0.2, medium: 0.4, large: 0.8 },
    });
    await waitForCommand(fake, 'show_bank_list');

    const small = screen.getByRole('button', { name: 'Small · 20%' });
    fireEvent.click(small);
    fireEvent.change(screen.getByLabelText('Candidate count'), { target: { value: '2' } });
    fireEvent.click(screen.getByRole('button', { name: 'Forge 2 candidate pairs' }));
    expect(await waitForCommand(fake, 'show_bank_generate_candidates')).toMatchObject({
      depth_preset: 'small',
      depth: 0.2,
    });

    fireEvent.keyDown(screen.getByTestId('show-kit-forge'), { key: '3' });
    expect(screen.getByRole('button', { name: 'Large · 80%' })).toHaveAttribute(
      'aria-pressed',
      'true',
    );
  });

  it('separates whole-bank readiness from the selected cue readiness', async () => {
    const fake = new FakeCockpitClient();
    mount(fake);
    await waitForCommand(fake, 'show_bank_list');

    fireEvent.click(screen.getByRole('button', { name: /2\. Peak Release/ }));
    expect(await screen.findByText('Bank: Manually saved — attested/unverified')).toBeInTheDocument();
    expect(screen.getByText('Active cue: Show-ready')).toBeInTheDocument();
    expect(screen.getByText('Bank blocked reasons')).toBeInTheDocument();
    expect(screen.getByText('Active cue blocked reasons — Peak Release')).toBeInTheDocument();
  });

  it('labels an entry-owned historical Rytm audition without inferring current hardware state', async () => {
    const historicalEntry = {
      ...forgeEntry,
      rytm_audition_status: 'historical_audition_hardware_unknown' as const,
    };
    const fake = new FakeCockpitClient();
    mount(fake, {
      ...showBankState,
      banks: [
        {
          ...(showBankState.banks[0] as NonNullable<(typeof showBankState.banks)[number]>),
          active_entry_id: historicalEntry.entry_id,
          entries: [historicalEntry],
        },
      ],
    });
    await waitForCommand(fake, 'show_bank_list');

    expect(screen.getByText('Historical audition — hardware state unknown')).toBeInTheDocument();
    expect(screen.getByText(/Entry audition record: candidate/)).toHaveTextContent('candidate-one');
    expect(screen.getByText(/This Cockpit session has 2 unsaved send/)).toHaveTextContent(
      'server does not attribute live unsaved hardware to this cue',
    );
  });

  it('renders sparse server truth without inventing candidates, captures, OXI, or readiness', async () => {
    const sparseEntry = {
      ...forgeEntry,
      name: 'Sparse Cue',
      status: 'source' as const,
      rytm_audition_status: 'not_auditioned' as const,
      rytm_source: { ...forgeEntry.rytm_source, hardware_slot: null },
      analog_four_source: { ...forgeEntry.analog_four_source, hardware_slot: null },
      candidates: [],
      selected_candidate_id: null,
      favorite: null,
      rytm_hardware_save: null,
      analog_four_hardware_save: null,
      rytm_recapture: null,
      analog_four_recapture: null,
      oxi: { project: '', pattern: '', chapter: '', direct_oxi_control: false as const },
      recovery_notes: [],
      readiness: {
        status: 'source' as const,
        show_ready: false,
        blocked_reasons: [],
        recovery_actions: ['reload sparse source'],
      },
    };
    const sparseState: ShowBankState = {
      ...showBankState,
      banks: [
        {
          ...(showBankState.banks[0] as NonNullable<(typeof showBankState.banks)[number]>),
          active_entry_id: sparseEntry.entry_id,
          entries: [sparseEntry],
        },
      ],
    };
    const fake = new FakeCockpitClient();
    mount(fake, sparseState);
    await waitForCommand(fake, 'show_bank_list');

    act(() => {
      useCockpitStore.setState({ kitCaptures: [], profile: null, sessionStatus: null });
    });

    expect(screen.getByText('Two verified captures required')).toBeInTheDocument();
    expect(screen.getAllByText('No current capture.')).toHaveLength(2);
    expect(screen.getByText('Select a Cockpit profile first')).toBeInTheDocument();
    expect(screen.getByText('No candidates yet. Source state remains unchanged.')).toBeInTheDocument();
    expect(screen.getByText('No candidate selected')).toBeInTheDocument();
    expect(screen.getByText('Not auditioned')).toBeInTheDocument();
    expect(screen.getByText(/mark it favorite before recording/)).toBeInTheDocument();
    expect(screen.getAllByText(/Not reported/).length).toBeGreaterThan(0);
    expect(screen.getByRole('row', { name: /Sparse Cue/ })).toHaveTextContent('— / — / —');
    expect(screen.getByRole('row', { name: /Sparse Cue/ })).toHaveTextContent(
      'reload sparse source',
    );

    const emptyRecoveryEntry = {
      ...sparseEntry,
      readiness: { ...sparseEntry.readiness, recovery_actions: [] },
    };
    act(() => {
      useCockpitStore.setState({
        showBank: {
          ...sparseState,
          banks: [
            {
              ...(sparseState.banks[0] as NonNullable<(typeof sparseState.banks)[number]>),
              entries: [emptyRecoveryEntry],
            },
          ],
        },
      });
    });
    expect(screen.getByRole('row', { name: /Sparse Cue/ })).toHaveTextContent('—');
  });
});
