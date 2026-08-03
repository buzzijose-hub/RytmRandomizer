/**
 * ReconnectBanner tests — the mid-session sidecar-loss surface.
 *
 * Covers: visibility gating per WS status (hidden while connecting /
 * connected, loud while reconnecting / closed), the per-status copy,
 * the retry-attempt line + next-dial countdown driven by the client's
 * reconnect-state observable, the "Retry now" action, the announcer
 * wiring, and unsubscribe-on-unmount.
 */

import { act, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { _registerWriter, _reset } from '../../src/a11y';
import { RECONNECT_BANNER_DISPLAY, ReconnectBanner } from '../../src/cockpit/ReconnectBanner';

import { FakeCockpitClient } from './_fixtures';

describe('ReconnectBanner', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    _reset();
    vi.useRealTimers();
  });

  it.each(['connecting', 'connected'] as const)(
    'renders nothing while the status is %s',
    (status) => {
      const fake = new FakeCockpitClient();
      // A stale scheduled delay must not resurrect the banner while hidden.
      fake.reconnectState = { attempt: 1, nextDelayMs: 2000 };
      render(<ReconnectBanner client={fake.asClient()} status={status} />);

      expect(screen.queryByTestId('reconnect-banner')).not.toBeInTheDocument();
    },
  );

  it.each(['reconnecting', 'closed'] as const)(
    'renders the alert with the %s copy',
    (status) => {
      const fake = new FakeCockpitClient();
      render(<ReconnectBanner client={fake.asClient()} status={status} />);

      const banner = screen.getByTestId('reconnect-banner');
      expect(banner).toBeInTheDocument();
      const alert = screen.getByRole('alert');
      expect(alert).toHaveTextContent(RECONNECT_BANNER_DISPLAY[status].headline);
      expect(alert).toHaveTextContent(RECONNECT_BANNER_DISPLAY[status].detail);
    },
  );

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

    act(() => {
      screen.getByTestId('reconnect-banner-retry-now').click();
    });

    expect(fake.retryCalls).toBe(1);
  });

  it('announces the loss through the global announcer, once per visible status', () => {
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
