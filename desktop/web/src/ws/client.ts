/**
 * Typed WebSocket client for the cockpit ↔ Python sidecar protocol.
 *
 * Responsibilities:
 * - Connect to the shell-selected loopback sidecar port (fallback `ws://127.0.0.1:4317/ws`).
 * - Parse incoming JSON; dispatch Events to subscribers and Acks to their pending promises.
 * - Send Commands wrapped in an envelope with a generated `request_id`; return a Promise
 *   that resolves with the ack.
 * - Automatic reconnect with exponential backoff (capped). Connection-lifecycle callbacks
 *   for UI status surfaces.
 *
 * Transport-agnostic: callers inject a WebSocketFactory so tests can supply a mock.
 */

import {
  isCommandAck,
  isEvent,
  type Command,
  type CommandAck,
  type CommandEnvelope,
  type Event,
  type EventType,
} from './protocol';

// ---------- Types ----------

/** Connection lifecycle, surfaced to the UI for the connecting/connected/reconnecting chip. */
export type ConnectionStatus = 'connecting' | 'connected' | 'reconnecting' | 'closed';

/**
 * Reconnect visibility snapshot for UI surfaces (offline shell).
 *
 * `attempt` counts dials since the last successful open (resets to 0 on open).
 * `nextDelayMs` is the backoff delay of the currently scheduled dial, or `null`
 * when no dial is pending (connected, dialing right now, or closed).
 */
export interface ReconnectState {
  attempt: number;
  nextDelayMs: number | null;
}

/** Subscriber for a single event type. Unsubscribe via the returned function. */
export type EventHandler<E extends Event = Event> = (event: E) => void;

export type Unsubscribe = () => void;

export type WebSocketLike = Pick<
  WebSocket,
  'send' | 'close' | 'readyState' | 'addEventListener' | 'removeEventListener'
> & {
  readyState: number;
};

export type WebSocketFactory = (url: string, protocols?: string | string[]) => WebSocketLike;
export type AuthTokenResolver = () => string | null;

export interface ClientLogger {
  debug?: (msg: string, ...rest: unknown[]) => void;
  info?: (msg: string, ...rest: unknown[]) => void;
  warn?: (msg: string, ...rest: unknown[]) => void;
  // The error sink intentionally swallows the return so callers don't need to return void
  // explicitly when wrapping with an accumulator (e.g. `errors.push(args)`).
  error?: (msg: string, ...rest: unknown[]) => void;
}

declare global {
  interface Window {
    __RYTM_RAND_WS_TOKEN__?: string;
    /** Per-launch loopback port injected with the WS token by the Tauri shell. */
    __RYTM_RAND_WS_PORT__?: string | number;
    /**
     * Per-launch ARM secret, injected by the Tauri shell.
     *
     * Distinct from the WS token: that one only admits a connection, this
     * one authorises outbound transmit to hardware. The sidecar mints it and
     * writes it 0600; the shell reads that file and injects it
     * (`sidecar.rs::arm_secret_bootstrap_script`). Injection is what makes
     * arming reachable in a packaged double-click build — there is no
     * terminal there for an operator to read a secret from.
     */
    __RYTM_RAND_ARM_SECRET__?: string;
  }
}

export interface CockpitClientOptions {
  /** Full URL override. Otherwise resolve the shell's loopback port on every dial. */
  url?: string;
  /** Inject a custom WebSocket factory (used by tests). */
  webSocketFactory?: WebSocketFactory;
  /** Explicit per-launch WS handshake token. */
  authToken?: string | null;
  /** Resolve the per-launch WS handshake token lazily on socket open. */
  authTokenResolver?: AuthTokenResolver;
  /** Inject a request-id generator (used by tests for determinism). */
  requestIdGenerator?: () => string;
  /** Inject a setTimeout (used by tests with fake timers). */
  setTimeoutImpl?: typeof setTimeout;
  /** Inject a clearTimeout (used by tests with fake timers). */
  clearTimeoutImpl?: typeof clearTimeout;
  /** Initial reconnect delay (ms). Default 500. */
  initialReconnectDelayMs?: number;
  /** Cap on reconnect delay (ms). Default 10000. */
  maxReconnectDelayMs?: number;
  /** Ack timeout (ms). Default 5000. */
  ackTimeoutMs?: number;
  /** Maximum reconnect attempts (Infinity = unlimited). Default Infinity. */
  maxReconnectAttempts?: number;
  /** Disable automatic reconnect (used by tests). Default false. */
  disableReconnect?: boolean;
  /** Optional logger. */
  logger?: ClientLogger;
}

