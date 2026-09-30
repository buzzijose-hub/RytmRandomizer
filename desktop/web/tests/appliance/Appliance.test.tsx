import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';

import { App } from '../../src/App';
import { Appliance } from '../../src/appliance/Appliance';
import { useCockpitStore } from '../../src/state';
import { isEvent, type ApplianceState } from '../../src/ws/protocol';
import { connectionListening, diagnosticsHealthy } from '../cockpit/_fixtures';

import { ApplianceFakeClient, applianceState, candidateState } from './fixtures';

async function mount(state = applianceState()): Promise<ApplianceFakeClient> {
  const fake = new ApplianceFakeClient(); fake.ackQueue.push({ request_id: 'state', ok: true, appliance: state });
  render(<Appliance client={fake.asClient()} />);
  await screen.findByRole('heading', { name: 'HOME / PERFORM' });
  return fake;
}
async function settled(fake: ApplianceFakeClient): Promise<void> { await waitFor(() => expect(screen.getByRole('status')).not.toHaveTextContent('BUSY')); expect(fake.sent.length).toBeGreaterThan(0); }
function click(name: string): void {
  const matches = screen.getAllByRole('button', { name });
  const button = matches.length > 1 ? within(screen.getByRole('navigation', { name: 'Appliance pages' })).getByRole('button', { name }) : matches[0]!;
  button.focus(); fireEvent.click(button);
}
function emit(fake: ApplianceFakeClient, state: ApplianceState): void { act(() => fake.emit({ type: 'appliance_changed', state })); }

beforeEach(() => { useCockpitStore.getState().reset(); window.location.hash = ''; delete window.__RYTM_RAND_ARM_SECRET__; window.localStorage.clear(); });
afterEach(() => { cleanup(); vi.restoreAllMocks(); delete window.__RYTM_RAND_ARM_SECRET__; window.location.hash = ''; });

