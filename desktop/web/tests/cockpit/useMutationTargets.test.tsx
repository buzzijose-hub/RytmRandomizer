import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { CockpitClientProvider } from '../../src/cockpit/context';
import {
  ANALOG_FOUR_DEVICE_ID,
  RYTM_DEVICE_ID,
} from '../../src/cockpit/devices';
import { useMutationTargets } from '../../src/cockpit/useMutationTargets';
import { useCockpitStore } from '../../src/state';

import { candidate, enqueueRejection, FakeCockpitClient, patchGenome, sendPlan } from './_fixtures';

function wrapper(client: FakeCockpitClient) {
  return function Wrapper({ children }: { children: React.ReactNode }): JSX.Element {
    return <CockpitClientProvider client={client.asClient()}>{children}</CockpitClientProvider>;
  };
}

describe('useMutationTargets', () => {
  beforeEach(() => useCockpitStore.getState().reset());
  afterEach(() => useCockpitStore.getState().reset());

  it('treats an empty target list as the default all-scope behavior', () => {
    const fake = new FakeCockpitClient();
    const { result } = renderHook(() => useMutationTargets(RYTM_DEVICE_ID), {
      wrapper: wrapper(fake),
    });

    expect(result.current.hasExplicitTargets).toBe(false);
    expect(result.current.isTargeted(1)).toBe(true);
    expect(result.current.isTargeted(12)).toBe(true);
    act(() => result.current.clearTargets());
    expect(fake.sent).toEqual([]);
  });

  it('builds a Rytm multi-select include-list and clears the last selection', async () => {
    const fake = new FakeCockpitClient();
    const { result } = renderHook(() => useMutationTargets(RYTM_DEVICE_ID), {
      wrapper: wrapper(fake),
    });

    await act(async () => {
      result.current.toggleTarget(2);
      await Promise.resolve();
    });
    await act(async () => {
      result.current.toggleTarget(4);
      await Promise.resolve();
    });
    expect(result.current.targets).toEqual(new Set([2, 4]));
    expect(result.current.isTargeted(1)).toBe(false);
    expect(fake.sent.at(-1)).toEqual({
      type: 'set_mutation_targets',
      device_id: RYTM_DEVICE_ID,
      target_ids: [2, 4],
    });

    await act(async () => {
      result.current.toggleTarget(2);
      await Promise.resolve();
    });
    await act(async () => {
      result.current.toggleTarget(4);
      await Promise.resolve();
    });
    expect(fake.sent.at(-1)).toEqual({
      type: 'clear_mutation_targets',
      device_id: RYTM_DEVICE_ID,
    });
    expect(result.current.hasExplicitTargets).toBe(false);
  });

  it('sends Analog Four target replacements on the A4 device dimension', async () => {
    const fake = new FakeCockpitClient();
    useCockpitStore.getState().setPreviewCandidate(candidate);
    useCockpitStore.getState().setSendPlan(sendPlan);
    useCockpitStore.getState().setPatchGenome(patchGenome);
    const { result } = renderHook(() => useMutationTargets(ANALOG_FOUR_DEVICE_ID), {
      wrapper: wrapper(fake),
    });

    await act(async () => {
      result.current.toggleTarget(3);
      await Promise.resolve();
    });

    expect(fake.sent).toEqual([
      {
        type: 'set_mutation_targets',
        device_id: ANALOG_FOUR_DEVICE_ID,
        target_ids: [3],
      },
    ]);
    expect(useCockpitStore.getState().a4TrackTargets).toEqual([3]);
    expect(useCockpitStore.getState().previewCandidate).toBeNull();
    expect(useCockpitStore.getState().sendPlan).toBeNull();
    expect(useCockpitStore.getState().patchGenomeStale).toBe(true);
  });

  it('rolls back an optimistic target replacement when the server rejects it', async () => {
    const fake = new FakeCockpitClient();
    enqueueRejection(fake);
    const { result } = renderHook(() => useMutationTargets(RYTM_DEVICE_ID), {
      wrapper: wrapper(fake),
    });

    await act(async () => {
      result.current.toggleTarget(2);
      await Promise.resolve();
    });

    expect(result.current.hasExplicitTargets).toBe(false);
    expect(useCockpitStore.getState().rytmPadTargets).toEqual([]);
  });

  it('rolls back an optimistic target replacement on a transport error', async () => {
    const fake = new FakeCockpitClient();
    fake.nextRejection = new Error('socket not open');
    const { result } = renderHook(() => useMutationTargets(ANALOG_FOUR_DEVICE_ID), {
      wrapper: wrapper(fake),
    });

    await act(async () => {
      result.current.toggleTarget(3);
      await Promise.resolve();
    });

    expect(result.current.hasExplicitTargets).toBe(false);
    expect(useCockpitStore.getState().a4TrackTargets).toEqual([]);
  });

  it('uses the ack message when an A4 target replacement is rejected', async () => {
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({ request_id: 'a4-rejected', ok: false, message: 'mapping pending' });
    const { result } = renderHook(() => useMutationTargets(ANALOG_FOUR_DEVICE_ID), {
      wrapper: wrapper(fake),
    });

    await act(async () => {
      result.current.toggleTarget(4);
      await Promise.resolve();
    });

    expect(useCockpitStore.getState().a4TrackTargets).toEqual([]);
    expect(useCockpitStore.getState().operatorLog.at(-1)).toMatchObject({
      message: 'set_mutation_targets failed: mapping pending',
    });
  });

  it('uses the generic fallback when a target rejection has no detail', async () => {
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({ request_id: 'target-rejected', ok: false });
    const { result } = renderHook(() => useMutationTargets(RYTM_DEVICE_ID), {
      wrapper: wrapper(fake),
    });

    await act(async () => {
      result.current.toggleTarget(4);
      await Promise.resolve();
    });

    expect(useCockpitStore.getState().operatorLog.at(-1)).toMatchObject({
      message: 'set_mutation_targets failed: command rejected',
    });
  });

  it('logs a non-Error transport rejection for targets', async () => {
    const fake = new FakeCockpitClient();
    fake.nextRejection = 'transport closed';
    const { result } = renderHook(() => useMutationTargets(RYTM_DEVICE_ID), {
      wrapper: wrapper(fake),
    });

    await act(async () => {
      result.current.toggleTarget(4);
      await Promise.resolve();
    });

    expect(useCockpitStore.getState().operatorLog.at(-1)).toMatchObject({
      message: 'set_mutation_targets failed: transport closed',
    });
  });

  it('does not let an older rejection overwrite a newer target selection', async () => {
    const fake = new FakeCockpitClient();
    let rejectFirst!: (reason?: unknown) => void;
    fake.responseQueue.push(
      new Promise<never>((_resolve, reject) => {
        rejectFirst = reject;
      }),
    );
    const { result } = renderHook(() => useMutationTargets(RYTM_DEVICE_ID), {
      wrapper: wrapper(fake),
    });

    act(() => result.current.toggleTarget(2));
    await act(async () => {
      result.current.toggleTarget(4);
      await Promise.resolve();
    });
    await act(async () => {
      rejectFirst(new Error('late rejection'));
      await Promise.resolve();
    });

    expect(useCockpitStore.getState().rytmPadTargets).toEqual([2, 4]);
  });

  it('does not roll back over a newer same-generation whole-state target event', async () => {
    const fake = new FakeCockpitClient();
    let rejectRequest!: (reason?: unknown) => void;
    fake.responseQueue.push(
      new Promise<never>((_resolve, reject) => {
        rejectRequest = reject;
      }),
    );
    const { result } = renderHook(() => useMutationTargets(RYTM_DEVICE_ID), {
      wrapper: wrapper(fake),
    });

    act(() => result.current.toggleTarget(2));
    act(() => useCockpitStore.getState().setMutationTargets([3], []));
    await act(async () => {
      rejectRequest(new Error('late rejection after event'));
      await Promise.resolve();
    });

    expect(useCockpitStore.getState().rytmPadTargets).toEqual([3]);
  });

  it('does not roll back over a newer differently-sized target event', async () => {
    const fake = new FakeCockpitClient();
    let rejectRequest!: (reason?: unknown) => void;
    fake.responseQueue.push(
      new Promise<never>((_resolve, reject) => {
        rejectRequest = reject;
      }),
    );
    const { result } = renderHook(() => useMutationTargets(RYTM_DEVICE_ID), {
      wrapper: wrapper(fake),
    });

    act(() => result.current.toggleTarget(2));
    act(() => useCockpitStore.getState().setMutationTargets([3, 4], []));
    await act(async () => {
      rejectRequest(new Error('late rejection after larger event'));
      await Promise.resolve();
    });

    expect(useCockpitStore.getState().rytmPadTargets).toEqual([3, 4]);
  });
});