interface PendingCommand {
  resolve: (ack: CommandAck) => void;
  reject: (err: Error) => void;
  timeoutHandle: ReturnType<typeof setTimeout>;
}

export interface SendCommandOptions {
  /** Override the normal ack deadline for operator-paced commands such as SysEx capture. */
  timeoutMs?: number;
}

// ---------- Constants ----------

export const DEFAULT_WS_URL = 'ws://127.0.0.1:4317/ws';
export const WS_SUBPROTOCOL = 'rytm-rand-cockpit-v1';
export const HELLO_FRAME_TYPE = 'hello';
export const WS_AUTH_TOKEN_STORAGE_KEY = 'rytm-rand-ws-token';
/** Storage key the Tauri shell writes the selected loopback port to. */
export const WS_PORT_STORAGE_KEY = 'rytm-rand-ws-port';
/** Storage key the Tauri shell writes the per-launch ARM secret to. */
export const ARM_SECRET_STORAGE_KEY = 'rytm-rand-arm-secret';
const DEFAULT_INITIAL_RECONNECT_DELAY_MS = 500;
const DEFAULT_MAX_RECONNECT_DELAY_MS = 10_000;
const DEFAULT_ACK_TIMEOUT_MS = 5_000;
const MAX_WS_PORT = 65_535;

// ---------- Helpers ----------

function defaultWebSocketFactory(url: string, protocols?: string | string[]): WebSocketLike {
  // `WebSocket` is provided by the browser/jsdom.
  return new WebSocket(url, protocols) as unknown as WebSocketLike;
}

function defaultRequestIdGenerator(): string {
  // Sufficient uniqueness for in-process correlation. We don't need crypto-quality randomness.
  const rand = Math.random().toString(36).slice(2, 10);
  return `req_${Date.now().toString(36)}_${rand}`;
}

function validatedWebSocketPort(value: unknown): number | null {
  if (typeof value !== 'number' && (typeof value !== 'string' || !/^[0-9]+$/.test(value))) {
    return null;
  }
  const port = Number(value);
  return Number.isInteger(port) && port > 0 && port <= MAX_WS_PORT ? port : null;
}

function defaultWebSocketUrl(): string {
  if (typeof window === 'undefined') return DEFAULT_WS_URL;
  let port = validatedWebSocketPort(window.__RYTM_RAND_WS_PORT__);
  if (port === null) {
    try {
      port = validatedWebSocketPort(window.localStorage.getItem(WS_PORT_STORAGE_KEY));
    } catch {
      return DEFAULT_WS_URL;
    }
  }
  // Bootstrap data may select only a port, never a remote host or a different path.
  return port === null ? DEFAULT_WS_URL : `ws://127.0.0.1:${port}/ws`;
}

function defaultAuthTokenResolver(): string | null {
  if (typeof window === 'undefined') return null;
  if (typeof window.__RYTM_RAND_WS_TOKEN__ === 'string' && window.__RYTM_RAND_WS_TOKEN__ !== '') {
    return window.__RYTM_RAND_WS_TOKEN__;
  }
  try {
    const stored = window.localStorage.getItem(WS_AUTH_TOKEN_STORAGE_KEY);
    return stored !== null && stored !== '' ? stored : null;
  } catch {
    return null;
  }
}

/**
 * Resolve the per-launch ARM secret the shell injected, or `null`.
 *
 * Same precedence as {@link defaultAuthTokenResolver}: window property
 * first (set before any app code runs), then localStorage (survives a
 * webview reload). `null` means "no secret available" — callers MUST fail
 * closed and never send an empty token, because the server treats an empty
 * or missing secret as unauthorised anyway and a blank submission would
 * just surface as a confusing refusal.
 */
export function resolveArmSecret(): string | null {
  if (typeof window === 'undefined') return null;
  if (typeof window.__RYTM_RAND_ARM_SECRET__ === 'string' && window.__RYTM_RAND_ARM_SECRET__ !== '') {
    return window.__RYTM_RAND_ARM_SECRET__;
  }
  try {
    const stored = window.localStorage.getItem(ARM_SECRET_STORAGE_KEY);
    return stored !== null && stored !== '' ? stored : null;
  } catch {
    return null;
  }
}

function isHandshakeAck(msg: unknown): msg is { ok: boolean; code?: string } {
  if (msg === null || typeof msg !== 'object') return false;
  const obj = msg as Record<string, unknown>;
  return !('request_id' in obj) && typeof obj.ok === 'boolean';
}

// ---------- Client ----------

