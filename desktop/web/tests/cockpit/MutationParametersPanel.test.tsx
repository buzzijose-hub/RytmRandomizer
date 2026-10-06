import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { CockpitClientProvider } from '../../src/cockpit/context';
import { ActionBar } from '../../src/cockpit/ActionBar';
import { MutationParametersPanel } from '../../src/cockpit/panels/MutationParametersPanel';
import { bindClientToStore, useCockpitStore } from '../../src/state';
import { isEvent } from '../../src/ws/protocol';
import { runAxe } from '../a11y/__helpers__/axe';
import { candidate, FakeCockpitClient, readyDualMachineStage, sendPlan, sessionLive, sessionMock, snapshot } from './_fixtures';
import { parameterEvent } from './parameterScopeFixture';
import { forgeCaptures } from './showKitForgeFixture';
import type { CommandAck } from '../../src/ws/protocol';

function mount(fake = new FakeCockpitClient()) {
  return { fake, ...render(<CockpitClientProvider client={fake.asClient()}><MutationParametersPanel /></CockpitClientProvider>) };
}
function ready(): void {
  useCockpitStore.getState().setMutationParameters(parameterEvent);
  useCockpitStore.setState({ connectionStatus: 'connected', snapshot });
}
function pad2(): void { fireEvent.change(screen.getByLabelText('Parameter scope item'), { target: { value: '2' } }); }
async function click(name: string): Promise<void> {
  await act(async () => { fireEvent.click(screen.getByRole('button', { name })); });
}

beforeEach(() => useCockpitStore.getState().reset());
afterEach(() => useCockpitStore.getState().reset());

