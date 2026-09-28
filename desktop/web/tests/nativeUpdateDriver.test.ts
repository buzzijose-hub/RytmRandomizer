import { afterEach, describe, expect, it, vi } from 'vitest';

import { until } from '../e2e/fixtures/native_update_driver';

describe('native acceptance polling deadline', () => {
  afterEach(() => vi.useRealTimers());

  it('rejects a stalled IPC promise at the existing total deadline', async () => {
    vi.useFakeTimers();
    const pending = until('stalled IPC', () => new Promise<boolean>(() => {}));
    const failure = expect(pending).rejects.toThrow('Timed out: stalled IPC');

    await vi.advanceTimersByTimeAsync(25_000);
    await failure;
    expect(vi.getTimerCount()).toBe(0);
  });

  it('does not restart the deadline after an incomplete observation', async () => {
    vi.useFakeTimers();
    const predicate = vi.fn<() => boolean | Promise<boolean>>()
      .mockResolvedValueOnce(false)
      .mockImplementation(() => new Promise<boolean>(() => {}));
    const pending = until('decision evidence', predicate);
    const failure = expect(pending).rejects.toThrow('Timed out: decision evidence');

    await vi.advanceTimersByTimeAsync(25_000);
    await failure;
    expect(predicate).toHaveBeenCalledTimes(2);
    expect(vi.getTimerCount()).toBe(0);
  });

  it('retries incomplete observations and clears the deadline after success', async () => {
    vi.useFakeTimers();
    const predicate = vi.fn<() => boolean | Promise<boolean>>()
      .mockResolvedValueOnce(false)
      .mockResolvedValueOnce(true);
    const pending = until('decision evidence', predicate);

    await vi.advanceTimersByTimeAsync(75);
    await pending;
    expect(predicate).toHaveBeenCalledTimes(2);
    expect(vi.getTimerCount()).toBe(0);
  });

  it('preserves predicate failures and clears the deadline', async () => {
    vi.useFakeTimers();
    const failure = new Error('native snapshot rejected');

    await expect(until('snapshot', () => Promise.reject(failure))).rejects.toBe(failure);
    expect(vi.getTimerCount()).toBe(0);
  });
});
