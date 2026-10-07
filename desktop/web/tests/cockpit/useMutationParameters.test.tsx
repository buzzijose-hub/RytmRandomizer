import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { CockpitClientProvider } from '../../src/cockpit/context';
import { useMutationParameters } from '../../src/cockpit/useMutationParameters';
import { useCockpitStore } from '../../src/state';
import type { CockpitDeviceId } from '../../src/cockpit/devices';
import type { CommandAck } from '../../src/ws/protocol';
import { candidate, FakeCockpitClient, sendPlan } from './_fixtures';
import { parameterEvent } from './parameterScopeFixture';

function mount(fake: FakeCockpitClient) {
  return renderHook(({ deviceId }: { deviceId: CockpitDeviceId }) => useMutationParameters(deviceId), {
    initialProps: { deviceId: 'analog_rytm_mk2' },
    wrapper: ({ children }) => <CockpitClientProvider client={fake.asClient()}>{children}</CockpitClientProvider>,
  });
}

beforeEach(() => useCockpitStore.getState().reset());
afterEach(() => useCockpitStore.getState().reset());

describe('parameter selection requests', () => {
  it('sends explicit empty/legacy scope and clears candidates and plans before acknowledgment', async () => {
    const fake = new FakeCockpitClient();
    useCockpitStore.setState({ previewCandidate: candidate, sendPlan });
    const hook = mount(fake);
    await act(async () => hook.result.current.replace([]));
    expect(useCockpitStore.getState().rytmParameters).toEqual([]);
    expect(useCockpitStore.getState().previewCandidate).toBeNull();
    expect(useCockpitStore.getState().sendPlan).toBeNull();
    await act(async () => hook.result.current.replace(null));
    expect(fake.sent).toEqual([
      { type: 'set_mutation_parameters', device_id: 'analog_rytm_mk2', parameter_cells: [] },
      { type: 'set_mutation_parameters', device_id: 'analog_rytm_mk2', parameter_cells: null },
    ]);
  });
  it('changes A4 offline scope without disturbing Rytm cells', async () => {
    useCockpitStore.getState().setMutationParameters({ ...parameterEvent, rytm_parameters: [{ item_id: 2, parameter_key: 'flt' }] });
    const fake = new FakeCockpitClient();
    const hook = mount(fake);
    hook.rerender({ deviceId: 'analog_four_mk2' });
    await act(async () => hook.result.current.replace(null));
    expect(useCockpitStore.getState().a4Parameters).toBeNull();
    expect(useCockpitStore.getState().rytmParameters).toEqual([{ item_id: 2, parameter_key: 'flt' }]);
  });
  it.each([{ message: 'invalid cell' }, { error: 'invalid cell' }, {}])('rolls back current rejection but never restores a plan: %j', async (detail) => {
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({ request_id: 'no', ok: false, ...detail });
    const hook = mount(fake);
    await act(async () => hook.result.current.replace([]));
    expect(useCockpitStore.getState().rytmParameters).toBeNull();
    expect(useCockpitStore.getState().sendPlan).toBeNull();
    expect(useCockpitStore.getState().operatorLog.at(-1)?.message).toContain('Parameter scope rejected');
  });
  it.each([new Error('socket lost'), 'socket lost'])('reports transport failure and safely restores selection: %s', async (error) => {
    const fake = new FakeCockpitClient();
    fake.nextRejection = error;
    const hook = mount(fake);
    await act(async () => hook.result.current.replace([]));
    expect(useCockpitStore.getState().rytmParameters).toBeNull();
    expect(useCockpitStore.getState().operatorLog.at(-1)?.message).toContain('socket lost');
  });
  it('rolls back rejected A4 selection without altering Rytm scope', async () => {
    useCockpitStore.getState().setMutationParameters({ ...parameterEvent, rytm_parameters: [] });
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({ request_id: 'no', ok: false });
    const hook = mount(fake);
    hook.rerender({ deviceId: 'analog_four_mk2' });
    await act(async () => hook.result.current.replace(null));
    expect(useCockpitStore.getState().a4Parameters).toEqual([]);
    expect(useCockpitStore.getState().rytmParameters).toEqual([]);
  });
  it.each(['event', 'lock', 'newer', 'device', 'unmount'] as const)('does not roll back a delayed refusal after %s', async (change) => {
    const fake = new FakeCockpitClient();
    let resolve!: (ack: CommandAck) => void;
    fake.responseQueue.push(new Promise((done) => { resolve = done; }));
    const hook = mount(fake);
    act(() => hook.result.current.replace([]));
    act(() => {
      if (change === 'event') useCockpitStore.getState().setMutationParameters({ ...parameterEvent, rytm_parameters: [] });
      if (change === 'lock') useCockpitStore.getState().setRytmPadLocks([2]);
      if (change === 'newer') hook.result.current.replace([{ item_id: 2, parameter_key: 'flt' }]);
      if (change === 'device') hook.rerender({ deviceId: 'analog_four_mk2' });
      if (change === 'unmount') hook.unmount();
    });
    await act(async () => resolve({ request_id: 'old', ok: false }));
    expect(useCockpitStore.getState().rytmParameters).toEqual(change === 'newer' ? [{ item_id: 2, parameter_key: 'flt' }] : []);
    expect(useCockpitStore.getState().sendPlan).toBeNull();
  });
});