describe('Studio canonical parameter scope', () => {
  it('does not invent a source identity from display controls', () => {
    ready();
    useCockpitStore.setState({ snapshot: null });
    mount();
    expect(screen.getByText('not available', { selector: 'code' })).toBeVisible();
  });
  it('fails closed without fresh canonical controls', () => {
    const { fake } = mount();
    expect(screen.getByText(/Canonical parameter scope unavailable/)).toBeVisible();
    expect(screen.getByRole('button', { name: 'Pad 2 rehearsal' })).toBeDisabled();
    expect(screen.getByLabelText('Parameter scope item')).toBeDisabled();
    expect(fake.sent).toEqual([]);
  });
  it('uses native canonical fields and retains explicit none versus legacy all', async () => {
    ready();
    const { fake } = mount();
    pad2();
    expect(screen.getByRole('checkbox', { name: 'Mutate Pad 2 Filter Frequency' })).toBeChecked();
    expect(screen.getByText('Source 64')).toBeVisible();
    useCockpitStore.setState({ previewCandidate: { ...candidate, pad_deltas: [{ pad_id: 2, changed_keys: ['flt'], proposed_params: { flt: 66 } }] }, sendPlan });
    expect(await screen.findByText('Proposal 66')).toBeVisible();
    await click('Select none');
    expect(fake.sent.at(-1)).toEqual({ type: 'set_mutation_parameters', device_id: 'analog_rytm_mk2', parameter_cells: [] });
    expect(useCockpitStore.getState().previewCandidate).toBeNull();
    expect(useCockpitStore.getState().sendPlan).toBeNull();
    await click('Legacy all');
    expect(fake.sent.at(-1)).toMatchObject({ parameter_cells: null });
    await click('Clear page');
    expect(useCockpitStore.getState().rytmParameters).not.toContainEqual({ item_id: 2, parameter_key: 'flt' });
    expect(useCockpitStore.getState().rytmParameters).toContainEqual({ item_id: 1, parameter_key: 'src_bd_hard_decay' });
    await click('Select page');
    expect(useCockpitStore.getState().rytmParameters).toContainEqual({ item_id: 2, parameter_key: 'flt' });
  });
  it('selects individual/page/all cells while honoring locked, protected and missing rows', async () => {
    ready();
    mount();
    pad2();
    await click('Select none');
    await act(async () => { fireEvent.click(screen.getByRole('checkbox', { name: 'Mutate Pad 2 Filter Frequency' })); });
    expect(useCockpitStore.getState().rytmParameters).toEqual([{ item_id: 2, parameter_key: 'flt' }]);
    await act(async () => { fireEvent.click(screen.getByRole('checkbox', { name: 'Mutate Pad 2 Filter Frequency' })); });
    expect(useCockpitStore.getState().rytmParameters).toEqual([]);
    await click('Select all eligible');
    expect(useCockpitStore.getState().rytmParameters).toHaveLength(6);
    fireEvent.click(screen.getByRole('tab', { name: 'SRC' }));
    for (const name of ['Tune', 'Missing source', 'Synth Level']) expect(screen.getByRole('checkbox', { name: `Mutate Pad 2 ${name}` })).toBeDisabled();
    expect(screen.getByText('Mandatory protection')).toBeVisible();
    expect(screen.getByText('Source value unavailable')).toBeVisible();
    expect(screen.getByText('Range ? to ?')).toBeVisible();
    fireEvent.click(screen.getByRole('tab', { name: 'AMP' }));
    expect(screen.getByText('Source 12')).toBeVisible();
    await act(async () => { fireEvent.click(screen.getByLabelText('Lock pad')); });
    expect(screen.getByRole('checkbox', { name: 'Mutate Pad 2 Amp Decay Time' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Select page' })).toBeDisabled();
    await act(async () => { fireEvent.click(screen.getByLabelText('Lock pad')); });
    expect(screen.getByRole('checkbox', { name: 'Mutate Pad 2 Amp Decay Time' })).toBeEnabled();
    act(() => useCockpitStore.getState().setMutationTargets([1], []));
    expect(screen.getByRole('checkbox', { name: 'Mutate Pad 2 Amp Decay Time' })).toBeDisabled();
    expect(screen.getAllByText('Pad or track not targeted')).toHaveLength(3);
  });
  it('displays paired and CY Ride refusals without granting live-send eligibility', async () => {
    ready();
    mount();
    pad2();
    fireEvent.click(screen.getByRole('tab', { name: 'LFO' }));
    expect(screen.getByText('paired control precision unverified')).toBeVisible();
    expect(screen.getByText('Live send blocked')).toBeVisible();
    expect(screen.getByRole('checkbox', { name: 'Mutate Pad 2 LFO Depth' })).toBeEnabled();
    fireEvent.change(screen.getByLabelText('Parameter scope item'), { target: { value: '11' } });
    expect(screen.getByRole('checkbox', { name: 'Mutate Pad 11 Tail Decay' })).toBeDisabled();
    expect(screen.getByText('src cy ride slot unverified')).toBeVisible();
    expect(screen.getByRole('button', { name: 'Select page' })).toBeDisabled();
  });
  it('provides keyboard page tabs and canonical A4 precision only within offline scope', async () => {
    ready();
    useCockpitStore.getState().setKitCaptures(forgeCaptures);
    const { fake, container } = mount();
    pad2();
    const filter = screen.getByRole('tab', { name: 'FILTER' });
    fireEvent.keyDown(filter, { key: 'ArrowRight' });
    expect(screen.getByRole('tab', { name: 'AMP' })).toHaveAttribute('aria-selected', 'true');
    fireEvent.keyDown(screen.getByRole('tab', { name: 'AMP' }), { key: 'End' });
    expect(screen.getByRole('tab', { name: 'LFO' })).toHaveFocus();
    fireEvent.keyDown(screen.getByRole('tab', { name: 'LFO' }), { key: 'Home' });
    fireEvent.keyDown(filter, { key: 'Enter' });
    expect(filter).toHaveAttribute('aria-selected', 'true');
    fireEvent.change(screen.getByLabelText('Parameter scope device'), { target: { value: 'analog_four_mk2' } });
    expect(screen.getByText('Source 63.50')).toBeVisible();
    expect(screen.getByText('Native 16256 / unsigned_q8_8')).toBeVisible();
    expect(screen.getByText('A4 offline only; SEND blocked')).toBeVisible();
    await click('Select page');
    expect(fake.sent.at(-1)).toEqual({ type: 'set_mutation_parameters', device_id: 'analog_four_mk2', parameter_cells: [{ item_id: 1, parameter_key: 'filter1_frequency' }] });
    expect((await runAxe(container)).violations).toEqual([]);
    fireEvent.click(screen.getByRole('tab', { name: 'OSC1' }));
    expect(screen.getByRole('checkbox', { name: 'Mutate Track 1 OSC1 Tune' })).toBeDisabled();
  });
  it.each([{ message: 'capture Pad 2 first' }, { error: 'capture Pad 2 first' }, {}])('surfaces rejected rehearsal preset without claiming validation: %j', async (detail) => {
    ready();
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({ request_id: 'preset', ok: false, ...detail });
    mount(fake);
    await click('Pad 2 rehearsal');
    expect(screen.getByRole('alert')).toHaveTextContent(detail.message ?? detail.error ?? 'Preset refused.');
    expect(screen.getByText('Physical validation pending')).toBeVisible();
    expect(fake.sent).toEqual([{ type: 'set_rehearsal_preset', preset_id: 'rytm_pad2_common' }]);
  });
  it('applies the preset through the backend and names the correct pad', async () => {
    ready();
    const fake = new FakeCockpitClient();
    mount(fake);
    await click('Pad 2 rehearsal');
    expect(screen.getByLabelText('Parameter scope item')).toHaveValue('2');
    expect(useCockpitStore.getState().rytmParameters).toBeNull(); // no locally invented preset cells
    fake.nextRejection = 'offline';
    await click('Pad 2 rehearsal');
    expect(screen.getByRole('alert')).toHaveTextContent('offline');
  });
  it('closes an exact-plan confirmation immediately when the parameter scope changes', async () => {
    ready();
    useCockpitStore.setState({ previewCandidate: candidate, sendPlan, sessionStatus: sessionLive,
      dualMachineStage: readyDualMachineStage, rytmPadLocks: [2] });
    const fake = new FakeCockpitClient();
    render(<CockpitClientProvider client={fake.asClient()}>
      <MutationParametersPanel /><ActionBar previewOn onTogglePreview={() => undefined} />
    </CockpitClientProvider>);
    fireEvent.click(screen.getByTestId('action-send'));
    expect(screen.getByTestId('send-confirm-dialog')).toBeVisible();
    await click('Select none');
    expect(screen.queryByTestId('send-confirm-dialog')).not.toBeInTheDocument();
    expect(screen.getByTestId('action-send')).toBeDisabled();
    expect(fake.sent.some((command) => command.type === 'send')).toBe(false);
  });
  it('shows no-device metadata and source fallbacks without inventing values', () => {
    ready();
    act(() => useCockpitStore.getState().setMutationParameters({ ...parameterEvent, controls: [] }));
    mount();
    expect(screen.getByText('No canonical source controls available for this device.')).toBeVisible();
    expect(screen.queryByRole('tab')).not.toBeInTheDocument();
  });
  it('updates explicit pad targeting through the shared target hook', async () => {
    ready();
    const { fake } = mount();
    pad2();
    await act(async () => { fireEvent.click(screen.getByLabelText('Explicit target pad')); });
    expect(fake.sent.at(-1)).toEqual({ type: 'set_mutation_targets', device_id: 'analog_rytm_mk2', target_ids: [2] });
    expect(screen.getByLabelText('Explicit target pad')).toBeChecked();
  });
  it('refreshes metadata after bootstrap, new source and reconnect; old controls never authorize edits', async () => {
    ready();
    const fake = new FakeCockpitClient();
    const unbind = bindClientToStore(fake.asClient());
    useCockpitStore.getState().setSessionStatus(sessionMock);
    mount(fake);
    await act(async () => undefined);
    expect(fake.sent.at(-1)).toEqual({ type: 'get_mutation_parameters' });
    expect(screen.getByRole('button', { name: 'Pad 2 rehearsal' })).toBeDisabled();
    act(() => fake.emitEvent(parameterEvent));
    expect(isEvent(parameterEvent)).toBe(true);
    expect(screen.getByRole('button', { name: 'Pad 2 rehearsal' })).toBeEnabled();
    await act(async () => useCockpitStore.getState().setSnapshot({ ...snapshot, snapshot_id: 'new-source' }));
    expect(fake.sent.filter((command) => command.type === 'get_mutation_parameters')).toHaveLength(2);
    act(() => fake.emitEvent(parameterEvent));
    act(() => useCockpitStore.getState().setConnectionStatus('reconnecting'));
    await act(async () => { useCockpitStore.getState().setConnectionStatus('connected'); useCockpitStore.getState().setSessionStatus(sessionMock); });
    expect(fake.sent.filter((command) => command.type === 'get_mutation_parameters')).toHaveLength(3);
    unbind();
  });
  it.each([{ message: 'unavailable' }, { error: 'unavailable' }, {}])('logs metadata refusal and remains closed: %j', async (detail) => {
    ready();
    useCockpitStore.getState().setSessionStatus(sessionMock);
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({ request_id: 'get', ok: false, ...detail });
    mount(fake);
    await act(async () => undefined);
    expect(useCockpitStore.getState().operatorLog.at(-1)?.message).toContain('Parameter catalog refresh refused');
    expect(screen.getByRole('button', { name: 'Pad 2 rehearsal' })).toBeDisabled();
  });
  it.each([new Error('lost'), 'lost'])('logs metadata transport failure without retaining old metadata: %s', async (error) => {
    ready();
    useCockpitStore.getState().setSessionStatus(sessionMock);
    const fake = new FakeCockpitClient();
    fake.nextRejection = error;
    mount(fake);
    await act(async () => undefined);
    expect(useCockpitStore.getState().operatorLog.at(-1)?.message).toContain('Parameter catalog refresh failed: lost');
    expect(useCockpitStore.getState().parameterControls).toEqual([]);
  });
  it.each([false, true])('ignores obsolete catalog responses after unmount (reject=%s)', async (reject) => {
    ready();
    useCockpitStore.getState().setSessionStatus(sessionMock);
    const fake = new FakeCockpitClient();
    let resolve!: (ack: CommandAck) => void;
    let fail!: (error: Error) => void;
    fake.responseQueue.push(new Promise((done, refused) => { resolve = done; fail = refused; }));
    const view = mount(fake);
    view.unmount();
    await act(async () => {
      if (reject) fail(new Error('old request'));
      else resolve({ request_id: 'old', ok: false });
    });
    expect(useCockpitStore.getState().operatorLog).toEqual([]);
  });
});