describe('touch performance appliance', () => {
  it('mounts its route with disconnected truthful controls while preserving studio navigation', async () => {
    const fake = new ApplianceFakeClient(); fake.setStatus('closed'); window.location.hash = '#/appliance';
    render(<App client={fake.asClient()} />);
    expect(screen.getByTestId('appliance')).toBeInTheDocument(); expect(screen.getByText('DISCONNECTED')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'MUTATE' })).toBeDisabled();
    click('RETRY CONNECTION'); expect(fake.retryCalls).toBe(1);
    expect(screen.getByRole('link', { name: 'OPEN STUDIO' })).toHaveAttribute('href', '#/');
    expect(document.title).toMatch(/Appliance/);
    expect(isEvent({ type: 'appliance_changed', state: applianceState() })).toBe(true);
  });

  it('targets recognizable 12 pads without silently expanding an empty selection', async () => {
    const fake = await mount();
    expect(screen.getByText('SIMULATION / NO MIDI')).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: /^Pad \d+,/ })).toHaveLength(12);
    click('Pad 1, selected'); await settled(fake);
    expect(fake.sent.at(-1)).toMatchObject({ type: 'appliance', operation: 'scope', expected_revision: 3, payload: { lanes: { analog_rytm_mk2: { target_ids: [2] } } } });
    click('RYTM'); click('NONE'); await settled(fake);
    expect(fake.sent.at(-1)).toMatchObject({ payload: { lanes: { analog_rytm_mk2: { target_ids: [] } } } });
    const empty = applianceState(); empty.lanes.analog_rytm_mk2.scope.target_ids = []; emit(fake, empty);
    expect(screen.getByRole('button', { name: 'MUTATE' })).toBeDisabled();
    expect(screen.getByRole('status')).toHaveTextContent('choose unlocked tracks');
  });

  it('offers touch numeric master adjustment and guards zero depth', async () => {
    const fake = await mount(); click('MASTER 25 percent. Adjust');
    click('-10'); click('-1'); click('+1'); click('+10'); click('0%'); click('SET 0%'); await settled(fake);
    expect(fake.sent.at(-1)).toMatchObject({ operation: 'scope', payload: { master_depth: 0 } });
    emit(fake, applianceState({ master_depth: 0, revision: 4 }));
    expect(screen.getByRole('button', { name: 'MUTATE' })).toBeDisabled();
    expect(screen.getByRole('status')).toHaveTextContent('master depth zero');
    click('MASTER 0 percent. Adjust'); click('+10'); click('CANCEL');
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('publishes independent target/page/track depth and parameter protection rules', async () => {
    const fake = await mount(); click('RYTM');
    click('ALL 12'); await settled(fake); expect(fake.sent.at(-1)).toMatchObject({ payload: { lanes: { analog_rytm_mk2: { target_ids: Array.from({ length: 12 }, (_, i) => i + 1) } } } });
    fireEvent.change(screen.getByLabelText('Track to edit'), { target: { value: '2' } });
    click('TRACK 2 100 percent. Adjust'); click('50%'); click('SET 50%'); await settled(fake);
    expect(fake.sent.at(-1)).toMatchObject({ payload: { lanes: { analog_rytm_mk2: { track_depths: { '2': .5 } } } } });
    click('UNLOCK PAD 2'); await settled(fake); expect(fake.sent.at(-1)).toMatchObject({ payload: { lanes: { analog_rytm_mk2: { locked_ids: [] } } } });
    click('PAGES'); click('AMP OFF'); await settled(fake); expect(fake.sent.at(-1)).toMatchObject({ payload: { lanes: { analog_rytm_mk2: { page_ids: ['FILTER', 'AMP'] } } } });
    click('AMP 100 percent. Adjust'); click('75%'); click('SET 75%'); await settled(fake);
    expect(fake.sent.at(-1)).toMatchObject({ payload: { lanes: { analog_rytm_mk2: { page_depths: { AMP: .75 } } } } });
    click('PROTECT'); click('Protect CUTOFF'); await settled(fake);
    expect(fake.sent.at(-1)).toMatchObject({ payload: { lanes: { analog_rytm_mk2: { parameter_locks: ['pitch', 'cutoff'] } } } });
    click('Unlock TUNING'); await settled(fake);
    expect(fake.sent.at(-1)).toMatchObject({ payload: { lanes: { analog_rytm_mk2: { parameter_locks: [] } } } });
    expect(screen.getByRole('button', { name: 'Unlock ROUTING' })).toBeDisabled();
    fireEvent.change(screen.getByLabelText('Parameter page'), { target: { value: 'AMP' } });
    expect(screen.getByText(/capture mapping pending/)).toBeInTheDocument();
  });

  it('exposes four A4 tracks and both lanes with precision and linked-apply limitations', async () => {
    const fake = await mount(); click('A4'); await settled(fake);
    expect(screen.getAllByRole('button', { name: /^Track \d+,/ })).toHaveLength(4);
    expect(screen.getByText(/A4 SIMULATED 7-BIT VALUES/)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Track to edit'), { target: { value: '3' } }); click('PROTECT TRACK 3'); await settled(fake);
    expect(fake.sent.at(-1)).toMatchObject({ payload: { lanes: { analog_four_mk2: { locked_ids: [2, 3] } } } });
    click('BOTH'); await settled(fake); expect(screen.getByText(/not atomic/)).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: /^Pad \d+,/ })).toHaveLength(12);
    expect(screen.getAllByRole('button', { name: /^Track \d+,/ })).toHaveLength(4);
    expect(fake.sent.at(-1)).toMatchObject({ payload: { target: 'both' } });
  });

  it('confirms one exact candidate and keeps simulated apply local', async () => {
    const fake = await mount(candidateState()); click('LOCAL APPLY…');
    expect(screen.getByRole('dialog')).toHaveTextContent('No output port is opened');
    expect(screen.getByRole('dialog')).toHaveTextContent('candidate-3');
    expect(within(screen.getByRole('dialog')).getByText('68')).toBeInTheDocument();
    click('CONFIRM LOCAL APPLY'); await settled(fake);
    expect(fake.sent.at(-1)).toEqual({ type: 'appliance', operation: 'apply', expected_revision: 3, payload: { candidate_id: 'candidate-3', confirmed: true } });
    expect(fake.sent.some((command) => command.type === 'send' || command.type === 'arm')).toBe(false);
  });

  it('closes exact and numeric dialogs on revision changes and disconnect', async () => {
    const fake = await mount(candidateState()); click('LOCAL APPLY…');
    emit(fake, candidateStateWithRevision(4)); await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    click('MASTER 25 percent. Adjust'); emit(fake, candidateStateWithRevision(5));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    click('LOCAL APPLY…'); act(() => fake.setStatus('reconnecting'));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument(); expect(screen.getByText('DISCONNECTED')).toBeInTheDocument();
    expect(fake.sent.filter((command) => command.type === 'appliance' && command.operation === 'apply')).toHaveLength(0);
  });

  it('keeps unverified production apply blocked and distinguishes capture from hardware restore', async () => {
    const production = candidateState(); production.mode = 'production'; production.candidate!.blocked_reasons = ['working_state_readback_unverified'];
    const fake = await mount(production); expect(screen.getByRole('button', { name: 'APPLY…' })).toBeDisabled();
    expect(screen.getByText('working state readback unverified')).toBeInTheDocument();
    click('HISTORY'); expect(screen.getByText(/do not restore an instrument/)).toBeInTheDocument();
    click('LOCAL REDO'); await settled(fake); expect(fake.sent.at(-1)).toMatchObject({ operation: 'redo' });
    click('RETURN TO ANCHOR / LOCAL'); await settled(fake); expect(fake.sent.at(-1)).toMatchObject({ operation: 'return_anchor' });
    click('NEW ANCHOR…'); expect(screen.getByRole('dialog')).toHaveTextContent('does not request a capture'); click('ADOPT KNOWN BASELINE'); await settled(fake);
    expect(fake.sent.at(-1)).toMatchObject({ operation: 'anchor' });
    click('UNDO / LOCAL'); await settled(fake); expect(fake.sent.at(-1)).toMatchObject({ operation: 'undo' });
  });

  it('uses existing exact arm/disarm service and refuses ambiguous endpoints', async () => {
    const fake = await mount(applianceState({ mode: 'production' }));
    act(() => useCockpitStore.getState().setConnection({ ...connectionListening, available_outputs: ['RYTM OUT', 'DUPLICATE', 'DUPLICATE'] }));
    click('ARM…'); expect(screen.getByRole('button', { name: 'CONFIRM ARM' })).toBeDisabled();
    expect(screen.getByText(/Arm secret unavailable/)).toBeInTheDocument(); click('CANCEL');
    window.__RYTM_RAND_ARM_SECRET__ = 'test-secret'; click('ARM…');
    fireEvent.change(screen.getByLabelText('Exact MIDI output'), { target: { value: 'DUPLICATE' } }); expect(screen.getByRole('button', { name: 'CONFIRM ARM' })).toBeDisabled();
    fireEvent.change(screen.getByLabelText('Exact MIDI output'), { target: { value: 'RYTM OUT' } }); click('CONFIRM ARM'); await settled(fake);
    expect(fake.sent).toContainEqual({ type: 'arm', arm_token: 'test-secret', confirm: true, port_name: 'RYTM OUT' });
    emit(fake, applianceState({ mode: 'production', armed: true, revision: 4 })); click('DISARM'); await settled(fake);
    expect(fake.sent).toContainEqual({ type: 'disarm' });
  });

  it('renders exact live confirmation only from current backend live-ready authority', async () => {
    const ready = candidateState(); ready.mode = 'production'; ready.armed = true; ready.candidate!.live_ready = true; ready.candidate!.send_plan_id = 'exact-plan';
    useCockpitStore.getState().setConnection(connectionListening);
    const fake = await mount(ready); click('APPLY…'); expect(screen.getByRole('dialog')).toHaveTextContent('exact-plan');
    click('CONFIRM EXACT APPLY'); await settled(fake); expect(fake.sent.at(-1)).toMatchObject({ payload: { candidate_id: 'candidate-3', confirmed: true, send_plan_id: 'exact-plan' } });
  });

  it('saves and recalls associated profiles and names them entirely through touch', async () => {
    const fake = await mount(); click('MORE'); click('NAME: PERFORMANCE 1'); click('CLEAR'); click('A'); click('B'); click('BACKSPACE'); click('SPACE'); click('1'); click('DONE');
    click('SAVE RULES'); await settled(fake); expect(fake.sent.at(-1)).toMatchObject({ operation: 'profile_save', payload: { name: 'A 1' } });
    click('RECALL'); await settled(fake); expect(fake.sent.at(-1)).toMatchObject({ operation: 'profile_load', payload: { name: 'SAFE' } });
    click('DELETE'); expect(screen.getByRole('dialog')).toHaveTextContent('SAFE'); click('DELETE SAFE'); await settled(fake);
    expect(fake.sent.at(-1)).toMatchObject({ operation: 'profile_delete', payload: { name: 'SAFE' } });
  });

  it('imports JSON through validated backend and categorizes corrupt/oversized files', async () => {
    const fake = await mount(); click('MORE'); click('IMPORT');
    const input = screen.getByLabelText('Import profile document');
    const valid = new File(['{}'], 'profile.json', { type: 'application/json' }); Object.defineProperty(valid, 'text', { value: () => Promise.resolve('{"schema_version":1}') });
    fireEvent.change(input, { target: { files: [valid] } }); await waitFor(() => expect(fake.sent.at(-1)).toMatchObject({ operation: 'profile_import', payload: { document: { schema_version: 1 } } }));
    const corrupt = new File(['x'], 'corrupt.json'); Object.defineProperty(corrupt, 'text', { value: () => Promise.resolve('x') });
    fireEvent.change(input, { target: { files: [corrupt] } }); await screen.findByText(/Profile JSON is corrupt/);
    fireEvent.change(input, { target: { files: [new File(['x'.repeat(262145)], 'too-large.json')] } }); expect(screen.getByText(/exceeds 256 KiB/)).toBeInTheDocument();
  });

  it('exports server-validated profile without persisting transient authority', async () => {
    const fake = await mount(); click('MORE');
    const create = vi.fn(() => 'blob:profile'); const revoke = vi.fn(); URL.createObjectURL = create; URL.revokeObjectURL = revoke;
    const anchorClick = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);
    fake.ackQueue.push({ request_id: 'export', ok: true, document: { schema_version: 1, profiles: {} } }); click('EXPORT');
    await screen.findByText(/Arming and live authority are excluded/); expect(create).toHaveBeenCalledOnce(); expect(revoke).toHaveBeenCalledWith('blob:profile'); expect(anchorClick).toHaveBeenCalledOnce();
    click('EXPORT'); await screen.findByText(/Profile export refused/);
  });

  it('requires an exact input and requests no automatic capture output', async () => {
    const fake = await mount(); click('CAPTURE / RESYNC');
    fake.ackQueue.push({ request_id: 'scan', ok: true, capture_enabled: true, capture_inputs: ['RYTM IN'] }); click('SCAN INPUTS'); await settled(fake);
    expect(screen.getByRole('button', { name: 'LISTEN FOR KIT CAPTURE' })).toBeDisabled();
    fireEvent.change(screen.getByLabelText('Exact capture input'), { target: { value: 'RYTM IN' } }); click('LISTEN FOR KIT CAPTURE'); await settled(fake);
    expect(fake.sent).toContainEqual({ type: 'capture_current_kit', device_id: 'analog_rytm_mk2', input_port: 'RYTM IN' });
    expect(fake.sent.at(-1)).toMatchObject({ operation: 'state' });
    fireEvent.click(within(screen.getByRole('heading', { name: 'CONNECTION / CAPTURE' }).parentElement!).getByRole('button', { name: 'A4' })); fake.ackQueue.push({ request_id: 'scan', ok: true, capture_enabled: true, capture_inputs: ['A4 IN'] }); click('SCAN INPUTS'); await settled(fake);
    expect(fake.sent.at(-1)).toEqual({ type: 'list_capture_inputs', device_id: 'analog_four_mk2' });
    expect(screen.getByText(/No automatic request/)).toBeInTheDocument();
  });

  it('reads existing diagnostics and offers reduced motion and the full studio', async () => {
    const fake = await mount(applianceState({ blocked_reasons: ['storage_corrupt'] })); click('MORE'); click('DIAGNOSTICS');
    fake.ackQueue.push({ request_id: 'diag', ok: true, diagnostics: diagnosticsHealthy }); click('READ HEALTH'); await settled(fake);
    expect(screen.getByText('darwin')).toBeInTheDocument(); expect(screen.getByText('storage corrupt')).toBeInTheDocument();
    click('MOTION SYSTEM'); expect(screen.getByRole('button', { name: 'MOTION REDUCED' })).toHaveAttribute('aria-pressed', 'true');
    click('RETRY CONNECTION'); expect(fake.retryCalls).toBe(1); expect(screen.getByRole('link', { name: 'STUDIO VIEW' })).toHaveAttribute('href', '#/');
  });

  it('uses keyboard focus trapping, visible cancel and escape for numeric touch dialog', async () => {
    await mount(); click('MASTER 25 percent. Adjust');
    const dialog = screen.getByRole('dialog'); const close = within(dialog).getByRole('button', { name: 'Close dialog' });
    expect(close).toHaveFocus(); fireEvent.keyDown(dialog, { key: 'Tab', shiftKey: true }); expect(within(dialog).getByRole('button', { name: 'SET 25%' })).toHaveFocus();
    fireEvent.keyDown(dialog, { key: 'Tab' }); expect(close).toHaveFocus(); fireEvent.keyDown(dialog, { key: 'Escape' });
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument(); expect(screen.getByRole('button', { name: 'MASTER 25 percent. Adjust' })).toHaveFocus();
  });
});

function candidateStateWithRevision(revision: number): ApplianceState { const state = candidateState(); state.revision = revision; state.candidate!.revision = revision; return state; }
