import { act, renderHook, waitFor } from '@testing-library/react';

import { useAppliance } from '../../src/appliance/useAppliance';
import type { CommandAck } from '../../src/ws/protocol';

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
});
