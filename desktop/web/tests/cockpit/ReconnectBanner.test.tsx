/**
 * ReconnectBanner tests — the single sidecar-connection surface.
 *
 * Covers: visibility gating per WS status (hidden while connected; the
 * initial-connecting grace with fake timers; reconnecting/closed shown
 * immediately), the per-status copy in BOTH modes (pre-session vs
 * mid-session), the pre-session "Connection help" disclosure (WS target +
 * per-OS hints), the retry-attempt line + next-dial countdown driven by
 * the client's reconnect-state observable, the "Retry now" action (and
 * its dial-in-flight disablement), the announcer wiring, and
 * unsubscribe-on-unmount.
 */

import { act, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { _registerWriter, _reset } from '../../src/a11y';
import {
  INITIAL_CONNECT_GRACE_MS,
  RECONNECT_BANNER_DISPLAY,
  RECONNECT_BANNER_PRE_SESSION_DISPLAY,
  ReconnectBanner,
} from '../../src/cockpit/ReconnectBanner';
import { useCockpitStore } from '../../src/state';

import { FakeCockpitClient, sessionMock } from './_fixtures';

function seedSession(): void {
  act(() => {
    useCockpitStore.getState().setSessionStatus(sessionMock);
  });
}

describe('ReconnectBanner', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    act(() => {
      useCockpitStore.getState().reset();
    });
  });

  afterEach(() => {
    _reset();
    vi.useRealTimers();
    act(() => {
      useCockpitStore.getState().reset();
    });
  });

  it('renders nothing while the status is connected', () => {
    const fake = new FakeCockpitClient();
    // A stale scheduled delay must not resurrect the banner while hidden.
    fake.reconnectState = { attempt: 1, nextDelayMs: 2000 };
    render(<ReconnectBanner client={fake.asClient()} status="connected" />);

    expect(screen.queryByTestId('reconnect-banner')).not.toBeInTheDocument();
  });

  it('grace-gates the initial connecting status, then shows the banner', () => {
    const fake = new FakeCockpitClient();
    render(<ReconnectBanner client={fake.asClient()} status="connecting" />);

    // During the grace window a normal fast launch shows NO banner flash.
    expect(screen.queryByTestId('reconnect-banner')).not.toBeInTheDocument();
    act(() => {
      vi.advanceTimersByTime(INITIAL_CONNECT_GRACE_MS - 1);
    });
    expect(screen.queryByTestId('reconnect-banner')).not.toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(1);
    });
    expect(screen.getByTestId('reconnect-banner')).toBeInTheDocument();
    expect(screen.getByTestId('reconnect-banner-status')).toHaveTextContent('connecting');
  });

  it('resets the grace when the status leaves connecting and returns', () => {
    const fake = new FakeCockpitClient();
    const { rerender } = render(
      <ReconnectBanner client={fake.asClient()} status="connecting" />,
    );
    act(() => {
      vi.advanceTimersByTime(INITIAL_CONNECT_GRACE_MS);
    });
    expect(screen.getByTestId('reconnect-banner')).toBeInTheDocument();

    // Connected hides the banner and re-arms the grace…
    rerender(<ReconnectBanner client={fake.asClient()} status="connected" />);
    expect(screen.queryByTestId('reconnect-banner')).not.toBeInTheDocument();

    // …so a fresh connecting phase starts hidden again.
    rerender(<ReconnectBanner client={fake.asClient()} status="connecting" />);
    expect(screen.queryByTestId('reconnect-banner')).not.toBeInTheDocument();
    act(() => {
      vi.advanceTimersByTime(INITIAL_CONNECT_GRACE_MS);
    });
    expect(screen.getByTestId('reconnect-banner')).toBeInTheDocument();
  });

  it.each(['reconnecting', 'closed'] as const)(
    'shows the banner immediately (no grace) for %s',
    (status) => {
      const fake = new FakeCockpitClient();
      render(<ReconnectBanner client={fake.asClient()} status={status} />);

      expect(screen.getByTestId('reconnect-banner')).toBeInTheDocument();
      expect(screen.getByTestId('reconnect-banner-status')).toHaveTextContent(status);
    },
  );

  it.each(['reconnecting', 'closed'] as const)(
    'renders the mid-session alert copy for %s when a session is on screen',
    (status) => {
      seedSession();
      const fake = new FakeCockpitClient();
      render(<ReconnectBanner client={fake.asClient()} status={status} />);

      const alert = screen.getByRole('alert');
      expect(alert).toHaveTextContent(RECONNECT_BANNER_DISPLAY[status].headline);
      expect(alert).toHaveTextContent(RECONNECT_BANNER_DISPLAY[status].detail);
    },
  );

  it('renders the mid-session connecting copy once the grace elapses', () => {
    seedSession();
    const fake = new FakeCockpitClient();
    render(<ReconnectBanner client={fake.asClient()} status="connecting" />);
    act(() => {
      vi.advanceTimersByTime(INITIAL_CONNECT_GRACE_MS);
    });

    const alert = screen.getByRole('alert');
    expect(alert).toHaveTextContent(RECONNECT_BANNER_DISPLAY.connecting.headline);
  });

  it.each(['reconnecting', 'closed'] as const)(
    'renders the pre-session alert copy for %s while no session ever arrived',
    (status) => {
      const fake = new FakeCockpitClient();
      render(<ReconnectBanner client={fake.asClient()} status={status} />);

      const alert = screen.getByRole('alert');
      expect(alert).toHaveTextContent(
        RECONNECT_BANNER_PRE_SESSION_DISPLAY[status].headline,
      );
      expect(alert).toHaveTextContent(RECONNECT_BANNER_PRE_SESSION_DISPLAY[status].detail);
    },
  );

  it('renders the pre-session connecting copy once the grace elapses', () => {
    const fake = new FakeCockpitClient();
    render(<ReconnectBanner client={fake.asClient()} status="connecting" />);
    act(() => {
      vi.advanceTimersByTime(INITIAL_CONNECT_GRACE_MS);
    });

    expect(screen.getByRole('alert')).toHaveTextContent(
      RECONNECT_BANNER_PRE_SESSION_DISPLAY.connecting.headline,
    );
  });

  it('carries the connection-help disclosure (WS target + per-OS hints) pre-session', () => {
    const fake = new FakeCockpitClient();
    fake.url = 'ws://127.0.0.1:9999/ws';
    render(<ReconnectBanner client={fake.asClient()} status="reconnecting" />);

    const help = screen.getByTestId('reconnect-banner-help');
    expect(help).toBeInTheDocument();
    expect(screen.getByTestId('reconnect-banner-ws-target')).toHaveTextContent(
      'WebSocket target: ws://127.0.0.1:9999/ws',
    );
    expect(help).toHaveTextContent('python -m rytm_randomizer.cockpit');
    expect(help).toHaveTextContent('lsof -i :4317');
    expect(help).toHaveTextContent('netstat -ano | findstr 4317');
    expect(help).toHaveTextContent('ss -ltnp | grep 4317');
    expect(help).toHaveTextContent('RYTM_RAND_WS_PORT');
    expect(help).toHaveTextContent('The app keeps retrying in the background');
  });

  it('drops the connection-help disclosure once a session is on screen', () => {
    seedSession();
    const fake = new FakeCockpitClient();
    render(<ReconnectBanner client={fake.asClient()} status="reconnecting" />);

    expect(screen.getByTestId('reconnect-banner')).toBeInTheDocument();
    expect(screen.queryByTestId('reconnect-banner-help')).not.toBeInTheDocument();
  });

  it('hides the retry line while no reconnect attempt has been made', () => {
    const fake = new FakeCockpitClient();
    render(<ReconnectBanner client={fake.asClient()} status="reconnecting" />);

    expect(screen.queryByTestId('reconnect-banner-retry-line')).not.toBeInTheDocument();
  });

  it('seeds attempt count and countdown from the client snapshot on mount', () => {
    const fake = new FakeCockpitClient();
    fake.reconnectState = { attempt: 3, nextDelayMs: 4000 };
    render(<ReconnectBanner client={fake.asClient()} status="reconnecting" />);

    expect(screen.getByTestId('reconnect-banner-retry-line')).toHaveTextContent(
      'Retry attempt 3 — next dial in 4 s',
    );
  });

  it('counts down toward the next dial and clamps at 0', () => {
    const fake = new FakeCockpitClient();
    render(<ReconnectBanner client={fake.asClient()} status="reconnecting" />);

    act(() => {
      fake.emitReconnectState({ attempt: 2, nextDelayMs: 4000 });
    });
    expect(screen.getByTestId('reconnect-banner-retry-line')).toHaveTextContent(
      'Retry attempt 2 — next dial in 4 s',
    );

    act(() => {
      vi.advanceTimersByTime(1500);
    });
    expect(screen.getByTestId('reconnect-banner-retry-line')).toHaveTextContent(
      'Retry attempt 2 — next dial in 3 s',
    );

    // Past the scheduled delay the countdown clamps at 0 (the client dials
    // and emits a fresh state in the real flow).
    act(() => {
      vi.advanceTimersByTime(5000);
    });
    expect(screen.getByTestId('reconnect-banner-retry-line')).toHaveTextContent(
      'Retry attempt 2 — next dial in 0 s',
    );
  });

  it('shows "dialing now" while a dial is in flight and hides the line after reset', () => {
    const fake = new FakeCockpitClient();
    render(<ReconnectBanner client={fake.asClient()} status="reconnecting" />);

    act(() => {
      fake.emitReconnectState({ attempt: 5, nextDelayMs: null });
    });
    expect(screen.getByTestId('reconnect-banner-retry-line')).toHaveTextContent(
      'Retry attempt 5 — dialing now…',
    );

    act(() => {
      fake.emitReconnectState({ attempt: 0, nextDelayMs: null });
    });
    expect(screen.queryByTestId('reconnect-banner-retry-line')).not.toBeInTheDocument();
  });

  it('fires client.retryNow() when Retry now is clicked', () => {
    const fake = new FakeCockpitClient();
    render(<ReconnectBanner client={fake.asClient()} status="closed" />);

    const button = screen.getByTestId('reconnect-banner-retry-now');
    expect(button).toBeEnabled();
    act(() => {
      button.click();
    });

    expect(fake.retryCalls).toBe(1);
  });

  it('disables Retry now (with a reason) while a dial is already in flight', () => {
    const fake = new FakeCockpitClient();
    render(<ReconnectBanner client={fake.asClient()} status="connecting" />);
    act(() => {
      vi.advanceTimersByTime(INITIAL_CONNECT_GRACE_MS);
    });

    const button = screen.getByTestId('reconnect-banner-retry-now');
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute('title', 'A dial is already in flight');
  });

  it('announces the loss through the global announcer, once per visible status', () => {
    seedSession();
    const messages: string[] = [];
    _registerWriter((message) => messages.push(message));
    const fake = new FakeCockpitClient();
    const { rerender } = render(
      <ReconnectBanner client={fake.asClient()} status="connected" />,
    );

    act(() => {
      vi.advanceTimersByTime(250);
    });
    // Hidden status: nothing announced.
    expect(messages).toEqual([]);

    rerender(<ReconnectBanner client={fake.asClient()} status="reconnecting" />);
    act(() => {
      vi.advanceTimersByTime(250);
    });
    expect(messages).toEqual(['Sidecar connection reconnecting — cockpit data may be stale']);

    rerender(<ReconnectBanner client={fake.asClient()} status="closed" />);
    act(() => {
      vi.advanceTimersByTime(250);
    });
    expect(messages).toEqual([
      'Sidecar connection reconnecting — cockpit data may be stale',
      'Sidecar connection closed — cockpit data may be stale',
    ]);
  });

  it('announces without the stale-data suffix while no session ever arrived', () => {
    const messages: string[] = [];
    _registerWriter((message) => messages.push(message));
    const fake = new FakeCockpitClient();
    render(<ReconnectBanner client={fake.asClient()} status="reconnecting" />);

    act(() => {
      vi.advanceTimersByTime(250);
    });
    expect(messages).toEqual(['Sidecar connection reconnecting']);
  });

  it('stops listening to reconnect state after unmount', () => {
    const fake = new FakeCockpitClient();
    const { unmount } = render(
      <ReconnectBanner client={fake.asClient()} status="reconnecting" />,
    );
    unmount();

    // No throw / no state update on a dead component.
    fake.emitReconnectState({ attempt: 9, nextDelayMs: 1000 });
    expect(fake.reconnectState.attempt).toBe(9);
  });
});
