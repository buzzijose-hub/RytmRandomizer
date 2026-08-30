/**
 * Tests for usePadLocks — local lock state + set_pad_lock emission + rollback.
 */

import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { act, renderHook } from '@testing-library/react';

import { CockpitClientProvider } from '../../src/cockpit/context';
import { usePadLocks } from '../../src/cockpit/usePadLocks';
import { useCockpitStore } from '../../src/state';

import { candidate, FakeCockpitClient, enqueueRejection, sendPlan } from './_fixtures';

function makeWrapper(client: FakeCockpitClient) {
  return function Wrapper({ children }: { children: React.ReactNode }): JSX.Element {
    return <CockpitClientProvider client={client.asClient()}>{children}</CockpitClientProvider>;
  };
}

describe('usePadLocks', () => {
  beforeEach(() => {
    useCockpitStore.getState().reset();
  });

  afterEach(() => {
    useCockpitStore.getState().reset();
  });

  it('starts with no pads locked', () => {
    const fake = new FakeCockpitClient();
    const { result } = renderHook(() => usePadLocks(), { wrapper: makeWrapper(fake) });
    expect(result.current.locked.size).toBe(0);
    expect(result.current.isLocked(1)).toBe(false);
  });

  it('toggling an unlocked pad locks it and emits set_pad_lock', async () => {
    const fake = new FakeCockpitClient();
    useCockpitStore.getState().setPreviewCandidate(candidate);
    useCockpitStore.getState().setSendPlan(sendPlan);
    const { result } = renderHook(() => usePadLocks(), { wrapper: makeWrapper(fake) });
    await act(async () => {
      result.current.toggleLock(2);
      await Promise.resolve();
    });
    expect(result.current.isLocked(2)).toBe(true);
    expect(fake.sent).toEqual([{ type: 'set_pad_lock', pad_id: 2, locked: true }]);
    expect(useCockpitStore.getState().previewCandidate).toBeNull();
    expect(useCockpitStore.getState().sendPlan).toBeNull();
  });

  it('toggling a locked pad unlocks it and emits set_pad_lock locked=false', async () => {
    const fake = new FakeCockpitClient();
    const { result } = renderHook(() => usePadLocks(), { wrapper: makeWrapper(fake) });
    await act(async () => {
      result.current.toggleLock(3);
      await Promise.resolve();
    });
    await act(async () => {
      result.current.toggleLock(3);
      await Promise.resolve();
    });
    expect(result.current.isLocked(3)).toBe(false);
    expect(fake.sent).toEqual([
      { type: 'set_pad_lock', pad_id: 3, locked: true },
      { type: 'set_pad_lock', pad_id: 3, locked: false },
    ]);
  });

  it('rolls back to unlocked when the ack is ok=false on a lock attempt', async () => {
    const fake = new FakeCockpitClient();
    enqueueRejection(fake);
    const { result } = renderHook(() => usePadLocks(), { wrapper: makeWrapper(fake) });
    await act(async () => {
      result.current.toggleLock(1);
      // Let the ack microtask flush.
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(result.current.isLocked(1)).toBe(false);
  });

  it('rolls back to locked when the ack rejects on an unlock attempt', async () => {
    const fake = new FakeCockpitClient();
    // First toggle: success (lock).
    const { result } = renderHook(() => usePadLocks(), { wrapper: makeWrapper(fake) });
    await act(async () => {
      result.current.toggleLock(4);
      await Promise.resolve();
    });
    expect(result.current.isLocked(4)).toBe(true);
    // Second toggle: ack rejects.
    enqueueRejection(fake);
    await act(async () => {
      result.current.toggleLock(4);
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(result.current.isLocked(4)).toBe(true);
  });

  it('logs the generic command-rejected fallback when a lock ack has no error', async () => {
    const fake = new FakeCockpitClient();
    fake.ackQueue.push({ request_id: 'lock-rejected', ok: false });
    const { result } = renderHook(() => usePadLocks(), { wrapper: makeWrapper(fake) });
    await act(async () => {
      result.current.toggleLock(1);
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(useCockpitStore.getState().operatorLog.at(-1)).toMatchObject({
      level: 'error',
      message: 'set_pad_lock failed: command rejected',
    });
  });

  it('rolls back the optimistic flip when send() throws (network error)', async () => {
    const fake = new FakeCockpitClient();
    fake.nextRejection = new Error('socket not open');
    const { result } = renderHook(() => usePadLocks(), { wrapper: makeWrapper(fake) });
    await act(async () => {
      result.current.toggleLock(1);
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(result.current.isLocked(1)).toBe(false);
  });

  it('logs non-Error send() rejections for lock toggles', async () => {
    const fake = new FakeCockpitClient();
    fake.nextRejection = 'transport closed';
    const { result } = renderHook(() => usePadLocks(), { wrapper: makeWrapper(fake) });
    await act(async () => {
      result.current.toggleLock(1);
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(result.current.isLocked(1)).toBe(false);
    expect(useCockpitStore.getState().operatorLog.at(-1)).toMatchObject({
      level: 'error',
      message: 'set_pad_lock failed: transport closed',
    });
  });

  it('rolls back to locked on send() rejection during an unlock attempt', async () => {
    const fake = new FakeCockpitClient();
    const { result } = renderHook(() => usePadLocks(), { wrapper: makeWrapper(fake) });
    await act(async () => {
      result.current.toggleLock(2);
      await Promise.resolve();
    });
    expect(result.current.isLocked(2)).toBe(true);
    fake.nextRejection = new Error('socket closed');
    await act(async () => {
      result.current.toggleLock(2);
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(result.current.isLocked(2)).toBe(true);
  });

  it('does not let an older rejection overwrite a newer lock toggle', async () => {
    const fake = new FakeCockpitClient();
    let rejectFirst!: (reason?: unknown) => void;
    fake.responseQueue.push(
      new Promise<never>((_resolve, reject) => {
        rejectFirst = reject;
      }),
    );
    const { result } = renderHook(() => usePadLocks(), { wrapper: makeWrapper(fake) });

    act(() => result.current.toggleLock(1));
    await act(async () => {
      result.current.toggleLock(1);
      await Promise.resolve();
    });
    await act(async () => {
      rejectFirst(new Error('late rejection'));
      await Promise.resolve();
    });

    expect(result.current.isLocked(1)).toBe(false);
  });

  it('rolls back a rejected A4 track lock through the A4 state branch', async () => {
    const fake = new FakeCockpitClient();
    enqueueRejection(fake);
    const { result } = renderHook(() => usePadLocks('analog_four_mk2'), {
      wrapper: makeWrapper(fake),
    });

    await act(async () => {
      result.current.toggleLock(3);
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(useCockpitStore.getState().a4TrackLocks).toEqual([]);
  });

  it('does not roll back over a newer authoritative lock-state replacement', async () => {
    const fake = new FakeCockpitClient();
    let rejectRequest!: (reason?: unknown) => void;
    fake.responseQueue.push(
      new Promise<never>((_resolve, reject) => {
        rejectRequest = reject;
      }),
    );
    const { result } = renderHook(() => usePadLocks(), { wrapper: makeWrapper(fake) });

    act(() => result.current.toggleLock(1));
    act(() => useCockpitStore.getState().setRytmPadLocks([]));
    await act(async () => {
      rejectRequest(new Error('late rejection after authoritative state'));
      await Promise.resolve();
    });

    expect(useCockpitStore.getState().rytmPadLocks).toEqual([]);
  });

  it('sorts multi-lock optimistic state and rollback state deterministically', async () => {
    useCockpitStore.getState().setRytmPadLocks([2]);
    const fake = new FakeCockpitClient();
    const { result } = renderHook(() => usePadLocks(), { wrapper: makeWrapper(fake) });

    await act(async () => {
      result.current.toggleLock(1);
      await Promise.resolve();
    });
    expect(useCockpitStore.getState().rytmPadLocks).toEqual([1, 2]);

    enqueueRejection(fake);
    await act(async () => {
      result.current.toggleLock(1);
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(useCockpitStore.getState().rytmPadLocks).toEqual([1, 2]);
  });
});
