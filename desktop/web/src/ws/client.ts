/**
 * Typed WebSocket client for the cockpit ↔ Python sidecar protocol.
 *
 * Responsibilities:
 * - Connect to the sidecar (default `ws://127.0.0.1:4317/ws`).
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

/** Subscriber for a single event type. Unsubscribe via the returned function. */
export type EventHandler<E extends Event = Event> = (event: E) => void;

export type Unsubscribe = () => void;

export type WebSocketLike = Pick<
  WebSocket,
  'send' | 'close' | 'readyState' | 'addEventListener' | 'removeEventListener'
> & {
  readyState: number;
};

export type WebSocketFactory = (url: string) => WebSocketLike;

export interface ClientLogger {
  debug?: (msg: string, ...rest: unknown[]) => void;
  info?: (msg: string, ...rest: unknown[]) => void;
  warn?: (msg: string, ...rest: unknown[]) => void;
  // The error sink intentionally swallows the return so callers don't need to return void
  // explicitly when wrapping with an accumulator (e.g. `errors.push(args)`).
  error?: (msg: string, ...rest: unknown[]) => void;
}



export interface CockpitClientOptions {
  /** Full WebSocket URL. Default: `ws://127.0.0.1:4317/ws`. */
  url?: string;
  /** Inject a custom WebSocket factory (used by tests). */
  webSocketFactory?: WebSocketFactory;
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

// ---------- Constants ----------

export const DEFAULT_WS_URL = 'ws://127.0.0.1:4317/ws';
const DEFAULT_INITIAL_RECONNECT_DELAY_MS = 500;
const DEFAULT_MAX_RECONNECT_DELAY_MS = 10_000;
const DEFAULT_ACK_TIMEOUT_MS = 5_000;

// ---------- Helpers ----------

function defaultWebSocketFactory(url: string): WebSocketLike {
  // `WebSocket` is provided by the browser/jsdom.
  return new WebSocket(url) as unknown as WebSocketLike;
}

function defaultRequestIdGenerator(): string {
  // Sufficient uniqueness for in-process correlation. We don't need crypto-quality randomness.
  const rand = Math.random().toString(36).slice(2, 10);
  return `req_${Date.now().toString(36)}_${rand}`;
}

// ---------- Client ----------

export class CockpitClient {
  private readonly url: string;
  private readonly webSocketFactory: WebSocketFactory;
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
  private closedByUser = false;

  private readonly eventHandlers = new Map<EventType, Set<EventHandler>>();
  private readonly statusHandlers = new Set<(status: ConnectionStatus) => void>();
  private readonly pending = new Map<string, PendingCommand>();

  // Bound DOM-style handlers so we can add/remove them deterministically.
  private readonly onOpen = (): void => this.handleOpen();
  private readonly onMessage = (ev: Event_): void => this.handleMessage(ev);
  private readonly onError = (ev: Event_): void => this.handleError(ev);
  private readonly onClose = (ev: CloseEvent_): void => this.handleClose(ev);

  constructor(opts: CockpitClientOptions = {}) {
    this.url = opts.url ?? DEFAULT_WS_URL;
    this.webSocketFactory = opts.webSocketFactory ?? defaultWebSocketFactory;
    this.requestIdGenerator = opts.requestIdGenerator ?? defaultRequestIdGenerator;
    this.setTimeoutImpl = opts.setTimeoutImpl ?? setTimeout;
    this.clearTimeoutImpl = opts.clearTimeoutImpl ?? clearTimeout;
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
  send<C extends Command>(command: C): Promise<CommandAck> {
    if (this.socket === null || this.socket.readyState !== WS_OPEN) {
      return Promise.reject(new Error('socket not open'));
    }
    const requestId = this.requestIdGenerator();
    const envelope: CommandEnvelope<C> = { request_id: requestId, command };
    return new Promise<CommandAck>((resolve, reject) => {
      const timeoutHandle = this.setTimeoutImpl(() => {
        if (this.pending.delete(requestId)) {
          reject(new Error(`ack timeout for ${command.type} (request_id=${requestId})`));
        }
      }, this.ackTimeoutMs);
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

  private openSocket(): void {
    this.setStatus(this.reconnectAttempt === 0 ? 'connecting' : 'reconnecting');
    const sock = this.webSocketFactory(this.url);
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
    this.reconnectTimer = this.setTimeoutImpl(() => {
      this.reconnectTimer = null;
      this.openSocket();
    }, delay);
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
}

// ---------- Type aliases for narrow DOM types (avoid forcing lib.dom into call sites) ----------

// We re-export internal aliases so test mocks don't need to drag in full lib.dom types.
// At runtime they're the standard browser types; jsdom provides them in tests.
type Event_ = globalThis.Event;
type CloseEvent_ = globalThis.CloseEvent;
type MessageEvent_ = globalThis.MessageEvent;

// Standard WebSocket readyState constant (we don't reference the global to keep this testable).
const WS_OPEN = 1;
