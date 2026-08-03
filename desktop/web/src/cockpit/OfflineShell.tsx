/**
 * OfflineShell — the surface shown while no session_status has arrived from
 * the sidecar (sidecar down, still dialing, or connected-but-quiet).
 *
 * Replaces the old dead "Connecting…" placeholder with an honest screen:
 * live WS status, the auto-retry attempt count and next-dial countdown from
 * the client's reconnect-state observable, a manual "Retry now" action, and
 * client-side connection help (WS target + per-OS hints, mirroring the
 * Connection Doctor's tone). Auto-retry continues regardless — this surface
 * only makes it visible.
 *
 * A11y: status transitions are pushed through the global announcer (the
 * `<LiveRegion />` mounted by App), so screen readers hear "Sidecar
 * connection reconnecting" without the ticking countdown flooding the
 * polite region.
 */

import { useEffect, useState } from 'react';

import { announce } from '../a11y';
import type { CockpitClient, ConnectionStatus, ReconnectState } from '../ws/client';

import './styles.css';

/** How often the next-retry countdown re-renders. */
const COUNTDOWN_TICK_MS = 250;

/** Icon + operator copy per WS connection status (icons are decorative). */
export const OFFLINE_STATUS_DISPLAY: Readonly<
  Record<ConnectionStatus, { icon: string; label: string; detail: string }>
> = {
  connecting: {
    icon: '◌',
    label: 'connecting',
    detail: 'Dialing the sidecar…',
  },
  connected: {
    icon: '●',
    label: 'connected',
    detail: 'Connected — waiting for the first session status from the sidecar…',
  },
  reconnecting: {
    icon: '↻',
    label: 'reconnecting',
    detail: 'Sidecar unreachable — retrying automatically.',
  },
  closed: {
    icon: '○',
    label: 'closed',
    detail: 'Not connected. Auto-retry is stopped — use Retry now.',
  },
};

export interface OfflineShellProps {
  /** The app's singleton client — used for retryNow() and reconnect visibility. */
  client: CockpitClient;
  /** Current WS connection status (App already subscribes via onStatusChange). */
  status: ConnectionStatus;
}

export function OfflineShell({ client, status }: OfflineShellProps): JSX.Element {
  const [reconnect, setReconnect] = useState<ReconnectState>(() => client.getReconnectState());
  const [remainingMs, setRemainingMs] = useState<number | null>(null);

  useEffect(() => client.onReconnectStateChange(setReconnect), [client]);

  useEffect(() => {
    announce(`Sidecar connection ${OFFLINE_STATUS_DISPLAY[status].label}`);
  }, [status]);

  useEffect(() => {
    const delay = reconnect.nextDelayMs;
    if (delay === null) {
      setRemainingMs(null);
      return undefined;
    }
    setRemainingMs(delay);
    const startedAt = Date.now();
    const tick = setInterval(() => {
      const left = delay - (Date.now() - startedAt);
      setRemainingMs(left > 0 ? left : 0);
    }, COUNTDOWN_TICK_MS);
    return () => clearInterval(tick);
  }, [reconnect]);

  const display = OFFLINE_STATUS_DISPLAY[status];
  // A dial is already in flight while connecting/connected — retryNow() would
  // be a no-op, so the button is disabled to keep the UI honest.
  const dialInFlight = status === 'connecting' || status === 'connected';
  const retryLine =
    reconnect.attempt > 0
      ? remainingMs !== null
        ? `Retry attempt ${reconnect.attempt} — next dial in ${Math.ceil(remainingMs / 1000)} s`
        : `Retry attempt ${reconnect.attempt} — dialing now…`
      : null;

  return (
    <div className="offline-shell" data-testid="offline-shell">
      <header className="cockpit-header">
        <span className="title">RytmRandomizer · Cockpit</span>
        <span
          className={`badge offline-status-badge offline-status-${status}`}
          data-testid="offline-status"
        >
          <span aria-hidden="true">{display.icon}</span> {display.label}
        </span>
      </header>
      <main className="offline-shell-main">
        <section className="offline-shell-card" aria-labelledby="offline-shell-heading">
          <h1 id="offline-shell-heading">Waiting for the RytmRandomizer sidecar</h1>
          <p className="offline-shell-detail" data-testid="offline-detail">
            {display.detail}
          </p>
          {retryLine !== null && (
            <p className="offline-shell-retry-line" data-testid="offline-retry-line">
              {retryLine}
            </p>
          )}
          <div className="offline-shell-actions">
            <button
              type="button"
              className="offline-retry-button"
              data-testid="offline-retry-now"
              onClick={() => client.retryNow()}
              disabled={dialInFlight}
            >
              Retry now
            </button>
            <span className="offline-shell-target" data-testid="offline-ws-target">
              WebSocket target: <code>{client.getUrl()}</code>
            </span>
          </div>
          <section className="offline-shell-help" aria-label="Connection help">
            <h2>Nothing listening?</h2>
            <ul>
              <li>
                Start the sidecar: <code>.venv/bin/python -m rytm_randomizer.cockpit</code> — or
                launch the desktop app, which spawns it automatically.
              </li>
              <li>
                macOS: confirm the port is really free with <code>lsof -i :4317</code>.
              </li>
              <li>
                Windows: check the listener with <code>netstat -ano | findstr 4317</code>.
              </li>
              <li>
                Linux: check the listener with <code>ss -ltnp | grep 4317</code>.
              </li>
              <li>
                Custom port? The sidecar honours <code>RYTM_RAND_WS_PORT</code> — the shell must
                dial the same port.
              </li>
            </ul>
            <p className="offline-shell-note">
              The app keeps retrying in the background — device-independent features (library,
              wizard, reports) unlock the moment the sidecar answers.
            </p>
          </section>
        </section>
      </main>
    </div>
  );
}
