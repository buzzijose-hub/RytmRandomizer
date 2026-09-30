import { act, renderHook, waitFor } from '@testing-library/react';

import { useAppliance } from '../../src/appliance/useAppliance';
import type { CommandAck, Event } from '../../src/ws/protocol';
import { connectionListening, readyDualMachineStage, snapshot } from '../cockpit/_fixtures';

import { ApplianceFakeClient, applianceState } from './fixtures';

describe('authenticated appliance controller', () => {
  it('requests fresh whole state and publishes revision-bound commands', async () => {
    const fake = new ApplianceFakeClient();
    fake.ackQueue.push({ request_id: 'state', ok: true, appliance: applianceState() });
    const { result } = renderHook(() => useAppliance(fake.asClient()));
    await waitFor(() => expect(result.current.state?.revision).toBe(3));
    expect(fake.sent[0]).toEqual({ type: 'appliance', operation: 'state' });
    fake.ackQueue.push({ request_id: 'scope', ok: true, appliance: applianceState({ revision: 4 }), message: 'Scope accepted' });
    await act(async () => { await result.current.execute('scope', { master_depth: 0 }); });
    expect(fake.sent[1]).toEqual({ type: 'appliance', operation: 'scope', expected_revision: 3, payload: { master_depth: 0 } });
    expect(result.current.state?.revision).toBe(4);
    expect(result.current.notice).toBe('Scope accepted');
  });

  it('does not act while disconnected and drops authority before reconnect bootstrap', async () => {
    const fake = new ApplianceFakeClient(); fake.setStatus('closed');
    const { result } = renderHook(() => useAppliance(fake.asClient()));
    await act(async () => { expect(await result.current.execute('mutate')).toBeNull(); expect(await result.current.execute('state')).toBeNull(); });
    expect(fake.sent).toHaveLength(0);
    fake.ackQueue.push({ request_id: 'state', ok: true, appliance: applianceState() });
    act(() => fake.setStatus('connected'));
    await waitFor(() => expect(result.current.state).not.toBeNull());
    act(() => fake.setStatus('reconnecting'));
    expect(result.current.state).toBeNull();
    expect(result.current.notice).toMatch(/Fresh state/);
  });

  it('refuses duplicate clicks synchronously and ignores late ack after disconnect', async () => {
    const fake = new ApplianceFakeClient(); fake.ackQueue.push({ request_id: 'state', ok: true, appliance: applianceState() });
    const { result } = renderHook(() => useAppliance(fake.asClient()));
    await waitFor(() => expect(result.current.state).not.toBeNull());
    let resolve!: (ack: CommandAck) => void;
    fake.responseQueue.push(new Promise((done) => { resolve = done; }));
    let pending!: Promise<CommandAck | null>;
    act(() => { pending = result.current.execute('mutate'); });
    await act(async () => { expect(await result.current.execute('mutate')).toBeNull(); });
    expect(fake.sent).toHaveLength(2);
    act(() => fake.setStatus('closed'));
    await act(async () => { resolve({ request_id: 'late', ok: true, appliance: applianceState({ armed: true }) }); expect(await pending).toBeNull(); });
    expect(result.current.state).toBeNull(); expect(result.current.busy).toBe(false);
  });

  it('applies whole events and surfaces categorized refusal and transport errors', async () => {
    const fake = new ApplianceFakeClient(); fake.ackQueue.push({ request_id: 'state', ok: true, appliance: applianceState() });
    const { result, unmount } = renderHook(() => useAppliance(fake.asClient()));
    await waitFor(() => expect(result.current.state).not.toBeNull());
    act(() => fake.emit({ type: 'appliance_changed', state: applianceState({ revision: 7 }) }));
    expect(result.current.state?.revision).toBe(7);
    fake.ackQueue.push({ request_id: 'no', ok: false, code: 'appliance.stale_revision' });
    await act(async () => { await result.current.execute('mutate'); });
    expect(result.current.notice).toBe('appliance.stale_revision');
    fake.nextRejection = new Error('closed');
    await act(async () => { expect(await result.current.command({ type: 'diagnostics' }, 10)).toBeNull(); });
    expect(result.current.notice).toMatch(/interrupted/);
    unmount();
  });

  it('explains unsupported bootstrap instead of fabricating demo state', async () => {
    const fake = new ApplianceFakeClient();
    const { result } = renderHook(() => useAppliance(fake.asClient()));
    await waitFor(() => expect(result.current.notice).toMatch(/Update the sidecar/));
    expect(result.current.state).toBeNull();
  });

  it('handles bootstrap rejection and unmount before a late bootstrap', async () => {
    const fake = new ApplianceFakeClient(); fake.nextRejection = new Error('no sidecar');
    const first = renderHook(() => useAppliance(fake.asClient()));
    await waitFor(() => expect(first.result.current.notice).toMatch(/No action was queued/));
    first.unmount();
    let resolve!: (ack: CommandAck) => void;
    fake.responseQueue.push(new Promise((done) => { resolve = done; }));
    const second = renderHook(() => useAppliance(fake.asClient())); second.unmount();
    await act(async () => resolve({ request_id: 'state', ok: true, appliance: applianceState() }));
  });

  it('lets disarm supersede a pending action and ignores its eventual result', async () => {
    const fake = new ApplianceFakeClient(); fake.ackQueue.push({ request_id: 'state', ok: true, appliance: applianceState({ armed: true }) });
    const { result } = renderHook(() => useAppliance(fake.asClient())); await waitFor(() => expect(result.current.state).not.toBeNull());
    let resolve!: (ack: CommandAck) => void; fake.responseQueue.push(new Promise((done) => { resolve = done; }));
    let pending!: Promise<CommandAck | null>; act(() => { pending = result.current.execute('mutate'); });
    await act(async () => { await result.current.command({ type: 'disarm' }); });
    expect(fake.sent.at(-1)).toEqual({ type: 'disarm' });
    await act(async () => { resolve({ request_id: 'old', ok: true, appliance: applianceState({ armed: true, revision: 8 }) }); await pending; });
    expect(result.current.state?.revision).toBe(3);
  });

  it('renders default refusal message and explicit bootstrap refusal', async () => {
    const fake = new ApplianceFakeClient(); fake.ackQueue.push({ request_id: 'state', ok: false, message: 'Upgrade required' });
    const { result } = renderHook(() => useAppliance(fake.asClient())); await waitFor(() => expect(result.current.notice).toBe('Upgrade required'));
    act(() => fake.emit({ type: 'appliance_changed', state: applianceState() }));
    fake.ackQueue.push({ request_id: 'refuse', ok: false }); await act(async () => { await result.current.execute('mutate'); });
    expect(result.current.notice).toMatch(/Command refused/);
    fake.ackQueue.push({ request_id: 'refuse', ok: false, message: 'Locked' }); await act(async () => { await result.current.execute('mutate'); }); expect(result.current.notice).toBe('Locked');
  });

  it('ignores rejected late commands and both resolved/rejected late bootstrap results', async () => {
    const fake = new ApplianceFakeClient(); fake.ackQueue.push({ request_id: 'state', ok: true, appliance: applianceState() });
    const { result, unmount } = renderHook(() => useAppliance(fake.asClient())); await waitFor(() => expect(result.current.state).not.toBeNull());
    let reject!: (reason: Error) => void; fake.responseQueue.push(new Promise((_resolve, fail) => { reject = fail; })); let pending!: Promise<CommandAck | null>;
    act(() => { pending = result.current.execute('mutate'); }); act(() => fake.setStatus('closed'));
    await act(async () => { reject(new Error('late')); await pending; }); expect(result.current.notice).toMatch(/Transport disconnected/); unmount();
    let resolve!: (ack: CommandAck) => void; fake.responseQueue.push(new Promise((done) => { resolve = done; })); fake.setStatus('connected');
    const late = renderHook(() => useAppliance(fake.asClient())); act(() => fake.setStatus('closed')); await act(async () => resolve({ request_id: 'late', ok: true, appliance: applianceState() })); expect(late.result.current.state).toBeNull(); late.unmount();
    fake.setStatus('connected'); fake.responseQueue.push(new Promise((_resolve, fail) => { reject = fail; })); const gone = renderHook(() => useAppliance(fake.asClient())); gone.unmount(); await act(async () => reject(new Error('late bootstrap')));
  });

  it('drops authority synchronously for each external capture, connection and Studio context event', async () => {
    const events: Event[] = [
      { type: 'connection_changed', connection: connectionListening },
      { type: 'kit_captures_changed', captures: [] },
      { type: 'snapshot_changed', snapshot },
      { type: 'performance_console_changed', performance_console: null },
      { type: 'show_bank_changed', show_bank: null },
      { type: 'dual_machine_stage_changed', stage: readyDualMachineStage },
      { type: 'profile_changed', profile: null },
    ];
    const fake = new ApplianceFakeClient(); fake.ackQueue.push({ request_id: 'state', ok: true, appliance: applianceState() });
    const { result, unmount } = renderHook(() => useAppliance(fake.asClient())); await waitFor(() => expect(result.current.state).not.toBeNull());
    for (const [index, event] of events.entries()) {
      let resolve!: (ack: CommandAck) => void; fake.responseQueue.push(new Promise((done) => { resolve = done; }));
      act(() => fake.emit(event));
      expect(result.current.getState()).toBeNull(); expect(result.current.state).toBeNull(); expect(result.current.pendingCommand).toBeNull();
      expect(fake.sent.at(-1)).toEqual({ type: 'appliance', operation: 'state' });
      await act(async () => { expect(await result.current.execute('apply', { confirmed: true })).toBeNull(); resolve({ request_id: 'fresh', ok: true, appliance: applianceState({ revision: 10 + index }) }); });
      expect(result.current.state?.revision).toBe(10 + index); expect(result.current.state?.candidate).toBeNull();
    }
    act(() => fake.setStatus('closed')); const count = fake.sent.length;
    act(() => fake.emit({ type: 'kit_captures_changed', captures: [] })); expect(fake.sent).toHaveLength(count); expect(result.current.state).toBeNull();
    unmount(); fake.emit({ type: 'profile_changed', profile: null }); expect(fake.sent).toHaveLength(count);
  });

  it('ignores an obsolete command and rejected bootstrap after external context changes', async () => {
    const fake = new ApplianceFakeClient(); fake.ackQueue.push({ request_id: 'state', ok: true, appliance: applianceState() });
    const { result } = renderHook(() => useAppliance(fake.asClient())); await waitFor(() => expect(result.current.state).not.toBeNull());
    let oldResolve!: (ack: CommandAck) => void; fake.responseQueue.push(new Promise((done) => { oldResolve = done; }));
    let pending!: Promise<CommandAck | null>; act(() => { pending = result.current.execute('mutate'); });
    let oldReject!: (error: Error) => void; fake.responseQueue.push(new Promise((_done, reject) => { oldReject = reject; }));
    act(() => fake.emit({ type: 'kit_captures_changed', captures: [] }));
    fake.ackQueue.push({ request_id: 'fresh', ok: true, appliance: applianceState({ revision: 9 }) });
    await act(async () => fake.emit({ type: 'profile_changed', profile: null }));
    await act(async () => { oldResolve({ request_id: 'old', ok: true, appliance: applianceState({ armed: true }) }); oldReject(new Error('obsolete state request')); expect(await pending).toBeNull(); });
    expect(result.current.state?.revision).toBe(9); expect(result.current.state?.armed).toBe(false); expect(result.current.busy).toBe(false); expect(result.current.notice).toMatch(/State received/);
  });
});