export class CockpitClient {
  private readonly explicitUrl: string | undefined;
  private url: string;
  private readonly webSocketFactory: WebSocketFactory;
  private readonly authToken: string | null | undefined;
  private readonly authTokenResolver: AuthTokenResolver;
  private readonly requestIdGenerator: () => string;
  private readonly setTimeoutImpl: typeof setTimeout;
  private readonly clearTimeoutImpl: typeof clearTimeout;
  private readonly initialReconnectDelayMs: number;
  private readonly maxReconnectDelayMs: number;
  private readonly ackTimeoutMs: number;
  private readonly maxReconnectAttempts: number;
  private readonly disableReconnect: boolean;
  private readonly logger: ClientLogger;

  private socket: WebSocketLike | null = null;
  private status: ConnectionStatus = 'closed';
  private reconnectAttempt = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private nextReconnectDelayMs: number | null = null;
  private closedByUser = false;

  private readonly eventHandlers = new Map<EventType, Set<EventHandler>>();
  private readonly statusHandlers = new Set<(status: ConnectionStatus) => void>();
  private readonly reconnectStateHandlers = new Set<(state: ReconnectState) => void>();
  private readonly pending = new Map<string, PendingCommand>();

  // Bound DOM-style handlers so we can add/remove them deterministically.
  private readonly onOpen = (): void => this.handleOpen();
  private readonly onMessage = (ev: Event_): void => this.handleMessage(ev);
  private readonly onError = (ev: Event_): void => this.handleError(ev);
  private readonly onClose = (ev: CloseEvent_): void => this.handleClose(ev);

  constructor(opts: CockpitClientOptions = {}) {
    this.explicitUrl = opts.url;
    this.url = opts.url ?? DEFAULT_WS_URL;
    this.webSocketFactory = opts.webSocketFactory ?? defaultWebSocketFactory;
    this.authToken = opts.authToken;
    this.authTokenResolver = opts.authTokenResolver ?? defaultAuthTokenResolver;
    this.requestIdGenerator = opts.requestIdGenerator ?? defaultRequestIdGenerator;
    this.setTimeoutImpl = opts.setTimeoutImpl ?? globalThis.setTimeout.bind(globalThis);
    this.clearTimeoutImpl = opts.clearTimeoutImpl ?? globalThis.clearTimeout.bind(globalThis);
    this.initialReconnectDelayMs =
      opts.initialReconnectDelayMs ?? DEFAULT_INITIAL_RECONNECT_DELAY_MS;
    this.maxReconnectDelayMs = opts.maxReconnectDelayMs ?? DEFAULT_MAX_RECONNECT_DELAY_MS;
    this.ackTimeoutMs = opts.ackTimeoutMs ?? DEFAULT_ACK_TIMEOUT_MS;
    this.maxReconnectAttempts = opts.maxReconnectAttempts ?? Number.POSITIVE_INFINITY;
    this.disableReconnect = opts.disableReconnect ?? false;
    this.logger = opts.logger ?? {};
  }

  // ----- Public API -----

  /** Open the connection. Safe to call when already open (no-op). */
  connect(): void {
    if (this.socket !== null) return;
    this.closedByUser = false;
    this.openSocket();
  }

