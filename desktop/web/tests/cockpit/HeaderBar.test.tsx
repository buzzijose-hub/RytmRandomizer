/**
 * Tests for HeaderBar — null session, mock mode, live armed mode, unsaved
 * sends chip, the Wave-4 connection pill (icon + text per phase), and the
 * dismissible reconnect toast.
 */

import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { act, fireEvent, render, screen } from '@testing-library/react';

import { CONNECTION_PHASE_DISPLAY, HeaderBar } from '../../src/cockpit/HeaderBar';
import { CockpitClientProvider } from '../../src/cockpit/context';
import { RECONNECT_NOTICE, useCockpitStore } from '../../src/state';

import {
  FakeCockpitClient,
  connectionFault,
  connectionListening,
  sessionLive,
  sessionMock,
} from './_fixtures';

function renderHeaderBar(): FakeCockpitClient {
  const fake = new FakeCockpitClient();
  render(
    <CockpitClientProvider client={fake.asClient()}>
      <HeaderBar />
    </CockpitClientProvider>,
  );
  return fake;
}

describe('HeaderBar', () => {
  beforeEach(() => {
    act(() => {
      useCockpitStore.getState().reset();
    });
  });
  afterEach(() => {
    act(() => {
      useCockpitStore.getState().reset();
    });
  });

  it('renders the disconnected placeholder when session is null', () => {
    renderHeaderBar();
    expect(screen.getByText('RytmRandomizer · Cockpit')).toBeInTheDocument();
    expect(screen.getByText('disconnected')).toBeInTheDocument();
    expect(screen.queryByTestId('connection-pill')).not.toBeInTheDocument();
  });

  it('renders live + armed + unsaved badges when session is live and unsaved>0', () => {
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionLive);
    });
    renderHeaderBar();
    expect(screen.getByText('RytmRandomizer · Live')).toBeInTheDocument();
    expect(screen.getByText('● armed')).toBeInTheDocument();
    expect(screen.getByText('port: IAC Driver Bus 1')).toBeInTheDocument();
    expect(screen.getByText('2 unsaved sends')).toBeInTheDocument();
  });

  it('renders mock + safe + no-unsaved-sends + port=none when session is mock', () => {
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
    });
    renderHeaderBar();
    expect(screen.getByText('RytmRandomizer · Mock')).toBeInTheDocument();
    expect(screen.getByText('○ safe')).toBeInTheDocument();
    expect(screen.getByText('port: none')).toBeInTheDocument();
    expect(screen.getByText('no unsaved sends')).toBeInTheDocument();
  });

  it('drives the connection pill from session_status until connection_changed arrives', () => {
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
    });
    renderHeaderBar();
    const pill = screen.getByTestId('connection-pill');
    expect(pill).toHaveTextContent('disconnected');
    expect(pill.className).toContain('connection-pill-disconnected');

    act(() => {
      useCockpitStore.getState().setConnection(connectionListening);
    });
    const updated = screen.getByTestId('connection-pill');
    expect(updated).toHaveTextContent('listening');
    expect(updated.className).toContain('connection-pill-listening');
    // Icon + text — never hue alone.
    expect(updated).toHaveTextContent(CONNECTION_PHASE_DISPLAY.listening.icon);
  });

  it('maps every phase to a distinct icon + label pair', () => {
    const seen = new Set(
      Object.values(CONNECTION_PHASE_DISPLAY).map((d) => `${d.icon} ${d.label}`),
    );
    expect(seen.size).toBe(5);
  });

  it('shows the reconnect toast after fault → listening and dismisses on click', () => {
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
      useCockpitStore.getState().setConnection(connectionFault);
    });
    renderHeaderBar();
    expect(screen.queryByTestId('reconnect-toast')).not.toBeInTheDocument();
    expect(screen.getByTestId('connection-pill')).toHaveTextContent('fault');

    act(() => {
      useCockpitStore.getState().setConnection(connectionListening);
    });
    expect(screen.getByTestId('reconnect-toast')).toHaveTextContent(RECONNECT_NOTICE);

    fireEvent.click(screen.getByRole('button', { name: 'Dismiss reconnect notice' }));
    expect(screen.queryByTestId('reconnect-toast')).not.toBeInTheDocument();
  });
});
