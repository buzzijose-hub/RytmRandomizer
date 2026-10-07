/**
 * Tests for SafetyRail -- passive session/device readiness summary.
 */

import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { act, render, screen } from '@testing-library/react';

import { SafetyRail } from '../../src/cockpit/SafetyRail';
import { useCockpitStore } from '../../src/state';
import type { SendPlanReadinessReason } from '../../src/ws/protocol';

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

  it('explains that a paired-control refusal blocks every packet in the plan', () => {
    act(() => {
      useCockpitStore.getState().setSendPlan({
        ...sendPlan,
        ready: false,
        readiness_reason: 'paired_control_precision_unverified',
        blocked_reasons: ['paired_control_precision_unverified'],
      });
    });

    render(<SafetyRail />);

    expect(screen.getByText('Blocked')).toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveTextContent(
      'Paired-control precision is unverified. No part of this plan will be sent.',
    );
  });

  it.each([
    ['candidate_high_risk', 'High-risk or protected changes are blocked.'],
    ['profile_mismatch', 'The candidate belongs to another profile.'],
    ['source_snapshot_mismatch', 'The candidate belongs to another source.'],
    ['no_sendable_changes', 'No supported changes remain in the selected, unlocked pads.'],
    ['parameter_scope_mismatch', 'Parameter scope changed. Regenerate the candidate'],
    ['unsupported_control_changed', 'An unsupported or protected control changed. No part of this plan will be sent.'],
  ] as const)('explains the specific requirement for %s', (reason, message) => {
    act(() => {
      useCockpitStore.getState().setSendPlan({
        ...sendPlan,
        ready: false,
        readiness_reason: reason,
        blocked_reasons: [reason],
      });
    });
    render(<SafetyRail />);
    expect(screen.getByRole('status')).toHaveTextContent(message);
  });

  it('shows every refusal while omitting the ready sentinel', () => {
    const reasons: SendPlanReadinessReason[] = [
      'ready', 'candidate_high_risk', 'paired_control_precision_unverified',
    ];
    act(() => {
      useCockpitStore.getState().setSendPlan({ ...blockedSendPlan, blocked_reasons: reasons });
    });
    render(<SafetyRail />);
    expect(screen.getAllByRole('status')).toHaveLength(2);
    expect(screen.queryByText('Ready after prepare')).not.toBeInTheDocument();
  });
});
