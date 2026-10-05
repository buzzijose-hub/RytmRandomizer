import { afterEach, describe, expect, it, vi } from 'vitest';

const restartFixture = vi.hoisted(() => ({
  connectionStatus: 'connected',
  invoke: vi.fn(),
  snapshot: {
    state: { state: 'staged', version: '1.35.1', hardware_revalidation: false },
    journal: [{ event: 'download_ok' }],
  },
}));

vi.mock('@tauri-apps/api/core', () => ({ invoke: restartFixture.invoke }));
vi.mock('../src/state', () => ({
  useCockpitStore: { getState: () => ({
    connectionStatus: restartFixture.connectionStatus,
    sessionStatus: { armed: false },
  }) },
}));
vi.mock('../src/updateProtocol', () => ({
  parseUpdateSnapshot: (value: unknown) => value,
  requestUpdateCheck: vi.fn().mockResolvedValue(true),
  confirmUpdateChoiceOnShell: vi.fn(),
  subscribeUpdateState: (event: () => void, hydrate: (value: unknown) => void) => {
    hydrate(restartFixture.snapshot);
    event();
    return () => {};
  },
}));

import { run, staleHandshakeOutcome, until } from '../e2e/fixtures/native_update_driver';

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

  it.each(['rejected', 'accepted'] as const)('polls the socket despite stale connected state and detects %s', async (verdict) => {
    vi.useFakeTimers();
    document.body.innerHTML = '<div data-testid="cockpit-root"></div><div data-testid="update-chip">1.35.1</div>';
    window.__RYTM_RAND_WS_TOKEN__ = 'old-token';
    window.__RYTM_RAND_ARM_SECRET__ = 'old-secret';
    window.localStorage.setItem('rytm-rand-ws-port', '4317');
    restartFixture.connectionStatus = 'connected';
    restartFixture.invoke.mockImplementation(async (command: string, args?: { action?: string }) => {
      if (command === 'update_snapshot') return restartFixture.snapshot;
      if (args?.action === 'restart_backend') {
        // The old socket's close event has not reached the store yet.
        window.__RYTM_RAND_WS_TOKEN__ = 'new-token';
        window.__RYTM_RAND_ARM_SECRET__ = 'new-secret';
      }
      return { terminal: [] };
    });
    const probes: string[] = [];
    class ProbeSocket {
      onopen: (() => void) | null = null;
      onmessage: ((event: { data: string }) => void) | null = null;
      onclose: ((event: { code: number }) => void) | null = null;
      constructor() {
        probes.push(restartFixture.connectionStatus);
        queueMicrotask(() => {
          if (probes.length === 1) this.onclose?.({ code: 1006 });
          else this.onopen?.();
        });
      }
      send(message: string) {
        expect(JSON.parse(message)).toEqual({ type: 'hello', token: 'old-token' });
        queueMicrotask(() => this.onmessage?.({ data: verdict === 'rejected'
          ? '{"code":"auth_failed"}' : '{"type":"session_status"}' }));
      }
      close() {}
    }
    vi.stubGlobal('WebSocket', ProbeSocket);
    try {
      const pending = run('backend_restart', 'http://fixture.invalid');
      await vi.advanceTimersByTimeAsync(0);
      expect(window.__RYTM_RAND_WS_TOKEN__).toBe('new-token');
      expect(probes).toEqual(['connected']);

      await vi.advanceTimersByTimeAsync(75);
      await pending;
      expect(probes).toEqual(['connected', 'connected']);
      expect(restartFixture.invoke).toHaveBeenCalledWith('report', {
        passed: verdict === 'rejected', detail: expect.stringContaining(verdict === 'rejected'
          ? 'native/DOM assertions' : 'got accepted'),
      });
      expect(vi.getTimerCount()).toBe(0);
    } finally {
      vi.unstubAllGlobals();
      document.body.innerHTML = '';
      window.localStorage.clear();
    }
  });
});

describe('socket-level stale credential verdict', () => {
  class ProbeSocket {
    static script: (socket: ProbeSocket) => void = () => undefined;
    onopen: (() => void) | null = null;
    onmessage: ((event: { data: string }) => void) | null = null;
    onclose: ((event: { code: number }) => void) | null = null;
    sent: string[] = [];
    constructor(public url: string, public protocol: string) {
      queueMicrotask(() => ProbeSocket.script(this));
    }
    send(data: string): void { this.sent.push(data); }
    close(): void {}
  }
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.useRealTimers();
    window.localStorage.clear();
  });
  const probe = (script: (socket: ProbeSocket) => void): Promise<string> => {
    ProbeSocket.script = script;
    vi.stubGlobal('WebSocket', ProbeSocket);
    return staleHandshakeOutcome('old-token', '4317');
  };
  it('distinguishes unreachable from rejection', async () => {
    await expect(probe((socket) => socket.onclose?.({ code: 1006 }))).resolves.toBe('unreachable');
    await expect(probe((socket) => socket.onclose?.({ code: 1008 }))).resolves.toBe('rejected');
  });
  it('sends the stale credential and settles only once', async () => {
    let sent: string[] = [];
    await expect(probe((socket) => {
      socket.onopen?.();
      sent = socket.sent;
      socket.onmessage?.({ data: '{"code":"auth_failed"}' });
      socket.onclose?.({ code: 1006 });
    })).resolves.toBe('rejected');
    expect(JSON.parse(sent[0] ?? '{}')).toEqual({ type: 'hello', token: 'old-token' });
  });
  it('does not treat an unrelated error or session bootstrap as rejection', async () => {
    await expect(probe((socket) => socket.onmessage?.({ data: '{"code":"auth_required"}' })))
      .resolves.toBe('no_verdict');
    await expect(probe((socket) => socket.onmessage?.({ data: '{"type":"session_status"}' })))
      .resolves.toBe('accepted');
    await expect(probe((socket) => { socket.onopen?.(); socket.onclose?.({ code: 1000 }); }))
      .resolves.toBe('no_verdict');
  });
  it('bounds silence and resolves the default port from the page', async () => {
    vi.useFakeTimers();
    vi.stubGlobal('WebSocket', ProbeSocket);
    window.localStorage.setItem('rytm-rand-ws-port', '4999');
    let url = '';
    ProbeSocket.script = (socket) => { url = socket.url; socket.onopen?.(); };
    const pending = staleHandshakeOutcome('old-token');
    await vi.advanceTimersByTimeAsync(5000);
    await expect(pending).resolves.toBe('no_verdict');
    expect(url).toBe('ws://127.0.0.1:4999/ws');
    expect(vi.getTimerCount()).toBe(0);
  });
});
