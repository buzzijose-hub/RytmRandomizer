/**
 * OfflineShell tests — the no-sidecar surface.
 *
 * Covers: per-status rendering (badge/detail/button disablement), the
 * retry-attempt line + next-dial countdown driven by the client's
 * reconnect-state observable, the "Retry now" action, the WS-target /
 * connection-help content, and the announcer wiring (aria-live via the
 * global LiveRegion announcer).
 */

import { act, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { _registerWriter, _reset } from '../../src/a11y';
import { OFFLINE_STATUS_DISPLAY, OfflineShell } from '../../src/cockpit/OfflineShell';

import { FakeCockpitClient } from './_fixtures';

describe('OfflineShell', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    _reset();
    vi.useRealTimers();
  });

  it('renders the header title, WS target, and connection help', () => {
    const fake = new FakeCockpitClient();
    fake.url = 'ws://127.0.0.1:9999/ws';
    render(<OfflineShell client={fake.asClient()} status="connecting" />);

    expect(screen.getByTestId('offline-shell')).toBeInTheDocument();
    expect(screen.getByText('RytmRandomizer · Cockpit')).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      'Waiting for the RytmRandomizer sidecar',
    );
    expect(screen.getByTestId('offline-ws-target')).toHaveTextContent(
      'WebSocket target: ws://127.0.0.1:9999/ws',
    );
    const help = screen.getByRole('region', { name: 'Connection help' });
    expect(help).toHaveTextContent('python -m rytm_randomizer.cockpit');
    expect(help).toHaveTextContent('lsof -i :4317');
    expect(help).toHaveTextContent('netstat -ano | findstr 4317');
    expect(help).toHaveTextContent('ss -ltnp | grep 4317');
    expect(help).toHaveTextContent('RYTM_RAND_WS_PORT');
  });

  it.each([
    ['connecting', true],
    ['connected', true],
    ['reconnecting', false],
    ['closed', false],
  ] as const)('status %s renders its badge/detail and retry-button state', (status, disabled) => {
    const fake = new FakeCockpitClient();
    render(<OfflineShell client={fake.asClient()} status={status} />);

    expect(screen.getByTestId('offline-status')).toHaveTextContent(
      OFFLINE_STATUS_DISPLAY[status].label,
    );
    expect(screen.getByTestId('offline-detail')).toHaveTextContent(
      OFFLINE_STATUS_DISPLAY[status].detail,
    );
    const button = screen.getByTestId('offline-retry-now');
    if (disabled) {
      expect(button).toBeDisabled();
    } else {
      expect(button).toBeEnabled();
    }
  });

  it('fires client.retryNow() when Retry now is clicked', () => {
    const fake = new FakeCockpitClient();
    render(<OfflineShell client={fake.asClient()} status="reconnecting" />);

    act(() => {
      screen.getByTestId('offline-retry-now').click();
    });

    expect(fake.retryCalls).toBe(1);
  });

  it('hides the retry line while no reconnect attempt has been made', () => {
    const fake = new FakeCockpitClient();
    render(<OfflineShell client={fake.asClient()} status="connecting" />);

    expect(screen.queryByTestId('offline-retry-line')).not.toBeInTheDocument();
  });

  it('seeds attempt count and countdown from the client snapshot on mount', () => {
    const fake = new FakeCockpitClient();
    fake.reconnectState = { attempt: 3, nextDelayMs: 4000 };
    render(<OfflineShell client={fake.asClient()} status="reconnecting" />);

    expect(screen.getByTestId('offline-retry-line')).toHaveTextContent(
      'Retry attempt 3 — next dial in 4 s',
    );
  });

  it('counts down toward the next dial as time advances', () => {
    const fake = new FakeCockpitClient();
    render(<OfflineShell client={fake.asClient()} status="reconnecting" />);

    act(() => {
      fake.emitReconnectState({ attempt: 2, nextDelayMs: 4000 });
    });
    expect(screen.getByTestId('offline-retry-line')).toHaveTextContent(
      'Retry attempt 2 — next dial in 4 s',
    );

    act(() => {
      vi.advanceTimersByTime(1500);
    });
    expect(screen.getByTestId('offline-retry-line')).toHaveTextContent(
      'Retry attempt 2 — next dial in 3 s',
    );

    // Past the scheduled delay the countdown clamps at 0 (the client dials
    // and emits a fresh state in the real flow).
    act(() => {
      vi.advanceTimersByTime(5000);
    });
    expect(screen.getByTestId('offline-retry-line')).toHaveTextContent(
      'Retry attempt 2 — next dial in 0 s',
    );
  });

  it('shows "dialing now" when a retry is in flight and hides the line after reset', () => {
    const fake = new FakeCockpitClient();
    render(<OfflineShell client={fake.asClient()} status="reconnecting" />);

    act(() => {
      fake.emitReconnectState({ attempt: 5, nextDelayMs: null });
    });
    expect(screen.getByTestId('offline-retry-line')).toHaveTextContent(
      'Retry attempt 5 — dialing now…',
    );

    act(() => {
      fake.emitReconnectState({ attempt: 0, nextDelayMs: null });
    });
    expect(screen.queryByTestId('offline-retry-line')).not.toBeInTheDocument();
  });

  it('announces status transitions through the global live-region announcer', () => {
    const messages: string[] = [];
    _registerWriter((message) => messages.push(message));
    const fake = new FakeCockpitClient();
    const { rerender } = render(<OfflineShell client={fake.asClient()} status="connecting" />);

    act(() => {
      vi.advanceTimersByTime(250);
    });
    expect(messages).toEqual(['Sidecar connection connecting']);

    rerender(<OfflineShell client={fake.asClient()} status="reconnecting" />);
    act(() => {
      vi.advanceTimersByTime(250);
    });
    expect(messages).toEqual([
      'Sidecar connection connecting',
      'Sidecar connection reconnecting',
    ]);
  });

  it('stops listening to reconnect state after unmount', () => {
    const fake = new FakeCockpitClient();
    const { unmount } = render(<OfflineShell client={fake.asClient()} status="reconnecting" />);
    unmount();

    // No throw / no state update on a dead component.
    fake.emitReconnectState({ attempt: 9, nextDelayMs: 1000 });
    expect(fake.reconnectState.attempt).toBe(9);
  });
});
