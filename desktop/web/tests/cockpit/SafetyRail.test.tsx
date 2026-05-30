/**
 * Tests for SafetyRail -- passive session/device readiness summary.
 */

import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { act, render, screen } from '@testing-library/react';

import { SafetyRail } from '../../src/cockpit/SafetyRail';
import { useCockpitStore } from '../../src/state';

import { blockedSendPlan, sendPlan, sessionLive, sessionMock } from './_fixtures';

describe('SafetyRail', () => {
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

  it('renders mock-safe defaults before a send plan is prepared', () => {
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
      useCockpitStore.getState().setConnectionStatus('connected');
      useCockpitStore.getState().appendOperatorLog({
        level: 'info',
        message: 'WebSocket connected',
      });
    });

    render(<SafetyRail />);

    expect(screen.getByLabelText('Safety status')).toBeInTheDocument();
    expect(screen.getByText('Mock Safe')).toBeInTheDocument();
    expect(screen.getByText('No MIDI Port Open')).toBeInTheDocument();
    expect(screen.getByText('Hardware Off')).toBeInTheDocument();
    expect(screen.getByText('Simulation / Mock')).toBeInTheDocument();
    expect(screen.getByText('Connected')).toBeInTheDocument();
    expect(screen.getByText('Operator Log')).toBeInTheDocument();
    expect(screen.getByText('WebSocket connected')).toBeInTheDocument();
    expect(screen.getByText('No send plan prepared')).toBeInTheDocument();
  });

  it('renders live armed readiness counts when a send plan is ready', () => {
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionLive);
      useCockpitStore.getState().setSendPlan(sendPlan);
    });

    render(<SafetyRail />);

    expect(screen.getByText('Live Armed')).toBeInTheDocument();
    expect(screen.getByText('IAC Driver Bus 1')).toBeInTheDocument();
    expect(screen.getByText('Hardware Armed')).toBeInTheDocument();
    expect(screen.getByText('Live Hardware')).toBeInTheDocument();
    expect(screen.getByText('Ready after prepare')).toBeInTheDocument();
    expect(screen.getAllByText(String(sendPlan.packets.length))).toHaveLength(2);
    expect(sendPlan.packets.length).toBe(sendPlan.estimated_midi_msgs);
  });

  it('renders blocked readiness when a prepared plan is not sendable', () => {
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
      useCockpitStore.getState().setSendPlan(blockedSendPlan);
    });

    render(<SafetyRail />);

    expect(screen.getByText('Blocked')).toBeInTheDocument();
  });
});
