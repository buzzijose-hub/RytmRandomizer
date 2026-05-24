/**
 * Tests for HeaderBar — null session, mock mode, live armed mode, unsaved sends chip.
 */

import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';

import { HeaderBar } from '../../src/cockpit/HeaderBar';
import { useCockpitStore } from '../../src/state';

import { sessionLive, sessionMock } from './_fixtures';

describe('HeaderBar', () => {
  beforeEach(() => {
    useCockpitStore.getState().reset();
  });
  afterEach(() => {
    useCockpitStore.getState().reset();
  });

  it('renders the disconnected placeholder when session is null', () => {
    render(<HeaderBar />);
    expect(screen.getByText('RytmRandomizer · Cockpit')).toBeInTheDocument();
    expect(screen.getByText('disconnected')).toBeInTheDocument();
  });

  it('renders live + armed + unsaved badges when session is live and unsaved>0', () => {
    useCockpitStore.getState().setSessionStatus(sessionLive);
    render(<HeaderBar />);
    expect(screen.getByText('RytmRandomizer · Live')).toBeInTheDocument();
    expect(screen.getByText('● armed')).toBeInTheDocument();
    expect(screen.getByText('port: IAC Driver Bus 1')).toBeInTheDocument();
    expect(screen.getByText('2 unsaved sends')).toBeInTheDocument();
  });

  it('renders mock + safe + no-unsaved-sends + port=none when session is mock', () => {
    useCockpitStore.getState().setSessionStatus(sessionMock);
    render(<HeaderBar />);
    expect(screen.getByText('RytmRandomizer · Mock')).toBeInTheDocument();
    expect(screen.getByText('○ safe')).toBeInTheDocument();
    expect(screen.getByText('port: none')).toBeInTheDocument();
    expect(screen.getByText('no unsaved sends')).toBeInTheDocument();
  });
});
