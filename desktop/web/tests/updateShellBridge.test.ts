import { waitFor } from '@testing-library/react';
import { clearMocks } from '@tauri-apps/api/mocks';
import { afterEach, describe, expect, it, vi } from 'vitest';

import {
  UPDATE_STATE_EVENT_NAME,
  confirmUpdateChoiceOnShell,
  parseUpdateSnapshot,
  requestUpdateCheck,
  subscribeUpdateState,
  type UpdateSnapshot,
} from '../src/updateProtocol';
import { emitTauriEvent, installTauriEventBridge } from './tauriEvent';

function snapshot(version = '1.35.1'): UpdateSnapshot {
  return {
    state: { state: 'staged', version, notes: '', hardware_revalidation: true, error_code: null },
    journal: [{ ts: '2026-09-08T12:00:00Z', event: 'download_ok', version, detail: 'verified' }],
    channel: 'beta',
    frozen: false,
  };
}

const subscriptions: Array<() => void> = [];

afterEach(() => {
  subscriptions.splice(0).forEach((stop) => stop());
  clearMocks();
});

describe('read-only snapshot contract', () => {
  it('retains journal details, hardware revalidation and launch settings', () => {
    expect(parseUpdateSnapshot(snapshot())).toEqual(snapshot());
  });

  it.each([
    null,
    'snapshot',
    { ...snapshot(), channel: 'canary' },
    { ...snapshot(), frozen: 'false' },
    { ...snapshot(), journal: null },
    { ...snapshot(), state: null },
    { ...snapshot(), journal: [{ event: 'invented' }] },
  ])('refuses an incomplete or unrecognised snapshot: %j', (payload) => {
    expect(parseUpdateSnapshot(payload)).toBeNull();
  });
});

describe('Tauri event and snapshot composition', () => {
  it('replays state emitted before mount without starting an update check', async () => {
    const command = vi.fn(() => snapshot());
    installTauriEventBridge(command);
    const receive = vi.fn();
    subscriptions.push(subscribeUpdateState(vi.fn(), receive));
    await waitFor(() => expect(receive).toHaveBeenCalledWith(snapshot()));
    expect(command.mock.calls).toEqual([['update_snapshot', {}]]);
  });

  it('installs the listener before querying and refuses an older response after a new event', async () => {
    let requests = 0;
    let finishOld: (value: UpdateSnapshot) => void = () => { throw new Error('query not started'); };
    const oldResponse = new Promise<UpdateSnapshot>((resolve) => { finishOld = resolve; });
    const fresh = snapshot('1.36.0');
    installTauriEventBridge(async () => {
      requests += 1;
      if (requests === 1) {
        // This event is emitted during the first query. It must be heard.
        await emitTauriEvent(UPDATE_STATE_EVENT_NAME, fresh.state);
        return oldResponse;
      }
      return fresh;
    });
    const state = vi.fn();
    const receive = vi.fn();
    subscriptions.push(subscribeUpdateState(state, receive));
    await waitFor(() => expect(receive).toHaveBeenCalledWith(fresh));
    expect(state).toHaveBeenCalledWith(fresh.state);
    finishOld(snapshot());
    await oldResponse;
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(receive.mock.calls).toEqual([[fresh]]);
  });

  it('ignores malformed events and does not refresh them', async () => {
    const command = vi.fn(() => snapshot());
    installTauriEventBridge(command);
    const state = vi.fn();
    const receive = vi.fn();
    subscriptions.push(subscribeUpdateState(state, receive));
    await waitFor(() => expect(receive).toHaveBeenCalledOnce());
    await emitTauriEvent(UPDATE_STATE_EVENT_NAME, { state: 'unknown' });
    expect(state).not.toHaveBeenCalled();
    expect(command).toHaveBeenCalledOnce();
  });

  it('does not deliver a pending snapshot after unmount', async () => {
    let finish: (value: UpdateSnapshot) => void = () => { throw new Error('query not started'); };
    const response = new Promise<UpdateSnapshot>((resolve) => { finish = resolve; });
    const command = vi.fn(() => response);
    installTauriEventBridge(command);
    const receive = vi.fn();
    const stop = subscribeUpdateState(vi.fn(), receive);
    subscriptions.push(stop);
    await waitFor(() => expect(command).toHaveBeenCalledOnce());
    stop();
    finish(snapshot());
    await response;
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(receive).not.toHaveBeenCalled();
  });

  it('can unmount before the asynchronous listener is registered', async () => {
    const command = vi.fn();
    installTauriEventBridge(command);
    const receive = vi.fn();
    const stop = subscribeUpdateState(receive, receive);
    stop();
    await new Promise((resolve) => setTimeout(resolve, 0));
    await emitTauriEvent(UPDATE_STATE_EVENT_NAME, snapshot().state);
    expect(receive).not.toHaveBeenCalled();
    expect(command).not.toHaveBeenCalled();
  });

  it('keeps listening when snapshot hydration fails', async () => {
    const command = vi.fn(() => { throw new Error('backend unavailable'); });
    installTauriEventBridge(command);
    const state = vi.fn();
    const receive = vi.fn();
    subscriptions.push(subscribeUpdateState(state, receive));
    await waitFor(() => expect(command).toHaveBeenCalledOnce());
    await emitTauriEvent(UPDATE_STATE_EVENT_NAME, snapshot().state);
    expect(state).toHaveBeenCalledWith(snapshot().state);
    expect(receive).not.toHaveBeenCalled();
  });

  it('supports a state-only subscriber without querying the shell', async () => {
    const command = vi.fn();
    installTauriEventBridge(command);
    const state = vi.fn();
    subscriptions.push(subscribeUpdateState(state));
    await new Promise((resolve) => setTimeout(resolve, 0));
    await emitTauriEvent(UPDATE_STATE_EVENT_NAME, snapshot().state);
    expect(state).toHaveBeenCalledWith(snapshot().state);
    expect(command).not.toHaveBeenCalled();
  });
});

describe('shell action acknowledgements', () => {
  it.each([true, false, undefined, 'accepted'])('requires an explicit boolean true: %j', async (response) => {
    const command = vi.fn(() => response);
    installTauriEventBridge(command);
    expect(await requestUpdateCheck()).toBe(response === true);
    expect(await confirmUpdateChoiceOnShell('1.35.1', 'install_on_quit')).toBe(response === true);
    expect(command.mock.calls).toEqual([
      ['update_check_now', {}],
      ['update_confirm_choice', { version: '1.35.1', choice: 'install_on_quit' }],
    ]);
  });
});
