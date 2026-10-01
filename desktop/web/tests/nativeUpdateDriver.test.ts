import { afterEach, describe, expect, it, vi } from 'vitest';

import {
  describePage,
  recordPageErrors,
  redact,
  staleHandshakeOutcome,
  until,
} from '../e2e/fixtures/native_update_driver';

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

describe('native acceptance timeout evidence (#251)', () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    document.body.innerHTML = '';
  });

  it('redacts absolute paths before they reach CI logs', () => {
    expect(redact('failed at C:\\Users\\runner\\app\\main.tsx:4')).toBe('failed at <path>');
    expect(redact('bad import /Users/eddie/RytmRandomizer/src/x.ts')).toBe('bad import <path>');
    expect(redact('y'.repeat(400))).toHaveLength(160);
  });

  it('redacts whole paths whose folder names contain spaces', () => {
    expect(redact('failed at C:\\Users\\First Last\\private\\take.syx')).toBe('failed at <path>');
    expect(redact('failed at C:/Users/First Last/private/take.syx')).toBe('failed at <path>');
    expect(redact('bad import /Users/First Last/Rytm Randomizer/x.ts')).toBe('bad import <path>');
    expect(redact('{"file":"/home/first last/x.syx","ok":false}')).toBe('{"file":"<path>","ok":false}');
    expect(redact('line one /tmp/a b\nline two')).toBe('line one <path>\nline two');
  });

  it('says React never mounted when #root is empty', () => {
    document.body.innerHTML = '<div id="root"></div>';
    const state = JSON.parse(describePage());
    expect(state.rootChildren).toBe(0);
    expect(state.renderError).toBeNull();
  });

  it('reports a missing #root and a render error from the app boundary', () => {
    document.body.innerHTML =
      '<main data-testid="app-render-error">Something went wrong at /Users/eddie/x.ts</main>';
    const state = JSON.parse(describePage());
    expect(state.rootChildren).toBe(-1);
    expect(state.renderError).toBe('Something went wrong at <path>');
  });

  it('lists failed module requests by status and path only', () => {
    document.body.innerHTML = '<div id="root"></div>';
    vi.spyOn(performance, 'getEntriesByType').mockReturnValue([
      { name: 'http://127.0.0.1:5173/src/App.tsx?t=1', responseStatus: 504 },
      { name: 'http://127.0.0.1:5173/src/ok.ts', responseStatus: 200 },
      { name: 'http://127.0.0.1:5173/src/legacy.ts' },
    ] as unknown as PerformanceEntry[]);
    expect(JSON.parse(describePage()).failedResources).toEqual(['504 /src/App.tsx']);
  });

  it('tolerates a runtime without the resource timing API', () => {
    document.body.innerHTML = '<div id="root"><p></p></div>';
    const original = performance.getEntriesByType;
    // @ts-expect-error -- simulating an environment that lacks the API
    performance.getEntriesByType = undefined;
    try {
      const state = JSON.parse(describePage());
      expect(state.failedResources).toEqual([]);
      expect(state.rootChildren).toBe(1);
    } finally {
      performance.getEntriesByType = original;
    }
  });

  it('records uncaught errors and rejections, bounded', () => {
    const target = new EventTarget() as unknown as Window;
    recordPageErrors(target);
    target.dispatchEvent(Object.assign(new Event('error'), { message: 'module failed /Users/e/a.ts' }));
    target.dispatchEvent(Object.assign(new Event('error'), { message: '' }));
    target.dispatchEvent(Object.assign(new Event('unhandledrejection'), { reason: new Error('import rejected') }));
    target.dispatchEvent(Object.assign(new Event('unhandledrejection'), { reason: 'ignored: over the cap' }));
    expect(JSON.parse(describePage()).pageErrors).toEqual([
      'module failed <path>',
      'error event',
      'import rejected',
    ]);
  });

  it('puts the page state into the timeout message itself', async () => {
    vi.useFakeTimers();
    document.body.innerHTML = '<div id="root"></div>';
    const pending = until('React cockpit mounted', () => false);
    const failure = expect(pending).rejects.toThrow(/Timed out: React cockpit mounted \{.*"rootChildren":0/);
    await vi.advanceTimersByTimeAsync(25_100);
    await failure;
  });
});

