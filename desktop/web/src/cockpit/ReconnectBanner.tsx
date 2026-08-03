/**
 * ReconnectBanner — prominent mid-session reconnect visibility.
 *
 * When the sidecar dies mid-session the cockpit deliberately STAYS
 * mounted on its last-known data (`bindClientToStore` never clears
 * `sessionStatus` — losing panel context mid-performance is worse than
 * stale values). Before this banner the only truthful surface was the
 * SafetyRail's small "WebSocket: Reconnecting" line, which is easy to
 * miss while performing. This banner is the loud half of that design
 * decision: a fixed-position alert rendered by App whenever the WS
 * status is `reconnecting`/`closed` while a session is still on screen.
 *
 * Reuses the client's reconnect-state observable (attempt count +
 * next-dial countdown) and `retryNow()` — the exact surfaces the
 * OfflineShell already exposes pre-session, so the two reconnect
 * surfaces can never disagree about what the client is doing.
 *
 * A11y: the headline/detail live in a `role="alert"` region whose
 * content is static per status (announced once on appearance); the
 * ticking countdown is rendered OUTSIDE the alert so screen readers are
 * not flooded four times a second. Status transitions additionally go
 * through the global announcer, mirroring OfflineShell's pattern.
 */

import { useEffect, useState } from 'react';

import { announce } from '../a11y';
import type { CockpitClient, ConnectionStatus, ReconnectState } from '../ws/client';

import './styles.css';

/** How often the next-retry countdown re-renders (matches OfflineShell). */
const COUNTDOWN_TICK_MS = 250;

/** The two WS statuses that make the banner visible. */
export type ReconnectBannerStatus = 'reconnecting' | 'closed';

/** Operator copy per visible status. */
export const RECONNECT_BANNER_DISPLAY: Readonly<
  Record<ReconnectBannerStatus, { headline: string; detail: string }>
> = {
  reconnecting: {
    headline: 'Sidecar connection lost',
    detail: 'Reconnecting automatically — cockpit data may be stale until the sidecar answers.',
  },
  closed: {
    headline: 'Sidecar connection closed',
    detail: 'Auto-retry is stopped — use Retry now. Cockpit data may be stale.',
  },
};

/** Narrow a ConnectionStatus to the banner-visible subset (or null). */
function toBannerStatus(status: ConnectionStatus): ReconnectBannerStatus | null {
  return status === 'reconnecting' || status === 'closed' ? status : null;
}

export interface ReconnectBannerProps {
  /** The app's singleton client — used for retryNow() and reconnect visibility. */
  client: CockpitClient;
  /** Current WS connection status (App already subscribes via onStatusChange). */
  status: ConnectionStatus;
}

export function ReconnectBanner({ client, status }: ReconnectBannerProps): JSX.Element | null {
  const [reconnect, setReconnect] = useState<ReconnectState>(() => client.getReconnectState());
  const [remainingMs, setRemainingMs] = useState<number | null>(null);
  const bannerStatus = toBannerStatus(status);

  useEffect(() => client.onReconnectStateChange(setReconnect), [client]);

  useEffect(() => {
    if (bannerStatus === null) return;
    announce(`Sidecar connection ${bannerStatus} — cockpit data may be stale`);
  }, [bannerStatus]);

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

  const display = RECONNECT_BANNER_DISPLAY[bannerStatus];
  const retryLine =
    reconnect.attempt > 0
      ? remainingMs !== null
        ? `Retry attempt ${reconnect.attempt} — next dial in ${Math.ceil(remainingMs / 1000)} s`
        : `Retry attempt ${reconnect.attempt} — dialing now…`
      : null;

  return (
    <div className="reconnect-banner" data-testid="reconnect-banner">
      {/* Static per-status copy only — announced once when the banner appears. */}
      <div role="alert" className="reconnect-banner-alert">
        <span className="reconnect-banner-headline">{display.headline}</span>{' '}
        <span className="reconnect-banner-detail">{display.detail}</span>
      </div>
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
        onClick={() => client.retryNow()}
      >
        Retry now
      </button>
    </div>
  );
}