  /** Close the connection. Cancels reconnection and rejects any in-flight commands. */
  close(): void {
    this.closedByUser = true;
    if (this.reconnectTimer !== null) {
      this.clearTimeoutImpl(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.setNextReconnectDelay(null);
    this.rejectAllPending(new Error('client closed'));
    if (this.socket !== null) {
      try {
        this.socket.close();
      } catch (err) {
        this.logger.warn?.('error closing socket', err);
      }
      this.detachSocket();
    }
    this.setStatus('closed');
  }

  /** Current connection status. */
  getStatus(): ConnectionStatus {
    return this.status;
  }

  /** Existing socket target, or the next dial's current target when disconnected. */
  getUrl(): string {
    return this.socket === null ? this.resolveUrl() : this.url;
  }

  /** Current reconnect visibility snapshot (see {@link ReconnectState}). */
  getReconnectState(): ReconnectState {
    return { attempt: this.reconnectAttempt, nextDelayMs: this.nextReconnectDelayMs };
  }

  /** Subscribe to reconnect-state changes (attempt count / next-retry delay). */
  onReconnectStateChange(handler: (state: ReconnectState) => void): Unsubscribe {
    this.reconnectStateHandlers.add(handler);
    return () => {
      this.reconnectStateHandlers.delete(handler);
    };
  }

  /**
   * Cancel any pending backoff timer and dial immediately.
   *
   * No-op while a socket already exists (connecting/connected) or after a
   * user-initiated `close()` — auto-reconnect must never resurrect a
   * deliberately closed client.
   */
  retryNow(): void {
    if (this.socket !== null || this.closedByUser) return;
    if (this.reconnectTimer !== null) {
      this.clearTimeoutImpl(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.setNextReconnectDelay(null);
    this.openSocket();
  }

  /** Subscribe to one event type. Returns an unsubscribe function. */
  on<T extends EventType>(
    eventType: T,
    handler: EventHandler<Extract<Event, { type: T }>>,
  ): Unsubscribe {
    let bucket = this.eventHandlers.get(eventType);
    if (bucket === undefined) {
      bucket = new Set();
      this.eventHandlers.set(eventType, bucket);
    }
    bucket.add(handler as EventHandler);
    return () => {
      const b = this.eventHandlers.get(eventType);
      if (b !== undefined) {
        b.delete(handler as EventHandler);
      }
    };
  }

  /** Subscribe to connection-status changes. */
  onStatusChange(handler: (status: ConnectionStatus) => void): Unsubscribe {
    this.statusHandlers.add(handler);
    return () => {
      this.statusHandlers.delete(handler);
    };
  }

  /**
   * Send a typed Command. Returns a Promise that resolves with the server's ack.
   *
   * Rejects if:
   * - The socket is not OPEN.
   * - The ack does not arrive within `ackTimeoutMs`.
   * - The connection closes before the ack arrives.
   */
  send<C extends Command>(command: C, options: SendCommandOptions = {}): Promise<CommandAck> {
    if (this.socket === null || this.socket.readyState !== WS_OPEN) {
      return Promise.reject(new Error('socket not open'));
    }
    const requestId = this.requestIdGenerator();
    const envelope: CommandEnvelope<C> = { request_id: requestId, command };
    const timeoutMs = options.timeoutMs ?? this.ackTimeoutMs;
    return new Promise<CommandAck>((resolve, reject) => {
      const timeoutHandle = this.setTimeoutImpl(() => {
        if (this.pending.delete(requestId)) {
          reject(new Error(`ack timeout for ${command.type} (request_id=${requestId})`));
        }
      }, timeoutMs);
      this.pending.set(requestId, { resolve, reject, timeoutHandle });
      // We verified `this.socket !== null` at the top of `send`. Inside this Promise
      // executor TypeScript loses that narrowing, so we copy to a local. There's no
      // dead-code defensive null check here because nothing between the check and the
      // copy can mutate `this.socket`.
      const sock = this.socket as WebSocketLike;
      try {
        sock.send(JSON.stringify(envelope));
      } catch (err) {
        this.clearTimeoutImpl(timeoutHandle);
        this.pending.delete(requestId);
        reject(err instanceof Error ? err : new Error(String(err)));
      }
    });
  }

  // ----- Internal: socket lifecycle -----

  private resolveUrl(): string {
    return this.explicitUrl ?? defaultWebSocketUrl();
  }

  private openSocket(): void {
    // The shell may inject bootstrap data after startup or choose a new port on restart.
    this.url = this.resolveUrl();
    this.setStatus(this.reconnectAttempt === 0 ? 'connecting' : 'reconnecting');
    const sock = this.webSocketFactory(this.url, WS_SUBPROTOCOL);
    this.socket = sock;
    // The `Event_` and `CloseEvent_` types are erased to `Event` / `CloseEvent` at runtime.
    sock.addEventListener('open', this.onOpen as unknown as EventListener);
    sock.addEventListener('message', this.onMessage as unknown as EventListener);
    sock.addEventListener('error', this.onError as unknown as EventListener);
    sock.addEventListener('close', this.onClose as unknown as EventListener);
  }

  /**
   * Detach the current socket. Callers MUST ensure `this.socket !== null`. Both call
   * sites — `close()` and `handleClose()` — already guarantee this.
   */
  private detachSocket(): void {
    // Narrow with a non-null assertion: precondition checked by caller.
    const sock = this.socket as WebSocketLike;
    sock.removeEventListener('open', this.onOpen as unknown as EventListener);
    sock.removeEventListener('message', this.onMessage as unknown as EventListener);
    sock.removeEventListener('error', this.onError as unknown as EventListener);
    sock.removeEventListener('close', this.onClose as unknown as EventListener);
    this.socket = null;
  }

  private handleOpen(): void {
    this.logger.info?.('cockpit ws connected', this.url);
    this.reconnectAttempt = 0;
    this.setNextReconnectDelay(null);
    try {
      this.sendHandshake();
    } catch (err) {
      this.logger.warn?.('cockpit ws handshake send failed', err);
      this.socket?.close();
      return;
    }
    this.setStatus('connected');
  }

  private handleMessage(ev: Event_): void {
    const raw = (ev as MessageEvent_).data;
    if (typeof raw !== 'string') {
      this.logger.warn?.('cockpit ws received non-string message; ignoring');
      return;
    }
    let parsed: unknown;
    try {
      parsed = JSON.parse(raw);
    } catch (err) {
      this.logger.warn?.('cockpit ws failed to parse message', err);
      return;
    }
    if (isCommandAck(parsed)) {
      const pending = this.pending.get(parsed.request_id);
      if (pending === undefined) {
        this.logger.warn?.('cockpit ws received ack for unknown request_id', parsed.request_id);
        return;
      }
      this.pending.delete(parsed.request_id);
      this.clearTimeoutImpl(pending.timeoutHandle);
      pending.resolve(parsed);
      return;
    }
    if (isHandshakeAck(parsed)) {
      if (!parsed.ok) this.logger.warn?.('cockpit ws handshake rejected', parsed.code);
      return;
    }
    if (isEvent(parsed)) {
      this.dispatchEvent(parsed);
      return;
    }
    this.logger.warn?.('cockpit ws received unrecognized message shape', parsed);
  }

  private handleError(ev: Event_): void {
    this.logger.warn?.('cockpit ws error', ev);
  }

  private handleClose(_ev: CloseEvent_): void {
    this.logger.info?.('cockpit ws closed');
    this.rejectAllPending(new Error('socket closed'));
    this.detachSocket();
    if (this.closedByUser || this.disableReconnect) {
      this.setStatus('closed');
      return;
    }
    this.scheduleReconnect();
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempt >= this.maxReconnectAttempts) {
      this.logger.error?.('cockpit ws max reconnect attempts reached', this.reconnectAttempt);
      this.setStatus('closed');
      return;
    }
    this.setStatus('reconnecting');
    const delay = Math.min(
      this.initialReconnectDelayMs * Math.pow(2, this.reconnectAttempt),
      this.maxReconnectDelayMs,
    );
    this.reconnectAttempt += 1;
    this.setNextReconnectDelay(delay);
    this.reconnectTimer = this.setTimeoutImpl(() => {
      this.reconnectTimer = null;
      this.setNextReconnectDelay(null);
      this.openSocket();
    }, delay);
  }

  /** Record the pending backoff delay and notify reconnect-state subscribers. */
  private setNextReconnectDelay(delayMs: number | null): void {
    this.nextReconnectDelayMs = delayMs;
    const state = this.getReconnectState();
    for (const handler of this.reconnectStateHandlers) {
      try {
        handler(state);
      } catch (err) {
        this.logger.error?.('cockpit ws reconnect-state handler threw', err);
      }
    }
  }

  private dispatchEvent(event: Event): void {
    const bucket = this.eventHandlers.get(event.type);
    if (bucket === undefined) return;
    for (const handler of bucket) {
      try {
        handler(event);
      } catch (err) {
        this.logger.error?.('cockpit ws event handler threw', event.type, err);
      }
    }
  }

  private rejectAllPending(err: Error): void {
    for (const [, pending] of this.pending) {
      this.clearTimeoutImpl(pending.timeoutHandle);
      pending.reject(err);
    }
    this.pending.clear();
  }

  private setStatus(next: ConnectionStatus): void {
    if (this.status === next) return;
    this.status = next;
    for (const handler of this.statusHandlers) {
      try {
        handler(next);
      } catch (err) {
        this.logger.error?.('cockpit ws status handler threw', err);
      }
    }
  }

  private sendHandshake(): void {
    const token = this.authToken !== undefined ? this.authToken : this.authTokenResolver();
    if (token === null || token === '') {
      this.logger.warn?.('cockpit ws auth token unavailable; waiting for server close');
      return;
    }
    const sock = this.socket as WebSocketLike;
    sock.send(JSON.stringify({ type: HELLO_FRAME_TYPE, token }));
  }
}

// ---------- Type aliases for narrow DOM types (avoid forcing lib.dom into call sites) ----------

// We re-export internal aliases so test mocks don't need to drag in full lib.dom types.
// At runtime they're the standard browser types; jsdom provides them in tests.
type Event_ = globalThis.Event;
type CloseEvent_ = globalThis.CloseEvent;
type MessageEvent_ = globalThis.MessageEvent;

// Standard WebSocket readyState constant (we don't reference the global to keep this testable).
const WS_OPEN = 1;