describe('stale-token probe after a backend restart (#251)', () => {
  // Plays one server behaviour per test. `script` runs after construction so
  // the probe has attached its handlers, exactly as with a real socket.
  class FakeSocket {
    static script: (ws: FakeSocket) => void = () => undefined;
    onopen: (() => void) | null = null;
    onmessage: ((m: { data: string }) => void) | null = null;
    onclose: ((e: { code: number }) => void) | null = null;
    sent: string[] = [];
    closed = false;
    constructor(public url: string, public protocol: string) {
      queueMicrotask(() => FakeSocket.script(this));
    }
    send(data: string): void { this.sent.push(data); }
    close(): void { this.closed = true; }
  }

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  const probe = (script: (ws: FakeSocket) => void, timeoutMs = 5000): Promise<string> => {
    FakeSocket.script = script;
    vi.stubGlobal('WebSocket', FakeSocket);
    return staleHandshakeOutcome('old-token', '4317', timeoutMs);
  };

  it('reports unreachable, not accepted, when the new backend is not listening yet', async () => {
    // The CI failure: credentials rotate before uvicorn binds, the connection
    // is refused (1006), and the old boolean helper called that "not rejected".
    await expect(probe((ws) => ws.onclose?.({ code: 1006 }))).resolves.toBe('unreachable');
  });

  it('reports rejected on auth_failed, after sending the stale token', async () => {
    let sent: string[] = [];
    const outcome = await probe((ws) => {
      ws.onopen?.();
      sent = ws.sent;
      ws.onmessage?.({ data: JSON.stringify({ code: 'auth_failed' }) });
    });
    expect(outcome).toBe('rejected');
    expect(JSON.parse(sent[0] ?? '{}')).toEqual({ type: 'hello', token: 'old-token' });
  });

  it('reports rejected on a 1008 policy close', async () => {
    await expect(probe((ws) => { ws.onopen?.(); ws.onclose?.({ code: 1008 }); })).resolves.toBe('rejected');
  });

  it('reports accepted when the backend starts a session for the stale token', async () => {
    const outcome = probe((ws) => {
      ws.onopen?.();
      ws.onmessage?.({ data: JSON.stringify({ type: 'session_status' }) });
    });
    await expect(outcome).resolves.toBe('accepted');
  });

  it('gives no verdict for an unrelated code, an open-then-close, or silence', async () => {
    await expect(probe((ws) => { ws.onopen?.(); ws.onmessage?.({ data: JSON.stringify({ code: 'auth_required' }) }); }))
      .resolves.toBe('no_verdict');
    await expect(probe((ws) => { ws.onopen?.(); ws.onclose?.({ code: 1000 }); })).resolves.toBe('no_verdict');

    vi.useFakeTimers();
    const silent = probe((ws) => ws.onopen?.(), 5000);
    await vi.advanceTimersByTimeAsync(5000);
    await expect(silent).resolves.toBe('no_verdict');
  });

  it('settles once, ignoring a close that follows its own verdict', async () => {
    const outcome = await probe((ws) => {
      ws.onopen?.();
      ws.onmessage?.({ data: JSON.stringify({ code: 'auth_failed' }) });
      ws.onclose?.({ code: 1006 });
    });
    expect(outcome).toBe('rejected');
  });

  it('defaults the port from the page and the timeout to five seconds', async () => {
    window.localStorage.setItem('rytm-rand-ws-port', '4999');
    let url = '';
    FakeSocket.script = (ws) => { url = ws.url; ws.onclose?.({ code: 1006 }); };
    vi.stubGlobal('WebSocket', FakeSocket);
    await expect(staleHandshakeOutcome('t')).resolves.toBe('unreachable');
    expect(url).toBe('ws://127.0.0.1:4999/ws');
  });
});
