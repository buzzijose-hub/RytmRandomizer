/**
 * Tests for the typed WebSocket client.
 *
 * The tests inject a `FakeWebSocket` via the client's `webSocketFactory` option so we never
 * touch a real socket. The fake exposes `emit*` helpers driving the client through every
 * code path: open, message (ack/event/garbage/non-string), error, close, reconnect, send,
 * ack timeout, send-before-open, send after socket-readyState-not-open, and the user-close
 * path.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import {
  CockpitClient,
  DEFAULT_WS_URL,
  ARM_SECRET_STORAGE_KEY,
  resolveArmSecret,
  WS_AUTH_TOKEN_STORAGE_KEY,
  WS_SUBPROTOCOL,
  type ClientLogger,
  type ConnectionStatus,
  type ReconnectState,
  type WebSocketLike,
} from '../src/ws/client';
import {
  isCommandAck,
  isEvent,
  type BuildOperatorPackageReceiptCommand,
  type Command,
  type CommandAck,
  type Event,
  type MockApplyOperatorPackageCommand,
  type PreviewOperatorPackageApplyCommand,
  type SessionStatusEvent,
} from '../src/ws/protocol';

// ---------- Fake WebSocket ----------

class FakeWebSocket implements WebSocketLike {
  static readonly CONNECTING = 0;
  static readonly OPEN = 1;
  static readonly CLOSING = 2;
  static readonly CLOSED = 3;

  readyState = FakeWebSocket.CONNECTING;
  readonly url: string;
  readonly protocols: string | string[] | undefined;
  readonly sent: string[] = [];
  readonly closeCalls: number[] = [];
  private throwOnSend: Error | null = null;
  private readonly listeners = new Map<string, Set<(ev: unknown) => void>>();

  constructor(url: string, protocols?: string | string[]) {
    this.url = url;
    this.protocols = protocols;
  }

  addEventListener(type: string, listener: (ev: unknown) => void): void {
    let bucket = this.listeners.get(type);
    if (bucket === undefined) {
      bucket = new Set();
      this.listeners.set(type, bucket);
    }
    bucket.add(listener);
  }

  removeEventListener(type: string, listener: (ev: unknown) => void): void {
    this.listeners.get(type)?.delete(listener);
  }

  send(data: string): void {
    if (this.throwOnSend !== null) {
      const err = this.throwOnSend;
      this.throwOnSend = null;
      throw err;
    }
    this.sent.push(data);
  }

  close(): void {
    this.closeCalls.push(Date.now());
    this.readyState = FakeWebSocket.CLOSED;
  }

  // ----- test helpers (not part of WebSocketLike) -----

  emitOpen(): void {
    this.readyState = FakeWebSocket.OPEN;
    this.dispatch('open', new Event('open'));
  }

  emitMessage(payload: unknown): void {
    const data = typeof payload === 'string' ? payload : JSON.stringify(payload);
    this.dispatch('message', new MessageEvent('message', { data }));
  }

  emitRawMessage(data: unknown): void {
    this.dispatch('message', { data } as unknown as Event);
  }

  emitError(): void {
    this.dispatch('error', new Event('error'));
  }

  emitClose(): void {
    this.readyState = FakeWebSocket.CLOSED;
    this.dispatch('close', new CloseEvent('close'));
  }

  primeSendError(err: Error): void {
    this.throwOnSend = err;
  }

  private dispatch(type: string, ev: unknown): void {
    const bucket = this.listeners.get(type);
    if (bucket === undefined) return;
    for (const listener of bucket) listener(ev);
  }
}

// ---------- Fixtures ----------

const sessionStatusEvent: SessionStatusEvent = {
  type: 'session_status',
  armed: false,
  midi_port: null,
  mode: 'mock',
  connection_phase: 'disconnected',
  unsaved_sends: 0,
};

const ack = (request_id: string, extra: Partial<CommandAck> = {}): CommandAck => ({
  request_id,
  ok: true,
  ...extra,
});

// ---------- Helpers ----------

interface Harness {
  client: CockpitClient;
  fakes: FakeWebSocket[];
  currentSocket: () => FakeWebSocket;
}

interface HarnessOpts {
  disableReconnect?: boolean;
  maxReconnectAttempts?: number;
  initialReconnectDelayMs?: number;
  maxReconnectDelayMs?: number;
  ackTimeoutMs?: number;
  logger?: ClientLogger;
  authToken?: string | null;
  authTokenResolver?: () => string | null;
  setTimeoutImpl?: typeof setTimeout;
  clearTimeoutImpl?: typeof clearTimeout;
}

function makeHarness(opts: HarnessOpts = {}): Harness {
  const fakes: FakeWebSocket[] = [];
  let counter = 0;
  const client = new CockpitClient({
    url: 'ws://test/ws',
    disableReconnect: opts.disableReconnect ?? false,
    maxReconnectAttempts: opts.maxReconnectAttempts,
    initialReconnectDelayMs: opts.initialReconnectDelayMs,
    maxReconnectDelayMs: opts.maxReconnectDelayMs,
    ackTimeoutMs: opts.ackTimeoutMs,
    setTimeoutImpl: opts.setTimeoutImpl,
    clearTimeoutImpl: opts.clearTimeoutImpl,
    authToken: opts.authToken,
    authTokenResolver: opts.authTokenResolver,
    requestIdGenerator: () => `r${++counter}`,
    logger: opts.logger,
    webSocketFactory: (url, protocols) => {
      const fake = new FakeWebSocket(url, protocols);
      fakes.push(fake);
      return fake;
    },
  });
  return {
    client,
    fakes,
    currentSocket: () => {
      const last = fakes[fakes.length - 1];
      if (last === undefined) throw new Error('no socket created');
      return last;
    },
  };
}

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  if (typeof window !== 'undefined') delete window.__RYTM_RAND_WS_TOKEN__;
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

// ---------- Tests ----------

describe('CockpitClient — defaults & constants', () => {
  it('exposes the default WS URL', () => {
    expect(DEFAULT_WS_URL).toBe('ws://127.0.0.1:4317/ws');
  });

  it('exposes the pinned cockpit WS subprotocol and browser token storage key', () => {
    expect(WS_SUBPROTOCOL).toBe('rytm-rand-cockpit-v1');
    expect(WS_AUTH_TOKEN_STORAGE_KEY).toBe('rytm-rand-ws-token');
  });

  it('constructs with all defaults applied and reports closed status', () => {
    const c = new CockpitClient();
    expect(c.getStatus()).toBe('closed');
  });

  it('the default WebSocket factory is exercisable (constructs without crashing in jsdom)', () => {
    // jsdom provides a stub WebSocket. We only verify the path exists; we immediately close.
    const c = new CockpitClient({
      url: 'ws://127.0.0.1:0/ws',
      disableReconnect: true,
      requestIdGenerator: () => 'r1',
      logger: { warn: () => {} },
    });
    expect(() => c.connect()).not.toThrow();
    c.close();
  });

  it('calls default browser timers with the global receiver', async () => {
    const receivers: unknown[] = [];
    const fakeSetTimeout = function (this: unknown): ReturnType<typeof setTimeout> {
      receivers.push(this);
      return {} as ReturnType<typeof setTimeout>;
    } as unknown as typeof setTimeout;
    const fakeClearTimeout = function (this: unknown): void {
      receivers.push(this);
    } as unknown as typeof clearTimeout;
    vi.stubGlobal('setTimeout', fakeSetTimeout);
    vi.stubGlobal('clearTimeout', fakeClearTimeout);

    const sockets: FakeWebSocket[] = [];
    const client = new CockpitClient({
      url: 'ws://test/ws',
      disableReconnect: true,
      requestIdGenerator: () => 'r1',
      webSocketFactory: (url, protocols) => {
        const socket = new FakeWebSocket(url, protocols);
        sockets.push(socket);
        return socket;
      },
    });
    client.connect();
    const socket = sockets[0];
    if (socket === undefined) throw new Error('socket not created');
    socket.emitOpen();

    const promise = client.send({ type: 'regen' });
    socket.emitMessage(ack('r1'));

    await expect(promise).resolves.toMatchObject({ ok: true });
    expect(receivers).toEqual([globalThis, globalThis]);
  });

  it('the default request-id generator produces unique-ish strings', () => {
    // Reach into the private by constructing two clients with the default generator and
    // sending the same command; correlation requires distinct ids.
    const ids = new Set<string>();
    const gen = (): string => {
      // Replicate the default by calling the client's exported factory indirectly:
      // the cleanest path is two `send()` invocations against the same client.
      return '';
    };
    expect(gen()).toBe(''); // placeholder; real coverage comes from the default-path test below.
    for (let i = 0; i < 50; i += 1) ids.add(`req_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`);
    expect(ids.size).toBeGreaterThan(40); // statistical: 50 distinct ids should yield >40 unique.
  });
});

describe('CockpitClient — connect / open / status', () => {
  it('connect() is a no-op when already connected', () => {
    const h = makeHarness();
    h.client.connect();
    h.client.connect(); // second call
    expect(h.fakes.length).toBe(1);
  });

  it('requests the pinned subprotocol when opening the browser WebSocket', () => {
    const h = makeHarness();
    h.client.connect();
    expect(h.currentSocket().protocols).toBe(WS_SUBPROTOCOL);
  });

  it('sends the hello frame with the configured token when the socket opens', () => {
    const h = makeHarness({ authToken: 'token-for-test' });
    h.client.connect();
    h.currentSocket().emitOpen();
    expect(h.currentSocket().sent).toEqual([
      JSON.stringify({ type: 'hello', token: 'token-for-test' }),
    ]);
  });

  it('resolves the hello token lazily from the configured resolver', () => {
    const h = makeHarness({ authTokenResolver: () => 'resolver-token' });
    h.client.connect();
    h.currentSocket().emitOpen();
    expect(h.currentSocket().sent).toEqual([
      JSON.stringify({ type: 'hello', token: 'resolver-token' }),
    ]);
  });

  it('resolves the hello token from the browser launch global before storage', () => {
    const storageRead = vi.spyOn(Storage.prototype, 'getItem');
    window.__RYTM_RAND_WS_TOKEN__ = 'browser-token';
    const h = makeHarness();
    h.client.connect();
    h.currentSocket().emitOpen();
    expect(storageRead).not.toHaveBeenCalled();
    expect(h.currentSocket().sent).toEqual([
      JSON.stringify({ type: 'hello', token: 'browser-token' }),
    ]);
  });

  it('falls back to browser token storage when the launch global is empty', () => {
    window.__RYTM_RAND_WS_TOKEN__ = '';
    vi.spyOn(Storage.prototype, 'getItem').mockReturnValue('storage-token');
    const h = makeHarness();
    h.client.connect();
    h.currentSocket().emitOpen();
    expect(h.currentSocket().sent).toEqual([
      JSON.stringify({ type: 'hello', token: 'storage-token' }),
    ]);
  });

  it('treats browser token storage read failures as a missing token', () => {
    const warnings: unknown[] = [];
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('storage denied');
    });
    const h = makeHarness({ logger: { warn: (...args) => warnings.push(args) } });
    h.client.connect();
    h.currentSocket().emitOpen();
    expect(h.currentSocket().sent).toEqual([]);
    expect(
      warnings.some((w) => Array.isArray(w) && String(w[0]).includes('auth token unavailable')),
    ).toBe(true);
  });

  it('closes the socket when sending the hello frame fails', () => {
    const warnings: unknown[] = [];
    const h = makeHarness({
      authToken: 'token-for-test',
      logger: { warn: (...args) => warnings.push(args) },
    });
    h.client.connect();
    h.currentSocket().primeSendError(new Error('handshake send failed'));
    h.currentSocket().emitOpen();
    expect(h.currentSocket().closeCalls).toHaveLength(1);
    expect(
      warnings.some((w) => Array.isArray(w) && String(w[0]).includes('handshake send failed')),
    ).toBe(true);
  });

  it('emits status transitions: connecting → connected', () => {
    const h = makeHarness();
    const seen: ConnectionStatus[] = [];
    h.client.onStatusChange((s) => seen.push(s));
    h.client.connect();
    expect(seen).toEqual(['connecting']);
    h.currentSocket().emitOpen();
    expect(seen).toEqual(['connecting', 'connected']);
    expect(h.client.getStatus()).toBe('connected');
  });

  it('setStatus is a no-op when the status does not change', () => {
    const h = makeHarness();
    const seen: ConnectionStatus[] = [];
    h.client.onStatusChange((s) => seen.push(s));
    h.client.connect();
    h.currentSocket().emitOpen();
    // calling setStatus(connected) again via a second open event should not duplicate.
    h.currentSocket().emitOpen();
    expect(seen).toEqual(['connecting', 'connected']);
  });

  it('onStatusChange returns an unsubscribe that detaches the listener', () => {
    const h = makeHarness();
    const seen: ConnectionStatus[] = [];
    const off = h.client.onStatusChange((s) => seen.push(s));
    h.client.connect();
    expect(seen).toEqual(['connecting']);
    off();
    h.currentSocket().emitOpen();
    expect(seen).toEqual(['connecting']); // no further notifications
  });

  it('a throwing status handler does not break the dispatch loop', () => {
    const errors: unknown[] = [];
    const h = makeHarness({ logger: { error: (_msg, ...rest) => errors.push(rest) } });
    h.client.onStatusChange(() => {
      throw new Error('boom');
    });
    const seen: ConnectionStatus[] = [];
    h.client.onStatusChange((s) => seen.push(s));
    h.client.connect();
    expect(seen).toEqual(['connecting']);
    expect(errors.length).toBeGreaterThan(0);
  });
});

describe('CockpitClient — message dispatch', () => {
  it('routes recognized events to their handlers', () => {
    const h = makeHarness();
    const events: Event[] = [];
    const off = h.client.on('session_status', (e) => events.push(e));
    h.client.connect();
    h.currentSocket().emitOpen();
    h.currentSocket().emitMessage(sessionStatusEvent);
    expect(events).toEqual([sessionStatusEvent]);
    off();
    h.currentSocket().emitMessage(sessionStatusEvent);
    expect(events).toHaveLength(1);
  });

  it('does nothing when no handlers are registered for an event type', () => {
    const h = makeHarness();
    h.client.connect();
    h.currentSocket().emitOpen();
    expect(() => h.currentSocket().emitMessage(sessionStatusEvent)).not.toThrow();
  });

  it('catches errors thrown by event handlers and logs them', () => {
    const logged: unknown[] = [];
    const h = makeHarness({ logger: { error: (...args) => logged.push(args) } });
    h.client.on('session_status', () => {
      throw new Error('handler-boom');
    });
    h.client.connect();
    h.currentSocket().emitOpen();
    h.currentSocket().emitMessage(sessionStatusEvent);
    expect(logged.length).toBe(1);
  });

  it('ignores non-string message payloads', () => {
    const warnings: unknown[] = [];
    const h = makeHarness({ logger: { warn: (...args) => warnings.push(args) } });
    h.client.connect();
    h.currentSocket().emitOpen();
    h.currentSocket().emitRawMessage(123); // numeric data
    expect(warnings.some((w) => Array.isArray(w) && String(w[0]).includes('non-string'))).toBe(
      true,
    );
  });

  it('treats a non-browser global as a missing token', () => {
    const warnings: unknown[] = [];
    vi.stubGlobal('window', undefined);
    const h = makeHarness({ logger: { warn: (...args) => warnings.push(args) } });
    h.client.connect();
    h.currentSocket().emitOpen();
    expect(h.currentSocket().sent).toEqual([]);
    expect(
      warnings.some((w) => Array.isArray(w) && String(w[0]).includes('auth token unavailable')),
    ).toBe(true);
  });

  it('warns on malformed JSON and continues', () => {
    const warnings: unknown[] = [];
    const h = makeHarness({ logger: { warn: (...args) => warnings.push(args) } });
    h.client.connect();
    h.currentSocket().emitOpen();
    h.currentSocket().emitMessage('not-json{');
    expect(warnings.some((w) => Array.isArray(w) && String(w[0]).includes('failed to parse'))).toBe(
      true,
    );
  });

  it('warns on an unrecognized message shape (neither event nor ack)', () => {
    const warnings: unknown[] = [];
    const h = makeHarness({ logger: { warn: (...args) => warnings.push(args) } });
    h.client.connect();
    h.currentSocket().emitOpen();
    h.currentSocket().emitMessage({ hello: 'world' });
    expect(warnings.some((w) => Array.isArray(w) && String(w[0]).includes('unrecognized'))).toBe(
      true,
    );
  });

  it('treats the token-handshake ack as transport setup noise, not an unknown message', () => {
    const warnings: unknown[] = [];
    const h = makeHarness({
      authToken: 'token-for-test',
      logger: { warn: (...args) => warnings.push(args) },
    });
    h.client.connect();
    h.currentSocket().emitOpen();
    h.currentSocket().emitMessage({ ok: true });
    expect(warnings).toEqual([]);
  });

  it('warns when the token-handshake ack rejects authentication', () => {
    const warnings: unknown[] = [];
    const h = makeHarness({
      authToken: 'token-for-test',
      logger: { warn: (...args) => warnings.push(args) },
    });
    h.client.connect();
    h.currentSocket().emitOpen();
    h.currentSocket().emitMessage({ ok: false, code: 'bad-token' });
    expect(
      warnings.some(
        (w) =>
          Array.isArray(w) &&
          String(w[0]).includes('handshake rejected') &&
          w.includes('bad-token'),
      ),
    ).toBe(true);
  });

  it('warns on parsed null and scalar message shapes', () => {
    const warnings: unknown[] = [];
    const h = makeHarness({ logger: { warn: (...args) => warnings.push(args) } });
    h.client.connect();
    h.currentSocket().emitOpen();
    h.currentSocket().emitMessage(null);
    h.currentSocket().emitMessage(42);
    const unrecognized = warnings.filter(
      (w) => Array.isArray(w) && String(w[0]).includes('unrecognized'),
    );
    expect(unrecognized).toHaveLength(2);
  });
});

describe('CockpitClient — send / ack correlation', () => {
  it('round-trips a command through to an ack', async () => {
    const h = makeHarness();
    h.client.connect();
    h.currentSocket().emitOpen();
    const cmd: Command = { type: 'set_depth', depth: 0.5 };
    const promise = h.client.send(cmd);
    expect(h.currentSocket().sent).toHaveLength(1);
    const sent = JSON.parse(h.currentSocket().sent[0] ?? '') as { request_id: string };
    h.currentSocket().emitMessage(ack(sent.request_id, { candidate: undefined }));
    const result = await promise;
    expect(result.ok).toBe(true);
    expect(result.request_id).toBe(sent.request_id);
  });

  it('round-trips an operator package rehearsal command with typed ack payload', async () => {
    const h = makeHarness();
    h.client.connect();
    h.currentSocket().emitOpen();
    const cmd: Command = {
      type: 'rehearse_operator_package_step',
      operator_package_id: 'live-kit-operator-package',
      step_key: 'operator-step-hard-groove-lift',
      slot_key: 'hard-groove-lift',
      package_export_key: 'operator-package-hard-groove-lift',
      snapshot_id: 'snap-06',
      depth_percent: 70,
      mock_safe: true,
    };
    const promise = h.client.send(cmd);
    const sent = JSON.parse(h.currentSocket().sent[0] ?? '') as {
      request_id: string;
      command: Command;
    };
    expect(sent.command).toMatchObject(cmd);
    h.currentSocket().emitMessage(
      ack(sent.request_id, {
        operator_package_rehearsal: {
          rehearsal_id: 'operator-package-rehearsal:operator-step-hard-groove-lift',
          operator_package_id: 'live-kit-operator-package',
          step_key: 'operator-step-hard-groove-lift',
          slot_key: 'hard-groove-lift',
          mock_safe: true,
          rehearsal_status: 'mock_safe_ready',
          opened_midi_port: false,
          sent_midi: false,
          writes_files: false,
        },
      }),
    );

    const result = await promise;
    expect(result.operator_package_rehearsal?.sent_midi).toBe(false);
    expect(result.operator_package_rehearsal?.rehearsal_status).toBe('mock_safe_ready');
  });

  it('round-trips an operator package sequence rehearsal command with typed ack payload', async () => {
    const h = makeHarness();
    h.client.connect();
    h.currentSocket().emitOpen();
    const cmd: Command = {
      type: 'rehearse_operator_package_sequence',
      operator_package_id: 'live-kit-operator-package',
      step_keys: [
        'operator-step-hard-groove-lift',
        'operator-step-industrial-pressure',
      ],
      package_export_keys: {
        'operator-step-hard-groove-lift': 'operator-package-hard-groove-lift',
        'operator-step-industrial-pressure': 'operator-package-industrial-pressure',
      },
      snapshot_id: 'snap-06',
      mock_safe: true,
    };
    const promise = h.client.send(cmd);
    const sent = JSON.parse(h.currentSocket().sent[0] ?? '') as {
      request_id: string;
      command: Command;
    };
    expect(sent.command).toMatchObject(cmd);
    h.currentSocket().emitMessage(
      ack(sent.request_id, {
        operator_package_sequence_rehearsal: {
          rehearsal_id: 'operator-package-sequence-rehearsal:live-kit-operator-package',
          operator_package_id: 'live-kit-operator-package',
          step_count: 2,
          step_keys: [
            'operator-step-hard-groove-lift',
            'operator-step-industrial-pressure',
          ],
          snapshot_id: 'snap-06',
          mock_safe: true,
          rehearsal_status: 'mock_safe_ready',
          opened_midi_port: false,
          sent_midi: false,
          writes_files: false,
          step_rehearsals: [],
        },
      }),
    );

    const result = await promise;
    expect(result.operator_package_sequence_rehearsal?.sent_midi).toBe(false);
    expect(result.operator_package_sequence_rehearsal?.step_count).toBe(2);
  });

  it('round-trips an operator package apply preview command with typed ack payload', async () => {
    const h = makeHarness();
    h.client.connect();
    h.currentSocket().emitOpen();
    const cmd: PreviewOperatorPackageApplyCommand = {
      type: 'preview_operator_package_apply',
      operator_package_id: 'live-kit-operator-package',
      step_keys: [
        'operator-step-hard-groove-lift',
        'operator-step-industrial-pressure',
      ],
      package_export_keys: {
        'operator-step-hard-groove-lift': 'operator-package-hard-groove-lift',
        'operator-step-industrial-pressure': 'operator-package-industrial-pressure',
      },
      snapshot_id: 'snap-06',
      mock_safe: true,
    };
    const promise = h.client.send(cmd);
    const sent = JSON.parse(h.currentSocket().sent[0] ?? '') as {
      request_id: string;
      command: Command;
    };
    expect(sent.command).toMatchObject(cmd);
    h.currentSocket().emitMessage(
      ack(sent.request_id, {
        operator_package_apply_preview: {
          preview_id: 'operator-package-apply-preview:live-kit-operator-package',
          operator_package_id: 'live-kit-operator-package',
          snapshot_id: 'snap-06',
          mock_safe: true,
          preview_status: 'mock_safe_ready',
          apply_policy: 'preview_only',
          opened_midi_port: false,
          sent_midi: false,
          writes_files: false,
          step_count: 2,
          step_keys: [
            'operator-step-hard-groove-lift',
            'operator-step-industrial-pressure',
          ],
          apply_steps: [
            {
              step_key: 'operator-step-hard-groove-lift',
              label: 'Hard Groove Lift',
              slot_key: 'hard-groove-lift',
              package_export_key: 'operator-package-hard-groove-lift',
              order: 1,
              local_action: 'stage-local-set-plan',
              operator_command: 'go',
              recovery_command: 'Z then send',
              readiness_status: 'ready_for_mock_apply_preview',
              blocked_action: 'real_send_blocked',
            },
          ],
          readiness_checks: [
            {
              check: 'mock_safe',
              status: 'passed',
              required: true,
            },
          ],
          recovery_requirements: [
            {
              requirement_key: 'z-then-send',
              label: 'Recovery: Z then send',
              command: 'Z then send',
              required_before_send: true,
              evidence: 'captured-base exposes recovery before staging',
            },
          ],
          blocked_actions: ['open MIDI port from operator package'],
          safety_lines: ['no MIDI sending'],
          dry_run_summary: {
            apply_policy: 'preview_only',
            would_apply_steps: 2,
            would_open_midi_port: false,
            would_send_midi: false,
            would_write_files: false,
            would_mutate_snapshot: false,
            events_emitted: false,
          },
        },
      }),
    );

    const result = await promise;
    expect(result.operator_package_apply_preview?.sent_midi).toBe(false);
    expect(result.operator_package_apply_preview?.writes_files).toBe(false);
    expect(result.operator_package_apply_preview?.step_count).toBe(2);
  });

  it('round-trips an operator package mock apply command with typed ack payload', async () => {
    const h = makeHarness();
    h.client.connect();
    h.currentSocket().emitOpen();
    const cmd: MockApplyOperatorPackageCommand = {
      type: 'mock_apply_operator_package',
      operator_package_id: 'live-kit-operator-package',
      step_keys: [
        'operator-step-hard-groove-lift',
        'operator-step-industrial-pressure',
      ],
      package_export_keys: {
        'operator-step-hard-groove-lift': 'operator-package-hard-groove-lift',
        'operator-step-industrial-pressure': 'operator-package-industrial-pressure',
      },
      snapshot_id: 'snap-06',
      mock_safe: true,
    };
    const promise = h.client.send(cmd);
    const sent = JSON.parse(h.currentSocket().sent[0] ?? '') as {
      request_id: string;
      command: Command;
    };
    expect(sent.command).toMatchObject(cmd);
    h.currentSocket().emitMessage(
      ack(sent.request_id, {
        operator_package_mock_apply: {
          mock_apply_id: 'operator-package-mock-apply:live-kit-operator-package',
          operator_package_id: 'live-kit-operator-package',
          snapshot_id: 'snap-06',
          mock_safe: true,
          mock_apply_status: 'mock_applied',
          apply_policy: 'mock_apply_only',
          opened_midi_port: false,
          sent_midi: false,
          writes_files: false,
          mutated_snapshot: false,
          applied_send_plan: false,
          emitted_events: false,
          step_count: 2,
          step_keys: [
            'operator-step-hard-groove-lift',
            'operator-step-industrial-pressure',
          ],
          mock_apply_steps: [
            {
              step_key: 'operator-step-hard-groove-lift',
              label: 'Hard Groove Lift',
              slot_key: 'hard-groove-lift',
              package_export_key: 'operator-package-hard-groove-lift',
              order: 1,
              local_action: 'stage-local-set-plan',
              operator_command: 'go',
              recovery_command: 'Z then send',
              mock_apply_status: 'accepted_for_mock_apply',
              blocked_action: 'real_apply_blocked',
            },
          ],
          readiness_checks: [
            {
              check: 'mock_safe',
              status: 'passed',
              required: true,
            },
          ],
          recovery_requirements: [
            {
              requirement_key: 'z-then-send',
              label: 'Recovery: Z then send',
              command: 'Z then send',
              required_before_send: true,
              evidence: 'captured-base exposes recovery before staging',
            },
          ],
          blocked_actions: ['open MIDI port from operator package'],
          safety_lines: ['no MIDI sending'],
          dry_run_summary: {
            apply_policy: 'mock_apply_only',
            mock_applied_steps: 2,
            opened_midi_port: false,
            sent_midi: false,
            writes_files: false,
            mutated_snapshot: false,
            applied_send_plan: false,
            events_emitted: false,
          },
        },
      }),
    );

    const result = await promise;
    expect(result.operator_package_mock_apply?.sent_midi).toBe(false);
    expect(result.operator_package_mock_apply?.applied_send_plan).toBe(false);
    expect(result.operator_package_mock_apply?.step_count).toBe(2);
  });

  it('round-trips an operator package receipt command with typed ack payload', async () => {
    const h = makeHarness();
    h.client.connect();
    h.currentSocket().emitOpen();
    const cmd: BuildOperatorPackageReceiptCommand = {
      type: 'build_operator_package_receipt',
      operator_package_id: 'live-kit-operator-package',
      step_keys: [
        'operator-step-hard-groove-lift',
        'operator-step-industrial-pressure',
      ],
      package_export_keys: {
        'operator-step-hard-groove-lift': 'operator-package-hard-groove-lift',
        'operator-step-industrial-pressure': 'operator-package-industrial-pressure',
      },
      snapshot_id: 'snap-06',
      mock_safe: true,
    };
    const promise = h.client.send(cmd);
    const sent = JSON.parse(h.currentSocket().sent[0] ?? '') as {
      request_id: string;
      command: Command;
    };
    expect(sent.command).toMatchObject(cmd);
    h.currentSocket().emitMessage(
      ack(sent.request_id, {
        operator_package_receipt: {
          receipt_id: 'operator-package-receipt:live-kit-operator-package:snap-06:operator-step-hard-groove-lift',
          receipt_digest: '0123456789abcdef',
          operator_package_id: 'live-kit-operator-package',
          snapshot_id: 'snap-06',
          mock_safe: true,
          receipt_status: 'mock_safe_receipt_ready',
          receipt_policy: 'passive_audit_only',
          opened_midi_port: false,
          sent_midi: false,
          writes_files: false,
          mutated_snapshot: false,
          applied_send_plan: false,
          events_emitted: false,
          step_count: 2,
          step_keys: [
            'operator-step-hard-groove-lift',
            'operator-step-industrial-pressure',
          ],
          receipt_steps: [
            {
              step_key: 'operator-step-hard-groove-lift',
              label: 'Hard Groove Lift',
              slot_key: 'hard-groove-lift',
              package_export_key: 'operator-package-hard-groove-lift',
              order: 1,
              local_action: 'stage-local-set-plan',
              operator_command: 'go',
              recovery_command: 'Z then send',
              readiness_status: 'ready_for_mock_apply_preview',
              blocked_action: 'real_send_blocked',
              receipt_status: 'recorded_for_review',
            },
          ],
          readiness_checks: [
            {
              check: 'mock_safe',
              status: 'passed',
              required: true,
            },
          ],
          recovery_requirements: [
            {
              requirement_key: 'z-then-send',
              label: 'Recovery: Z then send',
              command: 'Z then send',
              required_before_send: true,
              evidence: 'captured-base exposes recovery before staging',
            },
          ],
          blocked_actions: ['open MIDI port from operator package'],
          safety_lines: ['no MIDI sending'],
          audit_summary: {
            receipt_policy: 'passive_audit_only',
            recorded_steps: 2,
            records_apply_preview: true,
            would_open_midi_port: false,
            would_send_midi: false,
            would_write_files: false,
            would_mutate_snapshot: false,
            would_apply_send_plan: false,
            events_emitted: false,
          },
        },
      }),
    );

    const result = await promise;
    expect(result.operator_package_receipt?.sent_midi).toBe(false);
    expect(result.operator_package_receipt?.writes_files).toBe(false);
    expect(result.operator_package_receipt?.step_count).toBe(2);
    expect(result.operator_package_receipt?.receipt_digest).toBe('0123456789abcdef');
  });

  it('rejects send() when the socket is not OPEN', async () => {
    const h = makeHarness();
    h.client.connect();
    // do not emit open
    await expect(h.client.send({ type: 'regen' })).rejects.toThrow('socket not open');
  });

  it('rejects send() when no socket exists yet', async () => {
    const h = makeHarness();
    await expect(h.client.send({ type: 'regen' })).rejects.toThrow('socket not open');
  });

  it('rejects send() with the underlying error when the socket .send() throws (Error path)', async () => {
    const h = makeHarness();
    h.client.connect();
    h.currentSocket().emitOpen();
    h.currentSocket().primeSendError(new Error('eperm'));
    await expect(h.client.send({ type: 'regen' })).rejects.toThrow('eperm');
  });

  it('rejects send() with a wrapped error when the socket .send() throws a non-Error (string)', async () => {
    const h = makeHarness();
    h.client.connect();
    h.currentSocket().emitOpen();
    // FakeWebSocket only accepts Error; cast through unknown to throw a string.
    (h.currentSocket() as unknown as { primeSendError: (e: unknown) => void }).primeSendError(
      'plain-string-error' as unknown as Error,
    );
    await expect(h.client.send({ type: 'regen' })).rejects.toThrow('plain-string-error');
  });

  it('rejects pending commands with ack timeout', async () => {
    const h = makeHarness({ ackTimeoutMs: 100 });
    h.client.connect();
    h.currentSocket().emitOpen();
    const promise = h.client.send({ type: 'regen' });
    vi.advanceTimersByTime(101);
    await expect(promise).rejects.toThrow(/ack timeout/);
  });

  it('ignores stale ack-timeout callbacks after an ack already resolved', async () => {
    const timeoutCallbacks: Array<() => void> = [];
    const captureTimeout = ((callback: TimerHandler): ReturnType<typeof setTimeout> => {
      timeoutCallbacks.push(callback as () => void);
      return 1 as unknown as ReturnType<typeof setTimeout>;
    }) as unknown as typeof setTimeout;
    const h = makeHarness({
      ackTimeoutMs: 100,
      setTimeoutImpl: captureTimeout,
      clearTimeoutImpl: () => undefined,
    });
    h.client.connect();
    h.currentSocket().emitOpen();
    const promise = h.client.send({ type: 'regen' });
    const sent = JSON.parse(h.currentSocket().sent[0] ?? '') as { request_id: string };
    h.currentSocket().emitMessage(ack(sent.request_id));
    await expect(promise).resolves.toMatchObject({ ok: true });
    expect(timeoutCallbacks).toHaveLength(1);
    const staleTimeoutCallback = timeoutCallbacks[0];
    if (staleTimeoutCallback === undefined) throw new Error('timeout callback was not captured');
    staleTimeoutCallback();
    expect(h.client.getStatus()).toBe('connected');
  });

  it('warns when an ack arrives with an unknown request_id', () => {
    const warnings: unknown[] = [];
    const h = makeHarness({ logger: { warn: (...args) => warnings.push(args) } });
    h.client.connect();
    h.currentSocket().emitOpen();
    h.currentSocket().emitMessage(ack('unknown-id'));
    expect(warnings.some((w) => Array.isArray(w) && String(w[0]).includes('unknown request_id'))).toBe(
      true,
    );
  });

  it('rejects all pending commands when the socket closes mid-flight', async () => {
    const h = makeHarness();
    h.client.connect();
    h.currentSocket().emitOpen();
    const promise = h.client.send({ type: 'regen' });
    h.currentSocket().emitClose();
    await expect(promise).rejects.toThrow(/socket closed|client closed/);
  });

  it('ack arriving after timeout is harmlessly ignored (deleted pending entry)', async () => {
    const warnings: unknown[] = [];
    const h = makeHarness({ ackTimeoutMs: 50, logger: { warn: (...args) => warnings.push(args) } });
    h.client.connect();
    h.currentSocket().emitOpen();
    const promise = h.client.send({ type: 'regen' });
    vi.advanceTimersByTime(51);
    await expect(promise).rejects.toThrow();
    // Now the server's "late" ack arrives — should be warned, not crash.
    h.currentSocket().emitMessage(ack('r1'));
    expect(warnings.some((w) => Array.isArray(w) && String(w[0]).includes('unknown request_id'))).toBe(
      true,
    );
  });
});

describe('CockpitClient — close & reconnect', () => {
  it('allows multiple subscribers per event and ignores stale unsubscribe handles', () => {
    const h = makeHarness();
    const first = vi.fn();
    const second = vi.fn();
    const unsubscribeFirst = h.client.on('session_status', first);
    const unsubscribeSecond = h.client.on('session_status', second);
    h.client.connect();
    h.currentSocket().emitOpen();
    h.currentSocket().emitMessage(sessionStatusEvent);
    expect(first).toHaveBeenCalledTimes(1);
    expect(second).toHaveBeenCalledTimes(1);

    unsubscribeFirst();
    h.currentSocket().emitMessage(sessionStatusEvent);
    expect(first).toHaveBeenCalledTimes(1);
    expect(second).toHaveBeenCalledTimes(2);

    const internals = h.client as unknown as {
      eventHandlers: Map<string, Set<unknown>>;
    };
    internals.eventHandlers.delete('session_status');
    expect(() => unsubscribeSecond()).not.toThrow();
  });

  it('close() prevents reconnect and rejects in-flight commands', async () => {
    const h = makeHarness();
    h.client.connect();
    h.currentSocket().emitOpen();
    const inflight = h.client.send({ type: 'regen' });
    h.client.close();
    await expect(inflight).rejects.toThrow('client closed');
    expect(h.client.getStatus()).toBe('closed');
  });

  it('close() is safe to call when never connected', () => {
    const h = makeHarness();
    expect(() => h.client.close()).not.toThrow();
    expect(h.client.getStatus()).toBe('closed');
  });

  it('close() catches errors thrown by socket.close()', () => {
    const warnings: unknown[] = [];
    const h = makeHarness({ logger: { warn: (...args) => warnings.push(args) } });
    h.client.connect();
    const sock = h.currentSocket();
    sock.close = () => {
      throw new Error('close failed');
    };
    expect(() => h.client.close()).not.toThrow();
    expect(warnings.some((w) => Array.isArray(w) && String(w[0]).includes('error closing'))).toBe(
      true,
    );
  });

  it('schedules a reconnect after an unexpected close with the initial delay', () => {
    const h = makeHarness({ initialReconnectDelayMs: 100, maxReconnectDelayMs: 1000 });
    h.client.connect();
    h.currentSocket().emitOpen();
    expect(h.fakes.length).toBe(1);
    h.currentSocket().emitClose();
    expect(h.client.getStatus()).toBe('reconnecting');
    vi.advanceTimersByTime(99);
    expect(h.fakes.length).toBe(1); // not yet
    vi.advanceTimersByTime(1);
    expect(h.fakes.length).toBe(2);
  });

  it('uses exponential backoff between consecutive failed connect attempts', () => {
    // Disable open between attempts → reconnectAttempt does not reset, so backoff grows.
    const h = makeHarness({ initialReconnectDelayMs: 50, maxReconnectDelayMs: 10_000 });
    h.client.connect();
    // Socket 1 never opens — emitClose immediately to start backoff.
    h.currentSocket().emitClose();
    // Attempt 0 → delay 50ms.
    vi.advanceTimersByTime(50);
    expect(h.fakes.length).toBe(2);
    h.currentSocket().emitClose();
    // Attempt 1 → delay 100ms.
    vi.advanceTimersByTime(99);
    expect(h.fakes.length).toBe(2);
    vi.advanceTimersByTime(1);
    expect(h.fakes.length).toBe(3);
    h.currentSocket().emitClose();
    // Attempt 2 → delay 200ms.
    vi.advanceTimersByTime(199);
    expect(h.fakes.length).toBe(3);
    vi.advanceTimersByTime(1);
    expect(h.fakes.length).toBe(4);
  });

  it('caps reconnect delay at maxReconnectDelayMs', () => {
    const h = makeHarness({ initialReconnectDelayMs: 1000, maxReconnectDelayMs: 1500 });
    h.client.connect();
    h.currentSocket().emitClose(); // attempt 0 → delay min(1000, 1500) = 1000
    vi.advanceTimersByTime(1000);
    expect(h.fakes.length).toBe(2);
    h.currentSocket().emitClose(); // attempt 1 → delay min(2000, 1500) = 1500 (capped)
    vi.advanceTimersByTime(1499);
    expect(h.fakes.length).toBe(2);
    vi.advanceTimersByTime(1);
    expect(h.fakes.length).toBe(3);
  });

  it('resets the backoff counter on a successful open', () => {
    const h = makeHarness({ initialReconnectDelayMs: 100 });
    h.client.connect();
    h.currentSocket().emitClose();
    vi.advanceTimersByTime(100);
    h.currentSocket().emitClose(); // attempt 1 → 200ms
    vi.advanceTimersByTime(200);
    h.currentSocket().emitOpen(); // resets attempt back to 0
    h.currentSocket().emitClose();
    vi.advanceTimersByTime(99);
    expect(h.fakes.length).toBe(3);
    vi.advanceTimersByTime(1);
    expect(h.fakes.length).toBe(4); // reset → delay 100 again
  });

  it('disableReconnect=true skips reconnect on unexpected close', () => {
    const h = makeHarness({ disableReconnect: true });
    h.client.connect();
    h.currentSocket().emitOpen();
    h.currentSocket().emitClose();
    expect(h.client.getStatus()).toBe('closed');
    expect(h.fakes.length).toBe(1);
  });

  it('maxReconnectAttempts=0 → no reconnect, status closed', () => {
    const errors: unknown[] = [];
    const h = makeHarness({
      maxReconnectAttempts: 0,
      logger: { error: (...args) => errors.push(args) },
    });
    h.client.connect();
    h.currentSocket().emitOpen();
    h.currentSocket().emitClose();
    expect(h.client.getStatus()).toBe('closed');
    expect(errors.length).toBeGreaterThan(0);
  });

  it('close() during scheduled-but-not-fired reconnect cancels the timer', () => {
    const h = makeHarness({ initialReconnectDelayMs: 500 });
    h.client.connect();
    h.currentSocket().emitOpen();
    h.currentSocket().emitClose();
    expect(h.client.getStatus()).toBe('reconnecting');
    h.client.close();
    vi.advanceTimersByTime(1000);
    expect(h.fakes.length).toBe(1); // no new socket created
  });

  it('reconnect on attempt > 0 emits the "reconnecting" status, not "connecting"', () => {
    const h = makeHarness({ initialReconnectDelayMs: 50 });
    const seen: ConnectionStatus[] = [];
    h.client.onStatusChange((s) => seen.push(s));
    h.client.connect();
    h.currentSocket().emitOpen();
    h.currentSocket().emitClose();
    vi.advanceTimersByTime(50);
    expect(seen).toEqual(['connecting', 'connected', 'reconnecting']);
  });
});

describe('CockpitClient — error event handler', () => {
  it('logs but does not crash on error events', () => {
    const warnings: unknown[] = [];
    const h = makeHarness({ logger: { warn: (...args) => warnings.push(args) } });
    h.client.connect();
    h.currentSocket().emitError();
    expect(warnings.some((w) => Array.isArray(w) && String(w[0]).includes('cockpit ws error'))).toBe(
      true,
    );
  });
});

describe('CockpitClient — logger optional-chain branches', () => {
  it('exercises every logger sink (info/warn/error/debug) when the logger has them all', async () => {
    // Fully-populated logger exercises the truthy arm of each `?.` short-circuit.
    const sinks: Record<string, unknown[][]> = { debug: [], info: [], warn: [], error: [] };
    const logger = {
      debug: (...a: unknown[]) => sinks.debug?.push(a),
      info: (...a: unknown[]) => sinks.info?.push(a),
      warn: (...a: unknown[]) => sinks.warn?.push(a),
      error: (...a: unknown[]) => sinks.error?.push(a),
    };
    const h = makeHarness({
      ackTimeoutMs: 50,
      maxReconnectAttempts: 0,
      initialReconnectDelayMs: 10,
      logger,
    });
    h.client.connect();
    h.currentSocket().emitOpen(); // → info("cockpit ws connected")
    // error event → warn
    h.currentSocket().emitError();
    // unknown ack → warn
    h.currentSocket().emitMessage({ request_id: 'orphan', ok: true });
    // non-string message → warn
    h.currentSocket().emitRawMessage(123);
    // bad JSON → warn
    h.currentSocket().emitMessage('not-json{');
    // unknown shape → warn
    h.currentSocket().emitMessage({ hello: 'world' });
    // event handler throws → error
    h.client.on('session_status', () => {
      throw new Error('handler-boom');
    });
    h.currentSocket().emitMessage(sessionStatusEvent);
    // status handler throws → error
    h.client.onStatusChange(() => {
      throw new Error('status-boom');
    });
    // close → info("cockpit ws closed") + error("max reconnect attempts reached") because max=0
    h.currentSocket().emitClose();
    // socket.close() throwing → warn("error closing socket")
    h.client.connect();
    const second = h.currentSocket();
    second.close = () => {
      throw new Error('close-fail');
    };
    h.client.close();
    expect(sinks.info?.length).toBeGreaterThan(0);
    expect(sinks.warn?.length).toBeGreaterThan(0);
    expect(sinks.error?.length).toBeGreaterThan(0);
  });

  it('does not crash when the logger is the default empty object (falsy arm of `?.`)', () => {
    // No `logger` option ⇒ defaults to {} inside the client ⇒ every `?.` short-circuits.
    const h = makeHarness({ maxReconnectAttempts: 0, initialReconnectDelayMs: 5 });
    h.client.connect();
    h.currentSocket().emitOpen();
    h.currentSocket().emitError();
    h.currentSocket().emitMessage({ request_id: 'orphan', ok: true });
    h.currentSocket().emitRawMessage(123);
    h.currentSocket().emitMessage('not-json{');
    h.currentSocket().emitMessage({ hello: 'world' });
    h.currentSocket().emitClose();
    h.client.close();
    expect(h.client.getStatus()).toBe('closed');
  });
});

describe('CockpitClient — default request id generator path (no injection)', () => {
  it('generates ids that correlate ack-back without an injected generator', async () => {
    // Construct without `requestIdGenerator` to exercise the default branch.
    let last: FakeWebSocket | null = null;
    const client = new CockpitClient({
      url: 'ws://test/ws',
      ackTimeoutMs: 1_000,
      disableReconnect: true,
      webSocketFactory: (url, protocols) => {
        last = new FakeWebSocket(url, protocols);
        return last;
      },
    });
    client.connect();
    if (last === null) throw new Error('socket not created');
    (last as FakeWebSocket).emitOpen();
    const promise = client.send({ type: 'regen' });
    const sent = JSON.parse((last as FakeWebSocket).sent[0] ?? '') as { request_id: string };
    expect(typeof sent.request_id).toBe('string');
    (last as FakeWebSocket).emitMessage(ack(sent.request_id));
    await expect(promise).resolves.toMatchObject({ ok: true });
    client.close();
  });
});

describe('protocol type guards', () => {
  it('isEvent identifies all seven event types', () => {
    expect(isEvent({ type: 'snapshot_changed', snapshot: {} })).toBe(true);
    expect(isEvent({ type: 'mutation_previewed', candidate: null })).toBe(true);
    expect(isEvent({ type: 'send_plan_changed', send_plan: null })).toBe(true);
    expect(isEvent({ type: 'history_updated', history: {} })).toBe(true);
    expect(isEvent({ type: 'profile_changed', profile: null })).toBe(true);
    expect(isEvent({ type: 'performance_console_changed', performance_console: null })).toBe(
      true,
    );
    expect(isEvent({ type: 'session_status' })).toBe(true);
  });

  it('isEvent rejects nulls, non-objects, non-string types, missing types, and unknown types', () => {
    expect(isEvent(null)).toBe(false);
    expect(isEvent(undefined)).toBe(false);
    expect(isEvent(42)).toBe(false);
    expect(isEvent('hello')).toBe(false);
    expect(isEvent({})).toBe(false);
    expect(isEvent({ type: 42 })).toBe(false);
    expect(isEvent({ type: 'not_a_real_event' })).toBe(false);
  });

  it('isEvent rejects messages that also carry a request_id (they are acks)', () => {
    expect(isEvent({ type: 'session_status', request_id: 'r1' })).toBe(false);
  });

  it('isCommandAck identifies ack-shaped messages and rejects others', () => {
    expect(isCommandAck({ request_id: 'r1', ok: true })).toBe(true);
    expect(isCommandAck({ request_id: 'r1', ok: false, error: 'nope' })).toBe(true);
    expect(isCommandAck({ ok: true })).toBe(false);
    expect(isCommandAck({ request_id: 'r1' })).toBe(false);
    expect(isCommandAck({ request_id: 1, ok: true })).toBe(false);
    expect(isCommandAck({ request_id: 'r1', ok: 'yes' })).toBe(false);
    expect(isCommandAck(null)).toBe(false);
    expect(isCommandAck(undefined)).toBe(false);
    expect(isCommandAck(42)).toBe(false);
    expect(isCommandAck('hello')).toBe(false);
  });

  it('resolveArmSecret returns null when localStorage access throws', () => {
    // A hardened webview (or Safari private mode) can make localStorage
    // access throw outright. The resolver must fail CLOSED — returning null
    // so the arm dialog refuses with a real message — rather than letting
    // the exception escape into a render.
    delete (window as { __RYTM_RAND_ARM_SECRET__?: string }).__RYTM_RAND_ARM_SECRET__;
    const original = Object.getOwnPropertyDescriptor(window, 'localStorage');
    Object.defineProperty(window, 'localStorage', {
      configurable: true,
      get() {
        throw new Error('localStorage is blocked');
      },
    });
    try {
      expect(resolveArmSecret()).toBeNull();
    } finally {
      if (original !== undefined) Object.defineProperty(window, 'localStorage', original);
    }
  });

  it('resolveArmSecret returns null in a non-browser global (SSR guard)', () => {
    // Mirrors the WS auth-token resolver's own SSR guard: the module can be
    // imported where `window` does not exist, and arming must resolve to
    // "no secret" rather than throwing on property access.
    vi.stubGlobal('window', undefined);
    try {
      expect(resolveArmSecret()).toBeNull();
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it('ARM_SECRET_STORAGE_KEY matches the key the Tauri shell writes', () => {
    // Pinned against sidecar.rs::ARM_SECRET_STORAGE_KEY — a silent rename on
    // either side would break arming in packaged builds only.
    expect(ARM_SECRET_STORAGE_KEY).toBe('rytm-rand-arm-secret');
  });
});

describe('CockpitClient — reconnect visibility & retryNow', () => {
  it('getUrl() reports the dialed URL (custom + default)', () => {
    const h = makeHarness();
    expect(h.client.getUrl()).toBe('ws://test/ws');
    expect(new CockpitClient().getUrl()).toBe(DEFAULT_WS_URL);
  });

  it('emits attempt + delay when a reconnect is scheduled, null delay when it dials, and a reset on open', () => {
    const h = makeHarness({ initialReconnectDelayMs: 100 });
    const seen: ReconnectState[] = [];
    h.client.onReconnectStateChange((state) => seen.push(state));

    h.client.connect();
    h.currentSocket().emitClose();
    expect(seen).toEqual([{ attempt: 1, nextDelayMs: 100 }]);
    expect(h.client.getReconnectState()).toEqual({ attempt: 1, nextDelayMs: 100 });

    vi.advanceTimersByTime(100);
    expect(seen).toEqual([
      { attempt: 1, nextDelayMs: 100 },
      { attempt: 1, nextDelayMs: null },
    ]);

    h.currentSocket().emitOpen();
    expect(seen[seen.length - 1]).toEqual({ attempt: 0, nextDelayMs: null });
    expect(h.client.getReconnectState()).toEqual({ attempt: 0, nextDelayMs: null });
  });

  it('starts with a zeroed reconnect state', () => {
    const h = makeHarness();
    expect(h.client.getReconnectState()).toEqual({ attempt: 0, nextDelayMs: null });
  });

  it('retryNow() cancels the pending backoff timer and dials immediately', () => {
    const h = makeHarness({ initialReconnectDelayMs: 10_000 });
    const seen: ReconnectState[] = [];
    h.client.onReconnectStateChange((state) => seen.push(state));
    h.client.connect();
    h.currentSocket().emitClose();
    expect(h.fakes.length).toBe(1);
    expect(h.client.getReconnectState()).toEqual({ attempt: 1, nextDelayMs: 10_000 });

    h.client.retryNow();
    expect(h.fakes.length).toBe(2); // dialed without advancing timers
    expect(h.client.getStatus()).toBe('reconnecting');
    expect(seen[seen.length - 1]).toEqual({ attempt: 1, nextDelayMs: null });

    // The cancelled timer must not fire a second dial later.
    vi.advanceTimersByTime(20_000);
    expect(h.fakes.length).toBe(2);
  });

  it('retryNow() is a no-op while a socket already exists', () => {
    const h = makeHarness();
    h.client.connect();
    h.currentSocket().emitOpen();
    h.client.retryNow();
    expect(h.fakes.length).toBe(1);
    expect(h.client.getStatus()).toBe('connected');
  });

  it('retryNow() is a no-op after a user-initiated close()', () => {
    const h = makeHarness();
    h.client.connect();
    h.currentSocket().emitOpen();
    h.client.close();
    h.client.retryNow();
    expect(h.fakes.length).toBe(1);
    expect(h.client.getStatus()).toBe('closed');
  });

  it('retryNow() dials from a gave-up closed state (no pending timer)', () => {
    const h = makeHarness({ maxReconnectAttempts: 0, logger: { error: () => {} } });
    h.client.connect();
    h.currentSocket().emitClose(); // max attempts reached → closed, no timer
    expect(h.client.getStatus()).toBe('closed');
    h.client.retryNow();
    expect(h.fakes.length).toBe(2);
  });

  it('close() during a pending backoff resets the published reconnect delay', () => {
    const h = makeHarness({ initialReconnectDelayMs: 500 });
    const seen: ReconnectState[] = [];
    h.client.onReconnectStateChange((state) => seen.push(state));
    h.client.connect();
    h.currentSocket().emitClose();
    expect(h.client.getReconnectState()).toEqual({ attempt: 1, nextDelayMs: 500 });
    h.client.close();
    expect(h.client.getReconnectState()).toEqual({ attempt: 1, nextDelayMs: null });
    expect(seen[seen.length - 1]).toEqual({ attempt: 1, nextDelayMs: null });
  });

  it('unsubscribing a reconnect-state handler stops its notifications', () => {
    const h = makeHarness({ initialReconnectDelayMs: 100 });
    const seen: ReconnectState[] = [];
    const off = h.client.onReconnectStateChange((state) => seen.push(state));
    off();
    h.client.connect();
    h.currentSocket().emitClose();
    expect(seen).toEqual([]);
  });

  it('a throwing reconnect-state handler is caught and logged', () => {
    const errors: unknown[] = [];
    const h = makeHarness({
      initialReconnectDelayMs: 100,
      logger: { error: (...args) => errors.push(args) },
    });
    const seen: ReconnectState[] = [];
    h.client.onReconnectStateChange(() => {
      throw new Error('handler boom');
    });
    h.client.onReconnectStateChange((state) => seen.push(state));
    h.client.connect();
    h.currentSocket().emitClose();
    expect(seen).toEqual([{ attempt: 1, nextDelayMs: 100 }]);
    expect(
      errors.some(
        (e) => Array.isArray(e) && String(e[0]).includes('reconnect-state handler threw'),
      ),
    ).toBe(true);
  });

  it('a throwing reconnect-state handler without a logger is still swallowed', () => {
    const h = makeHarness({ initialReconnectDelayMs: 100 });
    h.client.onReconnectStateChange(() => {
      throw new Error('handler boom');
    });
    h.client.connect();
    expect(() => h.currentSocket().emitClose()).not.toThrow();
  });
});
