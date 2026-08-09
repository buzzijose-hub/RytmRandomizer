/**
 * ReconnectBanner — the single sidecar-connection surface.
 *
 * The cockpit mounts unconditionally (there is no session gate in App
 * anymore): plenty of the UI is usable with no sidecar at all, and the
 * client keeps retrying in the background. This banner is the loud,
 * actionable truth about the WebSocket, in both directions:
 *
 * - **Never connected** (`sessionStatus === null`): the banner carries the
 *   retired OfflineShell's essential content in compact form — status,
 *   retry attempt count + next-dial countdown, a Retry-now action, and a
 *   collapsible "Connection help" disclosure with the WS target and
 *   per-OS start-the-sidecar hints.
 * - **Lost mid-session** (`sessionStatus !== null`): the cockpit
 *   deliberately STAYS mounted on its last-known data (`bindClientToStore`
 *   never clears `sessionStatus` — losing panel context mid-performance is
 *   worse than stale values). The banner warns that data may be stale.
 *
 * Visibility: shown whenever the WS is not `connected`. The initial
 * `connecting` status is grace-gated by {@link INITIAL_CONNECT_GRACE_MS}
 * so a normal fast launch never flashes the banner; `reconnecting` and
 * `closed` show immediately.
 *
 * Reuses the client's reconnect-state observable (attempt count +
 * next-dial countdown) and `retryNow()`.
 *
 * A11y: the headline/detail live in a `role="alert"` region whose
 * content is static per status (announced once on appearance); the
 * ticking countdown is rendered OUTSIDE the alert so screen readers are
 * not flooded four times a second. Status transitions additionally go
 * through the global announcer.
 */

import { useEffect, useState } from 'react';

import { announce } from '../a11y';
import { useCockpitStore } from '../state';
import type { CockpitClient, ConnectionStatus, ReconnectState } from '../ws/client';

import './styles.css';

/** How often the next-retry countdown re-renders. */
const COUNTDOWN_TICK_MS = 250;

/**
 * Grace period before the banner appears for the `connecting` status, so a
 * normal fast launch (sidecar already listening) never flashes the banner.
 * `reconnecting`/`closed` are never graced — a failed dial is always shown.
 */
export const INITIAL_CONNECT_GRACE_MS = 1500;

/**
 * Accessible reason used on controls that are disabled because they cannot
 * do anything without a sidecar connection (arm, regen, save, …).
 */
export const SIDECAR_REQUIRED_REASON = 'Requires sidecar connection';

/** The WS statuses that can make the banner visible. */
export type ReconnectBannerStatus = 'connecting' | 'reconnecting' | 'closed';

/** Operator copy per visible status while a session is on screen. */
export const RECONNECT_BANNER_DISPLAY: Readonly<
  Record<ReconnectBannerStatus, { headline: string; detail: string }>
> = {
  connecting: {
    headline: 'Sidecar not connected',
    detail: 'Dialing the sidecar — cockpit data may be stale until it answers.',
  },
  reconnecting: {
    headline: 'Sidecar connection lost',
    detail: 'Reconnecting automatically — cockpit data may be stale until the sidecar answers.',
  },
  closed: {
    headline: 'Sidecar connection closed',
    detail: 'Auto-retry is stopped — use Retry now. Cockpit data may be stale.',
  },
};

/**
 * Operator copy per visible status before ANY session arrived. There is no
 * cockpit data yet, so the message is about what still works (everything
 * local) and what unlocks when the sidecar answers.
 */
export const RECONNECT_BANNER_PRE_SESSION_DISPLAY: Readonly<
  Record<ReconnectBannerStatus, { headline: string; detail: string }>
> = {
  connecting: {
    headline: 'Waiting for the RytmRandomizer sidecar',
    detail: 'Dialing the sidecar — the cockpit is usable now; connected features unlock when it answers.',
  },
  reconnecting: {
    headline: 'Sidecar unreachable',
    detail: 'Retrying automatically — the cockpit stays usable while offline.',
  },
  closed: {
    headline: 'Sidecar not connected',
    detail: 'Auto-retry is stopped — use Retry now. The cockpit stays usable while offline.',
  },
};

/** Narrow a ConnectionStatus to the banner-relevant subset (or null). */
function toBannerStatus(status: ConnectionStatus): ReconnectBannerStatus | null {
  return status === 'connected' ? null : status;
}

export interface ReconnectBannerProps {
  /** The app's singleton client — used for retryNow() and reconnect visibility. */
  client: CockpitClient;
  /** Current WS connection status (App already subscribes via onStatusChange). */
  status: ConnectionStatus;
}

export function ReconnectBanner({ client, status }: ReconnectBannerProps): JSX.Element | null {
  const sessionStatus = useCockpitStore((s) => s.sessionStatus);
  const [reconnect, setReconnect] = useState<ReconnectState>(() => client.getReconnectState());
  const [remainingMs, setRemainingMs] = useState<number | null>(null);
  const [graceElapsed, setGraceElapsed] = useState(false);
  const rawStatus = toBannerStatus(status);
  // The initial `connecting` dial gets a short grace so a healthy launch
  // never flashes the banner; failed dials (reconnecting/closed) never wait.
  const bannerStatus = rawStatus === 'connecting' && !graceElapsed ? null : rawStatus;
  const preSession = sessionStatus === null;

  useEffect(() => client.onReconnectStateChange(setReconnect), [client]);

  useEffect(() => {
    if (rawStatus !== 'connecting') {
      setGraceElapsed(false);
      return undefined;
    }
    const timer = setTimeout(() => setGraceElapsed(true), INITIAL_CONNECT_GRACE_MS);
    return () => clearTimeout(timer);
  }, [rawStatus]);

  useEffect(() => {
    if (bannerStatus === null) return;
    announce(
      preSession
        ? `Sidecar connection ${bannerStatus}`
        : `Sidecar connection ${bannerStatus} — cockpit data may be stale`,
    );
  }, [bannerStatus, preSession]);

  useEffect(() => {
    const delay = reconnect.nextDelayMs;
    if (bannerStatus === null || delay === null) {
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
  }, [reconnect, bannerStatus]);

  if (bannerStatus === null) return null;

  const display = (preSession ? RECONNECT_BANNER_PRE_SESSION_DISPLAY : RECONNECT_BANNER_DISPLAY)[
    bannerStatus
  ];
  const retryLine =
    reconnect.attempt > 0
      ? remainingMs !== null
        ? `Retry attempt ${reconnect.attempt} — next dial in ${Math.ceil(remainingMs / 1000)} s`
        : `Retry attempt ${reconnect.attempt} — dialing now…`
      : null;
  // A dial is already in flight while `connecting` — retryNow() would be a
  // no-op, so the button is disabled (with a reason) to keep the UI honest.
  const dialInFlight = bannerStatus === 'connecting';

  return (
    <div className="reconnect-banner" data-testid="reconnect-banner">
      {/* Static per-status copy only — announced once when the banner appears. */}
      <div role="alert" className="reconnect-banner-alert">
        <span className="reconnect-banner-headline">{display.headline}</span>{' '}
        <span className="reconnect-banner-detail">{display.detail}</span>
      </div>
      {/* Machine-readable status token (static per status; outside the alert). */}
      <span className="reconnect-banner-status" data-testid="reconnect-banner-status">
        {bannerStatus}
      </span>
      {/* Ticking countdown lives OUTSIDE the alert region (SR flood guard). */}
      {retryLine !== null && (
        <p className="reconnect-banner-retry-line" data-testid="reconnect-banner-retry-line">
          {retryLine}
        </p>
      )}
      <button
        type="button"
        className="reconnect-banner-retry-button"
        data-testid="reconnect-banner-retry-now"
        disabled={dialInFlight}
        title={dialInFlight ? 'A dial is already in flight' : undefined}
        onClick={() => client.retryNow()}
      >
        Retry now
      </button>
      {preSession && (
        <details className="reconnect-banner-help" data-testid="reconnect-banner-help">
          <summary>Connection help</summary>
          <p className="reconnect-banner-target" data-testid="reconnect-banner-ws-target">
            WebSocket target: <code>{client.getUrl()}</code>
          </p>
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
          <p className="reconnect-banner-note">
            The app keeps retrying in the background — the cockpit is usable now; connected
            features (session, snapshots, sends) unlock the moment the sidecar answers.
          </p>
        </details>
      )}
    </div>
  );
}
